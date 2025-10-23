# File: tests/unit/scripts/test_error_handling_coverage.py
# Purpose: Extended test coverage for error handling and custom exceptions
# Context: Coverage expansion for exception handling and edge cases

"""Test coverage for error handling and custom exceptions."""

import pytest
import json
import sys
from pathlib import Path

# Add scripts/ci to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts" / "ci"))

from run_quality_checks_ndjson import (
    CIWrapperError,
    YAMLParseError,
    ToolExecutionError,
    GateCEvaluationError,
    WorkingDirectoryError,
)


class TestCIWrapperErrorBase:
    """Test base CIWrapperError exception."""

    def test_ci_wrapper_error_creation(self):
        """Test creating CIWrapperError."""
        error = CIWrapperError("Test error message")
        assert str(error) == "Test error message"

    def test_ci_wrapper_error_inheritance(self):
        """Test that CIWrapperError inherits from Exception."""
        error = CIWrapperError("test")
        assert isinstance(error, Exception)

    def test_ci_wrapper_error_can_be_caught(self):
        """Test that CIWrapperError can be caught."""
        with pytest.raises(CIWrapperError):
            raise CIWrapperError("test error")


class TestYAMLParseError:
    """Test YAMLParseError exception."""

    def test_yaml_parse_error_with_path(self):
        """Test YAMLParseError with file path."""
        original_error = ValueError("Invalid YAML")
        error = YAMLParseError("config.yaml", original_error)

        assert "config.yaml" in str(error)
        assert error.path == "config.yaml"
        assert error.error == original_error

    def test_yaml_parse_error_with_line_number(self):
        """Test YAMLParseError with line number."""
        original_error = ValueError("Invalid structure")
        error = YAMLParseError("config.yaml", original_error, line_number=42)

        assert "config.yaml" in str(error)
        assert "42" in str(error)
        assert error.line_number == 42

    def test_yaml_parse_error_inheritance(self):
        """Test that YAMLParseError inherits from CIWrapperError."""
        error = YAMLParseError("test.yaml", ValueError("test"))
        assert isinstance(error, CIWrapperError)
        assert isinstance(error, Exception)


class TestToolExecutionError:
    """Test ToolExecutionError exception."""

    def test_tool_execution_error_with_exit_code(self):
        """Test ToolExecutionError with exit code."""
        error = ToolExecutionError("Tool failed", exit_code=3)
        assert str(error) == "Tool failed"
        assert error.exit_code == 3

    def test_tool_execution_error_default_exit_code(self):
        """Test ToolExecutionError with default exit code."""
        error = ToolExecutionError("Tool failed")
        assert error.exit_code == 3  # Default

    def test_tool_execution_error_inheritance(self):
        """Test that ToolExecutionError inherits from CIWrapperError."""
        error = ToolExecutionError("test", exit_code=3)
        assert isinstance(error, CIWrapperError)
        assert isinstance(error, Exception)

    def test_tool_execution_error_custom_exit_code(self):
        """Test ToolExecutionError with custom exit codes."""
        error2 = ToolExecutionError("test", exit_code=2)
        error1 = ToolExecutionError("test", exit_code=1)
        assert error2.exit_code == 2
        assert error1.exit_code == 1


class TestGateCEvaluationError:
    """Test GateCEvaluationError exception."""

    def test_gate_c_evaluation_error(self):
        """Test GateCEvaluationError creation."""
        original_error = FileNotFoundError("Report not found")
        error = GateCEvaluationError("reports/editorial.md", original_error)

        assert "reports/editorial.md" in str(error)
        assert error.report_path == "reports/editorial.md"
        assert error.error == original_error

    def test_gate_c_evaluation_error_inheritance(self):
        """Test that GateCEvaluationError inherits from CIWrapperError."""
        error = GateCEvaluationError("report.md", ValueError("test"))
        assert isinstance(error, CIWrapperError)
        assert isinstance(error, Exception)


class TestWorkingDirectoryError:
    """Test WorkingDirectoryError exception."""

    def test_working_directory_error(self):
        """Test WorkingDirectoryError creation."""
        original_error = PermissionError("Cannot access directory")
        error = WorkingDirectoryError("/invalid/path", original_error)

        assert "/invalid/path" in str(error)
        assert error.path == "/invalid/path"
        assert error.error == original_error

    def test_working_directory_error_inheritance(self):
        """Test that WorkingDirectoryError inherits from CIWrapperError."""
        error = WorkingDirectoryError("/path", OSError("test"))
        assert isinstance(error, CIWrapperError)
        assert isinstance(error, Exception)


class TestExceptionCatching:
    """Test exception catching patterns."""

    def test_catch_tool_execution_error(self):
        """Test catching ToolExecutionError specifically."""
        with pytest.raises(ToolExecutionError) as exc_info:
            raise ToolExecutionError("Tool failed", exit_code=3)

        assert exc_info.value.exit_code == 3

    def test_catch_ci_wrapper_error_catches_all(self):
        """Test that CIWrapperError catches all CI-related errors."""
        errors = [
            YAMLParseError("test.yaml", ValueError("test")),
            ToolExecutionError("test", exit_code=3),
            GateCEvaluationError("report.md", FileNotFoundError("test")),
            WorkingDirectoryError("/path", OSError("test")),
        ]

        for error in errors:
            with pytest.raises(CIWrapperError):
                raise error

    def test_catch_specific_error_not_base(self):
        """Test that catching specific error doesn't catch others."""
        # ToolExecutionError should not be caught by YAMLParseError handler
        with pytest.raises(ToolExecutionError):
            try:
                raise ToolExecutionError("test", exit_code=3)
            except YAMLParseError:
                pass  # Should not reach here

    def test_exception_error_message_clarity(self):
        """Test that exception messages are clear and helpful."""
        error = YAMLParseError(
            "config/quality/gate_defaults.yaml",
            ValueError("Invalid key structure"),
            line_number=25
        )

        error_msg = str(error)
        assert "gate_defaults.yaml" in error_msg
        assert "25" in error_msg
        assert "Invalid key structure" in error_msg


class TestExceptionErrorContext:
    """Test exception error context preservation."""

    def test_exception_chain_preserved(self):
        """Test that exception chains are preserved."""
        try:
            original = ValueError("Original error")
            raise YAMLParseError("config.yaml", original)
        except YAMLParseError as e:
            assert e.error.args[0] == "Original error"

    def test_exception_attributes_accessible(self):
        """Test that exception attributes are accessible."""
        error = WorkingDirectoryError("/invalid/path", OSError("Permission denied"))
        assert error.path == "/invalid/path"
        assert isinstance(error.error, OSError)


class TestErrorMessageFormatting:
    """Test error message formatting for logging."""

    def test_yaml_parse_error_message_format(self):
        """Test YAMLParseError message is properly formatted."""
        error = YAMLParseError(
            "test.yaml",
            ValueError("Invalid syntax"),
            line_number=10
        )
        msg = str(error)
        # Should include path, error type, and line number
        assert "test.yaml" in msg
        assert "10" in msg

    def test_tool_execution_error_message_format(self):
        """Test ToolExecutionError message is properly formatted."""
        error = ToolExecutionError("Tool subprocess failed with timeout", exit_code=3)
        msg = str(error)
        assert "Tool subprocess failed" in msg

    def test_gate_c_evaluation_error_message_format(self):
        """Test GateCEvaluationError message is properly formatted."""
        error = GateCEvaluationError(
            "reports/editorial.md",
            FileNotFoundError("File not found")
        )
        msg = str(error)
        assert "editorial.md" in msg
        assert "failed" in msg.lower()
