# File: tests/unit/mcp_servers/test_tool_registry.py
# Purpose: Verify that the tool registry registers utility tools on a server.
# Context: Uses a minimal dummy server to avoid MCP runtime dependency.

from typing import Any, Callable

from mcp_servers.noveler.server.tool_registry import register_utility_tools


class DummyServer:
    def __init__(self) -> None:
        self._tools: dict[str, dict[str, Any]] = {}

    def tool(self, name: str, description: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._tools[name] = {"func": func, "description": description}
            return func

        return decorator


class DummyCtx:
    def __init__(self) -> None:
        class _Conv:
            def convert(self, payload: dict[str, Any]) -> dict[str, Any]:
                return {"success": True, "command": payload.get("command", "dummy")}

        self.converter = _Conv()

        class _Log:
            def exception(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover
                pass

        self.logger = _Log()
        from pathlib import Path

        self.output_dir = Path.cwd()

    def _format_json_result(self, result: dict[str, Any]) -> str:  # noqa: D401
        return f"成功: {result.get('success')}\nコマンド: {result.get('command')}"


def test_register_utility_tools_adds_expected_tools() -> None:
    server = DummyServer()
    ctx = DummyCtx()

    register_utility_tools(server, ctx)

    assert "convert_cli_to_json" in server._tools
    assert "validate_json_response" in server._tools
    assert "get_file_reference_info" in server._tools

