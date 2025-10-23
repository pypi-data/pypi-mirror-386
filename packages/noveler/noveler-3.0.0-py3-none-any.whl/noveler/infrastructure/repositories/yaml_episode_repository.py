"""YAMLベースのエピソードリポジトリ実装

DDD原則に基づき、インフラストラクチャ層でのエピソード永続化を実装
"""

import re
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.entities.episode import Episode, EpisodeStatus
from noveler.domain.repositories.episode_repository import EpisodeRepository
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.episode_title import EpisodeTitle
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.value_objects.quality_score import QualityScore
from noveler.domain.value_objects.word_count import WordCount
from noveler.infrastructure.utils.yaml_utils import YAMLHandler

# パフォーマンス最適化統合
try:
    from noveler.infrastructure.performance.comprehensive_performance_optimizer import performance_monitor
except ImportError:
    # パフォーマンス監視が利用不可の場合のフォールバック
    def performance_monitor(_name: str):
        """パフォーマンス監視デコレータ（フォールバック）"""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return func

        return decorator


# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


from noveler.domain.interfaces.i_path_service import IPathService


class YamlEpisodeRepository(EpisodeRepository):
    """YAMLファイルベースのエピソードリポジトリ実装"""

    def __init__(self, project_root: str | Path, path_service: IPathService | None = None) -> None:
        """初期化

        Args:
            project_root: プロジェクトルートパス
            path_service: パスサービス（Noneの場合はPathServiceAdapterを自動生成）
        """
        self.project_root = Path(project_root) if isinstance(project_root, str) else project_root

        # IPathServiceインターフェースを使用
        if path_service is None:
            from noveler.infrastructure.adapters.path_service_adapter import PathServiceAdapter

            path_service = PathServiceAdapter(self.project_root)

        self._path_service = path_service
        self.manuscript_dir = self._path_service.get_manuscript_dir()
        self.management_dir = self._path_service.get_management_dir()
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """必要なディレクトリを作成"""
        self.manuscript_dir.mkdir(parents=True, exist_ok=True)
        self.management_dir.mkdir(parents=True, exist_ok=True)

    @performance_monitor("YamlEpisodeRepository.save")
    def save(self, episode: Episode, _project_id: str) -> None:
        """エピソードを保存"""
        # Markdownファイルとして原稿を保存（共通基盤のパス解決に統一）
        manuscript_path = self.manuscript_dir / self._build_manuscript_filename(
            episode.number.value, episode.title.value
        )
        # バッチ書き込みを使用
        Path(manuscript_path).write_text(episode.content, encoding="utf-8")

        # 話数管理YAMLを更新
        self._update_episode_management(_project_id, episode)

    @performance_monitor("YamlEpisodeRepository.find_by_number")
    def find_by_number(self, _project_id: str, number: int | EpisodeNumber) -> Episode | None:
        """エピソード番号で検索"""
        # 話数管理YAMLから情報を取得
        management_data: dict[str, Any] = self._load_episode_management()

        episode_number = number.value if isinstance(number, EpisodeNumber) else number

        episodes_list = management_data.get("episodes", [])
        episode_data: dict[str, Any] | None = None
        for item in episodes_list:
            if item.get("number") == episode_number:
                episode_data = item
                break

        if episode_data is not None:

            # 原稿ファイルを読み込み（共通基盤のパス解決に統一）
            manuscript_path = self.manuscript_dir / self._build_manuscript_filename(
                episode_number, episode_data["title"]
            )

            if not manuscript_path.exists():
                return None

            manuscript_content = Path(manuscript_path).read_text(encoding="utf-8")

            # エピソードエンティティを再構築
            episode = Episode(
                number=EpisodeNumber(episode_number),
                title=EpisodeTitle(episode_data["title"]),
                content=manuscript_content,
                target_words=WordCount(episode_data.get("target_words", 3000)),
            )

            # ステータスを復元
            status_str = episode_data.get("status", "DRAFT")
            episode.status = EpisodeStatus[status_str]

            # その他の属性を復元
            if episode_data.get("quality_score") is not None:
                episode.set_quality_score(QualityScore(int(episode_data["quality_score"])))

            if episode_data.get("created_at"):
                episode.created_at = datetime.fromisoformat(episode_data["created_at"])

            if episode_data.get("completed_at"):
                episode.completed_at = datetime.fromisoformat(episode_data["completed_at"])

            episode.version = episode_data.get("version", 1)

            return episode

        return None

    @performance_monitor("YamlEpisodeRepository.find_all")
    def find_all(self, _project_id: str) -> list[Episode]:
        """すべてのエピソードを取得"""
        management_data: dict[str, Any] = self._load_episode_management()
        episodes = []

        for episode_data in management_data.get("episodes", []):
            episode = self.find_by_number(
                _project_id,
                EpisodeNumber(episode_data["number"]),
            )

            if episode:
                episodes.append(episode)

        return episodes

    @performance_monitor("YamlEpisodeRepository.exists")
    def exists(self, _project_id: str, number: int | EpisodeNumber) -> bool:
        """エピソードの存在確認"""
        return self.find_by_number(_project_id, number) is not None

    @performance_monitor("YamlEpisodeRepository.get_next_episode_number")
    def get_next_episode_number(self, _project_id: str) -> int:
        """次のエピソード番号を取得"""
        management_data: dict[str, Any] = self._load_episode_management()
        episodes = management_data.get("episodes", [])

        if not episodes:
            return 1

        max_number = max(ep["number"] for ep in episodes)
        return max_number + 1

    # 旧実装の互換メソッドは削除済み（PathService.get_manuscript_path へ統一）

    def _load_episode_management(self) -> dict[str, Any]:
        """話数管理YAMLを読み込み"""
        path = self.management_dir / "話数管理.yaml"

        if not path.exists():
            return {"episodes": []}

        with Path(path).open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {"episodes": []}

    def _save_episode_management(self, data: dict[str, Any]) -> None:
        """話数管理YAMLを保存"""
        path = self.management_dir / "話数管理.yaml"

        # YAMLHandlerを使用して整形付き保存を試みる
        try:
            YAMLHandler.save_yaml(path, data, use_formatter=True)
        except (ImportError, Exception):
            # フォールバック: 従来の方法で保存
            with Path(path).open("w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

    def _update_episode_management(self, _project_id: str, episode: Episode) -> None:
        """話数管理YAMLを更新"""
        data = self._load_episode_management()
        episodes = data.get("episodes", [])

        # 既存エピソードを探す
        found = False
        for i, ep_data in enumerate(episodes):
            if ep_data["number"] == episode.number.value:
                episodes[i] = self._episode_to_dict(episode)
                found = True
                break

        # 新規エピソードの場合は追加
        if not found:
            episodes.append(self._episode_to_dict(episode))

        # 番号順にソート（管理データのキーは number）
        episodes.sort(key=lambda x: x.get("number", 0))

        data["episodes"] = episodes
        data["updated_at"] = self._format_datetime(project_now().datetime)

        self._save_episode_management(data)

    def _episode_to_dict(self, episode: Episode) -> dict[str, Any]:
        """エピソードを辞書形式に変換"""
        created_at = self._format_datetime(getattr(episode, "created_at", None))
        completed_at = self._format_datetime(getattr(episode, "completed_at", None))
        updated_at = self._format_datetime(project_now().datetime)

        return {
            "number": episode.number.value,
            "title": episode.title.value,
            "status": episode.status.name,
            "word_count": episode.word_count.value,
            "target_words": episode.target_words.value,
            "version": episode.version,
            "quality_score": episode.quality_score.value if episode.quality_score else None,
            "created_at": created_at,
            "completed_at": completed_at,
            "updated_at": updated_at,
        }

    def _build_manuscript_filename(self, episode_number: int, title: str) -> str:
        """原稿ファイル名を生成"""
        safe_title = re.sub(r"[\\/:*?\"<>|]", "", title).strip() or "無題"
        return f"第{episode_number:03d}話_{safe_title}.md"

    def _format_datetime(self, value: datetime | None) -> str | None:
        """datetimeをISO形式に整形（タイムゾーン情報を除外）"""
        if value is None:
            return None
        dt = value
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt.isoformat()

    def update_status(self, episode_file: Path, status: str) -> None:
        """エピソードのステータスを簡易更新(テスト用)"""
        # 話数管理YAMLを読み込み
        self.management_dir / "話数管理.yaml"
        data = self._load_episode_management()

        # エピソードを検索
        episode_name = episode_file.stem
        for ep_data in data.get("episodes", []):
            if f"第{ep_data['number']:03d}話_{ep_data['title']}" == episode_name:
                ep_data["status"] = status
                ep_data["updated_at"] = project_now().datetime.isoformat()
                break

        # 保存
        self._save_episode_management(data)

    # 以下、抽象メソッドの実装を追加
    def find_by_id(self, episode_id: str, project_id: str) -> Episode | None:
        """IDでエピソードを検索(エピソード番号をIDとして使用)"""
        try:
            episode_number = int(episode_id)
            return self.find_by_project_and_number(project_id, episode_number)
        except ValueError:
            return None

    def find_by_project_and_number(self, project_id: str, episode_number: int) -> Episode | None:
        """プロジェクトIDとエピソード番号でエピソードを検索"""
        return self.find_by_number(project_id, EpisodeNumber(episode_number))

    def find_all_by_project(self, project_id: str) -> list[Episode]:
        """プロジェクトの全エピソードを取得"""
        return self.find_all(project_id)

    def find_by_status(self, project_id: str, status: str | EpisodeStatus) -> list[Episode]:
        """ステータスでエピソードを検索"""
        all_episodes = self.find_all(project_id)
        status_name = status.name if isinstance(status, EpisodeStatus) else status
        return [ep for ep in all_episodes if ep.status.name == status_name]

    def find_by_date_range(self, project_id: str, start_date: datetime, end_date: datetime) -> list[Episode]:
        """日付範囲でエピソードを検索"""
        all_episodes = self.find_all(project_id)
        return [ep for ep in all_episodes if ep.created_at and start_date <= ep.created_at <= end_date]

    def delete(self, episode_id: str, project_id: str) -> bool:
        """エピソードをIDで削除"""
        try:
            episode_number = int(episode_id)
            self.delete_by_number(project_id, EpisodeNumber(episode_number))
            return True
        except (ValueError, Exception):
            return False

    def delete_by_number(self, _project_id: str, number: EpisodeNumber) -> None:
        """エピソードを番号で削除(内部使用)"""
        # 話数管理から削除
        management_data: dict[str, Any] = self._load_episode_management()
        episodes = management_data.get("episodes", [])

        # 該当エピソードを探して削除
        for i, episode_data in enumerate(episodes):
            if episode_data["number"] == number.value:
                manuscript_path = self.manuscript_dir / self._build_manuscript_filename(
                    episode_data["number"], episode_data.get("title", "")
                )

                if manuscript_path.exists():
                    manuscript_path.unlink()

                episodes.pop(i)
                break

        # 更新を保存
        management_data["episodes"] = episodes
        self._save_episode_management(management_data)

    def get_episode_count(self, _project_id: str) -> int:
        """エピソード数を取得"""
        management_data: dict[str, Any] = self._load_episode_management()
        return len(management_data.get("episodes", []))

    def get_total_word_count(self, _project_id: str) -> int:
        """総文字数を取得"""
        management_data: dict[str, Any] = self._load_episode_management()
        total = 0
        for ep_data in management_data.get("episodes", []):
            total += ep_data.get("word_count", 0)
        return total

    def find_by_tags(self, project_id: str, tags: list[str]) -> list[Episode]:
        """タグでエピソードを検索"""
        all_episodes = self.find_all(project_id)
        return [ep for ep in all_episodes if any(tag in ep.tags for tag in tags)]

    def find_by_quality_score_range(self, project_id: str, min_score: float, max_score: float) -> list[Episode]:
        """品質スコア範囲でエピソードを検索"""
        all_episodes = self.find_all(project_id)
        return [ep for ep in all_episodes if ep.quality_score and min_score <= ep.quality_score.value <= max_score]

    def find_ready_for_publication(self, project_id: str) -> list[Episode]:
        """公開準備完了のエピソードを取得"""
        all_episodes = self.find_all(project_id)
        return [ep for ep in all_episodes if ep.can_publish()]

    def get_statistics(self, project_id: str) -> dict[str, Any]:
        """エピソード統計情報を取得"""
        all_episodes = self.find_all(project_id)

        status_counts = {}
        for ep in all_episodes:
            status = ep.status.name
            status_counts[status] = status_counts.get(status, 0) + 1

        quality_scores = [ep.quality_score.value for ep in all_episodes if ep.quality_score]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

        return {
            "total_episodes": len(all_episodes),
            "total_word_count": sum(ep.calculate_word_count() for ep in all_episodes),
            "status_distribution": status_counts,
            "average_quality_score": avg_quality,
            "publishable_count": len([ep for ep in all_episodes if ep.can_publish()]),
        }

    def bulk_update_status(self, project_id: str, episode_ids: list[str], new_status: str) -> int:
        """複数エピソードのステータスを一括更新"""
        count = 0
        for episode_id in episode_ids:
            episode = self.find_by_id(episode_id, project_id)
            if episode:
                episode.status = EpisodeStatus[new_status]
                self.save(episode, project_id)
                count += 1
        return count

    def backup_episode(self, episode_id: str, project_id: str) -> bool:
        """エピソードをバックアップ"""
        episode = self.find_by_id(episode_id, project_id)
        if not episode:
            return False

        backup_dir = self.project_root / "backup" / project_now().datetime.strftime("%Y%m%d_%H%M%S")
        backup_dir.mkdir(parents=True, exist_ok=True)

        # 原稿ファイルのバックアップ
        manuscript_path = self._path_service.get_manuscript_path(episode.number.value)
        if manuscript_path.exists():
            backup_path = backup_dir / manuscript_path.name
            backup_path.write_text(manuscript_path.read_text(encoding="utf-8"), encoding="utf-8")

        # メタデータのバックアップ
        metadata_path = backup_dir / f"episode_{episode_id}_metadata.yaml"
        with Path(metadata_path).open("w", encoding="utf-8") as f:
            yaml.dump(self._episode_to_dict(episode), f, allow_unicode=True)

        return True

    def restore_episode(self, episode_id: str, project_id: str, backup_version: str) -> bool:
        """エピソードをバックアップから復元"""
        backup_dir = self.project_root / "backup" / backup_version
        if not backup_dir.exists():
            return False

        # メタデータの復元
        metadata_path = backup_dir / f"episode_{episode_id}_metadata.yaml"
        if not metadata_path.exists():
            return False

        with Path(metadata_path).open(encoding="utf-8") as f:
            episode_data: dict[str, Any] = yaml.safe_load(f)

        # 原稿ファイルの復元
        manuscript_filename = self._path_service.get_manuscript_path(episode_data['number']).name
        backup_manuscript = backup_dir / manuscript_filename
        if backup_manuscript.exists():
            content = backup_manuscript.read_text(encoding="utf-8")

            # エピソードエンティティの再構築
            episode = Episode(
                number=EpisodeNumber(episode_data["number"]),
                title=EpisodeTitle(episode_data["title"]),
                content=content,
                target_words=WordCount(episode_data.get("target_words", 3000)),
            )

            # 保存
            self.save(episode, project_id)
            return True

        return False

    def get_all_episodes(self, _project_name: str) -> list[dict[str, Any]]:
        """プロジェクトの全エピソード情報を取得"""
        data = self._load_episode_management()
        episodes_data: dict[str, Any] = data.get("episodes", [])

        # 辞書形式(episode_001: {...})の場合をリスト形式に変換
        if isinstance(episodes_data, dict):
            episodes_list = []
            for episode_key, episode_info in episodes_data.items():
                # エピソード番号を抽出(episode_001 → 1)
                episode_number = self._extract_episode_number_from_key(episode_key)
                if episode_number is not None:
                    episode_dict = episode_info.copy()
                    episode_dict["number"] = episode_number
                    # タイトルが設定されていない場合はエピソードキーから取得
                    if "title" not in episode_dict:
                        episode_dict["title"] = episode_info.get("title", episode_key)
                    episodes_list.append(episode_dict)
            return sorted(episodes_list, key=lambda x: x.get("number", 0))

        # 既存のリスト形式はそのまま返す
        return episodes_data

    def _extract_episode_number(self, episode_key: str) -> int | None:
        """エピソードキーから番号を抽出(第001話 → 1)"""

        match = re.match(r"第(\d+)話", episode_key)
        if match:
            return int(match.group(1))
        return None

    def _extract_episode_number_from_key(self, episode_key: str) -> int | None:
        """エピソードキーから番号を抽出(episode_001 → 1)"""
        import re


        # episode_001形式のパターンマッチング
        match = re.match(r"episode_(\d+)", episode_key)
        if match:
            return int(match.group(1))

        # 従来の第001話形式もサポート
        match = re.match(r"第(\d+)話", episode_key)
        if match:
            return int(match.group(1))

        return None

    def _find_actual_episode_file(self, episode_number: int) -> Path | None:
        """実際のエピソードファイルを検索

        Args:
            episode_number: エピソード番号

        Returns:
            Path | None: 見つかったファイルパス、見つからない場合はNone
        """
        if not self.manuscript_dir.exists():
            return None

        # パターン: 第{number:03d}話_*.md
        pattern = f"第{episode_number:03d}話_*.md"

        matching_files = list(self.manuscript_dir.glob(pattern))
        if matching_files:
            return matching_files[0]

        return None

    def get_episode_info(self, _project_name: str, episode_number: int) -> dict[str, Any] | None:
        """エピソード情報を取得"""
        episodes = self.get_all_episodes(_project_name)
        for ep in episodes:
            if ep.get("number") == episode_number:
                return ep
        return None

    def get_episodes_in_range(self, project_name: str, start_episode: int, end_episode: int) -> list[dict[str, Any]]:
        """範囲指定でエピソード情報を取得"""
        episodes = self.get_all_episodes(project_name)
        return [ep for ep in episodes if start_episode <= ep.get("number", 0) <= end_episode]

    def get_latest_episode(self, project_name: str) -> dict[str, Any] | None:
        """最新のエピソード情報を取得"""
        episodes = self.get_all_episodes(project_name)
        if not episodes:
            return None
        return max(episodes, key=lambda x: x.get("number", 0))

    def update_content(self, project_name: str, episode_number: int, new_content: str) -> None:
        """エピソードの内容を更新"""
        episode_info = self.get_episode_info(project_name, episode_number)
        if episode_info:
            manuscript_path = self._path_service.get_manuscript_path(episode_number)
            # バッチ書き込みを使用
            Path(manuscript_path).write_text(new_content, encoding="utf-8")

    def update_phase(self, _project_name: str, episode_number: int, new_phase: str) -> None:
        """エピソードのフェーズを更新"""
        data = self._load_episode_management()
        episodes = data.get("episodes", [])

        for ep in episodes:
            if ep.get("number") == episode_number:
                ep["phase"] = str(new_phase)
                break

        data["episodes"] = episodes
        self._save_episode_management(data)

    def get_episode_content(self, project_name: str, episode_number: int) -> str:
        """エピソードの内容を取得

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号

        Returns:
            str: エピソードの内容

        Raises:
            FileNotFoundError: エピソードが見つからない場合
        """
        # 共通基盤のパス解決を優先
        manuscript_path = self._path_service.get_manuscript_path(episode_number)
        if manuscript_path.exists():
            with manuscript_path.open("r", encoding="utf-8") as f:
                return f.read()

        # フォールバック: 実際のファイルを検索（命名のズレに対応）
        actual_file_path = self._find_actual_episode_file(episode_number)
        if actual_file_path and actual_file_path.exists():
            with actual_file_path.open("r", encoding="utf-8") as f:
                return f.read()

        msg = f"エピソード {episode_number} の原稿が見つかりません"
        raise FileNotFoundError(msg)

    def save_episode_content(self, target_file: Path, content: str) -> None:
        """エピソード内容をファイルに保存

        Args:
            target_file: 保存先ファイルパス
            content: 保存する内容

        Raises:
            OSError: ファイル保存に失敗した場合
        """
        try:
            # ディレクトリが存在しない場合は作成
            target_file.parent.mkdir(parents=True, exist_ok=True)

            with target_file.Path("w").open(encoding="utf-8") as f:
                f.write(content)
        except OSError as e:
            msg = f"エピソード内容の保存に失敗しました: {e}"
            raise OSError(msg) from e

    def update_episode_content(self, project_name: str, episode_number: int, new_content: str) -> None:
        """エピソード内容の更新(自動修正用)

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号
            new_content: 新しい内容

        Raises:
            FileNotFoundError: エピソードファイルが見つからない場合
        """
        # 既存のエピソード情報を取得
        episodes = self.get_all_episodes(project_name)
        target_episode = None

        for episode in episodes:
            if episode.get("number") == episode_number:
                target_episode = episode
                break

        if not target_episode:
            msg = f"エピソード {episode_number} が見つかりません"
            raise FileNotFoundError(msg)

        # エピソードファイルのパスを共通基盤で構築
        episode_file_path = self._path_service.get_manuscript_path(episode_number)

        # ファイルの存在確認
        if not episode_file_path.exists():
            msg = f"エピソードファイルが見つかりません: {episode_file_path}"
            raise FileNotFoundError(msg)

        # 内容を更新
        episode_file_path.write_text(new_content, encoding="utf-8")
