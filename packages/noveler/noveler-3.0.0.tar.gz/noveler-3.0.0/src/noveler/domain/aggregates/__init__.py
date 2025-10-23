# File: src/noveler/domain/aggregates/__init__.py
# Purpose: Expose domain aggregates for infrastructure integration.
# Context: Introduced alongside refactored infrastructure integration architecture.

"""Domain aggregates package."""

from noveler.domain.aggregates.infrastructure_service_catalog import InfrastructureServiceCatalog
from noveler.domain.aggregates.service_execution_aggregate import ServiceExecutionAggregate

__all__ = [
    "InfrastructureServiceCatalog",
    "ServiceExecutionAggregate",
]
