# File: src/mcp_servers/noveler/core/format_utils.py
# Purpose: Shared formatting helpers for MCP server responses. Provides
#          small, dependency-light utilities to render JSON conversion results
#          and simple mappings as human-readable text.
# Context: Imported by MCP server implementations (JSON/async variants). No
#          side effects at import time. Keep functions small and testable.

from __future__ import annotations

from typing import Any


def format_json_result(result: dict[str, Any]) -> str:
    """Format a JSON conversion payload for textual display.

    Purpose:
        Produce a compact, readable textual representation of a JSON
        conversion result.

    Args:
        result (dict[str, Any]): Converted payload returned by the JSON
            converter.

    Returns:
        str: Multiline summary of the conversion outcome.

    Side Effects:
        None.
    """
    lines: list[str] = []
    lines.append(f"成功: {result.get('success', 'N/A')}")
    lines.append(f"コマンド: {result.get('command', 'N/A')}")

    if "outputs" in result:
        outputs = result["outputs"]
        lines.append(f"出力ファイル数: {outputs.get('total_files', 0)}")
        lines.append(f"総サイズ: {outputs.get('total_size_bytes', 0)} bytes")

    if "error" in result:
        error = result["error"]
        lines.append(f"エラーコード: {error.get('code', 'N/A')}")
        lines.append(f"エラーメッセージ: {error.get('message', 'N/A')}")

    return "\n".join(lines)


def format_dict(data: dict[str, Any]) -> str:
    """Render a dictionary as a simple key/value newline list.

    Purpose:
        Create a compact textual representation for simple mapping data.

    Args:
        data (dict[str, Any]): Mapping to render.

    Returns:
        str: Lines joined by newlines as key: value pairs.

    Side Effects:
        None.
    """
    return "\n".join(f"{k}: {v}" for k, v in data.items())

