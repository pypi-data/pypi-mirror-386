#!/usr/bin/env python3
"""プロットスコア値オブジェクト

プロット分析の評価スコアを表現する不変オブジェクト
"""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class PlotScore:
    """プロットの評価スコア(0-100)

    不変条件:
    - スコアは0以上100以下
    - グレードは自動計算される
    """

    value: int

    def __post_init__(self) -> None:
        """値の妥当性検証"""
        MAX_SCORE = 100
        if not 0 <= self.value <= MAX_SCORE:
            msg = f"プロットスコアは0以上100以下でなければなりません: {self.value}"
            raise ValueError(msg)

    @property
    def grade(self) -> Literal["S", "A", "B", "C", "D", "E"]:
        """スコアに基づくグレード評価"""
        GRADE_S_THRESHOLD = 90
        GRADE_A_THRESHOLD = 80
        GRADE_B_THRESHOLD = 70
        GRADE_C_THRESHOLD = 60
        GRADE_D_THRESHOLD = 50
        if self.value >= GRADE_S_THRESHOLD:
            return "S"
        if self.value >= GRADE_A_THRESHOLD:
            return "A"
        if self.value >= GRADE_B_THRESHOLD:
            return "B"
        if self.value >= GRADE_C_THRESHOLD:
            return "C"
        if self.value >= GRADE_D_THRESHOLD:
            return "D"
        return "E"

    def is_high_quality(self) -> bool:
        """高品質かどうか(80点以上)"""
        HIGH_QUALITY_THRESHOLD = 80
        return self.value >= HIGH_QUALITY_THRESHOLD

    def is_acceptable(self) -> bool:
        """許容範囲かどうか(60点以上)"""
        ACCEPTABLE_THRESHOLD = 60
        return self.value >= ACCEPTABLE_THRESHOLD

    def __str__(self) -> str:
        return f"{self.value}/100 ({self.grade})"
