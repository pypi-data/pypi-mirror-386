"""Tests.unit.mcp_servers.tools.test_quality_metadata_no_line_width
Where: Automated test module.
What: Ensure quality metadata tools do not expose line-width aspects or codes.
Why: Aligns with removal of line-width warnings and wrapping.
"""

from __future__ import annotations

from mcp_servers.noveler.tools.quality_metadata_tools import (
    GetQualitySchemaTool,
    ListQualityPresetsTool,
)


def test_list_quality_presets_has_no_line_width_thresholds() -> None:
    tool = ListQualityPresetsTool()
    res = tool.execute(type("Req", (), {"episode_number": 1})())  # minimal dummy request
    presets = res.issues[0].details  # type: ignore[index]
    narou = presets["narou"]
    assert "max_line_width_warn" not in narou
    assert "max_line_width_critical" not in narou


def test_get_quality_schema_excludes_line_width_items() -> None:
    tool = GetQualitySchemaTool()
    res = tool.execute(type("Req", (), {"episode_number": 1})())
    payload = res.issues[0].details  # type: ignore[index]
    aspects = payload["aspects"]
    reason_codes = payload["reason_codes"]
    assert "line_width" not in aspects
    assert "LINE_WIDTH_OVERFLOW" not in reason_codes

