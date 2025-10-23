# File: src/noveler/application/infrastructure_services/service_execution_orchestrator.py
# Purpose: Coordinate infrastructure service execution using refactored domain aggregates.
# Context: Bridges legacy aggregate execution with new orchestration, cache, and fallback handling.

"""Service execution orchestrator for refactored infrastructure integration."""

from __future__ import annotations

import hashlib
import time
import uuid
from typing import Callable, Iterable

from noveler.application.infrastructure_services.infrastructure_integration_aggregate import (
    InfrastructureIntegrationAggregate,
)
from noveler.application.infrastructure_services.infrastructure_integration_services import (
    ExecuteServiceRequest,
    ExecuteServiceResponse,
    InfrastructureServiceExecutionService,
)
from noveler.application.services.infrastructure_integration_mapper import InfrastructureIntegrationMapper
from noveler.domain.aggregates.service_execution_aggregate import ServiceExecutionAggregate
from noveler.domain.entities.infrastructure_integration_aggregate import ServiceExecutionResult
from noveler.domain.events.base import DomainEvent
from noveler.domain.interfaces.cache_provider_port import CacheProviderPort
from noveler.domain.interfaces.fallback_strategy_port import FallbackStrategyPort
from noveler.domain.interfaces.metrics_sink_port import MetricsSinkPort
from noveler.domain.interfaces.service_gateway_port import ServiceGatewayPort
from noveler.infrastructure.adapters.infrastructure_cache_provider import InMemoryCacheProvider
from noveler.infrastructure.adapters.infrastructure_fallback_strategy import AggregateFallbackStrategy
from noveler.infrastructure.adapters.infrastructure_service_gateway import AggregateServiceGateway


class _NullMetricsSink(MetricsSinkPort):
    """Default metrics sink when none is provided."""

    def publish(self, events: Iterable[DomainEvent]) -> None:
        """Drop events by default."""
        del events


class ServiceExecutionOrchestrator:
    """Coordinate service execution with new domain aggregates."""

    def __init__(
        self,
        execution_service: InfrastructureServiceExecutionService | None = None,
        metrics_sink: MetricsSinkPort | None = None,
        mapper: InfrastructureIntegrationMapper | None = None,
        cache_provider: CacheProviderPort | None = None,
        gateway_factory: Callable[[InfrastructureIntegrationAggregate], ServiceGatewayPort] | None = None,
        fallback_factory: Callable[[InfrastructureIntegrationAggregate], FallbackStrategyPort] | None = None,
    ) -> None:
        self._execution_service = execution_service or InfrastructureServiceExecutionService()
        self._metrics_sink = metrics_sink or _NullMetricsSink()
        self._mapper = mapper or InfrastructureIntegrationMapper()
        self._cache_provider = cache_provider or InMemoryCacheProvider()
        self._gateway_factory = gateway_factory
        self._fallback_factory = fallback_factory

    def execute(
        self,
        aggregate: InfrastructureIntegrationAggregate,
        request: ExecuteServiceRequest,
    ) -> ExecuteServiceResponse:
        """Execute service using refactored orchestration flow."""
        catalog = self._mapper.build_catalog(aggregate.project_id, aggregate)
        definition = catalog.get(request.service_name)
        if not definition:
            return ExecuteServiceResponse(success=False, error_message=f"サービス '{request.service_name}' が登録されていません")

        execution_aggregate = ServiceExecutionAggregate(project_id=aggregate.project_id)
        correlation_id = str(uuid.uuid4())
        execution_context = dict(request.execution_context)
        execution_context.setdefault("project_id", request.project_id)

        context_hash = self._hash_context(execution_context)
        attempt = execution_aggregate.start_execution(definition, context_hash=context_hash, correlation_id=correlation_id)

        cache_policy = definition.execution_policy.cache_policy
        cache_key = f"{definition.name}:{context_hash}"
        if cache_policy.enabled:
            cached_result: ServiceExecutionResult | None = self._cache_provider.get(cache_key)
            if cached_result:
                execution_aggregate.complete_success(attempt, cache_hit=True, duration_seconds=0.0)
                self._publish_events(execution_aggregate)
                return ExecuteServiceResponse(success=True, execution_result=cached_result)
            execution_aggregate.record_cache_miss(attempt)

        gateway = self._resolve_gateway(aggregate)
        fallback_strategy = self._resolve_fallback_strategy(aggregate)

        policy = definition.execution_policy
        last_error: str | None = None

        while True:
            start_time = time.monotonic()
            success, execution_result, error_message = gateway.execute(definition, execution_context)
            duration = time.monotonic() - start_time

            if success and execution_result:
                execution_aggregate.complete_success(attempt, cache_hit=False, duration_seconds=duration)
                if cache_policy.enabled:
                    self._cache_provider.set(cache_key, execution_result, cache_policy.ttl_seconds)
                self._publish_events(execution_aggregate)
                return ExecuteServiceResponse(success=True, execution_result=execution_result)

            last_error = error_message or "サービス実行に失敗しました"
            attempt.retries += 1

            if policy.should_retry(attempt.retries):
                continue

            fallback_policy = policy.fallback_policy
            if fallback_policy.allows_fallback() and fallback_strategy:
                fallback_success, fallback_result, fallback_error = fallback_strategy.invoke(
                    definition,
                    execution_context,
                    fallback_policy.fallback_service or "",
                )
                if fallback_success and fallback_result:
                    execution_aggregate.record_fallback(
                        attempt,
                        fallback_policy.fallback_service or "",
                        last_error,
                    )
                    execution_aggregate.complete_success(attempt, cache_hit=False, duration_seconds=duration)
                    if cache_policy.enabled:
                        self._cache_provider.set(cache_key, fallback_result, cache_policy.ttl_seconds)
                    self._publish_events(execution_aggregate)
                    return ExecuteServiceResponse(success=True, execution_result=fallback_result)
                last_error = fallback_error or last_error
                execution_aggregate.complete_failure(
                    attempt,
                    policy,
                    last_error,
                    fallback_used=True,
                    fallback_service=fallback_policy.fallback_service,
                    retry_count=attempt.retries,
                )
            else:
                execution_aggregate.complete_failure(
                    attempt,
                    policy,
                    last_error,
                    fallback_used=False,
                    fallback_service=None,
                    retry_count=attempt.retries,
                )
            break

        self._publish_events(execution_aggregate)
        return ExecuteServiceResponse(success=False, error_message=last_error or "サービス実行に失敗しました")

    def _hash_context(self, context: dict) -> str:
        """Create deterministic hash for execution context."""
        serialized_items = ",".join(f"{key}={context[key]!r}" for key in sorted(context))
        return hashlib.sha256(serialized_items.encode("utf-8")).hexdigest()

    def _resolve_gateway(
        self,
        aggregate: InfrastructureIntegrationAggregate,
    ) -> ServiceGatewayPort:
        """Return gateway instance for aggregate."""
        if self._gateway_factory:
            return self._gateway_factory(aggregate)
        return AggregateServiceGateway(aggregate, self._execution_service)

    def _resolve_fallback_strategy(
        self,
        aggregate: InfrastructureIntegrationAggregate,
    ) -> FallbackStrategyPort | None:
        """Return fallback strategy for aggregate."""
        if self._fallback_factory:
            return self._fallback_factory(aggregate)
        return AggregateFallbackStrategy(aggregate, self._execution_service)

    def _publish_events(self, execution_aggregate: ServiceExecutionAggregate) -> None:
        """Publish pending domain events to the configured sink."""
        events = execution_aggregate.pending_events()
        if events:
            self._metrics_sink.publish(events)
