"""Infrastructure.adapters.logger_service_adapter
Where: Infrastructure adapter exposing structured logging to the domain.
What: Wraps the platform logger and implements the domain logging interface.
Why: Lets domain workflows log without depending on specific logging libraries.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""Adapter that exposes the unified logger via the `ILoggerService` contract."""


from typing import Any

from noveler.infrastructure.logging.unified_logger import (
    LogLevel,
)
from noveler.infrastructure.logging.unified_logger import (
    get_logger as _get_logger,
)


class LoggerServiceAdapter:
    """Wrap the unified logger to satisfy the `ILoggerService` interface."""

    def __init__(self, name: str = "noveler") -> None:
        """Initialize the adapter with the requested logger name.

        Args:
            name: Registered logger identifier.
        """
        self._wrapped_logger = _get_logger(name)

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Emit a debug-level log message."""
        self._wrapped_logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Emit an info-level log message."""
        self._wrapped_logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Emit a warning-level log message."""
        self._wrapped_logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Emit an error-level log message."""
        self._wrapped_logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Emit a critical-level log message."""
        self._wrapped_logger.critical(message, *args, **kwargs)

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Emit an error log that includes exception context."""
        self._wrapped_logger.exception(message, *args, **kwargs)

    def set_level(self, level: str) -> None:
        """Adjust the active log level at runtime.

        Args:
            level: Textual log level such as ``"INFO"`` or ``"DEBUG"``.
        """
        level_map = {
            "DEBUG": LogLevel.DEBUG.value,
            "INFO": LogLevel.INFO.value,
            "WARNING": LogLevel.WARNING.value,
            "ERROR": LogLevel.ERROR.value,
            "CRITICAL": LogLevel.CRITICAL.value,
        }
        if hasattr(self._wrapped_logger, "setLevel"):
            self._wrapped_logger.setLevel(level_map.get(level.upper(), LogLevel.INFO.value))

    def get_level(self) -> str:
        """Return the current effective log level."

        Returns:
            str: Log level name such as ``"INFO"``.
        """
        if hasattr(self._wrapped_logger, "level"):
            level = int(self._wrapped_logger.level)
            level_names = {
                LogLevel.DEBUG.value: "DEBUG",
                LogLevel.INFO.value: "INFO",
                LogLevel.WARNING.value: "WARNING",
                LogLevel.ERROR.value: "ERROR",
                LogLevel.CRITICAL.value: "CRITICAL",
            }
            return level_names.get(level, "INFO")
        return "INFO"

    def add_context(self, **context: Any) -> None:
        """Attach contextual data to subsequent log records."""
        # コンテキストの実装は既存のロガーに依存
        if hasattr(self._wrapped_logger, "add_context"):
            self._wrapped_logger.add_context(**context)

    def clear_context(self) -> None:
        """Remove contextual data previously applied to the logger."""
        if hasattr(self._wrapped_logger, "clear_context"):
            self._wrapped_logger.clear_context()
