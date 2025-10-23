#!/usr/bin/env python3
"""Noveler minimal CLI entrypoint

Adds `python -m noveler` support and a small `write` subcommand
that uses the existing 18-step writing workflow.

This preserves the existing MCP server entry via `mcp-server`.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

from noveler.presentation.cli.cli_adapter import execute_18_step_writing
from noveler.main import main as mcp_main_entry


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="noveler", add_help=True)
    sub = parser.add_subparsers(dest="cmd")

    # Keep MCP server entry compatible: `python -m noveler mcp-server`
    sub.add_parser("mcp-server", help="Run MCP server entrypoint")

    # Minimal writer: `python -m noveler write 1 --fresh-start`
    p_write = sub.add_parser("write", help="Run 18-step writing flow")
    p_write.add_argument("episode", type=int, help="Episode number (e.g., 1)")
    p_write.add_argument("--fresh-start", action="store_true", help="Kept for compatibility; existing files are backed up")
    p_write.add_argument("--dry-run", action="store_true", help="Do not write files; output only")

    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = _build_parser()
    args = parser.parse_args(argv)

    # No subcommand -> show help
    if args.cmd is None:
        parser.print_help()
        return 2

    if args.cmd == "mcp-server":
        # Delegate to existing entry
        return mcp_main_entry()

    if args.cmd == "write":
        episode = int(args.episode)
        dry_run = bool(args.dry_run)
        # project_root: current working directory where the project (with プロジェクト設定.yaml) lives
        project_root = os.getcwd()

        async def _run() -> int:
            try:
                result = await execute_18_step_writing(episode=episode, dry_run=dry_run, project_root=project_root)
                return 0 if result.get("success") else 1
            except Exception as e:  # noqa: BLE001
                # Avoid Rich Console dependencies here; let inner functions do fancy printing
                print(f"❌ 実行エラー: {e}")
                return 1

        return asyncio.run(_run())

    # Unknown command (should not happen due to argparse)
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
