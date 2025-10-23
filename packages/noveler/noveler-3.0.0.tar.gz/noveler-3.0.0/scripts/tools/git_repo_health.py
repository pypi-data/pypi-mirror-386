#!/usr/bin/env python3
# File: scripts/tools/git_repo_health.py
# Purpose: Diagnose repository gitdir health (esp. external gitdir like ~/.git-noveler)
#          and report JSON for LLM/CI. Optional clean actions are opt-in.
#
# Checks
# - .git pointer (gitdir: PATH) validity
# - gitdir writability (create/delete temp file)
# - presence of index.lock and gc.log
# - summary status
#
# Options
# --gitdir PATH      Override detected gitdir
# --json             Emit JSON only (default)
# --clean-locks      Remove stale index.lock (if exists)
# --clean-gc-log     Remove gc.log (if exists)
#
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict


def detect_project_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").exists() and (parent / "src").exists():
            return parent
    return Path.cwd()


essential = ["index", "objects", "HEAD"]


def load_gitdir(project_root: Path) -> Path | None:
    dotgit = project_root / ".git"
    try:
        content = dotgit.read_text(encoding="utf-8", errors="ignore")
        if content.startswith("gitdir:"):
            p = content.split(":", 1)[1].strip()
            return Path(p)
    except Exception:
        pass
    # fallback: bare .git directory
    if dotgit.is_dir():
        return dotgit
    return None


def check_writable(path: Path) -> tuple[bool, str | None]:
    try:
        path.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix="githealth_", dir=str(path), delete=True) as _:
            pass
        return True, None
    except Exception as e:
        return False, str(e)


def run_checks(gitdir: Path) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "gitdir": str(gitdir),
        "exists": gitdir.exists(),
        "is_dir": gitdir.is_dir(),
        "writable": False,
        "writable_error": None,
        "index_lock": None,
        "gc_log": None,
        "essential_present": {},
        "status": "unknown",
    }

    if gitdir.exists():
        ok, err = check_writable(gitdir)
        data["writable"] = ok
        data["writable_error"] = err

        index_lock = gitdir / "index.lock"
        gc_log = gitdir / "gc.log"
        data["index_lock"] = str(index_lock) if index_lock.exists() else None
        data["gc_log"] = str(gc_log) if gc_log.exists() else None

        for name in essential:
            data["essential_present"][name] = (gitdir / name).exists()

        if not data["exists"]:
            data["status"] = "missing"
        elif not data["is_dir"]:
            data["status"] = "invalid"
        elif not all(data["essential_present"].values()):
            data["status"] = "degraded"
        elif not data["writable"]:
            data["status"] = "readonly"
        elif data["index_lock"] or data["gc_log"]:
            data["status"] = "needs_cleanup"
        else:
            data["status"] = "healthy"
    else:
        data["status"] = "missing"

    return data


def apply_cleanup(gitdir: Path, clean_locks: bool, clean_gc: bool) -> Dict[str, Any]:
    result: Dict[str, Any] = {"removed": [], "errors": []}
    try:
        if clean_locks:
            p = gitdir / "index.lock"
            if p.exists():
                p.unlink()
                result["removed"].append(str(p))
    except Exception as e:
        result["errors"].append({"path": str(gitdir / "index.lock"), "error": str(e)})
    try:
        if clean_gc:
            p = gitdir / "gc.log"
            if p.exists():
                p.unlink()
                result["removed"].append(str(p))
    except Exception as e:
        result["errors"].append({"path": str(gitdir / "gc.log"), "error": str(e)})
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check gitdir health and optionally cleanup stale files")
    parser.add_argument("--gitdir", default=None, help="Override detected gitdir path")
    parser.add_argument("--json", action="store_true", help="Emit JSON only (default true)")
    parser.add_argument("--clean-locks", action="store_true", help="Remove index.lock if present")
    parser.add_argument("--clean-gc-log", action="store_true", help="Remove gc.log if present")
    args = parser.parse_args(argv)

    root = detect_project_root()
    gd = Path(args.gitdir) if args.gitdir else load_gitdir(root)
    if gd is None:
        out = {"gitdir": None, "status": "not_detected", "project_root": str(root)}
        print(json.dumps(out, ensure_ascii=False))
        return 0

    before = run_checks(gd)
    cleanup = None
    if args.clean_locks or args.clean_gc_log:
        cleanup = apply_cleanup(gd, args.clean_locks, args.clean_gc_log)
    after = run_checks(gd)

    payload = {
        "project_root": str(root),
        "before": before,
        "cleanup": cleanup,
        "after": after,
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
