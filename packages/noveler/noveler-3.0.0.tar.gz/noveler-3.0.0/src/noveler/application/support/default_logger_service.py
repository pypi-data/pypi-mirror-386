# File: src/noveler/application/support/default_logger_service.py
# Purpose: Provide a lightweight ILoggerService implementation decoupled from presentation utilities.
# Context: Used by application components when no DI-provided logger is available.
"""Default logger service helpers for the application layer."""

from __future__ import annotations

from typing import Optional

from noveler.domain.interfaces.logger_service_protocol import ILoggerService
from noveler.infrastructure.logging.unified_logger import get_logger


class _DefaultLoggerService(ILoggerService):
    """Default logger backed by the unified logging pipeline."""

    def __init__(self) -> None:
        self._logger = get_logger("noveler.application.default")

    def debug(self, message: str, *args, **kwargs) -> None:
        self._logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs) -> None:
        self._logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> None:
        self._logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> None:
        self._logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs) -> None:
        self._logger.critical(message, *args, **kwargs)


_DEFAULT_LOGGER: Optional[_DefaultLoggerService] = None


def get_default_logger_service() -> ILoggerService:
    """Return a singleton ILoggerService backed by the unified logging pipeline."""

    global _DEFAULT_LOGGER
    if _DEFAULT_LOGGER is None:
        _DEFAULT_LOGGER = _DefaultLoggerService()
    return _DEFAULT_LOGGER

