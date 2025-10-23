# File: src/noveler/application/support/default_path_service.py
# Purpose: Provide a presentation-free helper for obtaining IPathService instances.
# Context: Application layer consumers can call this when they need a default path service.
"""Default path service helper for the application layer."""

from __future__ import annotations

from pathlib import Path
from typing import overload

from noveler.domain.interfaces.path_service_protocol import IPathService
from noveler.infrastructure.factories.path_service_factory import create_common_path_service


@overload
def get_default_path_service(project_root: None = None) -> IPathService: ...


@overload
def get_default_path_service(project_root: Path | str) -> IPathService: ...


def get_default_path_service(project_root: Path | str | None = None) -> IPathService:
    """Return a path service suitable for application-layer operations."""

    return create_common_path_service(project_root)

