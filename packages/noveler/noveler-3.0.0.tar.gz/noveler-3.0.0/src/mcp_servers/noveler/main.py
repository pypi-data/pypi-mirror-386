#!/usr/bin/env python3
# File: src/mcp_servers/noveler/main.py
# Purpose: Thin compatibility wrapper delegating to the presentation-layer MCP
#          server runtime. Keeps legacy import paths stable while the actual
#          implementation resides under noveler.presentation.
"""Legacy entrypoint delegating to the presentation-layer server runtime."""

from __future__ import annotations

from noveler.presentation.mcp import server_runtime as _runtime

# Progressive Check MCP tools (compliance): get_check_tasks, execute_check_step,
# get_check_status, get_check_history

# Re-export common entrypoints used by CLI / tests.
console = _runtime.console
get_console = _runtime.get_console
server = _runtime.server
list_tools = _runtime.list_tools
call_tool = _runtime.call_tool
execute_task_subtask = _runtime.execute_task_subtask
convert_cli_to_json = _runtime.convert_cli_to_json
validate_json_response = _runtime.validate_json_response
wrap_json_text = _runtime.wrap_json_text
apply_path_fallback_from_locals = _runtime.apply_path_fallback_from_locals
resolve_path_service = _runtime.resolve_path_service
execute_novel_command = _runtime.execute_novel_command


# ---- Explicit delegates (statically discoverable) ----

# Enhanced writing delegates
async def execute_enhanced_get_writing_tasks(**kwargs):  # type: ignore[no-untyped-def]
    return await _runtime.execute_enhanced_get_writing_tasks(**kwargs)

async def execute_enhanced_execute_writing_step(**kwargs):  # type: ignore[no-untyped-def]
    return await _runtime.execute_enhanced_execute_writing_step(**kwargs)

async def execute_enhanced_resume_from_partial_failure(**kwargs):  # type: ignore[no-untyped-def]
    return await _runtime.execute_enhanced_resume_from_partial_failure(**kwargs)

# Progressive check delegates
async def execute_get_check_tasks(**kwargs):  # type: ignore[no-untyped-def]
    return await _runtime.execute_get_check_tasks(**kwargs)

async def execute_check_step_command(**kwargs):  # type: ignore[no-untyped-def]
    return await _runtime.execute_check_step_command(**kwargs)

async def execute_get_check_status(**kwargs):  # type: ignore[no-untyped-def]
    return await _runtime.execute_get_check_status(**kwargs)

async def execute_get_check_history(**kwargs):  # type: ignore[no-untyped-def]
    return await _runtime.execute_get_check_history(**kwargs)

async def execute_generate_episode_preview(**kwargs):  # type: ignore[no-untyped-def]
    return await _runtime.execute_generate_episode_preview(**kwargs)


async def _legacy_list_tools_impl() -> list[dict]:
    """Legacy implementation for listing available MCP tools.

    This function delegates to the presentation-layer runtime's list_tools
    to maintain backward compatibility with existing test infrastructure.
    """
    return await _runtime.list_tools()


async def main() -> None:
    """Delegate to the presentation-layer server runtime."""

    await _runtime.main()


def __getattr__(name: str):  # pragma: no cover - passthrough helper
    """Defer attribute access to the presentation-layer runtime module."""

    return getattr(_runtime, name)


__all__ = sorted({
    "console",
    "get_console",
    "server",
    "list_tools",
    "call_tool",
    "execute_task_subtask",
    "convert_cli_to_json",
    "validate_json_response",
    "wrap_json_text",
    "apply_path_fallback_from_locals",
    "resolve_path_service",
    "execute_novel_command",
    # Explicit delegates (discoverable by static tools)
    "execute_enhanced_get_writing_tasks",
    "execute_enhanced_execute_writing_step",
    "execute_enhanced_resume_from_partial_failure",
    "execute_get_check_tasks",
    "execute_check_step_command",
    "execute_get_check_status",
    "execute_get_check_history",
    "execute_generate_episode_preview",
    "_legacy_list_tools_impl",
    "main",
})


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
