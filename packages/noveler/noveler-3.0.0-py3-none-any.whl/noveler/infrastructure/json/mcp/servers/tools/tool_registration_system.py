"""Shared abstractions that coordinate MCP tool registration."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from mcp.server.fastmcp import FastMCP


class ToolRegistrationMixin(ABC):
    """Mixin that exposes helpers for registering FastMCP tools."""

    def __init__(self, server: FastMCP) -> None:
        """Initialise the mixin with the FastMCP server instance."""
        self.server = server

    @abstractmethod
    def register_tools(self) -> None:
        """Register tools with FastMCP. Must be implemented by subclasses."""

    def _register_tool(
        self,
        name: str,
        description: str,
        schema: dict[str, Any],
        handler: Callable,
    ) -> None:
        """Register a tool handler with the FastMCP server."""
        @self.server.tool(name, description)
        async def tool_wrapper(arguments: dict[str, Any]) -> dict[str, Any]:
            try:
                return await handler(arguments)
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__
                }

        # スキーマ設定
        if schema:
            tool_wrapper.__annotations__["arguments"] = schema

    def _format_tool_result(self, result: Any, success: bool = True) -> dict[str, Any]:
        """Normalise tool execution results into a common structure."""
        if isinstance(result, dict) and "success" in result:
            return result

        return {
            "success": success,
            "result": result,
            "timestamp": self._get_current_timestamp()
        }

    def _get_current_timestamp(self) -> str:
        """Return the current timestamp in ISO 8601 format."""
        from noveler.domain.value_objects.project_time import project_now
        return project_now().datetime.isoformat()


class CoreToolsRegistration(ToolRegistrationMixin):
    """Register common utility tools exposed via FastMCP."""

    def register_tools(self) -> None:
        """Register the set of core conversion and validation tools."""
        self._register_cli_conversion_tool()
        self._register_validation_tool()
        self._register_file_reference_tool()

    def _register_cli_conversion_tool(self) -> None:
        """Register the CLI conversion wrapper tool."""
        @self.server.tool("convert_cli_to_json", "CLI実行結果をJSON形式に変換し、95%トークン削減と参照アーキテクチャを適用")
        async def convert_cli_to_json(cli_result: dict[str, Any]) -> dict[str, Any]:
            """Convert CLI output into the JSON structure used by clients."""
            try:
                return await self._handle_cli_conversion(cli_result)
            except Exception:
                return self._format_tool_result(None, False)

    def _register_validation_tool(self) -> None:
        """Register the JSON response validation tool."""
        @self.server.tool("validate_json_response", "JSON レスポンス形式検証")
        async def validate_json_response(json_data: dict[str, Any]) -> dict[str, Any]:
            """Validate that the JSON payload conforms to the expected schema."""
            try:
                return await self._handle_json_validation(json_data)
            except Exception:
                return self._format_tool_result(None, False)

    def _register_file_reference_tool(self) -> None:
        """Register the file reference lookup tool."""
        @self.server.tool("get_file_reference_info", "ファイル参照情報取得")
        async def get_file_reference_info(file_path: str) -> dict[str, Any]:
            """Return metadata for archived files looked up by FastMCP."""
            try:
                return await self._handle_file_reference(file_path)
            except Exception:
                return self._format_tool_result(None, False)

    async def _handle_cli_conversion(self, cli_result: dict[str, Any]) -> dict[str, Any]:
        """CLI変換ハンドラー（派生クラスで実装）"""
        raise NotImplementedError

    async def _handle_json_validation(self, json_data: dict[str, Any]) -> dict[str, Any]:
        """JSON検証ハンドラー（派生クラスで実装）"""
        raise NotImplementedError

    async def _handle_file_reference(self, file_path: str) -> dict[str, Any]:
        """ファイル参照ハンドラー（派生クラスで実装）"""
        raise NotImplementedError
