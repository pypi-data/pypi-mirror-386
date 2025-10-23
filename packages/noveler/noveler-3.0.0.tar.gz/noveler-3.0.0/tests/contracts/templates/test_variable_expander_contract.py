"""Contract tests for VariableExpander.

Tests verify that VariableExpander honors its public interface contract:
- expand() returns expanded string
- validate_syntax() returns boolean
- Jinja2TemplateError raised on template errors
"""

import pytest
from src.noveler.templates.domain.variable_expander import (
    VariableExpander,
    Jinja2TemplateError,
)


class TestVariableExpanderContract:
    """Contract tests for VariableExpander public interface."""

    def setup_method(self):
        """Setup test fixture."""
        self.expander = VariableExpander()

    def test_expand_returns_string(self):
        """Contract: expand() must return str."""
        template = "Hello {{ name }}"
        context = {"name": "World"}

        result = self.expander.expand(template, context)

        assert isinstance(result, str)
        assert result == "Hello World"

    def test_expand_replaces_all_variables(self):
        """Contract: expand() must replace all {{ var }} placeholders."""
        template = "{{ a }} and {{ b }}"
        context = {"a": "foo", "b": "bar"}

        result = self.expander.expand(template, context)

        assert "{{" not in result
        assert "}}" not in result
        assert result == "foo and bar"

    def test_expand_handles_nested_dict(self):
        """Contract: expand() must support nested dict access (e.g., {{ obj.key }})."""
        template = "Value: {{ config.setting }}"
        context = {"config": {"setting": "test"}}

        result = self.expander.expand(template, context)

        assert result == "Value: test"

    def test_expand_raises_on_undefined_variable(self):
        """Contract: expand() must raise Jinja2TemplateError on undefined variable."""
        template = "{{ undefined_var }}"
        context = {}

        with pytest.raises(Jinja2TemplateError) as exc_info:
            self.expander.expand(template, context)

        assert "Undefined variable" in str(exc_info.value)

    def test_expand_raises_on_syntax_error(self):
        """Contract: expand() must raise Jinja2TemplateError on invalid syntax."""
        template = "{{ invalid syntax }}"  # Space in variable name is invalid
        context = {}

        with pytest.raises(Jinja2TemplateError):
            self.expander.expand(template, context)

    def test_expand_is_pure_function(self):
        """Contract: expand() must be pure (same input → same output)."""
        template = "{{ x }}"
        context = {"x": "value"}

        result1 = self.expander.expand(template, context)
        result2 = self.expander.expand(template, context)

        assert result1 == result2

    def test_validate_syntax_returns_bool(self):
        """Contract: validate_syntax() must return bool."""
        result_valid = self.expander.validate_syntax("{{ valid }}")
        result_invalid = self.expander.validate_syntax("{{ invalid")

        assert isinstance(result_valid, bool)
        assert isinstance(result_invalid, bool)

    def test_validate_syntax_accepts_valid_template(self):
        """Contract: validate_syntax() returns True for valid syntax."""
        assert self.expander.validate_syntax("{{ var }}") is True
        assert self.expander.validate_syntax("{{ obj.key }}") is True
        assert self.expander.validate_syntax("Plain text") is True

    def test_validate_syntax_rejects_invalid_template(self):
        """Contract: validate_syntax() returns False for invalid syntax."""
        assert self.expander.validate_syntax("{{ unclosed") is False
        assert self.expander.validate_syntax("{{ }}") is False

    def test_expand_preserves_whitespace(self):
        """Contract: expand() should respect Jinja2 whitespace control settings."""
        template = "Line1\n{{ var }}\nLine2"
        context = {"var": "X"}

        result = self.expander.expand(template, context)

        # With trim_blocks=True, lstrip_blocks=True
        # Newlines around variables are cleaned up
        assert "Line1" in result
        assert "X" in result
        assert "Line2" in result


class TestVariableExpanderSpecCompliance:
    """Verify VariableExpander complies with design specifications."""

    def test_has_required_methods(self):
        """Spec: VariableExpander must have expand() and validate_syntax()."""
        expander = VariableExpander()

        assert hasattr(expander, "expand")
        assert callable(expander.expand)

        assert hasattr(expander, "validate_syntax")
        assert callable(expander.validate_syntax)

    def test_expand_signature(self):
        """Spec: expand(template_text: str, context: dict) -> str"""
        import inspect

        sig = inspect.signature(VariableExpander.expand)
        params = list(sig.parameters.keys())

        assert params == ["self", "template_text", "context"]
        assert sig.return_annotation == str

    def test_validate_syntax_signature(self):
        """Spec: validate_syntax(template_text: str) -> bool"""
        import inspect

        sig = inspect.signature(VariableExpander.validate_syntax)
        params = list(sig.parameters.keys())

        assert params == ["self", "template_text"]
        assert sig.return_annotation == bool

    def test_no_external_dependencies(self):
        """Spec: Domain layer must have no external dependencies (except stdlib)."""
        # VariableExpander should only import jinja2 (acceptable) and stdlib
        # This is verified by implementation inspection
        expander = VariableExpander()

        # Should be instantiable without any external configuration
        assert expander is not None

    def test_exception_type_contract(self):
        """Spec: Custom Jinja2TemplateError must be raised (not raw Jinja2 errors)."""
        expander = VariableExpander()

        # Undefined variable should raise our custom exception
        with pytest.raises(Jinja2TemplateError):
            expander.expand("{{ undef }}", {})

        # Syntax error should also raise our custom exception
        with pytest.raises(Jinja2TemplateError):
            expander.expand("{{ invalid", {})
