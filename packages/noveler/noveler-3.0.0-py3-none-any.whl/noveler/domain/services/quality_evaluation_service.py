#!/usr/bin/env python3

"""Domain.services.quality_evaluation_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""品質評価サービス(ドメインサービス)

品質スコアの計算やグレード判定などのビジネスロジックを提供。
"""


from typing import Any, ClassVar

from noveler.domain.entities.quality_check_session import CheckType, QualityCheckResult, QualityGrade, QualityScore


class QualityEvaluationService:
    """品質評価サービス

    ビジネスルール:
    1. 各チェック項目の重み付け
    2. 総合スコアの計算方法
    3. グレード判定基準
    4. 改善優先度の決定
    """

    # デフォルトの重み設定
    DEFAULT_WEIGHTS: ClassVar[dict[CheckType, float]] = {
        CheckType.BASIC_STYLE: 0.25,
        CheckType.COMPOSITION: 0.25,
        CheckType.CHARACTER_CONSISTENCY: 0.20,
        CheckType.READABILITY: 0.20,
        CheckType.INVALID_KANJI: 0.10,
    }

    # グレード判定基準
    GRADE_THRESHOLDS: ClassVar[dict[QualityGrade, int]] = {
        QualityGrade.S: 90,
        QualityGrade.A: 80,
        QualityGrade.B: 70,
        QualityGrade.C: 60,
        QualityGrade.D: 0,
    }

    def __init__(self, custom_weights: dict[CheckType, float] | None = None) -> None:
        """初期化

        Args:
            custom_weights: カスタム重み設定
        """
        self.weights = custom_weights or self.DEFAULT_WEIGHTS.copy()

    def calculate_weighted_score(
        self,
        check_results: list[QualityCheckResult],
    ) -> QualityScore:
        """重み付けスコアを計算

        Args:
            check_results: チェック結果リスト

        Returns:
            重み付け総合スコア
        """
        if not check_results:
            return QualityScore(0.0)

        total_weight = 0.0
        weighted_sum = 0.0

        for result in check_results:
            weight = self.weights.get(result.check_type, 0.0)
            weighted_sum += result.score.value * weight
            total_weight += weight

        if total_weight == 0:
            # 重みが設定されていない場合は単純平均
            avg_score = sum(r.score.value for r in check_results) / len(check_results)
            return QualityScore(avg_score)

        return QualityScore(weighted_sum / total_weight)

    def determine_grade(self, score: QualityScore) -> QualityGrade:
        """スコアからグレードを判定

        Args:
            score: 品質スコア

        Returns:
            品質グレード
        """
        for grade, threshold in self.GRADE_THRESHOLDS.items():
            if score.value >= threshold:
                return grade
        return QualityGrade.D

    def identify_weak_areas(
        self, check_results: list[QualityCheckResult], threshold: float = 70.0
    ) -> list[tuple[CheckType, float]]:
        """弱点領域を特定

        Args:
            check_results: チェック結果リスト
            threshold: 閾値(これ以下を弱点とする)

        Returns:
            弱点領域のリスト(チェックタイプ、スコア)
        """
        # 弱点領域を抽出しスコアの低い順にソート
        weak_areas = [
            (result.check_type, result.score.value) for result in check_results if result.score.value < threshold
        ]

        # スコアの低い順にソート
        return sorted(weak_areas, key=lambda x: x[1])

    def calculate_improvement_priority(
        self,
        check_results: list[QualityCheckResult],
    ) -> list[dict[str, Any]]:
        """改善優先度を計算

        Args:
            check_results: チェック結果リスト

        Returns:
            改善優先度リスト
        """
        priorities = []

        for result in check_results:
            # 重みとスコアから改善効果を計算
            weight = self.weights.get(result.check_type, 0.0)
            potential_improvement = (100 - result.score.value) * weight

            # エラー数も考慮
            error_impact = result.error_count * 5  # エラー1件につき5ポイント

            priority_score = potential_improvement + error_impact

            priorities.append(
                {
                    "check_type": result.check_type,
                    "current_score": result.score.value,
                    "priority_score": priority_score,
                    "potential_improvement": potential_improvement,
                    "weight": weight,
                }
            )

        # 優先度スコアの高い順にソート
        return sorted(priorities, key=lambda x: x["priority_score"], reverse=True)

    def generate_improvement_plan(
        self, check_results: list[QualityCheckResult], target_grade: QualityGrade
    ) -> dict[str, Any]:
        """改善計画を生成

        Args:
            check_results: チェック結果リスト
            target_grade: 目標グレード

        Returns:
            改善計画
        """
        current_score = self.calculate_weighted_score(check_results)
        current_grade = self.determine_grade(current_score)
        target_score = self.GRADE_THRESHOLDS[target_grade]

        score_gap = max(target_score - current_score.value, 0.0)

        plan = {
            "current_score": current_score.value,
            "current_grade": current_grade.value,
            "target_score": target_score,
            "target_grade": target_grade.value,
            "score_gap": score_gap,
            "improvement_steps": [],
        }

        if score_gap <= 0:
            plan["message"] = "既に目標グレードを達成しています"
            return plan

        # 改善優先度に基づいてステップを生成
        priorities = self.calculate_improvement_priority(check_results)

        for priority in priorities[:3]:  # 上位3つの改善項目
            check_type = priority["check_type"]
            current = priority["current_score"]

            # 必要な改善幅を計算
            weight = priority["weight"]
            if weight <= 0:
                weight = 1.0
            required_improvement = score_gap / weight
            target_item_score = min(current + required_improvement, 100)

            step = {
                "check_type": check_type.value,
                "current_score": current,
                "target_score": target_item_score,
                "improvement_needed": target_item_score - current,
                "priority": "high" if priority["priority_score"] > 20 else "medium",
                "estimated_impact": priority["potential_improvement"],
            }
            plan["improvement_steps"].append(step)

        return plan

    def validate_weights(self, weights: dict[CheckType, float]) -> bool:
        """重み設定の妥当性を検証

        Args:
            weights: 重み設定

        Returns:
            妥当性(合計が1.0に近いか)
        """
        total = sum(weights.values())
        return 0.99 <= total <= 1.01  # 誤差を許容
