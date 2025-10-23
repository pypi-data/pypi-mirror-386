# File: tests/contracts/test_fallback_strategy_contract.py
# Purpose: Contract tests for FallbackStrategyPort to ensure implementation compliance.
# Context: Validates AggregateFallbackStrategy adheres to FallbackStrategyPort protocol.

"""Contract tests for FallbackStrategyPort.

Purpose:
    Verify that all FallbackStrategyPort implementations satisfy the protocol contract.
Context:
    Part of B20 Workflow Phase 4 contract testing requirements.
Preconditions:
    None.
Side Effects:
    None (read-only tests).
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest

if TYPE_CHECKING:
    from noveler.domain.interfaces.fallback_strategy_port import FallbackStrategyPort

from noveler.infrastructure.adapters.infrastructure_fallback_strategy import AggregateFallbackStrategy

pytestmark = pytest.mark.contract


class TestFallbackStrategyContract:
    """Contract tests for FallbackStrategyPort protocol.

    Purpose:
        Ensure implementations satisfy fallback invocation contract.
    """

    @pytest.fixture
    def mock_aggregate(self):
        """Provide mock aggregate for testing."""
        aggregate = Mock()
        aggregate.project_id = "test_project"
        return aggregate

    @pytest.fixture
    def mock_execution_service(self):
        """Provide mock execution service for testing."""
        service = Mock()
        return service

    @pytest.fixture
    def strategy(self, mock_aggregate, mock_execution_service) -> FallbackStrategyPort:
        """Provide FallbackStrategyPort implementation for testing.

        Returns:
            AggregateFallbackStrategy instance as protocol implementation.
        """
        return AggregateFallbackStrategy(mock_aggregate, mock_execution_service)

    @pytest.mark.spec("SPEC-FALLBACK_STRATEGY_PORT-INVOKE_SUCCESS")
    def test_invoke_returns_success_tuple_on_success(
        self, strategy: FallbackStrategyPort, mock_execution_service
    ) -> None:
        """Verify invoke() returns (True, result, None) on success."""
        mock_result = Mock()
        mock_result.success = True
        mock_result.execution_result = {"data": "fallback_result"}
        mock_result.error_message = None
        mock_execution_service.execute.return_value = mock_result

        service_def = Mock(name="primary_service")
        context = {"key": "value"}

        success, result, error = strategy.invoke(service_def, context, "fallback_service")

        assert success is True
        assert result == {"data": "fallback_result"}
        assert error is None

    @pytest.mark.spec("SPEC-FALLBACK_STRATEGY_PORT-INVOKE_FAILURE")
    def test_invoke_returns_failure_tuple_on_failure(
        self, strategy: FallbackStrategyPort, mock_execution_service
    ) -> None:
        """Verify invoke() returns (False, None, error_msg) on failure."""
        mock_result = Mock()
        mock_result.success = False
        mock_result.execution_result = None
        mock_result.error_message = "Fallback service failed"
        mock_execution_service.execute.return_value = mock_result

        service_def = Mock()
        context = {}

        success, result, error = strategy.invoke(service_def, context, "fallback_service")

        assert success is False
        assert result is None
        assert "Fallback service failed" in error

    @pytest.mark.spec("SPEC-FALLBACK_STRATEGY_PORT-EMPTY_NAME")
    def test_invoke_rejects_empty_fallback_name(
        self, strategy: FallbackStrategyPort
    ) -> None:
        """Verify invoke() rejects empty fallback service name."""
        service_def = Mock()
        context = {}

        success, result, error = strategy.invoke(service_def, context, "")

        assert success is False
        assert result is None
        assert "No fallback service specified" in error

    @pytest.mark.spec("SPEC-FALLBACK_STRATEGY_PORT-EXCEPTION_HANDLING")
    def test_invoke_handles_exceptions_gracefully(
        self, strategy: FallbackStrategyPort, mock_execution_service
    ) -> None:
        """Verify invoke() handles exceptions and returns error tuple."""
        mock_execution_service.execute.side_effect = RuntimeError("Unexpected error")

        service_def = Mock()
        context = {}

        success, result, error = strategy.invoke(service_def, context, "fallback_service")

        assert success is False
        assert result is None
        assert "Fallback execution failed" in error
        assert "Unexpected error" in error


class TestFallbackStrategySpecCompliance:
    """Verify FallbackStrategyPort contract coverage and implementation compliance.

    Purpose:
        Meta-tests to ensure contract tests cover the protocol completely.
    """

    @pytest.mark.spec("SPEC-FALLBACK_STRATEGY_PORT-PROTOCOL_COMPLIANCE")
    def test_aggregate_implementation_is_valid_protocol(self) -> None:
        """Verify AggregateFallbackStrategy satisfies FallbackStrategyPort protocol."""
        from noveler.domain.interfaces.fallback_strategy_port import FallbackStrategyPort

        mock_aggregate = Mock()
        mock_service = Mock()
        strategy: FallbackStrategyPort = AggregateFallbackStrategy(mock_aggregate, mock_service)

        # Protocol methods exist
        assert hasattr(strategy, "invoke")
        assert callable(strategy.invoke)

    @pytest.mark.spec("SPEC-FALLBACK_STRATEGY_PORT-CONTRACT_COVERAGE")
    def test_fallback_strategy_contract_coverage(self) -> None:
        """Verify contract tests cover all critical scenarios."""
        required_scenarios = [
            "success",      # test_invoke_returns_success_tuple_on_success
            "failure",      # test_invoke_returns_failure_tuple_on_failure
            "empty",        # test_invoke_rejects_empty_fallback_name
            "exception",    # test_invoke_handles_exceptions_gracefully
        ]

        test_methods = [
            method
            for method in dir(TestFallbackStrategyContract)
            if method.startswith("test_")
        ]

        for scenario in required_scenarios:
            assert any(
                scenario in method for method in test_methods
            ), f"Missing contract test for scenario: {scenario}"
