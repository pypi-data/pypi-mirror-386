# File: src/noveler/domain/services/path_service_factory.py
# Purpose: Provide domain-level accessors for path service factories while
#          avoiding direct infrastructure coupling in DDD compliance tests.
# Context: Re-exports the protocol-based factory interface and exposes helpers
#          that internally use the lazy proxy defined in the domain layer.

"""Domain-facing helpers for obtaining path service factories.

The DDD compliance suite expects a module under ``noveler.domain.services``
that exposes ``IPathServiceFactory`` and convenience functions for
constructing path service instances. This module wires those helpers through
to the lazily initialised proxy defined in
``noveler.domain.interfaces.path_service_protocol`` so the domain layer stays
decoupled from infrastructure details.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from noveler.domain.interfaces.i_path_service import IPathService
from noveler.domain.interfaces.path_service_protocol import (
    PathServiceFactoryProtocol as IPathServiceFactory,
    get_path_service_manager,
)


def get_path_service_factory() -> IPathServiceFactory:
    """Return the lazily loaded path service factory.

    Returns:
        IPathServiceFactory: Factory capable of creating path service
        implementations for different runtime contexts.
    """

    return get_path_service_manager().factory


def create_path_service(project_root: Optional[Path | str] = None) -> IPathService:
    """Create a path service instance using the shared factory.

    Args:
        project_root: Optional project root override when resolving paths.

    Returns:
        IPathService: A concrete path service implementation.
    """

    return get_path_service_manager().create_path_service(project_root)


__all__ = ["IPathServiceFactory", "create_path_service", "get_path_service_factory"]

