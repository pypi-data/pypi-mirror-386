#!/usr/bin/env python3
"""Adapt the domain logger protocol to the unified infrastructure logger."""

from typing import Any

from noveler.domain.interfaces.logger_interface import ILogger
from noveler.infrastructure.logging.unified_logger import get_logger as get_unified_logger


class UnifiedLoggerAdapter:
    """Expose the unified logger through the domain-level `ILogger` protocol."""

    def __init__(self, name: str) -> None:
        """Initialize the adapter with the requested logger name.

        Args:
            name: Logger identifier, typically ``__name__``.
        """
        self._logger = get_unified_logger(name)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug-level message."""
        self._logger.debug(message, extra=kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log an info-level message."""
        self._logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning-level message."""
        self._logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log an error-level message."""
        self._logger.error(message, extra=kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log a critical-level message."""
        self._logger.critical(message, extra=kwargs)


def get_logger(name: str) -> ILogger:
    """Return a logger instance that satisfies the `ILogger` protocol.

    Args:
        name: Logger identifier, typically ``__name__``.

    Returns:
        ILogger: Adapter that routes through the unified logger.
    """
    return UnifiedLoggerAdapter(name)
