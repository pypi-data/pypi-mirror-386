#!/usr/bin/env python3
# File: tests/unit/mcp_servers/tools/test_export_quality_report_tool.py
# Purpose: Validate export_quality_report tool writes report to destination and returns metadata.
# Context: Uses a direct file_path to avoid repository/manuscript dependencies.

from __future__ import annotations

from pathlib import Path

from mcp_servers.noveler.tools.export_quality_report_tool import ExportQualityReportTool
from mcp_servers.noveler.domain.entities.mcp_tool_base import ToolRequest


def test_export_quality_report_writes_json_to_destination(tmp_path: Path) -> None:
    # Prepare a minimal manuscript file content
    content = "これはテスト原稿です。品質チェックのサンプルです。"
    manuscript = tmp_path / "episode_001.md"
    manuscript.write_text(content, encoding="utf-8")

    dest = tmp_path / "reports" / "quality" / "quality_episode001_test.json"

    tool = ExportQualityReportTool()
    request = ToolRequest(
        episode_number=1,
        project_name=str(tmp_path),
        additional_params={
            "file_path": str(manuscript),
            "format": "json",
            "destination": str(dest),
        },
    )

    response = tool.execute(request)

    assert response.success is True
    assert dest.exists() and dest.is_file()
    assert response.metadata.get("output_path") == str(dest)
    assert response.metadata.get("format") == "json"
