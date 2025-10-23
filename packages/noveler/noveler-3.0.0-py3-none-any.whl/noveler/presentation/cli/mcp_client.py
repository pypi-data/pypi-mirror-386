"""Lightweight synchronous MCP client used by the CLI facade."""

from __future__ import annotations

import asyncio
import importlib
from typing import Any, Callable


class MCPClientError(RuntimeError):
    """Raised when an MCP tool invocation fails in the CLI wrapper."""


class MCPClient:
    """Provide synchronous access to presentation-layer MCP tools."""

    def __init__(self) -> None:
        self._runtime = importlib.import_module("noveler.presentation.mcp.server_runtime")
        self._dispatcher = importlib.import_module("noveler.presentation.mcp.dispatcher")
        self._apply_path_fallback: Callable[[Any, dict[str, Any]], Any] = getattr(
            self._runtime, "apply_path_fallback_from_locals"
        )

    async def call_tool_async(self, name: str, payload: dict[str, Any]) -> Any:
        """Execute an MCP tool asynchronously and return its raw result."""

        if name == "noveler":
            options = payload.get("options") or {}
            return await self._runtime.execute_novel_command(
                payload.get("command", ""), payload.get("project_root"), options
            )

        handler = self._dispatcher.get_handler(name)
        if handler is None:
            raise MCPClientError(f"Unsupported MCP tool: {name}")

        result = await self._dispatcher.dispatch(name, payload)
        if result is None:
            raise MCPClientError(f"MCP tool '{name}' returned no result")
        return self._apply_path_fallback(result, {"arguments": payload})

    def call_tool(self, name: str, payload: dict[str, Any]) -> Any:
        """Synchronously invoke an MCP tool and return the result."""

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.call_tool_async(name, payload))

        if loop.is_running():
            new_loop = asyncio.new_event_loop()
            try:
                return new_loop.run_until_complete(self.call_tool_async(name, payload))
            finally:
                new_loop.close()

        return loop.run_until_complete(self.call_tool_async(name, payload))
