"""Domain.entities.bulk_quality_check
Where: Domain entity representing bulk quality check runs.
What: Stores batch parameters, per-episode results, and summaries.
Why: Enables aggregated quality insights across multiple episodes.
"""

from __future__ import annotations

"""全話品質チェック エンティティ"""


from dataclasses import dataclass
from typing import TYPE_CHECKING

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

if TYPE_CHECKING:
    from datetime import datetime


# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


@dataclass
class BulkQualityCheck:
    """全話品質チェック エンティティ"""

    project_name: str
    episode_range: tuple[int, int] | None = None
    parallel: bool = False
    include_archived: bool = False
    force_recheck: bool = False

    def __post_init__(self) -> None:
        if not self.project_name.strip():
            msg = "Project name cannot be empty"
            raise ValueError(msg)


@dataclass
class QualityRecord:
    """品質記録"""

    episode_number: int
    quality_score: float
    category_scores: dict
    timestamp: datetime


@dataclass
class QualityTrend:
    """品質トレンド"""

    direction: str  # "improving", "stable", "declining"
    slope: float
    confidence: float


class QualityHistory:
    """品質記録履歴"""

    def __init__(self, project_name: str) -> None:
        self.project_name = project_name
        self.records: list[QualityRecord] = []

    def add_record(self, episode_number: int, quality_result: dict) -> None:
        """品質記録を追加"""
        record = QualityRecord(
            episode_number=episode_number,
            quality_score=quality_result.overall_score.to_float(),
            category_scores=quality_result.category_scores.to_dict(),
            timestamp=project_now().datetime,
        )

        self.records.append(record)

    def calculate_trend(self) -> QualityTrend:
        """品質トレンドを計算"""
        if len(self.records) < 2:
            return QualityTrend(direction="stable", slope=0.0, confidence=0.0)

        # 簡単な線形回帰でトレンドを計算
        scores = [record.quality_score for record in self.records]
        x_values = list(range(len(scores)))

        # 傾きを計算
        n = len(scores)
        sum_x = sum(x_values)
        sum_y = sum(scores)
        sum_xy = sum(x * y for x, y in zip(x_values, scores, strict=False))
        sum_x2 = sum(x * x for x in x_values)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)

        # 方向を判定
        if slope > 1.0:
            direction = "improving"
        elif slope < -1.0:
            direction = "declining"
        else:
            direction = "stable"

        # 信頼度を計算(簡易版)
        confidence = min(abs(slope) / 5.0, 1.0)

        return QualityTrend(direction=direction, slope=slope, confidence=confidence)

    def find_problematic_episodes(self, threshold: float = 70.0) -> list[int]:
        """問題のあるエピソードを特定"""
        return [record.episode_number for record in self.records if record.quality_score < threshold]
