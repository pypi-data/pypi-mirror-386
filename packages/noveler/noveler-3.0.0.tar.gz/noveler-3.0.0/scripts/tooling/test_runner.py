# File: scripts/tooling/test_runner.py
# Purpose: Provide a cross-platform entrypoint for invoking the pytest runner.
# Context: Used by bin/test wrappers (Bash/PowerShell) so both Windows and WSL share identical behaviour.

"""Cross-platform pytest runner wrapper.

This small CLI delegates to scripts/run_pytest.py using sys.executable so
that both Unix shells and PowerShell invoke the same Python process without
needing bash-specific tooling.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence

ROOT_DIR = Path(__file__).resolve().parents[2]
RUN_PYTEST = ROOT_DIR / "scripts" / "run_pytest.py"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Execute the unified pytest runner with cross-platform defaults.",
        add_help=False,
    )
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments forwarded to pytest")
    return parser


def _resolve_python() -> str:
    python_bin = sys.executable
    if not python_bin:
        raise RuntimeError("Unable to locate Python executable for test runner")
    return python_bin


def _invoke_pytest(arguments: Sequence[str]) -> int:
    python_bin = _resolve_python()
    env = os.environ.copy()
    completed = subprocess.run(
        [python_bin, str(RUN_PYTEST), *arguments],
        cwd=str(ROOT_DIR),
        env=env,
        check=False,
    )
    return completed.returncode


def main(argv: Sequence[str] | None = None) -> int:
    if not RUN_PYTEST.exists():
        raise FileNotFoundError(f"Expected pytest runner at {RUN_PYTEST}")

    parser = _build_parser()
    parsed = parser.parse_args(argv)

    extra_args = parsed.args
    if extra_args and extra_args[0] == "--":
        extra_args = extra_args[1:]

    return _invoke_pytest(extra_args)


if __name__ == "__main__":
    raise SystemExit(main())
