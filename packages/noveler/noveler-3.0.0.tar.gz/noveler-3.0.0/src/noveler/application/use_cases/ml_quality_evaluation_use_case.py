# File: src/noveler/application/use_cases/ml_quality_evaluation_use_case.py
# Purpose: Application use case for ML-enhanced quality evaluation
# Context: Orchestrates ML quality optimization at application layer

"""
ML Quality Evaluation Use Case.

This use case orchestrates ML-enhanced quality evaluation by coordinating
domain services and repositories.

Architecture:
- Application Layer (orchestration logic)
- Depends on domain services via dependency injection
- Returns application-layer DTOs

Contract: SPEC-QUALITY-140 §2.1
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from noveler.domain.interfaces.logger_interface import (
    ILogger,
    NullLogger,
)
from noveler.domain.services.ml_quality import (
    MLQualityOptimizer,
    LearningMode,
    ProjectContext,
)
from noveler.domain.value_objects.episode_number import EpisodeNumber


@dataclass
class MLQualityEvaluationRequest:
    """
    Request for ML-enhanced quality evaluation.

    Attributes:
        episode_number: Episode to evaluate
        project_root: Project root path
        manuscript_text: Manuscript content
        base_quality_scores: Standard quality scores from existing checks
        base_issues: List of quality issues from existing checks
        ml_enabled: Enable ML optimization (default: False)
        learning_mode: ONLINE, BATCH, or DISABLED
        corpus_model_id: Optional specific corpus model to use
        auto_optimize_weights: Auto-optimize aspect weights
        use_dynamic_severity: Use context-aware severity estimation
    """
    episode_number: int
    project_root: Path
    manuscript_text: str
    base_quality_scores: dict[str, float]
    base_issues: list[dict]
    ml_enabled: bool = False
    learning_mode: str = "online"
    corpus_model_id: Optional[str] = None
    auto_optimize_weights: bool = False
    use_dynamic_severity: bool = True


@dataclass
class MLQualityEvaluationResponse:
    """
    Response from ML-enhanced quality evaluation.

    Attributes:
        success: Whether evaluation succeeded
        base_scores: Original quality scores
        optimized_scores: ML-adjusted scores (if ML enabled)
        dynamic_thresholds: Learned thresholds (if ML enabled)
        severity_adjustments: Context-aware severity adjustments
        improvement_priorities: Ranked improvement suggestions
        ml_metadata: ML optimization metadata
        error_message: Error message if failed
    """
    success: bool
    base_scores: dict[str, float]
    optimized_scores: dict[str, float]
    dynamic_thresholds: dict
    severity_adjustments: list[dict]
    improvement_priorities: list[dict]
    ml_metadata: dict
    error_message: Optional[str] = None


class MLQualityEvaluationUseCase:
    """
    ML-enhanced quality evaluation use case.

    This use case orchestrates ML quality optimization by:
    - Extracting project context
    - Coordinating ML optimizer
    - Handling errors and fallbacks
    - Recording feedback for learning

    Dependencies (injected):
    - ml_quality_optimizer: MLQualityOptimizer domain service
    - feedback_repository: IFeedbackRepository for recording results
    - logger: ILogger for diagnostics

    Contract: SPEC-QUALITY-140 §2.1
    """

    def __init__(
        self,
        ml_quality_optimizer: MLQualityOptimizer,
        feedback_repository: "IFeedbackRepository",
        logger: Optional[ILogger] = None
    ):
        """
        Initialize use case.

        Args:
            ml_quality_optimizer: Domain service for ML optimization
            feedback_repository: Repository for feedback recording
            logger: Optional logger (defaults to NullLogger)
        """
        self._ml_optimizer = ml_quality_optimizer
        self._feedback_repository = feedback_repository
        self._logger = logger or NullLogger()

    def execute(
        self,
        request: MLQualityEvaluationRequest
    ) -> MLQualityEvaluationResponse:
        """
        Execute ML-enhanced quality evaluation.

        Args:
            request: Evaluation request

        Returns:
            MLQualityEvaluationResponse with optimized results

        Algorithm:
            1. Extract project context (genre, target_audience)
            2. If ML disabled, return base scores
            3. Call MLQualityOptimizer with learning mode
            4. Handle ML optimization errors (fallback to base scores)
            5. Record feedback for future learning
            6. Return optimized results

        Performance:
            - Target: ≤15 seconds total (10s ML + 5s standard checks)

        Contract: SPEC-QUALITY-140 §5.2
        """
        # エピソード番号のバリデーション
        try:
            episode_number_vo = EpisodeNumber(request.episode_number)
        except ValueError as e:
            return MLQualityEvaluationResponse(
                success=False,
                base_scores=request.base_quality_scores,
                optimized_scores=request.base_quality_scores,
                dynamic_thresholds={},
                severity_adjustments=[],
                improvement_priorities=[],
                ml_metadata={"ml_enabled": False},
                error_message=f"無効なエピソード番号: {e}"
            )

        self._logger.info(
            f"Starting ML quality evaluation for episode {episode_number_vo.value}",
            extra={"ml_enabled": request.ml_enabled}
        )

        # Step 1: Extract project context
        project_context = self._extract_project_context(request)

        # Step 2: If ML disabled, return base scores
        if not request.ml_enabled:
            self._logger.info("ML optimization disabled, returning base scores")
            return MLQualityEvaluationResponse(
                success=True,
                base_scores=request.base_quality_scores,
                optimized_scores=request.base_quality_scores,
                dynamic_thresholds={},
                severity_adjustments=[],
                improvement_priorities=[],
                ml_metadata={"ml_enabled": False}
            )

        # Step 3: Execute ML optimization
        try:
            learning_mode = LearningMode(request.learning_mode.lower())

            optimized_result = self._ml_optimizer.optimize_quality_evaluation(
                manuscript=request.manuscript_text,
                project_context=project_context,
                base_quality_scores=request.base_quality_scores,
                base_issues=request.base_issues,
                learning_mode=learning_mode
            )

            # Step 4: Record feedback for learning
            self._record_feedback(
                request=request,
                optimized_result=optimized_result
            )

            # Step 5: Return optimized results
            return MLQualityEvaluationResponse(
                success=True,
                base_scores=optimized_result.base_scores,
                optimized_scores=optimized_result.optimized_scores,
                dynamic_thresholds=optimized_result.dynamic_thresholds,
                severity_adjustments=optimized_result.severity_adjustments,
                improvement_priorities=optimized_result.improvement_priorities,
                ml_metadata=optimized_result.ml_metadata
            )

        except Exception as e:
            # Fallback to base scores on ML error
            self._logger.error(
                f"ML optimization failed, falling back to base scores: {e}",
                exc_info=True
            )

            return MLQualityEvaluationResponse(
                success=True,  # Still success, just without ML
                base_scores=request.base_quality_scores,
                optimized_scores=request.base_quality_scores,
                dynamic_thresholds={},
                severity_adjustments=[],
                improvement_priorities=[],
                ml_metadata={
                    "ml_enabled": True,
                    "ml_failed": True,
                    "fallback_reason": str(e)
                },
                error_message=f"ML optimization failed: {e}"
            )

    def _extract_project_context(
        self,
        request: MLQualityEvaluationRequest
    ) -> ProjectContext:
        """
        Extract project context from request.

        This is a placeholder implementation. In production, this should:
        - Read project_info.yaml for genre/target_audience
        - Query episode count from episode repository
        - Calculate average quality score from quality history

        Args:
            request: Evaluation request

        Returns:
            ProjectContext for ML optimization
        """
        # TODO: Implement actual project context extraction
        # Placeholder: use defaults
        return ProjectContext(
            project_root=request.project_root,
            genre="fantasy",  # Should be read from project_info.yaml
            target_audience="young_adult",
            episode_count=request.episode_number,
            avg_quality_score=None
        )

    def _record_feedback(
        self,
        request: MLQualityEvaluationRequest,
        optimized_result
    ) -> None:
        """
        Record evaluation feedback for future learning.

        Args:
            request: Original request
            optimized_result: Optimized result from ML optimizer
        """
        try:
            from datetime import datetime

            # エピソード番号の再バリデーション (既にバリデーション済みだが安全のため)
            try:
                episode_number_vo = EpisodeNumber(request.episode_number)
            except ValueError:
                # バリデーションエラーの場合はフィードバック記録をスキップ
                return

            feedback = {
                "episode_number": episode_number_vo.value,
                "evaluation_timestamp": datetime.now(),
                "automated_scores": optimized_result.optimized_scores,
                "human_scores": None,  # Will be populated later if user provides feedback
                "user_corrections": [],
                "outcome": "PASS" if optimized_result.optimized_scores.get("overall", 0) >= 80 else "FAIL",
                "feedback_source": "AUTOMATED",
                "source": "AUTOMATED",  # Maintain compatibility with repository contract
                "aspects_checked": list(optimized_result.optimized_scores.keys()),
                "notes": None
            }

            self._feedback_repository.save_feedback(
                feedback=feedback,
                project_root=request.project_root
            )

            self._logger.debug("Feedback recorded successfully")

        except Exception as e:
            # Don't fail evaluation if feedback recording fails
            self._logger.warning(f"Failed to record feedback: {e}")


# Type hints for forward references
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from noveler.domain.protocols.feedback_repository_protocol import IFeedbackRepository
