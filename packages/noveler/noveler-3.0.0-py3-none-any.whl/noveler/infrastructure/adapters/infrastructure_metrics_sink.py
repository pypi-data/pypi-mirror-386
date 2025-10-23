# File: src/noveler/infrastructure/adapters/infrastructure_metrics_sink.py
# Purpose: Provide logging-based metrics sink implementation.
# Context: Implements MetricsSinkPort to emit metrics to application logs.

"""Logging metrics sink for infrastructure services.

Purpose:
    Emit domain events to application logs for debugging and monitoring.
Context:
    Used by ServiceExecutionOrchestrator when no external metrics system is configured.
Preconditions:
    None.
Side Effects:
    Writes to application logs.
"""

from __future__ import annotations

from typing import Iterable

from noveler.domain.events.base import DomainEvent
from noveler.infrastructure.logging.unified_logger import get_logger

logger = get_logger(__name__)


class LoggingMetricsSink:
    """Metrics sink that logs events to application logger.

    Purpose:
        Simple metrics sink for development and debugging.
    """

    def publish(self, events: Iterable[DomainEvent]) -> None:
        """Publish domain events to logger.

        Args:
            events: Iterable of domain events to log.

        Side Effects:
            Writes INFO-level logs for each event.
        """
        for event in events:
            logger.info(f"[MetricsEvent] {event.__class__.__name__}: {event}")
