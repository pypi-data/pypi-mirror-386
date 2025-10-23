#!/usr/bin/env python3
# File: tests/unit/domain/services/test_project_initializer_service.py
# Purpose: Unit tests for ProjectInitializerService domain business logic
# Context: Phase 4 Testing - Contract tests for project initialization service
"""Unit tests for ProjectInitializerService.

These tests verify business logic in isolation without I/O operations.
Tests cover: project name validation, title extraction, config generation, directory structure.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from noveler.domain.services.project_initializer_service import (
    DirectoryStructure,
    ProjectConfig,
    ProjectInitializerService,
)


@pytest.fixture
def mock_path_service():
    """Create mock PathService for dependency injection."""
    mock = MagicMock()
    mock.project_root = Path("/tmp/test_projects")
    return mock


@pytest.fixture
def service(mock_path_service):
    """Create ProjectInitializerService instance with mocked dependencies."""
    return ProjectInitializerService()


class TestProjectNameValidation:
    """Test project name validation business rules."""

    @pytest.mark.parametrize(
        "project_name",
        [
            "01_時空の図書館",
            "MyNovel",
            "fantasy-story",
            "project_name",
            "プロジェクト名",
            "12345678901234567890",  # 20 characters
            "a" * 100,  # Maximum length (100 characters)
        ],
    )
    def test_valid_project_names(self, service, project_name):
        """Valid project names should pass validation."""
        is_valid, error_msg = service.validate_project_name(project_name)
        assert is_valid is True
        assert error_msg is None

    @pytest.mark.parametrize(
        "project_name,expected_error",
        [
            ("", "empty"),
            (" ", "empty"),
            ("a" * 101, "length"),  # Too long (> 100 characters)
            ("project/name", "invalid_chars"),  # Slash not allowed
            ("project\\name", "invalid_chars"),  # Backslash not allowed
            ("project<name", "invalid_chars"),  # Angle bracket not allowed
            ("project>name", "invalid_chars"),  # Angle bracket not allowed
            ("project:name", "invalid_chars"),  # Colon not allowed on Windows
            ("project|name", "invalid_chars"),  # Pipe not allowed
            ("project?name", "invalid_chars"),  # Question mark not allowed
            ("project*name", "invalid_chars"),  # Asterisk not allowed
            ("..hidden", "invalid_chars"),  # Double dot not allowed (path traversal risk)
        ],
    )
    def test_invalid_project_names(self, service, project_name, expected_error):
        """Invalid project names should fail validation with appropriate error."""
        is_valid, error_msg = service.validate_project_name(project_name)
        assert is_valid is False
        assert error_msg is not None
        # Check for expected error type (don't check exact message due to encoding issues)
        if expected_error == "empty":
            assert "空" in error_msg
        elif expected_error == "length":
            assert "文字" in error_msg
        elif expected_error == "invalid_chars":
            assert "使用できない" in error_msg or "文字" in error_msg

    def test_validation_strips_whitespace(self, service):
        """Project names should be stripped of leading/trailing whitespace."""
        is_valid, error_msg = service.validate_project_name("  valid_name  ")
        assert is_valid is True
        assert error_msg is None


class TestTitleExtraction:
    """Test title extraction from project names."""

    @pytest.mark.parametrize(
        "project_name,expected_title",
        [
            ("01_時空の図書館", "時空の図書館"),
            ("08_fantasy_story", "fantasy_story"),
            ("12_my-novel", "my-novel"),
            ("999_超長編小説", "超長編小説"),
            ("no_prefix_here", "no_prefix_here"),
            ("plain", "plain"),
            ("01_", ""),  # Edge case: only prefix
            ("_title", "_title"),  # Edge case: underscore without number (no numeric prefix to remove)
        ],
    )
    def test_title_extraction(self, service, project_name, expected_title):
        """Title extraction should remove numeric prefix correctly."""
        title = service.extract_title_from_name(project_name)
        assert title == expected_title

    def test_title_extraction_preserves_internal_numbers(self, service):
        """Internal numbers should be preserved in title."""
        title = service.extract_title_from_name("01_novel_2024_v1")
        assert title == "novel_2024_v1"


class TestConfigGeneration:
    """Test project configuration generation."""

    def test_generate_config_basic(self, service):
        """Config generation should create valid ProjectConfig with defaults."""
        project_name = "01_時空の図書館"
        project_root = Path("/tmp/novels/01_時空の図書館")

        config = service.generate_config(
            project_name=project_name, project_root=project_root
        )

        assert isinstance(config, ProjectConfig)
        assert config.project_name == project_name
        assert config.project_root == project_root
        assert config.title == "時空の図書館"
        assert config.genre == "ファンタジー"  # Default genre
        assert config.status == "planning"  # Default status
        assert config.pen_name == "ペンネーム"  # Default pen name
        assert config.created_date is not None  # Should be set to current date

    def test_generate_config_with_overrides(self, service):
        """Config generation should accept parameter overrides."""
        project_name = "my_novel"
        project_root = Path("/tmp/my_novel")

        config = service.generate_config(
            project_name=project_name,
            project_root=project_root,
            genre="SF",
            pen_name="山田太郎",
        )

        assert config.genre == "SF"
        assert config.pen_name == "山田太郎"
        assert config.status == "planning"  # Default status

    def test_generate_config_created_date_format(self, service):
        """Created date should be in YYYY-MM-DD format."""
        config = service.generate_config(
            project_name="test", project_root=Path("/tmp/test")
        )

        assert config.created_date is not None
        # Verify date format (YYYY-MM-DD)
        import re

        assert re.match(r"^\d{4}-\d{2}-\d{2}$", config.created_date)


class TestDirectoryStructure:
    """Test directory structure generation."""

    def test_directory_structure_immutable(self):
        """DirectoryStructure should be immutable value object."""
        structure = DirectoryStructure.standard()

        # Attempt to modify should raise AttributeError (frozen dataclass)
        with pytest.raises(AttributeError):
            structure.directories.append("new_dir")  # type: ignore

    def test_standard_directory_list(self):
        """Standard directories should match project structure."""
        structure = DirectoryStructure.standard()

        expected_dirs = (
            "10_企画",
            "20_プロット/章別プロット",
            "30_設定集",
            "40_原稿",
            "50_管理資料/執筆記録",
            "90_アーカイブ",
        )

        assert structure.directories == expected_dirs

    def test_directory_structure_iteration(self):
        """DirectoryStructure should be iterable."""
        structure = DirectoryStructure.standard()

        dirs = list(structure.directories)
        assert len(dirs) == 6
        assert "10_企画" in dirs
        assert "40_原稿" in dirs


class TestServiceInitialization:
    """Test service initialization and dependencies."""

    def test_service_is_stateless(self, service):
        """Service should be stateless (no mutable state)."""
        # Call methods multiple times to ensure no state mutation
        service.validate_project_name("project1")
        service.validate_project_name("project2")

        title1 = service.extract_title_from_name("01_title1")
        title2 = service.extract_title_from_name("02_title2")

        assert title1 != title2  # Results independent of previous calls


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_unicode_project_names(self, service):
        """Unicode characters should be handled correctly."""
        # Note: Emoji may not be supported by the current pattern, test basic Unicode
        is_valid, _ = service.validate_project_name("プロジェクト名")
        assert is_valid is True

    def test_mixed_script_project_names(self, service):
        """Mixed script (Latin + CJK) should be valid."""
        is_valid, _ = service.validate_project_name("01_MyNovel異世界編")
        assert is_valid is True

    def test_empty_title_after_prefix_removal(self, service):
        """Empty title after prefix removal should be handled."""
        title = service.extract_title_from_name("01_")
        assert title == ""

    def test_project_root_with_spaces(self, service):
        """Project root paths with spaces should be handled."""
        project_root = Path("/tmp/my projects/novel name")
        config = service.generate_config(
            project_name="test", project_root=project_root
        )

        assert config.project_root == project_root


@pytest.mark.contract
class TestContractCompliance:
    """Contract tests verifying interface contracts."""

    def test_validate_project_name_contract(self, service):
        """validate_project_name must return (bool, Optional[str])."""
        result = service.validate_project_name("test")

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert result[1] is None or isinstance(result[1], str)

    def test_extract_title_contract(self, service):
        """extract_title_from_name must return str."""
        result = service.extract_title_from_name("01_test")

        assert isinstance(result, str)

    def test_generate_config_contract(self, service):
        """generate_config must return ProjectConfig."""
        result = service.generate_config(
            project_name="test", project_root=Path("/tmp/test")
        )

        assert isinstance(result, ProjectConfig)
        assert hasattr(result, "project_name")
        assert hasattr(result, "project_root")
        assert hasattr(result, "title")
        assert hasattr(result, "genre")
        assert hasattr(result, "status")
        assert hasattr(result, "created_date")
        assert hasattr(result, "pen_name")
