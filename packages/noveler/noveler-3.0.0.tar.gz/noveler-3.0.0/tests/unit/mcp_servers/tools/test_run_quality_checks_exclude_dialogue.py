#!/usr/bin/env python3
# File: tests/unit/mcp_servers/tools/test_run_quality_checks_exclude_dialogue.py
# Purpose: Verify run_quality_checks respects exclude_dialogue_lines for readability.
# Context: Ensures dialogue lines are excluded from sentence-length issues when flag is True.

import pytest
from pathlib import Path

from mcp_servers.noveler.domain.entities.mcp_tool_base import ToolRequest
from mcp_servers.noveler.tools.run_quality_checks_tool import RunQualityChecksTool


@pytest.mark.unit
def test_run_quality_checks_excludes_dialogue_long_sentence(tmp_path: Path) -> None:
    # Create a manuscript with long dialogue across multiple lines
    content = "\n".join([
        "「" + ("長い会話" * 30),  # long opening without closing
        ("さらに続く" * 20) + "」",  # closes on next line
        "地の文 これは短い。",
    ])
    fp = tmp_path / "manuscript.md"
    fp.write_text(content, encoding="utf-8")

    req = ToolRequest(
        episode_number=1,
        additional_params={
            "file_path": str(fp),
            "aspects": ["readability"],
            "exclude_dialogue_lines": True,
        },
    )
    tool = RunQualityChecksTool()
    res = tool.execute(req)
    # No long_sentence expected for dialogue lines when exclusion is enabled
    types = {i.type for i in res.issues}
    assert "long_sentence" not in types


@pytest.mark.unit
def test_run_quality_checks_without_exclusion_detects_long_sentence(tmp_path: Path) -> None:
    content = "\n".join([
        "「" + ("長い会話" * 30),
        ("さらに続く" * 20) + "」",
        "地の文 これは短い。",
    ])
    fp = tmp_path / "manuscript.md"
    fp.write_text(content, encoding="utf-8")

    req = ToolRequest(
        episode_number=1,
        additional_params={
            "file_path": str(fp),
            "aspects": ["readability"],
            # exclude_dialogue_lines omitted (False)
        },
    )
    tool = RunQualityChecksTool()
    res = tool.execute(req)
    types = {i.type for i in res.issues}
    # Depending on thresholds, at least one long_sentence should be present without exclusion
    assert "long_sentence" in types
