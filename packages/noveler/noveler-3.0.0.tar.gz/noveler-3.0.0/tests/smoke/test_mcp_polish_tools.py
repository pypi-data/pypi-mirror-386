# File: tests/smoke/test_mcp_polish_tools.py
# Purpose: Smoke tests for MCP polish/apply/restore/write/artifacts tools
# Context: Verify basic functionality of manuscript refinement and management tools

"""Smoke tests for MCP polish and manuscript management tools."""

import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from mcp_servers.noveler.tools import (
    polish_manuscript_tool,
    polish_manuscript_apply_tool,
    restore_manuscript_from_artifact_tool,
    write_file_tool,
    fetch_artifact_tool,
    list_artifacts_tool
)
from mcp_servers.noveler.domain.entities.mcp_tool_base import ToolRequest


class TestPolishToolsSmoke:
    """Smoke tests for polish manuscript tools."""

    @pytest.mark.smoke
    def test_polish_manuscript_tool_basic(self, tmp_path):
        """Test basic polish manuscript functionality."""
        # Setup
        manuscript_file = tmp_path / "60_作業ファイル" / "EP001_step12.md"
        manuscript_file.parent.mkdir(parents=True)
        manuscript_file.write_text("# Test Episode\n\nSample content for testing.")

        request = ToolRequest(
            episode_number=1,
            additional_params={
                "project_name": "test_project",
                "dry_run": True,
                "stages": ["stage2"]
            }
        )

        # Mock the underlying service
        with patch.object(polish_manuscript_tool, 'get_polish_service') as mock_service:
            mock_service.return_value.polish_manuscript.return_value = {
                "status": "success",
                "stages_completed": ["stage2"],
                "dry_run": True
            }

            # Execute
            result = polish_manuscript_tool.execute(request)

            # Assert
            assert result is not None
            assert "status" in result
            assert result["status"] == "success"

    @pytest.mark.smoke
    def test_polish_apply_tool_basic(self, tmp_path):
        """Test basic polish apply functionality."""
        request = ToolRequest(
            episode_number=1,
            additional_params={
                "project_name": "test_project",
                "dry_run": True,
                "save_report": False
            }
        )

        with patch.object(polish_manuscript_apply_tool, 'get_polish_service') as mock_service:
            mock_service.return_value.polish_apply.return_value = {
                "status": "success",
                "applied": False,
                "reason": "dry_run enabled"
            }

            result = polish_manuscript_apply_tool.execute(request)
            assert result is not None
            assert result["status"] == "success"
            assert result["applied"] is False


class TestManagementToolsSmoke:
    """Smoke tests for manuscript management tools."""

    @pytest.mark.smoke
    def test_restore_manuscript_tool_basic(self, tmp_path):
        """Test basic restore manuscript functionality."""
        request = ToolRequest(
            episode_number=1,
            additional_params={
                "artifact_id": "artifact:test123456",
                "project_name": "test_project",
                "dry_run": True
            }
        )

        with patch.object(restore_manuscript_from_artifact_tool, 'get_restore_service') as mock_service:
            mock_service.return_value.restore_from_artifact.return_value = {
                "status": "success",
                "restored": False,
                "reason": "dry_run enabled"
            }

            result = restore_manuscript_from_artifact_tool.execute(request)
            assert result is not None
            assert result["status"] == "success"

    @pytest.mark.smoke
    def test_write_file_tool_basic(self, tmp_path):
        """Test basic file writing functionality."""
        test_file = tmp_path / "test_output.txt"

        request = ToolRequest(
            additional_params={
                "relative_path": "test_output.txt",
                "content": "Test content",
                "project_root": str(tmp_path)
            }
        )

        result = write_file_tool.execute(request)

        assert result is not None
        assert "status" in result
        assert test_file.exists()
        assert test_file.read_text() == "Test content"


class TestArtifactToolsSmoke:
    """Smoke tests for artifact management tools."""

    @pytest.mark.smoke
    def test_fetch_artifact_tool_basic(self, tmp_path):
        """Test basic artifact fetching functionality."""
        # Setup artifact directory
        artifacts_dir = tmp_path / ".noveler" / "artifacts"
        artifacts_dir.mkdir(parents=True)

        # Create a test artifact
        artifact_file = artifacts_dir / "test123456.json"
        artifact_data = {
            "id": "artifact:test123456",
            "content": "Test artifact content",
            "metadata": {"version": 1}
        }
        artifact_file.write_text(json.dumps(artifact_data))

        request = ToolRequest(
            additional_params={
                "artifact_id": "artifact:test123456",
                "project_root": str(tmp_path)
            }
        )

        with patch.object(fetch_artifact_tool, 'get_artifact_service') as mock_service:
            mock_service.return_value.fetch_artifact.return_value = artifact_data

            result = fetch_artifact_tool.execute(request)
            assert result is not None
            assert "content" in result

    @pytest.mark.smoke
    def test_list_artifacts_tool_basic(self, tmp_path):
        """Test basic artifact listing functionality."""
        request = ToolRequest(
            additional_params={
                "project_root": str(tmp_path)
            }
        )

        with patch.object(list_artifacts_tool, 'get_artifact_service') as mock_service:
            mock_service.return_value.list_artifacts.return_value = {
                "artifacts": [
                    {"id": "artifact:test1", "created": "2025-01-01"},
                    {"id": "artifact:test2", "created": "2025-01-02"}
                ],
                "total": 2
            }

            result = list_artifacts_tool.execute(request)
            assert result is not None
            assert "artifacts" in result
            assert len(result["artifacts"]) == 2


@pytest.mark.smoke
class TestIntegrationSmoke:
    """Integration smoke tests for polish workflow."""

    def test_polish_workflow_end_to_end(self, tmp_path):
        """Test complete polish workflow from start to finish."""
        # Setup
        manuscript_file = tmp_path / "60_作業ファイル" / "EP001_step12.md"
        manuscript_file.parent.mkdir(parents=True)
        manuscript_file.write_text("# Episode 1\n\nOriginal content.")

        # Step 1: Polish with dry_run
        polish_request = ToolRequest(
            episode_number=1,
            additional_params={
                "project_name": "test_project",
                "dry_run": True
            }
        )

        with patch.object(polish_manuscript_tool, 'get_polish_service') as mock_service:
            mock_service.return_value.polish_manuscript.return_value = {
                "status": "success",
                "artifact_id": "artifact:polish123"
            }

            polish_result = polish_manuscript_tool.execute(polish_request)
            assert polish_result["status"] == "success"

        # Step 2: Apply polish
        apply_request = ToolRequest(
            episode_number=1,
            additional_params={
                "project_name": "test_project",
                "dry_run": False
            }
        )

        with patch.object(polish_manuscript_apply_tool, 'get_polish_service') as mock_service:
            mock_service.return_value.polish_apply.return_value = {
                "status": "success",
                "applied": True
            }

            apply_result = polish_manuscript_apply_tool.execute(apply_request)
            assert apply_result["applied"] is True