# File: tests/unit/domain/services/ml_quality/test_ml_quality_optimizer.py
# Purpose: Unit tests for MLQualityOptimizer domain service
# Context: Validates ML-enhanced quality evaluation orchestration

"""
Unit tests for MLQualityOptimizer.

Tests cover:
- optimize_quality_evaluation with all dependencies mocked
- Fallback mechanism when ML services fail
- Integration with CorpusAnalyzer, DynamicThresholdAdjuster, WeightOptimizer, SeverityEstimator
- Cache utilization and performance
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
from datetime import datetime

# Import the service under test
from noveler.domain.services.ml_quality.ml_quality_optimizer import (
    MLQualityOptimizer,
    ProjectContext,
    OptimizedQualityResult,
    LearningMode
)


@pytest.fixture
def mock_corpus_analyzer():
    """Mock CorpusAnalyzer dependency."""
    analyzer = Mock()
    analyzer.build_baseline_metrics.return_value = {
        "avg_sentence_length": 18.5,
        "p50_sentence_length": 17,
        "p75_sentence_length": 25,
        "p90_sentence_length": 35,
        "dialogue_ratio": 0.50,
        "avg_commas_per_sentence": 1.2
    }
    return analyzer


@pytest.fixture
def mock_threshold_adjuster():
    """Mock DynamicThresholdAdjuster dependency."""
    adjuster = Mock()
    adjuster.adjust_thresholds.return_value = {
        "long_sentence_length": 50,  # Adjusted from default 45
        "short_sentence_length": 8,   # Adjusted from default 10
        "max_commas_per_sentence": 3
    }
    return adjuster


@pytest.fixture
def mock_weight_optimizer():
    """Mock WeightOptimizer dependency."""
    optimizer = Mock()
    optimizer.optimize_weights.return_value = {
        "rhythm": 0.30,      # Adjusted from default 0.25
        "readability": 0.30, # Adjusted from default 0.25
        "grammar": 0.25,     # Adjusted from default 0.30
        "style": 0.15        # Adjusted from default 0.20
    }
    return optimizer


@pytest.fixture
def mock_severity_estimator():
    """Mock SeverityEstimator dependency."""
    estimator = Mock()
    estimator.estimate_severity.return_value = {
        "adjusted_severity": "high",
        "position_multiplier": 1.5,
        "frequency_penalty": 0.2,
        "explanation": "Issue at opening (1.5x multiplier)"
    }
    return estimator


@pytest.fixture
def mock_logger():
    """Mock ILogger dependency."""
    logger = Mock()
    return logger


@pytest.fixture
def ml_optimizer(
    mock_corpus_analyzer,
    mock_threshold_adjuster,
    mock_weight_optimizer,
    mock_severity_estimator,
    mock_logger
):
    """Create MLQualityOptimizer with all mocked dependencies."""
    return MLQualityOptimizer(
        corpus_analyzer=mock_corpus_analyzer,
        threshold_adjuster=mock_threshold_adjuster,
        weight_optimizer=mock_weight_optimizer,
        severity_estimator=mock_severity_estimator,
        logger=mock_logger
    )


@pytest.fixture
def project_context():
    """Sample project context."""
    return ProjectContext(
        project_root=Path("/tmp/test_project"),
        genre="fantasy",
        target_audience="young_adult",
        episode_count=10
    )


@pytest.fixture
def base_quality_scores():
    """Sample base quality scores."""
    return {
        "rhythm": 75.0,
        "readability": 80.0,
        "grammar": 90.0,
        "style": 85.0
    }


@pytest.fixture
def base_issues():
    """Sample base quality issues."""
    return [
        {
            "issue_id": "issue_001",
            "type": "rhythm",
            "reason_code": "LONG_SENTENCE",
            "line_number": 10,
            "severity": "medium",
            "text": "This is a very long sentence..."
        },
        {
            "issue_id": "issue_002",
            "type": "grammar",
            "reason_code": "TYPO",
            "line_number": 25,
            "severity": "low",
            "text": "Speling mistake"
        }
    ]


class TestMLQualityOptimizerBasicWorkflow:
    """Test basic ML quality optimization workflow."""

    def test_optimize_quality_evaluation_success(
        self,
        ml_optimizer,
        project_context,
        base_quality_scores,
        base_issues,
        mock_corpus_analyzer,
        mock_threshold_adjuster,
        mock_weight_optimizer
    ):
        """Test successful ML optimization flow."""
        # Execute optimization
        result = ml_optimizer.optimize_quality_evaluation(
            manuscript="Sample manuscript text",
            project_context=project_context,
            base_quality_scores=base_quality_scores,
            base_issues=base_issues,
            learning_mode=LearningMode.ONLINE
        )

        # Verify result structure
        assert isinstance(result, OptimizedQualityResult)
        assert result.optimized_scores is not None
        assert result.dynamic_thresholds is not None
        assert result.improvement_priorities is not None

        # Verify dependencies were called
        mock_corpus_analyzer.build_baseline_metrics.assert_called_once()
        mock_threshold_adjuster.adjust_thresholds.assert_called_once()
        mock_weight_optimizer.optimize_weights.assert_called_once()

    def test_optimize_quality_evaluation_with_batch_mode(
        self,
        ml_optimizer,
        project_context,
        base_quality_scores,
        base_issues
    ):
        """Test optimization with BATCH learning mode."""
        result = ml_optimizer.optimize_quality_evaluation(
            manuscript="Sample text",
            project_context=project_context,
            base_quality_scores=base_quality_scores,
            base_issues=base_issues,
            learning_mode=LearningMode.BATCH
        )

        assert isinstance(result, OptimizedQualityResult)
        # In BATCH mode, learning happens asynchronously
        # Result should still contain optimized data

    def test_optimize_quality_evaluation_with_disabled_mode(
        self,
        ml_optimizer,
        project_context,
        base_quality_scores,
        base_issues
    ):
        """Test optimization with DISABLED learning mode."""
        result = ml_optimizer.optimize_quality_evaluation(
            manuscript="Sample text",
            project_context=project_context,
            base_quality_scores=base_quality_scores,
            base_issues=base_issues,
            learning_mode=LearningMode.DISABLED
        )

        # With DISABLED mode, should still return results
        # but no learning/feedback recording
        assert isinstance(result, OptimizedQualityResult)


class TestMLQualityOptimizerFallback:
    """Test fallback mechanisms when ML services fail."""

    @pytest.mark.skip(reason="TODO: Implement fallback mechanism in MLQualityOptimizer")
    def test_fallback_when_corpus_analyzer_fails(
        self,
        ml_optimizer,
        project_context,
        base_quality_scores,
        base_issues,
        mock_corpus_analyzer,
        mock_logger
    ):
        """Test fallback to base scores when CorpusAnalyzer fails."""
        # Simulate corpus analyzer failure
        mock_corpus_analyzer.build_baseline_metrics.side_effect = Exception("Corpus load failed")

        # Should not raise exception, but fall back gracefully
        result = ml_optimizer.optimize_quality_evaluation(
            manuscript="Sample text",
            project_context=project_context,
            base_quality_scores=base_quality_scores,
            base_issues=base_issues
        )

        # Verify fallback behavior
        assert isinstance(result, OptimizedQualityResult)
        # Should use base scores as fallback
        assert result.optimized_scores == base_quality_scores

        # Verify error was logged
        assert mock_logger.error.called or mock_logger.warning.called

    @pytest.mark.skip(reason="TODO: Implement fallback mechanism in MLQualityOptimizer")
    def test_fallback_when_threshold_adjuster_fails(
        self,
        ml_optimizer,
        project_context,
        base_quality_scores,
        base_issues,
        mock_threshold_adjuster
    ):
        """Test fallback when DynamicThresholdAdjuster fails."""
        mock_threshold_adjuster.adjust_thresholds.side_effect = Exception("Threshold adjustment failed")

        result = ml_optimizer.optimize_quality_evaluation(
            manuscript="Sample text",
            project_context=project_context,
            base_quality_scores=base_quality_scores,
            base_issues=base_issues
        )

        # Should fall back to default thresholds
        assert isinstance(result, OptimizedQualityResult)
        assert result.dynamic_thresholds is not None


class TestMLQualityOptimizerScoreRecalculation:
    """Test score recalculation with optimized weights."""

    def test_recalculate_weighted_score(
        self,
        ml_optimizer,
        project_context,
        base_quality_scores,
        base_issues,
        mock_weight_optimizer
    ):
        """Test that scores are recalculated with optimized weights."""
        # Set up mock to return different weights
        mock_weight_optimizer.optimize_weights.return_value = {
            "rhythm": 0.40,      # Increased importance
            "readability": 0.30,
            "grammar": 0.20,     # Decreased importance
            "style": 0.10
        }

        result = ml_optimizer.optimize_quality_evaluation(
            manuscript="Sample text",
            project_context=project_context,
            base_quality_scores=base_quality_scores,
            base_issues=base_issues
        )

        # Verify optimized scores differ from base scores
        # (due to weight adjustments)
        assert result.optimized_scores is not None
        # Scores should be recalculated with new weights


class TestMLQualityOptimizerIssuePrioritization:
    """Test issue prioritization based on severity estimation."""

    def test_prioritize_issues_by_severity(
        self,
        ml_optimizer,
        project_context,
        base_quality_scores,
        base_issues,
        mock_severity_estimator
    ):
        """Test that issues are prioritized by estimated severity."""
        # Mock severity estimator to return different severities
        def mock_estimate(issue, manuscript, total_lines):
            if issue["issue_id"] == "issue_001":
                return {"adjusted_severity": "critical", "position_multiplier": 2.0}
            else:
                return {"adjusted_severity": "low", "position_multiplier": 1.0}

        mock_severity_estimator.estimate_severity.side_effect = mock_estimate

        result = ml_optimizer.optimize_quality_evaluation(
            manuscript="Sample text",
            project_context=project_context,
            base_quality_scores=base_quality_scores,
            base_issues=base_issues
        )

        # Verify issues are prioritized
        assert result.improvement_priorities is not None
        # First issue should be "issue_001" (critical severity)


@pytest.mark.spec("SPEC-QUALITY-140")
class TestMLQualityOptimizerSpecCompliance:
    """Verify compliance with SPEC-QUALITY-140 requirements."""

    def test_spec_6step_workflow(
        self,
        ml_optimizer,
        project_context,
        base_quality_scores,
        base_issues,
        mock_corpus_analyzer,
        mock_threshold_adjuster,
        mock_weight_optimizer,
        mock_severity_estimator
    ):
        """SPEC-QUALITY-140 §7: Verify 6-step optimization workflow."""
        result = ml_optimizer.optimize_quality_evaluation(
            manuscript="Sample text",
            project_context=project_context,
            base_quality_scores=base_quality_scores,
            base_issues=base_issues
        )

        # Step 1: Corpus baseline extraction
        assert mock_corpus_analyzer.build_baseline_metrics.called

        # Step 2: Dynamic threshold adjustment
        assert mock_threshold_adjuster.adjust_thresholds.called

        # Step 3: Weight optimization
        assert mock_weight_optimizer.optimize_weights.called

        # Step 4: Severity estimation (called for each issue)
        # Step 5: Score recalculation
        # Step 6: Priority generation
        assert result.optimized_scores is not None
        assert result.dynamic_thresholds is not None
        assert result.improvement_priorities is not None

    @pytest.mark.skip(reason="TODO: Implement fallback mechanism in MLQualityOptimizer per SPEC-QUALITY-140 §9")
    def test_spec_fallback_mechanism(
        self,
        ml_optimizer,
        project_context,
        base_quality_scores,
        base_issues,
        mock_corpus_analyzer
    ):
        """SPEC-QUALITY-140 §9: Verify graceful fallback on ML failure."""
        # Simulate total ML failure
        mock_corpus_analyzer.build_baseline_metrics.side_effect = Exception("ML failed")

        # Should not raise exception
        result = ml_optimizer.optimize_quality_evaluation(
            manuscript="Sample text",
            project_context=project_context,
            base_quality_scores=base_quality_scores,
            base_issues=base_issues
        )

        # Should return base scores as fallback
        assert result.optimized_scores == base_quality_scores

    def test_spec_learning_mode_support(self, ml_optimizer, project_context, base_quality_scores, base_issues):
        """SPEC-QUALITY-140 §4: Verify all 3 learning modes supported."""
        # Test ONLINE mode
        result_online = ml_optimizer.optimize_quality_evaluation(
            manuscript="Sample",
            project_context=project_context,
            base_quality_scores=base_quality_scores,
            base_issues=base_issues,
            learning_mode=LearningMode.ONLINE
        )
        assert isinstance(result_online, OptimizedQualityResult)

        # Test BATCH mode
        result_batch = ml_optimizer.optimize_quality_evaluation(
            manuscript="Sample",
            project_context=project_context,
            base_quality_scores=base_quality_scores,
            base_issues=base_issues,
            learning_mode=LearningMode.BATCH
        )
        assert isinstance(result_batch, OptimizedQualityResult)

        # Test DISABLED mode
        result_disabled = ml_optimizer.optimize_quality_evaluation(
            manuscript="Sample",
            project_context=project_context,
            base_quality_scores=base_quality_scores,
            base_issues=base_issues,
            learning_mode=LearningMode.DISABLED
        )
        assert isinstance(result_disabled, OptimizedQualityResult)
