# File: src/noveler/presentation/mcp/bootstrap.py
# Purpose: Composition root (presentation layer) for the Noveler MCP server.
# Context: Acts as a thin facade that delegates execution to the current
#          server implementation while providing a stable import path under
#          noveler/presentation for future refactors.
"""Presentation-layer bootstrap for the Noveler MCP server.

This module intentionally contains no business logic. It delegates execution to
the existing server runtime while giving the codebase a canonical composition
root under `noveler.presentation.mcp` in line with DDD/clean architecture.
"""

from __future__ import annotations

import asyncio
from typing import Awaitable, Callable


def _get_legacy_main() -> Callable[[], Awaitable[None]]:
    """Return the legacy async main function of the MCP server.

    Kept as an indirection so future migrations can replace the import target
    without touching callers.
    """
    from mcp_servers.noveler import main as legacy  # lazy import  # noqa: PLC0415

    return legacy.main  # type: ignore[return-value]


async def main() -> None:
    """Run the MCP server (delegates to the legacy implementation)."""
    legacy_main = _get_legacy_main()
    await legacy_main()


if __name__ == "__main__":
    asyncio.run(main())

