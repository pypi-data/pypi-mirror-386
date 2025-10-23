# File: src/noveler/infrastructure/config/debug_flags.py
# Purpose: Centralize debug flag evaluation and precedence for MCP/CLI contexts.
# Context: Replaces scattered checks of DEBUG_MCP / NOVELER_DEBUG / MCP_STRICT_STDOUT.

from __future__ import annotations

import os


def _env_truth(name: str) -> bool:
    val = (os.getenv(name) or "").strip().lower()
    return val in {"1", "true", "on", "yes"}


def is_debug_enabled(context: str | None = None) -> bool:
    """Return whether debug output should be enabled.

    Precedence (highest → lowest):
    - If MCP_STDIO_SAFE=1 (or context=="mcp" and MCP_STRICT_STDOUT=1), disable debug (safety first)
    - NOVELER_DEBUG (explicit, project-wide)
    - DEBUG_MCP (legacy; kept for backwards compatibility)

    Args:
        context: Optional execution context hint (e.g., "mcp").
    """
    # Hard safety for MCP stdio environments
    if context == "mcp":
        # MCP_STDIO_SAFE implies no stderr chatter; also respect strict stdout
        if _env_truth("MCP_STDIO_SAFE") or _env_truth("MCP_STRICT_STDOUT"):
            return False

    # Explicit project-wide debug
    if _env_truth("NOVELER_DEBUG"):
        return True

    # Legacy MCP debug flag
    if _env_truth("DEBUG_MCP"):
        return True

    return False
