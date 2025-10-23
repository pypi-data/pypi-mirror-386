#!/usr/bin/env python3

"""Unit tests for QualityGateService.

Tests the Domain service that provides quality gate functionality,
ensuring proper dependency injection and architectural compliance.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from dataclasses import dataclass
import asyncio

from noveler.domain.services.writing_steps.quality_gate_service import (
    QualityGateService,
    QualityGatePolicy,
    QualityGateResult,
    QualityGateResponse
)
from noveler.domain.interfaces.quality_check_interface import (
    IQualityCheckUseCase,
    IAdaptiveQualityEvaluationUseCase,
    QualityCheckRequestInterface,
    QualityCheckResponseInterface,
    QualityViolationInterface
)


class TestQualityGateService:
    """Test suite for QualityGateService."""

    @pytest.fixture
    def mock_quality_check_use_case(self):
        """Create a mock quality check use case."""
        mock = Mock(spec=IQualityCheckUseCase)
        mock.execute = AsyncMock()
        return mock

    @pytest.fixture
    def mock_adaptive_use_case(self):
        """Create a mock adaptive quality evaluation use case."""
        mock = Mock(spec=IAdaptiveQualityEvaluationUseCase)
        mock.evaluate = AsyncMock()
        mock.get_model_repository = Mock(return_value=None)
        return mock

    @pytest.fixture
    def mock_logger_service(self):
        """Create a mock logger service."""
        mock = Mock()
        mock.info = Mock()
        mock.error = Mock()
        mock.warning = Mock()
        return mock

    @pytest.fixture
    def quality_gate_service(
        self,
        mock_quality_check_use_case,
        mock_adaptive_use_case,
        mock_logger_service
    ):
        """Create a QualityGateService instance with mocked dependencies."""
        return QualityGateService(
            logger_service=mock_logger_service,
            unit_of_work=None,
            quality_policy=QualityGatePolicy(),
            quality_check_use_case=mock_quality_check_use_case,
            adaptive_quality_use_case=mock_adaptive_use_case
        )

    @pytest.mark.asyncio
    async def test_execute_with_passing_quality_gate(
        self,
        quality_gate_service,
        mock_quality_check_use_case
    ):
        """Test quality gate execution with passing score."""
        # Arrange
        mock_response = QualityCheckResponseInterface(
            total_score=85.0,
            violations=[],
            auto_fix_applied=False,
            fixed_content=None,
            passed=True
        )
        mock_quality_check_use_case.execute.return_value = mock_response

        # Act
        result = await quality_gate_service.execute(
            episode_number=1,
            previous_results={}
        )

        # Assert
        assert result.success is True
        assert result.quality_result is not None
        assert result.quality_result.gate_passed is True
        assert result.quality_result.overall_score == 85.0
        assert len(result.quality_result.critical_violations) == 0
        assert len(result.quality_result.warning_violations) == 0

    @pytest.mark.asyncio
    async def test_execute_with_failing_quality_gate(
        self,
        quality_gate_service,
        mock_quality_check_use_case
    ):
        """Test quality gate execution with failing score."""
        # Arrange
        violation = QualityViolationInterface(
            rule_id="structure_001",
            severity="critical",
            line_number=10,
            column_number=5,
            message="Structure issue detected",
            suggestion="Fix the structure",
            auto_fixable=True
        )

        mock_response = QualityCheckResponseInterface(
            total_score=60.0,
            violations=[violation],
            auto_fix_applied=False,
            fixed_content=None,
            passed=False
        )
        mock_quality_check_use_case.execute.return_value = mock_response

        # Act
        result = await quality_gate_service.execute(
            episode_number=1,
            previous_results={}
        )

        # Assert
        assert result.success is True
        assert result.quality_result is not None
        assert result.quality_result.gate_passed is False
        assert result.quality_result.overall_score == 60.0
        assert len(result.quality_result.critical_violations) == 1
        assert result.quality_result.critical_violations[0].rule_id == "structure_001"

    @pytest.mark.asyncio
    async def test_execute_with_adaptive_evaluation(
        self,
        quality_gate_service,
        mock_quality_check_use_case,
        mock_adaptive_use_case
    ):
        """Test quality gate with adaptive evaluation enabled."""
        # Enable adaptive evaluation
        quality_gate_service.quality_policy.adaptive_evaluation = True

        # Arrange
        mock_response = QualityCheckResponseInterface(
            total_score=75.0,
            violations=[],
            auto_fix_applied=False,
            fixed_content=None,
            passed=True
        )
        mock_quality_check_use_case.execute.return_value = mock_response

        mock_adaptive_use_case.evaluate.return_value = {
            "adaptive_enabled": True,
            "adjusted_scores": {"overall": 82.0}
        }

        # Act
        result = await quality_gate_service.execute(
            episode_number=1,
            previous_results={}
        )

        # Assert
        assert result.success is True
        assert mock_adaptive_use_case.evaluate.called is True  # Evaluate method should be called when adaptive evaluation is enabled

    @pytest.mark.asyncio
    async def test_execute_handles_exception(
        self,
        quality_gate_service,
        mock_quality_check_use_case
    ):
        """Test quality gate handles exceptions gracefully."""
        # Arrange
        mock_quality_check_use_case.execute.side_effect = Exception("Test error")

        # Act
        result = await quality_gate_service.execute(
            episode_number=1,
            previous_results={}
        )

        # Assert
        assert result.success is False
        assert "Test error" in result.error_message
        assert result.quality_result is None

    def test_quality_gate_policy_defaults(self):
        """Test QualityGatePolicy default values."""
        policy = QualityGatePolicy()

        assert policy.min_quality_score == 70.0
        assert policy.strict_mode is False
        assert policy.auto_fix_enabled is True
        assert "structure" in policy.critical_categories
        assert "consistency" in policy.critical_categories
        assert "readability" in policy.critical_categories
        assert "style" in policy.warning_categories
        assert policy.adaptive_evaluation is False

    @pytest.mark.asyncio
    async def test_strict_mode_fails_on_warnings(
        self,
        mock_quality_check_use_case,
        mock_adaptive_use_case,
        mock_logger_service
    ):
        """Test strict mode fails when warnings are present."""
        # Create service with strict mode enabled
        strict_policy = QualityGatePolicy(strict_mode=True)
        service = QualityGateService(
            logger_service=mock_logger_service,
            quality_policy=strict_policy,
            quality_check_use_case=mock_quality_check_use_case,
            adaptive_quality_use_case=mock_adaptive_use_case
        )

        # Create a warning violation
        warning = QualityViolationInterface(
            rule_id="style_001",
            severity="warning",
            line_number=5,
            column_number=1,
            message="Style issue",
            suggestion="Fix style",
            auto_fixable=False
        )

        mock_response = QualityCheckResponseInterface(
            total_score=85.0,  # High score
            violations=[warning],
            auto_fix_applied=False,
            fixed_content=None,
            passed=True
        )
        mock_quality_check_use_case.execute.return_value = mock_response

        # Act
        result = await service.execute(
            episode_number=1,
            previous_results={}
        )

        # Assert
        assert result.success is True
        assert result.quality_result.gate_passed is False  # Fails due to strict mode
        assert len(result.quality_result.warning_violations) == 1