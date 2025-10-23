# File: tests/unit/scripts/test_yaml_parsing_coverage.py
# Purpose: Extended test coverage for YAML parsing functions
# Context: Coverage expansion for _parse_yaml_simple, _parse_yaml_value, _deep_merge

"""Test coverage for YAML parsing edge cases and type conversions."""

import pytest
from pathlib import Path

# Add scripts/ci to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts" / "ci"))

from run_quality_checks_ndjson import (
    _parse_yaml_simple,
    _parse_yaml_value,
    _deep_merge,
)


class TestParseYAMLSimpleEdgeCases:
    """Test edge cases in YAML parsing."""

    def test_parse_yaml_with_comments(self):
        """Test that comments are properly ignored."""
        yaml_content = """
gate_defaults:
  # This is a comment
  thresholds:
    # Nested comment
    severity: medium  # Inline comment
    gate_b:
      rhythm: 80
"""
        result = _parse_yaml_simple(yaml_content)
        assert result["gate_defaults"]["thresholds"]["severity"] == "medium"
        assert result["gate_defaults"]["thresholds"]["gate_b"]["rhythm"] == 80

    def test_parse_yaml_with_blank_lines(self):
        """Test that blank lines are properly handled."""
        yaml_content = """
gate_defaults:

  thresholds:

    severity: medium

    gate_b:
      rhythm: 80
"""
        result = _parse_yaml_simple(yaml_content)
        assert result["gate_defaults"]["thresholds"]["severity"] == "medium"
        assert result["gate_defaults"]["thresholds"]["gate_b"]["rhythm"] == 80

    def test_parse_yaml_nested_lists(self):
        """Test parsing of nested lists."""
        yaml_content = """
gates:
  aspects:
    - rhythm
    - readability
    - grammar
    - style
"""
        result = _parse_yaml_simple(yaml_content)
        assert result["gates"]["aspects"] == ["rhythm", "readability", "grammar", "style"]

    def test_parse_yaml_list_with_comments(self):
        """Test lists with comments between items.

        Note: Dict items in lists with nested fields are a known limitation
        of the lightweight YAML parser. This test verifies the documented behavior.
        """
        yaml_content = """
steps:
  # Comment before list
  - simple_item
  - another_item
"""
        result = _parse_yaml_simple(yaml_content)
        assert isinstance(result["steps"], list)
        assert result["steps"] == ["simple_item", "another_item"]

    def test_parse_yaml_empty_dict(self):
        """Test parsing empty nested dicts."""
        yaml_content = """
root:
  empty_dict:
  nested:
    value: data
"""
        result = _parse_yaml_simple(yaml_content)
        assert result["root"]["empty_dict"] == {}
        assert result["root"]["nested"]["value"] == "data"

    def test_parse_yaml_empty_list(self):
        """Test parsing empty lists."""
        yaml_content = """
root:
  items:
nested:
  value: test
"""
        result = _parse_yaml_simple(yaml_content)
        # Empty list handling: should create empty dict or skip
        assert "nested" in result
        assert result["nested"]["value"] == "test"


class TestParseYAMLValue:
    """Test YAML value type detection and conversion."""

    def test_parse_value_boolean_true(self):
        """Test boolean true parsing."""
        assert _parse_yaml_value("true") is True
        assert _parse_yaml_value("True") is True
        assert _parse_yaml_value("yes") is True
        assert _parse_yaml_value("on") is True

    def test_parse_value_boolean_false(self):
        """Test boolean false parsing."""
        assert _parse_yaml_value("false") is False
        assert _parse_yaml_value("False") is False
        assert _parse_yaml_value("no") is False
        assert _parse_yaml_value("off") is False

    def test_parse_value_null(self):
        """Test null value parsing."""
        assert _parse_yaml_value("null") is None
        assert _parse_yaml_value("~") is None

    def test_parse_value_float(self):
        """Test float literal parsing."""
        assert _parse_yaml_value("82.5") == 82.5
        assert _parse_yaml_value("3.14") == 3.14
        assert _parse_yaml_value("-2.71") == -2.71
        assert _parse_yaml_value("0.0") == 0.0

    def test_parse_value_integer(self):
        """Test integer parsing."""
        assert _parse_yaml_value("80") == 80
        assert _parse_yaml_value("0") == 0
        assert _parse_yaml_value("-100") == -100

    def test_parse_value_string(self):
        """Test string parsing (unquoted and quoted)."""
        assert _parse_yaml_value("hello") == "hello"
        assert _parse_yaml_value('"quoted string"') == "quoted string"
        assert _parse_yaml_value("'single quoted'") == "single quoted"

    def test_parse_value_string_with_inline_comment(self):
        """Test that inline comments are stripped from strings."""
        # "value # comment" should become "value"
        assert _parse_yaml_value("value # comment") == "value"

    def test_parse_value_quoted_string_with_hash(self):
        """Test that hash inside quotes is preserved."""
        assert _parse_yaml_value('"value # not a comment"') == "value # not a comment"

    def test_parse_value_path(self):
        """Test parsing of file paths (strings with slashes)."""
        assert _parse_yaml_value("reports/quality.ndjson") == "reports/quality.ndjson"
        assert _parse_yaml_value("/absolute/path") == "/absolute/path"

    def test_parse_value_whitespace_handling(self):
        """Test that leading/trailing whitespace is handled."""
        assert _parse_yaml_value("  value  ") == "value"
        assert _parse_yaml_value("  true  ") is True


class TestDeepMerge:
    """Test dictionary deep merge functionality."""

    def test_deep_merge_simple_override(self):
        """Test simple value override."""
        target = {"a": 1, "b": 2}
        source = {"b": 3, "c": 4}
        _deep_merge(target, source)
        assert target == {"a": 1, "b": 3, "c": 4}

    def test_deep_merge_nested_dicts(self):
        """Test merging nested dictionaries."""
        target = {"a": {"b": 1, "c": 2}}
        source = {"a": {"c": 3, "d": 4}}
        _deep_merge(target, source)
        assert target == {"a": {"b": 1, "c": 3, "d": 4}}

    def test_deep_merge_deeply_nested(self):
        """Test merging deeply nested structures."""
        target = {
            "level1": {
                "level2": {
                    "level3": {"value": 1, "other": 2}
                }
            }
        }
        source = {
            "level1": {
                "level2": {
                    "level3": {"value": 99}
                }
            }
        }
        _deep_merge(target, source)
        assert target["level1"]["level2"]["level3"]["value"] == 99
        assert target["level1"]["level2"]["level3"]["other"] == 2

    def test_deep_merge_list_replacement(self):
        """Test that lists are replaced, not merged."""
        target = {"items": [1, 2, 3]}
        source = {"items": [4, 5]}
        _deep_merge(target, source)
        assert target["items"] == [4, 5]

    def test_deep_merge_empty_dicts(self):
        """Test merging with empty dictionaries."""
        target = {"a": 1}
        source = {}
        _deep_merge(target, source)
        assert target == {"a": 1}

    def test_deep_merge_into_empty(self):
        """Test merging into empty dictionary."""
        target = {}
        source = {"a": 1, "b": 2}
        _deep_merge(target, source)
        assert target == {"a": 1, "b": 2}


class TestYAMLParseIntegration:
    """Integration tests combining multiple parsing functions."""

    def test_parse_complex_yaml_structure(self):
        """Test parsing a complex realistic YAML structure."""
        yaml_content = """
ci:
  # CI Configuration
  tool:
    subprocess_timeout: 30
  output:
    default_path: temp/quality.ndjson
  gates:
    gate_b:
      min_threshold: 80.0
      aspects:
        - rhythm
        - readability
    gate_c:
      require_all_pass: true
  error_handling:
    exit_code_success: 0
    exit_code_error: 3
"""
        result = _parse_yaml_simple(yaml_content)

        # Verify structure
        assert result["ci"]["tool"]["subprocess_timeout"] == 30
        assert result["ci"]["output"]["default_path"] == "temp/quality.ndjson"
        assert result["ci"]["gates"]["gate_b"]["min_threshold"] == 80.0
        assert result["ci"]["gates"]["gate_b"]["aspects"] == ["rhythm", "readability"]
        assert result["ci"]["gates"]["gate_c"]["require_all_pass"] is True
        assert result["ci"]["error_handling"]["exit_code_error"] == 3

    def test_parse_yaml_with_various_types(self):
        """Test YAML with all supported type conversions."""
        yaml_content = """
config:
  string_value: hello
  int_value: 42
  float_value: 3.14
  bool_true: true
  bool_false: false
  null_value: null
  quoted_string: "quoted value"
  list_values:
    - item1
    - item2
    - item3
"""
        result = _parse_yaml_simple(yaml_content)

        assert result["config"]["string_value"] == "hello"
        assert result["config"]["int_value"] == 42
        assert result["config"]["float_value"] == 3.14
        assert result["config"]["bool_true"] is True
        assert result["config"]["bool_false"] is False
        assert result["config"]["null_value"] is None
        assert result["config"]["quoted_string"] == "quoted value"
        assert result["config"]["list_values"] == ["item1", "item2", "item3"]
