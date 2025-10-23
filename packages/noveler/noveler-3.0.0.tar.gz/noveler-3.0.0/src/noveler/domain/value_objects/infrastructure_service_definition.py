# File: src/noveler/domain/value_objects/infrastructure_service_definition.py
# Purpose: Represent infrastructure service metadata for domain aggregates.
# Context: Enables InfrastructureServiceCatalog and orchestrator to share definitions.

"""Infrastructure service definition value objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import FrozenSet, Mapping

from noveler.domain.exceptions import DomainException
from noveler.domain.value_objects.execution_policy import ExecutionPolicy


class InfrastructureServiceType(Enum):
    """Enumeration of supported infrastructure service types."""

    QUALITY_CHECKER = "quality_checker"
    EPISODE_MANAGER = "episode_manager"
    CONFIG_LOADER = "config_loader"
    CACHE_MANAGER = "cache_manager"
    FILE_SYSTEM = "file_system"
    BACKUP_MANAGER = "backup_manager"


@dataclass(frozen=True)
class ServiceDefinition:
    """Service definition used inside InfrastructureServiceCatalog."""

    name: str
    service_type: InfrastructureServiceType
    adapter_key: str
    dependencies: FrozenSet[str] = field(default_factory=frozenset)
    execution_policy: ExecutionPolicy = field(default_factory=ExecutionPolicy.default)

    def __post_init__(self) -> None:
        if not self.name:
            msg = "Service name cannot be empty"
            raise DomainException(msg)
        if not self.adapter_key:
            msg = "Adapter key cannot be empty"
            raise DomainException(msg)
        normalized_deps = frozenset(dep for dep in self.dependencies if dep and dep != self.name)
        object.__setattr__(self, "dependencies", normalized_deps)
        self.execution_policy.validate()

    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> "ServiceDefinition":
        """Create definition from mapping compatible with legacy configuration."""
        policy = ExecutionPolicy.from_dict(raw.get("policy", {}))
        return cls(
            name=str(raw["name"]),
            service_type=InfrastructureServiceType(raw["service_type"]),
            adapter_key=str(raw.get("adapter_class") or raw.get("adapter_key") or raw["name"]),
            dependencies=frozenset(raw.get("dependencies", []) or []),
            execution_policy=policy,
        )

    def requires(self, dependency: str) -> bool:
        """Return True when the service depends on the given name."""
        return dependency in self.dependencies
