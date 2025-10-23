# File: src/noveler/infrastructure/factories/ml_similarity_service_factory.py
# Purpose: Provide factory helpers for MachineLearningBasedSimilarityService with safe defaults.
# Context: Centralises adapter wiring and logger injection for ML similarity workflows.

"""Factory helpers for constructing machine-learning similarity services."""

from __future__ import annotations

from pathlib import Path

from noveler.domain.entities.similarity_analyzer import SimilarityAnalyzer
from noveler.domain.interfaces.logger_interface import ILogger
from noveler.domain.services.machine_learning_based_similarity_service import (
    MachineLearningBasedSimilarityService,
)
from noveler.infrastructure.adapters.nlp_analysis_adapter import NLPAnalysisAdapter
from noveler.infrastructure.adapters.similarity_calculation_adapter import (
    BasicSimilarityCalculationAdapter,
)
from noveler.infrastructure.logging.unified_logger import get_logger


def _resolve_project_root(project_root: str | Path | None) -> Path:
    """Normalise project root input to a ``Path`` instance."""

    if project_root is None:
        return Path.cwd()
    if isinstance(project_root, Path):
        return project_root
    return Path(project_root)


def create_ml_similarity_service(
    *,
    project_root: str | Path | None = None,
    enable_advanced_ml: bool = True,
    logger: ILogger | None = None,
) -> MachineLearningBasedSimilarityService:
    """Build a MachineLearningBasedSimilarityService with standard adapters."""

    similarity_analyzer = SimilarityAnalyzer(BasicSimilarityCalculationAdapter())
    nlp_adapter = NLPAnalysisAdapter(enable_advanced_features=enable_advanced_ml)
    resolved_logger = logger or get_logger(__name__)
    resolved_root = _resolve_project_root(project_root)

    return MachineLearningBasedSimilarityService(
        similarity_analyzer=similarity_analyzer,
        nlp_analyzer=nlp_adapter,
        logger=resolved_logger,
        project_root=resolved_root,
        enable_advanced_ml=enable_advanced_ml,
    )


def create_ml_similarity_service_with_overrides(
    *,
    project_root: str | Path | None = None,
    enable_advanced_ml: bool = True,
    logger: ILogger | None = None,
    similarity_analyzer: SimilarityAnalyzer | None = None,
    nlp_adapter: NLPAnalysisAdapter | None = None,
) -> MachineLearningBasedSimilarityService:
    """Factory allowing adapter overrides for specialised scenarios."""

    resolved_logger = logger or get_logger(__name__)
    resolved_root = _resolve_project_root(project_root)

    analyzer = similarity_analyzer or SimilarityAnalyzer(BasicSimilarityCalculationAdapter())
    nlp = nlp_adapter or NLPAnalysisAdapter(enable_advanced_features=enable_advanced_ml)

    return MachineLearningBasedSimilarityService(
        similarity_analyzer=analyzer,
        nlp_analyzer=nlp,
        logger=resolved_logger,
        project_root=resolved_root,
        enable_advanced_ml=enable_advanced_ml,
    )
