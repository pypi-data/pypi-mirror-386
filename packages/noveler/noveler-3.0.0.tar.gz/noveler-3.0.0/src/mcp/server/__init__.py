from __future__ import annotations
import asyncio, json, sys
from typing import Any, Callable, Awaitable

import signal, os

# File: src/mcp/server/__init__.py
# Purpose: Minimal JSON-RPC stdio server for MCP tests and local usage.
# Context: Provides lightweight handlers compatible with project tests and
#          B20 JSON principles. Avoid external deps and integrate via
#          decorators exposed from noveler MCP entrypoints.
from dataclasses import asdict, is_dataclass


def _tool_to_dict(tool: object) -> dict[str, object]:
    """Convert a Tool-like object to a JSON-serializable dict.

    Accepts the local dataclass `mcp.Tool` or any object with the same
    attributes (name/description/inputSchema). Unknown attributes are ignored.

    Args:
        tool: Tool-like value to convert.

    Returns:
        dict: Minimal JSON representation without None values.
    """
    if is_dataclass(tool):
        data = asdict(tool)
    else:
        data = {
            "name": getattr(tool, "name", None),
            "description": getattr(tool, "description", None),
            "inputSchema": getattr(tool, "inputSchema", None),
        }
    return {k: v for k, v in data.items() if v is not None}

class Server:
    def __init__(self, name: str) -> None:
        self.name = name
        self._list_tools_handler: Callable[[], Awaitable[list]] | None = None
        self._call_tool_handler: Callable[[str, dict[str, Any]], Awaitable[list]] | None = None
        self._protocol_version: str = os.getenv("MCP_PROTOCOL_VERSION", "2024-11-05")
        self._server_info: dict[str, str] = {
            "name": self.name,
            "version": os.getenv("MCP_SERVER_VERSION", "0.1.0"),
        }
        self._capabilities: dict[str, Any] = {
            "tools": {
                # Advertise support for standard tool listing/calling without
                # relying on boolean flags that violate the MCP schema.
                "listChanged": False,
            },
        }

    def list_tools(self):
        """Decorator to register the async list-tools handler."""
        def deco(fn: Callable[[], Awaitable[list]]):
            self._list_tools_handler = fn
            async def wrapper():
                return await fn()
            return wrapper
        return deco

    def call_tool(self):
        """Decorator to register the async call-tool handler."""
        def deco(fn: Callable[[str, dict[str, Any]], Awaitable[list]]):
            self._call_tool_handler = fn
            async def wrapper(name: str, arguments: dict[str, Any]):
                return await fn(name, arguments)
            return wrapper
        return deco

    def create_initialization_options(self) -> dict[str, Any]:
        """Return initialization options for the MCP server runtime."""
        return {
            "protocolVersion": self._protocol_version,
            "capabilities": {
                key: (value.copy() if isinstance(value, dict) else value)
                for key, value in self._capabilities.items()
            },
        }

    async def run(self, read_stream: Any, write_stream: Any, _init_opts: dict[str, Any]) -> None:
        """Run a minimal JSON-RPC 2.0 loop on stdio.

        Notes:
            - Uses stdin for input (read_stream is unused in this stub).
            - Emits only JSON-RPC frames to stdout (see docs/mcp/stdout_safety.md).
            - Exits immediately after first tools/call to avoid test races.
        """
        try:
            signal.signal(signal.SIGTERM, lambda *_: os._exit(0))
            signal.signal(signal.SIGINT, lambda *_: os._exit(0))
        except Exception:
            # Signals may be unsupported on some platforms
            pass

        async def _readline() -> str:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, sys.stdin.readline)

        while True:
            line = await _readline()
            if not line:
                await asyncio.sleep(0.05)
                continue
            try:
                msg = json.loads(line)
            except Exception:
                # Ignore non-JSON
                continue

            mid = msg.get("id")
            method = msg.get("method")

            # Notifications (no id) are ignored politely
            if mid is None and isinstance(method, str) and method.endswith("initialized"):
                continue

            if method == "initialize":
                params = msg.get("params") or {}
                init_options = self.create_initialization_options()
                requested_protocol = params.get("protocolVersion")
                if isinstance(requested_protocol, str) and requested_protocol.strip():
                    init_options["protocolVersion"] = requested_protocol
                resp = {
                    "jsonrpc": "2.0",
                    "id": mid,
                    "result": {
                        **init_options,
                        "serverInfo": self._server_info.copy(),
                    },
                }
            elif method == "tools/list":
                tools: list[dict[str, Any]] = []
                if self._list_tools_handler is not None:
                    try:
                        raw_tools = await self._list_tools_handler()
                        tools = [_tool_to_dict(t) for t in (raw_tools or [])]
                    except Exception:
                        tools = []
                resp = {"jsonrpc": "2.0", "id": mid, "result": {"tools": tools}}
            elif method == "tools/call":
                name = ((msg.get("params") or {}).get("name"))
                arguments = ((msg.get("params") or {}).get("arguments") or {})
                content = []
                if self._call_tool_handler is not None and isinstance(name, str):
                    try:
                        content = await self._call_tool_handler(name, arguments)
                    except Exception as _e:  # return protocol-shaped error content
                        content = [{"type": "text", "text": json.dumps({"error": str(_e)})}]
                # Normalise TextContent dataclass or dicts
                norm_content: list[dict[str, Any]] = []
                for c in content or []:
                    if is_dataclass(c):
                        norm_content.append(asdict(c))
                    elif isinstance(c, dict):
                        norm_content.append(c)
                    else:
                        norm_content.append({"type": "text", "text": str(c)})

                resp = {
                    "jsonrpc": "2.0",
                    "id": mid,
                    "result": {
                        "content": norm_content,
                    },
                }
                # Print and exit immediately to avoid race in tests
                print(json.dumps(resp, ensure_ascii=False), flush=True)
                os._exit(0)
                return
            else:
                resp = {"jsonrpc": "2.0", "id": mid, "result": {"ok": True}}

            print(json.dumps(resp, ensure_ascii=False), flush=True)

# Helper re-export for tests and utilities
server_tool_to_dict = _tool_to_dict
