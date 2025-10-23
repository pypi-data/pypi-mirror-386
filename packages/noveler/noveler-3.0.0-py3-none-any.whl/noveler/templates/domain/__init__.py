"""Domain Layer - Pure business logic.

Exports:
    - VariableExpander: Jinja2 template expansion
    - WritingStyleConfig: Configuration schema
    - ValidationError: Configuration validation errors
"""

from .variable_expander import VariableExpander, Jinja2TemplateError
from .config_schema import WritingStyleConfig, WritingStylePreset, ValidationError

__all__ = [
    "VariableExpander",
    "Jinja2TemplateError",
    "WritingStyleConfig",
    "WritingStylePreset",
    "ValidationError",
]
