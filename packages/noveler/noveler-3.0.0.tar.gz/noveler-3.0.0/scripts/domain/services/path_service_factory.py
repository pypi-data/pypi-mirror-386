# File: scripts/domain/services/path_service_factory.py
# Purpose: Provide scripts-level access to the path service factory for compliance hooks.
# Context: Forwards to noveler.domain to satisfy DDD helper imports used by tooling.

"""Wrapper module for DDD compliance tests.

Re-exports the domain path service factory helpers so that the scripts mirror
the production module layout expected by the compliance tooling.
"""

from noveler.domain.services.path_service_factory import (  # noqa: F401,F403
    IPathServiceFactory,
    create_path_service,
    get_path_service_factory,
)

__all__ = [
    "IPathServiceFactory",
    "create_path_service",
    "get_path_service_factory",
]
