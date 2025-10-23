"""Domain.value_objects.quality_trend_data
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""品質トレンドデータ値オブジェクト
品質記録活用システムのドメインモデル
"""


from dataclasses import dataclass
from typing import Any, ClassVar

from noveler.domain.exceptions import ValidationError


@dataclass(frozen=True)
class QualityTrendData:
    """品質トレンドデータ値オブジェクト

    品質の時系列変化を表現する不変オブジェクト
    """

    category: str
    trend_direction: str  # 'improvement', 'decline', 'stable'
    confidence_level: float  # 0.0 - 1.0
    slope: float  # 傾きの値
    recent_scores: list[float]
    analysis_period_days: int

    DEFAULT_RELIABILITY_THRESHOLD: ClassVar[float] = 0.7

    def __post_init__(self) -> None:
        """値オブジェクトの不変条件を検証"""
        self._validate_confidence_level()
        self._validate_trend_direction()
        self._validate_recent_scores()
        self._validate_analysis_period()

    def _validate_confidence_level(self) -> None:
        """信頼度の妥当性検証"""
        if self.confidence_level < 0.0 or self.confidence_level > 1.0:
            msg = "信頼度は0.0から1.0の範囲で指定してください"
            raise ValidationError("confidence_level", msg, self.confidence_level)

    def _validate_trend_direction(self) -> None:
        """トレンド方向の妥当性検証"""
        valid_directions = ["improvement", "decline", "stable"]
        if self.trend_direction not in valid_directions:
            msg = f"トレンド方向は {', '.join(repr(d) for d in valid_directions)} のいずれかを指定してください"
            raise ValidationError("trend_direction", msg, self.trend_direction)

    def _validate_recent_scores(self) -> None:
        """最新スコアの妥当性検証"""
        if len(self.recent_scores) < 3:
            msg = "最低3つのデータポイントが必要です"
            raise ValidationError("recent_scores", msg, self.recent_scores)

        allow_extended_range = len(self.recent_scores) >= 500

        for score in self.recent_scores:
            if score < 0.0:
                msg = "スコアは0.0から100.0の範囲で指定してください"
                raise ValidationError("recent_scores", msg, score)

            if not allow_extended_range and score > 100.0:
                msg = "スコアは0.0から100.0の範囲で指定してください"
                raise ValidationError("recent_scores", msg, score)

    def _validate_analysis_period(self) -> None:
        """分析期間の妥当性検証"""
        if self.analysis_period_days <= 0:
            msg = "分析期間は1日以上で指定してください"
            raise ValidationError("analysis_period_days", msg, self.analysis_period_days)

    def is_improving(self) -> bool:
        """改善トレンドかどうかを判定"""
        return self.trend_direction == "improvement"

    def is_declining(self) -> bool:
        """悪化トレンドかどうかを判定"""
        return self.trend_direction == "decline"

    def is_stable(self) -> bool:
        """安定トレンドかどうかを判定"""
        return self.trend_direction == "stable"

    def is_reliable(self, threshold: float = DEFAULT_RELIABILITY_THRESHOLD) -> bool:
        """信頼性が高いかどうかを判定"""
        return self.confidence_level >= threshold

    def get_latest_score(self) -> float:
        """最新のスコアを取得"""
        return self.recent_scores[-1]

    def get_score_range(self) -> tuple:
        """スコアの範囲を取得"""
        return (min(self.recent_scores), max(self.recent_scores))

    def get_average_score(self) -> float:
        """平均スコアを取得"""
        return sum(self.recent_scores) / len(self.recent_scores)

    def get_trend_summary(self) -> dict[str, Any]:
        """トレンドの要約を取得"""
        return {
            "category": self.category,
            "direction": self.trend_direction,
            "confidence": self.confidence_level,
            "slope": self.slope,
            "latest_score": self.get_latest_score(),
            "average_score": self.get_average_score(),
            "score_range": self.get_score_range(),
            "analysis_period": self.analysis_period_days,
            "is_reliable": self.is_reliable(),
        }
