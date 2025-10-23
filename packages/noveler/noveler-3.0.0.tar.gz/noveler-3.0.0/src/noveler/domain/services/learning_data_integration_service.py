#!/usr/bin/env python3

"""Domain.services.learning_data_integration_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""学習データ統合サービス
品質記録活用システムのドメインサービス
"""


import itertools
from typing import Any

from noveler.domain.exceptions import InsufficientDataError


class LearningDataIntegrationService:
    """学習データ統合サービス

    品質記録と学習データを統合して分析するドメインサービス
    """

    def __init__(self) -> None:
        self.improvement_threshold = 5.0
        self.decline_threshold = -5.0

    def integrate_learning_data(self, quality_record: object) -> dict[str, Any]:
        """学習データを統合"""

        if not quality_record.has_sufficient_data_for_analysis():
            msg = "統合には最低3つの品質記録が必要です"
            raise InsufficientDataError(msg)

        # 基本統計の計算
        total_writing_time = quality_record.get_total_writing_time()
        total_revisions = quality_record.get_total_revision_count()
        average_improvement_rate = quality_record.calculate_average_improvement_rate()

        # 強み・弱みの分析
        strengths = self._analyze_strengths(quality_record)
        areas_for_improvement = self._analyze_areas_for_improvement(quality_record)

        # 学習効率の計算
        learning_efficiency = self._calculate_learning_efficiency(quality_record)

        # 成長パターンの分析
        growth_patterns = self._analyze_growth_patterns(quality_record)

        return {
            "total_writing_time": total_writing_time,
            "total_revisions": total_revisions,
            "average_improvement_rate": average_improvement_rate,
            "learning_efficiency": learning_efficiency,
            "strengths": strengths,
            "areas_for_improvement": areas_for_improvement,
            "growth_patterns": growth_patterns,
            "data_quality": self._assess_data_quality(quality_record),
        }

    def _analyze_strengths(self, quality_record: object) -> list[str]:
        """強みを分析"""

        latest_scores = quality_record.get_latest_scores()
        strengths = []

        # 高スコアのカテゴリを特定
        for category, score in latest_scores.items():
            if score >= 80.0:
                strengths.append(f"{category}: {score:.1f}点")

        # 改善傾向のカテゴリを特定
        for category in latest_scores:
            trend = quality_record.get_improvement_trend(category)
            if len(trend) >= 3:
                recent_trend = trend[-3:]
                if all(current["score"] >= previous["score"] for previous, current in itertools.pairwise(recent_trend)):
                    strengths.append(f"{category}: 改善傾向継続中")

        return list(set(strengths))  # 重複を除去

    def _analyze_areas_for_improvement(self, quality_record: object) -> list[str]:
        """改善領域を分析"""

        latest_scores = quality_record.get_latest_scores()
        areas_for_improvement = []

        # 低スコアのカテゴリを特定
        for category, score in latest_scores.items():
            if score < 70.0:
                areas_for_improvement.append(f"{category}: {score:.1f}点")

        # 悪化傾向のカテゴリを特定
        for category in latest_scores:
            trend = quality_record.get_improvement_trend(category)
            if len(trend) >= 3:
                recent_trend = trend[-3:]
                if all(current["score"] < previous["score"] for previous, current in itertools.pairwise(recent_trend)):
                    areas_for_improvement.append(f"{category}: 悪化傾向")

        return list(set(areas_for_improvement))  # 重複を除去

    def _calculate_learning_efficiency(self, quality_record: object) -> float:
        """学習効率を計算"""

        if not quality_record.quality_checks:
            return 0.0

        total_improvement = 0.0
        total_time = 0.0

        for check in quality_record.quality_checks:
            improvement = check["learning_metrics"]["improvement_from_previous"]
            time_spent = check["learning_metrics"]["time_spent_writing"]

            total_improvement += improvement
            total_time += time_spent

        if total_time == 0:
            return 0.0

        return total_improvement / total_time

    def _analyze_growth_patterns(self, quality_record: object) -> dict[str, Any]:
        """成長パターンを分析"""

        patterns = {"consistent_improvement": False, "rapid_growth": False, "plateau": False, "regression": False}

        if len(quality_record.quality_checks) < 3:
            return patterns

        # 直近3回の改善率を取得
        recent_improvements = [
            check["learning_metrics"]["improvement_from_previous"] for check in quality_record.quality_checks[-3:]
        ]

        # 一貫した改善
        if all(rate > 0 for rate in recent_improvements):
            patterns["consistent_improvement"] = True

        # 急成長
        if any(rate > 10.0 for rate in recent_improvements):
            patterns["rapid_growth"] = True

        # 停滞
        if all(abs(rate) < 2.0 for rate in recent_improvements):
            patterns["plateau"] = True

        # 退行
        if all(rate < 0 for rate in recent_improvements):
            patterns["regression"] = True

        return patterns

    def _assess_data_quality(self, quality_record: object) -> dict[str, Any]:
        """データ品質を評価"""

        data_points = len(quality_record.quality_checks)

        # フィードバックの完全性
        feedback_completeness = (
            sum(1 for check in quality_record.quality_checks if check["learning_metrics"]["user_feedback"] is not None)
            / data_points
            if data_points > 0
            else 0
        )

        # データの一貫性
        consistency_score = self._calculate_consistency_score(quality_record)

        return {
            "data_points": data_points,
            "feedback_completeness": feedback_completeness,
            "consistency_score": consistency_score,
            "sufficient_for_analysis": data_points >= 3,
        }

    def _calculate_consistency_score(self, quality_record: object) -> float:
        """データの一貫性スコアを計算"""

        if len(quality_record.quality_checks) < 2:
            return 1.0

        # 執筆時間の変動を評価
        writing_times = [check["learning_metrics"]["time_spent_writing"] for check in quality_record.quality_checks]

        if len(writing_times) < 2:
            return 1.0

        # 標準偏差を計算
        mean_time = sum(writing_times) / len(writing_times)
        variance = sum((t - mean_time) ** 2 for t in writing_times) / len(writing_times)
        std_dev = variance**0.5

        # 変動係数を計算
        if mean_time == 0:
            return 0.0

        coefficient_of_variation = std_dev / mean_time

        # 一貫性スコア(変動が小さいほど高い)
        return max(0.0, 1.0 - coefficient_of_variation)

    def identify_learning_patterns(self, quality_record: object) -> dict[str, list[str]]:
        """学習パターンを特定"""

        patterns = {"improving_categories": [], "declining_categories": [], "stable_categories": []}

        if not quality_record.has_sufficient_data_for_analysis():
            return patterns

        # 各カテゴリの傾向を分析
        latest_scores = quality_record.get_latest_scores()

        for category in latest_scores:
            trend = quality_record.get_improvement_trend(category)

            if len(trend) >= 3:
                # 最初と最後のスコアを比較
                first_score = trend[0]["score"]
                last_score = trend[-1]["score"]
                improvement = last_score - first_score

                if improvement > self.improvement_threshold:
                    patterns["improving_categories"].append(category)
                elif improvement < self.decline_threshold:
                    patterns["declining_categories"].append(category)
                else:
                    patterns["stable_categories"].append(category)

        return patterns

    def integrate_quality_with_learning(
        self, quality_result: object, learning_metrics: object, previous_records: list[object] | None = None
    ) -> object:
        """品質結果と学習データを統合(互換性メソッド)"""

        # 改善率の計算
        improvement_rate = 0.0
        if previous_records:
            last_record = previous_records[-1]
            if hasattr(last_record, "overall_score") and hasattr(quality_result, "overall_score"):
                improvement_rate = quality_result.overall_score - last_record.overall_score

        # 学習効率の計算
        learning_efficiency = 0.0
        if hasattr(learning_metrics, "time_spent_writing") and learning_metrics.time_spent_writing > 0:
            learning_efficiency = improvement_rate / learning_metrics.time_spent_writing

        # 統合記録オブジェクトを作成
        class IntegratedRecord:
            def __init__(self, improvement_rate: float, learning_efficiency: float, is_first: bool = False) -> None:
                self.improvement_rate = improvement_rate
                self.learning_efficiency = learning_efficiency
                self._is_first = is_first

            def is_first_record(self) -> bool:
                return self._is_first

        is_first = len(previous_records or []) == 0
        return IntegratedRecord(
            improvement_rate=improvement_rate,
            learning_efficiency=learning_efficiency,
            is_first=is_first,
        )
