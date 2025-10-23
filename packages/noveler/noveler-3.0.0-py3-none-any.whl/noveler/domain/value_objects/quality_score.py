#!/usr/bin/env python3
# File: src/noveler/domain/value_objects/quality_score.py
# Purpose: Represent scalar manuscript or episode quality scores with domain validation and helpers.
# Context: Shared across application and domain layers when tracking aggregate quality metrics.

"""品質スコア値オブジェクト

整数スコア(0-100)を表すイミュータブルな値オブジェクト。
品質チェックや履歴管理で共通利用される。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from noveler.domain.exceptions import DomainException


@dataclass(frozen=True, slots=True, init=False)
class QualityScore:
    """品質スコアを表す単純な値オブジェクト。"""

    value: int

    # Small flyweight cache for 0..100 values to accelerate repeated construction
    _CACHE: ClassVar[dict[int, "QualityScore"]] = {}

    def __new__(cls, value: int):
        # Fast path: cache in valid range
        if isinstance(value, int) and 0 <= value <= 100:
            cached = cls._CACHE.get(value)
            if cached is not None:
                return cached
            self = object.__new__(cls)
            # Bypass __init__/__post_init__ by init=False; set attribute directly
            object.__setattr__(self, "value", value)
            cls._CACHE[value] = self
            return self
        # Validation for invalid types/ranges
        if not isinstance(value, int):
            raise DomainException("品質スコアは整数である必要があります")
        if value < 0:
            raise DomainException(f"品質スコアは0以上である必要があります: {value}")
        if value > 100:
            raise DomainException(f"品質スコアは100以下である必要があります: {value}")
        return object.__new__(cls)

    def __init__(self, value: int):
        # no-op; initialization handled in __new__
        pass

    MIN_SCORE = 0
    MAX_SCORE = 100
    DEFAULT_PASSING_THRESHOLD = 70

    def __post_init__(self) -> None:
        # Validation handled in __new__; keep for compatibility
        return

    # ------------------------------------------------------------------
    # 表示系ユーティリティ
    # ------------------------------------------------------------------
    def format(self) -> str:
        """人間向け形式でスコアを返す。"""
        return f"{self.value}点"

    def __str__(self) -> str:  # pragma: no cover - format()で検証済
        return self.format()

    # ------------------------------------------------------------------
    # 比較演算子
    # ------------------------------------------------------------------
    def _coerce_other(self, other: object) -> QualityScore | None:
        return other if isinstance(other, QualityScore) else None

    def __lt__(self, other: object) -> bool:
        other_score = self._coerce_other(other)
        if other_score is None:
            return NotImplemented
        return self.value < other_score.value

    def __le__(self, other: object) -> bool:
        other_score = self._coerce_other(other)
        if other_score is None:
            return NotImplemented
        return self.value <= other_score.value

    def __gt__(self, other: object) -> bool:
        other_score = self._coerce_other(other)
        if other_score is None:
            return NotImplemented
        return self.value > other_score.value

    def __ge__(self, other: object) -> bool:
        other_score = self._coerce_other(other)
        if other_score is None:
            return NotImplemented
        return self.value >= other_score.value

    # ------------------------------------------------------------------
    # ドメインロジック
    # ------------------------------------------------------------------
    def get_grade(self) -> str:
        """スコアから品質グレードを算出。"""
        if self.value >= 90:
            return "S"
        if self.value >= 80:
            return "A"
        if self.value >= 70:
            return "B"
        if self.value >= 60:
            return "C"
        return "D"

    def is_passing(self, threshold: int = DEFAULT_PASSING_THRESHOLD) -> bool:
        """合格判定を行う。"""
        if not isinstance(threshold, int):
            msg = "threshold must be an integer"
            raise DomainException(msg)
        if not (self.MIN_SCORE <= threshold <= self.MAX_SCORE):
            msg = "threshold must be between 0 and 100"
            raise DomainException(msg)
        return self.value >= threshold

    def is_acceptable(self, threshold: int = DEFAULT_PASSING_THRESHOLD) -> bool:
        """仕様上の許容基準を満たすか。"""
        return self.is_passing(threshold)

    def get_feedback(self) -> str:
        """スコアに応じた簡易フィードバック。"""
        if self.value >= 90:
            return "素晴らしい品質です!"
        if self.value >= 80:
            return "良い品質です。"
        if self.value >= 70:
            return "標準的な品質です。"
        if self.value >= 60:
            return "改善の余地があります。"
        return "大幅な改善が必要です。"

    def get_improvement_suggestions(self) -> list[str]:
        """改善提案のテンプレートを返す。"""
        suggestions: list[str] = []
        if self.value >= 90:
            return ["細部を微調整し、文章のリズムを整えましょう"]

        suggestions.extend([
            "文章構成を見直し、段落ごとの流れを明確にしましょう",
            "読者視点でリズムと情報量のバランスを調整しましょう",
        ])

        if self.value < 70:
            suggestions.append("キャラクターの動機と感情描写を掘り下げましょう")
        if self.value < 50:
            suggestions.append("プロット全体の骨子を再検討し、山場を強化しましょう")

        return suggestions

    @classmethod
    def from_float(cls, value: float) -> QualityScore:
        """浮動小数点値から安全にQualityScoreを構築。"""
        if not isinstance(value, (int, float)):
            msg = "品質スコアは数値である必要があります"
            raise DomainException(msg)
        if value < cls.MIN_SCORE or value > cls.MAX_SCORE:
            msg = f"品質スコアは0以上100以下である必要があります: {value}"
            raise DomainException(msg)
        return cls(int(round(value)))
