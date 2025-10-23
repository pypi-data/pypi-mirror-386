#!/usr/bin/env python3
"""
Update MCP client configs for Codex CLI and Claude Code, with safe backups.

Creates/merges the following (non-destructively, with timestamped backups):
- codex.mcp.json (repo root)
- .mcp/config.json (project-local MCP config)
- Claude Code's claude_desktop_config.json (user profile, per-OS path)

Usage examples:
  python scripts/setup/update_mcp_configs.py              # update all
  python scripts/setup/update_mcp_configs.py --codex      # only codex.mcp.json
  python scripts/setup/update_mcp_configs.py --project    # only .mcp/config.json
  python scripts/setup/update_mcp_configs.py --claude     # only Claude config
  python scripts/setup/update_mcp_configs.py --dry-run    # show changes, no write
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def detect_project_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").exists() and (parent / "src").exists():
            return parent
    return Path.cwd()


def ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except Exception:
        return {}


def backup_file(path: Path) -> Path:
    backup = path.with_suffix(path.suffix + f".backup_{ts()}")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            shutil.copy2(path, backup)
    except Exception:
        pass
    return backup


def _detect_environment(project_root: Path) -> str:
    """
    Detect whether the environment is development or production.

    Returns:
        "production" if src/ is missing and dist/ exists (dist-only deployment).
        "development" otherwise (default: cloned repo with src/).

    Context: After `make build`, the production artifact contains only `dist/`;
    source tree (`src/`) is not shipped. This detection allows a single
    `ensure_mcp_server_entry()` function to generate correct configs for both.
    """
    src_exists = (project_root / "src").exists()
    dist_exists = (project_root / "dist").exists()

    # Treat as production only if src/ is missing AND dist/ exists
    if not src_exists and dist_exists:
        return "production"
    return "development"


def ensure_mcp_server_entry(
    project_root: Path,
    name: str,
    description: str,
    env: str | None = None,
    command: str | None = None,
) -> dict:
    """
    Generate MCP server entry configuration that works in both dev and prod environments.

    Args:
        project_root: Project root directory.
        name: Display name for the server entry.
        description: Server description.
        env: Explicit environment ("development" or "production").
             If None, auto-detects based on src/ and dist/ presence.
        command: Python executable command. If None:
                 - production: uses sys.executable (absolute path from build time)
                 - development: uses "python" (from PATH during setup)
                 Explicitly specify if custom interpreter needed (e.g., "python3").

    Returns:
        Dictionary suitable for mcpServers[server_key] in MCP config.

    Context:
        - Development: src/mcp_servers/noveler/main.py exists; PYTHONPATH includes src/
        - Production (dist-only): dist/mcp_servers/noveler/main.py exists; src/ is absent
        This single function is the SSOT for MCP server entry generation (per CLAUDE.md).

    Reliability note:
        For production, command defaults to sys.executable to ensure the exact
        Python interpreter used during build is available in the deployed artifact.
        This prevents failures in dist-only environments where PATH may not include
        a python binary, or where only python3/venv-specific paths exist.
    """
    if env is None:
        env = _detect_environment(project_root)

    if env == "production":
        # Production: dist-only deployment
        main_path = project_root / "dist" / "mcp_servers" / "noveler" / "main.py"
        python_path = os.pathsep.join([str(project_root / "dist"), str(project_root)])
        # Default to sys.executable for production to ensure reliability
        # (use exact interpreter from build time, not PATH lookup)
        if command is None:
            command = sys.executable
    else:
        # Development: src/ is present
        main_path = project_root / "src" / "mcp_servers" / "noveler" / "main.py"
        python_path = os.pathsep.join([str(project_root), str(project_root / "src")])
        # Default to "python" for development (allows flexibility during setup)
        if command is None:
            command = "python"

    return {
        "name": name or "Noveler MCP",
        "type": "stdio",
        "command": command,
        "args": ["-u", str(main_path)],
        "env": {
            "PYTHONPATH": python_path,
            "PYTHONUNBUFFERED": "1",
            "NOVEL_PRODUCTION_MODE": "1",
            "MCP_STDIO_SAFE": "1",
        },
        "cwd": str(project_root),
        "description": description or "Noveler MCP server (writing/quality tools)",
    }


def merge_mcp_server(config: dict, server_key: str, server_entry: dict) -> dict:
    cfg = dict(config or {})
    mcp = cfg.get("mcpServers") or {}
    existing = mcp.get(server_key) or {}
    # shallow merge, do not drop unknown keys
    merged = {**existing, **server_entry}
    mcp[server_key] = merged
    cfg["mcpServers"] = mcp
    return cfg


def claude_config_paths() -> list[Path]:
    system = platform.system()
    home = Path.home()
    paths: list[Path] = []
    if system == "Windows":
        paths.extend([
            home / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json",
            Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json",
        ])
    elif system == "Darwin":
        paths.extend([
            home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
        ])
    else:
        paths.extend([
            home / ".config" / "claude" / "claude_desktop_config.json",
            home / ".claude" / "claude_desktop_config.json",
        ])
    return paths


def write_json(path: Path, data: dict, dry_run: bool) -> None:
    if dry_run:
        print(f"[dry-run] write {path}")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ wrote: {path}")


def update_codex_config(project_root: Path, server_key: str, dry_run: bool, name: str, description: str) -> None:
    path = project_root / "codex.mcp.json"
    data = load_json(path)
    backup_file(path)
    merged = merge_mcp_server(data, server_key, ensure_mcp_server_entry(project_root, name, description))
    write_json(path, merged, dry_run)


def update_project_mcp_config(project_root: Path, server_key: str, dry_run: bool, name: str, description: str) -> None:
    path = project_root / ".mcp" / "config.json"
    data = load_json(path)
    backup_file(path)
    merged = merge_mcp_server(data, server_key, ensure_mcp_server_entry(project_root, name, description))
    write_json(path, merged, dry_run)


def update_claude_config(project_root: Path, server_key: str, dry_run: bool, name: str, description: str) -> None:
    # Find first existing path or default to primary location on each platform
    paths = claude_config_paths()
    path = next((p for p in paths if p.exists()), paths[0])
    data = load_json(path)
    backup_file(path)
    merged = merge_mcp_server(data, server_key, ensure_mcp_server_entry(project_root, name, description))
    write_json(path, merged, dry_run)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Update MCP configs for Codex and Claude Code with backups")
    g = p.add_mutually_exclusive_group(required=False)
    g.add_argument("--codex", action="store_true", help="Update only codex.mcp.json")
    g.add_argument("--project", action="store_true", help="Update only .mcp/config.json")
    g.add_argument("--claude", action="store_true", help="Update only Claude's claude_desktop_config.json")
    p.add_argument("--server-key", default="noveler", help="mcpServers key (default: noveler)")
    p.add_argument("--name", default="Noveler MCP", help="Display name for the server entry")
    p.add_argument("--description", default="Noveler MCP server (writing/quality tools)", help="Description for the server entry")
    p.add_argument("--dry-run", action="store_true", help="Show changes without writing files")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    project_root = detect_project_root()
    server_key = args.server_key
    name = args.name
    description = args.description
    print(f"🔧 Updating MCP configs (server={server_key}) in project: {project_root}")

    try:
        if args.codex:
            update_codex_config(project_root, server_key, args.dry_run, name, description)
        elif args.project:
            update_project_mcp_config(project_root, server_key, args.dry_run, name, description)
        elif args.claude:
            update_claude_config(project_root, server_key, args.dry_run, name, description)
        else:
            # Default: update all
            update_codex_config(project_root, server_key, args.dry_run, name, description)
            update_project_mcp_config(project_root, server_key, args.dry_run, name, description)
            update_claude_config(project_root, server_key, args.dry_run, name, description)
        return 0
    except Exception as e:
        print(f"❌ 更新中にエラー: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
