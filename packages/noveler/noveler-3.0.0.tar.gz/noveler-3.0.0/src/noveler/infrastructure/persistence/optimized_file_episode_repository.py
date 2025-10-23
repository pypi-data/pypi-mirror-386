"""最適化されたファイルベースのエピソードリポジトリ実装"""

import re
from pathlib import Path
from threading import Lock

import yaml

from noveler.domain.writing.entities import Episode
from noveler.domain.writing.repositories import EpisodeRepository
from noveler.domain.writing.value_objects import EpisodeNumber, EpisodeTitle, PublicationStatus, WordCount, WritingPhase
from noveler.infrastructure.cache.yaml_cache import YAMLCache


class OptimizedFileEpisodeRepository(EpisodeRepository):
    """パフォーマンス最適化されたファイルシステムエピソードリポジトリ"""

    def __init__(self, base_path: Path | str) -> None:
        self.base_path = base_path
        self._episode_index: dict[str, tuple[str, Path]] = {}
        self._metadata_cache = YAMLCache()
        self._index_lock = Lock()
        self._build_index()

    def _build_index(self) -> None:
        """起動時に全エピソードのインデックスを構築"""
        with self._index_lock:
            self._episode_index.clear()

            for project_path in self.base_path.iterdir():
                if not project_path.is_dir():
                    continue

                from noveler.infrastructure.adapters.path_service_adapter import create_path_service

                path_service = create_path_service(project_path)
                episodes_dir = path_service.get_manuscript_dir()

                if not episodes_dir.exists():
                    continue

                # エピソードファイルをインデックスに追加
                for episode_file in episodes_dir.glob("第*.md"):
                    episode_id = episode_file.stem
                    self._episode_index[episode_id] = (project_path.name, episode_file)

    def find_by_id(self, episode_id: str) -> Episode | None:
        """IDでエピソードを取得(インデックス使用で高速化)"""
        with self._index_lock:
            if episode_id not in self._episode_index:
                # インデックスにない場合は再構築を試みる
                self._build_index()
                if episode_id not in self._episode_index:
                    return None

            project_id, episode_file = self._episode_index[episode_id]
            return self._load_episode_from_file(episode_file, project_id)

    def find_by_number(self, project_id: str, episode_number: int) -> Episode | None:
        """プロジェクトと話数でエピソードを取得"""
        # 話数パターンでインデックスを検索
        pattern = f"第{episode_number:03d}話"

        with self._index_lock:
            for episode_id, (proj_id, file_path) in self._episode_index.items():
                if proj_id == project_id and pattern in episode_id:
                    return self._load_episode_from_file(file_path, project_id)

        return None

    def find_all_by_project(self, project_id: str) -> list[Episode]:
        """プロジェクトの全エピソードを取得(遅延読み込み対応)"""
        episodes = []

        with self._index_lock:
            # インデックスから該当プロジェクトのエピソードを抽出
            project_episodes = [
                (episode_id, file_path)
                for episode_id, (proj_id, file_path) in self._episode_index.items()
                if proj_id == project_id
            ]

        # ソートして順次読み込み
        project_episodes.sort(key=lambda x: x[0])

        for _, file_path in project_episodes:
            episode = self._load_episode_from_file(file_path, project_id)
            if episode:
                episodes.append(episode)

        return episodes

    def find_by_phase(self, project_id: str, phase: WritingPhase) -> list[Episode]:
        """フェーズ別にエピソードを取得"""
        # メタデータから効率的に検索
        metadata = self._load_all_metadata(project_id)
        matching_ids = [ep_id for ep_id, meta in metadata.items() if meta.get("phase") == phase.value]

        episodes = []
        for episode_id in matching_ids:
            episode = self.find_by_id(episode_id)
            if episode:
                episodes.append(episode)

        return episodes

    def save(self, episode: Episode) -> None:
        """エピソードを保存(キャッシュ更新付き)"""
        project_path = self.base_path / episode.project_id
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        path_service = create_path_service(project_path)
        episodes_dir = path_service.get_manuscript_dir()
        episodes_dir.mkdir(parents=True, exist_ok=True)

        # B20準拠: PathServiceで原稿パスを一元解決
        if episode.episode_number:
            num = episode.episode_number.value if hasattr(episode.episode_number, "value") else int(episode.episode_number)
            file_path = path_service.get_manuscript_path(num)
        else:
            # エピソード番号が無い場合は従来のIDベースにフォールバック（稀ケース）
            file_path = episodes_dir / f"episode_{episode.id}.md"

        # コンテンツの保存
        # バッチ書き込みを使用
        Path(file_path).write_text(episode.content, encoding="utf-8")

        # インデックスを更新
        with self._index_lock:
            self._episode_index[episode.id] = (episode.project_id, file_path)

        # メタデータの保存
        self._save_episode_metadata(episode, project_path)

    def _load_episode_from_file(self, file_path: Path, project_id: str) -> Episode | None:
        """ファイルからエピソードを読み込み(最適化版)"""
        try:
            # コンテンツの読み込み
            content = file_path.read_text(encoding="utf-8")

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

            # メタデータの読み込み(キャッシュ使用)
            metadata = self._load_episode_metadata(project_id, file_path.stem)

            return Episode(
                id=file_path.stem,
                project_id=project_id,
                episode_number=episode_number,
                title=title,
                content=content,
                word_count=WordCount(len(content)),
                phase=metadata.get("phase", WritingPhase.DRAFT),
                publication_status=metadata.get("publication_status", PublicationStatus.UNPUBLISHED),
                created_at=metadata.get("created_at"),
                updated_at=metadata.get("updated_at"),
                published_at=metadata.get("published_at"),
            )

        except Exception:
            return None

    def _load_all_metadata(self, project_id: str) -> dict[str, str | int]:
        """プロジェクトの全メタデータを読み込み(キャッシュ使用)"""
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        path_service = create_path_service(self.base_path / project_id)
        metadata_file = path_service.get_management_dir() / "episodes_metadata.yaml"
        return self._metadata_cache.get(metadata_file) or {}

    def _load_episode_metadata(self, project_id: str, episode_id: str) -> dict[str, str | int]:
        """エピソードのメタデータを読み込み(キャッシュ使用)"""
        all_metadata = self._load_all_metadata(project_id)
        metadata = all_metadata.get(episode_id, {})

        # Enumに変換
        if "phase" in metadata:
            metadata["phase"] = WritingPhase(metadata["phase"])
        if "publication_status" in metadata:
            metadata["publication_status"] = PublicationStatus(metadata["publication_status"])

        return metadata

    def _save_episode_metadata(self, episode: Episode, project_path: Path) -> None:
        """エピソードのメタデータを保存(キャッシュ無効化付き)"""
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        path_service = create_path_service(project_path)
        metadata_dir = path_service.get_management_dir()
        metadata_dir.mkdir(parents=True, exist_ok=True)

        metadata_file = metadata_dir / "episodes_metadata.yaml"

        # 既存のメタデータを読み込み
        all_metadata = self._load_all_metadata(episode.project_id)

        # エピソードのメタデータを更新
        all_metadata[episode.id] = {
            "phase": episode.phase.value,
            "publication_status": episode.publication_status.value,
            "created_at": episode.created_at,
            "updated_at": episode.updated_at,
            "published_at": episode.published_at,
        }

        # 保存
        with Path(metadata_file).open("w", encoding="utf-8") as f:
            yaml.dump(all_metadata, f, allow_unicode=True, default_flow_style=False)

        # キャッシュを無効化
        self._metadata_cache.invalidate(metadata_file)

    def refresh_index(self) -> None:
        """インデックスを再構築"""
        self._build_index()

    def get_index_stats(self) -> dict[str, int]:
        """インデックス統計情報を取得"""
        with self._index_lock:
            project_counts = {}
            for project_id, _ in self._episode_index.values():
                project_counts[project_id] = project_counts.get(project_id, 0) + 1

            return {
                "total_episodes": len(self._episode_index),
                "total_projects": len(project_counts),
                "episodes_per_project": project_counts,
            }
