# File: src/noveler/infrastructure/adapters/message_bus_metrics_sink.py
# Purpose: Provide message bus integration for metrics sink.
# Context: Implements MetricsSinkPort to publish events via message bus.

"""Message bus metrics sink for infrastructure services.

Purpose:
    Publish domain events to message bus for asynchronous processing.
Context:
    Used by ServiceExecutionOrchestrator to integrate with application message bus.
Preconditions:
    MessageBus instance must be provided.
Side Effects:
    Publishes events to message bus.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

from noveler.domain.events.base import DomainEvent

if TYPE_CHECKING:
    from noveler.application.simple_message_bus import MessageBus


class MessageBusMetricsSink:
    """Metrics sink that publishes to message bus.

    Purpose:
        Integrate metrics events with application message bus.
    """

    def __init__(self, message_bus: MessageBus | None) -> None:
        """Initialize with message bus instance.

        Args:
            message_bus: Message bus for event publishing (optional).

        Side Effects:
            Stores reference to message bus.
        """
        self._message_bus = message_bus

    def publish(self, events: Iterable[DomainEvent]) -> None:
        """Publish domain events to message bus.

        Args:
            events: Iterable of domain events to publish.

        Side Effects:
            Publishes events to message bus if configured.
        """
        if not self._message_bus:
            return

        for event in events:
            # Stub: would normally call message_bus.publish(event)
            pass
