"""Domain.value_objects.validation_result
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""検証結果を表現する値オブジェクト

ファイルやコンテンツの検証結果を表現する不変オブジェクト
"""


from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ValidationLevel(Enum):
    """検証レベル"""

    ERROR = "error"  # エラー(必須項目の不足など)
    WARNING = "warning"  # 警告(推奨項目の不足など)
    INFO = "info"  # 情報(改善提案など)


@dataclass(frozen=True)
class ValidationIssue:
    """検証で発見された問題"""

    level: ValidationLevel
    message: str
    field_path: str = ""  # 問題のあるフィールドのパス(例: "chapters[0].title")
    suggestion: str = ""  # 修正方法の提案


@dataclass(frozen=True)
class ValidationResult:
    """検証結果"""

    is_valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    validated_fields: dict[str, Any] = field(default_factory=dict)  # 検証済みフィールドの値

    @property
    def has_errors(self) -> bool:
        """エラーが存在するか"""
        return any(issue.level == ValidationLevel.ERROR for issue in self.issues)

    @property
    def has_warnings(self) -> bool:
        """警告が存在するか"""
        return any(issue.level == ValidationLevel.WARNING for issue in self.issues)

    @property
    def error_count(self) -> int:
        """エラー数"""
        return sum(1 for issue in self.issues if issue.level == ValidationLevel.ERROR)

    @property
    def warning_count(self) -> int:
        """警告数"""
        return sum(1 for issue in self.issues if issue.level == ValidationLevel.WARNING)

    def get_errors(self) -> list[ValidationIssue]:
        """エラーレベルの問題のみ取得"""
        return [issue for issue in self.issues if issue.level == ValidationLevel.ERROR]

    def get_warnings(self) -> list[ValidationIssue]:
        """警告レベルの問題のみ取得"""
        return [issue for issue in self.issues if issue.level == ValidationLevel.WARNING]

    def merge(self, other: ValidationResult) -> ValidationResult:
        """他の検証結果とマージ"""
        return ValidationResult(
            is_valid=self.is_valid and other.is_valid,
            issues=self.issues + other.issues,
            validated_fields={**self.validated_fields, **other.validated_fields},
        )
