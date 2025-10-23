# File: scripts/tooling/cache_root.py
# Purpose: Ensure NOVELER cache directories default to a WSL-backed location on Windows hosts.
# Context: Imported by cross-platform CLI hubs so caches avoid OneDrive sync conflicts by preferring UNC paths.

"""Utilities for resolving a safe cache root across Windows and WSL environments.

The helper exposed here discovers an appropriate cache directory and exports it
via the ``NOVELER_CACHE_ROOT`` environment variable when unset. On Windows
hosts the logic prefers the ``\\wsl.localhost`` UNC share so that runtime
artifacts stay outside OneDrive-synchronised folders.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
import platform
from pathlib import Path
from typing import Iterable, MutableMapping, Optional, Sequence, Tuple


@dataclass(frozen=True)
class CacheRootResult:
    """Outcome of :func:`ensure_cache_root`.

    Attributes:
        path: Filesystem path selected as cache root.
        source: Description of the discovery path (e.g. ``"env"`` or ``"wsl:Ubuntu"``).
        created: True when the directory did not exist and was newly created.
    """

    path: Path
    source: str
    created: bool


def _running_on_windows() -> bool:
    """Return True when the current interpreter runs on a Windows host."""

    return platform.system().lower() == "windows"


def _candidate_usernames(env: MutableMapping[str, str]) -> Sequence[str]:
    """Collect plausible WSL usernames based on environment hints."""

    candidates: list[str] = []
    seen: set[str] = set()

    def _add(value: Optional[str]) -> None:
        if value:
            trimmed = value.strip()
            if trimmed and trimmed not in seen:
                candidates.append(trimmed)
                seen.add(trimmed)

    _add(env.get("NOVELER_WSL_USER"))
    _add(env.get("USERNAME"))
    _add(env.get("USER"))

    profile = env.get("USERPROFILE")
    if profile:
        _add(Path(profile).name)

    return candidates


def _ensure_directory(path: Path) -> Optional[Tuple[Path, bool]]:
    """Create *path* if needed and report whether it was newly created.

    Returns ``None`` when the directory cannot be created due to permissions.
    """

    try:
        existed = path.exists()
    except OSError:
        existed = False
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None
    return path, not existed


def _iter_wsl_distro_roots(env: MutableMapping[str, str]) -> Iterable[Path]:
    """Yield potential WSL distribution roots under ``\\\\wsl.localhost``."""

    hint = env.get("NOVELER_WSL_DISTRO")
    unc_root = Path("\\\\wsl.localhost")

    if hint:
        hinted = unc_root / hint
        yield hinted

    if not unc_root.exists():
        return

    try:
        for entry in unc_root.iterdir():
            if entry.is_dir():
                yield entry
    except OSError:
        return


def _discover_wsl_cache_root(env: MutableMapping[str, str]) -> Optional[CacheRootResult]:
    """Attempt to place the cache under a WSL home directory via UNC access."""

    usernames = _candidate_usernames(env)
    for distro in _iter_wsl_distro_roots(env):
        home_root = distro / "home"
        if usernames:
            for username in usernames:
                candidate = home_root / username / ".noveler_cache"
                prepared = _ensure_directory(candidate)
                if prepared:
                    path, created = prepared
                    return CacheRootResult(path=path, source=f"wsl:{distro.name}:{username}", created=created)
        try:
            for maybe_user in home_root.iterdir():
                if not maybe_user.is_dir():
                    continue
                candidate = maybe_user / ".noveler_cache"
                prepared = _ensure_directory(candidate)
                if prepared:
                    path, created = prepared
                    return CacheRootResult(path=path, source=f"wsl:{distro.name}:{maybe_user.name}", created=created)
        except OSError:
            continue
    return None


def ensure_cache_root(env: Optional[MutableMapping[str, str]] = None) -> CacheRootResult:
    """Ensure ``NOVELER_CACHE_ROOT`` is set to a writable directory.

    Args:
        env: Optional environment mapping to mutate. Defaults to :mod:`os.environ`.

    Returns:
        CacheRootResult describing the selected directory.
    """

    mapping: MutableMapping[str, str] = env if env is not None else os.environ

    existing = mapping.get("NOVELER_CACHE_ROOT")
    if existing:
        path = Path(existing)
        prepared = _ensure_directory(path)
        created = False
        if prepared:
            path, created = prepared
        return CacheRootResult(path=path, source="env", created=created)

    if _running_on_windows():
        wsl_result = _discover_wsl_cache_root(mapping)
        if wsl_result:
            mapping["NOVELER_CACHE_ROOT"] = str(wsl_result.path)
            return wsl_result

    fallback_path = Path.home() / ".noveler_cache"
    prepared = _ensure_directory(fallback_path)
    if prepared is None:
        # As a last resort use the current working directory.
        fallback_path = Path.cwd() / ".noveler_cache"
        prepared = _ensure_directory(fallback_path)
        if prepared is None:
            raise RuntimeError("Unable to initialise a writable cache directory")
    path, created = prepared
    mapping["NOVELER_CACHE_ROOT"] = str(path)
    return CacheRootResult(path=path, source="home", created=created)


__all__ = ["CacheRootResult", "ensure_cache_root"]
