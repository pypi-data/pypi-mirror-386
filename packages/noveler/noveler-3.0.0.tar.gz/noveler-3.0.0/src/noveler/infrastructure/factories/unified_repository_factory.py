"""Compatibility shim for legacy import path.

The unit tests still import ``noveler.infrastructure.factories.unified_repository_factory``.
The actual implementation lives in ``noveler.infrastructure.di.unified_repository_factory``.
This module simply re-exports the public API for backward compatibility.
"""

from __future__ import annotations

from noveler.infrastructure.di.unified_repository_factory import (
    UnifiedRepositoryFactory,
    get_unified_repository_factory,
    reset_unified_repository_factory,
)

__all__ = [
    "UnifiedRepositoryFactory",
    "get_unified_repository_factory",
    "reset_unified_repository_factory",
]
