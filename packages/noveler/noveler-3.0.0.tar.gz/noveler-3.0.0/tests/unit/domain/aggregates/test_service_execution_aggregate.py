# File: tests/unit/domain/aggregates/test_service_execution_aggregate.py
# Purpose: Validate ServiceExecutionAggregate event emission and metrics.
# Context: Regression coverage for refactored infrastructure integration design.

"""Tests for ServiceExecutionAggregate."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from noveler.domain.aggregates.service_execution_aggregate import ServiceExecutionAggregate
from noveler.domain.value_objects.execution_policy import ExecutionPolicy
from noveler.domain.value_objects.infrastructure_service_definition import (
    InfrastructureServiceType,
    ServiceDefinition,
)


def _definition(name: str) -> ServiceDefinition:
    return ServiceDefinition(
        name=name,
        service_type=InfrastructureServiceType.CACHE_MANAGER,
        adapter_key=f"adapter:{name}",
        dependencies=frozenset(),
        execution_policy=ExecutionPolicy.default(),
    )


def test_success_updates_metrics_and_emits_event() -> None:
    aggregate = ServiceExecutionAggregate(project_id="proj-1")
    definition = _definition("cache")
    attempt = aggregate.start_execution(definition, context_hash="ctx", correlation_id="corr-1")
    aggregate.complete_success(attempt, cache_hit=False, duration_seconds=0.5)

    metrics = aggregate.metrics("cache")
    assert metrics.total == 1
    assert metrics.success == 1
    events = aggregate.pending_events()
    assert any(event.service_name == "cache" for event in events)


def test_failure_generates_events_and_metrics() -> None:
    aggregate = ServiceExecutionAggregate(project_id="proj-1")
    definition = _definition("cache")
    attempt = aggregate.start_execution(definition, context_hash="ctx", correlation_id="corr-2")
    aggregate.complete_failure(
        attempt,
        policy=definition.execution_policy,
        error_message="boom",
        retry_count=1,
    )

    metrics = aggregate.metrics("cache")
    assert metrics.total == 1
    assert metrics.failure == 1
    events = aggregate.pending_events()
    assert any(event.error_message == "boom" for event in events)
