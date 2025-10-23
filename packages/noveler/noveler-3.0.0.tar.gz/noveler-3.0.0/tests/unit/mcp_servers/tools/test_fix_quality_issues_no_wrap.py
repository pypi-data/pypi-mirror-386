"""Tests.unit.mcp_servers.tools.test_fix_quality_issues_no_wrap
Where: Automated test module.
What: Ensure fix_quality_issues has no line-wrap controls and does not wrap lines.
Why: TDD for policy removing forced wrap from all subcommands.
"""

from __future__ import annotations

from pathlib import Path

from mcp_servers.noveler.domain.entities.mcp_tool_base import ToolRequest
from mcp_servers.noveler.tools.fix_quality_issues_tool import FixQualityIssuesTool


def test_schema_has_no_line_wrap_controls() -> None:
    tool = FixQualityIssuesTool()
    schema = tool.get_input_schema()
    props = set(schema["properties"].keys())
    assert "enable_line_wrap" not in props
    assert "max_line_width" not in props


def test_execute_does_not_insert_line_breaks(tmp_path: Path) -> None:
    # Prepare a file with an overlong single line
    p = tmp_path / "long.txt"
    long_line = "あ" * 300
    p.write_text(long_line, encoding="utf-8")

    tool = FixQualityIssuesTool()
    # Restrict to line-width related fixes only (should result in no changes now)
    # Write changes to output to inspect final content
    out = tmp_path / "out.txt"
    req = ToolRequest(
        episode_number=1,
        additional_params={
            "file_path": str(p),
            "reason_codes": ["LINE_WIDTH_OVERFLOW"],
            "dry_run": False,
            "output_path": str(out),
            "include_diff": True,
        },
    )
    resp = tool.execute(req)
    assert resp.success is True
    # Even if other safe normalizations apply, no hard line breaks should be inserted
    final = out.read_text(encoding="utf-8")
    assert "\n" not in final
