"""Convenience wrapper tool: polish

A40 Stage2/Stage3 の実行導線を単一ツールで提供。

mode:
- "apply": polish_manuscript_apply を呼び出して LLM実行→適用→レポートまで実行
- "prompt": polish_manuscript を呼び出して プロンプト生成のみ（導線）
"""
from __future__ import annotations

from typing import Any

from mcp_servers.noveler.domain.entities.mcp_tool_base import (
    MCPToolBase,
    ToolRequest,
    ToolResponse,
)
from noveler.infrastructure.logging.unified_logger import get_logger

from .polish_manuscript_tool import PolishManuscriptTool
from .polish_manuscript_apply_tool import PolishManuscriptApplyTool


class PolishTool(MCPToolBase):
    def __init__(self) -> None:
        super().__init__(
            tool_name="polish",
            tool_description="A40 Stage2/3 の実行導線（prompt/applyをモードで選択）",
        )

    def get_input_schema(self) -> dict[str, Any]:
        schema = self._get_common_input_schema()
        schema["properties"].update(
            {
                "file_path": {"type": "string", "description": "対象ファイルパス"},
                "stages": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["stage2", "stage3"]},
                    "default": ["stage2", "stage3"],
                },
                "mode": {
                    "type": "string",
                    "enum": ["apply", "prompt"],
                    "default": "apply",
                    "description": "apply=一気通貫, prompt=プロンプト生成のみ",
                },
                "dry_run": {"type": "boolean", "default": True},
                "save_report": {"type": "boolean", "default": False},
            }
        )
        return schema

    def execute(self, request: ToolRequest) -> ToolResponse:
        logger = get_logger(__name__)
        start_time = __import__("time").time()
        try:
            self._validate_request(request)
            ap = request.additional_params or {}
            mode = str(ap.get("mode", "apply")).lower()

            if mode == "prompt":
                tool = PolishManuscriptTool()
            else:
                tool = PolishManuscriptApplyTool()

            # そのまま委譲
            resp = tool.execute(
                ToolRequest(
                    episode_number=request.episode_number,
                    project_name=request.project_name,
                    additional_params=ap,
                )
            )
            # PathServiceフォールバック伝搬（親ツール側のメタに反映）
            self._apply_fallback_metadata(resp)
            return resp
        except Exception as e:
            return self._create_response(False, 0.0, [], start_time, f"polish error: {e!s}")
