#!/usr/bin/env python3
# File: tests/unit/infrastructure/logging/test_safe_rotating_file_handler.py
# Purpose: Validate SafeRotatingFileHandler warnings to prevent MCP stderr noise.
# Context: Ensures PermissionError rotation failures notify once while maintaining fallback behaviour.

from __future__ import annotations

from pathlib import Path

import pytest

from noveler.infrastructure.logging.unified_logger import SafeRotatingFileHandler


def test_permission_error_warning_emitted_once(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Ensure repeated PermissionError events do not spam stderr output.

    Purpose:
        Confirm that SafeRotatingFileHandler emits the PermissionError warning
        a single time per handler instance while still executing fallback
        rotation logic.
    Args:
        tmp_path (Path): Temporary directory supplied by pytest.
        capsys (pytest.CaptureFixture[str]): Fixture capturing stderr output.
    Returns:
        None: The test asserts on captured stderr content.
    Preconditions:
        pytest must provide functional tmp_path and capsys fixtures.
    Side Effects:
        Creates fallback directories beneath the temporary path.
    """
    log_path = tmp_path / "novel_system.log"
    fallback_dir = tmp_path / "fallback"

    handler = SafeRotatingFileHandler(
        log_path,
        maxBytes=1,
        backupCount=1,
        encoding="utf-8",
        delay=True,
        fallback_dir=fallback_dir,
        fallback_retention_days=0,
    )

    handler._handle_rotation_failure(PermissionError("forced rotation failure"))
    first_err = capsys.readouterr().err

    handler._handle_rotation_failure(PermissionError("repeated failure"))
    second_err = capsys.readouterr().err

    handler.close()

    assert "SafeRotatingFileHandler: PermissionError during rotation" in first_err
    assert "SafeRotatingFileHandler: PermissionError during rotation" not in second_err
