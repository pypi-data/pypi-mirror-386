# File: tests/unit/infrastructure/test_claude_code_environment_detector.py
# Purpose: Ensure ClaudeCodeEnvironmentDetector relies on shared platform utilities for OS detection.
# Context: Validates Phase 0 cross-platform rollout behaviour across Windows and WSL scenarios.

"""Unit tests for ClaudeCodeEnvironmentDetector environment detection."""

from __future__ import annotations

from pathlib import Path

import pytest

from noveler.infrastructure import claude_code_session_integration as claude_module
from noveler.infrastructure.utils.platform import PlatformInfo, PlatformKind

_ENV_KEYS = (
    claude_module.ClaudeCodeEnvironmentDetector._ENVIRONMENT_MARKERS
    + claude_module.ClaudeCodeEnvironmentDetector._PATH_ENV_KEYS
)


def _clear_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def _make_platform_info(
    kind: PlatformKind,
    *,
    is_wsl: bool,
    is_windows: bool,
    is_unix: bool,
    raw_system: str,
    details: dict[str, str] | None = None,
) -> PlatformInfo:
    return PlatformInfo(
        kind=kind,
        is_wsl=is_wsl,
        is_windows=is_windows,
        is_unix=is_unix,
        raw_system=raw_system,
        details=details or {},
    )


def test_environment_detected_when_marker_present(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _clear_environment(monkeypatch)
    info = _make_platform_info(
        PlatformKind.WINDOWS,
        is_wsl=False,
        is_windows=True,
        is_unix=False,
        raw_system="Windows",
    )
    monkeypatch.setattr(claude_module, "detect_platform", lambda: info)
    monkeypatch.setenv("CLAUDE_CODE_SESSION", "1")
    monkeypatch.setattr(claude_module.os, "getcwd", lambda: str(tmp_path))
    monkeypatch.setattr(claude_module, "_PROJECT_ROOT", tmp_path / "project")
    monkeypatch.chdir(tmp_path)

    assert claude_module.ClaudeCodeEnvironmentDetector.is_claude_code_environment() is True


def test_environment_detected_with_wsl_and_windows_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _clear_environment(monkeypatch)
    info = _make_platform_info(
        PlatformKind.WSL,
        is_wsl=True,
        is_windows=True,
        is_unix=True,
        raw_system="Linux",
        details={"wsl_distro": "Ubuntu-22.04"},
    )
    monkeypatch.setattr(claude_module, "detect_platform", lambda: info)
    project_root = Path("/mnt/c/Users/foo/00_ガイド")
    monkeypatch.setattr(claude_module, "_PROJECT_ROOT", project_root)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GUIDE_ROOT", r"C:\Users\foo\00_ガイド")
    monkeypatch.setattr(claude_module.os, "getcwd", lambda: r"C:\Users\foo\00_ガイド")

    assert claude_module.ClaudeCodeEnvironmentDetector.is_claude_code_environment() is True


def test_environment_not_detected_without_indicators(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _clear_environment(monkeypatch)
    info = _make_platform_info(
        PlatformKind.LINUX,
        is_wsl=False,
        is_windows=False,
        is_unix=True,
        raw_system="Linux",
    )
    monkeypatch.setattr(claude_module, "detect_platform", lambda: info)
    monkeypatch.setattr(claude_module, "_PROJECT_ROOT", Path("/srv/noveler"))
    monkeypatch.setattr(claude_module.os, "getcwd", lambda: str(tmp_path))
    monkeypatch.chdir(tmp_path)

    assert claude_module.ClaudeCodeEnvironmentDetector.is_claude_code_environment() is False
