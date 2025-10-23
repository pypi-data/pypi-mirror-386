# File: src/noveler/domain/writing_guide/models/validation_result.py
# Purpose: Define value object for content validation results.
# Context: Domain model representing validation outcomes with score and issues.

"""Value object for content validation results.

Purpose:
    Encapsulate validation outcome with issues, warnings, score, and recommendations.

Inputs:
    Validation issues, warnings, score, and recommendations.

Outputs:
    Immutable value object with validation state and query methods.

Preconditions:
    Score must be in range [0, 100].

Side Effects:
    None (immutable value object).

Exceptions:
    ValueError: When score is out of valid range.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ValidationResult:
    """Value object representing content validation outcome.

    Purpose:
        Provide immutable validation result with business logic for
        interpreting validation state.

    Attributes:
        issues: List of critical validation failures.
        warnings: List of non-critical validation concerns.
        score: Numeric quality score in range [0, 100].
        recommendations: List of suggested improvements.

    Preconditions:
        - score must be between 0 and 100 (inclusive)
        - issues, warnings, recommendations must not be None

    Side Effects:
        None (immutable).

    Exceptions:
        ValueError: When score is outside valid range or lists are None.
    """

    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    score: int = 100
    recommendations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate domain invariants.

        Purpose:
            Ensure score is within valid range and lists are not None.

        Raises:
            ValueError: When invariants are violated.

        Side Effects:
            None beyond potential exception.
        """
        if not (0 <= self.score <= 100):
            raise ValueError(f"Score must be in range [0, 100], got {self.score}")

        if self.issues is None:
            raise ValueError("issues must not be None")
        if self.warnings is None:
            raise ValueError("warnings must not be None")
        if self.recommendations is None:
            raise ValueError("recommendations must not be None")

    def is_valid(self) -> bool:
        """Check if validation passed without critical issues.

        Purpose:
            Business rule: Content is valid if no critical issues exist.

        Returns:
            bool: True if issues list is empty.

        Preconditions:
            None.

        Side Effects:
            None.

        Exceptions:
            None.
        """
        return len(self.issues) == 0

    def is_acceptable(self, threshold: int = 70) -> bool:
        """Check if score meets acceptance threshold.

        Purpose:
            Business rule: Determine if quality is acceptable for publication.

        Args:
            threshold: Minimum acceptable score (default 70).

        Returns:
            bool: True if score >= threshold and no critical issues.

        Preconditions:
            threshold should be in range [0, 100].

        Side Effects:
            None.

        Exceptions:
            None.
        """
        return self.is_valid() and self.score >= threshold

    def has_warnings(self) -> bool:
        """Check if validation produced warnings.

        Purpose:
            Business rule: Identify content needing improvement.

        Returns:
            bool: True if warnings list is non-empty.

        Preconditions:
            None.

        Side Effects:
            None.

        Exceptions:
            None.
        """
        return len(self.warnings) > 0

    def total_issue_count(self) -> int:
        """Calculate total number of issues and warnings.

        Purpose:
            Provide aggregate count of all validation concerns.

        Returns:
            int: Sum of issues and warnings counts.

        Preconditions:
            None.

        Side Effects:
            None.

        Exceptions:
            None.
        """
        return len(self.issues) + len(self.warnings)

    @classmethod
    def create_passed(cls, score: int = 100) -> "ValidationResult":
        """Factory method for creating successful validation result.

        Purpose:
            Convenient construction of clean validation outcome.

        Args:
            score: Quality score (default 100).

        Returns:
            ValidationResult: Instance with no issues or warnings.

        Preconditions:
            score must be in range [0, 100].

        Side Effects:
            None.

        Exceptions:
            ValueError: If score is invalid.
        """
        return cls(issues=[], warnings=[], score=score, recommendations=[])

    @classmethod
    def create_failed(cls, issues: list[str], score: int = 0) -> "ValidationResult":
        """Factory method for creating failed validation result.

        Purpose:
            Convenient construction of validation failure.

        Args:
            issues: List of critical validation failures.
            score: Quality score (default 0).

        Returns:
            ValidationResult: Instance with specified issues.

        Preconditions:
            issues must not be empty.
            score must be in range [0, 100].

        Side Effects:
            None.

        Exceptions:
            ValueError: If score is invalid or issues is empty.
        """
        if not issues:
            raise ValueError("issues must not be empty for failed validation")

        return cls(issues=issues, warnings=[], score=score, recommendations=[])
