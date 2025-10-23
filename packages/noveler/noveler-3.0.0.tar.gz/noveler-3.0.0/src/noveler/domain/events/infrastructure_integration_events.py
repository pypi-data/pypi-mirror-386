# File: src/noveler/domain/events/infrastructure_integration_events.py
# Purpose: Define domain events emitted during infrastructure service orchestration.
# Context: Supports refactored infrastructure integration workflow.

"""Domain events for infrastructure integration."""

from __future__ import annotations

from dataclasses import dataclass

from noveler.domain.events.base import DomainEvent


@dataclass
class InfrastructureServiceExecuted(DomainEvent):
    """Event published when a service completes successfully."""

    project_id: str = ""
    correlation_id: str = ""
    service_name: str = ""
    attempt_id: str = ""
    cache_hit: bool = False
    duration_seconds: float = 0.0


@dataclass
class InfrastructureServiceFailed(DomainEvent):
    """Event published when a service exhausts retries."""

    project_id: str = ""
    correlation_id: str = ""
    service_name: str = ""
    attempt_id: str = ""
    retry_count: int = 0
    error_message: str = ""


@dataclass
class InfrastructureFallbackInvoked(DomainEvent):
    """Event published when a fallback service is invoked."""

    project_id: str = ""
    correlation_id: str = ""
    primary_service: str = ""
    fallback_service: str = ""
    reason: str = ""


@dataclass
class InfrastructureCacheMiss(DomainEvent):
    """Event published when cache lookup fails for a service."""

    project_id: str = ""
    correlation_id: str = ""
    service_name: str = ""
    cache_key: str = ""
