#!/usr/bin/env python3
"""A40/A41 Stage1 AutoFix E2E test

Verifies that fix_quality_issues applies safe Stage1 normalization end-to-end
and writes results to file with metadata.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_servers.noveler import main as mcp_mod


def _write_novelerrc(root: Path, indent_enable: bool = False) -> None:
    content = f"""
fix_quality_issues:
  stage1:
    indent:
      enable: {str(bool(indent_enable)).lower()}
    punctuation:
      exclamation_question_fullwidth_space: true
"""
    (root / ".novelerrc.yaml").write_text(content, encoding="utf-8")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_stage1_autofix_end_to_end(tmp_path: Path) -> None:
    # Arrange
    content = "\n".join([
        "え!本当?",            # expect: え！　本当？
        "「OK!」.」。",         # expect: 「OK！」.」 → punctuation remove at EOL only for 」+。 pattern
        "空白 ） 」",           # expect: 空白）」
    ]) + "\n"
    fp = tmp_path / "第001話_Stage1対象.md"
    fp.write_text(content, encoding="utf-8")

    _write_novelerrc(tmp_path, indent_enable=False)

    # Patch path service for config resolution
    with patch("mcp_servers.noveler.tools.fix_quality_issues_tool.create_path_service", lambda: type("PS", (), {"project_root": tmp_path})()):
        res = await mcp_mod.execute_fix_quality_issues(
            {
                "episode_number": 1,
                "project_name": "e2e_stage1",
                "file_path": str(fp),
                "additional_params": {"file_path": str(fp), "dry_run": False},
            },
        )

    assert isinstance(res, dict) and res.get("success"), "fix_quality_issues failed"
    meta = res.get("metadata") or {}
    assert meta.get("applied", 0) > 0
    written = meta.get("written_to")
    assert written, "no output path returned"

    fixed = Path(written).read_text(encoding="utf-8").splitlines()
    assert fixed[0] == "え！　本当？"
    assert " ）" not in fixed[2] and " 」" not in fixed[2]
