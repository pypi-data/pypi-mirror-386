# File: tests/unit/domain/aggregates/test_infrastructure_service_catalog.py
# Purpose: Verify InfrastructureServiceCatalog invariants and ordering.
# Context: Regression coverage for refactored infrastructure integration design.

"""Tests for InfrastructureServiceCatalog aggregate."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

import pytest

from noveler.domain.aggregates.infrastructure_service_catalog import InfrastructureServiceCatalog
from noveler.domain.exceptions import DomainException
from noveler.domain.value_objects.execution_policy import ExecutionPolicy
from noveler.domain.value_objects.infrastructure_service_definition import (
    InfrastructureServiceType,
    ServiceDefinition,
)


def _service(name: str, *, deps: set[str] | None = None) -> ServiceDefinition:
    return ServiceDefinition(
        name=name,
        service_type=InfrastructureServiceType.CONFIG_LOADER,
        adapter_key=f"adapter:{name}",
        dependencies=frozenset(deps or set()),
        execution_policy=ExecutionPolicy.default(),
    )


def test_register_and_retrieve_services() -> None:
    catalog = InfrastructureServiceCatalog(project_id="proj-123")
    catalog.register(_service("config"))
    catalog.register(_service("quality", deps={"config"}))

    quality = catalog.get("quality")
    assert quality is not None
    assert quality.requires("config")


def test_duplicate_registration_without_override_raises() -> None:
    catalog = InfrastructureServiceCatalog(project_id="proj-123")
    catalog.register(_service("config"))

    with pytest.raises(DomainException):
        catalog.register(_service("config"))


def test_circular_dependencies_detected() -> None:
    catalog = InfrastructureServiceCatalog(project_id="proj-123")
    catalog.register(_service("config"))
    catalog.register(_service("quality", deps={"config"}))

    with pytest.raises(DomainException):
        catalog.register(_service("config", deps={"quality"}), override=True)


def test_dependency_ordering_respects_dependencies() -> None:
    catalog = InfrastructureServiceCatalog(project_id="proj-123")
    catalog.register(_service("config"))
    catalog.register(_service("quality", deps={"config"}))
    catalog.register(_service("report", deps={"quality"}))

    ordered = [service.name for service in catalog.ordered_services()]
    assert ordered.index("config") < ordered.index("quality") < ordered.index("report")
