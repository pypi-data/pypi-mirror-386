"""ファイルベースのエピソードリポジトリ実装"""

import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

from noveler.domain.writing.entities import Episode
from noveler.domain.writing.repositories import EpisodeRepository
from noveler.domain.writing.value_objects import EpisodeNumber, EpisodeTitle, PublicationStatus, WordCount, WritingPhase


class FileEpisodeRepository(EpisodeRepository):
    """ファイルシステムを使用したエピソードリポジトリ実装"""

    def __init__(self, base_path: Path | str) -> None:
        self.base_path = base_path

    def find_by_id(self, episode_id: str) -> Episode | None:
        """IDでエピソードを取得"""
        # 実装の簡略化のため、episode_idをファイル名として扱う
        for project_path in self.base_path.iterdir():
            if not project_path.is_dir():
                continue

            from noveler.infrastructure.adapters.path_service_adapter import create_path_service

            path_service = create_path_service(project_path)
            episodes_dir = path_service.get_manuscript_dir()

            if not episodes_dir.exists():
                continue

            for episode_file in episodes_dir.glob("*.md"):
                if episode_id in str(episode_file):
                    return self._load_episode_from_file(episode_file, project_path.name)

        return None

    def find_by_number(self, project_id: str, episode_number: int) -> Episode | None:
        """プロジェクトと話数でエピソードを取得"""
        # base_pathがプロジェクトディレクトリ自体の場合も考慮
        project_path = self.base_path if self.base_path.name == project_id else self.base_path / project_id
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        path_service = create_path_service(project_path)
        episodes_dir = path_service.get_manuscript_dir()

        # パターン探索を優先（タイトル付きのファイルも見つけられるように）
        if episodes_dir.exists():
            pattern = f"第{episode_number:03d}話*.md"
            matching_files = list(episodes_dir.glob(pattern))
            if matching_files:
                return self._load_episode_from_file(matching_files[0], project_id)

        # フォールバック: PathServiceで原稿パスを取得
        manuscript_file = path_service.get_manuscript_path(episode_number)
        if manuscript_file.exists():
            return self._load_episode_from_file(manuscript_file, project_id)

        return None

    def find_all_by_project(self, project_id: str) -> list[Episode]:
        """プロジェクトの全エピソードを取得"""
        project_path = self.base_path / project_id
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        path_service = create_path_service(project_path)
        episodes_dir = path_service.get_manuscript_dir()

        if not episodes_dir.exists():
            return []

        episodes = []
        for episode_file in sorted(episodes_dir.glob("第*.md")):
            episode = self._load_episode_from_file(episode_file, project_id)
            if episode:
                episodes.append(episode)

        return episodes

    def find_by_phase(self, project_id: str, phase: WritingPhase) -> list[Episode]:
        """フェーズ別にエピソードを取得"""
        # メタデータから読み込む必要があるが、簡略化のため全エピソードから絞り込む
        all_episodes = self.find_all_by_project(project_id)
        return [ep for ep in all_episodes if ep.phase == phase]

    def find_by_publication_status(self, project_id: str, status: PublicationStatus) -> list[Episode]:
        """公開ステータス別にエピソードを取得"""
        all_episodes = self.find_all_by_project(project_id)
        return [ep for ep in all_episodes if ep.publication_status == status]

    def find_latest_episode(self, project_id: str) -> Episode | None:
        """最新のエピソードを取得"""
        episodes = self.find_all_by_project(project_id)
        if not episodes:
            return None

        # 話数で最新を判定
        return max(episodes, key=lambda ep: ep.episode_number)

    def save(self, episode: Episode) -> Episode:
        """エピソードを保存"""
        project_path = self.base_path / episode.project_id
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        path_service = create_path_service(project_path)
        # B20準拠: PathServiceで原稿パスを一元解決
        if episode.episode_number:
            num = episode.episode_number.value if hasattr(episode.episode_number, "value") else int(episode.episode_number)
            # タイトルがある場合はファイル名に含める
            episodes_dir = path_service.get_manuscript_dir()
            episodes_dir.mkdir(parents=True, exist_ok=True)
            if episode.title:
                title_value = episode.title.value if hasattr(episode.title, "value") else str(episode.title)
                file_path = episodes_dir / f"第{num:03d}話_{title_value}.md"
            else:
                file_path = path_service.get_manuscript_path(num)
            file_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            # エピソード番号が無い場合のみフォールバック（稀ケース）
            episodes_dir = path_service.get_manuscript_dir()
            episodes_dir.mkdir(parents=True, exist_ok=True)
            file_path = episodes_dir / f"episode_{episode.id}.md"

        # コンテンツの保存
        # バッチ書き込みを使用
        Path(file_path).write_text(episode.content, encoding="utf-8")

        # メタデータの保存
        self._save_episode_metadata(episode, project_path)

        return episode

    def delete(self, episode_id: str) -> None:
        """エピソードを削除"""
        episode = self.find_by_id(episode_id)
        if not episode:
            return

        project_path = self.base_path / episode.project_id
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        path_service = create_path_service(project_path)
        episodes_dir = path_service.get_manuscript_dir()

        # ファイルを削除
        for episode_file in episodes_dir.glob("*.md"):
            if episode_id in str(episode_file):
                episode_file.unlink()
                break

    def _load_episode_from_file(self, file_path: Path, project_id: str) -> Episode | None:
        """ファイルからエピソードを読み込み"""
        try:
            # コンテンツの読み込み
            # ファイル読み込み
            content = Path(file_path).read_text(encoding="utf-8")

            # ファイル名から情報を抽出
            filename = file_path.stem
            episode_number_match = re.match(r"第(\d+)話", filename)

            episode_number = None
            if episode_number_match:
                episode_number = EpisodeNumber(int(episode_number_match.group(1)))

            # タイトルの抽出
            title_match = re.search(r"第\d+話_(.+)", filename)
            title = None
            if title_match:
                title = EpisodeTitle(title_match.group(1))

            # メタデータの読み込み
            metadata = self._load_episode_metadata(project_id, file_path.stem)

            # メタデータからタイトルを取得（ファイル名から取得できなかった場合）
            if not title and "title" in metadata:
                title = EpisodeTitle(metadata["title"])
            # それでもタイトルがない場合はデフォルト
            if not title:
                title = EpisodeTitle("無題")

            return Episode(
                id=file_path.stem,
                project_id=project_id,
                episode_number=episode_number,
                title=title,
                content=content,
                word_count=WordCount.from_japanese_text(content),
                phase=metadata.get("phase", WritingPhase.DRAFT),
                publication_status=metadata.get("publication_status", PublicationStatus.UNPUBLISHED),
                created_at=metadata.get(
                    "created_at", datetime.fromtimestamp(file_path.stat().st_ctime, tz=timezone.utc)
                ),
                updated_at=metadata.get(
                    "updated_at", datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
                ),
                published_at=metadata.get("published_at"),
            )

        except Exception:
            return None

    def _save_episode_metadata(self, episode: Episode, project_path: Path) -> None:
        """エピソードのメタデータを保存"""
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        path_service = create_path_service(project_path)
        metadata_dir = path_service.get_management_dir()
        metadata_dir.mkdir(parents=True, exist_ok=True)

        metadata_file = metadata_dir / "episodes_metadata.yaml"

        # 既存のメタデータを読み込み
        metadata = {}
        if metadata_file.exists():
            with Path(metadata_file).open(encoding="utf-8") as f:
                metadata = yaml.safe_load(f) or {}

        # エピソードのメタデータを更新
        metadata[episode.id] = {
            "title": episode.title.value if episode.title else "無題",
            "phase": episode.phase.value,
            "publication_status": episode.publication_status.value,
            "created_at": episode.created_at,
            "updated_at": episode.updated_at,
            "published_at": episode.published_at,
        }

        # 保存
        with Path(metadata_file).open("w", encoding="utf-8") as f:
            yaml.dump(metadata, f, allow_unicode=True, default_flow_style=False)

    def _load_episode_metadata(self, project_id: str, episode_id: str) -> dict[str, str | int]:
        """エピソードのメタデータを読み込み"""
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        path_service = create_path_service(self.base_path / project_id)
        metadata_file = path_service.get_management_dir() / "episodes_metadata.yaml"

        if not metadata_file.exists():
            return {}

        try:
            with Path(metadata_file).open(encoding="utf-8") as f:
                all_metadata = yaml.safe_load(f) or {}
                metadata = all_metadata.get(episode_id, {})

                # Enumに変換
                if "phase" in metadata:
                    metadata["phase"] = WritingPhase(metadata["phase"])
                if "publication_status" in metadata:
                    metadata["publication_status"] = PublicationStatus(metadata["publication_status"])

                return metadata
        except Exception:
            return {}
