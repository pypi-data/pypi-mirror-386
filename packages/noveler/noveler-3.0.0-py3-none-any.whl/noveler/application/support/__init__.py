# File: src/noveler/application/support/__init__.py
# Purpose: Expose default service helpers for application-layer consumers.
# Context: Keeps application utilities presentation-agnostic.
"""Support helpers for the Noveler application layer."""

from .default_console_service import get_default_console_service
from .default_logger_service import get_default_logger_service
from .default_path_service import get_default_path_service

__all__ = [
    "get_default_console_service",
    "get_default_logger_service",
    "get_default_path_service",
]
