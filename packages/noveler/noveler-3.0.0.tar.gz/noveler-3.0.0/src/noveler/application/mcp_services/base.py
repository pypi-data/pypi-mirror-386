# File: src/noveler/application/mcp_services/base.py
# Purpose: Define shared error types and utilities for MCP-facing tool services.
# Context: Used by infrastructure FastMCP registrations to delegate execution
#          to application-layer services with consistent error handling.
"""Shared base classes for MCP tool services."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict

from noveler.infrastructure.logging.unified_logger import get_logger


@dataclass(slots=True)
class ToolServiceError(Exception):
    """Structured error raised when a tool service cannot complete successfully."""

    message: str
    reason: str
    error_type: str = "ToolServiceError"
    hint: str | None = None
    details: Dict[str, Any] | None = field(default=None)

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return self.message


class BaseToolService:
    """Provide shared helpers for executing MCP tool handlers safely."""

    def __init__(self) -> None:
        self._logger = get_logger(self.__class__.__name__)

    async def _invoke(
        self,
        handler: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]],
        payload: Dict[str, Any],
        *,
        reason: str,
        hint: str | None = None,
    ) -> Dict[str, Any]:
        """Execute the given handler and normalise unexpected failures."""

        try:
            result = await handler(payload)
        except ToolServiceError:
            raise
        except Exception as exc:  # pragma: no cover - defensive conversion
            self._logger.exception("Tool handler raised an unexpected exception")
            raise ToolServiceError(
                message=str(exc),
                reason=reason,
                hint=hint,
                error_type=type(exc).__name__,
                details={"payload": self._redact_payload(payload)},
            ) from exc

        if not isinstance(result, dict):
            self._logger.error(
                "Tool handler returned non-dict payload", extra={"handler": handler, "type": type(result)}
            )
            raise ToolServiceError(
                message="Handler returned an invalid response payload.",
                reason="invalid_response",
                hint="Ensure the handler returns a JSON-serialisable mapping.",
                details={"received_type": type(result).__name__},
            )

        return result

    @staticmethod
    def _redact_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Return a shallow copy that avoids logging large content fields verbatim."""

        MAX_PREVIEW = 120
        redacted: Dict[str, Any] = {}
        for key, value in payload.items():
            if isinstance(value, str) and len(value) > MAX_PREVIEW:
                redacted[key] = f"{value[:MAX_PREVIEW]}… (truncated)"
            else:
                redacted[key] = value
        return redacted

