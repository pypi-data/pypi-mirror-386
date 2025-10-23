"""Tests.unit.presentation.mcp.test_handlers_adapter_write
Where: Automated test module.
What: Thin adapter test for write file.
Why: Guards behaviour as we extract write handler from main.py.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from noveler.presentation.mcp.adapters.handlers import write_file


@pytest.mark.asyncio
async def test_write_file_adapter_runs(tmp_path: Path) -> None:
    target = tmp_path / "sub" / "note.txt"
    res = await write_file({"relative_path": str(target.relative_to(tmp_path)), "content": "hello", "project_root": str(tmp_path)})
    assert res.get("success") is True
    assert target.exists()
    assert target.read_text(encoding="utf-8") == "hello"

