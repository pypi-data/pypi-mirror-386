#!/usr/bin/env python3

"""Domain.entities.progress_report
Where: Domain entity representing progress reports.
What: Captures progress metrics, achievements, and next steps.
Why: Supports reporting and planning based on project progress.
"""

from __future__ import annotations

"""進捗レポートエンティティ

プロジェクトの進捗状況を管理し、
次のアクションを提案するリッチなドメインエンティティ
"""


from dataclasses import dataclass, field

from noveler.domain.value_objects.progress_status import NextAction, ProgressStatus
from noveler.domain.value_objects.time_estimation import TimeEstimation
from noveler.domain.value_objects.workflow_stage_type import WorkflowStageType


@dataclass
class ProgressReport:
    """進捗レポートエンティティ"""

    project_root: str
    overall_completion: int
    stage_statuses: dict[WorkflowStageType, ProgressStatus]
    next_actions: list[NextAction] = field(default_factory=list)
    created_at: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """値の検証"""
        if not isinstance(self.project_root, str):
            msg = "project_rootは文字列である必要があります"
            raise TypeError(msg)
        if not (0 <= self.overall_completion <= 100):
            msg = "全体完了率は0-100の範囲である必要があります"
            raise ValueError(msg)
        if not isinstance(self.stage_statuses, dict):
            msg = "stage_statusesは辞書である必要があります"
            raise TypeError(msg)
        if not isinstance(self.next_actions, list):
            msg = "next_actionsはリストである必要があります"
            raise TypeError(msg)

    def is_completed(self) -> bool:
        """プロジェクト全体が完了しているかチェック"""
        return self.overall_completion >= 100

    def get_completed_stages(self) -> list[WorkflowStageType]:
        """完了した段階のリストを取得"""
        return [stage for stage, status in self.stage_statuses.items() if status == ProgressStatus.COMPLETED]

    def get_in_progress_stages(self) -> list[WorkflowStageType]:
        """進行中の段階のリストを取得"""
        return [stage for stage, status in self.stage_statuses.items() if status == ProgressStatus.IN_PROGRESS]

    def get_not_started_stages(self) -> list[WorkflowStageType]:
        """未開始の段階のリストを取得"""
        return [stage for stage, status in self.stage_statuses.items() if status == ProgressStatus.NOT_STARTED]

    def recommend_next_action(self) -> NextAction | None:
        """次のアクションを推奨(ビジネスルール適用)"""
        completed_stages = self.get_completed_stages()

        # ビジネスルール: マスタープロット完了後は章別プロットを推奨
        if WorkflowStageType.MASTER_PLOT in completed_stages and WorkflowStageType.CHAPTER_PLOT not in completed_stages:
            return NextAction(
                title="第1章プロット作成",
                command="novel plot chapter 1",
                time_estimation=TimeEstimation.from_minutes(45),
                priority="high",
            )

        # ビジネスルール: 章別プロット完了後は話数別プロットを推奨
        if (
            WorkflowStageType.CHAPTER_PLOT in completed_stages
            and WorkflowStageType.EPISODE_PLOT not in completed_stages
        ):
            return NextAction(
                title="第1話詳細プロット作成",
                command="novel plot episode 1",
                time_estimation=TimeEstimation.from_minutes(30),
                priority="high",
            )

        # 未開始段階があれば最初の段階を推奨
        not_started = self.get_not_started_stages()
        if not_started:
            stage = not_started[0]
            if stage == WorkflowStageType.MASTER_PLOT:
                return NextAction(
                    title="全体構成プロット作成",
                    command="novel plot master",
                    time_estimation=TimeEstimation.from_minutes(60),
                    priority="high",
                )

        return None

    def has_blocking_issues(self) -> bool:
        """阻害要因があるかチェック"""
        return any(status == ProgressStatus.BLOCKED for status in self.stage_statuses.values())

    def needs_review(self) -> bool:
        """レビューが必要かチェック"""
        return any(status == ProgressStatus.NEEDS_REVIEW for status in self.stage_statuses.values())

    def calculate_estimated_remaining_time(self) -> TimeEstimation:
        """残り作業時間の見積もり"""
        total_minutes = sum(action.time_estimation.in_minutes() for action in self.next_actions)
        return TimeEstimation.from_minutes(total_minutes)

    def generate_display(self) -> str:
        """進捗レポートの表示用テキスト生成"""
        display = f"""
📊 プロット作成進捗レポート

🎯 全体完了率: {self.overall_completion}%

📋 段階別状況:
    """

        # 段階別の状況表示
        for stage, status in self.stage_statuses.items():
            stage_name = self._get_stage_japanese_name(stage)
            emoji = status.emoji()
            display += f"  {emoji} {stage_name}: {status.value}\n"

        # 阻害要因や要確認項目があれば警告
        if self.has_blocking_issues():
            display += "\n⚠️ 阻害要因があります。解決が必要です。\n"

        if self.needs_review():
            display += "\n📝 レビューが必要な項目があります。\n"

        # 次のアクション
        if self.next_actions:
            display += "\n🔄 推奨される次のステップ:\n"
            for i, action in enumerate(self.next_actions[:3], 1):  # 最大3個まで表示
                display += f"  {i}. {action.display_text()}\n     コマンド: {action.command}\n"

        # 推奨アクション
        recommended = self.recommend_next_action()
        if recommended and recommended not in self.next_actions:
            display += f"\n💡 おすすめ: {recommended.display_text()}\n     コマンド: {recommended.command}\n"

        # 残り時間見積もり
        if self.next_actions:
            remaining_time = self.calculate_estimated_remaining_time()
            display += f"\n⏱️  残り作業時間見積もり: {remaining_time.display_text()}\n"

        return display

    def _get_stage_japanese_name(self, stage: WorkflowStageType) -> str:
        """ワークフロー段階の日本語名を取得"""
        stage_names = {
            WorkflowStageType.MASTER_PLOT: "全体構成",
            WorkflowStageType.CHAPTER_PLOT: "章別プロット",
            WorkflowStageType.EPISODE_PLOT: "話数別プロット",
        }
        return stage_names.get(stage, str(stage.value))
