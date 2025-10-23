# File: src/noveler/domain/aggregates/infrastructure_service_catalog.py
# Purpose: Manage infrastructure service definitions, dependencies, and invariants.
# Context: Replaces responsibilities previously embedded in InfrastructureIntegrationAggregate.

"""Infrastructure service catalog aggregate."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List

from noveler.domain.exceptions import DomainException
from noveler.domain.value_objects.infrastructure_service_definition import ServiceDefinition


@dataclass
class _DependencyGraph:
    """Internal helper for dependency tracking."""

    edges: Dict[str, set[str]] = field(default_factory=dict)

    def add(self, service: str, dependency: str) -> None:
        """Record dependency."""
        self.edges.setdefault(service, set()).add(dependency)

    def remove_service(self, service: str, *, preserve_inbound: bool = False) -> None:
        """Remove service from graph."""
        self.edges.pop(service, None)
        if not preserve_inbound:
            for deps in self.edges.values():
                deps.discard(service)

    def has_cycle(self) -> bool:
        """Detect cycles using DFS."""
        visited: set[str] = set()
        stack: set[str] = set()

        def visit(node: str) -> bool:
            if node in stack:
                return True
            if node in visited:
                return False
            visited.add(node)
            stack.add(node)
            for neighbour in self.edges.get(node, ()):  # pragma: no branch - simple iteration
                if visit(neighbour):
                    return True
            stack.remove(node)
            return False

        return any(visit(node) for node in list(self.edges))

    def toposort(self) -> List[str]:
        """Return nodes in dependency order."""
        indegree: Dict[str, int] = {}
        adjacency: Dict[str, set[str]] = {}
        nodes = set(self.edges)
        for deps in self.edges.values():
            nodes.update(deps)
        for node in nodes:
            indegree[node] = 0
        for service, deps in self.edges.items():
            indegree.setdefault(service, 0)
            indegree[service] += len(deps)
            for dep in deps:
                adjacency.setdefault(dep, set()).add(service)
        queue = [node for node, degree in indegree.items() if degree == 0]
        ordered: List[str] = []
        while queue:
            node = queue.pop(0)
            ordered.append(node)
            for dependent in adjacency.get(node, ()):
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    queue.append(dependent)
        if len(ordered) != len(indegree):
            msg = "Cycle detected while ordering services"
            raise DomainException(msg)
        return ordered


class InfrastructureServiceCatalog:
    """Aggregate storing infrastructure service definitions."""

    def __init__(self, project_id: str) -> None:
        self._project_id = project_id
        self._services: Dict[str, ServiceDefinition] = {}
        self._dependency_graph = _DependencyGraph()

    @property
    def project_id(self) -> str:
        """Return project identifier."""
        return self._project_id

    def register(self, definition: ServiceDefinition, *, override: bool = False) -> None:
        """Register service definition."""
        if definition.name in self._services and not override:
            msg = f"Service '{definition.name}' is already registered"
            raise DomainException(msg)

        self._validate_dependencies(definition)
        if override:
            self._dependency_graph.remove_service(definition.name, preserve_inbound=True)

        self._services[definition.name] = definition
        for dependency in definition.dependencies:
            self._dependency_graph.add(definition.name, dependency)

        if self._dependency_graph.has_cycle():
            self._dependency_graph.remove_service(definition.name)
            self._services.pop(definition.name, None)
            msg = f"Cyclic dependency detected when adding '{definition.name}'"
            raise DomainException(msg)

    def get(self, service_name: str) -> ServiceDefinition | None:
        """Return definition by name."""
        return self._services.get(service_name)

    def list_all(self) -> Iterable[ServiceDefinition]:
        """Iterate over registered services."""
        return list(self._services.values())

    def ordered_services(self) -> List[ServiceDefinition]:
        """Return services respecting dependency order."""
        ordered_names = self._dependency_graph.toposort()
        return [self._services[name] for name in ordered_names if name in self._services]

    def _validate_dependencies(self, definition: ServiceDefinition) -> None:
        """Ensure dependencies exist or will be registered later."""
        unresolved = [
            dependency
            for dependency in definition.dependencies
            if dependency not in self._services and dependency != definition.name
        ]
        if unresolved:
            missing = ", ".join(sorted(unresolved))
            msg = f"Dependencies missing for '{definition.name}': {missing}"
            raise DomainException(msg)
