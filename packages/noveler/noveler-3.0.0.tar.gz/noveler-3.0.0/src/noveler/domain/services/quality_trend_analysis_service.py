#!/usr/bin/env python3

"""Domain.services.quality_trend_analysis_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""品質トレンド分析サービス
品質記録活用システムのドメインサービス
"""


import statistics
from datetime import datetime
from typing import Any

from noveler.domain.exceptions import InsufficientDataError
from noveler.domain.value_objects.quality_trend_data import QualityTrendData


class QualityTrendAnalysisService:
    """品質トレンド分析サービス

    品質データの時系列分析を行うドメインサービス
    """

    def __init__(self, minimum_data_points: int = 3) -> None:
        self.minimum_data_points = minimum_data_points

    def analyze_quality_trend(
        self, category: str, scores: list[float], analysis_period_days: int = 30
    ) -> QualityTrendData:
        """品質トレンドを分析"""

        # データ不足チェック
        if len(scores) < self.minimum_data_points:
            msg = f"トレンド分析には最低{self.minimum_data_points}つのデータポイントが必要です"
            raise ValueError(msg)

        # 線形回帰による傾きの計算
        slope = self._calculate_slope(scores)

        # トレンド方向の判定
        trend_direction = self._determine_trend_direction(slope)

        # 信頼度の計算
        confidence_level = self._calculate_confidence_level(scores, slope)

        return QualityTrendData(
            category=category,
            trend_direction=trend_direction,
            confidence_level=confidence_level,
            slope=slope,
            recent_scores=scores,
            analysis_period_days=analysis_period_days,
        )

    def _calculate_slope(self, scores: list[float]) -> float:
        """スコアの傾きを計算(線形回帰)"""
        n = len(scores)
        if n < 2:
            return 0.0

        # x値は単純にインデックス
        x_values = list(range(n))

        # 線形回帰の計算
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(scores)

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, scores, strict=False))
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        if denominator == 0:
            return 0.0

        return numerator / denominator

    def _determine_trend_direction(self, slope: float, threshold: float = 0.1) -> str:
        """傾きからトレンド方向を判定"""
        if slope > threshold:
            return "improvement"
        if slope < -threshold:
            return "decline"
        return "stable"

    def _calculate_confidence_level(self, scores: list[float], _slope: float) -> float:
        """信頼度を計算"""
        if len(scores) < 2:
            return 0.0

        # 標準偏差を基に信頼度を計算
        std_dev = statistics.stdev(scores)
        mean_score = statistics.mean(scores)

        # 変動係数を計算
        if mean_score == 0:
            return 0.0

        coefficient_of_variation = std_dev / mean_score

        # 信頼度の計算(変動が小さいほど信頼度が高い)
        confidence = max(0.0, min(1.0, 1.0 - coefficient_of_variation))

        # データポイント数による重み付け
        data_point_weight = min(1.0, len(scores) / 10.0)

        return confidence * data_point_weight

    def analyze_quality_progression(self, quality_records: list[Any]) -> QualityTrendData:
        """品質記録のリストから品質推移を分析"""

        if len(quality_records) < self.minimum_data_points:
            msg = f"品質推移分析には最低{self.minimum_data_points}つの記録が必要です"
            raise InsufficientDataError(msg)

        # 全体的なスコアを抽出
        overall_scores = [record.overall_score for record in quality_records]

        # 期間の計算(最初と最後の記録の日数差)
        if hasattr(quality_records[0], "timestamp") and hasattr(quality_records[-1], "timestamp"):
            start_date = quality_records[0].timestamp
            end_date = quality_records[-1].timestamp

            if isinstance(start_date, datetime) and isinstance(end_date, datetime):
                analysis_period_days = (end_date - start_date).days
            else:
                analysis_period_days = 30  # デフォルト値
        else:
            analysis_period_days = 30

        return self.analyze_quality_trend(
            category="overall", scores=overall_scores, analysis_period_days=analysis_period_days
        )

    def detect_quality_patterns(self, trend_data: QualityTrendData) -> list[dict[str, Any]]:
        """品質パターンを検出"""
        patterns = []

        # 停滞パターンの検出
        if trend_data.is_stable() and trend_data.is_reliable():
            patterns.append(
                {"type": "stagnation", "description": "品質が停滞しています。新しい改善アプローチを試してみましょう"}
            )

        # 急激な改善パターンの検出
        if trend_data.is_improving() and trend_data.slope > 2.0:
            patterns.append(
                {"type": "rapid_improvement", "description": "品質が急激に改善しています。この調子を維持しましょう"}
            )

        # 悪化パターンの検出
        if trend_data.is_declining() and trend_data.is_reliable():
            patterns.append(
                {"type": "decline", "description": "品質が低下傾向にあります。基本に立ち返って見直しましょう"}
            )

        return patterns

    def get_trend_statistics(self, trend_data: QualityTrendData) -> dict[str, float]:
        """トレンドの統計情報を取得"""
        scores = trend_data.recent_scores

        return {
            "mean": statistics.mean(scores),
            "median": statistics.median(scores),
            "std_dev": statistics.stdev(scores) if len(scores) > 1 else 0.0,
            "min_score": min(scores),
            "max_score": max(scores),
            "range": max(scores) - min(scores),
            "slope": trend_data.slope,
            "confidence": trend_data.confidence_level,
        }
