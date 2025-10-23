# File: src/noveler/domain/interfaces/metrics_sink_port.py
# Purpose: Define port interface for publishing domain events to metrics systems.
# Context: Used by ServiceExecutionOrchestrator to emit execution metrics.

"""Metrics sink port for publishing domain events.

Purpose:
    Define a protocol for publishing domain events to external metrics
    collection systems.
Context:
    Consumed by application layer orchestrators to emit metrics without
    depending on specific monitoring implementations.
Preconditions:
    None.
Side Effects:
    None (interface only).
"""

from __future__ import annotations

from typing import Iterable, Protocol

from noveler.domain.events.base import DomainEvent


class MetricsSinkPort(Protocol):
    """Purpose: Describe operations for publishing domain events to metrics sinks.

    Side Effects:
        Implementations may forward events to external monitoring systems.
    """

    def publish(self, events: Iterable[DomainEvent]) -> None:
        """Purpose: Publish domain events to a metrics collection system.

        Args:
            events: Iterable of domain events to publish.

        Side Effects:
            Implementation defined; may issue network calls to monitoring platforms.

        Raises:
            None. Implementations should handle publishing errors gracefully.
        """
        ...
