# File: src/noveler/infrastructure/repositories/template_repository.py
# Purpose: Template file management and rendering
# Context: Infrastructure layer repository for external I/O

"""
TemplateRepository - テンプレート管理とレンダリング

This repository provides access to project template files and renders them
with Jinja2 template engine.

Responsibilities:
- Load template files from templates/ directory
- Render templates with provided parameters
- List available templates
- Validate template existence

Design Principles:
- Single Responsibility: Template management only
- Open/Closed: Easy to add new templates without code changes
- Dependency Injection: Template directory path is configurable
"""

from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound


class TemplateNotFoundError(FileNotFoundError):
    """Raised when requested template does not exist."""

    pass


class TemplateRepository:
    """
    Repository for managing and rendering Jinja2 templates.

    This repository abstracts template file access and rendering logic.
    Templates are stored in a configurable directory and rendered with Jinja2.

    Attributes:
        _template_dir: Path to template directory
        _env: Jinja2 Environment for template loading
    """

    def __init__(self, template_dir: Path):
        """
        Initialize template repository.

        Args:
            template_dir: Path to directory containing template files

        Raises:
            NotADirectoryError: If template_dir does not exist or is not a directory
        """
        if not template_dir.exists():
            raise NotADirectoryError(f"Template directory not found: {template_dir}")

        if not template_dir.is_dir():
            raise NotADirectoryError(f"Not a directory: {template_dir}")

        self._template_dir = template_dir
        self._env = Environment(
            loader=FileSystemLoader(str(template_dir), encoding="utf-8"),
            autoescape=False,  # Disable auto-escaping for text files
        )

    def get_template(self, name: str) -> Template:
        """
        Retrieve template by name.

        Args:
            name: Template name (relative path from template_dir)
                  e.g., "project/base/README.md.j2"

        Returns:
            Jinja2 Template object

        Raises:
            TemplateNotFoundError: If template does not exist

        Examples:
            >>> repo = TemplateRepository(Path("templates"))
            >>> template = repo.get_template("project/base/README.md.j2")
        """
        try:
            return self._env.get_template(name)
        except TemplateNotFound as e:
            raise TemplateNotFoundError(
                f"Template not found: {name}"
            ) from e

    def render_template(self, template: Template, params: Dict[str, any]) -> str:
        """
        Render template with provided parameters.

        Args:
            template: Jinja2 Template object (from get_template())
            params: Dictionary of template parameters

        Returns:
            Rendered template as string

        Examples:
            >>> template = repo.get_template("README.md.j2")
            >>> content = repo.render_template(template, {"title": "My Novel"})
        """
        return template.render(**params)

    def render_template_by_name(
        self, name: str, params: Dict[str, any]
    ) -> str:
        """
        Get and render template in one call.

        Convenience method combining get_template() and render_template().

        Args:
            name: Template name (relative path from template_dir)
            params: Dictionary of template parameters

        Returns:
            Rendered template as string

        Raises:
            TemplateNotFoundError: If template does not exist
        """
        template = self.get_template(name)
        return self.render_template(template, params)

    def list_available_templates(self, pattern: str = "**/*.j2") -> List[str]:
        """
        List all available template files.

        Args:
            pattern: Glob pattern for matching templates (default: "**/*.j2")

        Returns:
            List of template names (relative paths from template_dir)

        Examples:
            >>> repo.list_available_templates()
            ['project/base/README.md.j2', 'project/base/.gitignore.j2']
            >>> repo.list_available_templates("project/**/*.j2")
            ['project/base/README.md.j2']
        """
        template_files = self._template_dir.glob(pattern)
        relative_paths = [
            str(f.relative_to(self._template_dir)) for f in template_files
        ]
        return sorted(relative_paths)

    def validate_template_exists(self, name: str) -> bool:
        """
        Check if template exists.

        Args:
            name: Template name (relative path from template_dir)

        Returns:
            True if template exists, False otherwise

        Examples:
            >>> repo.validate_template_exists("project/base/README.md.j2")
            True
            >>> repo.validate_template_exists("nonexistent.j2")
            False
        """
        template_path = self._template_dir / name
        return template_path.exists() and template_path.is_file()

    def get_template_path(self, name: str) -> Path:
        """
        Get absolute path to template file.

        Args:
            name: Template name (relative path from template_dir)

        Returns:
            Absolute Path to template file

        Raises:
            TemplateNotFoundError: If template does not exist
        """
        template_path = self._template_dir / name
        if not self.validate_template_exists(name):
            raise TemplateNotFoundError(f"Template not found: {name}")
        return template_path
