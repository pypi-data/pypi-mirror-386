# File: src/noveler/application/adapters/quality_check_adapter.py
# Purpose: Adapt Application layer UseCases to Domain layer interfaces
# Context: Implements Domain interfaces to maintain DDD architecture

"""Quality check adapters for Application layer.

These adapters implement Domain interfaces and delegate to actual Application UseCases,
maintaining proper layer boundaries in DDD architecture.
"""

from __future__ import annotations
from typing import Any, Dict, Optional

from noveler.application.use_cases.quality_check_use_case import (
    QualityCheckRequest,
    QualityCheckResponse,
    QualityCheckUseCase,
)
from noveler.application.use_cases.adaptive_quality_evaluation import (
    AdaptiveQualityEvaluationUseCase,
    ModelRepository,
)
from noveler.domain.interfaces.quality_check_interface import (
    IQualityCheckUseCase,
    IAdaptiveQualityEvaluationUseCase,
    QualityCheckRequestInterface,
    QualityCheckResponseInterface,
    QualityViolationInterface,
)
from noveler.domain.interfaces.logger_service_protocol import ILoggerService
from noveler.domain.interfaces.unit_of_work_protocol import IUnitOfWorkProtocol


class QualityCheckUseCaseAdapter(IQualityCheckUseCase):
    """Adapter for QualityCheckUseCase.

    Implements Domain interface and delegates to Application UseCase.
    """

    def __init__(
        self,
        logger_service: ILoggerService | None = None,
        unit_of_work: IUnitOfWorkProtocol | None = None
    ):
        """Initialize adapter.

        Args:
            logger_service: Logger service
            unit_of_work: Unit of work
        """
        self._use_case = QualityCheckUseCase(
            logger_service=logger_service,
            unit_of_work=unit_of_work
        )

    async def execute(
        self,
        request: QualityCheckRequestInterface
    ) -> QualityCheckResponseInterface:
        """Execute quality check.

        Args:
            request: Quality check request interface

        Returns:
            Quality check response interface
        """
        # Convert interface to concrete request
        concrete_request = QualityCheckRequest(
            episode_id=request.episode_id,
            project_id=request.project_id,
            check_options=request.check_options or {}
        )

        # Execute concrete use case
        concrete_response = await self._use_case.execute(concrete_request)

        # Convert concrete response to interface
        violations = []
        if hasattr(concrete_response, 'violations') and concrete_response.violations:
            violations = [
                QualityViolationInterface(
                    rule_id=getattr(v, 'rule_id', ''),
                    severity=getattr(v, 'severity', 'warning'),
                    line_number=getattr(v, 'line_number', None),
                    column_number=getattr(v, 'column_number', None),
                    message=getattr(v, 'message', ''),
                    suggestion=getattr(v, 'suggestion', None),
                    auto_fixable=getattr(v, 'auto_fixable', False)
                )
                for v in concrete_response.violations
            ]

        return QualityCheckResponseInterface(
            total_score=getattr(concrete_response, 'total_score', None),
            violations=violations,
            auto_fix_applied=getattr(concrete_response, 'auto_fix_applied', False),
            fixed_content=getattr(concrete_response, 'fixed_content', None),
            # Backward compatibility
            passed=getattr(concrete_response, 'is_passed', False),
            metadata={}
        )


class AdaptiveQualityEvaluationUseCaseAdapter(IAdaptiveQualityEvaluationUseCase):
    """Adapter for AdaptiveQualityEvaluationUseCase.

    Implements Domain interface and delegates to Application UseCase.
    """

    def __init__(
        self,
        model_repository: ModelRepository | None = None,
        path_service: Any = None
    ):
        """Initialize adapter.

        Args:
            model_repository: Model repository
            path_service: Path service
        """
        self._use_case = AdaptiveQualityEvaluationUseCase(
            model_repository=model_repository,
            path_service=path_service
        )

    async def evaluate(
        self,
        content: str,
        episode_number: int,
        threshold: float = 0.8
    ) -> Dict[str, Any]:
        """Evaluate content quality adaptively.

        Args:
            content: Content to evaluate
            episode_number: Episode number
            threshold: Quality threshold

        Returns:
            Evaluation results
        """
        return await self._use_case.evaluate(
            content=content,
            episode_number=episode_number,
            threshold=threshold
        )

    def get_model_repository(self) -> Any:
        """Get model repository.

        Returns:
            Model repository instance
        """
        return self._use_case.model_repository