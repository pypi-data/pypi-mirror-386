# File: src/noveler/mcp_server.py
# Purpose: Provide a backwards-compatible facade for the legacy noveler.mcp_server import path.
# Context: The MCP server implementation moved to mcp_servers.noveler.main; older integrations
#          still import noveler.mcp_server expecting the original symbols.

"""Compatibility facade for the legacy ``noveler.mcp_server`` module.

Purpose: Delegate attribute access to mcp_servers.noveler.main for backward compatibility.

Context:
    This thin wrapper preserves compatibility with existing tooling after MCP server refactor.
    Explicit aliases document and preserve the old symbol names that callers relied on.

Side Effects:
    None - only re-exports symbols from legacy module.
"""

from __future__ import annotations

from typing import Any

from mcp_servers.noveler import main as _legacy_main

# Legacy aliases preserved for callers that imported these names directly.
execute_polish_manuscript_apply = _legacy_main.execute_polish_manuscript_apply
polish_manuscript_apply = _legacy_main.execute_polish_manuscript_apply


def __getattr__(name: str) -> Any:
    """Delegate attribute access to the legacy MCP server module.

    Purpose: Forward undefined attribute lookups to legacy implementation.

    Args:
        name: Attribute name being accessed.

    Returns:
        Attribute value from _legacy_main module.

    Raises:
        AttributeError: When attribute doesn't exist in legacy module.

    Side Effects:
        None - read-only delegation.
    """

    return getattr(_legacy_main, name)


def __dir__() -> list[str]:
    """Mirror attributes exported by the legacy module for introspection.

    Purpose: Provide complete attribute list for dir() calls.

    Returns:
        Sorted list of available attribute names.

    Side Effects:
        None - read-only operation.
    """

    return sorted(set(dir(_legacy_main)) | {"polish_manuscript_apply"})


__all__ = sorted(set(getattr(_legacy_main, "__all__", ())) | {"polish_manuscript_apply"})
