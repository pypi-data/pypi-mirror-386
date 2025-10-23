#!/usr/bin/env python3
"""A40/A41 Stage2/3 polish (prompt mode) E2E test

Verifies prompt structure and absence of artifact fetch instructions.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_servers.noveler import main as mcp_mod


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_polish_prompt_mode_generates_prompts(tmp_path: Path) -> None:
    # Arrange: create a minimal manuscript
    manuscript_dir = tmp_path / "temp/test_data/40_原稿"
    manuscript_dir.mkdir(parents=True, exist_ok=True)
    fp = manuscript_dir / "第001話_Prompt対象.md"
    content = "\n".join([
        "# 第001話 テスト原稿",
        "主人公は朝起きて、旅立ちを決意する。",
        "「行ってきます」",
    ]) + "\n"
    fp.write_text(content, encoding="utf-8")

    # Act: call polish_manuscript (prompt only)
    res = await mcp_mod.execute_polish_manuscript(
        {
            "episode_number": 1,
            "project_name": "e2e_polish_prompt",
            "file_path": str(fp),
            "stages": ["stage2", "stage3"],
            "dry_run": True,
            "include_diff": False,
        },
    )

    # Assert: basic structure
    assert isinstance(res, dict) and res.get("success"), "polish_manuscript failed"
    meta = res.get("metadata") or {}
    prompts = meta.get("prompts") or {}
    assert set(prompts.keys()) >= {"stage2", "stage3"}

    # Prompt content assertions (structure and content embedding)
    p2 = str(prompts.get("stage2", ""))
    p3 = str(prompts.get("stage3", ""))
    assert "Content Refiner" in p2
    assert "Reader Experience Designer" in p3
    assert "# Manuscript" in p2 and "```markdown" in p2
    assert "# Manuscript" in p3 and "```markdown" in p3
    # Manuscript content is embedded
    assert "第001話 テスト原稿" in p2 and "第001話 テスト原稿" in p3
    # No artifact fetch instruction in prompt mode (presence check: absence expected)
    assert "fetch_artifact" not in p2 and "fetch_artifact" not in p3
