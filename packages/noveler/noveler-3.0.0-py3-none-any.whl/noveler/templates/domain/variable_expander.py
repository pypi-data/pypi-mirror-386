"""Variable Expander - Jinja2-based template variable expansion.

Domain Layer: Pure business logic with NO I/O operations.
Responsible for: Template text + context → expanded text

SOLID Principles:
- SRP: Single responsibility (variable expansion only)
- OCP: Open for extension (custom filters can be added)
- LSP: N/A (no inheritance)
- ISP: Minimal interface (2 methods)
- DIP: No external dependencies
"""

from typing import Dict, Any
import jinja2
from jinja2 import Environment, Template, TemplateError, UndefinedError


class Jinja2TemplateError(Exception):
    """Custom exception for Jinja2 template errors."""
    pass


class VariableExpander:
    """Expands Jinja2 template variables with given context.

    This class provides pure function behavior - no side effects, no I/O.
    All operations are deterministic: same input → same output.

    Examples:
        >>> expander = VariableExpander()
        >>> template = "Target: {{ writing_style.target_average }} chars"
        >>> context = {"writing_style": {"target_average": 38}}
        >>> expander.expand(template, context)
        'Target: 38 chars'
    """

    def __init__(self) -> None:
        """Initialize Jinja2 environment with safe defaults.

        Configuration:
        - autoescape: False (YAML templates don't need HTML escaping)
        - undefined: StrictUndefined (fail fast on missing variables)
        - trim_blocks: True (clean YAML formatting)
        - lstrip_blocks: True (clean indentation)
        """
        self._env = Environment(
            autoescape=False,
            undefined=jinja2.StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def expand(self, template_text: str, context: Dict[str, Any]) -> str:
        """Expand Jinja2 template variables with given context.

        Args:
            template_text: Jinja2 template string (e.g., "{{ var }}")
            context: Variable dictionary (e.g., {"var": "value"})

        Returns:
            Expanded text with all variables replaced

        Raises:
            Jinja2TemplateError: If template syntax is invalid or variables undefined

        Precondition:
            - template_text is valid Jinja2 syntax
            - context contains all variables referenced in template

        Postcondition:
            - All {{ var }} placeholders are replaced with actual values
            - Returned string contains no Jinja2 syntax

        Purity:
            Pure function - no side effects, deterministic output
        """
        try:
            template = self._env.from_string(template_text)
            return template.render(**context)

        except UndefinedError as e:
            raise Jinja2TemplateError(
                f"Undefined variable in template: {e}"
            ) from e

        except TemplateError as e:
            raise Jinja2TemplateError(
                f"Template syntax error: {e}"
            ) from e

    def validate_syntax(self, template_text: str) -> bool:
        """Validate Jinja2 template syntax without rendering.

        Args:
            template_text: Jinja2 template string to validate

        Returns:
            True if syntax is valid, False otherwise

        Purity:
            Pure function - no side effects

        Note:
            This only checks syntax, not variable availability.
            Use expand() to verify variable resolution.
        """
        try:
            self._env.from_string(template_text)
            return True
        except TemplateError:
            return False
