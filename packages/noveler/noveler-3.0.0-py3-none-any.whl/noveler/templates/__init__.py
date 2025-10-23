"""Template Variable Expansion System.

Public API for template rendering with Jinja2 variable expansion.

Usage:
    >>> from noveler.templates import TemplateRenderer
    >>> renderer = TemplateRenderer(project_root)
    >>> yaml_data = renderer.render_template("templates/write_step13.yaml")
"""

from .template_renderer import TemplateRenderer

__all__ = ["TemplateRenderer"]
