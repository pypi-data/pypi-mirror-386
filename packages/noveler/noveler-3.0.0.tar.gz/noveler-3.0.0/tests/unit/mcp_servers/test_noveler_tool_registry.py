# File: tests/unit/mcp_servers/test_noveler_tool_registry.py
# Purpose: Ensure individual Noveler tools are registered via the registry.

from typing import Any, Callable

from mcp_servers.noveler.server.noveler_tool_registry import (
    register_individual_noveler_tools,
)


class DummyServer:
    def __init__(self) -> None:
        self._tools: dict[str, dict[str, Any]] = {}

    def tool(self, name: str, description: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._tools[name] = {"func": func, "description": description}
            return func

        return decorator


class DummyCtx:
    def _execute_novel_command(self, command: str, options: dict[str, Any], project_root: str | None = None) -> str:
        return f"executed: {command}"

    def _handle_write_via_bus_sync(self, episode_number: int) -> str:
        return f"bus: write {episode_number}"


def test_registers_primary_noveler_tools() -> None:
    server = DummyServer()
    ctx = DummyCtx()
    register_individual_noveler_tools(server, ctx)
    for name in ("noveler_write", "noveler_check", "noveler_plot", "noveler_complete"):
        assert name in server._tools

