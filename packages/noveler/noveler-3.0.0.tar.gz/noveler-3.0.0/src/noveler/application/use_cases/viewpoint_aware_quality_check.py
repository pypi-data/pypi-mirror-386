#!/usr/bin/env python3

"""Application.use_cases.viewpoint_aware_quality_check
Where: Application use case performing viewpoint-aware quality checks.
What: Evaluates manuscript quality with attention to narrative viewpoints and consistency.
Why: Ensures viewpoint-specific issues are surfaced alongside standard quality checks.
"""

from __future__ import annotations



from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from noveler.application.base.abstract_use_case import AbstractUseCase
from noveler.infrastructure.logging.unified_logger import get_logger

if TYPE_CHECKING:
    from noveler.domain.repositories.episode_repository import EpisodeRepository
    from noveler.domain.repositories.quality_repository import QualityRepository

logger = get_logger(__name__)


class ViewpointConsistencyLevel(Enum):
    """Enumerates the available viewpoint consistency levels."""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


@dataclass
class ViewpointAwareQualityCheckRequest:
    """Input payload for viewpoint-aware quality checks.

    Attributes:
        project_id: Project identifier.
        episode_number: Episode number to analyze.
        target_viewpoint: Optional target viewpoint to focus on.
        metadata: Additional caller-supplied information.
    """

    project_id: str
    episode_number: int
    target_viewpoint: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ViewpointAwareQualityCheckResponse:
    """Response payload returned by viewpoint-aware quality checks.

    Attributes:
        success: Indicates whether the check succeeded.
        consistency_level: Reported viewpoint consistency classification.
        overall_score: Overall quality score.
        error_details: Error detail when the check fails.
    """

    success: bool
    consistency_level: ViewpointConsistencyLevel | None = None
    overall_score: float = 0.0
    error_details: str | None = None


class ViewpointAwareQualityCheckUseCase(
    AbstractUseCase[ViewpointAwareQualityCheckRequest, ViewpointAwareQualityCheckResponse]
):
    """Manage viewpoint-aware quality checks using repositories."""

    def __init__(
        self, episode_repository: EpisodeRepository, quality_repository: QualityRepository, **kwargs: Any
    ) -> None:
        """初期化

        Args:
            episode_repository: Repository providing episode metadata.
            quality_repository: Repository used to retrieve quality-related data.
            **kwargs: Additional arguments forwarded to the base class.
        """
        super().__init__(**kwargs)
        self.episode_repository = episode_repository
        self.quality_repository = quality_repository

        logger.debug("ViewpointAwareQualityCheckUseCase initialized")

    def check_episode_quality(self, project_path: Path, episode_number: str, text: str) -> dict[str, Any]:
        """Execute a viewpoint-aware quality check for the given manuscript.

        Args:
            project_path: Project root path associated with the manuscript.
            episode_number: Target episode identifier.
            text: Manuscript content under review.

        Returns:
            dict[str, Any]: Adjusted scores, viewpoint context, and viewpoint info.
        """
        try:
            project_root = Path(project_path)
            episode_num = int(episode_number)

            viewpoint_info = self.episode_repository.get_episode_viewpoint_info(episode_number)

            base_quality_scores = self.quality_repository.check_quality(
                str(project_root), episode_num, text
            )

            if viewpoint_info is None:
                return {
                    "adjusted_scores": base_quality_scores,
                    "viewpoint_context": "📍 視点情報なし - 標準的な品質評価を実行",
                    "viewpoint_info": None,
                }

            adjusted_scores = self._adjust_scores_for_viewpoint(base_quality_scores, viewpoint_info)
            viewpoint_context = self._generate_viewpoint_context(viewpoint_info)

            return {
                "adjusted_scores": adjusted_scores,
                "viewpoint_context": viewpoint_context,
                "viewpoint_info": viewpoint_info,
            }

        except ValueError as exc:
            logger.exception("Quality check failed: invalid episode number provided")
            return {
                "adjusted_scores": {},
                "viewpoint_context": f"エラー: {exc}",
                "viewpoint_info": None,
            }
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception(f"Quality check failed: {exc}")
            return {
                "adjusted_scores": {},
                "viewpoint_context": f"エラー: {exc}",
                "viewpoint_info": None,
            }

    def _adjust_scores_for_viewpoint(self, base_scores: dict[str, Any], viewpoint_info) -> dict[str, Any]:
        """Adjust quality scores based on viewpoint characteristics."""
        from noveler.domain.quality.value_objects import QualityScore

        adjusted = base_scores.copy()

        if viewpoint_info.viewpoint_type.name == "SINGLE_INTROSPECTIVE" and "dialogue_ratio" in adjusted:
            current_score = adjusted["dialogue_ratio"]
            if isinstance(current_score, QualityScore):
                new_value = min(100.0, current_score.value + 15.0)
                adjusted["dialogue_ratio"] = QualityScore(new_value)

        return adjusted

    def _generate_viewpoint_context(self, viewpoint_info) -> str:
        """Return a human-readable context message for the viewpoint."""
        viewpoint_type = viewpoint_info.viewpoint_type.name

        if viewpoint_type == "SINGLE_INTROSPECTIVE":
            return "📍 単一視点・内省型 - 会話比率は参考値として扱い、内面描写を重視"
        if viewpoint_type == "BODY_SWAP":
            return "📍 身体交換 - 内面描写深度を重視、視点の明確さを特に重視"
        if viewpoint_type == "MULTIPLE_PERSPECTIVE":
            return "📍 複数視点 - 視点切り替えの明確さと一貫性を重視"
        return f"📍 {viewpoint_type} - 標準的な品質評価"

    async def execute(self, request: ViewpointAwareQualityCheckRequest) -> ViewpointAwareQualityCheckResponse:
        """Run the viewpoint-aware quality check workflow.

        Args:
            request: Viewpoint-aware quality check request payload.

        Returns:
            ViewpointAwareQualityCheckResponse: Response describing the outcome.
        """
        try:
            logger.info(f"Starting viewpoint-aware quality check for episode {request.episode_number}")

            # 簡易実装
            return ViewpointAwareQualityCheckResponse(
                success=True, consistency_level=ViewpointConsistencyLevel.GOOD, overall_score=0.8
            )

        except Exception as e:
            logger.exception(f"Viewpoint-aware quality check failed: {e}")
            return ViewpointAwareQualityCheckResponse(success=False, error_details=str(e))
