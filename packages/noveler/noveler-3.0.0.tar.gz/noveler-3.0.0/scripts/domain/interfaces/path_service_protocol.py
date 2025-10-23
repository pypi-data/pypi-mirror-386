"""Wrapper module for DDD compliance tests.

This file re-exports the production PathService protocol so that
scripts/domain mirrors the real domain interface layout.
"""

from noveler.domain.interfaces.path_service_protocol import *  # noqa: F401,F403
