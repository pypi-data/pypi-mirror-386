# File: src/noveler/presentation/mcp/adapters/io.py
# Purpose: Thin I/O helpers for presentation-layer MCP adapters (PathService resolution
#          and fallback metadata attachment).
# Context: Avoid duplicating path service resolution patterns and centralise how
#          path fallback events are attached to results.
"""Presentation-layer I/O helpers for MCP adapters.

This module intentionally hides infrastructure specifics behind tiny helpers so
server entrypoints can remain minimal and consistent.
"""

from __future__ import annotations

from typing import Any


def resolve_path_service(project_root: str | None) -> Any | None:
    """Return a PathService instance resolved from the optional project_root.

    This function is defensive: it catches import errors and returns ``None``
    when the path service factory is unavailable.
    """
    try:
        from noveler.infrastructure.factories.path_service_factory import (  # noqa: PLC0415
            create_path_service,
        )
    except Exception:
        return None

    try:
        if isinstance(project_root, str) and project_root:
            try:
                return create_path_service(project_root)
            except Exception:
                return create_path_service()
        return create_path_service()
    except Exception:
        return None


def apply_path_fallback_from_locals(result: dict[str, Any] | Any, ctx_locals: dict[str, Any]) -> dict[str, Any] | Any:
    """Attach path fallback events to the result by scanning local objects.

    The server code sometimes keeps PathService-like instances in local
    variables that expose ``get_and_clear_fallback_events``. This helper scans
    such locals and, if any events are found, attaches them to the payload.
    """
    try:
        fallback_events: list[dict] = []
        for v in list(ctx_locals.values()):
            if hasattr(v, "get_and_clear_fallback_events"):
                try:
                    ev = v.get_and_clear_fallback_events() or []
                    if ev:
                        fallback_events.extend(ev)
                except Exception:
                    continue
        if isinstance(result, dict) and fallback_events:
            return {**result, "path_fallback_used": True, "path_fallback_events": fallback_events}
    except Exception:
        pass
    return result

