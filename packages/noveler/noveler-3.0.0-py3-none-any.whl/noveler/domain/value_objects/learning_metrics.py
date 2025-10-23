#!/usr/bin/env python3
"""学習メトリクス値オブジェクト
品質記録活用システムのドメインモデル
"""

from dataclasses import dataclass

from noveler.domain.exceptions import ValidationError


@dataclass(frozen=True)
class LearningMetrics:
    """学習メトリクス値オブジェクト

    執筆者の学習に関する定量的・定性的データを管理する不変オブジェクト
    """

    improvement_from_previous: float
    time_spent_writing: int  # 分単位
    revision_count: int
    user_feedback: str | None = None
    writing_context: str | None = None

    def __post_init__(self) -> None:
        """値オブジェクトの不変条件を検証"""
        self._validate_improvement_rate()
        self._validate_time_spent()
        self._validate_revision_count()

    def _validate_improvement_rate(self) -> None:
        """改善率の妥当性検証"""
        if self.improvement_from_previous < -100.0 or self.improvement_from_previous > 100.0:
            raise ValidationError(
                "improvement_from_previous",
                "改善率は-100%から100%の範囲で指定してください",
                self.improvement_from_previous,
            )

    def _validate_time_spent(self) -> None:
        """執筆時間の妥当性検証"""
        if self.time_spent_writing < 0:
            raise ValidationError(
                "time_spent_writing",
                "執筆時間は0分以上で指定してください",
                self.time_spent_writing,
            )

    def _validate_revision_count(self) -> None:
        """リビジョン数の妥当性検証"""
        if self.revision_count < 0:
            raise ValidationError(
                "revision_count",
                "リビジョン数は0以上で指定してください",
                self.revision_count,
            )

    def is_improvement(self) -> bool:
        """改善しているかどうかを判定"""
        return self.improvement_from_previous > 0

    def is_significant_improvement(self, threshold: float) -> bool:
        """有意な改善があるかどうかを判定"""
        return self.improvement_from_previous >= threshold

    def get_learning_efficiency(self) -> float:
        """学習効率を計算(改善率/執筆時間)"""
        if self.time_spent_writing == 0:
            return 0.0
        return self.improvement_from_previous / self.time_spent_writing

    def get_quality_description(self) -> str:
        """品質の説明を取得"""
        if self.improvement_from_previous > 10:
            return "大幅な改善"
        if self.improvement_from_previous > 5:
            return "改善"
        if self.improvement_from_previous > -5:
            return "現状維持"
        return "要改善"
