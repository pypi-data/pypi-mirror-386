"""YAMLファイルベースのエピソードリポジトリアダプター

SPEC-901-DDD-REFACTORING: Port & Adapter分離実装
Golden Sampleに基づくヘキサゴナルアーキテクチャパターン適用

このアダプターは新しいEpisodeRepositoryPortを実装し、
非同期処理とエラーハンドリングを含む完全なPort & Adapter分離を実現します。
"""

import asyncio
import re
from datetime import datetime
from pathlib import Path

import yaml

from noveler.domain.entities.episode import Episode, EpisodeStatus
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.episode_title import EpisodeTitle
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.value_objects.quality_score import QualityScore
from noveler.domain.value_objects.word_count import WordCount
from noveler.infrastructure.ports.repositories.episode_repository import (
    AdvancedEpisodeRepositoryPort,
    EpisodeQuery,
    EpisodeStatistics,
)


class RepositoryError(Exception):
    """リポジトリ操作エラー"""


class FileEpisodeRepositoryAdapter(AdvancedEpisodeRepositoryPort):
    """ファイルシステムベースのエピソードリポジトリアダプター

    SPEC-901に従い、Golden Sampleのパターンを適用：
    - 非同期処理サポート
    - 適切なエラーハンドリング
    - 責任の明確な分離
    """

    def __init__(self, project_root: str | Path, path_service=None) -> None:
        """初期化

        Args:
            project_root: プロジェクトルートパス
            path_service: パスサービス（依存性注入対応）
        """
        self.project_root = Path(project_root) if isinstance(project_root, str) else project_root

        # 依存性注入対応
        if path_service is None:
            from noveler.infrastructure.adapters.path_service_adapter import PathServiceAdapter
            path_service = PathServiceAdapter(self.project_root)

        self._path_service = path_service
        self.manuscript_dir = self._path_service.get_manuscript_dir()
        self.management_dir = self._path_service.get_management_dir()
        self._ensure_directories()

        # JSTタイムゾーン
        self._jst = ProjectTimezone.jst().timezone

    def _ensure_directories(self) -> None:
        """必要なディレクトリを作成"""
        try:
            self.manuscript_dir.mkdir(parents=True, exist_ok=True)
            self.management_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise RepositoryError(f"ディレクトリ作成に失敗: {e}") from e

    async def save(self, episode: Episode, project_id: str) -> None:
        """エピソードを非同期で保存

        Args:
            episode: 保存するエピソード
            project_id: プロジェクトID

        Raises:
            RepositoryError: 保存に失敗した場合
        """
        try:
            # Markdownファイルとして原稿を保存（共通基盤のパス解決に統一）
            manuscript_path = self._path_service.get_manuscript_path(episode.number.value)

            # 非同期でファイル書き込み
            def write_manuscript():
                # バッチ書き込みを使用
                Path(manuscript_path).write_text(episode.content, encoding="utf-8")

            await asyncio.to_thread(write_manuscript)

            # 話数管理YAMLを更新
            await self._update_episode_metadata(episode, project_id)

        except Exception as e:
            raise RepositoryError(f"エピソード保存に失敗: {e}") from e

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
            # エピソードIDから番号を抽出（実装は既存ロジックを使用）
            episode_number = self._extract_episode_number_from_id(episode_id)
            if episode_number is None:
                return None

            return await self.find_by_project_and_number(project_id, episode_number)

        except Exception as e:
            raise RepositoryError(f"エピソード検索に失敗: {e}") from e

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
            # メタデータファイルから情報を取得
            metadata = await self._load_episode_metadata(project_id, episode_number)
            if not metadata:
                return None

            # 原稿ファイルから内容を読み込み
            content = await self._load_episode_content(metadata.get("title", f"エピソード{episode_number}"), episode_number)

            # Episodeエンティティを構築
            return self._build_episode_from_data(metadata, content, episode_number)

        except Exception as e:
            raise RepositoryError(f"エピソード検索に失敗: {e}") from e

    async def find_all_by_project(self, project_id: str) -> list[Episode]:
        """プロジェクトの全エピソードを非同期取得

        Args:
            project_id: プロジェクトID

        Returns:
            list[Episode]: エピソードリスト

        Raises:
            RepositoryError: 検索に失敗した場合
        """
        try:
            episodes = []
            metadata_file = self._get_episode_management_file()

            if not metadata_file.exists():
                return episodes

            def load_metadata():
                with metadata_file.open("r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}

            all_metadata = await asyncio.to_thread(load_metadata)

            for episode_num_str, metadata in all_metadata.items():
                if episode_num_str.isdigit():
                    episode_number = int(episode_num_str)
                    episode = await self.find_by_project_and_number(project_id, episode_number)
                    if episode:
                        episodes.append(episode)

            return sorted(episodes, key=lambda ep: ep.number.value)

        except Exception as e:
            raise RepositoryError(f"全エピソード取得に失敗: {e}") from e

    async def find_by_status(self, project_id: str, status: str) -> list[Episode]:
        """ステータスでエピソードを非同期検索"""
        try:
            all_episodes = await self.find_all_by_project(project_id)
            return [ep for ep in all_episodes if ep.status.value == status]
        except Exception as e:
            raise RepositoryError(f"ステータス検索に失敗: {e}") from e

    async def find_by_date_range(self, project_id: str, start_date: datetime, end_date: datetime) -> list[Episode]:
        """日付範囲でエピソードを非同期検索"""
        try:
            all_episodes = await self.find_all_by_project(project_id)
            return [
                ep for ep in all_episodes
                if start_date <= ep.created_at <= end_date
            ]
        except Exception as e:
            raise RepositoryError(f"日付範囲検索に失敗: {e}") from e

    async def delete(self, episode_id: str, project_id: str) -> bool:
        """エピソードを非同期削除"""
        try:
            episode_number = self._extract_episode_number_from_id(episode_id)
            if episode_number is None:
                return False

            # メタデータから削除
            await self._remove_episode_metadata(project_id, episode_number)

            # 原稿ファイルを削除
            await self._remove_episode_file(episode_number)

            return True

        except Exception as e:
            raise RepositoryError(f"エピソード削除に失敗: {e}") from e

    async def get_next_episode_number(self, project_id: str) -> int:
        """次のエピソード番号を非同期取得"""
        try:
            all_episodes = await self.find_all_by_project(project_id)
            if not all_episodes:
                return 1
            return max(ep.number.value for ep in all_episodes) + 1
        except Exception as e:
            raise RepositoryError(f"次のエピソード番号取得に失敗: {e}") from e

    async def get_statistics(self, project_id: str) -> EpisodeStatistics:
        """エピソード統計情報を非同期取得"""
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
            raise RepositoryError(f"統計情報取得に失敗: {e}") from e

    async def find_by_query(self, query: EpisodeQuery) -> list[Episode]:
        """クエリでエピソードを非同期検索"""
        try:
            if not query.project_id:
                raise ValueError("project_idは必須です")

            all_episodes = await self.find_all_by_project(query.project_id)
            filtered_episodes = self._apply_query_filters(all_episodes, query)

            return self._apply_query_sorting_and_pagination(filtered_episodes, query)

        except Exception as e:
            raise RepositoryError(f"クエリ検索に失敗: {e}") from e

    async def count_by_query(self, query: EpisodeQuery) -> int:
        """クエリに該当するエピソード数を非同期取得"""
        try:
            episodes = await self.find_by_query(query)
            return len(episodes)
        except Exception as e:
            raise RepositoryError(f"クエリカウント取得に失敗: {e}") from e

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
            raise RepositoryError(f"一括ステータス更新に失敗: {e}") from e

    async def backup_episode(self, episode_id: str, project_id: str) -> bool:
        """エピソードを非同期バックアップ"""
        try:
            episode = await self.find_by_id(episode_id, project_id)
            if not episode:
                return False

            backup_path = self._get_backup_path(episode.number.value, episode.title.value)
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            def write_backup():
                # バッチ書き込みを使用
                backup_path.write_text(episode.content, encoding="utf-8")

            await asyncio.to_thread(write_backup)
            return True

        except Exception as e:
            raise RepositoryError(f"エピソードバックアップに失敗: {e}") from e

    async def restore_episode(self, episode_id: str, project_id: str, backup_version: str) -> bool:
        """エピソードをバックアップから非同期復元"""
        try:
            # 実装は簡略化（実際にはバックアップバージョン管理が必要）
            episode_number = self._extract_episode_number_from_id(episode_id)
            if episode_number is None:
                return False

            backup_path = self._get_backup_path(episode_number, f"episode_{episode_number}")
            if not backup_path.exists():
                return False

            def read_backup():
                with backup_path.open("r", encoding="utf-8") as f:
                    return f.read()

            content = await asyncio.to_thread(read_backup)

            # 現在のエピソードを更新
            episode = await self.find_by_id(episode_id, project_id)
            if episode:
                episode.content = content
                await self.save(episode, project_id)
                return True

            return False

        except Exception as e:
            raise RepositoryError(f"エピソード復元に失敗: {e}") from e

    # プライベートメソッド（実装サポート）

    # 旧実装の互換メソッドは削除済み（PathService.get_manuscript_path へ統一）

    def _get_episode_management_file(self) -> Path:
        """エピソード管理YAMLファイルパスを取得"""
        return self.management_dir / "episodes.yaml"

    def _get_backup_path(self, episode_number: int, title: str) -> Path:
        """バックアップファイルパスを取得"""
        safe_title = re.sub(r"[^\w\-_\.]", "_", title)
        filename = f"{episode_number:03d}_{safe_title}_backup.md"
        backup_dir = self.project_root / "backups" / "episodes"
        return backup_dir / filename

    def _extract_episode_number_from_id(self, episode_id: str) -> int | None:
        """エピソードIDから番号を抽出"""
        # 簡単な実装（実際はより複雑なID管理が必要）
        match = re.search(r"episode_(\d+)", episode_id)
        return int(match.group(1)) if match else None

    async def _update_episode_metadata(self, episode: Episode, project_id: str) -> None:
        """エピソードメタデータを更新"""
        metadata_file = self._get_episode_management_file()

        def update_metadata():
            if metadata_file.exists():
                with metadata_file.open("r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
            else:
                data = {}

            data[str(episode.number.value)] = {
                "title": episode.title.value,
                "status": episode.status.value,
                "word_count": episode.word_count.value,
                "quality_score": episode.quality_score.value,
                "created_at": episode.created_at.isoformat(),
                "updated_at": episode.updated_at.isoformat(),
                "project_id": project_id,
            }

            with metadata_file.open("w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        await asyncio.to_thread(update_metadata)

    async def _load_episode_metadata(self, project_id: str, episode_number: int) -> dict | None:
        """エピソードメタデータを読み込み"""
        metadata_file = self._get_episode_management_file()

        if not metadata_file.exists():
            return None

        def load_metadata():
            with metadata_file.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return data.get(str(episode_number))

        return await asyncio.to_thread(load_metadata)

    async def _load_episode_content(self, title: str, episode_number: int) -> str:
        """エピソード内容を読み込み"""
        manuscript_path = self._path_service.get_manuscript_path(episode_number)

        if not manuscript_path.exists():
            return ""

        def read_content():
            with manuscript_path.open("r", encoding="utf-8") as f:
                return f.read()

        return await asyncio.to_thread(read_content)

    def _build_episode_from_data(self, metadata: dict, content: str, episode_number: int) -> Episode:
        """データからEpisodeエンティティを構築"""
        return Episode(
            number=EpisodeNumber(episode_number),
            title=EpisodeTitle(metadata.get("title", f"エピソード{episode_number}")),
            content=content,
            status=EpisodeStatus(metadata.get("status", "draft")),
            word_count=WordCount(metadata.get("word_count", len(content))),
            quality_score=QualityScore(metadata.get("quality_score", 0.0)),
            created_at=datetime.fromisoformat(metadata.get("created_at", project_now().isoformat())),
            updated_at=datetime.fromisoformat(metadata.get("updated_at", project_now().isoformat())),
        )

    async def _remove_episode_metadata(self, project_id: str, episode_number: int) -> None:
        """エピソードメタデータを削除"""
        metadata_file = self._get_episode_management_file()

        def remove_metadata():
            if metadata_file.exists():
                with metadata_file.open("r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}

                if str(episode_number) in data:
                    del data[str(episode_number)]

                with metadata_file.open("w", encoding="utf-8") as f:
                    yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        await asyncio.to_thread(remove_metadata)

    async def _remove_episode_file(self, episode_number: int) -> None:
        """エピソードファイルを削除（共通基盤のパス解決）"""
        target = self._path_service.get_manuscript_path(episode_number)
        if target.exists():
            def remove_file():
                target.unlink()
            await asyncio.to_thread(remove_file)

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
