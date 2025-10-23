"""遅延読み込み対応のリポジトリ実装"""

import re
from collections.abc import Callable, Iterator
from pathlib import Path

from noveler.domain.writing.entities import Episode
from noveler.domain.writing.value_objects import EpisodeNumber, PublicationStatus, WordCount, WritingPhase
from noveler.infrastructure.cache.yaml_cache import YAMLCache


class LazyEpisodeIterator:
    """エピソードの遅延読み込みイテレータ"""

    def __init__(
        self,
        episode_files: list[Path],
        project_id: str,
        loader_func: Callable[[Path, str], Episode | None],
        filter_func: Callable[[Episode], bool] | None = None,
    ) -> None:
        self.episode_files = episode_files
        self.project_id = project_id
        self.loader_func = loader_func
        self.filter_func = filter_func
        self.index = 0

    def __iter__(self) -> Iterator[Episode]:
        return self

    def __next__(self) -> Episode:
        while self.index < len(self.episode_files):
            file_path = self.episode_files[self.index]
            self.index += 1

            # エピソードを遅延読み込み
            episode = self.loader_func(file_path, self.project_id)

            if episode:
                # フィルタ適用
                if self.filter_func is None or self.filter_func(episode):
                    return episode

        raise StopIteration


class LazyLoadingEpisodeRepository:
    """遅延読み込み対応のエピソードリポジトリ"""

    def __init__(self, base_path: Path | str) -> None:
        self.base_path = base_path
        self._yaml_cache = YAMLCache()

    def find_all_lazy(self, project_id: str) -> Iterator[Episode]:
        """全エピソードを遅延読み込み"""
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        path_service = create_path_service(self.base_path / project_id)
        episodes_dir = path_service.get_manuscript_dir()

        if not episodes_dir.exists():
            return iter([])

        # ファイルリストを取得してソート
        episode_files = sorted(episodes_dir.glob("第*.md"))

        return LazyEpisodeIterator(
            episode_files,
            project_id,
            self._load_episode_from_file,
        )

    def find_by_phase_lazy(self, project_id: str, phase: WritingPhase) -> Iterator[Episode]:
        """フェーズ別にエピソードを遅延読み込み"""
        # メタデータを先読み
        metadata = self._load_all_metadata_cached(project_id)

        # 該当するエピソードファイルのみ取得
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        path_service = create_path_service(self.base_path / project_id)
        episodes_dir = path_service.get_manuscript_dir()
        if not episodes_dir.exists():
            return iter([])

        # メタデータでフィルタリング
        matching_files = []
        for episode_id, meta in metadata.items():
            if meta.get("phase") == phase.value:
                file_pattern = f"{episode_id}*.md"
                files = list(episodes_dir.glob(file_pattern))
                matching_files.extend(files)

        matching_files.sort()

        return LazyEpisodeIterator(
            matching_files,
            project_id,
            self._load_episode_from_file,
        )

    def find_recent_episodes_lazy(self, project_id: str, limit: int) -> Iterator[Episode]:
        """最近のエピソードを遅延読み込み"""
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        path_service = create_path_service(self.base_path / project_id)
        episodes_dir = path_service.get_manuscript_dir()

        if not episodes_dir.exists():
            return iter([])

        # 更新日時でソート(新しい順)
        episode_files = sorted(
            episodes_dir.glob("第*.md"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )[:limit]

        return LazyEpisodeIterator(
            episode_files,
            project_id,
            self._load_episode_from_file,
        )

    def process_episodes_in_batches(
        self, project_id: str, batch_size: int, processor: Callable[[list[Episode]], None] | None = None
    ) -> None:
        """エピソードをバッチ処理"""
        batch = []

        for episode in self.find_all_lazy(project_id):
            batch.append(episode)

            if len(batch) >= batch_size:
                if processor:
                    processor(batch)
                batch = []

        # 残りのバッチを処理
        if batch and processor:
            processor(batch)

    def _load_episode_from_file(self, file_path: Path, project_id: str) -> Episode | None:
        """ファイルからエピソードを読み込み(キャッシュ対応)"""
        try:
            # メタデータをキャッシュから取得
            metadata = self._load_episode_metadata_cached(
                project_id,
                file_path.stem,
            )

            # コンテンツのみ読み込み
            content = file_path.read_text(encoding="utf-8")

            # エピソード情報の解析

            filename = file_path.stem
            episode_number_match = re.match(r"第(\d+)話", filename)

            episode_number = None
            if episode_number_match:
                episode_number = EpisodeNumber(int(episode_number_match.group(1)))

            return Episode(
                id=file_path.stem,
                project_id=project_id,
                episode_number=episode_number,
                content=content,
                word_count=WordCount(len(content)),
                phase=metadata.get("phase", WritingPhase.DRAFT),
                publication_status=metadata.get(
                    "publication_status",
                    PublicationStatus.UNPUBLISHED,
                ),
            )

        except Exception:
            return None

    def _load_all_metadata_cached(self, project_id: str) -> dict[str, str | int]:
        """全メタデータをキャッシュ経由で読み込み"""
        metadata_file = self.base_path / project_id / "50_管理資料" / "episodes_metadata.yaml"
        return self._yaml_cache.get(metadata_file) or {}

    def _load_episode_metadata_cached(self, project_id: str, episode_id: str) -> dict[str, str | int]:
        """エピソードメタデータをキャッシュ経由で読み込み"""
        all_metadata = self._load_all_metadata_cached(project_id)
        metadata = all_metadata.get(episode_id, {})

        # Enumに変換
        if "phase" in metadata:
            metadata["phase"] = WritingPhase(metadata["phase"])
        if "publication_status" in metadata:
            metadata["publication_status"] = PublicationStatus(metadata["publication_status"])

        return metadata
