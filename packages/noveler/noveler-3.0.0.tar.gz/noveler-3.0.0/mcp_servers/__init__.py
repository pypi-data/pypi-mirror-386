"""
Lightweight namespace shim for `mcp_servers`.

Ensures that subpackages located under `src/mcp_servers` are importable even
when the test/runtime environment doesn't prepend `src` to `sys.path`.

This keeps imports like `mcp_servers.noveler` working consistently across
different runners without adding external dependencies.
"""
from __future__ import annotations

from pathlib import Path

# Compose the package search path to include the source layout location.
_here = Path(__file__).resolve().parent
_src_pkg = _here.parent / "src" / "mcp_servers"
_dist_pkg = _here.parent / "dist" / "mcp_servers"

# Package import machinery uses `__path__` to find submodules.
__path__: list[str] = [str(_here)]
if _src_pkg.exists():
    __path__.append(str(_src_pkg))
if _dist_pkg.exists():
    __path__.append(str(_dist_pkg))
