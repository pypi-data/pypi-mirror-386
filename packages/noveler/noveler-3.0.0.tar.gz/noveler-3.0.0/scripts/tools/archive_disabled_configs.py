#!/usr/bin/env python3
"""Archive disabled configs and backups into a standardized folder.

Usage:
  python scripts/tools/archive_disabled_configs.py \
    --project-root . \
    --dest archive/disabled_configs \
    --patterns "*.disabled.json,*.backup" \
    --dry-run

- Moves files matching the patterns into `{dest}/{YYYYMMDD}/` while
  preserving relative directory structure.
- Skips common directories (e.g., .git, dist, .mcp cache).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import fnmatch
import shutil
from pathlib import Path
import os
from typing import Iterable


SKIP_DIRS = {".git", "__pycache__", ".mcp", ".tmp", "dist", "build"}


def iter_files(root: Path, patterns: list[str]) -> Iterable[Path]:
    """Robust file iterator that skips problematic/broken directories."""
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        # prune skip dirs
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        # also prune hidden heavy dirs quickly
        dirnames[:] = [d for d in dirnames if not d.startswith(".") or d == ".noveler"]
        for name in filenames:
            try:
                if any(fnmatch.fnmatch(name, pat) for pat in patterns):
                    p = Path(dirpath) / name
                    yield p
            except Exception:
                # ignore transient errors
                continue


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", type=Path, default=Path("."))
    ap.add_argument(
        "--patterns",
        type=str,
        default="*.disabled.json,*.backup",
        help="Comma-separated glob patterns",
    )
    ap.add_argument(
        "--dest",
        type=Path,
        default=Path("archive/disabled_configs"),
        help="Destination base directory",
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    root = args.project_root.resolve()
    patterns = [s.strip() for s in str(args.patterns).split(",") if s.strip()]
    date_dir = _dt.datetime.now().strftime("%Y%m%d")
    base_dest = (args.dest / date_dir).resolve()
    base_dest.mkdir(parents=True, exist_ok=True)

    moved = 0
    for src in iter_files(root, patterns):
        rel = src.relative_to(root)
        dest_path = base_dest / rel
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        if args.dry_run:
            print(f"[DRY-RUN] move {src} -> {dest_path}")
        else:
            shutil.move(str(src), str(dest_path))
            print(f"moved {src} -> {dest_path}")
            moved += 1

    print(f"✅ Done. candidates={moved if not args.dry_run else 'dry-run'} dest={base_dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
