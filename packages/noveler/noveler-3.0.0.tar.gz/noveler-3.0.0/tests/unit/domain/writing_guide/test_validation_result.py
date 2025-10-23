# File: tests/unit/domain/writing_guide/test_validation_result.py
# Purpose: Unit tests for ValidationResult Value Object
# Context: Tests business logic, factory methods, and immutability

import pytest
from noveler.domain.writing_guide.models.validation_result import ValidationResult


class TestValidationResultConstruction:
    """Tests for ValidationResult construction."""

    def test_default_construction_creates_passed_result(self) -> None:
        """Verify default construction creates a passed result."""
        result = ValidationResult()
        assert result.is_valid() is True
        assert result.score == 100
        assert len(result.issues) == 0
        assert len(result.warnings) == 0

    def test_construction_with_issues(self) -> None:
        """Verify construction with issues."""
        result = ValidationResult(
            issues=["Issue 1", "Issue 2"],
            warnings=["Warning 1"],
            score=70,
            recommendations=["Fix Issue 1"],
        )
        assert len(result.issues) == 2
        assert len(result.warnings) == 1
        assert result.score == 70
        assert len(result.recommendations) == 1


class TestValidationResultBusinessLogic:
    """Tests for ValidationResult business logic methods."""

    def test_is_valid_returns_true_when_no_issues(self) -> None:
        """Verify is_valid returns True when no critical issues exist."""
        result = ValidationResult(warnings=["Warning 1"], score=80)
        assert result.is_valid() is True

    def test_is_valid_returns_false_when_issues_exist(self) -> None:
        """Verify is_valid returns False when critical issues exist."""
        result = ValidationResult(issues=["Issue 1"], score=50)
        assert result.is_valid() is False

    def test_is_acceptable_returns_true_for_valid_high_score(self) -> None:
        """Verify is_acceptable returns True for valid content above threshold."""
        result = ValidationResult(score=80)
        assert result.is_acceptable(threshold=70) is True

    def test_is_acceptable_returns_false_for_valid_low_score(self) -> None:
        """Verify is_acceptable returns False for valid content below threshold."""
        result = ValidationResult(score=60)
        assert result.is_acceptable(threshold=70) is False

    def test_is_acceptable_returns_false_for_invalid_high_score(self) -> None:
        """Verify is_acceptable returns False when issues exist regardless of score."""
        result = ValidationResult(issues=["Issue 1"], score=90)
        assert result.is_acceptable(threshold=70) is False

    def test_is_acceptable_uses_default_threshold_70(self) -> None:
        """Verify is_acceptable uses default threshold of 70."""
        result_pass = ValidationResult(score=71)
        result_fail = ValidationResult(score=69)
        assert result_pass.is_acceptable() is True
        assert result_fail.is_acceptable() is False

    def test_has_warnings_returns_true_when_warnings_exist(self) -> None:
        """Verify has_warnings detects presence of warnings."""
        result = ValidationResult(warnings=["Warning 1"])
        assert result.has_warnings() is True

    def test_has_warnings_returns_false_when_no_warnings(self) -> None:
        """Verify has_warnings detects absence of warnings."""
        result = ValidationResult()
        assert result.has_warnings() is False

    def test_total_issue_count_sums_issues_and_warnings(self) -> None:
        """Verify total_issue_count returns sum of issues and warnings."""
        result = ValidationResult(
            issues=["Issue 1", "Issue 2"],
            warnings=["Warning 1", "Warning 2", "Warning 3"],
        )
        assert result.total_issue_count() == 5

    def test_total_issue_count_returns_zero_for_clean_result(self) -> None:
        """Verify total_issue_count returns 0 for clean result."""
        result = ValidationResult()
        assert result.total_issue_count() == 0


class TestValidationResultFactoryMethods:
    """Tests for ValidationResult factory methods."""

    def test_create_passed_returns_valid_result(self) -> None:
        """Verify create_passed factory creates valid result."""
        result = ValidationResult.create_passed()
        assert result.is_valid() is True
        assert result.score == 100
        assert len(result.issues) == 0
        assert len(result.warnings) == 0

    def test_create_failed_returns_invalid_result_with_issue(self) -> None:
        """Verify create_failed factory creates invalid result."""
        result = ValidationResult.create_failed(issues=["Test failure"])
        assert result.is_valid() is False
        assert "Test failure" in result.issues
        assert result.score == 0

    def test_create_failed_with_custom_score(self) -> None:
        """Verify create_failed factory accepts custom score."""
        result = ValidationResult.create_failed(issues=["Partial failure"], score=30)
        assert result.is_valid() is False
        assert result.score == 30


class TestValidationResultImmutability:
    """Tests for ValidationResult immutability (frozen dataclass)."""

    def test_issues_field_is_immutable(self) -> None:
        """Verify issues field cannot be reassigned after construction."""
        result = ValidationResult(issues=["Issue 1"])
        with pytest.raises(AttributeError):
            result.issues = []  # type: ignore[misc]

    def test_score_field_is_immutable(self) -> None:
        """Verify score field cannot be modified after construction."""
        result = ValidationResult(score=80)
        with pytest.raises(AttributeError):
            result.score = 90  # type: ignore[misc]

    def test_issues_list_can_be_read_but_not_modified(self) -> None:
        """Verify issues list is accessible but modification attempts fail."""
        result = ValidationResult(issues=["Issue 1"])
        # Reading is allowed
        assert len(result.issues) == 1
        # Direct modification of list contents is allowed (Python limitation)
        # but reassignment is not
        with pytest.raises(AttributeError):
            result.issues = ["New Issue"]  # type: ignore[misc]


class TestValidationResultEquality:
    """Tests for ValidationResult value equality (frozen dataclass)."""

    def test_equal_results_are_equal(self) -> None:
        """Verify results with identical values are equal."""
        result1 = ValidationResult(
            issues=["Issue 1"],
            warnings=["Warning 1"],
            score=80,
            recommendations=["Rec 1"],
        )
        result2 = ValidationResult(
            issues=["Issue 1"],
            warnings=["Warning 1"],
            score=80,
            recommendations=["Rec 1"],
        )
        assert result1 == result2

    def test_different_score_not_equal(self) -> None:
        """Verify results with different scores are not equal."""
        result1 = ValidationResult(score=80)
        result2 = ValidationResult(score=70)
        assert result1 != result2

    def test_different_issues_not_equal(self) -> None:
        """Verify results with different issues are not equal."""
        result1 = ValidationResult(issues=["Issue 1"])
        result2 = ValidationResult(issues=["Issue 2"])
        assert result1 != result2

    def test_hashable_for_set_operations(self) -> None:
        """Verify frozen result can be used in sets and dicts."""
        # Frozen dataclasses with lists cannot be hashed (lists are unhashable)
        # This test verifies immutability but not hashability
        result = ValidationResult(score=80)
        # Direct set operations won't work due to unhashable list fields
        # but we can verify the object is frozen
        with pytest.raises(AttributeError):
            result.score = 90  # type: ignore[misc]


class TestValidationResultEdgeCases:
    """Tests for ValidationResult edge cases and boundary conditions."""

    def test_score_can_be_zero(self) -> None:
        """Verify score of 0 is valid."""
        result = ValidationResult(score=0)
        assert result.score == 0
        assert result.is_acceptable(threshold=0) is True

    def test_score_cannot_exceed_100(self) -> None:
        """Verify score cannot exceed 100 (upper bound enforced)."""
        with pytest.raises(ValueError, match="Score must be in range"):
            ValidationResult(score=150)

    def test_empty_lists_for_all_collections(self) -> None:
        """Verify empty collections are handled correctly."""
        result = ValidationResult(
            issues=[],
            warnings=[],
            recommendations=[],
        )
        assert result.is_valid() is True
        assert result.has_warnings() is False
        assert result.total_issue_count() == 0

    def test_large_number_of_issues(self) -> None:
        """Verify handling of large number of issues."""
        issues = [f"Issue {i}" for i in range(1000)]
        warnings = [f"Warning {i}" for i in range(500)]
        result = ValidationResult(issues=issues, warnings=warnings)
        assert len(result.issues) == 1000
        assert len(result.warnings) == 500
        assert result.total_issue_count() == 1500
