# File: src/noveler/domain/services/quality_trend_analyzer.py
# Purpose: Provide statistical analysis helpers for quality history trends and forecasts.
# Context: Invoked by quality history services to compute improvement metrics, trajectories, and insights.

"""Domain.services.quality_trend_analyzer
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

from typing import Any

"""
SPEC-QUALITY-002: 品質トレンド分析器

品質データの統計分析を行うドメインサービス。
DDD設計に基づく品質分析ビジネスロジックの実装。
"""


import statistics
from collections import defaultdict
from datetime import timedelta

from noveler.domain.services.quality_history_value_objects import (
    AnalysisPeriod,
    QualityPrediction,
    QualityRecord,
    QualityTrendAnalysis,
    TrendDirection,
)
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.value_objects.quality_score import QualityScore

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class QualityTrendAnalyzer:
    """品質トレンド分析器ドメインサービス"""

    def calculate_improvement_rate(self, records: list[QualityRecord]) -> float:
        """改善率を計算

        Args:
            records: 品質記録のリスト(時系列順)

        Returns:
            改善率(パーセンテージ)
        """
        if len(records) < 2:
            return 0.0

        sorted_records = sorted(records, key=self._get_record_timestamp)
        first_score = sorted_records[0].overall_score.value
        last_score = sorted_records[-1].overall_score.value

        if first_score == 0:
            return 0.0  # ゼロ除算回避

        return ((last_score - first_score) / first_score) * 100

    def identify_weak_areas(self, records: list[QualityRecord]) -> list[str]:
        """弱点領域を特定

        Args:
            records: 品質記録のリスト

        Returns:
            弱点カテゴリのリスト(スコア順)
        """
        if not records:
            return []

        # カテゴリ別平均スコアを計算
        category_scores = defaultdict(list)

        for record in records:
            for category, score in record.category_scores.items():
                category_scores[category].append(score.value)

        # 平均スコアを計算してソート
        category_averages = {}
        for category, scores in category_scores.items():
            if scores:
                category_averages[category] = statistics.mean(scores)

        # スコアの低い順にソート
        weak_areas = sorted(category_averages.keys(), key=lambda k: category_averages[k])

        # 平均以下のカテゴリのみ返す
        if category_averages:
            overall_average = statistics.mean(category_averages.values())
            weak_areas = [cat for cat in weak_areas if category_averages[cat] < overall_average]

        return weak_areas

    def predict_quality_trajectory(
        self, historical_data: list[QualityRecord], prediction_days: int
    ) -> QualityPrediction | None:
        """品質軌道を予測

        Args:
            historical_data: 履歴データ
            prediction_days: 予測日数

        Returns:
            品質予測、データ不足の場合はNone
        """
        if len(historical_data) < 3:
            return None

        sorted_data = sorted(historical_data, key=self._get_record_timestamp)

        # 線形回帰による簡易予測
        scores = [record.overall_score.value for record in sorted_data]
        n = len(scores)

        # 最近の傾向を重視した移動平均
        if n >= 5:
            recent_scores = scores[-5:]
            trend = (recent_scores[-1] - recent_scores[0]) / len(recent_scores)
        else:
            trend = (scores[-1] - scores[0]) / n

        # 予測スコア計算
        current_score = scores[-1]
        predicted_score_value = current_score + (trend * prediction_days)

        # スコア範囲制限
        predicted_score_value = max(0.0, min(100.0, predicted_score_value))

        # 信頼度計算(データ点数と傾向の一貫性から)
        confidence = min(1.0, n / 10.0)  # データが多いほど信頼度が高い

        # 分散による信頼度調整
        if n > 2:
            score_variance = statistics.variance(scores)
            confidence *= max(0.1, 1.0 - (score_variance / 1000.0))

        confidence = max(0.1, min(1.0, confidence))

        # 予測要因の特定
        factors = []
        if trend > 1.0:
            factors.append("継続的な改善傾向")
        elif trend < -1.0:
            factors.append("品質低下傾向")
        else:
            factors.append("安定した品質")

        if n > 2 and score_variance > 100:
            factors.append("品質のばらつきが大きい")

        return QualityPrediction(
            predicted_score=QualityScore.from_float(predicted_score_value),
            confidence_level=confidence,
            prediction_date=project_now().datetime + timedelta(days=prediction_days),
            factors=factors,
        )

    def analyze_category_trends(self, records: list[QualityRecord]) -> dict[str, QualityTrendAnalysis]:
        """カテゴリ別トレンド分析

        Args:
            records: 品質記録のリスト

        Returns:
            カテゴリ別のトレンド分析結果
        """
        if not records:
            return {}

        # カテゴリ別にレコードを分類
        category_records = defaultdict(list)

        for record in records:
            for category, score in record.category_scores.items():
                category_records[category].append(
                    QualityRecord(
                        check_id=record.check_id,
                        timestamp=record.timestamp,
                        overall_score=score,  # カテゴリスコアを総合スコアとして使用
                        category_scores={category: score},
                        improvement_suggestions=record.improvement_suggestions,
                        checker_version=record.checker_version,
                        metadata=record.metadata,
                    )
                )

        # カテゴリ別に分析実行
        category_analyses = {}

        for category, cat_records in category_records.items():
            if len(cat_records) >= 2:
                improvement_rate = self.calculate_improvement_rate(cat_records)

                # トレンド方向判定
                if improvement_rate > 5.0:
                    trend_direction = TrendDirection.IMPROVING
                elif improvement_rate < -5.0:
                    trend_direction = TrendDirection.DECLINING
                else:
                    trend_direction = TrendDirection.STABLE

                category_analyses[category] = QualityTrendAnalysis(
                    period=AnalysisPeriod.ALL_TIME,  # カテゴリ分析では全期間
                    improvement_rate=improvement_rate,
                    trend_direction=trend_direction,
                    strongest_categories=[category] if improvement_rate > 0 else [],
                    weakest_categories=[category] if improvement_rate < 0 else [],
                )

        return category_analyses

    def calculate_quality_velocity(self, records: list[QualityRecord]) -> dict[str, float]:
        """品質向上速度を計算

        Args:
            records: 品質記録のリスト

        Returns:
            各種速度指標の辞書
        """
        if len(records) < 2:
            return {"velocity": 0.0, "acceleration": 0.0}

        sorted_records = sorted(records, key=self._get_record_timestamp)

        # 速度計算(スコア変化 / 時間変化)
        total_score_change = sorted_records[-1].overall_score.value - sorted_records[0].overall_score.value
        total_time = sorted_records[-1].timestamp - sorted_records[0].timestamp
        total_time_days = max(1.0, total_time.total_seconds() / 86400.0)

        velocity = total_score_change / total_time_days

        # 加速度計算(近似)
        acceleration = 0.0
        if len(sorted_records) >= 4:
            # 前半と後半の速度を比較
            mid_point = len(sorted_records) // 2
            first_half = sorted_records[:mid_point]
            second_half = sorted_records[mid_point:]

            first_velocity = self._calculate_segment_velocity(first_half)
            second_velocity = self._calculate_segment_velocity(second_half)

            acceleration = second_velocity - first_velocity

        return {
            "velocity": velocity,
            "acceleration": acceleration,
            "total_change": total_score_change,
            "time_span_days": total_time_days,
        }

    def _calculate_segment_velocity(self, records: list[QualityRecord]) -> float:
        """セグメント速度を計算"""
        if len(records) < 2:
            return 0.0

        score_change = records[-1].overall_score.value - records[0].overall_score.value
        time_delta = records[-1].timestamp - records[0].timestamp
        time_days = max(1.0, time_delta.total_seconds() / 86400.0)

        return score_change / time_days

    @staticmethod
    def _get_record_timestamp(record: QualityRecord) -> Any:
        """品質記録のソート基準となるタイムスタンプを取得"""

        return getattr(record, "timestamp", getattr(record, "created_at", project_now().datetime))
