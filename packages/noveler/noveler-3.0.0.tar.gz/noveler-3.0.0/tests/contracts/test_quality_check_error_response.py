#!/usr/bin/env python3
"""Contract tests for quality check error handling (B20 Phase 4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.mcp_servers.noveler.domain.entities.mcp_tool_base import ToolRequest
from src.mcp_servers.noveler.tools.run_quality_checks_tool import RunQualityChecksTool


@pytest.mark.contract
class TestQualityCheckErrorContract:
    """B20 Contract: Proper error responses for missing files."""

    def test_file_not_found_returns_failure(self, tmp_path):
        """success=False when manuscript file not found."""
        tool = RunQualityChecksTool()
        missing_file = tmp_path / "nonexistent.md"

        request = ToolRequest(
            episode_number=999,
            project_name=None,
            additional_params={"file_path": str(missing_file)},
        )

        response = tool.execute(request)

        assert response.success is False
        assert response.score == 0.0
        assert response.metadata.get("error_message") is not None
        assert len(response.metadata.get("error_message", "")) > 0

    def test_error_message_mentions_a38(self, tmp_path):
        """Error message should guide user to A38 pattern."""
        tool = RunQualityChecksTool()
        request = ToolRequest(
            episode_number=1,
            additional_params={"file_path": str(tmp_path / "missing.md")},
        )

        response = tool.execute(request)

        assert response.success is False
        error_msg = response.metadata.get("error_message", "")
        assert ("第001話" in error_msg) or ("A38" in error_msg)

    def test_no_false_issues_on_error(self, tmp_path):
        """Failure response must not return false quality issues."""
        tool = RunQualityChecksTool()
        request = ToolRequest(
            episode_number=1,
            additional_params={"file_path": str(tmp_path / "missing.md")},
        )

        response = tool.execute(request)

        assert response.success is False
        quality_issues = [i for i in response.issues if i.type != "summary_metrics"]
        assert len(quality_issues) == 0
