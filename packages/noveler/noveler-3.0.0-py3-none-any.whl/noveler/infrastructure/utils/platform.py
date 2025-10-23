# File: src/noveler/infrastructure/utils/platform.py
# Purpose: Provide a centralised platform detection helper so runtime checks remain consistent.
# Context: Used by infrastructure modules (Claude Code integration, path services, diagnostics) to branch per OS/WSL.

"""Utilities for platform detection across Windows, WSL, Linux, and macOS.

This module exposes a cached `detect_platform` helper along with convenience
wrappers so other components can query environment details without duplicating
heuristics. Detection is read-only and designed to be easily unit tested by
mocking the underlying `platform` or environment modules.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from functools import lru_cache
import os
import platform
from pathlib import Path
from typing import Dict


class PlatformKind(Enum):
    """Enumeration of supported platform categories."""

    WINDOWS = auto()
    WSL = auto()
    LINUX = auto()
    MACOS = auto()
    UNKNOWN = auto()


@dataclass(frozen=True)
class PlatformInfo:
    """Snapshot of detected platform properties.

    Attributes:
        kind: High-level platform classification.
        is_wsl: True when running under Windows Subsystem for Linux.
        is_windows: True when the host OS is Windows (native or WSL).
        is_unix: True for Unix-like platforms (Linux, WSL, macOS).
        raw_system: Raw value from `platform.system()`.
        details: Optional metadata such as distro/build information.
    """

    kind: PlatformKind
    is_wsl: bool
    is_windows: bool
    is_unix: bool
    raw_system: str
    details: Dict[str, str]


def _read_text(path: Path) -> str:
    """Safely read a lowercase text representation from `path`.

    Returns an empty string when the file cannot be read.
    """

    try:
        return path.read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        return ""


def _detect_wsl(env: Dict[str, str], raw_system: str) -> bool:
    """Detect whether the current process is running inside WSL."""

    if env.get("WSL_DISTRO_NAME") or env.get("WSL_INTEROP"):
        return True

    if raw_system.lower() != "linux":
        return False

    version_text = _read_text(Path("/proc/version"))
    if "microsoft" in version_text:
        return True

    release_text = _read_text(Path("/proc/sys/kernel/osrelease"))
    return "microsoft" in release_text


@lru_cache(maxsize=1)
def detect_platform() -> PlatformInfo:
    """Detect and cache platform information for the current process."""

    raw_system = platform.system() or ""
    normalized = raw_system.lower()
    env = dict(os.environ)

    is_wsl = _detect_wsl(env, raw_system)

    if is_wsl:
        kind = PlatformKind.WSL
    elif normalized == "windows":
        kind = PlatformKind.WINDOWS
    elif normalized == "linux":
        kind = PlatformKind.LINUX
    elif normalized == "darwin":
        kind = PlatformKind.MACOS
    else:
        kind = PlatformKind.UNKNOWN

    is_windows = kind in {PlatformKind.WINDOWS, PlatformKind.WSL}
    is_unix = kind in {PlatformKind.WSL, PlatformKind.LINUX, PlatformKind.MACOS}

    details: Dict[str, str] = {
        "raw_system": raw_system,
    }
    if is_wsl:
        distro = env.get("WSL_DISTRO_NAME") or ""
        if distro:
            details["wsl_distro"] = distro
        version = _read_text(Path("/proc/version"))
        if version:
            details["wsl_kernel"] = version.strip()
    elif kind == PlatformKind.WINDOWS:
        release = platform.release()
        if release:
            details["windows_release"] = release

    return PlatformInfo(
        kind=kind,
        is_wsl=is_wsl,
        is_windows=is_windows,
        is_unix=is_unix,
        raw_system=raw_system,
        details=details,
    )


def reset_platform_cache() -> None:
    """Clear cached detection results (used by tests)."""

    detect_platform.cache_clear()


def is_wsl() -> bool:
    """Return True when running under Windows Subsystem for Linux."""

    return detect_platform().is_wsl


def is_windows_native() -> bool:
    """Return True when running on Windows without WSL."""

    info = detect_platform()
    return info.kind == PlatformKind.WINDOWS


def is_windows() -> bool:
    """Return True for Windows hosts (native or WSL)."""

    return detect_platform().is_windows


def is_macos() -> bool:
    """Return True when running on macOS."""

    return detect_platform().kind == PlatformKind.MACOS


def is_linux() -> bool:
    """Return True for Linux hosts excluding WSL."""

    info = detect_platform()
    return info.kind == PlatformKind.LINUX


def is_unix_like() -> bool:
    """Return True for Unix-like systems (Linux, WSL, macOS)."""

    return detect_platform().is_unix
