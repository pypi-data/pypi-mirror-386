"""Infrastructure.factories.path_service_factory_impl
Where: Infrastructure implementation for path service factories.
What: Contains concrete factory implementations and helpers for path services.
Why: Keeps factory behaviour encapsulated and replaceable.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""Concrete implementation of the path service factory protocol.

This module bridges the protocol based factory lookup with the
``PathServiceAdapter`` implementation that already encapsulates the legacy
CommonPathService behaviour.

It mirrors the resolution logic from ``path_service_factory`` so callers that
go through :func:`noveler.domain.interfaces.path_service_protocol.get_path_service_manager`
receive the same results as when using the fallback helpers directly.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from noveler.domain.interfaces.path_service_protocol import PathServiceFactoryProtocol
from noveler.infrastructure.adapters.path_service_adapter import PathServiceAdapter
from noveler.infrastructure.factories.path_service_factory import (
    _resolve_project_root,
    is_mcp_environment,
)

if TYPE_CHECKING:
    from noveler.domain.interfaces.path_service import IPathService


class PathServiceFactoryImpl(PathServiceFactoryProtocol):
    """Protocol implementation that produces :class:`PathServiceAdapter` instances."""

    def __init__(self) -> None:
        self._cached_default_root: Path | None = None

    def _normalise_root(self, project_root: Path | str | None) -> Path:
        """Resolve the project root using the shared helper from the legacy factory."""
        if project_root is None:
            if self._cached_default_root is None:
                self._cached_default_root = _resolve_project_root(None)
            return self._cached_default_root
        return _resolve_project_root(project_root)

    def create_path_service(self, project_root: Path | str | None = None) -> IPathService:
        """Create a path service adapter for the requested project root."""
        root = self._normalise_root(project_root)
        return PathServiceAdapter(root)

    def create_mcp_aware_path_service(self) -> IPathService:
        """Create a path service that respects the MCP working directory rules."""
        if is_mcp_environment():
            return self.create_path_service(Path.cwd())
        return self.create_path_service()

    def create_common_path_service(self, project_root: Path | str | None = None) -> IPathService:
        """Backwards compatible creation helper used by legacy call sites."""
        return self.create_path_service(project_root)

    def is_mcp_environment(self) -> bool:
        """Expose the shared MCP environment detection utilised by the fallback."""
        return is_mcp_environment()
