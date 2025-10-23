# File: tests/unit/domain/services/ml_quality/test_severity_estimator.py
# Purpose: Unit tests for SeverityEstimator service
# Context: Test context-aware severity estimation for quality issues

"""
Unit tests for SeverityEstimator service.

Test coverage:
- Position-based severity multipliers (opening/climax/ending have higher impact)
- Frequency-based penalties for repeated violations
- Manuscript region determination
- Severity explanation generation
- SPEC-QUALITY-140 compliance
"""

import pytest
from unittest.mock import Mock

from noveler.domain.services.ml_quality.severity_estimator import (
    SeverityEstimator,
    SeverityEstimate
)


@pytest.fixture
def mock_logger():
    """Create mock logger."""
    logger = Mock()
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    return logger


@pytest.fixture
def severity_estimator(mock_logger):
    """Create SeverityEstimator with mocked logger."""
    return SeverityEstimator(logger=mock_logger)


@pytest.fixture
def sample_issue():
    """Sample quality issue."""
    return {
        "issue_id": "issue_001",
        "line_number": 50,
        "severity": "medium",
        "reason_code": "LONG_SENTENCE"
    }


class TestSeverityEstimatorBasicWorkflow:
    """Test basic severity estimation workflow."""

    def test_estimate_severity_success(
        self,
        severity_estimator,
        sample_issue
    ):
        """Test successful severity estimation."""
        result = severity_estimator.estimate_severity(
            issue=sample_issue,
            manuscript="Sample manuscript text",
            total_lines=1000
        )

        # Verify result structure
        assert isinstance(result, dict)
        assert "issue_id" in result
        assert "line_number" in result
        assert "base_severity" in result
        assert "position_multiplier" in result
        assert "frequency_penalty" in result
        assert "adjusted_severity" in result
        assert "explanation" in result

        # Verify values
        assert result["issue_id"] == "issue_001"
        assert result["line_number"] == 50
        assert result["base_severity"] > 0.0
        assert result["position_multiplier"] >= 1.0
        assert result["frequency_penalty"] >= 1.0
        assert result["adjusted_severity"] > 0.0

    def test_estimate_severity_for_different_severities(
        self,
        severity_estimator
    ):
        """Test severity estimation for low, medium, high severities."""
        low_issue = {"issue_id": "low", "line_number": 100, "severity": "low", "reason_code": "TEST"}
        medium_issue = {"issue_id": "med", "line_number": 100, "severity": "medium", "reason_code": "TEST"}
        high_issue = {"issue_id": "high", "line_number": 100, "severity": "high", "reason_code": "TEST"}

        low_result = severity_estimator.estimate_severity(low_issue, "text", 1000)
        medium_result = severity_estimator.estimate_severity(medium_issue, "text", 1000)
        high_result = severity_estimator.estimate_severity(high_issue, "text", 1000)

        # Verify severity ordering
        assert low_result["base_severity"] < medium_result["base_severity"]
        assert medium_result["base_severity"] < high_result["base_severity"]


class TestSeverityEstimatorPositionMultipliers:
    """Test position-based severity multipliers."""

    def test_opening_region_multiplier(self, severity_estimator, sample_issue):
        """Test higher multiplier for opening region (first 10%)."""
        # Line 5 out of 100 = 5% (opening region)
        sample_issue["line_number"] = 5
        result = severity_estimator.estimate_severity(sample_issue, "text", 100)

        # Opening region should have multiplier 1.5
        assert result["position_multiplier"] == severity_estimator.POSITION_MULTIPLIERS["opening"]
        assert result["position_multiplier"] == 1.5

    def test_middle_region_multiplier(self, severity_estimator, sample_issue):
        """Test standard multiplier for middle region."""
        # Line 500 out of 1000 = 50% (middle region)
        sample_issue["line_number"] = 500
        result = severity_estimator.estimate_severity(sample_issue, "text", 1000)

        # Middle region should have multiplier 1.0
        assert result["position_multiplier"] == severity_estimator.POSITION_MULTIPLIERS["middle"]
        assert result["position_multiplier"] == 1.0

    def test_climax_region_multiplier(self, severity_estimator, sample_issue):
        """Test higher multiplier for climax region (80-90%)."""
        # Line 850 out of 1000 = 85% (climax region)
        sample_issue["line_number"] = 850
        result = severity_estimator.estimate_severity(sample_issue, "text", 1000)

        # Climax region should have multiplier 1.8
        assert result["position_multiplier"] == severity_estimator.POSITION_MULTIPLIERS["climax"]
        assert result["position_multiplier"] == 1.8

    def test_ending_region_multiplier(self, severity_estimator, sample_issue):
        """Test highest multiplier for ending region (last 5%)."""
        # Line 980 out of 1000 = 98% (ending region)
        sample_issue["line_number"] = 980
        result = severity_estimator.estimate_severity(sample_issue, "text", 1000)

        # Ending region should have multiplier 2.0
        assert result["position_multiplier"] == severity_estimator.POSITION_MULTIPLIERS["ending"]
        assert result["position_multiplier"] == 2.0


class TestSeverityEstimatorRegionDetermination:
    """Test manuscript region determination."""

    def test_determine_region_opening(self, severity_estimator):
        """Test opening region detection (0-10%)."""
        assert severity_estimator._determine_region(0.05) == "opening"
        assert severity_estimator._determine_region(0.09) == "opening"

    def test_determine_region_middle(self, severity_estimator):
        """Test middle region detection."""
        assert severity_estimator._determine_region(0.15) == "middle"
        assert severity_estimator._determine_region(0.50) == "middle"
        assert severity_estimator._determine_region(0.75) == "middle"

    def test_determine_region_climax(self, severity_estimator):
        """Test climax region detection (80-90%)."""
        assert severity_estimator._determine_region(0.80) == "climax"
        assert severity_estimator._determine_region(0.85) == "climax"
        assert severity_estimator._determine_region(0.89) == "climax"

    def test_determine_region_ending(self, severity_estimator):
        """Test ending region detection (95-100%)."""
        assert severity_estimator._determine_region(0.95) == "ending"
        assert severity_estimator._determine_region(0.98) == "ending"
        assert severity_estimator._determine_region(1.00) == "ending"


class TestSeverityEstimatorBaseSeverityParsing:
    """Test base severity string parsing."""

    def test_parse_low_severity(self, severity_estimator):
        """Test parsing 'low' severity."""
        assert severity_estimator._parse_base_severity("low") == 1.0
        assert severity_estimator._parse_base_severity("LOW") == 1.0

    def test_parse_medium_severity(self, severity_estimator):
        """Test parsing 'medium' severity."""
        assert severity_estimator._parse_base_severity("medium") == 2.0
        assert severity_estimator._parse_base_severity("MEDIUM") == 2.0

    def test_parse_high_severity(self, severity_estimator):
        """Test parsing 'high' severity."""
        assert severity_estimator._parse_base_severity("high") == 3.0
        assert severity_estimator._parse_base_severity("HIGH") == 3.0

    def test_parse_unknown_severity(self, severity_estimator):
        """Test parsing unknown severity defaults to medium."""
        assert severity_estimator._parse_base_severity("unknown") == 2.0
        assert severity_estimator._parse_base_severity("") == 2.0


class TestSeverityEstimatorExplanationGeneration:
    """Test explanation generation."""

    def test_generate_explanation_with_position_only(self, severity_estimator):
        """Test explanation when only position multiplier applies."""
        explanation = severity_estimator._generate_explanation(
            region="opening",
            similar_count=0,
            position_multiplier=1.5,
            frequency_penalty=1.0
        )

        # Should mention region impact
        assert "opening" in explanation
        assert "1.5" in explanation

    def test_generate_explanation_with_frequency_only(self, severity_estimator):
        """Test explanation when only frequency penalty applies."""
        explanation = severity_estimator._generate_explanation(
            region="middle",
            similar_count=3,
            position_multiplier=1.0,
            frequency_penalty=1.3
        )

        # Should mention similar issues
        assert "3" in explanation or "similar" in explanation

    def test_generate_explanation_with_both(self, severity_estimator):
        """Test explanation when both position and frequency apply."""
        explanation = severity_estimator._generate_explanation(
            region="climax",
            similar_count=2,
            position_multiplier=1.8,
            frequency_penalty=1.2
        )

        # Should mention both factors
        assert "climax" in explanation
        assert len(explanation) > 20  # Should be a meaningful explanation

    def test_generate_explanation_no_adjustments(self, severity_estimator):
        """Test explanation when no adjustments apply."""
        explanation = severity_estimator._generate_explanation(
            region="middle",
            similar_count=0,
            position_multiplier=1.0,
            frequency_penalty=1.0
        )

        # Should indicate standard severity
        assert "Standard" in explanation or "no adjustments" in explanation


class TestSeverityEstimatorAdjustedSeverityCalculation:
    """Test adjusted severity calculation."""

    def test_adjusted_severity_multiplication(self, severity_estimator):
        """Test adjusted severity is base × position × frequency."""
        issue = {
            "issue_id": "test",
            "line_number": 5,  # Opening region → 1.5x
            "severity": "medium",  # → 2.0
            "reason_code": "TEST"
        }

        result = severity_estimator.estimate_severity(issue, "text", 100)

        # Base: 2.0, Position: 1.5, Frequency: 1.0 → 2.0 × 1.5 × 1.0 = 3.0
        expected = result["base_severity"] * result["position_multiplier"] * result["frequency_penalty"]
        assert abs(result["adjusted_severity"] - expected) < 0.01


@pytest.mark.spec("SPEC-QUALITY-140")
class TestSeverityEstimatorSpecCompliance:
    """Test SPEC-QUALITY-140 compliance."""

    def test_spec_severity_estimation(
        self,
        severity_estimator,
        sample_issue
    ):
        """SPEC-QUALITY-140 §2.2.5: Verify severity estimation contract."""
        result = severity_estimator.estimate_severity(
            issue=sample_issue,
            manuscript="Sample text",
            total_lines=1000
        )

        # Verify all required fields are present
        required_fields = [
            "issue_id",
            "line_number",
            "base_severity",
            "position_multiplier",
            "frequency_penalty",
            "adjusted_severity",
            "explanation"
        ]

        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

    def test_spec_position_multiplier_ranges(self, severity_estimator):
        """SPEC-QUALITY-140 §2.2.5: Verify position multipliers are in [1.0, 2.0]."""
        # Test all defined regions
        for region, multiplier in severity_estimator.POSITION_MULTIPLIERS.items():
            assert 1.0 <= multiplier <= 2.0, f"Region {region} multiplier {multiplier} out of range"

    def test_spec_performance_target(self, severity_estimator, sample_issue):
        """SPEC-QUALITY-140 §4.4: Verify performance target (≤100ms per issue)."""
        import time

        start = time.time()
        severity_estimator.estimate_severity(sample_issue, "Sample text", 1000)
        duration = time.time() - start

        # Should complete in ≤100ms
        assert duration < 0.1, f"Severity estimation took {duration}s, expected <100ms"
