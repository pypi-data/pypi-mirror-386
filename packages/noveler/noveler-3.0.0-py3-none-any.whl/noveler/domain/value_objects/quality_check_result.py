"""Domain.value_objects.quality_check_result
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""品質チェック結果の値オブジェクト
DDD原則に従った不変な値オブジェクト実装
"""


from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True)
class QualityIssue:
    """品質問題の値オブジェクト"""

    category: str
    severity: str  # "critical", "warning", "info"
    message: str
    location: str | None = None
    suggestions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "category": self.category,
            "severity": self.severity,
            "message": self.message,
            "location": self.location,
            "suggestions": self.suggestions
        }


@dataclass(frozen=True)
class QualitySuggestion:
    """品質改善提案の値オブジェクト"""

    type: str
    description: str
    priority: str = "medium"  # "high", "medium", "low"

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "type": self.type,
            "description": self.description,
            "priority": self.priority
        }


@dataclass(frozen=True)
class QualityError:
    """品質チェックエラーの値オブジェクト"""

    type: str
    message: str
    line_number: int | None = None
    column: int | None = None
    severity: str = "error"  # "error", "warning", "info"
    fixed: bool = False
    suggestion: str | None = None

    def __post_init__(self) -> None:
        if self.type is None or self.type.strip() == "":
            msg = "Error type cannot be empty"
            raise ValueError(msg)
        if self.message is None or self.message.strip() == "":
            msg = "Error message cannot be empty"
            raise ValueError(msg)
        if self.severity not in ["error", "warning", "info"]:
            msg = f"Invalid severity: {self.severity}"
            raise ValueError(msg)
        if self.line_number is not None and self.line_number < 1:
            msg = "Line number must be positive"
            raise ValueError(msg)

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "type": self.type,
            "message": self.message,
            "line_number": self.line_number,
            "severity": self.severity,
            "fixed": self.fixed,
            "suggestion": self.suggestion,
        }


@dataclass(frozen=True)
class AutoFix:
    """自動修正情報の値オブジェクト"""

    type: str
    description: str
    count: int
    affected_lines: list[int] | None = None

    def __post_init__(self) -> None:
        if self.type is None or self.type.strip() == "":
            msg = "Fix type cannot be empty"
            raise ValueError(msg)
        if self.description is None or self.description.strip() == "":
            msg = "Fix description cannot be empty"
            raise ValueError(msg)
        if self.count < 0:
            msg = "Fix count cannot be negative"
            raise ValueError(msg)

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "type": self.type,
            "description": self.description,
            "count": self.count,
            "affected_lines": self.affected_lines,
        }


@dataclass(frozen=True)
class QualityScore:
    """品質スコアの値オブジェクト"""

    value: Decimal

    def __post_init__(self) -> None:
        if not (Decimal("0") <= self.value <= Decimal("100")):
            msg = f"Quality score must be between 0 and 100, got {self.value}"
            raise ValueError(msg)

    @classmethod
    def from_float(cls, value: float) -> QualityScore:
        """floatから安全に変換"""
        return cls(Decimal(str(value)))

    def to_float(self) -> float:
        """float表現に変換"""
        return float(self.value)

    def is_passing(self, threshold: Decimal) -> bool:
        """閾値を超えているかチェック"""
        return self.value >= threshold


@dataclass(frozen=True)
class CategoryScores:
    """カテゴリ別品質スコアの値オブジェクト"""

    basic_style: QualityScore
    composition: QualityScore
    character_consistency: QualityScore
    readability: QualityScore

    def overall_score(self) -> QualityScore:
        """総合スコアを計算"""
        total = (
            self.basic_style.value + self.composition.value + self.character_consistency.value + self.readability.value
        )

        average = total / Decimal("4")
        return QualityScore(average)

    def to_dict(self) -> dict[str, float]:
        """辞書形式に変換"""
        return {
            "basic_style": self.basic_style.to_float(),
            "composition": self.composition.to_float(),
            "character_consistency": self.character_consistency.to_float(),
            "readability": self.readability.to_float(),
        }


@dataclass(frozen=True)
class QualityCheckResult:
    """品質チェック結果の値オブジェクト(ルートアグリゲート)"""

    episode_number: int
    timestamp: datetime
    checker_version: str
    category_scores: CategoryScores
    errors: list[QualityError]
    warnings: list[QualityError]
    auto_fixes: list[AutoFix]
    word_count: int | None = None

    def __post_init__(self) -> None:
        if self.episode_number < 1:
            msg = "Episode number must be positive"
            raise ValueError(msg)
        if not self.checker_version.strip():
            msg = "Checker version cannot be empty"
            raise ValueError(msg)

        # リストの不変性確保
        object.__setattr__(self, "errors", tuple(self.errors))
        object.__setattr__(self, "warnings", tuple(self.warnings))
        object.__setattr__(self, "auto_fixes", tuple(self.auto_fixes))

    @property
    def overall_score(self) -> QualityScore:
        """総合品質スコア"""
        return self.category_scores.overall_score()

    @property
    def error_count(self) -> int:
        """エラー数"""
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        """警告数"""
        return len(self.warnings)

    @property
    def auto_fix_applied(self) -> bool:
        """自動修正が適用されたか"""
        return len(self.auto_fixes) > 0

    @property
    def total_fixes_count(self) -> int:
        """総修正回数"""
        return sum(fix.count for fix in self.auto_fixes)

    def is_high_quality(self, threshold: Decimal) -> bool:
        """高品質かどうか(85点以上)"""
        return self.overall_score.value >= threshold

    def has_critical_errors(self) -> bool:
        """重大エラーが存在するか"""
        return any(error.severity == "error" for error in self.errors)

    def to_summary_dict(self) -> dict:
        """サマリー辞書に変換(外部システム連携用)"""
        return {
            "episode_number": self.episode_number,
            "timestamp": self.timestamp.isoformat(),
            "overall_score": self.overall_score.to_float(),
            "category_scores": self.category_scores.to_dict(),
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "auto_fix_applied": self.auto_fix_applied,
            "total_fixes_count": self.total_fixes_count,
            "checker_version": self.checker_version,
            "errors": [error.to_dict() if hasattr(error, "to_dict") else error for error in self.errors],
            "warnings": [warning.to_dict() if hasattr(warning, "to_dict") else warning for warning in self.warnings],
            "auto_fixes": [fix.to_dict() if hasattr(fix, "to_dict") else fix for fix in self.auto_fixes],
        }
