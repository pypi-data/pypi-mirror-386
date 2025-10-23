#!/usr/bin/env python3
# File: scripts/setup/hydrate_slash_commands.py
# Purpose: Hydrate config/slash_commands.yaml from repository/user templates
# Context: SPEC-CLI-050 — keep SSOT at config/slash_commands.yaml, but allow
#          simple, explicit refresh/merge from templates to reduce drift.

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install PyYAML", file=sys.stderr)
    sys.exit(1)


@dataclass
class HydrateOptions:
    templates_dir: Path
    config_path: Path
    run_build: bool
    dry_run: bool
    backup: bool


def detect_project_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").exists() and (parent / "src").exists():
            return parent
    return Path.cwd()


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            raise ValueError(f"YAML root must be a mapping: {path}")
        return data


def _iter_template_files(templates_dir: Path) -> list[Path]:
    if not templates_dir.exists():
        return []
    files = [p for p in templates_dir.glob("*.yaml") if p.is_file()]
    # stable ordering by name
    return sorted(files, key=lambda p: p.name)


def _merge_commands(base_cmds: list[dict[str, Any]], add_cmds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge command lists by `name`.

    - If names collide, entries from `add_cmds` overwrite the entire object.
    - Order is preserved: existing order in base, then new items in add.
    """
    by_name: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for cmd in base_cmds or []:
        name = cmd.get("name")
        if not isinstance(name, str):
            continue
        by_name[name] = cmd
        order.append(name)

    for cmd in add_cmds or []:
        name = cmd.get("name")
        if not isinstance(name, str):
            continue
        if name not in by_name:
            order.append(name)
        by_name[name] = cmd

    return [by_name[n] for n in order]


def hydrate_from_templates(config_path: Path, templates_dir: Path) -> dict[str, Any]:
    # Load current config (SSOT)
    current = _load_yaml(config_path)

    # Collect commands from templates
    files = _iter_template_files(templates_dir)
    merged = dict(current) if current else {}
    merged.setdefault("version", current.get("version", "1.0.0") if current else "1.0.0")
    merged["last_updated"] = datetime.now().strftime("%Y-%m-%d")

    base_cmds = list(current.get("commands", [])) if isinstance(current.get("commands"), list) else []
    for tf in files:
        data = _load_yaml(tf)
        cmds = data.get("commands", []) if isinstance(data, dict) else []
        if not isinstance(cmds, list):
            continue
        base_cmds = _merge_commands(base_cmds, cmds)

    merged["commands"] = base_cmds
    return merged


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def run_build(project_root: Path, *, dry_run: bool) -> int:
    builder = project_root / "scripts" / "setup" / "build_slash_commands.py"
    if not builder.exists():
        print(f"[WARN] Build script not found: {builder}")
        return 0
    import subprocess
    cmd = [sys.executable, str(builder)]
    if dry_run:
        cmd.append("--dry-run")
    return subprocess.run(cmd, check=False).returncode


def parse_args(argv: list[str] | None = None) -> HydrateOptions:
    root = detect_project_root()
    p = argparse.ArgumentParser(description="Hydrate config/slash_commands.yaml from templates")
    p.add_argument("--templates-dir", type=Path, default=root / "templates" / "slash_commands")
    p.add_argument("--config", dest="config_path", type=Path, default=root / "config" / "slash_commands.yaml")
    p.add_argument("--run-build", action="store_true", help="Run build_slash_commands.py after hydration")
    p.add_argument("--dry-run", action="store_true", help="Preview merged YAML without writing")
    p.add_argument("--no-backup", action="store_true", help="Do not create .bak file before overwrite")
    args = p.parse_args(argv)
    return HydrateOptions(
        templates_dir=args.templates_dir,
        config_path=args.config_path,
        run_build=args.run_build,
        dry_run=args.dry_run,
        backup=(not args.no_backup),
    )


def main(argv: list[str] | None = None) -> int:
    opts = parse_args(argv)
    project_root = detect_project_root()

    print(f"[*] Templates: {opts.templates_dir}")
    print(f"[*] Config   : {opts.config_path}")

    merged = hydrate_from_templates(opts.config_path, opts.templates_dir)

    if opts.dry_run:
        print("\n=== DRY RUN: merged config preview ===\n")
        print(json.dumps(merged, ensure_ascii=False, indent=2))
    else:
        if opts.backup and opts.config_path.exists():
            backup = opts.config_path.with_suffix(opts.config_path.suffix + ".bak")
            opts.config_path.replace(backup)
            print(f"[OK] Backup created: {backup}")
        write_yaml(opts.config_path, merged)
        print(f"[OK] Wrote: {opts.config_path}")

    if opts.run_build:
        rc = run_build(project_root, dry_run=opts.dry_run)
        if rc != 0:
            print(f"[ERROR] build_slash_commands.py failed (rc={rc})", file=sys.stderr)
            return rc
        print("[OK] build_slash_commands.py completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

