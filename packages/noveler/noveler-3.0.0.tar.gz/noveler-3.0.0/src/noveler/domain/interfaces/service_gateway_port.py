# File: src/noveler/domain/interfaces/service_gateway_port.py
# Purpose: Define port interface for executing infrastructure services.
# Context: Used by ServiceExecutionOrchestrator to abstract service execution details.

"""Service gateway port for infrastructure service execution.

Purpose:
    Define a protocol for executing infrastructure services with context.
Context:
    Consumed by application layer orchestrators to execute services without
    depending on specific gateway implementations.
Preconditions:
    None.
Side Effects:
    None (interface only).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, Tuple

if TYPE_CHECKING:
    from noveler.domain.aggregates.infrastructure_service_catalog import ServiceDefinition


class ServiceGatewayPort(Protocol):
    """Protocol for service gateways that execute infrastructure services.

    Purpose:
        Abstract service execution operations with error handling.
    """

    def execute(
        self,
        service_definition: ServiceDefinition,
        execution_context: dict[str, Any],
    ) -> Tuple[bool, Any, str | None]:
        """Execute infrastructure service with provided context.

        Args:
            service_definition: Definition of the service to execute.
            execution_context: Context data for service execution.

        Returns:
            Tuple of (success, result, error_message):
                - success: True if execution succeeded, False otherwise.
                - result: Service execution result if successful, None otherwise.
                - error_message: Error description if failed, None if successful.

        Side Effects:
            May execute external services, which could have I/O side effects.

        Raises:
            None (implementations should return error in tuple instead).
        """
        ...
