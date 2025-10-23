#!/usr/bin/env python3

"""Domain.ai_integration.value_objects.analysis_criteria
Where: Domain value object capturing criteria for AI integration analyses.
What: Encodes thresholds, weights, and parameters guiding benchmark evaluations.
Why: Keeps analysis criteria consistent across AI integration services.
"""

from __future__ import annotations

"""分析基準値オブジェクト

プロット分析の評価基準を表現する
"""


from dataclasses import dataclass
from enum import Enum


class CriteriaCategory(Enum):
    """評価カテゴリー"""

    STRUCTURE = "structure"  # 構成
    CHARACTERS = "characters"  # キャラクター
    THEMES = "themes"  # テーマ
    ORIGINALITY = "originality"  # 独創性
    TECHNICAL = "technical"  # 技術面


@dataclass(frozen=True)
class CriteriaWeight:
    """評価基準の重み(パーセンテージ)"""

    value: int

    def __post_init__(self) -> None:
        """重みの妥当性検証"""
        MAX_WEIGHT = 100
        if not 0 <= self.value <= MAX_WEIGHT:
            msg = f"重みは0以上100以下でなければなりません: {self.value}"
            raise ValueError(msg)


@dataclass(frozen=True)
class AnalysisCriteria:
    """分析基準

    カテゴリー、重み、評価要素を含む
    """

    category: CriteriaCategory
    weight: CriteriaWeight
    factors: list[str]

    def __post_init__(self) -> None:
        """評価要素の妥当性検証"""
        if not self.factors:
            msg = "評価要素は1つ以上必要です"
            raise ValueError(msg)

        # factorsをタプルに変換して不変性を保証
        object.__setattr__(self, "factors", tuple(self.factors))

    def has_factor(self, factor: str) -> bool:
        """特定の評価要素を含むかどうか"""
        return factor in self.factors
