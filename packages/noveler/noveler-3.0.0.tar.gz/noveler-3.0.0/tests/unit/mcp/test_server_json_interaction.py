#!/usr/bin/env python3
# File: tests/unit/mcp/test_server_json_interaction.py
# Purpose: Validate basic JSON serialization helpers for MCP server tools.
# Context: Ensures Tool dataclasses can be converted to JSON dictionaries
#          and keep B20-friendly compactness (no None fields).

from __future__ import annotations

import json

from mcp import Tool
from mcp.server import server_tool_to_dict


def test_tool_to_dict_serialization() -> None:
    """Tool dataclass converts to JSON-serializable dict."""
    tool = Tool(
        name="convert_cli_to_json",
        description="CLI実行結果をJSONに変換",
        inputSchema={"type": "object", "properties": {"cli_result": {"type": "object"}}},
    )

    data = server_tool_to_dict(tool)

    # Required keys exist and are serializable
    assert data["name"] == "convert_cli_to_json"
    assert data["description"].startswith("CLI実行結果")
    assert isinstance(data["inputSchema"], dict)

    # No None values should remain in the serialized output
    assert all(v is not None for v in data.values())

    # JSON dump must succeed for transmission to clients
    dumped = json.dumps(data, ensure_ascii=False)
    assert "convert_cli_to_json" in dumped
