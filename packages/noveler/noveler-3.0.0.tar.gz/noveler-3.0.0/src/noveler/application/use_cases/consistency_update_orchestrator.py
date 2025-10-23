#!/usr/bin/env python3
"""Consistency update orchestrator for version management.

This module orchestrates consistency updates when major version changes occur,
coordinating updates across episodes and foreshadowing management files.
"""

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class ForeshadowImpact:
    """伏線影響分析結果"""

    potentially_invalidated: list[str]
    review_recommendations: list[str]


class EpisodeUpdater(Protocol):
    """エピソード更新器のプロトコル"""

    def mark_episodes_for_revision(
        self, episodes_data: dict, affected_chapters: list[int], new_version: str
    ) -> dict:
        """エピソードを改訂対象としてマーク"""
        ...


class ForeshadowAnalyzer(Protocol):
    """伏線分析器のプロトコル"""

    def analyze_foreshadowing_validity(
        self, foreshadowing_data: dict, affected_chapters: list[str]
    ) -> ForeshadowImpact:
        """伏線の有効性を分析"""
        ...


class FileManager(Protocol):
    """ファイル管理器のプロトコル"""

    def load_episodes_data(self) -> dict:
        """エピソードデータをロード"""
        ...

    def save_episodes_data(self, data: dict) -> None:
        """エピソードデータを保存"""
        ...

    def load_foreshadowing_data(self) -> dict:
        """伏線データをロード"""
        ...

    def save_foreshadowing_data(self, data: dict) -> None:
        """伏線データを保存"""
        ...


@dataclass(frozen=True)
class ConsistencyUpdateResult:
    """整合性更新結果"""

    success: bool
    update_summary: list[str]
    error_message: str = ""


class ConsistencyUpdateOrchestrator:
    """整合性更新オーケストレータ"""

    def __init__(
        self, episode_updater: EpisodeUpdater, foreshadow_analyzer: ForeshadowAnalyzer, file_manager: FileManager
    ) -> None:
        self.episode_updater = episode_updater
        self.foreshadow_analyzer = foreshadow_analyzer
        self.file_manager = file_manager

    def execute_consistency_update(self, version_change: dict) -> ConsistencyUpdateResult:
        """整合性更新を実行"""
        update_summary = []

        try:
            # 1. 話数管理の更新(常に実行)
            episodes_data: dict[str, Any] = self.file_manager.load_episodes_data()
            affected_chapters = version_change.get("affected_chapters", [])
            new_version = version_change["to"]

            updated_episodes = self.episode_updater.mark_episodes_for_revision(
                episodes_data,
                affected_chapters,
                new_version,
            )

            self.file_manager.save_episodes_data(updated_episodes)
            update_summary.append("話数管理ステータスを更新")

            # 2. 伏線管理の更新(メジャーバージョンのみ)
            if version_change["type"] == "major":
                foreshadowing_data: dict[str, Any] = self.file_manager.load_foreshadowing_data()
                foreshadow_impact = self.foreshadow_analyzer.analyze_foreshadowing_validity(
                    foreshadowing_data,
                    affected_chapters,
                )

                if foreshadow_impact.potentially_invalidated:
                    # 伏線管理ファイルにレビューノートを追加
                    self._add_foreshadowing_review_notes(
                        foreshadowing_data,
                        foreshadow_impact,
                        new_version,
                    )

                    self.file_manager.save_foreshadowing_data(foreshadowing_data)
                    update_summary.append("伏線管理にレビューノートを追加")

            return ConsistencyUpdateResult(
                success=True,
                update_summary=update_summary,
            )

        except Exception as e:
            return ConsistencyUpdateResult(
                success=False,
                update_summary=update_summary,
                error_message=str(e),
            )

    def _add_foreshadowing_review_notes(
        self, foreshadowing_data: dict, impact: ForeshadowImpact, version: str
    ) -> None:
        """伏線管理ファイルにレビューノートを追加"""
        if "review_notes" not in foreshadowing_data:
            foreshadowing_data["review_notes"] = []

        foreshadowing_data["review_notes"].append(
            {
                "version": version,
                "review_items": list(impact.review_recommendations),
                "potentially_invalidated": list(impact.potentially_invalidated),
            }
        )
