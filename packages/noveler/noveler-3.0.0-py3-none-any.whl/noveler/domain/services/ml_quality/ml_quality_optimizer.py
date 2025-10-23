# File: src/noveler/domain/services/ml_quality/ml_quality_optimizer.py
# Purpose: ML-based quality optimization orchestrator service
# Context: Integrates corpus learning, dynamic thresholds, weight optimization, and severity estimation

"""
ML Quality Optimizer Service.

This service orchestrates ML-enhanced quality evaluation by coordinating:
- Corpus-based baseline metrics
- Dynamic threshold adjustment
- Weight optimization
- Context-aware severity estimation

Architecture:
- Domain Service (pure business logic, no infrastructure dependencies)
- Depends on other domain services via dependency injection
- Returns domain entities and value objects only

Contract: SPEC-QUALITY-140 §2.2.1
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

from noveler.domain.interfaces.logger_interface import ILogger, NullLogger


class LearningMode(Enum):
    """Learning mode for ML optimization."""
    ONLINE = "online"      # Incremental learning
    BATCH = "batch"        # Full retraining
    DISABLED = "disabled"  # No learning


@dataclass(frozen=True)
class ProjectContext:
    """Project metadata for ML optimization."""
    project_root: Path
    genre: str
    target_audience: str
    episode_count: int
    avg_quality_score: Optional[float] = None


@dataclass(frozen=True)
class OptimizedQualityResult:
    """
    Result of ML-enhanced quality evaluation.

    Fields:
        base_scores: Standard quality scores (rhythm, readability, grammar, style)
        optimized_scores: ML-adjusted scores
        dynamic_thresholds: Context-aware thresholds learned from corpus
        severity_adjustments: Position/frequency-based severity modifications
        improvement_priorities: Ranked improvement suggestions
        ml_metadata: Debugging and explainability metadata
    """
    base_scores: dict[str, float]
    optimized_scores: dict[str, float]
    dynamic_thresholds: dict[str, dict]
    severity_adjustments: list[dict]
    improvement_priorities: list[dict]
    ml_metadata: dict


class MLQualityOptimizer:
    """
    ML-based quality optimization orchestrator.

    Responsibilities:
    - Integrate corpus learning, dynamic thresholds, and feedback loops
    - Coordinate weight optimization and severity estimation
    - Generate adaptive quality recommendations

    Dependencies (injected):
    - corpus_analyzer: CorpusAnalyzer for baseline metrics
    - threshold_adjuster: DynamicThresholdAdjuster for learned thresholds
    - weight_optimizer: WeightOptimizer for aspect weights
    - severity_estimator: SeverityEstimator for context-aware penalties
    - logger: ILogger for diagnostics

    Contract: SPEC-QUALITY-140 §2.2.1
    """

    def __init__(
        self,
        corpus_analyzer: "CorpusAnalyzer",
        threshold_adjuster: "DynamicThresholdAdjuster",
        weight_optimizer: "WeightOptimizer",
        severity_estimator: "SeverityEstimator",
        logger: Optional[ILogger] = None
    ):
        """
        Initialize ML quality optimizer.

        Args:
            corpus_analyzer: Service for corpus-based baseline metrics
            threshold_adjuster: Service for dynamic threshold adjustment
            weight_optimizer: Service for weight optimization
            severity_estimator: Service for severity estimation
            logger: Optional logger (defaults to NullLogger)
        """
        self._corpus_analyzer = corpus_analyzer
        self._threshold_adjuster = threshold_adjuster
        self._weight_optimizer = weight_optimizer
        self._severity_estimator = severity_estimator
        self._logger = logger or NullLogger()

    def optimize_quality_evaluation(
        self,
        manuscript: str,
        project_context: ProjectContext,
        base_quality_scores: dict[str, float],
        base_issues: list[dict],
        learning_mode: LearningMode = LearningMode.ONLINE
    ) -> OptimizedQualityResult:
        """
        Execute ML-enhanced quality evaluation.

        Args:
            manuscript: Target manuscript text
            project_context: Project metadata (genre, target_audience, etc.)
            base_quality_scores: Standard quality scores from existing checks
            base_issues: List of quality issues from existing checks
            learning_mode: ONLINE (incremental), BATCH (full retrain), or DISABLED

        Returns:
            OptimizedQualityResult with:
            - base_scores: Original quality scores
            - optimized_scores: ML-adjusted scores
            - dynamic_thresholds: Context-aware thresholds
            - severity_adjustments: Position/frequency-based adjustments
            - improvement_priorities: Ranked improvement suggestions

        Raises:
            MLOptimizationError: If optimization fails critically

        Algorithm:
            1. Extract corpus baseline metrics (genre-specific)
            2. Adjust thresholds based on corpus + feedback history
            3. Optimize aspect weights using historical performance
            4. Re-score issues with context-aware severity
            5. Generate prioritized improvement suggestions

        Performance:
            - Target: ≤10 seconds total (5s ML overhead + 5s standard checks)
            - Corpus metrics: ≤3s (cached: ≤100ms)
            - Weight optimization: ≤2s
            - Severity estimation: ≤100ms per issue

        Contract: SPEC-QUALITY-140 §4, §11
        """
        self._logger.info(
            "Starting ML-enhanced quality evaluation",
            extra={
                "genre": project_context.genre,
                "learning_mode": learning_mode.value
            }
        )

        if learning_mode == LearningMode.DISABLED:
            self._logger.info("ML optimization disabled, returning base scores")
            return OptimizedQualityResult(
                base_scores=base_quality_scores,
                optimized_scores=base_quality_scores,
                dynamic_thresholds={},
                severity_adjustments=[],
                improvement_priorities=[],
                ml_metadata={"mode": "disabled"}
            )

        # Step 1: Get corpus-based baseline metrics
        self._logger.debug("Fetching corpus baseline metrics")
        corpus_metrics = self._corpus_analyzer.build_baseline_metrics(
            genre=project_context.genre,
            target_audience=project_context.target_audience,
            project_root=project_context.project_root
        )

        # Step 2: Adjust thresholds dynamically
        self._logger.debug("Adjusting thresholds based on feedback history")
        dynamic_thresholds = self._threshold_adjuster.adjust_thresholds(
            current_thresholds=self._extract_current_thresholds(base_quality_scores),
            corpus_metrics=corpus_metrics,
            project_root=project_context.project_root
        )

        # Step 3: Optimize weights
        self._logger.debug("Optimizing aspect weights")
        optimized_weights = self._weight_optimizer.optimize_weights(
            project_root=project_context.project_root,
            base_scores=base_quality_scores
        )

        # Step 4: Re-estimate severity with context
        self._logger.debug("Re-estimating issue severity with context")
        severity_adjustments = []
        for issue in base_issues:
            adjusted = self._severity_estimator.estimate_severity(
                issue=issue,
                manuscript=manuscript,
                total_lines=manuscript.count('\n') + 1
            )
            severity_adjustments.append(adjusted)

        # Step 5: Recalculate optimized scores
        optimized_scores = self._recalculate_scores(
            base_scores=base_quality_scores,
            weights=optimized_weights,
            severity_adjustments=severity_adjustments
        )

        # Step 6: Generate improvement priorities
        improvement_priorities = self._generate_priorities(
            severity_adjustments=severity_adjustments,
            optimized_scores=optimized_scores,
            dynamic_thresholds=dynamic_thresholds
        )

        self._logger.info(
            "ML optimization complete",
            extra={
                "base_overall": base_quality_scores.get("overall", 0),
                "optimized_overall": optimized_scores.get("overall", 0),
                "priority_count": len(improvement_priorities)
            }
        )

        return OptimizedQualityResult(
            base_scores=base_quality_scores,
            optimized_scores=optimized_scores,
            dynamic_thresholds=dynamic_thresholds,
            severity_adjustments=severity_adjustments,
            improvement_priorities=improvement_priorities,
            ml_metadata={
                "mode": learning_mode.value,
                "corpus_sample_count": corpus_metrics.get("sample_count", 0),
                "weights_optimized": True,
                "thresholds_adjusted": True
            }
        )

    def _extract_current_thresholds(
        self,
        base_scores: dict[str, float]
    ) -> dict[str, float]:
        """
        Extract current thresholds from base scores.

        This is a placeholder implementation. In production, thresholds
        should be read from .novelerrc.yaml or project configuration.
        """
        return {
            "overall": 80.0,
            "rhythm": 75.0,
            "readability": 70.0,
            "grammar": 85.0,
            "style": 75.0
        }

    def _recalculate_scores(
        self,
        base_scores: dict[str, float],
        weights: dict[str, float],
        severity_adjustments: list[dict]
    ) -> dict[str, float]:
        """
        Recalculate quality scores using optimized weights and adjusted severities.

        Algorithm:
            1. Apply optimized weights to each aspect score
            2. Adjust overall score based on re-estimated severity
            3. Ensure scores remain in [0, 100] range
        """
        # Placeholder: Simple weighted average
        # TODO: Integrate severity adjustments into score calculation
        weighted_sum = sum(
            base_scores.get(aspect, 0) * weights.get(aspect, 0)
            for aspect in weights.keys()
        )
        weight_total = sum(weights.values())

        optimized_overall = weighted_sum / weight_total if weight_total > 0 else 0

        optimized_scores = base_scores.copy()
        optimized_scores["overall"] = max(0.0, min(100.0, optimized_overall))

        return optimized_scores

    def _generate_priorities(
        self,
        severity_adjustments: list[dict],
        optimized_scores: dict[str, float],
        dynamic_thresholds: dict[str, dict]
    ) -> list[dict]:
        """
        Generate prioritized improvement suggestions.

        Algorithm:
            1. Identify aspects below dynamic thresholds
            2. Sort by (severity × impact) descending
            3. Return top N suggestions
        """
        priorities = []

        for aspect, score in optimized_scores.items():
            if aspect == "overall":
                continue

            threshold_data = dynamic_thresholds.get(aspect, {})
            threshold = threshold_data.get("threshold", 80.0)

            if score < threshold:
                gap = threshold - score
                priorities.append({
                    "aspect": aspect,
                    "current_score": score,
                    "target_threshold": threshold,
                    "gap": gap,
                    "priority": gap * 1.0  # Simple priority: larger gap = higher priority
                })

        # Sort by priority descending
        priorities.sort(key=lambda x: x["priority"], reverse=True)

        # Return top 5
        return priorities[:5]


# Type hints for forward references
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from noveler.domain.services.ml_quality.corpus_analyzer import CorpusAnalyzer
    from noveler.domain.services.ml_quality.dynamic_threshold_adjuster import DynamicThresholdAdjuster
    from noveler.domain.services.ml_quality.weight_optimizer import WeightOptimizer
    from noveler.domain.services.ml_quality.severity_estimator import SeverityEstimator
