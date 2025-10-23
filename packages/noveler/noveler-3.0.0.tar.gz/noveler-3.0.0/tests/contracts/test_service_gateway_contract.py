# File: tests/contracts/test_service_gateway_contract.py
# Purpose: Contract tests for ServiceGatewayPort to ensure implementation compliance.
# Context: Validates AggregateServiceGateway adheres to ServiceGatewayPort protocol.

"""Contract tests for ServiceGatewayPort.

Purpose:
    Verify that all ServiceGatewayPort implementations satisfy the protocol contract.
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
    from noveler.domain.interfaces.service_gateway_port import ServiceGatewayPort

from noveler.infrastructure.adapters.infrastructure_service_gateway import AggregateServiceGateway

pytestmark = pytest.mark.contract


class TestServiceGatewayContract:
    """Contract tests for ServiceGatewayPort protocol.

    Purpose:
        Ensure implementations satisfy service execution contract.
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
    def gateway(self, mock_aggregate, mock_execution_service) -> ServiceGatewayPort:
        """Provide ServiceGatewayPort implementation for testing.

        Returns:
            AggregateServiceGateway instance as protocol implementation.
        """
        return AggregateServiceGateway(mock_aggregate, mock_execution_service)

    @pytest.mark.spec("SPEC-SERVICE_GATEWAY_PORT-EXECUTE_SUCCESS")
    def test_execute_returns_success_tuple_on_success(
        self, gateway: ServiceGatewayPort, mock_execution_service
    ) -> None:
        """Verify execute() returns (True, result, None) on success."""
        mock_result = Mock()
        mock_result.success = True
        mock_result.execution_result = {"output": "success_data"}
        mock_result.error_message = None
        mock_execution_service.execute.return_value = mock_result

        service_def = Mock(name="test_service")
        context = {"input": "test_data"}

        success, result, error = gateway.execute(service_def, context)

        assert success is True
        assert result == {"output": "success_data"}
        assert error is None

    @pytest.mark.spec("SPEC-SERVICE_GATEWAY_PORT-EXECUTE_FAILURE")
    def test_execute_returns_failure_tuple_on_failure(
        self, gateway: ServiceGatewayPort, mock_execution_service
    ) -> None:
        """Verify execute() returns (False, None, error_msg) on failure."""
        mock_result = Mock()
        mock_result.success = False
        mock_result.execution_result = None
        mock_result.error_message = "Service execution failed"
        mock_execution_service.execute.return_value = mock_result

        service_def = Mock()
        context = {}

        success, result, error = gateway.execute(service_def, context)

        assert success is False
        assert result is None
        assert "Service execution failed" in error

    @pytest.mark.spec("SPEC-SERVICE_GATEWAY_PORT-EXCEPTION_HANDLING")
    def test_execute_handles_exceptions_gracefully(
        self, gateway: ServiceGatewayPort, mock_execution_service
    ) -> None:
        """Verify execute() handles exceptions and returns error tuple."""
        mock_execution_service.execute.side_effect = RuntimeError("Unexpected error")

        service_def = Mock()
        context = {}

        success, result, error = gateway.execute(service_def, context)

        assert success is False
        assert result is None
        assert error is not None
        assert "Unexpected error" in error

    @pytest.mark.spec("SPEC-SERVICE_GATEWAY_PORT-EMPTY_CONTEXT")
    def test_execute_accepts_empty_context(
        self, gateway: ServiceGatewayPort, mock_execution_service
    ) -> None:
        """Verify execute() accepts empty execution context."""
        mock_result = Mock()
        mock_result.success = True
        mock_result.execution_result = "result"
        mock_result.error_message = None
        mock_execution_service.execute.return_value = mock_result

        service_def = Mock()
        empty_context = {}

        success, result, error = gateway.execute(service_def, empty_context)

        assert success is True


class TestServiceGatewaySpecCompliance:
    """Verify ServiceGatewayPort contract coverage and implementation compliance.

    Purpose:
        Meta-tests to ensure contract tests cover the protocol completely.
    """

    @pytest.mark.spec("SPEC-SERVICE_GATEWAY_PORT-PROTOCOL_COMPLIANCE")
    def test_aggregate_gateway_is_valid_protocol(self) -> None:
        """Verify AggregateServiceGateway satisfies ServiceGatewayPort protocol."""
        from noveler.domain.interfaces.service_gateway_port import ServiceGatewayPort

        mock_aggregate = Mock()
        mock_service = Mock()
        gateway: ServiceGatewayPort = AggregateServiceGateway(mock_aggregate, mock_service)

        assert hasattr(gateway, "execute")
        assert callable(gateway.execute)

    @pytest.mark.spec("SPEC-SERVICE_GATEWAY_PORT-CONTRACT_COVERAGE")
    def test_service_gateway_contract_coverage(self) -> None:
        """Verify contract tests cover all critical scenarios."""
        required_scenarios = [
            "success",     # test_execute_returns_success_tuple_on_success
            "failure",     # test_execute_returns_failure_tuple_on_failure
            "exception",   # test_execute_handles_exceptions_gracefully
            "empty",       # test_execute_accepts_empty_context
        ]

        test_methods = [
            method
            for method in dir(TestServiceGatewayContract)
            if method.startswith("test_")
        ]

        for scenario in required_scenarios:
            assert any(
                scenario in method for method in test_methods
            ), f"Missing contract test for scenario: {scenario}"
