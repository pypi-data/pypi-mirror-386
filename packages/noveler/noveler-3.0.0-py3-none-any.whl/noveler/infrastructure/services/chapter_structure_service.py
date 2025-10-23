"""Infrastructure.services.chapter_structure_service
Where: Infrastructure service managing chapter structure persistence.
What: Loads, validates, and updates chapter structure information from storage.
Why: Ensures chapter structure data remains in sync with project changes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

"""章構成管理サービス

全体構成.yamlから章構成情報を読み込み、エピソードから章番号を決定するサービス。
CommonPathServiceを活用してプロジェクトパス管理を統一。
"""


import yaml

from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.infrastructure.adapters.path_service_adapter import create_path_service

if TYPE_CHECKING:
    from pathlib import Path


class ChapterInfo:
    """章情報を表すデータクラス"""

    def __init__(
        self,
        chapter_number: int,
        name: str,
        start_episode: int,
        end_episode: int,
        purpose: str,
        main_events: list[str] | None = None,
    ) -> None:
        self.chapter_number = chapter_number
        self.name = name
        self.start_episode = start_episode
        self.end_episode = end_episode
        self.purpose = purpose
        self.main_events = main_events or []
        self.total_episodes = end_episode - start_episode + 1
    def contains_episode(self, episode_number: int) -> bool:
        """指定エピソードが章に含まれるかチェック"""
        return self.start_episode <= episode_number <= self.end_episode

    def __str__(self) -> str:
        return f"第{self.chapter_number}章: {self.name} (第{self.start_episode}-{self.end_episode}話)"


class ChapterStructureService:
    """章構成管理サービス

    全体構成.yamlから章構成情報を読み込み、エピソードから章番号を決定する。
    CommonPathServiceを使用してプロジェクトパス管理を統一。
    """

    def __init__(self, project_root: Path | None = None, logger_service=None, console_service=None) -> None:
        """サービス初期化

        Args:
            project_root: プロジェクトルートパス（省略時は自動検出）
        """
        self._path_service = create_path_service(project_root)
        self._chapters_cache: list[ChapterInfo] | None = None

        self.logger_service = logger_service
        self.console_service = console_service
    def get_chapter_by_episode(self, episode_number: EpisodeNumber) -> ChapterInfo | None:
        """エピソード番号から章情報を取得

        Args:
            episode_number: エピソード番号

        Returns:
            ChapterInfo | None: 章情報（見つからない場合はNone）
        """
        chapters = self._load_chapters()

        for chapter in chapters:
            if chapter.contains_episode(episode_number.value):
                return chapter

        return None

    def get_all_chapters(self) -> list[ChapterInfo]:
        """全章情報を取得

        Returns:
            list[ChapterInfo]: 全章情報リスト
        """
        return self._load_chapters()

    def get_chapter_by_number(self, chapter_number: int) -> ChapterInfo | None:
        """章番号から章情報を取得

        Args:
            chapter_number: 章番号

        Returns:
            ChapterInfo | None: 章情報（見つからない場合はNone）
        """
        chapters = self._load_chapters()

        for chapter in chapters:
            if chapter.chapter_number == chapter_number:
                return chapter

        return None

    def _load_chapters(self) -> list[ChapterInfo]:
        """章構成を全体構成.yamlから読み込み（旧形式・新形式両対応）

        Returns:
            list[ChapterInfo]: 章情報リスト
        """
        if self._chapters_cache is not None:
            return self._chapters_cache

        try:
            overall_config_path = self._path_service.get_plot_dir() / "全体構成.yaml"

            if not overall_config_path.exists():
                self.console_service.print(f"全体構成.yamlが見つかりません: {overall_config_path}")
                return self._fallback_chapter_structure()

            with open(overall_config_path, encoding="utf-8") as f:
                config_data: dict[str, Any] = yaml.safe_load(f)

            story_structure = config_data.get("story_structure", {})

            # 新形式（推奨）: story_structure.chapters から読み込み
            chapters_data: dict[str, Any] = story_structure.get("chapters", [])
            if chapters_data:
                chapters = []
                for chapter_data in chapters_data:
                    chapter_info = ChapterInfo(
                        chapter_number=chapter_data.get("chapter_number", 1),
                        name=chapter_data.get("name", ""),
                        start_episode=chapter_data.get("start_episode", 1),
                        end_episode=chapter_data.get("end_episode", 1),
                        purpose=chapter_data.get("purpose", ""),
                        main_events=chapter_data.get("main_events", []),
                    )

                    chapters.append(chapter_info)

                self._chapters_cache = chapters
                return chapters

            # 旧形式のchaptersセクション対応（後方互換性）
            old_chapters = config_data.get("chapters", {})
            if old_chapters and isinstance(old_chapters, dict):
                chapters = []
                episode_start = 1

                for chapter_key in sorted(old_chapters.keys()):
                    chapter_data: dict[str, Any] = old_chapters[chapter_key]
                    episodes_count = chapter_data.get("episodes_count", 20)

                    chapter_info = ChapterInfo(
                        chapter_number=len(chapters) + 1,
                        name=chapter_data.get("title", ""),
                        start_episode=episode_start,
                        end_episode=episode_start + episodes_count - 1,
                        purpose=chapter_data.get("purpose", ""),
                        main_events=[],
                    )

                    chapters.append(chapter_info)
                    episode_start += episodes_count

                self._chapters_cache = chapters
                return chapters

            # 従来形式からの変換（act1/act2/act3形式）
            act1 = story_structure.get("act1", {})
            act2 = story_structure.get("act2", {})
            act3 = story_structure.get("act3", {})

            if act1 or act2 or act3:
                chapters = [
                    ChapterInfo(1, act1.get("name", "第1章"), 1, 20, act1.get("purpose", "")),
                    ChapterInfo(2, act2.get("name", "第2章"), 21, 80, act2.get("purpose", "")),
                    ChapterInfo(3, act3.get("name", "第3章"), 81, 100, act3.get("purpose", "")),
                ]
                self._chapters_cache = chapters
                return chapters

            return self._fallback_chapter_structure()

        except Exception as e:
            self.console_service.print(f"章構成の読み込みエラー: {e}")
            return self._fallback_chapter_structure()

    def _fallback_chapter_structure(self) -> list[ChapterInfo]:
        """フォールバック章構成（全体構成.yamlが読み込めない場合）

        Returns:
            list[ChapterInfo]: デフォルト章構成
        """
        fallback_chapters = [
            ChapterInfo(1, "第1章: DEBUGログ覚醒編", 1, 20, "世界観提示・主人公確立"),
            ChapterInfo(2, "第2章: The Architects探求編", 21, 80, "チーム開発の痕跡発見"),
            ChapterInfo(3, "第3章: 新生The Architects編", 81, 100, "失われたチームの復活"),
        ]

        self._chapters_cache = fallback_chapters
        return fallback_chapters

    def clear_cache(self) -> None:
        """キャッシュをクリア（設定ファイル更新時用）"""
        self._chapters_cache = None


# グローバルインスタンス
_chapter_structure_service: ChapterStructureService | None = None


def get_chapter_structure_service(project_root: Path | None = None) -> ChapterStructureService:
    """章構成サービスのインスタンスを取得

    Args:
        project_root: プロジェクトルートパス（省略時は自動検出）

    Returns:
        ChapterStructureService: 章構成サービス
    """
    global _chapter_structure_service

    if _chapter_structure_service is None or (
        project_root and _chapter_structure_service._path_service.project_root != project_root
    ):
        _chapter_structure_service = ChapterStructureService(project_root)

    return _chapter_structure_service
