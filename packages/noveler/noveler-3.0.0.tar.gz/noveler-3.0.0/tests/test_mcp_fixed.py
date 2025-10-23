#!/usr/bin/env python3
"""MCPエントリポイントのフォールバック動作を検証するテスト"""

import pytest
from pathlib import Path

from noveler.presentation.mcp.server_runtime import execute_novel_command


@pytest.mark.asyncio
async def test_mcp_fixed() -> None:
    """execute_novel_command が直接呼び出せることを検証"""
    result = await execute_novel_command(
        command="write 1",
        project_root=str(Path.cwd()),
        options={"fresh-start": True},
    )

    assert isinstance(result, dict)
    data = result.get("result", {}).get("data", {})
    assert data.get("status") == "success"
