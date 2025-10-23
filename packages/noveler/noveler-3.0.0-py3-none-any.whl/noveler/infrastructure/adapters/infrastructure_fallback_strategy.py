# File: src/noveler/infrastructure/adapters/infrastructure_fallback_strategy.py
# Purpose: Provide fallback strategy implementation for service execution failures.
# Context: Implements FallbackStrategyPort to handle primary service failures gracefully.

"""Fallback strategy for infrastructure service execution.

Purpose:
    Implement fallback logic when primary service execution fails.
Context:
    Used by ServiceExecutionOrchestrator to invoke fallback services.
Preconditions:
    None.
Side Effects:
    Executes fallback services (I/O operations).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Tuple

if TYPE_CHECKING:
    from noveler.application.infrastructure_services.infrastructure_integration_aggregate import InfrastructureIntegrationAggregate
    from noveler.application.infrastructure_services.infrastructure_integration_services import InfrastructureServiceExecutionService
    from noveler.domain.aggregates.infrastructure_service_catalog import ServiceDefinition


class AggregateFallbackStrategy:
    """Fallback strategy using aggregate's fallback services.

    Purpose:
        Execute fallback services when primary execution fails.
    """

    def __init__(
        self,
        aggregate: InfrastructureIntegrationAggregate,
        execution_service: InfrastructureServiceExecutionService,
    ) -> None:
        """Initialize strategy with aggregate and execution service.

        Args:
            aggregate: Infrastructure integration aggregate.
            execution_service: Service to handle execution logic.

        Side Effects:
            Stores references to aggregate and execution service.
        """
        self._aggregate = aggregate
        self._execution_service = execution_service

    def invoke(
        self,
        service_definition: ServiceDefinition,
        execution_context: dict[str, Any],
        fallback_service_name: str,
    ) -> Tuple[bool, Any, str | None]:
        """Invoke fallback service when primary fails.

        Args:
            service_definition: Definition of the failed service.
            execution_context: Context from primary attempt.
            fallback_service_name: Name of fallback service to invoke.

        Returns:
            Tuple of (success, result, error_message).

        Side Effects:
            May execute fallback service with I/O side effects.
        """
        if not fallback_service_name:
            return (False, None, "No fallback service specified")

        try:
            # Stub implementation - attempts to execute fallback service
            result = self._execution_service.execute(
                self._aggregate,
                fallback_service_name,
                execution_context,
            )
            return (result.success, result.execution_result, result.error_message)
        except Exception as e:
            return (False, None, f"Fallback execution failed: {str(e)}")
