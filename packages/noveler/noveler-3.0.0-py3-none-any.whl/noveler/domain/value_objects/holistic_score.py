"""Domain.value_objects.holistic_score
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""統合スコア値オブジェクト

統合コンテキスト分析での包括的品質スコアを表現する値オブジェクト。
直接Claude分析レベルの詳細評価を数値化。
"""


from dataclasses import dataclass


@dataclass(frozen=True)
class HolisticScore:
    """統合品質スコア値オブジェクト

    統合コンテキスト分析による包括的品質評価スコア。
    0.0-100.0の範囲で、直接Claude分析レベルの詳細度を数値化。
    """

    value: float

    def __post_init__(self) -> None:
        """スコア値の妥当性検証"""
        if not isinstance(self.value, int | float):
            msg = f"スコア値は数値である必要があります: {type(self.value)}"
            raise ValueError(msg)

        if not (0.0 <= self.value <= 100.0):
            msg = f"スコア値は0.0-100.0の範囲である必要があります: {self.value}"
            raise ValueError(msg)

    @classmethod
    def from_phase_scores(
        cls, phase_scores: dict[str, float], weights: dict[str, float] | None = None
    ) -> HolisticScore:
        """段階別スコアから統合スコアを計算

        Args:
            phase_scores: 段階別スコア辞書
            weights: 段階別重み（デフォルト: 均等）

        Returns:
            HolisticScore: 計算された統合スコア
        """
        if not phase_scores:
            msg = "段階別スコアが空です"
            raise ValueError(msg)

        # デフォルト重み設定
        if weights is None:
            weights = dict.fromkeys(phase_scores.keys(), 1.0)

        # 重み付き平均計算
        weighted_sum = sum(score * weights.get(phase, 1.0) for phase, score in phase_scores.items())
        total_weight = sum(weights.get(phase, 1.0) for phase in phase_scores)

        if total_weight == 0:
            msg = "重みの合計が0です"
            raise ValueError(msg)

        holistic_value = weighted_sum / total_weight
        return cls(holistic_value)

    def get_grade(self) -> str:
        """スコアに基づくグレード取得

        Returns:
            str: グレード文字列
        """
        if self.value >= 95.0:
            return "S"
        if self.value >= 90.0:
            return "A"
        if self.value >= 80.0:
            return "B"
        if self.value >= 70.0:
            return "C"
        if self.value >= 60.0:
            return "D"
        return "F"

    def get_grade_description(self) -> str:
        """グレード説明の取得

        Returns:
            str: グレード説明
        """
        grade_descriptions = {
            "S": "卓越した品質 - 直接Claude分析レベル達成",
            "A": "優秀な品質 - 高度な統合分析結果",
            "B": "良好な品質 - 満足できる統合度",
            "C": "標準的品質 - 基本要件達成",
            "D": "要改善品質 - 部分的統合",
            "F": "大幅改善必要 - 統合分析推奨",
        }
        return grade_descriptions[self.get_grade()]

    def is_high_quality(self) -> bool:
        """高品質判定

        Returns:
            bool: 高品質（A以上）かどうか
        """
        return self.value >= 90.0

    def calculate_improvement_potential(self, target_score: float = 95.0) -> float:
        """改善ポテンシャルの計算

        Args:
            target_score: 目標スコア

        Returns:
            float: 改善ポテンシャル
        """
        if target_score <= self.value:
            return 0.0

        return target_score - self.value

    def __str__(self) -> str:
        """文字列表現"""
        return f"{self.value:.1f} ({self.get_grade()})"

    def __repr__(self) -> str:
        """開発者向け表現"""
        return f"HolisticScore(value={self.value}, grade='{self.get_grade()}')"
