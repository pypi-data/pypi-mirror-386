#!/usr/bin/env python3
"""
Plot template system integration adapter

This infrastructure adapter handles template loading, caching, and rendering
for plot generation, separating template engine concerns from domain logic.

Follows DDD principles:
- Infrastructure layer responsibilities only
- Template system integration focus
- Caching and performance optimization
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from noveler.infrastructure.caching.file_cache_service import get_file_cache_service

try:
    from jinja2 import Environment, FileSystemLoader, Template

    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False


@dataclass
class TemplateData:
    """Data for template rendering"""

    episode_number: int
    chapter_number: int
    project_name: str
    context_data: dict[str, Any]
    variables: dict[str, Any]


@dataclass
class TemplateResult:
    """Result of template rendering"""

    success: bool
    content: str
    template_used: str
    error_message: str | None = None
    render_time_ms: int | None = None


@dataclass
class TemplateInfo:
    """Template metadata"""

    template_id: str
    name: str
    description: str
    category: str
    variables: list[str]
    last_modified: str


class PlotTemplateAdapter:
    """
    Infrastructure adapter for plot template system

    Responsibilities:
    - Template file loading and management
    - Template rendering with data
    - Template caching for performance
    - Template validation and error handling
    """

    def __init__(self, template_directories: list[Path] | None = None) -> None:
        """Initialize template adapter

        Args:
            template_directories: Directories to search for templates
        """
        self._template_directories = template_directories or self._get_default_template_dirs()
        self._template_cache: dict[str, Template] = {}
        self._template_info_cache: dict[str, TemplateInfo] = {}
        self._jinja_env: Environment | None = None
        self._initialize_template_engine()

    def generate_with_template(self, template_id: str, template_data: TemplateData) -> TemplateResult:
        """Generate plot using template system

        Args:
            template_id: ID of template to use
            template_data: Data for template rendering

        Returns:
            TemplateResult: Rendered template result
        """
        try:
            start_time = datetime.now(timezone.utc)

            template = self._load_template(template_id)
            if not template:
                return TemplateResult(
                    success=False,
                    content="",
                    template_used=template_id,
                    error_message=f"Template '{template_id}' not found",
                )

            rendered_content = self._render_template(template, template_data)
            end_time = datetime.now(timezone.utc)

            return TemplateResult(
                success=True,
                content=rendered_content,
                template_used=template_id,
                render_time_ms=int((end_time - start_time).total_seconds() * 1000),
            )

        except Exception as e:
            return TemplateResult(
                success=False, content="", template_used=template_id, error_message=f"Template rendering error: {e!s}"
            )

    def get_available_templates(self) -> list[TemplateInfo]:
        """Get list of available templates

        Returns:
            list[TemplateInfo]: Available template information
        """
        templates = []

        for template_dir in self._template_directories:
            if not template_dir.exists():
                continue

            # 高速化: ファイルキャッシュサービス使用でglob操作を最適化
            cache_service = get_file_cache_service()
            template_files = cache_service.get_matching_files(
                template_dir, "*.yaml", ttl_seconds=600  # テンプレートは変更頻度低いので10分キャッシュ
            )

            for template_file in template_files:
                try:
                    template_info = self._load_template_info(template_file)
                    if template_info:
                        templates.append(template_info)
                except Exception:
                    # Skip invalid templates
                    continue

        return templates

    def validate_template_data(self, template_id: str, template_data: TemplateData) -> list[str]:
        """Validate template data for required variables

        Args:
            template_id: Template to validate against
            template_data: Data to validate

        Returns:
            list[str]: List of validation errors (empty if valid)
        """
        errors: list[Any] = []

        template_info = self._get_template_info(template_id)
        if not template_info:
            errors.append(f"Template '{template_id}' not found")
            return errors

        # Check required variables
        required_vars = template_info.variables
        provided_vars = set(template_data.variables.keys())
        provided_vars.update({"episode_number", "chapter_number", "project_name"})

        missing_vars = set(required_vars) - provided_vars
        if missing_vars:
            errors.append(f"Missing required variables: {', '.join(missing_vars)}")

        # Basic data validation
        if template_data.episode_number <= 0:
            errors.append("Episode number must be positive")

        if template_data.chapter_number <= 0:
            errors.append("Chapter number must be positive")

        if not template_data.project_name.strip():
            errors.append("Project name is required")

        return errors

    def load_template_cache(self) -> dict[str, Any]:
        """Load template cache information

        Returns:
            dict: Template cache statistics and information
        """
        return {
            "cached_templates": len(self._template_cache),
            "template_directories": [str(d) for d in self._template_directories],
            "jinja2_available": JINJA2_AVAILABLE,
            "cache_entries": list(self._template_cache.keys()),
        }

    def clear_template_cache(self) -> None:
        """Clear template cache"""
        self._template_cache.clear()
        self._template_info_cache.clear()

    def _initialize_template_engine(self) -> None:
        """Initialize Jinja2 template engine if available"""
        if not JINJA2_AVAILABLE:
            return

        try:
            template_paths = [str(d) for d in self._template_directories if d.exists()]
            if template_paths:
                self._jinja_env = Environment(
                    loader=FileSystemLoader(template_paths),
                    autoescape=False,  # YAML output doesn't need escaping
                )
        except Exception:
            self._jinja_env = None

    def _get_default_template_dirs(self) -> list[Path]:
        """Get default template directories

        Returns:
            list[Path]: Default template search paths
        """
        # Try to find templates relative to script location
        script_dir = Path(__file__).parent.parent.parent.parent

        return [
            script_dir / "templates",
            script_dir / "scripts" / "templates" / "plot",
            Path("templates"),  # Current directory fallback
        ]

    def _load_template(self, template_id: str) -> Template | None:
        """Load template by ID

        Args:
            template_id: Template identifier

        Returns:
            Template: Loaded template or None if not found
        """
        # Check cache first
        if template_id in self._template_cache:
            return self._template_cache[template_id]

        # Try to load template file
        template_path = self._find_template_file(template_id)
        if not template_path:
            return None

        try:
            if JINJA2_AVAILABLE and self._jinja_env:
                # Use Jinja2 for advanced templating
                template = self._jinja_env.get_template(template_path.name)
            else:
                # Simple fallback: read file and treat as raw template text
                template_content = template_path.read_text(encoding="utf-8")
                template = Template(template_content)

            # Cache the template
            self._template_cache[template_id] = template
            return template

        except Exception:
            return None

    def _find_template_file(self, template_id: str) -> Path | None:
        """Find template file by ID

        Args:
            template_id: Template identifier

        Returns:
            Path: Template file path or None if not found
        """
        possible_names = [f"{template_id}.yaml", f"{template_id}_template.yaml", f"plot_{template_id}.yaml"]

        for template_dir in self._template_directories:
            if not template_dir.exists():
                continue

            for name in possible_names:
                template_path = template_dir / name
                if template_path.exists():
                    return template_path

        return None

    def _render_template(self, template: Template, template_data: TemplateData) -> str:
        """Render template with data

        Args:
            template: Template to render
            template_data: Data for rendering

        Returns:
            str: Rendered template content
        """
        # Prepare template variables
        template_vars = {
            "episode_number": template_data.episode_number,
            "chapter_number": template_data.chapter_number,
            "project_name": template_data.project_name,
            "context": template_data.context_data,
            **template_data.variables,
        }

        if JINJA2_AVAILABLE and hasattr(template, "render"):
            # Jinja2 template
            return template.render(**template_vars)
        # Simple string substitution
        content = str(template)
        for key, value in template_vars.items():
            placeholder = f"{{{{{key}}}}}"
            content = content.replace(placeholder, str(value))
        return content

    def _load_template_info(self, template_file: Path) -> TemplateInfo | None:
        """Load template metadata

        Args:
            template_file: Template file path

        Returns:
            TemplateInfo: Template information or None if invalid
        """
        try:
            f_content = template_file.read_text(encoding="utf-8")
            template_data: dict[str, Any] = yaml.safe_load(f_content) or {}

            if not isinstance(template_data, dict):
                return None

            # Extract metadata from template
            metadata = template_data.get("metadata", {})
            template_id = metadata.get("id", template_file.stem)

            return TemplateInfo(
                template_id=template_id,
                name=metadata.get("name", template_file.stem),
                description=metadata.get("description", "No description"),
                category=metadata.get("category", "general"),
                variables=metadata.get("required_variables", []),
                last_modified=str(template_file.stat().st_mtime),
            )

        except Exception:
            return None

    def _get_template_info(self, template_id: str) -> TemplateInfo | None:
        """Get template information by ID

        Args:
            template_id: Template identifier

        Returns:
            TemplateInfo: Template information or None if not found
        """
        # Check cache
        if template_id in self._template_info_cache:
            return self._template_info_cache[template_id]

        # Find and load template info
        template_file = self._find_template_file(template_id)
        if not template_file:
            return None

        template_info = self._load_template_info(template_file)
        if template_info:
            self._template_info_cache[template_id] = template_info

        return template_info
