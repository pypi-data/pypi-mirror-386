# File: src/noveler/application/services/infrastructure_integration_mapper.py
# Purpose: Translate legacy infrastructure aggregate structures into refactored domain objects.
# Context: Supports feature-flagged migration path for infrastructure orchestration.

"""Mapper utilities for infrastructure integration refactor."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from noveler.application.infrastructure_services.infrastructure_integration_aggregate import (
    InfrastructureIntegrationAggregate,
)
from noveler.domain.aggregates.infrastructure_service_catalog import InfrastructureServiceCatalog
from noveler.domain.value_objects.execution_policy import (
    CachePolicy,
    ExecutionBackoffStrategy,
    ExecutionPolicy,
    FallbackPolicy,
)
from noveler.domain.value_objects.infrastructure_service_definition import ServiceDefinition


@dataclass
class InfrastructureIntegrationMapper:
    """Map legacy aggregate data into new domain value objects."""

    def build_catalog(
        self,
        project_id: str,
        aggregate: InfrastructureIntegrationAggregate,
    ) -> InfrastructureServiceCatalog:
        """Build catalog from legacy aggregate."""
        catalog = InfrastructureServiceCatalog(project_id=project_id)
        for service in aggregate.service_registry.get_all_services():
            definition = self._to_service_definition(service.configuration)
            catalog.register(definition, override=True)
        return catalog

    def _to_service_definition(self, config: Mapping[str, object]) -> ServiceDefinition:
        """Convert legacy configuration mapping to ServiceDefinition."""
        policy = self._execution_policy_from_config(config)
        raw = {
            "name": config["name"],
            "service_type": config["service_type"],
            "adapter_class": config.get("adapter_class") or config["name"],
            "dependencies": config.get("dependencies", []),
            "policy": {
                "timeout_seconds": policy.timeout_seconds,
                "retry_limit": policy.retry_limit,
                "backoff_strategy": policy.backoff_strategy.value,
                "health_error_threshold": policy.health_error_threshold,
                "cache": {
                    "enabled": policy.cache_policy.enabled,
                    "ttl_seconds": policy.cache_policy.ttl_seconds,
                    "max_entries": policy.cache_policy.max_entries,
                },
                "fallback": {
                    "enabled": policy.fallback_policy.enabled,
                    "service": policy.fallback_policy.fallback_service,
                    "reuse_context": policy.fallback_policy.reuse_original_context,
                },
            },
        }
        return ServiceDefinition.from_dict(raw)

    def _execution_policy_from_config(self, config: Mapping[str, object]) -> ExecutionPolicy:
        """Build ExecutionPolicy from legacy configuration."""
        cache_enabled = bool(config.get("cache_enabled", False))
        ttl_default = int(config.get("cache_ttl_seconds", config.get("cache_ttl", 3600)))
        max_entries_default = int(config.get("cache_max_size", 1000))
        cache_policy = CachePolicy(
            enabled=cache_enabled,
            ttl_seconds=ttl_default if cache_enabled else 0,
            max_entries=max_entries_default if cache_enabled else 0,
        )
        fallback = FallbackPolicy(
            enabled=bool(config.get("fallback_service")),
            fallback_service=config.get("fallback_service"),
            reuse_original_context=bool(config.get("fallback_reuse_context", True)),
        )
        return ExecutionPolicy(
            timeout_seconds=float(config.get("timeout", 60)),
            retry_limit=int(config.get("retry_count", 0)),
            backoff_strategy=ExecutionBackoffStrategy(config.get("backoff_strategy", "none")),
            cache_policy=cache_policy,
            fallback_policy=fallback,
            health_error_threshold=float(config.get("health_error_threshold", 10.0)),
        )
