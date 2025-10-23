# File: src/noveler/domain/aggregates/service_execution_aggregate.py
# Purpose: Track infrastructure service executions, metrics, and events.
# Context: Complements InfrastructureServiceCatalog in refactored architecture.

"""Service execution aggregate for infrastructure orchestration."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional

from noveler.domain.events.infrastructure_integration_events import (
    InfrastructureCacheMiss,
    InfrastructureFallbackInvoked,
    InfrastructureServiceExecuted,
    InfrastructureServiceFailed,
)
from noveler.domain.value_objects.execution_policy import ExecutionPolicy
from noveler.domain.value_objects.infrastructure_service_definition import ServiceDefinition
from noveler.domain.value_objects.project_time import project_now


@dataclass
class ExecutionAttempt:
    """Active execution attempt metadata."""

    attempt_id: str
    service_name: str
    project_id: str
    correlation_id: str
    start_time: datetime
    context_hash: str
    retries: int = 0

    @classmethod
    def start(cls, service_name: str, project_id: str, correlation_id: str, context_hash: str) -> "ExecutionAttempt":
        """Create new attempt instance."""
        return cls(
            attempt_id=str(uuid.uuid4()),
            service_name=service_name,
            project_id=project_id,
            correlation_id=correlation_id,
            start_time=datetime.now(timezone.utc),
            context_hash=context_hash,
        )


@dataclass
class ServiceMetricsSnapshot:
    """Aggregate metrics snapshot for reporting."""

    total: int = 0
    success: int = 0
    failure: int = 0
    error_rate: float = 0.0
    last_execution: Optional[datetime] = None

    def record_success(self) -> None:
        """Add success metrics."""
        self.total += 1
        self.success += 1
        self._update_error_rate()
        self.last_execution = datetime.now(timezone.utc)

    def record_failure(self) -> None:
        """Add failure metrics."""
        self.total += 1
        self.failure += 1
        self._update_error_rate()
        self.last_execution = datetime.now(timezone.utc)

    def _update_error_rate(self) -> None:
        if self.total == 0:
            self.error_rate = 0.0
        else:
            self.error_rate = (self.failure / self.total) * 100.0


class ServiceExecutionAggregate:
    """Aggregate coordinating execution metrics and events."""

    def __init__(self, project_id: str) -> None:
        self._project_id = project_id
        self._attempts: Dict[str, ExecutionAttempt] = {}
        self._metrics: Dict[str, ServiceMetricsSnapshot] = {}
        self._events: list = []

    def start_execution(self, definition: ServiceDefinition, context_hash: str, correlation_id: str) -> ExecutionAttempt:
        """Record start of execution and return attempt metadata."""
        attempt = ExecutionAttempt.start(definition.name, self._project_id, correlation_id, context_hash)
        self._attempts[attempt.attempt_id] = attempt
        self._metrics.setdefault(definition.name, ServiceMetricsSnapshot())
        return attempt

    def record_cache_miss(self, attempt: ExecutionAttempt) -> None:
        """Emit cache miss event."""
        event = InfrastructureCacheMiss(
            project_id=self._project_id,
            correlation_id=attempt.correlation_id,
            service_name=attempt.service_name,
            cache_key=attempt.context_hash,
            occurred_at=project_now().datetime,
        )
        self._events.append(event)

    def complete_success(self, attempt: ExecutionAttempt, cache_hit: bool, duration_seconds: float) -> None:
        """Complete attempt as success and emit event."""
        metrics = self._metrics.setdefault(attempt.service_name, ServiceMetricsSnapshot())
        metrics.record_success()
        event = InfrastructureServiceExecuted(
            project_id=self._project_id,
            correlation_id=attempt.correlation_id,
            service_name=attempt.service_name,
            attempt_id=attempt.attempt_id,
            cache_hit=cache_hit,
            duration_seconds=duration_seconds,
            occurred_at=project_now().datetime,
        )
        self._events.append(event)
        self._attempts.pop(attempt.attempt_id, None)

    def complete_failure(
        self,
        attempt: ExecutionAttempt,
        policy: ExecutionPolicy,
        error_message: str,
        *,
        fallback_used: bool = False,
        fallback_service: str | None = None,
        retry_count: int,
    ) -> None:
        """Complete attempt as failure and emit events."""
        metrics = self._metrics.setdefault(attempt.service_name, ServiceMetricsSnapshot())
        metrics.record_failure()
        failure_event = InfrastructureServiceFailed(
            project_id=self._project_id,
            correlation_id=attempt.correlation_id,
            service_name=attempt.service_name,
            attempt_id=attempt.attempt_id,
            retry_count=retry_count,
            error_message=error_message,
            occurred_at=project_now().datetime,
        )
        self._events.append(failure_event)

        if fallback_used and fallback_service:
            self.record_fallback(attempt, fallback_service, error_message)

        self._attempts.pop(attempt.attempt_id, None)

    def metrics(self, service_name: str) -> ServiceMetricsSnapshot:
        """Return metrics snapshot for service."""
        return self._metrics.setdefault(service_name, ServiceMetricsSnapshot())

    def is_healthy(self, service_name: str, policy: ExecutionPolicy) -> bool:
        """Evaluate health based on error threshold."""
        metrics = self._metrics.setdefault(service_name, ServiceMetricsSnapshot())
        return metrics.error_rate < policy.health_error_threshold

    def record_fallback(self, attempt: ExecutionAttempt, fallback_service: str, reason: str) -> None:
        """Record fallback invocation event."""
        fallback_event = InfrastructureFallbackInvoked(
            project_id=self._project_id,
            correlation_id=attempt.correlation_id,
            primary_service=attempt.service_name,
            fallback_service=fallback_service,
            reason=reason,
            occurred_at=project_now().datetime,
        )
        self._events.append(fallback_event)

    def pending_events(self) -> list:
        """Return and clear pending domain events."""
        events = list(self._events)
        self._events.clear()
        return events
