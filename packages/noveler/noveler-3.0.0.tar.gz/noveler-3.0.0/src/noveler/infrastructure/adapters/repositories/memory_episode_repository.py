"""インメモリエピソードリポジトリアダプター

SPEC-901-DDD-REFACTORING: Port & Adapter分離実装
Golden Sampleに基づくテスト用インメモリ実装

このアダプターは高速なテスト実行のための一時的なエピソード管理を提供します。
すべてのデータはメモリ内に保持され、プロセス終了時に失われます。
"""

from datetime import datetime

from noveler.domain.entities.episode import Episode, EpisodeStatus
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.episode_title import EpisodeTitle
from noveler.domain.value_objects.word_count import WordCount
from noveler.infrastructure.ports.repositories.episode_repository import (
    AdvancedEpisodeRepositoryPort,
    EpisodeQuery,
    EpisodeStatistics,
)


class RepositoryError(Exception):
    """リポジトリ操作エラー"""


class MemoryEpisodeRepositoryAdapter(AdvancedEpisodeRepositoryPort):
    """インメモリエピソードリポジトリアダプター

    テスト用の高速な実装を提供。
    Golden Sampleのパターンに従い、完全な機能セットをサポート。
    """

    def __init__(self) -> None:
        """初期化"""
        # プロジェクトID -> エピソード番号 -> Episode のマップ
        self._episodes: dict[str, dict[int, Episode]] = {}
        # バックアップストレージ
        self._backups: dict[str, dict[int, dict[str, str]]] = {}
        # 次のエピソード番号管理
        self._next_episode_numbers: dict[str, int] = {}

    async def save(self, episode: Episode, project_id: str) -> None:
        """エピソードを非同期で保存

        Args:
            episode: 保存するエピソード
            project_id: プロジェクトID

        Raises:
            RepositoryError: 保存に失敗した場合
        """
        try:
            if project_id not in self._episodes:
                self._episodes[project_id] = {}

            # エピソードを保存（ディープコピー相当）
            self._episodes[project_id][episode.number.value] = self._copy_episode(episode)

            # 次のエピソード番号を更新
            if project_id not in self._next_episode_numbers:
                self._next_episode_numbers[project_id] = 1
            self._next_episode_numbers[project_id] = max(
                self._next_episode_numbers[project_id],
                episode.number.value + 1
            )

        except Exception as e:
            msg = f"エピソード保存に失敗: {e}"
            raise RepositoryError(msg) from e

    async def find_by_id(self, episode_id: str, project_id: str) -> Episode | None:
        """IDでエピソードを非同期検索

        Args:
            episode_id: エピソードID
            project_id: プロジェクトID

        Returns:
            Episode: 見つかったエピソード、なければNone

        Raises:
            RepositoryError: 検索に失敗した場合
        """
        try:
            # 簡単な実装：episode_idから番号を抽出
            episode_number = self._extract_episode_number_from_id(episode_id)
            if episode_number is None:
                return None

            return await self.find_by_project_and_number(project_id, episode_number)

        except Exception as e:
            msg = f"エピソード検索に失敗: {e}"
            raise RepositoryError(msg) from e

    async def find_by_project_and_number(self, project_id: str, episode_number: int) -> Episode | None:
        """プロジェクトIDとエピソード番号でエピソードを非同期検索

        Args:
            project_id: プロジェクトID
            episode_number: エピソード番号

        Returns:
            Episode: 見つかったエピソード、なければNone

        Raises:
            RepositoryError: 検索に失敗した場合
        """
        try:
            if project_id not in self._episodes:
                return None

            episode = self._episodes[project_id].get(episode_number)
            return self._copy_episode(episode) if episode else None

        except Exception as e:
            msg = f"エピソード検索に失敗: {e}"
            raise RepositoryError(msg) from e

    async def find_all_by_project(self, project_id: str) -> list[Episode]:
        """プロジェクトの全エピソードを非同期取得

        Args:
            project_id: プロジェクトID

        Returns:
            List[Episode]: エピソードリスト

        Raises:
            RepositoryError: 検索に失敗した場合
        """
        try:
            if project_id not in self._episodes:
                return []

            episodes = [
                self._copy_episode(episode)
                for episode in self._episodes[project_id].values()
            ]
            return sorted(episodes, key=lambda ep: ep.number.value)

        except Exception as e:
            msg = f"全エピソード取得に失敗: {e}"
            raise RepositoryError(msg) from e

    async def find_by_status(self, project_id: str, status: str) -> list[Episode]:
        """ステータスでエピソードを非同期検索"""
        try:
            all_episodes = await self.find_all_by_project(project_id)
            # EpisodeStatusはEnumなので、文字列比較のためvalueを使う
            target_status = EpisodeStatus(status) if isinstance(status, str) else status
            return [ep for ep in all_episodes if ep.status == target_status]
        except Exception as e:
            msg = f"ステータス検索に失敗: {e}"
            raise RepositoryError(msg) from e

    async def find_by_date_range(self, project_id: str, start_date: datetime, end_date: datetime) -> list[Episode]:
        """日付範囲でエピソードを非同期検索"""
        try:
            all_episodes = await self.find_all_by_project(project_id)
            return [
                ep for ep in all_episodes
                if start_date <= ep.created_at <= end_date
            ]
        except Exception as e:
            msg = f"日付範囲検索に失敗: {e}"
            raise RepositoryError(msg) from e

    async def delete(self, episode_id: str, project_id: str) -> bool:
        """エピソードを非同期削除

        Args:
            episode_id: エピソードID
            project_id: プロジェクトID

        Returns:
            bool: 削除成功時True

        Raises:
            RepositoryError: 削除に失敗した場合
        """
        try:
            episode_number = self._extract_episode_number_from_id(episode_id)
            if episode_number is None:
                return False

            if project_id not in self._episodes:
                return False

            if episode_number in self._episodes[project_id]:
                del self._episodes[project_id][episode_number]
                return True

            return False

        except Exception as e:
            msg = f"エピソード削除に失敗: {e}"
            raise RepositoryError(msg) from e

    async def get_next_episode_number(self, project_id: str) -> int:
        """次のエピソード番号を非同期取得

        Args:
            project_id: プロジェクトID

        Returns:
            int: 次のエピソード番号

        Raises:
            RepositoryError: 取得に失敗した場合
        """
        try:
            return self._next_episode_numbers.get(project_id, 1)
        except Exception as e:
            msg = f"次のエピソード番号取得に失敗: {e}"
            raise RepositoryError(msg) from e

    async def get_statistics(self, project_id: str) -> EpisodeStatistics:
        """エピソード統計情報を非同期取得

        Args:
            project_id: プロジェクトID

        Returns:
            EpisodeStatistics: 統計情報

        Raises:
            RepositoryError: 取得に失敗した場合
        """
        try:
            all_episodes = await self.find_all_by_project(project_id)

            total_episodes = len(all_episodes)
            total_word_count = sum(ep.word_count.value for ep in all_episodes)
            published_episodes = len([ep for ep in all_episodes if ep.status.value == "published"])
            draft_episodes = len([ep for ep in all_episodes if ep.status.value == "draft"])
            average_word_count = total_word_count / total_episodes if total_episodes > 0 else 0.0

            last_updated = "未更新"
            if all_episodes:
                latest_episode = max(all_episodes, key=lambda ep: ep.updated_at)
                last_updated = latest_episode.updated_at.strftime("%Y-%m-%d %H:%M:%S")

            return EpisodeStatistics(
                total_episodes=total_episodes,
                total_word_count=total_word_count,
                published_episodes=published_episodes,
                draft_episodes=draft_episodes,
                average_word_count=average_word_count,
                last_updated=last_updated,
            )

        except Exception as e:
            msg = f"統計情報取得に失敗: {e}"
            raise RepositoryError(msg) from e

    async def find_by_query(self, query: EpisodeQuery) -> list[Episode]:
        """クエリでエピソードを非同期検索

        Args:
            query: 検索クエリ

        Returns:
            List[Episode]: 検索結果

        Raises:
            RepositoryError: 検索に失敗した場合
        """
        try:
            if not query.project_id:
                msg = "project_idは必須です"
                raise ValueError(msg)

            all_episodes = await self.find_all_by_project(query.project_id)
            filtered_episodes = self._apply_query_filters(all_episodes, query)

            return self._apply_query_sorting_and_pagination(filtered_episodes, query)

        except Exception as e:
            msg = f"クエリ検索に失敗: {e}"
            raise RepositoryError(msg) from e

    async def count_by_query(self, query: EpisodeQuery) -> int:
        """クエリに該当するエピソード数を非同期取得"""
        try:
            episodes = await self.find_by_query(query)
            return len(episodes)
        except Exception as e:
            msg = f"クエリカウント取得に失敗: {e}"
            raise RepositoryError(msg) from e

    async def bulk_update_status(self, project_id: str, episode_ids: list[str], new_status: str) -> int:
        """複数エピソードのステータスを一括更新"""
        try:
            updated_count = 0
            for episode_id in episode_ids:
                episode = await self.find_by_id(episode_id, project_id)
                if episode:
                    episode.status = EpisodeStatus(new_status)
                    await self.save(episode, project_id)
                    updated_count += 1
            return updated_count
        except Exception as e:
            msg = f"一括ステータス更新に失敗: {e}"
            raise RepositoryError(msg) from e

    async def backup_episode(self, episode_id: str, project_id: str) -> bool:
        """エピソードを非同期バックアップ

        Args:
            episode_id: エピソードID
            project_id: プロジェクトID

        Returns:
            bool: バックアップ成功時True

        Raises:
            RepositoryError: バックアップに失敗した場合
        """
        try:
            episode = await self.find_by_id(episode_id, project_id)
            if not episode:
                return False

            if project_id not in self._backups:
                self._backups[project_id] = {}
            if episode.number.value not in self._backups[project_id]:
                self._backups[project_id][episode.number.value] = {}

            # 簡単なバックアップ（現在時刻をバージョンとする）
            backup_version = datetime.now().isoformat()
            self._backups[project_id][episode.number.value][backup_version] = episode.content

            return True

        except Exception as e:
            msg = f"エピソードバックアップに失敗: {e}"
            raise RepositoryError(msg) from e

    async def restore_episode(self, episode_id: str, project_id: str, backup_version: str) -> bool:
        """エピソードをバックアップから非同期復元

        Args:
            episode_id: エピソードID
            project_id: プロジェクトID
            backup_version: バックアップバージョン

        Returns:
            bool: 復元成功時True

        Raises:
            RepositoryError: 復元に失敗した場合
        """
        try:
            episode_number = self._extract_episode_number_from_id(episode_id)
            if episode_number is None:
                return False

            if (project_id not in self._backups or
                episode_number not in self._backups[project_id] or
                backup_version not in self._backups[project_id][episode_number]):
                return False

            # 現在のエピソードを取得
            episode = await self.find_by_id(episode_id, project_id)
            if not episode:
                return False

            # バックアップから内容を復元
            backup_content = self._backups[project_id][episode_number][backup_version]
            episode.content = backup_content

            # 保存
            await self.save(episode, project_id)

            return True

        except Exception as e:
            msg = f"エピソード復元に失敗: {e}"
            raise RepositoryError(msg) from e

        # プライベートメソッド（テストユーティリティ）

    def _extract_episode_number_from_id(self, episode_id: str) -> int | None:
        """エピソードIDから番号を抽出（簡単な実装）"""
        import re
        match = re.search(r"episode_(\d+)", episode_id)
        return int(match.group(1)) if match else None

    def _copy_episode(self, episode: Episode) -> Episode:
        """エピソードのコピーを作成"""
        if not episode:
            return None

        # 新しいEpisodeエンティティの構造に合わせて修正
        return Episode(
            number=EpisodeNumber(episode.number.value),
            title=EpisodeTitle(episode.title.value),
            content=episode.content,
            target_words=WordCount(episode.target_words.value),
            status=episode.status,
            version=episode.version,
        )

    def _apply_query_filters(self, episodes: list[Episode], query: EpisodeQuery) -> list[Episode]:
        """クエリフィルターを適用"""
        filtered = episodes

        if query.episode_numbers:
            filtered = [ep for ep in filtered if ep.number.value in query.episode_numbers]

        if query.statuses:
            filtered = [ep for ep in filtered if ep.status.value in query.statuses]

        if query.min_word_count is not None:
            filtered = [ep for ep in filtered if ep.word_count.value >= query.min_word_count]

        if query.max_word_count is not None:
            filtered = [ep for ep in filtered if ep.word_count.value <= query.max_word_count]

        if query.min_quality_score is not None:
            filtered = [ep for ep in filtered if ep.quality_score.value >= query.min_quality_score]

        if query.max_quality_score is not None:
            filtered = [ep for ep in filtered if ep.quality_score.value <= query.max_quality_score]

        if query.created_after:
            filtered = [ep for ep in filtered if ep.created_at >= query.created_after]

        if query.created_before:
            filtered = [ep for ep in filtered if ep.created_at <= query.created_before]

        if query.updated_after:
            filtered = [ep for ep in filtered if ep.updated_at >= query.updated_after]

        if query.updated_before:
            filtered = [ep for ep in filtered if ep.updated_at <= query.updated_before]

        return filtered

    def _apply_query_sorting_and_pagination(self, episodes: list[Episode], query: EpisodeQuery) -> list[Episode]:
        """クエリソートとページネーションを適用"""
        # ソート
        if query.order_by == "episode_number":
            episodes.sort(key=lambda ep: ep.number.value, reverse=query.order_desc)
        elif query.order_by == "created_at":
            episodes.sort(key=lambda ep: ep.created_at, reverse=query.order_desc)
        elif query.order_by == "updated_at":
            episodes.sort(key=lambda ep: ep.updated_at, reverse=query.order_desc)
        elif query.order_by == "word_count":
            episodes.sort(key=lambda ep: ep.word_count.value, reverse=query.order_desc)
        elif query.order_by == "quality_score":
            episodes.sort(key=lambda ep: ep.quality_score.value, reverse=query.order_desc)

        # ページネーション
        start_idx = query.offset
        if query.limit is not None:
            end_idx = start_idx + query.limit
            episodes = episodes[start_idx:end_idx]
        else:
            episodes = episodes[start_idx:]

        return episodes

    # テストサポートメソッド

    def clear_all_data(self) -> None:
        """全データをクリア（テスト用）"""
        self._episodes.clear()
        self._backups.clear()
        self._next_episode_numbers.clear()

    def get_episode_count_by_project(self, project_id: str) -> int:
        """プロジェクトのエピソード数を取得（テスト用）"""
        return len(self._episodes.get(project_id, {}))

    def has_episode(self, project_id: str, episode_number: int) -> bool:
        """エピソードが存在するかチェック（テスト用）"""
        return (project_id in self._episodes and
                episode_number in self._episodes[project_id])
