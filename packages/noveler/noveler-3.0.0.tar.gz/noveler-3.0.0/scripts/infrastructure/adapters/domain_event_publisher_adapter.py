# File: scripts/infrastructure/adapters/domain_event_publisher_adapter.py
# Purpose: Provide compliance-level access to the domain event publisher adapter.
# Context: Delegates to infrastructure adapter so scripts.* mirrors production surfaces.

"""Wrapper module for DDD compliance tests.

This delegates to the production DomainEventPublisher adapter so that the
``scripts/infrastructure`` namespace exposes the same surface expected by the
DDD compliance tooling.
"""

from noveler.infrastructure.adapters.domain_event_publisher_adapter import (  # noqa: F401,F403
    ConsoleEventPublisherAdapter,
    get_domain_event_publisher,
)

__all__ = [
    "ConsoleEventPublisherAdapter",
    "get_domain_event_publisher",
]
