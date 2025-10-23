# File: tests/unit/domain/services/test_machine_learning_based_similarity_service.py
# Purpose: Verify MachineLearningBasedSimilarityService defaults and logging behaviour.
# Context: Ensures NullLogger fallback remains stable when no logger is injected.

"""Tests for MachineLearningBasedSimilarityService logging defaults and behaviour."""

from pathlib import Path

import pytest

from noveler.domain.entities.similarity_analyzer import SimilarityAnalyzer
from noveler.domain.interfaces.logger_interface import NullLogger
from noveler.domain.services.machine_learning_based_similarity_service import (
    MachineLearningBasedSimilarityService,
)
from noveler.domain.value_objects.function_signature import FunctionSignature
from noveler.infrastructure.adapters.nlp_analysis_adapter import NLPAnalysisAdapter
from noveler.infrastructure.adapters.similarity_calculation_adapter import (
    BasicSimilarityCalculationAdapter,
)


@pytest.mark.unit
class TestMachineLearningBasedSimilarityService:
    """Unit tests covering initialisation and basic analysis behaviour."""

    def _make_function(self, name: str, path: str) -> FunctionSignature:
        return FunctionSignature(
            name=name,
            module_path="noveler.tests",
            file_path=Path(path),
            line_number=12,
            parameters=["value"],
            return_type="None",
            docstring="Test stub",
            ddd_layer="domain",
        )

    def test_initialisation_without_logger_uses_null_logger(self) -> None:
        """Service should default to NullLogger when logger is omitted."""

        similarity_analyzer = SimilarityAnalyzer(BasicSimilarityCalculationAdapter())
        nlp_adapter = NLPAnalysisAdapter(enable_advanced_features=True)

        service = MachineLearningBasedSimilarityService(
            similarity_analyzer=similarity_analyzer,
            nlp_analyzer=nlp_adapter,
            logger=None,
            project_root=Path("/tmp/project"),
        )

        assert isinstance(service._logger, NullLogger)

    def test_analyse_similarity_succeeds_with_default_logger(self) -> None:
        """Basic analysis should complete even when no logger is provided."""

        similarity_analyzer = SimilarityAnalyzer(BasicSimilarityCalculationAdapter())
        nlp_adapter = NLPAnalysisAdapter(enable_advanced_features=False)
        service = MachineLearningBasedSimilarityService(
            similarity_analyzer=similarity_analyzer,
            nlp_analyzer=nlp_adapter,
        )

        source = self._make_function("foo", "/tmp/foo.py")
        target = self._make_function("bar", "/tmp/bar.py")

        result = service.analyze_ml_based_similarity(source, target)

        assert result.source_function == source
        assert result.target_function == target
        assert result.feature_importance_ranking
