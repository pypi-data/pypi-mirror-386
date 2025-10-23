# File: tests/unit/infrastructure/utils/test_platform.py
# Purpose: Validate platform detection helper behaviour across operating systems.
# Context: Ensures infrastructure utilities make consistent OS/WSL decisions for downstream modules.

"""Unit tests for platform detection utilities."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Dict

import pytest

from noveler.infrastructure.utils import platform as platform_utils


@pytest.fixture(autouse=True)
def _reset_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure each test receives a fresh detection cache."""

    platform_utils.reset_platform_cache()
    yield
    platform_utils.reset_platform_cache()


def _patch_environment(monkeypatch: pytest.MonkeyPatch, values: Dict[str, str]) -> None:
    for key in list(values.keys()):
        monkeypatch.setenv(key, values[key])

    # Remove common indicators unless explicitly supplied.
    for key in ("WSL_DISTRO_NAME", "WSL_INTEROP"):
        if key not in values:
            monkeypatch.delenv(key, raising=False)


def test_detect_windows_native(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(platform_utils.platform, "system", lambda: "Windows")
    monkeypatch.setattr(platform_utils.platform, "release", lambda: "11")
    _patch_environment(monkeypatch, {})

    info = platform_utils.detect_platform()

    assert info.kind is platform_utils.PlatformKind.WINDOWS
    assert info.is_windows is True
    assert info.is_wsl is False
    assert info.details.get("windows_release") == "11"
    assert info.is_unix is False


def test_detect_wsl_via_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(platform_utils.platform, "system", lambda: "Linux")
    _patch_environment(monkeypatch, {"WSL_DISTRO_NAME": "Ubuntu-22.04"})
    monkeypatch.setattr(
        platform_utils,
        "_read_text",
        lambda path: "linux version 5.15.0-WSL microsoft"
        if "version" in path.as_posix()
        else "microsoft",
    )

    info = platform_utils.detect_platform()

    assert info.kind is platform_utils.PlatformKind.WSL
    assert platform_utils.is_wsl() is True
    assert info.details.get("wsl_distro") == "Ubuntu-22.04"
    assert "microsoft" in info.details.get("wsl_kernel", "")


def test_detect_linux(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(platform_utils.platform, "system", lambda: "Linux")
    _patch_environment(monkeypatch, {})
    monkeypatch.setattr(platform_utils, "_read_text", lambda path: "")

    info = platform_utils.detect_platform()

    assert info.kind is platform_utils.PlatformKind.LINUX
    assert info.is_unix is True
    assert info.is_wsl is False
    assert platform_utils.is_linux() is True
    assert platform_utils.is_unix_like() is True


def test_detect_macos(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(platform_utils.platform, "system", lambda: "Darwin")
    _patch_environment(monkeypatch, {})

    info = platform_utils.detect_platform()

    assert info.kind is platform_utils.PlatformKind.MACOS
    assert platform_utils.is_macos() is True
    assert platform_utils.is_windows() is False


def test_detect_platform_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = SimpleNamespace(count=0)

    def _system() -> str:
        calls.count += 1
        return "Windows"

    monkeypatch.setattr(platform_utils.platform, "system", _system)
    monkeypatch.setattr(platform_utils.platform, "release", lambda: "10")
    _patch_environment(monkeypatch, {})

    first = platform_utils.detect_platform()
    second = platform_utils.detect_platform()

    assert first is second
    assert calls.count == 1
