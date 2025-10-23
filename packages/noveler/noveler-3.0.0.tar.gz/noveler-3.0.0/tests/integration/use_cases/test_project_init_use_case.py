#!/usr/bin/env python3
# File: tests/integration/use_cases/test_project_init_use_case.py
# Purpose: Integration tests for ProjectInitUseCase orchestration and rollback
# Context: Phase 4 Testing - Full workflow tests including transaction semantics
"""Integration tests for ProjectInitUseCase.

These tests verify the complete workflow including:
- Dependency coordination (service + repository)
- File system operations
- Transaction semantics with rollback
- End-to-end success scenarios
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from noveler.application.use_cases.project_init_use_case import (
    ProjectInitRequest,
    ProjectInitResult,
    ProjectInitUseCase,
)
from noveler.domain.services.project_initializer_service import (
    ProjectInitializerService,
)
from noveler.infrastructure.repositories.template_repository import (
    TemplateRepository,
)


@pytest.fixture
def temp_project_root(tmp_path):
    """Create temporary project root directory."""
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    return projects_dir


@pytest.fixture
def temp_templates(tmp_path):
    """Create temporary template directory with required templates."""
    template_dir = tmp_path / "templates" / "project" / "base"
    template_dir.mkdir(parents=True)

    # README template
    readme_template = template_dir / "README.md.j2"
    readme_template.write_text(
        """# {{ title }}

作成日: {{ created_date }}

## 概要
[作品の概要をここに記載]
""",
        encoding="utf-8",
    )

    # .gitignore template
    gitignore_template = template_dir / ".gitignore.j2"
    gitignore_template.write_text(
        """*.tmp
*.bak
.env
""",
        encoding="utf-8",
    )

    # プロジェクト設定 template
    config_template = template_dir / "プロジェクト設定.yaml.j2"
    config_template.write_text(
        """paths:
  project_root: "{{ project_root }}"

project:
  name: "{{ title }}"
  genre: "{{ genre }}"
  status: "{{ status }}"
  created_date: "{{ created_date }}"

author:
  pen_name: "{{ pen_name }}"
""",
        encoding="utf-8",
    )

    return tmp_path / "templates"


@pytest.fixture
def mock_path_service(temp_project_root):
    """Create mock PathService."""
    mock = MagicMock()
    mock.project_root = temp_project_root
    return mock


@pytest.fixture
def initializer_service(mock_path_service):
    """Create ProjectInitializerService instance."""
    return ProjectInitializerService()


@pytest.fixture
def template_repository(temp_templates):
    """Create TemplateRepository instance."""
    return TemplateRepository(template_dir=temp_templates)


@pytest.fixture
def use_case(initializer_service, template_repository):
    """Create ProjectInitUseCase instance."""
    return ProjectInitUseCase(
        initializer_service=initializer_service,
        template_repository=template_repository,
    )


class TestSuccessfulInitialization:
    """Test successful project initialization scenarios."""

    def test_basic_project_initialization(
        self, use_case, temp_project_root
    ):
        """Basic project initialization should create all required files/directories."""
        project_name = "01_test_novel"

        request = ProjectInitRequest(
            project_name=project_name,
            project_root=temp_project_root,
            template_name="base",
        )

        result = use_case.execute(request)

        assert result.success is True
        assert result.project_path is not None
        assert result.project_path.exists()
        assert result.error_message is None

        # Verify directory structure
        expected_dirs = [
            "10_企画",
            "20_プロット",
            "30_設定集",
            "40_原稿",
            "50_管理資料",
            "90_アーカイブ",
        ]

        for dir_name in expected_dirs:
            dir_path = result.project_path / dir_name
            assert dir_path.exists(), f"Directory {dir_name} should exist"
            assert dir_path.is_dir(), f"{dir_name} should be a directory"

        # Verify configuration file
        config_path = result.project_path / "プロジェクト設定.yaml"
        assert config_path.exists(), "Configuration file should exist"
        config_content = config_path.read_text(encoding="utf-8")
        assert "test_novel" in config_content

        # Verify README
        readme_path = result.project_path / "README.md"
        assert readme_path.exists(), "README should exist"
        readme_content = readme_path.read_text(encoding="utf-8")
        assert "test_novel" in readme_content

        # Verify .gitignore
        gitignore_path = result.project_path / ".gitignore"
        assert gitignore_path.exists(), ".gitignore should exist"
        gitignore_content = gitignore_path.read_text(encoding="utf-8")
        assert "*.tmp" in gitignore_content

    def test_initialization_with_custom_parameters(
        self, use_case, temp_project_root
    ):
        """Initialization with custom parameters should use overrides."""
        request = ProjectInitRequest(
            project_name="my_novel",
            project_root=temp_project_root,
            template_name="base",
            genre="SF",
            pen_name="山田太郎",
        )

        result = use_case.execute(request)

        assert result.success is True

        # Verify custom parameters in configuration
        config_path = result.project_path / "プロジェクト設定.yaml"
        config_content = config_path.read_text(encoding="utf-8")

        assert "SF" in config_content
        assert "山田太郎" in config_content

    def test_result_contains_created_dirs_list(self, use_case, temp_project_root):
        """Result should contain list of created directories."""
        request = ProjectInitRequest(
            project_name="test",
            project_root=temp_project_root,
            template_name="base",
        )

        result = use_case.execute(request)

        assert result.created_dirs is not None
        # 7 directories: 1 project root + 6 standard directories
        assert len(result.created_dirs) == 7
        # Check that directory names are present (as strings, not full paths)
        created_dir_str = "\n".join(result.created_dirs)
        assert "10_企画" in created_dir_str
        assert "40_原稿" in created_dir_str


class TestValidationFailures:
    """Test precondition validation failures."""

    def test_invalid_project_name(self, use_case, temp_project_root):
        """Invalid project name should fail validation."""
        request = ProjectInitRequest(
            project_name="invalid/name",  # Slash not allowed
            project_root=temp_project_root,
            template_name="base",
        )

        result = use_case.execute(request)

        assert result.success is False
        assert result.error_message is not None
        # Error message is in Japanese: "プロジェクト名に使用できない文字が含まれています"
        assert ("使用できない" in result.error_message or "invalid" in result.error_message.lower())

    def test_nonexistent_template(self, use_case, temp_project_root):
        """Nonexistent template should fail validation."""
        request = ProjectInitRequest(
            project_name="test",
            project_root=temp_project_root,
            template_name="nonexistent",  # Template doesn't exist
        )

        result = use_case.execute(request)

        assert result.success is False
        assert result.error_message is not None
        assert "template" in result.error_message.lower()


class TestRollbackMechanism:
    """Test transaction rollback on failure."""

    def test_rollback_on_template_error(
        self, initializer_service, template_repository, temp_project_root
    ):
        """Rollback should clean up on template rendering failure."""
        # Create use case with broken template
        broken_template_dir = temp_project_root / "broken_templates"
        broken_template_dir.mkdir()

        broken_repo = TemplateRepository(template_dir=broken_template_dir)
        use_case = ProjectInitUseCase(
            initializer_service=initializer_service,
            template_repository=broken_repo,
        )

        request = ProjectInitRequest(
            project_name="test",
            project_root=temp_project_root,
            template_name="base",
        )

        result = use_case.execute(request)

        assert result.success is False

        # Verify project directory was NOT created (or was cleaned up)
        project_path = temp_project_root / "test"
        # Directory might exist but should be empty after rollback
        if project_path.exists():
            contents = list(project_path.iterdir())
            assert (
                len(contents) == 0
            ), "Project directory should be empty after rollback"

    def test_partial_success_rollback(
        self, initializer_service, temp_project_root, temp_templates
    ):
        """Rollback should handle partial success (some files created)."""
        # Create incomplete template directory (missing some templates)
        incomplete_dir = temp_templates / "project" / "incomplete"
        incomplete_dir.mkdir(parents=True)

        # Only create README template, missing config and gitignore
        readme = incomplete_dir / "README.md.j2"
        readme.write_text("# {{ title }}")

        template_repo = TemplateRepository(template_dir=temp_templates)
        use_case = ProjectInitUseCase(
            initializer_service=initializer_service,
            template_repository=template_repo,
        )

        request = ProjectInitRequest(
            project_name="test",
            project_root=temp_project_root,
            template_name="incomplete",
        )

        result = use_case.execute(request)

        assert result.success is False

        # Verify cleanup
        project_path = temp_project_root / "test"
        if project_path.exists():
            # Should not have partial files
            config_path = project_path / "プロジェクト設定.yaml"
            assert not config_path.exists(), "Partial files should be cleaned up"


class TestExistingDirectoryHandling:
    """Test behavior when project directory already exists."""

    def test_existing_empty_directory(self, use_case, temp_project_root):
        """Existing empty directory should be usable."""
        project_name = "existing_project"
        project_path = temp_project_root / project_name
        project_path.mkdir(parents=True)

        request = ProjectInitRequest(
            project_name=project_name,
            project_root=temp_project_root,
            template_name="base",
        )

        result = use_case.execute(request)

        # Should succeed (directory already exists, that's okay)
        assert result.success is True


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_unicode_project_name(self, use_case, temp_project_root):
        """Unicode project names should work correctly."""
        request = ProjectInitRequest(
            project_name="時空の図書館",
            project_root=temp_project_root,
            template_name="base",
        )

        result = use_case.execute(request)

        assert result.success is True
        assert result.project_path.exists()

    def test_project_root_with_spaces(self, use_case, tmp_path):
        """Project root paths with spaces should work."""
        project_root = tmp_path / "my projects"
        project_root.mkdir()

        request = ProjectInitRequest(
            project_name="test",
            project_root=project_root,
            template_name="base",
        )

        result = use_case.execute(request)

        assert result.success is True


@pytest.mark.contract
class TestContractCompliance:
    """Contract tests for use case interface."""

    def test_execute_returns_project_init_result(self, use_case, temp_project_root):
        """execute() must return ProjectInitResult."""
        request = ProjectInitRequest(
            project_name="test",
            project_root=temp_project_root,
            template_name="base",
        )

        result = use_case.execute(request)

        assert isinstance(result, ProjectInitResult)
        assert hasattr(result, "success")
        assert hasattr(result, "project_path")
        assert hasattr(result, "created_dirs")
        assert hasattr(result, "config_path")
        assert hasattr(result, "error_message")

    def test_success_result_has_valid_paths(self, use_case, temp_project_root):
        """Successful result must have valid paths."""
        request = ProjectInitRequest(
            project_name="test",
            project_root=temp_project_root,
            template_name="base",
        )

        result = use_case.execute(request)

        if result.success:
            assert result.project_path is not None
            assert isinstance(result.project_path, Path)
            assert result.config_path is not None
            assert isinstance(result.config_path, Path)
            assert result.error_message is None

    def test_failure_result_has_error_message(
        self, use_case, temp_project_root
    ):
        """Failed result must have error message."""
        request = ProjectInitRequest(
            project_name="invalid/name",
            project_root=temp_project_root,
            template_name="base",
        )

        result = use_case.execute(request)

        if not result.success:
            assert result.error_message is not None
            assert isinstance(result.error_message, str)
            assert len(result.error_message) > 0
