# File: scripts/ci/ensure_dist_wrapper.py
# Purpose: Ensure dist/mcp_servers/noveler/main.py exists for CI/tests.
# Context: Some tests and MCP configs expect a dist wrapper path to exist.
#          This script generates a minimal, safe wrapper that delegates
#          to the src entrypoint without requiring a full production build.

"""CI helper to ensure dist MCP wrapper exists.

This script creates `dist/mcp_servers/noveler/main.py` if missing and writes a
thin wrapper that imports the source entrypoint (`mcp_servers.noveler.main`) by
temporarily adding the project `src/` directory to `sys.path`.

It keeps behavior minimal and reversible:
- Does not modify other dist assets.
- Idempotent: safe to run multiple times.

Side effects:
- Creates directories under `dist/mcp_servers/noveler/` if they do not exist.
"""

from __future__ import annotations

import os
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parents[2]
    dist_dir = project_root / "dist" / "mcp_servers" / "noveler"
    dist_dir.mkdir(parents=True, exist_ok=True)

    wrapper_path = dist_dir / "main.py"

    # Minimal, robust wrapper that executes the src entrypoint.
    content = """#!/usr/bin/env python3
from __future__ import annotations
import sys, os
from pathlib import Path

# Resolve project root and ensure src is importable
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PROJECT_ROOT / 'src'
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

os.environ.setdefault('PYTHONUNBUFFERED', '1')

def _run() -> int:
    try:
        import asyncio
        from importlib import import_module
        src_main = import_module('mcp_servers.noveler.main')
        if hasattr(src_main, 'main'):
            asyncio.run(src_main.main())
            return 0
    except SystemExit as e:
        return int(getattr(e, 'code', 0) or 0)
    except Exception:
        # Fallback: presentation runtime direct call
        try:
            import asyncio
            from noveler.presentation.mcp import server_runtime
            asyncio.run(server_runtime.main())
            return 0
        except Exception as e:  # pragma: no cover - best-effort wrapper
            print(f"Wrapper failed to start MCP server: {e}")
            return 1
    return 0

if __name__ == '__main__':
    raise SystemExit(_run())
"""

    # Only write if missing or content changed to avoid unnecessary churn
    if not wrapper_path.exists() or wrapper_path.read_text(encoding="utf-8", errors="ignore") != content:
        wrapper_path.write_text(content, encoding="utf-8")
        try:
            wrapper_path.chmod(0o755)
        except Exception:
            pass

    # Optional: set env hint for prod runs (harmless for tests)
    os.environ.setdefault("NOVEL_PRODUCTION_MODE", "1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
