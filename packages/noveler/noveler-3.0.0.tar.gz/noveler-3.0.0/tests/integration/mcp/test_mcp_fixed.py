#!/usr/bin/env python3
"""Test to verify fallback behavior of MCP entry point.

Standard pattern example using common fixture (mcp_test_project) for MCP integration tests.
For details, see "MCP Pattern" section in tests/README.md.

Background:
    Originally placed in tests/test_mcp_fixed.py, but moved to tests/integration/mcp/
    for clearer test categorization.
"""

from pathlib import Path

import pytest

from noveler.presentation.mcp.server_runtime import execute_novel_command


@pytest.mark.asyncio
async def test_mcp_fixed(mcp_test_project: Path) -> None:
    """Verify that execute_novel_command can be invoked directly.

    Args:
        mcp_test_project: Common fixture (tests/integration/mcp/conftest.py) that
                          automatically constructs temporary project root and manages
                          environment variables/caches

    Assertions:
        - Result is a dictionary
        - Response contains "result" -> "data" -> "status"
        - status equals "success"

    Background:
        This test originally defined mcp_test_project fixture locally, but was
        simplified to use common fixture to reduce code duplication.
        For details, see "MCP Pattern" section in tests/README.md.
    """
    result = await execute_novel_command(
        command="write 1",
        project_root=str(mcp_test_project),
        options={"fresh-start": True},
    )

    # Type check
    assert isinstance(result, dict), (
        f"Expected result to be dict, got {type(result).__name__}"
    )

    # Verify response structure
    data = result.get("result", {}).get("data", {})
    status = data.get("status")

    # Status check
    assert status == "success", (
        f"Expected status='success', got status='{status}'. Full data: {data}"
    )
