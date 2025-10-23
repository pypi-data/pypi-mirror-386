"""Tests.unit.mcp_servers.tools.test_check_rhythm_no_line_width
Where: Automated test module.
What: Verifies line-width warnings are not produced and schema has no line-width knobs.
Why: TDD for removing forced wrap and line-width warnings across all subcommands.
"""

from __future__ import annotations

from mcp_servers.noveler.domain.entities.mcp_tool_base import ToolRequest
from mcp_servers.noveler.tools.check_rhythm_tool import CheckRhythmTool


def test_schema_has_no_line_width_aspect_or_thresholds() -> None:
    tool = CheckRhythmTool()
    schema = tool.get_input_schema()
    aspects_enum = schema["properties"]["check_aspects"]["items"]["enum"]
    assert "line_width" not in aspects_enum
    thresholds_props = set(schema["properties"]["thresholds"]["properties"].keys())
    assert "max_line_width_warn" not in thresholds_props
    assert "max_line_width_critical" not in thresholds_props


def test_execute_reports_no_line_width_issues() -> None:
    tool = CheckRhythmTool()
    long_line = "あ" * 300  # deliberately over any former threshold
    req = ToolRequest(
        episode_number=1,
        additional_params={
            "file_path": None,
            "content": long_line,
            # do not specify aspects: default should not include line_width
        },
    )
    resp = tool.execute(req)
    assert resp.success is True
    # Ensure no issues of type/reason for line width overflow exist
    for issue in resp.issues:
        assert issue.type != "line_width_overflow"
        assert issue.reason_code != "LINE_WIDTH_OVERFLOW"

