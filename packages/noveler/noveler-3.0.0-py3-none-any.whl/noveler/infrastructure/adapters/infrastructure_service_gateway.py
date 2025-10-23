# File: src/noveler/infrastructure/adapters/infrastructure_service_gateway.py
# Purpose: Provide service gateway implementation for infrastructure service execution.
# Context: Implements ServiceGatewayPort to execute services via InfrastructureIntegrationAggregate.

"""Service gateway for executing infrastructure services.

Purpose:
    Execute infrastructure services through aggregates with error handling.
Context:
    Used by ServiceExecutionOrchestrator to execute services defined in aggregates.
Preconditions:
    None.
Side Effects:
    Executes external services (I/O operations).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Tuple

if TYPE_CHECKING:
    from noveler.application.infrastructure_services.infrastructure_integration_aggregate import InfrastructureIntegrationAggregate
    from noveler.application.infrastructure_services.infrastructure_integration_services import InfrastructureServiceExecutionService
    from noveler.domain.aggregates.infrastructure_service_catalog import ServiceDefinition


class AggregateServiceGateway:
    """Gateway for executing services via InfrastructureIntegrationAggregate.

    Purpose:
        Bridge between orchestrator and aggregate service execution.
    """

    def __init__(
        self,
        aggregate: InfrastructureIntegrationAggregate,
        execution_service: InfrastructureServiceExecutionService,
    ) -> None:
        """Initialize gateway with aggregate and execution service.

        Args:
            aggregate: Infrastructure integration aggregate.
            execution_service: Service to handle execution logic.

        Side Effects:
            Stores references to aggregate and execution service.
        """
        self._aggregate = aggregate
        self._execution_service = execution_service

    def execute(
        self,
        service_definition: ServiceDefinition,
        execution_context: dict[str, Any],
    ) -> Tuple[bool, Any, str | None]:
        """Execute infrastructure service through aggregate.

        Args:
            service_definition: Definition of the service to execute.
            execution_context: Context data for service execution.

        Returns:
            Tuple of (success, result, error_message).

        Side Effects:
            May execute external services with I/O side effects.
        """
        try:
            # Stub implementation - delegates to execution service
            result = self._execution_service.execute(
                self._aggregate,
                service_definition.name,
                execution_context,
            )
            return (result.success, result.execution_result, result.error_message)
        except Exception as e:
            return (False, None, str(e))
