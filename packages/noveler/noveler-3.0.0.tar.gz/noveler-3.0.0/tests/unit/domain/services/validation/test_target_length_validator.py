# File: tests/unit/domain/services/validation/test_target_length_validator.py
# Purpose: Unit tests for TargetLengthValidator
# Context: Tests target_length validation and normalization logic

import pytest
from noveler.domain.services.validation import TargetLengthValidator
from noveler.domain.services.progressive_check_manager import ProjectConfigError


# ============================================================================
# Unit Tests - normalize_target_length
# ============================================================================


class TestNormalizeTargetLength:
    """Test normalize_target_length() behavior."""

    def test_normalize_valid_target_length(self):
        """normalize_target_length() should accept valid dict."""
        candidate = {"min": 3000, "max": 5000}

        result = TargetLengthValidator.normalize_target_length(
            candidate,
            source="test",
        )

        assert result["min"] == 3000
        assert result["max"] == 5000
        assert result["source"] == "test"

    def test_normalize_coerces_string_to_int(self):
        """normalize_target_length() should coerce string values to int."""
        candidate = {"min": "3000", "max": "5000"}

        result = TargetLengthValidator.normalize_target_length(
            candidate,
            source="test",
        )

        assert result["min"] == 3000
        assert result["max"] == 5000
        assert isinstance(result["min"], int)
        assert isinstance(result["max"], int)

    def test_normalize_coerces_float_to_int(self):
        """normalize_target_length() should coerce float values to int."""
        candidate = {"min": 3000.0, "max": 5000.9}

        result = TargetLengthValidator.normalize_target_length(
            candidate,
            source="test",
        )

        assert result["min"] == 3000
        assert result["max"] == 5000

    def test_normalize_raises_when_not_dict(self):
        """normalize_target_length() should raise when candidate is not dict."""
        with pytest.raises(ProjectConfigError) as exc_info:
            TargetLengthValidator.normalize_target_length(
                "not a dict",  # type: ignore[arg-type]
                source="test",
            )

        assert exc_info.value.code == "QC-010"
        assert "辞書形式ではありません" in str(exc_info.value)
        assert exc_info.value.details["source"] == "test"

    def test_normalize_raises_when_missing_min(self):
        """normalize_target_length() should raise when min is missing."""
        candidate = {"max": 5000}

        with pytest.raises(ProjectConfigError) as exc_info:
            TargetLengthValidator.normalize_target_length(
                candidate,
                source="test",
            )

        assert exc_info.value.code == "QC-010"
        assert "min/max が存在しない" in str(exc_info.value)

    def test_normalize_raises_when_missing_max(self):
        """normalize_target_length() should raise when max is missing."""
        candidate = {"min": 3000}

        with pytest.raises(ProjectConfigError) as exc_info:
            TargetLengthValidator.normalize_target_length(
                candidate,
                source="test",
            )

        assert exc_info.value.code == "QC-010"
        assert "min/max が存在しない" in str(exc_info.value)

    def test_normalize_raises_when_min_not_numeric(self):
        """normalize_target_length() should raise when min is not numeric."""
        candidate = {"min": "invalid", "max": 5000}

        with pytest.raises(ProjectConfigError) as exc_info:
            TargetLengthValidator.normalize_target_length(
                candidate,
                source="test",
            )

        assert exc_info.value.code == "QC-010"
        assert "数値ではありません" in str(exc_info.value)

    def test_normalize_raises_when_max_not_numeric(self):
        """normalize_target_length() should raise when max is not numeric."""
        candidate = {"min": 3000, "max": "invalid"}

        with pytest.raises(ProjectConfigError) as exc_info:
            TargetLengthValidator.normalize_target_length(
                candidate,
                source="test",
            )

        assert exc_info.value.code == "QC-010"
        assert "数値ではありません" in str(exc_info.value)

    def test_normalize_raises_when_min_less_than_1(self):
        """normalize_target_length() should raise when min < 1."""
        candidate = {"min": 0, "max": 5000}

        with pytest.raises(ProjectConfigError) as exc_info:
            TargetLengthValidator.normalize_target_length(
                candidate,
                source="test",
            )

        assert exc_info.value.code == "QC-010"
        assert "min/max が不正です" in str(exc_info.value)
        assert exc_info.value.details["min"] == 0

    def test_normalize_raises_when_max_less_than_1(self):
        """normalize_target_length() should raise when max < 1."""
        candidate = {"min": 3000, "max": 0}

        with pytest.raises(ProjectConfigError) as exc_info:
            TargetLengthValidator.normalize_target_length(
                candidate,
                source="test",
            )

        assert exc_info.value.code == "QC-010"
        assert "min/max が不正です" in str(exc_info.value)
        assert exc_info.value.details["max"] == 0

    def test_normalize_raises_when_min_equals_max(self):
        """normalize_target_length() should raise when min == max."""
        candidate = {"min": 3000, "max": 3000}

        with pytest.raises(ProjectConfigError) as exc_info:
            TargetLengthValidator.normalize_target_length(
                candidate,
                source="test",
            )

        assert exc_info.value.code == "QC-010"
        assert "min/max が不正です" in str(exc_info.value)

    def test_normalize_raises_when_min_greater_than_max(self):
        """normalize_target_length() should raise when min > max."""
        candidate = {"min": 5000, "max": 3000}

        with pytest.raises(ProjectConfigError) as exc_info:
            TargetLengthValidator.normalize_target_length(
                candidate,
                source="test",
            )

        assert exc_info.value.code == "QC-010"
        assert "min/max が不正です" in str(exc_info.value)
        assert exc_info.value.details["min"] == 5000
        assert exc_info.value.details["max"] == 3000

    def test_normalize_accepts_min_1_max_2(self):
        """normalize_target_length() should accept min=1, max=2 (edge case)."""
        candidate = {"min": 1, "max": 2}

        result = TargetLengthValidator.normalize_target_length(
            candidate,
            source="test",
        )

        assert result["min"] == 1
        assert result["max"] == 2

    def test_normalize_preserves_source_identifier(self):
        """normalize_target_length() should preserve source identifier."""
        candidate = {"min": 3000, "max": 5000}

        result = TargetLengthValidator.normalize_target_length(
            candidate,
            source="project_config",
        )

        assert result["source"] == "project_config"

        result = TargetLengthValidator.normalize_target_length(
            candidate,
            source="manifest",
        )

        assert result["source"] == "manifest"

    def test_normalize_ignores_extra_keys(self):
        """normalize_target_length() should ignore extra keys in candidate."""
        candidate = {
            "min": 3000,
            "max": 5000,
            "extra_key": "extra_value",
        }

        result = TargetLengthValidator.normalize_target_length(
            candidate,
            source="test",
        )

        # Only min, max, source should be in result
        assert set(result.keys()) == {"min", "max", "source"}
        assert result["min"] == 3000
        assert result["max"] == 5000


# ============================================================================
# Integration Tests
# ============================================================================


class TestTargetLengthValidatorIntegration:
    """Integration tests for complete workflow."""

    def test_validate_multiple_sources(self):
        """Test validation with different source identifiers."""
        candidate = {"min": 2000, "max": 4000}

        sources = ["project_config", "manifest", "override"]

        for source in sources:
            result = TargetLengthValidator.normalize_target_length(
                candidate,
                source=source,
            )

            assert result["source"] == source
            assert result["min"] == 2000
            assert result["max"] == 4000

    def test_error_details_include_source(self):
        """Test that all errors include source in details."""
        invalid_cases = [
            ({"min": 0, "max": 5000}, "source1"),
            ({"min": 5000, "max": 3000}, "source2"),
            ({"min": "invalid", "max": 5000}, "source3"),
        ]

        for candidate, source in invalid_cases:
            with pytest.raises(ProjectConfigError) as exc_info:
                TargetLengthValidator.normalize_target_length(
                    candidate,
                    source=source,
                )

            assert exc_info.value.details["source"] == source

    def test_boundary_values(self):
        """Test boundary values for min and max."""
        # Minimum valid range
        result = TargetLengthValidator.normalize_target_length(
            {"min": 1, "max": 2},
            source="test",
        )
        assert result["min"] == 1
        assert result["max"] == 2

        # Large values
        result = TargetLengthValidator.normalize_target_length(
            {"min": 1000000, "max": 2000000},
            source="test",
        )
        assert result["min"] == 1000000
        assert result["max"] == 2000000
