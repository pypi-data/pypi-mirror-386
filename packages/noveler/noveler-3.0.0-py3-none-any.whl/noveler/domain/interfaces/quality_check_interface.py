# File: src/noveler/domain/interfaces/quality_check_interface.py
# Purpose: Define interfaces for quality check operations to maintain DDD layer boundaries
# Context: Domain layer contracts that Application layer must implement

"""Quality check interfaces for Domain layer.

These interfaces define contracts that Application layer implementations must follow,
maintaining proper DDD architecture without Domain depending on Application.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class QualityCheckRequestInterface:
    """Interface for quality check requests."""
    episode_id: str
    project_id: str
    check_options: Optional[Dict[str, Any]] = None
    # Backward compatibility fields
    episode_number: Optional[int] = None
    content: Optional[str] = None
    check_type: str = "comprehensive"
    threshold_score: float = 75.0
    auto_fix: bool = False
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class QualityViolationInterface:
    """Interface for quality violations."""
    rule_id: str
    severity: str
    line_number: Optional[int]
    column_number: Optional[int]
    message: str
    suggestion: Optional[str] = None
    auto_fixable: bool = False


@dataclass
class QualityCheckResponseInterface:
    """Interface for quality check responses."""
    # Primary fields used by QualityGateService
    total_score: Optional[float] = None
    violations: Optional[List[QualityViolationInterface]] = None
    auto_fix_applied: bool = False
    fixed_content: Optional[str] = None

    # Backward compatibility fields
    episode_number: Optional[int] = None
    overall_score: Optional[float] = None
    passed: bool = False
    metadata: Optional[Dict[str, Any]] = None


class IQualityCheckUseCase(ABC):
    """Interface for quality check use case.

    This interface must be implemented by Application layer
    and injected into Domain services that need quality checking.
    """

    @abstractmethod
    async def execute(
        self,
        request: QualityCheckRequestInterface
    ) -> QualityCheckResponseInterface:
        """Execute quality check.

        Args:
            request: Quality check request

        Returns:
            Quality check response
        """
        pass


class IAdaptiveQualityEvaluationUseCase(ABC):
    """Interface for adaptive quality evaluation use case.

    This interface supports machine learning-based quality evaluation.
    """

    @abstractmethod
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
        pass

    @abstractmethod
    def get_model_repository(self) -> Any:
        """Get model repository.

        Returns:
            Model repository instance
        """
        pass