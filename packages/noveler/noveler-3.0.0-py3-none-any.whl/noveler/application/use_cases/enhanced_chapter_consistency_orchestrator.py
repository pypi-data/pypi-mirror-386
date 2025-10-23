#!/usr/bin/env python3
"""拡張章別プロット整合性オーケストレータ
双方向伏線管理を含む高度な整合性管理
"""

from dataclasses import dataclass, field
from pathlib import Path
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
class BidirectionalImpact:
    """双方向影響分析結果"""

    direct_impacts: list[ChapterImpact]
    reverse_impacts: set[int]
    cross_references: dict[int, list[int]]


class ChapterAnalyzer(Protocol):
    """章分析器のプロトコル"""

    def analyze_chapter_impact(self, chapter_file: Path) -> ChapterImpact:
        """単一章の影響を分析"""
        ...

    def analyze_multiple_chapters_impact(self, chapter_files: list[Path]) -> MultipleChaptersImpact:
        """複数章の影響を分析"""
        ...


class EpisodeUpdater(Protocol):
    """エピソード更新器のプロトコル"""

    def update_chapter_episodes(self, episodes_data: list[dict[str, Any]], chapter_number: int) -> dict[str, Any]:
        """章のエピソードを更新"""
        ...


class BidirectionalAnalyzer(Protocol):
    """双方向分析器のプロトコル"""

    def analyze_reverse_impact(self, impact: ChapterImpact, episodes_data: list[dict[str, Any]]) -> set[int]:
        """逆方向影響を分析"""
        ...


class StatusUpdater(Protocol):
    """ステータス更新器のプロトコル"""

    def update_episode_statuses(self, episodes_data: list[dict[str, Any]], reverse_check_chapters: set[int]) -> None:
        """エピソードステータスを更新"""
        ...


class FileManager(Protocol):
    """ファイル管理器のプロトコル"""

    def load_episodes_data(self) -> dict:
        """エピソードデータをロード"""
        ...

    def save_episodes_data(self, data: list[dict[str, Any]]) -> None:
        """エピソードデータを保存"""
        ...


@dataclass(frozen=True)
class EnhancedConsistencyUpdateResult:
    """拡張整合性更新結果"""

    success: bool
    update_summary: list[str]
    affected_chapters: list[int] = field(default_factory=list)
    reverse_check_chapters: set[int] = field(default_factory=set)
    error_message: str = ""


class EnhancedChapterConsistencyOrchestrator:
    """拡張章別プロット整合性オーケストレータ"""

    def __init__(
        self,
        chapter_analyzer: ChapterAnalyzer,
        episode_updater: EpisodeUpdater,
        bidirectional_analyzer: BidirectionalAnalyzer | None = None,
        status_updater: StatusUpdater | None = None,
        file_manager: FileManager | None = None,
    ) -> None:
        self.chapter_analyzer = chapter_analyzer
        self.episode_updater = episode_updater
        self.bidirectional_analyzer = bidirectional_analyzer
        self.status_updater = status_updater
        self.file_manager = file_manager

    def execute_chapter_consistency_update(self, version_change: dict[str, Any]) -> EnhancedConsistencyUpdateResult:
        """章別整合性更新を実行(双方向分析含む)"""
        update_summary = []
        affected_chapters = []
        reverse_check_chapters = set()

        try:
            changed_files = version_change.get("changed_files", [])
            new_version = version_change["to"]

            # 章別プロットファイルを特定
            chapter_files = [f for f in changed_files if "章別プロット" in f]

            if len(chapter_files) == 1:
                # 単一章の処理
                impact = self.chapter_analyzer.analyze_chapter_impact(chapter_files[0])
                affected_chapters = [impact.affected_chapter]

                # 双方向伏線分析を含む更新処理
                reverse_chapters = self._update_single_chapter_enhanced(
                    impact,
                    new_version,
                    update_summary,
                )

                reverse_check_chapters.update(reverse_chapters)

            elif len(chapter_files) > 1:
                # 複数章の処理
                impact = self.chapter_analyzer.analyze_multiple_chapters_impact(chapter_files)
                affected_chapters = impact.affected_chapters

                # 各章ごとに双方向分析を含む更新処理
                for chapter_impact in impact.chapter_impacts:
                    reverse_chapters = self._update_single_chapter_enhanced(
                        chapter_impact,
                        new_version,
                        update_summary,
                    )

                    reverse_check_chapters.update(reverse_chapters)

            # 逆方向チェック推奨を追加
            if reverse_check_chapters:
                chapters_str = ", ".join(f"第{ch}章" for ch in sorted(reverse_check_chapters))
                update_summary.append(f"逆方向チェック推奨: {chapters_str}の確認も推奨")

            return EnhancedConsistencyUpdateResult(
                success=True,
                update_summary=update_summary,
                affected_chapters=affected_chapters,
                reverse_check_chapters=reverse_check_chapters,
            )

        except Exception as e:
            return EnhancedConsistencyUpdateResult(
                success=False,
                update_summary=update_summary,
                affected_chapters=affected_chapters,
                reverse_check_chapters=reverse_check_chapters,
                error_message=str(e),
            )

    def _update_single_chapter_enhanced(
        self, chapter_impact: ChapterImpact, new_version: str, update_summary: list[str]
    ) -> set[int]:
        """単一章の拡張更新処理(双方向分析含む)"""
        chapter_number = chapter_impact.affected_chapter
        reverse_check_chapters = set()

        # 1. 話数管理の更新(既存処理)
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

        # 2. 双方向伏線分析(新規)
        if chapter_impact.requires_foreshadowing_review:
            foreshadowing_data: dict[str, Any] = self.file_manager.load_foreshadowing_data()

            # 双方向影響分析
            bidirectional_impact = self.bidirectional_analyzer.analyze_bidirectional_impact(
                foreshadowing_data,
                chapter_number,
            )

            if bidirectional_impact.has_bidirectional_impact:
                # ステータス更新
                updated_foreshadowing = self.status_updater.update_foreshadowing_status(
                    foreshadowing_data,
                    bidirectional_impact,
                    new_version,
                )

                self.file_manager.save_foreshadowing_data(updated_foreshadowing)

                # サマリー追加
                update_summary.append(f"伏線ステータス更新: 第{chapter_number}章")

                # 逆方向チェックが必要な章を取得
                reverse_chapters = self.bidirectional_analyzer.get_reverse_check_chapters(bidirectional_impact)

                reverse_check_chapters.update(reverse_chapters)

        return reverse_check_chapters

    def _create_bidirectional_summary(self, bidirectional_impact: BidirectionalImpact) -> str:
        """双方向影響のサマリーを作成"""
        parts = []
        setup_count = len(getattr(bidirectional_impact, "setup_modified", []))
        resolution_count = len(getattr(bidirectional_impact, "resolution_modified", []))

        if setup_count:
            parts.append(f"仕込み変更: {setup_count}件")
        if resolution_count:
            parts.append(f"回収変更: {resolution_count}件")

        if setup_count and resolution_count:
            return f"双方向影響検出 - {', '.join(parts)}"
        if parts:
            return parts[0]
        return "影響なし"
