"""Domain.services.plot_progress_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""プロット進捗管理サービス(DDD準拠リファクタリング版)

ファイルI/OやYAML解析を排除し、リポジトリパターンを使用
純粋なドメインロジックのみを含む
"""


from pathlib import Path

# Phase 6修正: Service → Repository循環依存解消
from typing import Any, Protocol

from noveler.domain.entities.progress_report import ProgressReport


class IPlotProgressRepository(Protocol):
    """プロット進捗リポジトリインターフェース（循環依存解消）"""

    def load_progress_data(self, project_path: Path) -> dict[str, Any]: ...
    def save_progress_report(self, report: ProgressReport) -> bool: ...
    def get_current_stage(self, project_path: Path) -> str: ...


from noveler.domain.value_objects.progress_status import NextAction, ProgressStatus
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.value_objects.time_estimation import TimeEstimation
from noveler.domain.value_objects.workflow_stage_type import WorkflowStageType

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class PlotProgressService:
    """プロット進捗管理サービス(DDD準拠)"""

    def __init__(self, repository: IPlotProgressRepository) -> None:
        """Args:
        repository: プロット進捗リポジトリ
        """
        self.repository = repository

    def analyze_project_progress(self, project_id: str) -> ProgressReport:
        """プロジェクトの進捗状況を分析

        Args:
            project_id: プロジェクトID

        Returns:
            ProgressReport: 進捗レポート
        """
        # 各段階の状況を分析
        stage_statuses = {}

        # マスタープロット
        master = self.repository.find_master_plot(project_id)
        stage_statuses[WorkflowStageType.MASTER_PLOT] = self._determine_master_status(master)

        # 章別プロット
        chapters = self.repository.find_chapter_plots(project_id)
        stage_statuses[WorkflowStageType.CHAPTER_PLOT] = self._determine_chapters_status(chapters)

        # 話別プロット
        episodes = self.repository.find_episode_plots(project_id)
        stage_statuses[WorkflowStageType.EPISODE_PLOT] = self._determine_episodes_status(episodes)

        # 全体完了率の計算
        overall_completion = self._calculate_overall_completion(stage_statuses)

        # 次のアクションの提案
        next_actions = self._suggest_next_actions(stage_statuses, project_id)

        # プロジェクトルート取得(互換性のため)
        project_root = self.repository.get_project_root(project_id) or Path(project_id)  # TODO: IPathServiceを使用するように修正

        return ProgressReport(
            project_root=str(project_root),
            overall_completion=overall_completion,
            stage_statuses=stage_statuses,
            next_actions=next_actions,
            created_at=project_now().datetime.isoformat(),
            metadata={
                "version": "2.0",
                "ddd_compliant": True,
                "analyzer": "PlotProgressService",
            },
        )

    def _determine_master_status(self, master_data: dict[str, Any] | None) -> ProgressStatus:
        """マスタープロットのステータス判定"""
        if not master_data:
            return ProgressStatus.NOT_STARTED

        # 完成度スコアに基づく判定
        completion_score = self.repository.calculate_file_completion(master_data)

        if completion_score >= 80:
            return ProgressStatus.COMPLETED
        if completion_score >= 30:
            return ProgressStatus.IN_PROGRESS
        return ProgressStatus.NEEDS_REVIEW

    def _determine_chapters_status(self, chapters: list[dict[str, Any]]) -> ProgressStatus:
        """章別プロットの総合ステータス判定"""
        if not chapters:
            return ProgressStatus.NOT_STARTED

        try:
            chapter_list = list(chapters)
        except TypeError:
            return ProgressStatus.NOT_STARTED

        if not chapter_list or not all(isinstance(chapter, dict) for chapter in chapter_list):
            return ProgressStatus.NOT_STARTED

        # 各章の完成度を計算
        completion_scores: list[float] = []
        for chapter in chapter_list:
            score = self.repository.calculate_file_completion(chapter)
            completion_scores.append(score)

        # 平均完成度で判定
        if not completion_scores:
            return ProgressStatus.NOT_STARTED

        average_completion = sum(completion_scores) / len(completion_scores)

        if average_completion >= 80:
            return ProgressStatus.COMPLETED
        if average_completion >= 30:
            return ProgressStatus.IN_PROGRESS
        return ProgressStatus.NEEDS_REVIEW

    def _determine_episodes_status(self, episodes: list[dict[str, Any]]) -> ProgressStatus:
        """話別プロットの総合ステータス判定"""
        # 章別と同様のロジック
        return self._determine_chapters_status(episodes)

    def _calculate_overall_completion(self, stage_statuses: dict[WorkflowStageType, ProgressStatus]) -> int:
        """重み付き全体完了率の計算

        Args:
            stage_statuses: 各ステージのステータス

        Returns:
            全体完了率(0-100)
        """
        # 各ステージの重み
        weights = {
            WorkflowStageType.MASTER_PLOT: 0.3,
            WorkflowStageType.CHAPTER_PLOT: 0.4,
            WorkflowStageType.EPISODE_PLOT: 0.3,
        }

        # ステータスごとの完了率
        status_percentages = {
            ProgressStatus.NOT_STARTED: 0,
            ProgressStatus.IN_PROGRESS: 50,
            ProgressStatus.NEEDS_REVIEW: 30,
            ProgressStatus.COMPLETED: 100,
        }

        total = 0.0
        for stage_type, status in stage_statuses.items():
            percentage = status_percentages.get(status, 0)
            weight = weights.get(stage_type, 0)
            total += percentage * weight

        return int(total)

    def _suggest_next_actions(self, stage_statuses: dict[str, ProgressStatus], project_id: str) -> list[NextAction]:
        """進捗に基づく次のアクション提案

        Args:
            stage_statuses: 各ステージのステータス
            project_id: プロジェクトID

        Returns:
            推奨アクションのリスト
        """
        actions = []

        # マスタープロット未完成の場合
        if stage_statuses[WorkflowStageType.MASTER_PLOT] != ProgressStatus.COMPLETED:
            action = NextAction(
                title="マスタープロットを完成させましょう",
                command="novel plot master",
                time_estimation=TimeEstimation.from_hours(2),
                priority="high",
            )

            actions.append(action)

        # 章別プロット進行中の場合
        elif stage_statuses[WorkflowStageType.CHAPTER_PLOT] == ProgressStatus.IN_PROGRESS:
            incomplete = self.repository.find_incomplete_chapters(project_id)
            if incomplete:
                chapter_num = incomplete[0]
                action = NextAction(
                    title=f"chapter{chapter_num:02d}のプロットを完成させましょう",
                    command=f"novel plot chapter {chapter_num}",
                    time_estimation=TimeEstimation.from_minutes(60),
                    priority="high",
                )

                actions.append(action)

        # 章別プロット未着手の場合
        elif stage_statuses[WorkflowStageType.CHAPTER_PLOT] == ProgressStatus.NOT_STARTED:
            action = NextAction(
                title="chapter01のプロットから始めましょう",
                command="novel plot chapter 1",
                time_estimation=TimeEstimation.from_minutes(60),
                priority="high",
            )

            actions.append(action)

        # 話別プロット未着手の場合
        elif stage_statuses[WorkflowStageType.EPISODE_PLOT] == ProgressStatus.NOT_STARTED:
            action = NextAction(
                title="episode001の詳細プロットを作成しましょう",
                command="novel plot episode 1",
                time_estimation=TimeEstimation.from_minutes(30),
                priority="high",
            )

            actions.append(action)

        # すべて完了している場合
        elif all(status == ProgressStatus.COMPLETED for status in stage_statuses.values()):
            action = NextAction(
                title="プロット作成が完了しました!執筆を開始しましょう",
                command="novel write 1",
                time_estimation=TimeEstimation.from_hours(1),
                priority="high",
            )

            actions.append(action)

        return actions

    def get_completion_summary(self, project_id: str) -> str:
        """進捗サマリーを文字列で取得

        Args:
            project_id: プロジェクトID

        Returns:
            進捗サマリー文字列
        """
        report = self.analyze_project_progress(project_id)

        lines = [
            f"📊 プロット作成進捗: {report.overall_completion}%",
            "",
            "📋 段階別状況:",
        ]

        stage_names = self._get_stage_names()
        status_symbols = self._get_status_symbols()

        for stage_type, status in report.stage_statuses.items():
            name = stage_names.get(stage_type, str(stage_type))
            symbol = status_symbols.get(status, "❓")
            lines.append(f"  {symbol} {name}: {status.value}")

        if report.next_actions:
            lines.extend(["", "🔄 推奨される次のステップ:"])
            for i, action in enumerate(report.next_actions[:3], 1):
                time_text = action.estimated_time.display_text()
                lines.append(f"  {i}. {action.description} (所要時間: {time_text})")
                if action.command:
                    lines.append(f"     コマンド: {action.command}")

        return "\n".join(lines)

    def _get_stage_names(self) -> dict[WorkflowStageType, str]:
        """ステージ名のマッピングを取得"""
        return {
            WorkflowStageType.MASTER_PLOT: "全体構成",
            WorkflowStageType.CHAPTER_PLOT: "章別プロット",
            WorkflowStageType.EPISODE_PLOT: "話数別プロット",
        }

    def _get_status_symbols(self) -> dict[ProgressStatus, str]:
        """ステータスシンボルのマッピングを取得"""
        return {
            ProgressStatus.NOT_STARTED: "⚪",
            ProgressStatus.IN_PROGRESS: "🔄",
            ProgressStatus.NEEDS_REVIEW: "⚠️",
            ProgressStatus.COMPLETED: "✅",
        }
