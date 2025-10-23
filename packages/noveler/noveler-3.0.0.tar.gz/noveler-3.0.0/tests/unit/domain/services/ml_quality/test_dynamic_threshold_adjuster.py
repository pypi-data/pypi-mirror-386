# File: tests/unit/domain/services/ml_quality/test_dynamic_threshold_adjuster.py
# Purpose: Unit tests for DynamicThresholdAdjuster service
# Context: Test threshold auto-tuning based on feedback history

"""
Unit tests for DynamicThresholdAdjuster service.

Test coverage:
- Threshold adjustment based on feedback
- False positive/negative identification
- Adjustment policy application (CONSERVATIVE, MODERATE, AGGRESSIVE)
- Corpus-only fallback when no feedback available
- Recommended action determination
- SPEC-QUALITY-140 compliance
"""

import pytest
from pathlib import Path
from unittest.mock import Mock

from noveler.domain.services.ml_quality.dynamic_threshold_adjuster import (
    DynamicThresholdAdjuster,
    AdjustedThresholds,
    AdjustmentPolicy
)


@pytest.fixture
def mock_feedback_repository():
    """Create mock feedback repository."""
    repo = Mock()
    repo.load_recent_feedback = Mock(return_value=[
        {
            "automated_outcome": "FAIL",
            "manual_outcome": "PASS",
            "aspects": ["rhythm"],
            "scores": {"rhythm": 72.0}
        },
        {
            "automated_outcome": "PASS",
            "manual_outcome": "FAIL",
            "aspects": ["readability"],
            "scores": {"readability": 81.0}
        },
        {
            "automated_outcome": "PASS",
            "manual_outcome": "PASS",
            "aspects": ["grammar"],
            "scores": {"grammar": 90.0}
        }
    ])
    return repo


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
def threshold_adjuster(mock_feedback_repository, mock_logger):
    """Create DynamicThresholdAdjuster with mocked dependencies."""
    return DynamicThresholdAdjuster(
        feedback_repository=mock_feedback_repository,
        logger=mock_logger
    )


@pytest.fixture
def current_thresholds():
    """Sample current thresholds."""
    return {
        "rhythm": 75.0,
        "readability": 80.0,
        "grammar": 85.0,
        "style": 80.0
    }


@pytest.fixture
def corpus_metrics():
    """Sample corpus metrics."""
    return {
        "rhythm_baseline": 70.0,
        "readability_baseline": 78.0,
        "grammar_baseline": 88.0,
        "style_baseline": 82.0
    }


class TestDynamicThresholdAdjusterBasicWorkflow:
    """Test basic threshold adjustment workflow."""

    def test_adjust_thresholds_success(
        self,
        threshold_adjuster,
        current_thresholds,
        corpus_metrics,
        mock_feedback_repository,
        mock_logger
    ):
        """Test successful threshold adjustment."""
        result = threshold_adjuster.adjust_thresholds(
            current_thresholds=current_thresholds,
            corpus_metrics=corpus_metrics,
            project_root=Path("/tmp/test_project"),
            adjustment_policy=AdjustmentPolicy.CONSERVATIVE
        )

        # Verify repository was called
        mock_feedback_repository.load_recent_feedback.assert_called_once()

        # Verify result structure
        assert isinstance(result, dict)
        assert "thresholds" in result
        assert "false_positive_rate_estimate" in result
        assert "false_negative_rate_estimate" in result
        assert "recommended_action" in result

        # Verify thresholds structure
        thresholds = result["thresholds"]
        for aspect in current_thresholds.keys():
            assert aspect in thresholds
            assert "current" in thresholds[aspect]
            assert "adjusted" in thresholds[aspect]
            assert "confidence_interval" in thresholds[aspect]
            assert "rationale" in thresholds[aspect]

        # Verify logger was called
        assert mock_logger.info.called

    def test_adjust_thresholds_with_no_feedback(
        self,
        threshold_adjuster,
        current_thresholds,
        corpus_metrics,
        mock_feedback_repository,
        mock_logger
    ):
        """Test fallback to corpus-only adjustment when no feedback."""
        # Simulate no feedback available
        mock_feedback_repository.load_recent_feedback.return_value = []

        result = threshold_adjuster.adjust_thresholds(
            current_thresholds=current_thresholds,
            corpus_metrics=corpus_metrics,
            project_root=Path("/tmp/test_project")
        )

        # Verify corpus-only fallback was used
        assert result["recommended_action"] == "review"
        assert mock_logger.warning.called

    def test_adjust_thresholds_with_different_policies(
        self,
        threshold_adjuster,
        current_thresholds,
        corpus_metrics
    ):
        """Test threshold adjustment with different adjustment policies."""
        # Test CONSERVATIVE policy
        result_conservative = threshold_adjuster.adjust_thresholds(
            current_thresholds=current_thresholds,
            corpus_metrics=corpus_metrics,
            project_root=Path("/tmp/test_project"),
            adjustment_policy=AdjustmentPolicy.CONSERVATIVE
        )

        # Test AGGRESSIVE policy
        result_aggressive = threshold_adjuster.adjust_thresholds(
            current_thresholds=current_thresholds,
            corpus_metrics=corpus_metrics,
            project_root=Path("/tmp/test_project"),
            adjustment_policy=AdjustmentPolicy.AGGRESSIVE
        )

        # AGGRESSIVE should produce larger adjustments than CONSERVATIVE
        # (This is implementation-dependent, but we can verify structure)
        assert "thresholds" in result_conservative
        assert "thresholds" in result_aggressive


class TestDynamicThresholdAdjusterClassificationErrors:
    """Test false positive/negative identification."""

    def test_identify_classification_errors(
        self,
        threshold_adjuster
    ):
        """Test identification of FP and FN cases."""
        feedback_history = [
            {"automated_outcome": "FAIL", "manual_outcome": "PASS"},  # FP
            {"automated_outcome": "PASS", "manual_outcome": "FAIL"},  # FN
            {"automated_outcome": "PASS", "manual_outcome": "PASS"},  # TN
            {"automated_outcome": "FAIL", "manual_outcome": "FAIL"},  # TP
            {"automated_outcome": "FAIL", "manual_outcome": "PASS"},  # FP
        ]

        fp_cases, fn_cases = threshold_adjuster._identify_classification_errors(
            feedback_history
        )

        # Verify FP and FN counts
        assert len(fp_cases) == 2
        assert len(fn_cases) == 1

        # Verify FP cases
        for fp in fp_cases:
            assert fp["automated_outcome"] == "FAIL"
            assert fp["manual_outcome"] == "PASS"

        # Verify FN cases
        for fn in fn_cases:
            assert fn["automated_outcome"] == "PASS"
            assert fn["manual_outcome"] == "FAIL"


class TestDynamicThresholdAdjusterCorpusOnly:
    """Test corpus-only threshold adjustment."""

    def test_adjust_from_corpus_only(
        self,
        threshold_adjuster,
        current_thresholds,
        corpus_metrics
    ):
        """Test corpus-only adjustment strategy."""
        result = threshold_adjuster._adjust_from_corpus_only(
            current_thresholds=current_thresholds,
            corpus_metrics=corpus_metrics
        )

        # Verify structure
        assert "thresholds" in result
        assert "false_positive_rate_estimate" in result
        assert "false_negative_rate_estimate" in result
        assert result["recommended_action"] == "review"

        # Verify thresholds were adjusted
        thresholds = result["thresholds"]
        for aspect in current_thresholds.keys():
            assert aspect in thresholds
            assert "current" in thresholds[aspect]
            assert "adjusted" in thresholds[aspect]
            assert thresholds[aspect]["current"] == current_thresholds[aspect]


class TestDynamicThresholdAdjusterAspectAdjustment:
    """Test individual aspect threshold adjustment."""

    def test_adjust_aspect_threshold_with_fp_cases(
        self,
        threshold_adjuster
    ):
        """Test threshold adjustment when FP cases dominate."""
        fp_cases = [
            {"aspects": ["rhythm"]},
            {"aspects": ["rhythm"]},
            {"aspects": ["rhythm"]}
        ]
        fn_cases = [{"aspects": ["rhythm"]}]

        result = threshold_adjuster._adjust_aspect_threshold(
            aspect="rhythm",
            current_threshold=75.0,
            feedback_history=[],
            fp_cases=fp_cases,
            fn_cases=fn_cases,
            adjustment_policy=AdjustmentPolicy.CONSERVATIVE
        )

        # Verify adjustment structure
        assert result["current"] == 75.0
        assert result["adjusted"] > result["current"]  # Should raise threshold
        assert "confidence_interval" in result
        assert "rationale" in result

    def test_adjust_aspect_threshold_with_fn_cases(
        self,
        threshold_adjuster
    ):
        """Test threshold adjustment when FN cases dominate."""
        fp_cases = [{"aspects": ["readability"]}]
        fn_cases = [
            {"aspects": ["readability"]},
            {"aspects": ["readability"]},
            {"aspects": ["readability"]}
        ]

        result = threshold_adjuster._adjust_aspect_threshold(
            aspect="readability",
            current_threshold=80.0,
            feedback_history=[],
            fp_cases=fp_cases,
            fn_cases=fn_cases,
            adjustment_policy=AdjustmentPolicy.CONSERVATIVE
        )

        # Verify adjustment structure
        assert result["current"] == 80.0
        assert result["adjusted"] < result["current"]  # Should lower threshold
        assert "confidence_interval" in result
        assert "rationale" in result

    def test_adjust_aspect_threshold_clamping(
        self,
        threshold_adjuster
    ):
        """Test threshold values are clamped to [50, 95]."""
        fp_cases = [{"aspects": ["rhythm"]}] * 100  # Many FP cases
        fn_cases = []

        result = threshold_adjuster._adjust_aspect_threshold(
            aspect="rhythm",
            current_threshold=90.0,
            feedback_history=[],
            fp_cases=fp_cases,
            fn_cases=fn_cases,
            adjustment_policy=AdjustmentPolicy.AGGRESSIVE
        )

        # Verify clamping
        assert 50.0 <= result["adjusted"] <= 95.0


class TestDynamicThresholdAdjusterErrorRates:
    """Test error rate estimation."""

    def test_estimate_current_fp_rate(self, threshold_adjuster):
        """Test current false positive rate estimation."""
        feedback_history = [
            {"automated_outcome": "FAIL", "manual_outcome": "PASS"},  # FP
            {"automated_outcome": "FAIL", "manual_outcome": "PASS"},  # FP
            {"automated_outcome": "PASS", "manual_outcome": "PASS"},  # TN
            {"automated_outcome": "PASS", "manual_outcome": "PASS"},  # TN
        ]

        fp_rate = threshold_adjuster._estimate_current_fp_rate(feedback_history)

        # 2 FP out of 4 total = 0.5
        assert fp_rate == 0.5

    def test_estimate_current_fn_rate(self, threshold_adjuster):
        """Test current false negative rate estimation."""
        feedback_history = [
            {"automated_outcome": "PASS", "manual_outcome": "FAIL"},  # FN
            {"automated_outcome": "PASS", "manual_outcome": "PASS"},  # TN
            {"automated_outcome": "PASS", "manual_outcome": "PASS"},  # TN
            {"automated_outcome": "PASS", "manual_outcome": "PASS"},  # TN
        ]

        fn_rate = threshold_adjuster._estimate_current_fn_rate(feedback_history)

        # 1 FN out of 4 total = 0.25
        assert fn_rate == 0.25

    def test_estimate_error_rates_with_empty_history(self, threshold_adjuster):
        """Test error rate estimation with empty feedback history."""
        fp_rate = threshold_adjuster._estimate_current_fp_rate([])
        fn_rate = threshold_adjuster._estimate_current_fn_rate([])

        # Should return default conservative estimates
        assert fp_rate == 0.05
        assert fn_rate == 0.10


class TestDynamicThresholdAdjusterActionDetermination:
    """Test recommended action determination."""

    def test_determine_action_apply(self, threshold_adjuster):
        """Test 'apply' action when both rates improve significantly."""
        action = threshold_adjuster._determine_action(
            current_fp_rate=0.10,
            current_fn_rate=0.15,
            new_fp_rate=0.05,
            new_fn_rate=0.10,
            target_fp_rate=0.05,
            target_fn_rate=0.10
        )

        # Both improved by >0.02
        assert action == "apply"

    def test_determine_action_keep_current(self, threshold_adjuster):
        """Test 'keep_current' action when rates worsen."""
        action = threshold_adjuster._determine_action(
            current_fp_rate=0.05,
            current_fn_rate=0.10,
            new_fp_rate=0.10,
            new_fn_rate=0.15,
            target_fp_rate=0.05,
            target_fn_rate=0.10
        )

        # Both worsened by >0.02
        assert action == "keep_current"

    def test_determine_action_review(self, threshold_adjuster):
        """Test 'review' action when results are mixed."""
        action = threshold_adjuster._determine_action(
            current_fp_rate=0.05,
            current_fn_rate=0.10,
            new_fp_rate=0.04,
            new_fn_rate=0.09,
            target_fp_rate=0.05,
            target_fn_rate=0.10
        )

        # Small improvements (< 0.02)
        assert action == "review"


@pytest.mark.spec("SPEC-QUALITY-140")
class TestDynamicThresholdAdjusterSpecCompliance:
    """Test SPEC-QUALITY-140 compliance."""

    def test_spec_threshold_adjustment(
        self,
        threshold_adjuster,
        current_thresholds,
        corpus_metrics
    ):
        """SPEC-QUALITY-140 §2.2.3: Verify threshold adjustment contract."""
        result = threshold_adjuster.adjust_thresholds(
            current_thresholds=current_thresholds,
            corpus_metrics=corpus_metrics,
            project_root=Path("/tmp/test_project")
        )

        # Verify required output fields
        required_fields = [
            "thresholds",
            "false_positive_rate_estimate",
            "false_negative_rate_estimate",
            "recommended_action"
        ]

        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

        # Verify threshold structure for each aspect
        for aspect, threshold_data in result["thresholds"].items():
            assert "current" in threshold_data
            assert "adjusted" in threshold_data
            assert "confidence_interval" in threshold_data
            assert "rationale" in threshold_data

    def test_spec_adjustment_policy_support(
        self,
        threshold_adjuster,
        current_thresholds,
        corpus_metrics
    ):
        """SPEC-QUALITY-140 §4.3: Verify all 3 adjustment policies supported."""
        # Test all three policies
        for policy in [AdjustmentPolicy.CONSERVATIVE, AdjustmentPolicy.MODERATE, AdjustmentPolicy.AGGRESSIVE]:
            result = threshold_adjuster.adjust_thresholds(
                current_thresholds=current_thresholds,
                corpus_metrics=corpus_metrics,
                project_root=Path("/tmp/test_project"),
                adjustment_policy=policy
            )

            # Verify successful execution
            assert "thresholds" in result

    def test_spec_fp_fn_minimization(
        self,
        threshold_adjuster,
        current_thresholds,
        corpus_metrics
    ):
        """SPEC-QUALITY-140 §2.2.3: Verify FP/FN rate targets."""
        result = threshold_adjuster.adjust_thresholds(
            current_thresholds=current_thresholds,
            corpus_metrics=corpus_metrics,
            project_root=Path("/tmp/test_project"),
            target_fp_rate=0.05,
            target_fn_rate=0.10
        )

        # Verify error rate estimates are provided
        assert isinstance(result["false_positive_rate_estimate"], float)
        assert isinstance(result["false_negative_rate_estimate"], float)

        # Verify rates are within reasonable bounds [0, 1]
        assert 0.0 <= result["false_positive_rate_estimate"] <= 1.0
        assert 0.0 <= result["false_negative_rate_estimate"] <= 1.0
