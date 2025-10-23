#!/usr/bin/env python3

"""Domain.entities.user_guidance
Where: Domain entity representing user guidance content.
What: Stores guidance steps and metadata for user-facing flows.
Why: Delivers consistent guidance across presentation layers.
"""

from __future__ import annotations

"""ユーザーガイダンスエンティティ

ユーザーへの手順案内とガイダンス情報を管理するリッチなドメインエンティティ
ビジネスルールと状態管理を含む
"""


from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

from noveler.domain.value_objects.time_estimation import TimeEstimation

if TYPE_CHECKING:
    from noveler.domain.value_objects.workflow_stage_type import WorkflowStageType


class GuidanceType(Enum):
    """ガイダンスタイプ"""

    PREREQUISITE_MISSING = "prerequisite_missing"
    SUCCESS_NEXT_STEPS = "success_next_steps"
    ERROR_RESOLUTION = "error_resolution"
    PROGRESS_UPDATE = "progress_update"
    BEGINNER_FRIENDLY = "beginner_friendly"
    PROGRESS_BASED = "progress_based"


@dataclass
class GuidanceStep:
    """ガイダンスステップエンティティ"""

    step_number: int
    title: str
    description: str
    command: str
    time_estimation: TimeEstimation
    is_completed: bool = False
    prerequisites: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """値の検証"""
        if self.step_number <= 0:
            msg = "ステップ番号は1以上である必要があります"
            raise ValueError(msg)
        if not self.title.strip():
            msg = "ステップタイトルは必須です"
            raise ValueError(msg)
        if not self.description.strip():
            msg = "ステップ説明は必須です"
            raise ValueError(msg)
        if not self.command.strip():
            msg = "実行コマンドは必須です"
            raise ValueError(msg)

    def mark_as_completed(self) -> None:
        """ステップを完了状態に変更"""
        self.is_completed = True

    def can_execute(self, existing_files: list[str]) -> bool:
        """ステップの実行可能性を判定"""
        if not self.prerequisites:
            return True

        # 前提条件となるファイルがすべて存在するかチェック
        return all(prereq in existing_files for prereq in self.prerequisites)

    def generate_display(self) -> str:
        """ステップの表示用テキスト生成"""
        status_emoji = "✅" if self.is_completed else "📝"
        return f"{status_emoji} {self.step_number}. {self.title}\n   {self.description}\n   コマンド: {self.command}\n   所要時間: {self.time_estimation.display_text()}"


@dataclass
class UserGuidance:
    """ユーザーガイダンスエンティティ"""

    guidance_type: GuidanceType
    title: str
    steps: list[GuidanceStep]
    target_stage: WorkflowStageType
    created_at: str | None = None
    context_info: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """値の検証"""
        if not self.title.strip():
            msg = "ガイダンスタイトルは必須です"
            raise ValueError(msg)
        if not self.steps:
            msg = "ガイダンスステップは最低1個必要です"
            raise ValueError(msg)

        # ステップ番号の連続性チェック
        for i, step in enumerate(self.steps, 1):
            if step.step_number != i:
                msg = f"ステップ番号が連続していません: 期待値{i}, 実際値{step.step_number}"
                raise ValueError(msg)

    def calculate_total_time(self) -> TimeEstimation:
        """全体の所要時間を計算"""
        total_minutes = sum(step.time_estimation.in_minutes() for step in self.steps)
        return TimeEstimation.from_minutes(total_minutes)

    def calculate_completion_rate(self) -> int:
        """完了率を計算(パーセンテージ)"""
        if not self.steps:
            return 0

        completed_steps = sum(1 for step in self.steps if step.is_completed)
        return int((completed_steps / len(self.steps)) * 100)

    def get_next_step(self) -> GuidanceStep | None:
        """次に実行すべきステップを取得"""
        for step in self.steps:
            if not step.is_completed:
                return step
        return None

    def get_current_step_number(self) -> int:
        """現在のステップ番号を取得"""
        next_step = self.get_next_step()
        return next_step.step_number if next_step else len(self.steps) + 1

    def is_completed(self) -> bool:
        """ガイダンス全体が完了しているかチェック"""
        return all(step.is_completed for step in self.steps)

    def can_start_next_step(self, existing_files: list[str]) -> bool:
        """次のステップを開始できるかチェック"""
        next_step = self.get_next_step()
        if not next_step:
            return False
        return next_step.can_execute(existing_files)

    def generate_display(self) -> str:
        """ガイダンスの表示用テキスト生成"""
        completion_rate = self.calculate_completion_rate()
        total_time = self.calculate_total_time()

        display = f"""
🎯 {self.title}

📊 進捗: {completion_rate}% 完了
⏱️  予想所要時間: {total_time.display_text()}

📋 実行手順:
    """

        for step in self.steps:
            display += f"\n{step.generate_display()}\n"

        # 次のステップのハイライト
        next_step = self.get_next_step()
        if next_step:
            display += f"\n🔄 次のステップ: {next_step.title}"
        else:
            display += "\n✅ 全ステップ完了!"

        return display

    @property
    def type(self) -> GuidanceType:
        """ガイダンスタイプのエイリアス"""
        return self.guidance_type

    @property
    def message(self) -> str:
        """コンテキスト情報からメッセージを取得"""
        return self.context_info.get("message", self.title)

    @property
    def estimated_time(self) -> TimeEstimation:
        """推定時間のエイリアス"""
        return self.calculate_total_time()

    @property
    def priority(self) -> str:
        """優先度を取得"""
        return self.context_info.get("priority", "normal")

    @property
    def improvement_examples(self) -> list[str]:
        """改善例を取得"""
        return self.context_info.get("improvement_examples", [])
