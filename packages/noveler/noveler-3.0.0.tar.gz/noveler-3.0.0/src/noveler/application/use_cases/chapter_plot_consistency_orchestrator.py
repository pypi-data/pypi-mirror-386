#!/usr/bin/env python3
"""章別プロット整合性オーケストレータ
マイナーバージョンアップ時の章固有影響管理
"""

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class ChapterImpact:
    """章の影響分析結果"""

    affected_chapter: int
    requires_episode_review: bool
    requires_foreshadowing_review: bool


@dataclass
class MultipleChaptersImpact:
    """複数章の影響分析結果"""

    affected_chapters: list[int]
    chapter_impacts: list[ChapterImpact]


@dataclass
class ForeshadowingImpact:
    """伏線影響分析結果"""

    chapter: int
    affected_foreshadowing: list[str]
    review_recommendation: str


class ChapterAnalyzer(Protocol):
    """章分析器のプロトコル"""

    def analyze_chapter_impact(self, chapter_file: str) -> ChapterImpact:
        """単一章の影響を分析"""
        ...

    def analyze_multiple_chapters_impact(self, chapter_files: list[str]) -> MultipleChaptersImpact:
        """複数章の影響を分析"""
        ...


class EpisodeUpdater(Protocol):
    """エピソード更新器のプロトコル"""

    def update_chapter_episodes(self, episodes_data: dict[str, Any], chapter_number: int) -> dict:
        """章のエピソードを更新"""
        ...


class ForeshadowAnalyzer(Protocol):
    """伏線分析器のプロトコル"""

    def analyze_chapter_foreshadowing(self, foreshadowing_data: dict, chapter_number: int) -> ForeshadowingImpact:
        """章の伏線を分析"""
        ...


class FileManager(Protocol):
    """ファイル管理器のプロトコル"""

    def load_episodes_data(self) -> dict:
        """エピソードデータをロード"""
        ...

    def save_episodes_data(self, data: dict[str, Any]) -> None:
        """エピソードデータを保存"""
        ...

    def load_foreshadowing_data(self) -> dict:
        """伏線データをロード"""
        ...

    def save_foreshadowing_data(self, data: dict[str, Any]) -> None:
        """伏線データを保存"""
        ...


@dataclass(frozen=True)
class ChapterConsistencyUpdateResult:
    """章別整合性更新結果"""

    success: bool
    update_summary: list[str]
    affected_chapters: list[int] = field(default_factory=list)
    error_message: str = ""


class ChapterPlotConsistencyOrchestrator:
    """章別プロット整合性オーケストレータ"""

    def __init__(self, chapter_analyzer: ChapterAnalyzer, episode_updater: EpisodeUpdater) -> None:
        self.chapter_analyzer = chapter_analyzer
        self.episode_updater = episode_updater
        self.file_manager: FileManager = None  # Will be injected
        self.foreshadow_analyzer: ForeshadowAnalyzer = None  # Will be injected

    def execute_chapter_consistency_update(self, version_change: dict[str, Any]) -> ChapterConsistencyUpdateResult:
        """章別整合性更新を実行"""
        update_summary = []
        affected_chapters = []

        try:
            changed_files = version_change.get("changed_files", [])
            new_version = version_change["to"]

            # 単一章 vs 複数章の判定
            chapter_files = [f for f in changed_files if "章別プロット" in f]

            if len(chapter_files) == 1:
                # 単一章の処理
                impact = self.chapter_analyzer.analyze_chapter_impact(chapter_files[0])
                affected_chapters = [impact.affected_chapter]

                # 章固有の更新処理
                self._update_single_chapter(impact, new_version, update_summary)

            elif len(chapter_files) > 1:
                # 複数章の処理
                impact = self.chapter_analyzer.analyze_multiple_chapters_impact(chapter_files)
                affected_chapters = impact.affected_chapters

                # 各章ごとに更新処理
                for chapter_impact in impact.chapter_impacts:
                    self._update_single_chapter(chapter_impact, new_version, update_summary)

            return ChapterConsistencyUpdateResult(
                success=True,
                update_summary=update_summary,
                affected_chapters=affected_chapters,
            )

        except Exception as e:
            return ChapterConsistencyUpdateResult(
                success=False,
                update_summary=update_summary,
                affected_chapters=affected_chapters,
                error_message=str(e),
            )

    def _update_single_chapter(
        self, chapter_impact: ChapterImpact, new_version: str, update_summary: list[str]
    ) -> None:
        """単一章の更新処理"""
        chapter_number = chapter_impact.affected_chapter

        # 1. 話数管理の更新
        if chapter_impact.requires_episode_review:
            episodes_data: dict[str, Any] = self.file_manager.load_episodes_data()
            updated_episodes = self.episode_updater.update_chapter_episodes(
                episodes_data,
                chapter_number,
                new_version,
                f"第{chapter_number}章プロット変更",
            )

            self.file_manager.save_episodes_data(updated_episodes)
            update_summary.append(f"第{chapter_number}章の話数ステータスを更新")

        # 2. 伏線管理の更新
        if chapter_impact.requires_foreshadowing_review:
            foreshadowing_data: dict[str, Any] = self.file_manager.load_foreshadowing_data()
            foreshadow_impact = self.foreshadow_analyzer.analyze_chapter_foreshadowing(
                foreshadowing_data,
                chapter_number,
            )

            if foreshadow_impact.affected_foreshadowing:
                # 章別伏線レビューノートを追加
                self._add_chapter_foreshadowing_review(
                    foreshadowing_data,
                    foreshadow_impact
                )

                self.file_manager.save_foreshadowing_data(foreshadowing_data)
                update_summary.append(f"第{chapter_number}章の伏線レビューノートを追加")

    def _add_chapter_foreshadowing_review(
        self, foreshadowing_data: dict[str, Any], impact: ForeshadowingImpact
    ) -> None:
        """章別伏線レビューノートを追加"""
        if "chapter_review_notes" not in foreshadowing_data:
            foreshadowing_data["chapter_review_notes"] = []

        foreshadowing_data["chapter_review_notes"].append(
            {"version": getattr(impact, "version", "unknown"), "chapter": impact.chapter}
        )
