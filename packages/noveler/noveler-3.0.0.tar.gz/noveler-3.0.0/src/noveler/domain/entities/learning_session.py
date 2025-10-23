#!/usr/bin/env python3

"""Domain.entities.learning_session
Where: Domain entity tracking learning sessions.
What: Records learning objectives, activities, and outcomes.
Why: Supports analytics and progress tracking for learning workflows.
"""

from __future__ import annotations

"""学習セッションエンティティ
品質記録活用システムのドメインモデル
"""


from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from noveler.domain.exceptions import BusinessRuleViolationError
from noveler.domain.value_objects.learning_metrics import LearningMetrics
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

if TYPE_CHECKING:
    from datetime import datetime

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


@dataclass
class LearningSession:
    """学習セッションエンティティ

    個別の執筆セッションのコンテキストと学習データを管理
    """

    project_name: str
    episode_number: int
    start_time: datetime
    writing_environment: str | None = None
    target_audience: str | None = None
    writing_goal: str | None = None
    end_time: datetime | None = None
    total_writing_time: int = 0  # 分単位
    is_completed: bool = False

    def __post_init__(self) -> None:
        """エンティティの不変条件を検証"""
        self._validate_project_name()
        self._validate_episode_number()
        self._validate_start_time()

    def _validate_project_name(self) -> None:
        """プロジェクト名の妥当性検証"""
        if not self.project_name or len(self.project_name.strip()) == 0:
            msg = "プロジェクト名は必須です"
            error_code = "project_name_required"
            raise BusinessRuleViolationError(error_code, msg)

    def _validate_episode_number(self) -> None:
        """エピソード番号の妥当性検証"""
        if self.episode_number <= 0:
            msg = "エピソード番号は1以上の正の整数である必要があります"
            error_code = "episode_number_invalid"
            raise BusinessRuleViolationError(error_code, msg)

    def _validate_start_time(self) -> None:
        """開始時刻の妥当性検証"""
        if self.start_time is None:
            msg = "開始時刻は必須です"
            error_code = "start_time_required"
            raise BusinessRuleViolationError(error_code, msg)

    def complete(self, end_time: datetime | None = None) -> None:
        """学習セッションを完了"""
        if self.is_completed:
            msg = "既に完了したセッションです"
            error_code = "session_already_completed"
            raise BusinessRuleViolationError(error_code, msg)

        self.end_time = end_time or project_now().datetime

        # 開始時刻より前に終了することはできない
        if self.end_time < self.start_time:
            msg = "終了時刻は開始時刻より後である必要があります"
            error_code = "invalid_end_time"
            raise BusinessRuleViolationError(error_code, msg)

        # 執筆時間を計算(分単位)
        duration = self.end_time - self.start_time
        self.total_writing_time = int(duration.total_seconds() / 60)

        self.is_completed = True

    def get_session_duration(self) -> int:
        """セッションの継続時間を取得(分単位)"""
        if not self.is_completed:
            return 0
        return self.total_writing_time

    def get_session_context(self) -> dict[str, Any]:
        """セッションのコンテキストを取得"""
        return {
            "project_name": self.project_name,
            "episode_number": self.episode_number,
            "writing_environment": self.writing_environment,
            "target_audience": self.target_audience,
            "writing_goal": self.writing_goal,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_writing_time": self.total_writing_time,
            "is_completed": self.is_completed,
        }

    def create_learning_metrics(
        self, improvement_from_previous: float, revision_count: int, user_feedback: str | None = None
    ) -> LearningMetrics:
        """学習メトリクスを作成"""
        if not self.is_completed:
            msg = "セッションが完了していません"
            error_code = "session_not_completed"
            raise BusinessRuleViolationError(error_code, msg)

        return LearningMetrics(
            improvement_from_previous=improvement_from_previous,
            time_spent_writing=self.total_writing_time,
            revision_count=revision_count,
            user_feedback=user_feedback,
            writing_context=self.writing_environment,
        )

    def is_long_session(self, threshold_minutes: int = 120) -> bool:
        """長時間セッションかどうかを判定"""
        return self.total_writing_time >= threshold_minutes

    def is_short_session(self, threshold_minutes: int = 30) -> bool:
        """短時間セッションかどうかを判定"""
        return self.total_writing_time <= threshold_minutes

    def get_productivity_level(self) -> str:
        """生産性レベルを取得"""
        # 標準的な閾値を使用(120分を高生産性、30分を低生産性とする)
        if self.is_long_session(120):
            return "高生産性"
        if self.is_short_session(30):
            return "低生産性"
        return "標準生産性"
