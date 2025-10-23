#!/usr/bin/env python3
# File: tests/unit/presentation/cli/test_slash_command_edge_cases.py
# Purpose: Edge case tests for /noveler-write slash command
# Context: P1 task from Serena Deep Review - ensure robustness and security

"""Edge case tests for noveler write command.

Tests cover:
- Invalid episode numbers (negative, non-numeric, overflow)
- Injection attempts (SQL-like, shell-like)
- Boundary conditions

All tests verify graceful failure and appropriate error messages.
"""

from __future__ import annotations

import pytest

from noveler.presentation.cli import cli_adapter


@pytest.mark.unit
class TestNovelerWriteEdgeCases:
    """Edge case tests for 'noveler write' command."""

    @pytest.fixture(autouse=True)
    def _stub_execute(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Stub execute_18_step_writing to avoid heavy IO in unit tests."""

        async def _dummy_execute(episode: int, dry_run: bool, project_root: str) -> dict:  # noqa: ANN001
            return {"success": True}

        monkeypatch.setattr(cli_adapter, "execute_18_step_writing", _dummy_execute)

    def test_write_with_negative_episode(self) -> None:
        """Negative episode number passes int() validation but may fail in business logic.

        Expected behavior:
        - int() accepts negative numbers
        - Business logic may reject negative episodes
        - Returns exit code 0 (success) or 1 (business logic failure)

        Note: Current implementation allows negative numbers through CLI validation.
        Business logic validation is performed by MCP server/use case layer.
        """
        result = cli_adapter.run(["write", "-1"])
        # Allow success or business logic failure, but not usage error
        assert result in (0, 1), "Negative episode should pass CLI validation"

    def test_write_with_non_numeric_episode(self) -> None:
        """Non-numeric episode should fail gracefully.

        Expected behavior:
        - Returns exit code 2 (usage error)
        - int() conversion fails early
        - Displays error message about requiring integer episode
        """
        result = cli_adapter.run(["write", "abc"])
        assert result == 2, "Non-numeric episode should be rejected"

    def test_write_with_very_large_episode(self) -> None:
        """Very large episode number should be handled.

        Expected behavior:
        - Either processes normally (if within Python int range)
        - Or fails gracefully (if business logic rejects)
        - Must not crash or cause undefined behavior
        """
        result = cli_adapter.run(["write", "999999999"])
        # Allow any valid exit code (0=success, 1=failure, 2=usage error)
        # The important thing is no crash
        assert result in (0, 1, 2), "Large episode number must not crash"

    def test_write_with_sql_injection_attempt(self) -> None:
        """SQL injection-like input should be rejected.

        Expected behavior:
        - Returns exit code 2 (usage error)
        - int() conversion fails on non-numeric input
        - Injection payload never reaches database or command execution
        """
        result = cli_adapter.run(["write", "1; DROP TABLE episodes;"])
        assert result == 2, "Injection attempt should be rejected at parsing"

    def test_write_with_shell_injection_attempt(self) -> None:
        """Shell injection-like input should be rejected.

        Expected behavior:
        - Returns exit code 2 (usage error)
        - int() conversion fails on non-numeric input
        - Shell metacharacters never reach command execution
        """
        result = cli_adapter.run(["write", "1 && rm -rf /"])
        assert result == 2, "Shell injection attempt should be rejected at parsing"

    def test_write_with_zero_episode(self) -> None:
        """Zero episode number should be handled.

        Expected behavior:
        - Depends on business logic (may be valid or invalid)
        - Must not crash
        - Should return predictable exit code
        """
        result = cli_adapter.run(["write", "0"])
        assert result in (0, 1, 2), "Zero episode must not crash"

    def test_write_with_float_episode(self) -> None:
        """Float episode number should be rejected.

        Expected behavior:
        - Returns exit code 2 (usage error)
        - int() conversion fails on float string
        - Displays error message about requiring integer
        """
        result = cli_adapter.run(["write", "1.5"])
        assert result == 2, "Float episode should be rejected"

    def test_write_with_special_characters(self) -> None:
        """Special characters in episode should be rejected.

        Expected behavior:
        - Returns exit code 2 (usage error)
        - int() conversion fails on special characters
        - No escaping issues in error messages
        """
        result = cli_adapter.run(["write", "1'5"])
        assert result == 2, "Special characters should be rejected"

    def test_write_with_unicode_digits(self) -> None:
        """Unicode digits should be rejected.

        Expected behavior:
        - Returns exit code 2 (usage error)
        - int() only accepts ASCII digits
        - Unicode normalization does not bypass validation
        """
        result = cli_adapter.run(["write", "①"])  # Circled digit one (U+2460)
        assert result == 2, "Unicode digits should be rejected"

    def test_write_with_empty_string(self) -> None:
        """Empty string episode should be rejected.

        Expected behavior:
        - Returns exit code 2 (usage error)
        - Caught by "if not rest" check before int() conversion
        - Displays usage message
        """
        result = cli_adapter.run(["write", ""])
        assert result == 2, "Empty string should be rejected"

    def test_write_with_whitespace_only(self) -> None:
        """Whitespace-only episode should be rejected.

        Expected behavior:
        - Returns exit code 2 (usage error)
        - int() conversion fails on whitespace
        - Displays error message
        """
        result = cli_adapter.run(["write", "   "])
        assert result == 2, "Whitespace-only should be rejected"

    def test_write_with_hexadecimal_format(self) -> None:
        """Hexadecimal format episode should be rejected.

        Expected behavior:
        - Returns exit code 2 (usage error)
        - int() with no base parameter does not accept "0x" prefix
        - Must explicitly use base 10
        """
        result = cli_adapter.run(["write", "0x10"])
        assert result == 2, "Hexadecimal format should be rejected"

    def test_write_with_dry_run_only_defaults_to_episode_one(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Dry-run flag without explicit episode should default to episode 1."""
        captured: dict[str, object] = {}

        async def _capture_execute(episode: int, dry_run: bool, project_root: str) -> dict:  # noqa: ANN001
            captured["episode"] = episode
            captured["dry_run"] = dry_run
            captured["project_root"] = project_root
            return {"success": True}

        monkeypatch.setattr(cli_adapter, "execute_18_step_writing", _capture_execute)

        result = cli_adapter.run(["write", "--dry-run"])

        assert result == 0, "Dry-run without explicit episode should succeed"
        assert captured.get("episode") == 1
        assert captured.get("dry_run") is True

    def test_write_without_arguments_defaults_to_episode_one(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """No arguments should trigger episode 1 execution."""
        captured: dict[str, object] = {}

        async def _capture_execute(episode: int, dry_run: bool, project_root: str) -> dict:  # noqa: ANN001
            captured["episode"] = episode
            captured["dry_run"] = dry_run
            return {"success": True}

        monkeypatch.setattr(cli_adapter, "execute_18_step_writing", _capture_execute)

        result = cli_adapter.run(["write"])

        assert result == 0
        assert captured.get("episode") == 1
        assert captured.get("dry_run") is False

    def test_write_with_unknown_flag_returns_usage_error(self) -> None:
        """Unknown flags should raise a usage error (exit code 2)."""
        result = cli_adapter.run(["write", "--unknown-option"])
        assert result == 2, "Unknown flag should be treated as usage error"
