#!/usr/bin/env python3
# File: tests/unit/infrastructure/repositories/test_template_repository.py
# Purpose: Unit tests for TemplateRepository infrastructure component
# Context: Phase 4 Testing - Template management and Jinja2 rendering tests
"""Unit tests for TemplateRepository.

These tests verify template loading, rendering, and error handling.
Tests use temporary directories to avoid filesystem dependencies.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from noveler.infrastructure.repositories.template_repository import (
    TemplateNotFoundError,
    TemplateRepository,
)


@pytest.fixture
def temp_template_dir(tmp_path):
    """Create temporary template directory with sample templates."""
    template_dir = tmp_path / "templates"
    template_dir.mkdir()

    # Create simple test template
    simple_template = template_dir / "simple.j2"
    simple_template.write_text("Hello {{ name }}!")

    # Create template with multiple variables
    complex_template = template_dir / "complex.j2"
    complex_template.write_text(
        """# {{ title }}

Created: {{ created_date }}
Author: {{ author }}

## Description
{{ description }}
"""
    )

    # Create nested directory with template
    nested_dir = template_dir / "nested"
    nested_dir.mkdir()
    nested_template = nested_dir / "nested.j2"
    nested_template.write_text("Nested: {{ value }}")

    return template_dir


@pytest.fixture
def repository(temp_template_dir):
    """Create TemplateRepository instance with temporary directory."""
    return TemplateRepository(template_dir=temp_template_dir)


class TestRepositoryInitialization:
    """Test repository initialization."""

    def test_initialization_with_valid_path(self, temp_template_dir):
        """Repository should initialize with valid directory path."""
        repo = TemplateRepository(template_dir=temp_template_dir)
        assert repo._template_dir == temp_template_dir
        assert repo._env is not None

    def test_initialization_with_nonexistent_path(self, tmp_path):
        """Repository should raise NotADirectoryError for nonexistent path."""
        nonexistent = tmp_path / "nonexistent"
        with pytest.raises(NotADirectoryError) as exc_info:
            TemplateRepository(template_dir=nonexistent)

        assert "not found" in str(exc_info.value).lower()


class TestGetTemplate:
    """Test template retrieval."""

    def test_get_existing_template(self, repository):
        """Getting existing template should return Template object."""
        template = repository.get_template("simple.j2")
        assert template is not None
        assert hasattr(template, "render")

    def test_get_nested_template(self, repository):
        """Getting nested template should work with relative path."""
        template = repository.get_template("nested/nested.j2")
        assert template is not None

    def test_get_nonexistent_template_raises_error(self, repository):
        """Getting nonexistent template should raise TemplateNotFoundError."""
        with pytest.raises(TemplateNotFoundError) as exc_info:
            repository.get_template("nonexistent.j2")

        assert "nonexistent.j2" in str(exc_info.value)


class TestRenderTemplate:
    """Test template rendering."""

    def test_render_simple_template(self, repository):
        """Simple template should render with single parameter."""
        template = repository.get_template("simple.j2")
        result = repository.render_template(template, {"name": "World"})

        assert result == "Hello World!"

    def test_render_complex_template(self, repository):
        """Complex template should render with multiple parameters."""
        template = repository.get_template("complex.j2")
        params = {
            "title": "My Novel",
            "created_date": "2025-10-14",
            "author": "Author Name",
            "description": "A fantastic story",
        }

        result = repository.render_template(template, params)

        assert "# My Novel" in result
        assert "Created: 2025-10-14" in result
        assert "Author: Author Name" in result
        assert "A fantastic story" in result

    def test_render_with_missing_parameter(self, repository):
        """Rendering with missing parameter should use empty string (default Jinja2 behavior)."""
        template = repository.get_template("simple.j2")
        result = repository.render_template(template, {})

        # Jinja2 renders undefined variables as empty string by default
        assert result == "Hello !"

    def test_render_with_extra_parameters(self, repository):
        """Extra parameters should be ignored during rendering."""
        template = repository.get_template("simple.j2")
        result = repository.render_template(
            template, {"name": "World", "extra": "ignored"}
        )

        assert result == "Hello World!"

    def test_render_preserves_unicode(self, repository):
        """Unicode characters should be preserved during rendering."""
        template = repository.get_template("simple.j2")
        result = repository.render_template(template, {"name": "世界"})

        assert result == "Hello 世界!"


class TestListAvailableTemplates:
    """Test template listing."""

    def test_list_all_templates(self, repository):
        """list_available_templates should return all .j2 files."""
        templates = repository.list_available_templates()

        assert len(templates) >= 3
        assert "simple.j2" in templates
        assert "complex.j2" in templates
        # Accept both Unix (/) and Windows (\) path separators
        nested_template = "nested/nested.j2"
        windows_template = "nested\\nested.j2"
        assert nested_template in templates or windows_template in templates

    def test_list_templates_with_pattern(self, repository, temp_template_dir):
        """list_available_templates should support custom glob patterns."""
        # Create .txt template for testing
        txt_template = temp_template_dir / "test.txt"
        txt_template.write_text("text template")

        templates = repository.list_available_templates(pattern="**/*.txt")

        assert len(templates) >= 1
        assert "test.txt" in templates

    def test_list_templates_empty_directory(self, tmp_path):
        """Empty directory should return empty list."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        repo = TemplateRepository(template_dir=empty_dir)
        templates = repo.list_available_templates()

        assert templates == []


class TestValidateTemplateExists:
    """Test template existence validation."""

    def test_validate_existing_template(self, repository):
        """Existing template should validate as True."""
        exists = repository.validate_template_exists("simple.j2")
        assert exists is True

    def test_validate_nested_template(self, repository):
        """Nested template should validate with full path."""
        exists = repository.validate_template_exists("nested/nested.j2")
        assert exists is True

    def test_validate_nonexistent_template(self, repository):
        """Nonexistent template should validate as False."""
        exists = repository.validate_template_exists("nonexistent.j2")
        assert exists is False


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_template_with_special_characters(self, repository, temp_template_dir):
        """Templates with special characters in filenames should work."""
        special_template = temp_template_dir / "special-name_01.j2"
        special_template.write_text("Special: {{ value }}")

        template = repository.get_template("special-name_01.j2")
        result = repository.render_template(template, {"value": "test"})

        assert result == "Special: test"

    def test_empty_template(self, repository, temp_template_dir):
        """Empty template should render as empty string."""
        empty_template = temp_template_dir / "empty.j2"
        empty_template.write_text("")

        template = repository.get_template("empty.j2")
        result = repository.render_template(template, {})

        assert result == ""

    def test_template_with_jinja2_control_structures(
        self, repository, temp_template_dir
    ):
        """Templates with control structures (if, for) should render correctly."""
        control_template = temp_template_dir / "control.j2"
        control_template.write_text(
            """{% if show %}
Visible
{% endif %}
{% for item in items %}
- {{ item }}
{% endfor %}"""
        )

        template = repository.get_template("control.j2")
        result = repository.render_template(
            template, {"show": True, "items": ["a", "b", "c"]}
        )

        assert "Visible" in result
        assert "- a" in result
        assert "- b" in result
        assert "- c" in result


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_template_not_found_error_message(self, repository):
        """TemplateNotFoundError should contain template name."""
        with pytest.raises(TemplateNotFoundError) as exc_info:
            repository.get_template("missing.j2")

        error_msg = str(exc_info.value)
        assert "missing.j2" in error_msg

    def test_invalid_template_syntax(self, repository, temp_template_dir):
        """Invalid Jinja2 syntax should raise appropriate error."""
        invalid_template = temp_template_dir / "invalid.j2"
        invalid_template.write_text("{{ unclosed")

        with pytest.raises(Exception):  # Jinja2 raises TemplateSyntaxError
            template = repository.get_template("invalid.j2")
            repository.render_template(template, {})


@pytest.mark.contract
class TestContractCompliance:
    """Contract tests verifying interface contracts."""

    def test_get_template_contract(self, repository):
        """get_template must return Template object or raise TemplateNotFoundError."""
        # Success case
        template = repository.get_template("simple.j2")
        assert hasattr(template, "render")

        # Error case
        with pytest.raises(TemplateNotFoundError):
            repository.get_template("nonexistent.j2")

    def test_render_template_contract(self, repository):
        """render_template must return str."""
        template = repository.get_template("simple.j2")
        result = repository.render_template(template, {"name": "Test"})

        assert isinstance(result, str)

    def test_list_available_templates_contract(self, repository):
        """list_available_templates must return List[str]."""
        result = repository.list_available_templates()

        assert isinstance(result, list)
        assert all(isinstance(item, str) for item in result)

    def test_validate_template_exists_contract(self, repository):
        """validate_template_exists must return bool."""
        result = repository.validate_template_exists("simple.j2")

        assert isinstance(result, bool)


@pytest.mark.integration
class TestIntegrationScenarios:
    """Integration-like tests for common usage patterns."""

    def test_full_workflow_get_render(self, repository):
        """Complete workflow: get template → render → verify output."""
        # Get template
        template = repository.get_template("complex.j2")

        # Render with parameters
        params = {
            "title": "Test Title",
            "created_date": "2025-10-14",
            "author": "Test Author",
            "description": "Test Description",
        }
        result = repository.render_template(template, params)

        # Verify all parameters rendered
        assert "Test Title" in result
        assert "2025-10-14" in result
        assert "Test Author" in result
        assert "Test Description" in result

    def test_multiple_renders_same_template(self, repository):
        """Same template should render independently multiple times."""
        template = repository.get_template("simple.j2")

        result1 = repository.render_template(template, {"name": "First"})
        result2 = repository.render_template(template, {"name": "Second"})

        assert result1 == "Hello First!"
        assert result2 == "Hello Second!"
        assert result1 != result2
