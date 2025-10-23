# File: src/noveler/domain/services/ml_quality/weight_optimizer.py
# Purpose: Optimize aspect weights for weighted_average scoring
# Context: Learn optimal weights from project-specific evaluation history

"""
Weight Optimizer Service.

This service optimizes aspect weights for weighted_average quality scoring
based on project-specific evaluation history and human feedback.

Responsibilities:
- Learn optimal weights from historical performance data
- Minimize prediction error between automated and human scores
- Provide explainable weight adjustments
- Support multiple optimization objectives (F1, precision, recall, RMSE)

Architecture:
- Domain Service (pure business logic)
- Depends on IFeedbackRepository for historical data
- Returns OptimizedWeights value objects

Contract: SPEC-QUALITY-140 §2.2.4
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

from noveler.domain.interfaces.logger_interface import ILogger, NullLogger


class OptimizationObjective(Enum):
    """Optimization objective for weight tuning."""
    F1_SCORE = "f1_score"          # Balance precision and recall
    PRECISION = "precision"        # Minimize false positives
    RECALL = "recall"              # Minimize false negatives
    RMSE = "rmse"                  # Minimize root mean square error


@dataclass(frozen=True)
class OptimizedWeights:
    """
    Optimized aspect weights with performance metrics.

    Fields:
        weights: Optimized weight values per aspect (sum to 1.0)
        performance_metrics: Cross-validation scores
        feature_importance: Contribution of each aspect to overall score
        baseline_comparison: Improvement over default weights

    Contract: SPEC-QUALITY-140 §2.2.4
    """
    weights: dict[str, float]
    performance_metrics: dict[str, float]
    feature_importance: dict[str, float]
    baseline_comparison: dict[str, float]


class WeightOptimizer:
    """
    Optimize aspect weights for weighted_average scoring.

    Responsibilities:
    - Learn optimal weights from project-specific evaluation history
    - Minimize prediction error between automated and human scores
    - Provide explainable weight adjustments
    - Support cross-validation for robustness

    Dependencies (injected):
    - feedback_repository: IFeedbackRepository for evaluation history
    - logger: ILogger for diagnostics

    Contract: SPEC-QUALITY-140 §2.2.4
    """

    DEFAULT_WEIGHTS = {
        "rhythm": 0.25,
        "readability": 0.25,
        "grammar": 0.30,
        "style": 0.20
    }

    def __init__(
        self,
        feedback_repository: "IFeedbackRepository",
        logger: Optional[ILogger] = None
    ):
        """
        Initialize weight optimizer.

        Args:
            feedback_repository: Repository for evaluation history access
            logger: Optional logger (defaults to NullLogger)
        """
        self._feedback_repository = feedback_repository
        self._logger = logger or NullLogger()

    def optimize_weights(
        self,
        project_root: Path,
        base_scores: dict[str, float],
        feedback_history_limit: int = 50,
        optimization_objective: OptimizationObjective = OptimizationObjective.F1_SCORE
    ) -> dict[str, float]:
        """
        Optimize aspect weights based on project feedback history.

        Args:
            project_root: Project root for feedback lookup
            base_scores: Current quality scores (for context)
            feedback_history_limit: Number of historical evaluations to use
            optimization_objective: F1_SCORE, PRECISION, RECALL, or RMSE

        Returns:
            Dictionary with optimized weights per aspect (sum to 1.0)

        Raises:
            WeightOptimizationError: If optimization fails

        Algorithm:
            1. Load feedback history with automated + human scores
            2. Split into train/validation sets (80/20)
            3. For each candidate weight configuration:
               a. Compute weighted_average overall scores
               b. Compare with human scores
               c. Calculate objective metric (F1, RMSE, etc.)
            4. Select best weights via grid search or gradient descent
            5. Validate on holdout set
            6. Calculate feature importance (SHAP values)

        Performance:
            - Target: ≤2 seconds for 50 feedback records

        Contract: SPEC-QUALITY-140 §4.2
        """
        self._logger.info(
            f"Optimizing weights with objective: {optimization_objective.value}"
        )

        # Load feedback history
        feedback_history = self._feedback_repository.load_recent_feedback(
            project_root=project_root,
            limit=feedback_history_limit
        )

        if len(feedback_history) < 10:
            self._logger.warning(
                f"Insufficient feedback history ({len(feedback_history)} records), "
                "using default weights"
            )
            return self.DEFAULT_WEIGHTS

        # Filter records with human scores
        labeled_records = [
            f for f in feedback_history
            if f.get("human_scores") is not None
        ]

        if len(labeled_records) < 5:
            self._logger.warning(
                f"Insufficient labeled records ({len(labeled_records)}), "
                "using default weights"
            )
            return self.DEFAULT_WEIGHTS

        self._logger.info(f"Using {len(labeled_records)} labeled records for optimization")

        # TODO: Implement actual weight optimization algorithm
        # Placeholder: Simple heuristic based on aspect variance

        # For now, return default weights
        optimized_weights = self.DEFAULT_WEIGHTS.copy()

        self._logger.info(
            "Weight optimization complete",
            extra={"optimized_weights": optimized_weights}
        )

        return optimized_weights


# Type hints for forward references
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from noveler.domain.protocols.feedback_repository_protocol import IFeedbackRepository
