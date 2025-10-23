# File: src/noveler/infrastructure/utils/infra_path.py
# Purpose: Provide infrastructure-safe path service access without direct
#          presentation layer dependencies.
# Context: B20/DDD compliance - Infrastructure layer should use factories
#          from application layer for path service access

"""Infrastructure-safe path service access utilities.

This module provides path service access for Infrastructure layer services
without violating DDD layering principles. It delegates to application
layer factories which manage dependency injection properly.

Usage:
    from noveler.infrastructure.utils.infra_path import get_path_service

    path_service = get_path_service()
    project_root = path_service.project_root
    manuscript_dir = path_service.get_manuscript_dir()
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from noveler.domain.services.path_service import PathService

__all__ = ["get_path_service", "get_project_root"]


def get_path_service(project_root: str | Path | None = None) -> PathService:
    """Return a PathService instance for infrastructure layer services.

    Delegates to application layer factory which handles proper
    dependency injection without violating DDD boundaries.

    Args:
        project_root: Optional project root path. If None, uses current directory.

    Returns:
        PathService instance configured for the given project root
    """
    from noveler.infrastructure.factories.path_service_factory import create_path_service

    return create_path_service(project_root)


def get_project_root(project_root: str | Path | None = None) -> Path:
    """Return the project root path.

    Convenience function for infrastructure services that only need
    the project root without full PathService interface.

    Args:
        project_root: Optional project root path. If None, uses current directory.

    Returns:
        Path to project root
    """
    return get_path_service(project_root).project_root
