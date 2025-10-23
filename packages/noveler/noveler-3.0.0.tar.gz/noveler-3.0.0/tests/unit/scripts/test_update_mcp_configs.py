# File: tests/unit/scripts/test_update_mcp_configs.py
# Purpose: Test environment detection and SSOT config generation for MCP servers
# Context: Validates that both dev and production configs are correctly generated

"""Tests for scripts/setup/update_mcp_configs.py (SSOT for MCP configuration).

Ensures that:
- Environment detection correctly identifies dev vs production deployments.
- MCP entry generation produces correct paths and PYTHONPATH for both environments.
- Configuration is consistent across different calling contexts (build.py, setup scripts, etc).
"""

from __future__ import annotations

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parents[3] / "scripts" / "setup"))

from update_mcp_configs import _detect_environment, ensure_mcp_server_entry


class TestDetectEnvironment:
    """Test environment auto-detection logic."""

    def test_development_with_src_only(self, tmp_path: Path) -> None:
        """When src/ exists (cloned repo), should detect development."""
        src = tmp_path / "src"
        src.mkdir()

        assert _detect_environment(tmp_path) == "development"

    def test_production_with_dist_only(self, tmp_path: Path) -> None:
        """When src/ is missing and dist/ exists (after make build), should detect production."""
        dist = tmp_path / "dist"
        dist.mkdir()

        assert _detect_environment(tmp_path) == "production"

    def test_development_with_both_src_and_dist(self, tmp_path: Path) -> None:
        """When both src/ and dist/ exist (after make build in cloned repo), default to development."""
        (tmp_path / "src").mkdir()
        (tmp_path / "dist").mkdir()

        assert _detect_environment(tmp_path) == "development"

    def test_development_with_neither_src_nor_dist(self, tmp_path: Path) -> None:
        """When neither src/ nor dist/ exist (unusual state), default to development."""
        assert _detect_environment(tmp_path) == "development"


class TestEnsureMcpServerEntry:
    """Test MCP server entry generation for both environments."""

    def test_development_entry(self, tmp_path: Path) -> None:
        """Development environment should point to src/mcp_servers/noveler/main.py."""
        src = tmp_path / "src"
        src.mkdir()

        entry = ensure_mcp_server_entry(
            tmp_path,
            name="Test MCP",
            description="Test Description",
            env="development"
        )

        expected_main = str(tmp_path / "src" / "mcp_servers" / "noveler" / "main.py")
        assert entry["args"][1] == expected_main
        assert "PYTHONPATH" in entry["env"]
        assert str(tmp_path / "src") in entry["env"]["PYTHONPATH"]
        assert entry["type"] == "stdio"
        assert entry["command"] == "python"
        assert entry["name"] == "Test MCP"
        assert entry["description"] == "Test Description"

    def test_production_entry(self, tmp_path: Path) -> None:
        """Production environment should point to dist/mcp_servers/noveler/main.py.

        Production defaults to sys.executable for reliability in dist-only environments.
        """
        dist = tmp_path / "dist"
        dist.mkdir()

        entry = ensure_mcp_server_entry(
            tmp_path,
            name="Test MCP Prod",
            description="Test Prod Description",
            env="production"
        )

        expected_main = str(tmp_path / "dist" / "mcp_servers" / "noveler" / "main.py")
        assert entry["args"][1] == expected_main
        assert "PYTHONPATH" in entry["env"]
        assert str(tmp_path / "dist") in entry["env"]["PYTHONPATH"]
        assert entry["type"] == "stdio"
        # Production defaults to sys.executable for reliability (not "python")
        assert entry["command"] == sys.executable
        assert entry["name"] == "Test MCP Prod"
        assert entry["description"] == "Test Prod Description"

    def test_auto_detect_development(self, tmp_path: Path) -> None:
        """Without explicit env, should auto-detect development when src/ exists."""
        (tmp_path / "src").mkdir()

        entry = ensure_mcp_server_entry(tmp_path, "", "")

        expected_main = str(tmp_path / "src" / "mcp_servers" / "noveler" / "main.py")
        assert entry["args"][1] == expected_main

    def test_auto_detect_production(self, tmp_path: Path) -> None:
        """Without explicit env, should auto-detect production when dist-only."""
        (tmp_path / "dist").mkdir()

        entry = ensure_mcp_server_entry(tmp_path, "", "")

        expected_main = str(tmp_path / "dist" / "mcp_servers" / "noveler" / "main.py")
        assert entry["args"][1] == expected_main

    def test_default_name_and_description(self, tmp_path: Path) -> None:
        """Should use defaults when name/description are empty strings."""
        (tmp_path / "src").mkdir()

        entry = ensure_mcp_server_entry(tmp_path, "", "")

        assert entry["name"] == "Noveler MCP"
        assert entry["description"] == "Noveler MCP server (writing/quality tools)"

    def test_pythonpath_ordering_dev(self, tmp_path: Path) -> None:
        """Development PYTHONPATH should include project_root first, then src/."""
        (tmp_path / "src").mkdir()

        entry = ensure_mcp_server_entry(tmp_path, "", "", env="development")

        pythonpath = entry["env"]["PYTHONPATH"]
        paths = pythonpath.split(";" if ";" in pythonpath else ":")

        # First element should be project_root, second should be src
        assert str(tmp_path) in paths[0]
        assert "src" in paths[1]

    def test_pythonpath_ordering_prod(self, tmp_path: Path) -> None:
        """Production PYTHONPATH should include dist/ first, then project_root."""
        (tmp_path / "dist").mkdir()

        entry = ensure_mcp_server_entry(tmp_path, "", "", env="production")

        pythonpath = entry["env"]["PYTHONPATH"]
        paths = pythonpath.split(";" if ";" in pythonpath else ":")

        # First element should be dist, second should be project_root
        assert "dist" in paths[0]
        assert str(tmp_path) in paths[1]

    def test_required_env_vars(self, tmp_path: Path) -> None:
        """Should include all required environment variables."""
        (tmp_path / "src").mkdir()

        entry = ensure_mcp_server_entry(tmp_path, "", "")

        assert entry["env"]["PYTHONUNBUFFERED"] == "1"
        assert entry["env"]["NOVEL_PRODUCTION_MODE"] == "1"
        assert entry["env"]["MCP_STDIO_SAFE"] == "1"

    def test_cwd_is_project_root(self, tmp_path: Path) -> None:
        """CWD should always be project_root."""
        (tmp_path / "src").mkdir()

        entry = ensure_mcp_server_entry(tmp_path, "", "")

        assert entry["cwd"] == str(tmp_path)
