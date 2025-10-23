# File: tests/unit/domain/services/ml_quality/test_weight_optimizer.py
# Purpose: Unit tests for WeightOptimizer service
# Context: Test weight optimization for weighted_average scoring

"""
Unit tests for WeightOptimizer service.

Test coverage:
- Weight optimization from feedback history
- Default weights fallback for insufficient data
- Multiple optimization objectives (F1, PRECISION, RECALL, RMSE)
- Weight normalization (sum to 1.0)
- SPEC-QUALITY-140 compliance
"""

import pytest
from pathlib import Path
from unittest.mock import Mock

from noveler.domain.services.ml_quality.weight_optimizer import (
    WeightOptimizer,
    OptimizedWeights,
    OptimizationObjective
)


@pytest.fixture
def mock_feedback_repository():
    """Create mock feedback repository."""
    repo = Mock()
    repo.load_recent_feedback = Mock(return_value=[
        {
            "automated_scores": {"rhythm": 75.0, "readability": 80.0, "grammar": 90.0, "style": 85.0},
            "human_scores": {"overall": 82.0}
        },
        {
            "automated_scores": {"rhythm": 70.0, "readability": 85.0, "grammar": 88.0, "style": 80.0},
            "human_scores": {"overall": 80.0}
        },
        {
            "automated_scores": {"rhythm": 80.0, "readability": 78.0, "grammar": 92.0, "style": 88.0},
            "human_scores": {"overall": 85.0}
        },
    ] * 4)  # 12 records total
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
def weight_optimizer(mock_feedback_repository, mock_logger):
    """Create WeightOptimizer with mocked dependencies."""
    return WeightOptimizer(
        feedback_repository=mock_feedback_repository,
        logger=mock_logger
    )


@pytest.fixture
def base_scores():
    """Sample base quality scores."""
    return {
        "rhythm": 75.0,
        "readability": 80.0,
        "grammar": 90.0,
        "style": 85.0
    }


class TestWeightOptimizerBasicWorkflow:
    """Test basic weight optimization workflow."""

    def test_optimize_weights_success(
        self,
        weight_optimizer,
        base_scores,
        mock_feedback_repository,
        mock_logger
    ):
        """Test successful weight optimization."""
        result = weight_optimizer.optimize_weights(
            project_root=Path("/tmp/test_project"),
            base_scores=base_scores,
            feedback_history_limit=50
        )

        # Verify repository was called
        mock_feedback_repository.load_recent_feedback.assert_called_once()

        # Verify result is a dictionary of weights
        assert isinstance(result, dict)
        assert "rhythm" in result
        assert "readability" in result
        assert "grammar" in result
        assert "style" in result

        # Verify all weights are positive
        for aspect, weight in result.items():
            assert weight > 0.0

        # Verify weights sum to 1.0 (with floating point tolerance)
        assert abs(sum(result.values()) - 1.0) < 0.01

        # Verify logger was called
        assert mock_logger.info.called

    def test_optimize_weights_with_insufficient_feedback(
        self,
        weight_optimizer,
        base_scores,
        mock_feedback_repository,
        mock_logger
    ):
        """Test fallback to default weights with insufficient feedback."""
        # Simulate insufficient feedback (< 10 records)
        mock_feedback_repository.load_recent_feedback.return_value = [
            {"automated_scores": {}, "human_scores": {"overall": 80.0}}
        ] * 5

        result = weight_optimizer.optimize_weights(
            project_root=Path("/tmp/test_project"),
            base_scores=base_scores
        )

        # Verify default weights are returned
        assert result == weight_optimizer.DEFAULT_WEIGHTS

        # Verify warning was logged
        assert mock_logger.warning.called

    def test_optimize_weights_with_different_objectives(
        self,
        weight_optimizer,
        base_scores
    ):
        """Test weight optimization with different optimization objectives."""
        # Test all objectives
        for objective in OptimizationObjective:
            result = weight_optimizer.optimize_weights(
                project_root=Path("/tmp/test_project"),
                base_scores=base_scores,
                optimization_objective=objective
            )

            # Verify successful execution
            assert isinstance(result, dict)
            assert len(result) > 0


class TestWeightOptimizerDefaultWeights:
    """Test default weights behavior."""

    def test_default_weights_sum_to_one(self, weight_optimizer):
        """Test default weights sum to 1.0."""
        weights = weight_optimizer.DEFAULT_WEIGHTS

        # Verify sum
        assert abs(sum(weights.values()) - 1.0) < 0.001

    def test_default_weights_all_positive(self, weight_optimizer):
        """Test all default weights are positive."""
        weights = weight_optimizer.DEFAULT_WEIGHTS

        # Verify all positive
        for aspect, weight in weights.items():
            assert weight > 0.0


class TestWeightOptimizerInsufficientData:
    """Test behavior with insufficient data."""

    def test_insufficient_total_feedback(
        self,
        weight_optimizer,
        base_scores,
        mock_feedback_repository,
        mock_logger
    ):
        """Test fallback when total feedback is insufficient."""
        # Only 3 records (< 10 threshold)
        mock_feedback_repository.load_recent_feedback.return_value = [
            {"automated_scores": {}, "human_scores": {"overall": 80.0}}
        ] * 3

        result = weight_optimizer.optimize_weights(
            project_root=Path("/tmp/test_project"),
            base_scores=base_scores
        )

        # Should return default weights
        assert result == weight_optimizer.DEFAULT_WEIGHTS
        assert mock_logger.warning.called

    def test_insufficient_labeled_records(
        self,
        weight_optimizer,
        base_scores,
        mock_feedback_repository,
        mock_logger
    ):
        """Test fallback when labeled records are insufficient."""
        # 10 total records but only 3 with human_scores
        mock_feedback_repository.load_recent_feedback.return_value = [
            {"automated_scores": {}, "human_scores": {"overall": 80.0}},
            {"automated_scores": {}, "human_scores": {"overall": 85.0}},
            {"automated_scores": {}, "human_scores": {"overall": 78.0}},
            {"automated_scores": {}, "human_scores": None},  # No label
            {"automated_scores": {}, "human_scores": None},  # No label
            {"automated_scores": {}, "human_scores": None},  # No label
            {"automated_scores": {}, "human_scores": None},  # No label
            {"automated_scores": {}, "human_scores": None},  # No label
            {"automated_scores": {}, "human_scores": None},  # No label
            {"automated_scores": {}, "human_scores": None},  # No label
        ]

        result = weight_optimizer.optimize_weights(
            project_root=Path("/tmp/test_project"),
            base_scores=base_scores
        )

        # Should return default weights
        assert result == weight_optimizer.DEFAULT_WEIGHTS
        assert mock_logger.warning.called


@pytest.mark.spec("SPEC-QUALITY-140")
class TestWeightOptimizerSpecCompliance:
    """Test SPEC-QUALITY-140 compliance."""

    def test_spec_weight_optimization(
        self,
        weight_optimizer,
        base_scores
    ):
        """SPEC-QUALITY-140 §2.2.4: Verify weight optimization contract."""
        result = weight_optimizer.optimize_weights(
            project_root=Path("/tmp/test_project"),
            base_scores=base_scores
        )

        # Verify weights are returned as dict
        assert isinstance(result, dict)

        # Verify all aspects have weights
        required_aspects = ["rhythm", "readability", "grammar", "style"]
        for aspect in required_aspects:
            assert aspect in result
            assert isinstance(result[aspect], float)

        # Verify weights sum to 1.0
        assert abs(sum(result.values()) - 1.0) < 0.01

    def test_spec_optimization_objectives(
        self,
        weight_optimizer,
        base_scores
    ):
        """SPEC-QUALITY-140 §2.2.4: Verify all 4 optimization objectives supported."""
        objectives = [
            OptimizationObjective.F1_SCORE,
            OptimizationObjective.PRECISION,
            OptimizationObjective.RECALL,
            OptimizationObjective.RMSE
        ]

        for objective in objectives:
            result = weight_optimizer.optimize_weights(
                project_root=Path("/tmp/test_project"),
                base_scores=base_scores,
                optimization_objective=objective
            )

            # Verify successful execution
            assert isinstance(result, dict)
            assert len(result) > 0

    def test_spec_performance_target(
        self,
        weight_optimizer,
        base_scores
    ):
        """SPEC-QUALITY-140 §4.2: Verify performance target (≤2 seconds for 50 records)."""
        import time

        start = time.time()
        weight_optimizer.optimize_weights(
            project_root=Path("/tmp/test_project"),
            base_scores=base_scores,
            feedback_history_limit=50
        )
        duration = time.time() - start

        # Should complete in ≤2 seconds
        assert duration < 2.0, f"Weight optimization took {duration}s, expected <2s"
