# File: src/noveler/infrastructure/adapters/metrics_sink_composite.py
# Purpose: Provide composite metrics sink for multiple sink coordination.
# Context: Implements MetricsSinkPort to broadcast events to multiple sinks.

"""Composite metrics sink for infrastructure services.

Purpose:
    Coordinate multiple metrics sinks with fanout pattern.
Context:
    Used by ServiceExecutionOrchestrator to send events to multiple destinations.
Preconditions:
    None.
Side Effects:
    Delegates to configured sinks.
"""

from __future__ import annotations

from typing import Iterable

from noveler.domain.events.base import DomainEvent
from noveler.domain.interfaces.metrics_sink_port import MetricsSinkPort


class CompositeMetricsSink:
    """Composite sink that broadcasts to multiple sinks.

    Purpose:
        Fanout events to multiple metrics destinations.
    """

    def __init__(self, sinks: list[MetricsSinkPort | None]) -> None:
        """Initialize with list of sinks.

        Args:
            sinks: List of metrics sinks (None values filtered out).

        Side Effects:
            Stores filtered list of sinks.
        """
        self._sinks = [s for s in sinks if s is not None]

    def publish(self, events: Iterable[DomainEvent]) -> None:
        """Publish events to all configured sinks.

        Args:
            events: Iterable of domain events to publish.

        Side Effects:
            Calls publish() on each configured sink.

        Raises:
            None (errors in individual sinks are silently ignored).
        """
        events_list = list(events)
        for sink in self._sinks:
            try:
                sink.publish(iter(events_list))
            except Exception:  # noqa: S110
                # Silent failure to prevent cascade failures
                pass
