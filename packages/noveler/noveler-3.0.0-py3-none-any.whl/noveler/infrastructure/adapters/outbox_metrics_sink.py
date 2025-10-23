# File: src/noveler/infrastructure/adapters/outbox_metrics_sink.py
# Purpose: Provide outbox pattern metrics sink implementation.
# Context: Implements MetricsSinkPort to store events for eventual consistency.

"""Outbox metrics sink for infrastructure services.

Purpose:
    Store domain events in outbox for transactional event publishing.
Context:
    Used by ServiceExecutionOrchestrator to ensure reliable event delivery.
Preconditions:
    None.
Side Effects:
    Stores events in memory (stub implementation).
"""

from __future__ import annotations

from typing import Iterable

from noveler.domain.events.base import DomainEvent


class OutboxMetricsSink:
    """Metrics sink using outbox pattern for reliable delivery.

    Purpose:
        Store events for eventual publishing (stub implementation).
    """

    def __init__(self) -> None:
        """Initialize outbox storage.

        Side Effects:
            Creates internal event storage.
        """
        self._outbox: list[DomainEvent] = []

    def publish(self, events: Iterable[DomainEvent]) -> None:
        """Store events in outbox for eventual publishing.

        Args:
            events: Iterable of domain events to store.

        Side Effects:
            Appends events to internal outbox list.
        """
        self._outbox.extend(events)
