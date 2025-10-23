# File: scripts/domain/interfaces/event_publisher_protocol.py
# Purpose: Expose domain event publisher protocol aliases for compliance checks.
# Context: Re-exports production interfaces so scripts-level DDD tests import cleanly.

"""Wrapper module for DDD compliance tests.

This re-exports the production event publisher protocol so that
``scripts/domain`` mirrors the real domain interface layout expected by the
DDD compliance tooling.
"""

from noveler.domain.interfaces.event_publisher_protocol import *  # noqa: F401,F403

__all__ = [name for name in globals() if not name.startswith("_")]
