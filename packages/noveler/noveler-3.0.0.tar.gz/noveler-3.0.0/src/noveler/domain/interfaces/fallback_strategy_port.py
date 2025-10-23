# File: src/noveler/domain/interfaces/fallback_strategy_port.py
# Purpose: Define port interface for fallback strategies in infrastructure integration.
# Context: Used by ServiceExecutionOrchestrator to handle service execution failures.

"""Fallback strategy port for service execution failure handling.

Purpose:
    Define a protocol for implementing fallback strategies when primary
    service execution fails.
Context:
    Consumed by application layer orchestrators to enable graceful degradation
    without depending on specific fallback implementations.
Preconditions:
    None.
Side Effects:
    None (interface only).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, Tuple

if TYPE_CHECKING:
    from noveler.domain.aggregates.infrastructure_service_catalog import ServiceDefinition


class FallbackStrategyPort(Protocol):
    """Protocol for fallback strategies in service execution.

    Purpose:
        Abstract fallback invocation when primary service fails.
    """

    def invoke(
        self,
        service_definition: ServiceDefinition,
        execution_context: dict[str, Any],
        fallback_service_name: str,
    ) -> Tuple[bool, Any, str | None]:
        """Invoke fallback service when primary execution fails.

        Args:
            service_definition: Definition of the failed service.
            execution_context: Execution context from primary attempt.
            fallback_service_name: Name of fallback service to invoke.

        Returns:
            Tuple of (success, result, error_message):
                - success: True if fallback succeeded, False otherwise.
                - result: Fallback execution result if successful, None otherwise.
                - error_message: Error description if failed, None if successful.

        Side Effects:
            May execute fallback service, which could have I/O side effects.

        Raises:
            None (implementations should return error in tuple instead).
        """
        ...
