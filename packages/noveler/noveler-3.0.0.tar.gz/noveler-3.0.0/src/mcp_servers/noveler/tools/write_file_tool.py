# File: src/mcp_servers/noveler/tools/write_file_tool.py
# Purpose: Provide a simple MCP tool for writing files relative to a project root.
# Context: Used by smoke tests and local MCP workflows that need deterministic file output.

"""MCP tool implementation for writing text files relative to the project root."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from mcp_servers.noveler.domain.entities.mcp_tool_base import (
    MCPToolBase,
    ToolIssue,
    ToolRequest,
    ToolResponse,
)


class WriteFileTool(MCPToolBase):
    """Create or overwrite a text file relative to the project working directory."""

    def __init__(self) -> None:
        super().__init__(
            tool_name="write_file",
            tool_description="プロジェクトルート相対パスで指定されたファイルへテキストを書き込む",
        )

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "relative_path": {
                    "type": "string",
                    "description": "プロジェクトルートからの相対パス",
                },
                "content": {
                    "type": "string",
                    "description": "書き込むテキストコンテンツ",
                },
                "project_root": {
                    "type": "string",
                    "description": "任意指定のプロジェクトルート。省略時はカレントディレクトリ",
                },
            },
            "required": ["relative_path", "content"],
        }

    def execute(self, request: ToolRequest) -> ToolResponse:
        start = time.time()
        self._validate_request(request, require_episode_number=False)
        additional = request.additional_params or {}
        relative_path = additional.get("relative_path")
        content = additional.get("content", "")
        project_root = additional.get("project_root")

        if not isinstance(relative_path, str) or not relative_path.strip():
            raise ValueError("relative_path is required")

        base_dir = Path(project_root).expanduser() if isinstance(project_root, str) else Path.cwd()
        base_dir = base_dir.resolve()
        target_path = (base_dir / relative_path).resolve()
        try:
            target_path.relative_to(base_dir)
        except ValueError:
            raise ValueError("relative_path must stay within the project root") from None

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(str(content), encoding="utf-8")

        issue = ToolIssue(
            type="file_written",
            severity="low",
            message="ファイルを書き込みました",
            file_path=str(target_path),
            details={"bytes_written": len(str(content).encode("utf-8"))},
        )

        response = self._create_response(True, 100.0, [issue], start)
        response.metadata.update(
            {
                "relative_path": relative_path,
                "absolute_path": str(target_path),
            }
        )
        return response


write_file_tool = WriteFileTool()
