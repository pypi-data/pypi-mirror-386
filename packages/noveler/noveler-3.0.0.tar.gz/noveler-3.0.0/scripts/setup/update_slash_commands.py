#!/usr/bin/env python3
# File: scripts/setup/update_slash_commands.py
# Purpose: Wire chat slash commands (/test, /test-failed, /test-changed) to
#          project test runners by updating local and user-level settings.
# Context: 
#   - Adds Bash permissions for bin/test* into Claude Code settings
#   - Optionally writes a repo-local .codex/commands.json with mappings

from __future__ import annotations

import argparse
import json
import os
import platform
from pathlib import Path
from typing import Any


def detect_project_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").exists() and (parent / "src").exists():
            return parent
    return Path.cwd()


def claude_user_config_paths() -> list[Path]:
    home = Path.home()
    sys = platform.system()
    paths: list[Path] = []
    if sys == "Windows":
        paths.extend([
            home / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json",
            Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json",
        ])
    elif sys == "Darwin":
        paths.extend([
            home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
        ])
    else:
        paths.extend([
            home / ".config" / "claude" / "claude_desktop_config.json",
            home / ".claude" / "claude_desktop_config.json",
        ])
    return paths


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except Exception:
        return {}


def write_json(path: Path, data: dict, dry_run: bool) -> None:
    if dry_run:
        print(f"[dry-run] write {path}")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ wrote: {path}")


BASH_PERMS = [
    "Bash(bin/test:*)",
    "Bash(bin/test-failed:*)",
    "Bash(bin/test-changed:*)",
    "Bash(./bin/test:*)",
    "Bash(./bin/test-failed:*)",
    "Bash(./bin/test-changed:*)",
]


def ensure_permissions(obj: dict) -> dict:
    perms = obj.get("permissions") or {}
    allow = set(perms.get("allow") or [])
    allow.update(BASH_PERMS)
    perms["allow"] = sorted(allow)
    obj["permissions"] = perms
    return obj


def update_repo_local(project_root: Path, dry_run: bool) -> None:
    # Update repo-local Claude settings (optional local runner)
    local = project_root / ".claude" / "settings.local.json"
    data = load_json(local)
    data = ensure_permissions(data)
    write_json(local, data, dry_run)

    # Optional Codex commands mapping (repo-local)
    codex_dir = project_root / ".codex"
    codex_dir.mkdir(exist_ok=True)
    commands = {
        "slashCommands": {
            "/test": "bin/test",
            "/test-failed": "bin/test-failed",
            "/test-changed": "bin/test-changed"
        }
    }
    write_json(codex_dir / "commands.json", commands, dry_run)


def update_user_claude(dry_run: bool) -> None:
    # Update first existing user config; otherwise write to primary path
    paths = claude_user_config_paths()
    target = next((p for p in paths if p.exists()), paths[0])
    data = load_json(target)
    data = ensure_permissions(data)
    write_json(target, data, dry_run)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Wire /test* slash commands to project runners")
    p.add_argument("--dry-run", action="store_true", help="Show changes without writing files")
    p.add_argument("--no-user", action="store_true", help="Skip updating user-level Claude settings")
    p.add_argument("--no-repo", action="store_true", help="Skip updating repo-local files (.claude/.codex)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = detect_project_root()
    print(f"🔧 Update slash commands bindings (project={root})")
    if not args.no_repo:
        update_repo_local(root, args.dry_run)
    if not args.no_user:
        update_user_claude(args.dry_run)
    print("✅ Completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
