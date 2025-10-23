"""Domain.services.quality_history_value_objects
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""
SPEC-QUALITY-002: 品質履歴管理 - 値オブジェクト定義

品質履歴管理に関する値オブジェクトを定義。
DDD設計に基づく不変オブジェクトとして実装。
"""


from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

if TYPE_CHECKING:
    from noveler.domain.value_objects.episode_number import EpisodeNumber
    from noveler.domain.value_objects.quality_score import QualityScore

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class AnalysisPeriod(Enum):
    """分析期間列挙型"""

    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"
    LAST_YEAR = "last_year"
    ALL_TIME = "all_time"


class TrendDirection(Enum):
    """トレンド方向列挙型"""

    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class QualityRecord:
    """品質記録値オブジェクト"""

    check_id: str
    timestamp: datetime
    overall_score: QualityScore
    category_scores: dict[str, QualityScore]
    improvement_suggestions: list[str]
    checker_version: str
    metadata: dict[str, Any]

    def __post_init__(self) -> None:
        """バリデーション"""
        if not self.check_id or not self.check_id.strip():
            msg = "チェックIDは必須です"
            raise ValueError(msg)
        if not isinstance(self.category_scores, dict):
            msg = "カテゴリスコアは辞書形式である必要があります"
            raise TypeError(msg)
        if not isinstance(self.improvement_suggestions, list):
            msg = "改善提案はリスト形式である必要があります"
            raise TypeError(msg)
        if not isinstance(self.metadata, dict):
            msg = "メタデータは辞書形式である必要があります"
            raise TypeError(msg)


@dataclass(frozen=True)
class ImprovementRate:
    """改善率値オブジェクト"""

    rate_per_day: float
    rate_per_week: float
    rate_per_month: float
    total_improvement: float

    def __post_init__(self) -> None:
        """バリデーション"""
        if not -100.0 <= self.total_improvement <= 100.0:
            msg = "改善率は-100.0から100.0の範囲である必要があります"
            raise ValueError(msg)


@dataclass(frozen=True)
class QualityPrediction:
    """品質予測値オブジェクト"""

    predicted_score: QualityScore
    confidence_level: float  # 0.0-1.0
    prediction_date: datetime
    factors: list[str]

    def __post_init__(self) -> None:
        """バリデーション"""
        if not 0.0 <= self.confidence_level <= 1.0:
            msg = "信頼度は0.0から1.0の範囲である必要があります"
            raise ValueError(msg)


@dataclass(frozen=True)
class QualityTrendAnalysis:
    """品質トレンド分析値オブジェクト"""

    period: AnalysisPeriod
    improvement_rate: float
    trend_direction: TrendDirection
    strongest_categories: list[str]
    weakest_categories: list[str]
    prediction: QualityPrediction | None = None

    def get_trend_summary(self) -> str:
        """トレンドサマリーを取得"""
        if self.trend_direction == TrendDirection.IMPROVING:
            return f"品質が{self.improvement_rate:.1f}%改善しています"
        if self.trend_direction == TrendDirection.DECLINING:
            return f"品質が{abs(self.improvement_rate):.1f}%低下しています"
        return "品質は安定しています"


@dataclass(frozen=True)
class ImprovementPattern:
    """改善パターン値オブジェクト"""

    pattern_id: str
    problem_type: str
    successful_solutions: list[str]
    effectiveness_score: float  # 0.0-1.0
    usage_frequency: int

    def __post_init__(self) -> None:
        """バリデーション"""
        if not 0.0 <= self.effectiveness_score <= 1.0:
            msg = "効果性スコアは0.0から1.0の範囲である必要があります"
            raise ValueError(msg)
        if self.usage_frequency < 0:
            msg = "使用頻度は負の値にできません"
            raise ValueError(msg)

    def calculate_priority_score(self) -> float:
        """優先度スコアを計算"""
        return self.effectiveness_score * min(self.usage_frequency / 10.0, 1.0)


@dataclass(frozen=True)
class QualityAnalysisSummary:
    """品質分析サマリー値オブジェクト"""

    total_checks: int
    average_score: QualityScore
    improvement_trend: TrendDirection
    most_improved_category: str | None
    most_problematic_category: str | None
    recent_improvement_rate: float

    def get_performance_level(self) -> str:
        """パフォーマンスレベルを取得"""
        avg = self.average_score.value
        if avg >= 90:
            return "excellent"
        if avg >= 80:
            return "good"
        if avg >= 70:
            return "fair"
        return "needs_improvement"


@dataclass(frozen=True)
class QualityHistory:
    """品質履歴値オブジェクト"""

    episode_number: EpisodeNumber
    history_records: list[QualityRecord]
    analysis_summary: QualityAnalysisSummary | None
    created_at: datetime

    def __post_init__(self) -> None:
        """バリデーション"""
        if not isinstance(self.history_records, list):
            msg = "履歴記録はリスト形式である必要があります"
            raise TypeError(msg)

    def get_trend_analysis(self, period: AnalysisPeriod) -> QualityTrendAnalysis:
        """トレンド分析を取得"""
        # 期間内の記録をフィルタ
        now = project_now().datetime
        period_start = self._get_period_start(now, period)

        period_records = [record for record in self.history_records if record.timestamp >= period_start]

        if len(period_records) < 2:
            return QualityTrendAnalysis(
                period=period,
                improvement_rate=0.0,
                trend_direction=TrendDirection.UNKNOWN,
                strongest_categories=[],
                weakest_categories=[],
            )

        # 改善率計算
        first_score = period_records[0].overall_score.value
        last_score = period_records[-1].overall_score.value
        improvement_rate = ((last_score - first_score) / first_score) * 100

        # トレンド方向判定
        if improvement_rate > 5.0:
            trend_direction = TrendDirection.IMPROVING
        elif improvement_rate < -5.0:
            trend_direction = TrendDirection.DECLINING
        else:
            trend_direction = TrendDirection.STABLE

        # カテゴリ別分析
        category_improvements = self._analyze_category_improvements(period_records)
        strongest = sorted(category_improvements.keys(), key=lambda k: category_improvements[k], reverse=True)[:3]
        weakest = sorted(category_improvements.keys(), key=lambda k: category_improvements[k])[:3]

        return QualityTrendAnalysis(
            period=period,
            improvement_rate=improvement_rate,
            trend_direction=trend_direction,
            strongest_categories=strongest,
            weakest_categories=weakest,
        )

    def get_improvement_rate(self) -> ImprovementRate:
        """改善率を取得"""
        if len(self.history_records) < 2:
            return ImprovementRate(0.0, 0.0, 0.0, 0.0)

        # 時系列でソート
        sorted_records = sorted(self.history_records, key=lambda r: r.timestamp)

        first_score = sorted_records[0].overall_score.value
        last_score = sorted_records[-1].overall_score.value
        total_improvement = last_score - first_score

        # 期間計算
        total_days = (sorted_records[-1].timestamp - sorted_records[0].timestamp).days
        if total_days == 0:
            return ImprovementRate(0.0, 0.0, 0.0, total_improvement)

        rate_per_day = total_improvement / total_days
        rate_per_week = rate_per_day * 7
        rate_per_month = rate_per_day * 30

        return ImprovementRate(
            rate_per_day=rate_per_day,
            rate_per_week=rate_per_week,
            rate_per_month=rate_per_month,
            total_improvement=total_improvement,
        )

    def _get_period_start(self, now: datetime, period: AnalysisPeriod) -> datetime:
        """期間の開始日時を取得"""
        if period == AnalysisPeriod.LAST_7_DAYS:
            return now - timedelta(days=7)
        if period == AnalysisPeriod.LAST_30_DAYS:
            return now - timedelta(days=30)
        if period == AnalysisPeriod.LAST_90_DAYS:
            return now - timedelta(days=90)
        if period == AnalysisPeriod.LAST_YEAR:
            return now - timedelta(days=365)
        # ALL_TIME
        return datetime.min.replace(tzinfo=timezone.utc)

    def _analyze_category_improvements(self, records: list[QualityRecord]) -> dict[str, float]:
        """カテゴリ別改善分析"""
        if len(records) < 2:
            return {}

        category_improvements = {}
        all_categories = set()

        for record in records:
            all_categories.update(record.category_scores.keys())

        for category in all_categories:
            # リスト内包表記で効率的にスコアを収集
            first_scores = [
                record.category_scores[category].value
                for record in records[: len(records) // 2]
                if category in record.category_scores
            ]

            last_scores = [
                record.category_scores[category].value
                for record in records[len(records) // 2 :]
                if category in record.category_scores
            ]

            if first_scores and last_scores:
                avg_first = sum(first_scores) / len(first_scores)
                avg_last = sum(last_scores) / len(last_scores)
                category_improvements[category] = avg_last - avg_first

        return category_improvements
