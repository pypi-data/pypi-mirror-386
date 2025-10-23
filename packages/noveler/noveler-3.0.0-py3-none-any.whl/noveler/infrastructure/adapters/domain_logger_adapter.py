#!/usr/bin/env python3
"""Adapt the infrastructure unified logger to the domain `ILogger` contract."""

from noveler.domain.interfaces.logger import ILogger
from noveler.infrastructure.logging.unified_logger import get_logger as get_unified_logger


class DomainLoggerAdapter(ILogger):
    """Expose the unified logger through the domain-facing `ILogger` interface."""

    def __init__(self, name: str = __name__) -> None:
        """Initialize the adapter with the provided logger name.

        Args:
            name: Logger identifier, typically ``__name__``.
        """
        self._unified_logger = get_unified_logger(name)

    def debug(self, message: str, *args, **kwargs) -> None:
        """Log a debug-level message."""
        self._unified_logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs) -> None:
        """Log an info-level message."""
        self._unified_logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> None:
        """Log a warning-level message."""
        self._unified_logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> None:
        """Log an error-level message."""
        self._unified_logger.error(message, *args, **kwargs)

    def exception(self, message: str, *args: object) -> None:
        """Log an error message that includes exception information."""
        formatted_message = message % args if args else message
        self._unified_logger.exception(formatted_message)


# Domain Layer用ファクトリー関数
def get_domain_logger(name: str = __name__) -> ILogger:
    """Return an `ILogger` implementation backed by the unified logger.

    Args:
        name: Logger identifier, typically ``__name__``.

    Returns:
        ILogger: Domain logger abstraction.
    """
    return DomainLoggerAdapter(name)
