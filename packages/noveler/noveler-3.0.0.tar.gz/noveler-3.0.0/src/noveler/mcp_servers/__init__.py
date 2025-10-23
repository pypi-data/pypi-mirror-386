"""Compatibility shim exposing `mcp_servers.noveler` as `noveler.mcp_servers`.

The MCP server implementation historically lived outside the `noveler` package.
Several integration points and tests still import it via `noveler.mcp_servers`,
so this module proxies to the real implementation without duplicating code.
"""
from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable

_target_pkg: ModuleType | None = None

# Initialize package metadata with safe defaults; updated upon first access.
__all__: list[str] = []
__path__: list[str] = []

__spec__ = importlib.util.spec_from_loader(__name__, loader=None, is_package=True)
if __spec__ is not None:
    __spec__.submodule_search_locations = __path__


def _extend_search_path(candidate: Path) -> None:
    """Append existing package locations to ``__path__`` for delegation."""

    if not candidate.exists():
        return
    location = str(candidate)
    if location not in __path__:
        __path__.append(location)
    if __spec__ is not None:
        __spec__.submodule_search_locations = __path__


_current_file = Path(__file__).resolve()
for parent in _current_file.parents:
    _extend_search_path(parent / "mcp_servers")
    _extend_search_path(parent / "src" / "mcp_servers")
    _extend_search_path(parent / "dist" / "mcp_servers")


def _ensure_target_loaded() -> ModuleType:
    global _target_pkg, __all__, __path__
    if _target_pkg is None:
        pkg = importlib.import_module("mcp_servers.noveler")
        _target_pkg = pkg
        try:
            __all__ = list(getattr(pkg, "__all__", []) or [])
            __path__ = list(getattr(pkg, "__path__", []) or [])
            if __spec__ is not None:
                __spec__.submodule_search_locations = __path__
        except Exception:
            pass
    return _target_pkg  # type: ignore[return-value]

# Note: We intentionally avoid adding sys.modules alias entries to keep
# the shim minimal. Attribute access resolves to the real package below.


def _load_submodule(name: str) -> ModuleType:
    # Load submodule from the real MCP package namespace.
    _ensure_target_loaded()
    return importlib.import_module(f"mcp_servers.noveler.{name}")


def __getattr__(name: str) -> Any:
    # Special-case attribute 'noveler' so that noveler.mcp_servers.noveler
    # resolves to the actual mcp_servers.noveler package.
    if name == "noveler":
        return _ensure_target_loaded()
    try:
        return getattr(_ensure_target_loaded(), name)
    except AttributeError:
        return _load_submodule(name)


def __dir__() -> Iterable[str]:
    return sorted(set(globals()) | set(dir(_target_pkg)))


for _submodule in ("tools", "core", "domain", "testing"):
    try:
        _load_submodule(_submodule)
    except ModuleNotFoundError:
        continue
