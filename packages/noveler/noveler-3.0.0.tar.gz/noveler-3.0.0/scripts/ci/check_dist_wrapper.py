#!/usr/bin/env python3
# File: scripts/ci/check_dist_wrapper.py
# Purpose: Verify that the dist MCP wrapper exists and is callable by config.
from __future__ import annotations

import json
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

report = {"root": str(ROOT), "checks": []}

# 1) dist wrapper path
wrapper = ROOT / 'dist' / 'mcp_servers' / 'noveler' / 'main.py'
report["checks"].append({"name": "dist_wrapper_exists", "ok": wrapper.exists(), "path": str(wrapper)})

# 2) project .mcp/config.json references (if present)
project_cfg = ROOT / '.mcp' / 'config.json'
if project_cfg.exists():
    try:
        cfg = json.loads(project_cfg.read_text(encoding='utf-8'))
        mcp = cfg.get('mcpServers', {})
        nov = mcp.get('noveler', {})
        args = nov.get('args', [])
        ok = any('dist/mcp_servers/noveler/main.py' in str(a) for a in args)
        report["checks"].append({"name": "project_mcp_points_to_dist", "ok": ok, "args": args})
    except Exception as e:
        report["checks"].append({"name": "project_mcp_read_error", "ok": False, "error": str(e)})
else:
    report["checks"].append({"name": "project_mcp_missing", "ok": True})

# 3) codex.mcp.json references (if present)
codex_cfg = ROOT / 'codex.mcp.json'
if codex_cfg.exists():
    try:
        cfg = json.loads(codex_cfg.read_text(encoding='utf-8'))
        mcp = cfg.get('mcpServers', {})
        any_ok = False
        for k, v in mcp.items():
            args = v.get('args', []) if isinstance(v, dict) else []
            if any('dist/mcp_servers/noveler/main.py' in str(a) for a in args):
                any_ok = True
                break
        report["checks"].append({"name": "codex_mcp_points_to_dist", "ok": any_ok})
    except Exception as e:
        report["checks"].append({"name": "codex_mcp_read_error", "ok": False, "error": str(e)})
else:
    report["checks"].append({"name": "codex_mcp_missing", "ok": True})

print(json.dumps(report, ensure_ascii=False))

# Gate on strict mode: if STRICT_DIST_WRAPPER=1 and any critical check fails, exit non-zero.
strict = os.environ.get("STRICT_DIST_WRAPPER", "0").strip().lower() in {"1", "true", "yes", "on"}
if strict:
    # critical checks: dist_wrapper_exists, project_mcp_points_to_dist (if project cfg exists),
    # codex_mcp_points_to_dist (if codex cfg exists)
    ok = True
    exists_check = next((c for c in report["checks"] if c.get("name") == "dist_wrapper_exists"), {"ok": False})
    ok = ok and bool(exists_check.get("ok"))
    # If project cfg present, require it to point to dist
    proj_present = not any(c.get("name") == "project_mcp_missing" for c in report["checks"])
    if proj_present:
        proj_check = next((c for c in report["checks"] if c.get("name") == "project_mcp_points_to_dist"), {"ok": True})
        ok = ok and bool(proj_check.get("ok", True))
    # If codex cfg present, require at least one to point to dist
    codex_present = not any(c.get("name") == "codex_mcp_missing" for c in report["checks"])
    if codex_present:
        codex_check = next((c for c in report["checks"] if c.get("name") == "codex_mcp_points_to_dist"), {"ok": True})
        ok = ok and bool(codex_check.get("ok", True))

    sys.exit(0 if ok else 2)

# Non-strict: only warn in JSON; success exit
sys.exit(0)
