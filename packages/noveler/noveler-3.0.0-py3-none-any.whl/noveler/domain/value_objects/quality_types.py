#!/usr/bin/env python3
"""
Quality Types - Domain Value Objects

Consolidated quality-related types and enums for the novel writing system.
Follows DDD principles with immutable value objects.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class QualityCheckType(Enum):
    """Quality check type enumeration"""

    BASIC = "basic"
    COMPREHENSIVE = "comprehensive"
    ADAPTIVE = "adaptive"
    VIEWPOINT_AWARE = "viewpoint_aware"
    A31_CHECKLIST = "a31_checklist"


class QualitySeverity(Enum):
    """Quality issue severity enumeration"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class QualityIssue:
    """Quality issue value object"""

    type: str
    severity: QualitySeverity
    message: str
    location: str | None = None
    line_number: int | None = None
    column_number: int | None = None
    suggestion: str | None = None
    auto_fixable: bool = False

    def __post_init__(self) -> None:
        """Validate quality issue data"""
        if not self.type.strip():
            msg = "Quality issue type cannot be empty"
            raise ValueError(msg)
        if not self.message.strip():
            msg = "Quality issue message cannot be empty"
            raise ValueError(msg)
        if self.line_number is not None and self.line_number < 1:
            msg = "Line number must be positive"
            raise ValueError(msg)
        if self.column_number is not None and self.column_number < 1:
            msg = "Column number must be positive"
            raise ValueError(msg)


@dataclass
class QualityScore:
    """Quality score value object"""

    category: str
    score: float
    max_score: float = 100.0
    percentage: float | None = None
    issues: list[QualityIssue] = None

    def __post_init__(self) -> None:
        """Validate and calculate derived values"""
        if not self.category.strip():
            msg = "Quality score category cannot be empty"
            raise ValueError(msg)
        if self.score < 0:
            msg = "Quality score cannot be negative"
            raise ValueError(msg)
        if self.max_score <= 0:
            msg = "Max score must be positive"
            raise ValueError(msg)
        if self.score > self.max_score:
            msg = "Score cannot exceed max score"
            raise ValueError(msg)

        # Calculate percentage if not provided
        if self.percentage is None:
            self.percentage = (self.score / self.max_score) * 100 if self.max_score > 0 else 0

        # Initialize issues list if not provided
        if self.issues is None:
            self.issues = []


@dataclass
class QualityCheckResult:
    """Quality check result value object"""

    success: bool
    check_type: QualityCheckType
    total_score: float
    max_total_score: float
    overall_percentage: float
    grade: str
    scores: list[QualityScore]
    all_issues: list[QualityIssue]
    suggestions: list[str]
    auto_fixed_content: str | None = None
    execution_time: float | None = None
    check_timestamp: datetime | None = None

    def __post_init__(self) -> None:
        """Validate quality check result"""
        if self.total_score < 0:
            msg = "Total score cannot be negative"
            raise ValueError(msg)
        if self.max_total_score <= 0:
            msg = "Max total score must be positive"
            raise ValueError(msg)
        if self.total_score > self.max_total_score:
            msg = "Total score cannot exceed max total score"
            raise ValueError(msg)
        if not (0 <= self.overall_percentage <= 100):
            msg = "Overall percentage must be between 0 and 100"
            raise ValueError(msg)
        if not self.grade.strip():
            msg = "Grade cannot be empty"
            raise ValueError(msg)

        # Initialize lists if not provided
        if self.scores is None:
            self.scores = []
        if self.all_issues is None:
            self.all_issues = []
        if self.suggestions is None:
            self.suggestions = []

    @property
    def error_count(self) -> int:
        """Get count of error-level issues"""
        return len([issue for issue in self.all_issues if issue.severity == QualitySeverity.ERROR])

    @property
    def warning_count(self) -> int:
        """Get count of warning-level issues"""
        return len([issue for issue in self.all_issues if issue.severity == QualitySeverity.WARNING])

    @property
    def critical_count(self) -> int:
        """Get count of critical-level issues"""
        return len([issue for issue in self.all_issues if issue.severity == QualitySeverity.CRITICAL])

    @property
    def has_critical_issues(self) -> bool:
        """Check if result has critical issues"""
        return self.critical_count > 0

    @property
    def issue_summary(self) -> dict[str, int]:
        """Get summary of issues by severity"""
        summary = {severity.value: 0 for severity in QualitySeverity}
        for issue in self.all_issues:
            summary[issue.severity.value] += 1
        return summary
