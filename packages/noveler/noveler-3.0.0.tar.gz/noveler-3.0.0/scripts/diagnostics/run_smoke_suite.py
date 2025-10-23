# File: scripts/diagnostics/run_smoke_suite.py
# Purpose: Automate smoke-level pytest execution via invoke for Windows/WSL parity checks.
# Context: Scheduled by Task Scheduler / cron to keep cross-environment test feedback consistent.

"""Execute smoke-level pytest runs via `bin/invoke test` for cross-platform monitoring.

This helper wraps the invoke task so that Windows (PowerShell) and WSL
installations reuse the same smoke command. Results are persisted in JSON/TXT
under `reports/smoke/`, ready for weekly review dashboards or alerts.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import MutableMapping, Sequence

ROOT_DIR = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT_DIR / "reports" / "smoke"
INVOKE_PATH = ROOT_DIR / "scripts" / "tooling" / "invoke.py"
PYTHON_BIN = sys.executable or "python"


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _default_json_path() -> Path:
    return REPORT_DIR / f"smoke_{_timestamp()}.json"


def _default_log_path() -> Path:
    return REPORT_DIR / f"smoke_{_timestamp()}.log"


def _prepare_environment(env: MutableMapping[str, str]) -> MutableMapping[str, str]:
    prepared = dict(env)
    prepared.setdefault("PYTHONIOENCODING", "utf-8")
    prepared.setdefault("PYTHONUTF8", "1")
    prepared.setdefault("LLM_REPORT", "0")
    prepared.setdefault("NOVELER_SMOKE", "1")
    return prepared


def _invoke_smoke(marker: str, target: str, env: MutableMapping[str, str], timeout: int) -> subprocess.CompletedProcess[str]:
    command = [
        PYTHON_BIN,
        str(INVOKE_PATH),
        "test",
        "--",
        "--k",
        marker,
        "-q",
        target,
    ]
    return subprocess.run(  # noqa: S603 - trusted invoke call
        command,
        cwd=str(ROOT_DIR),
        env=_prepare_environment(env),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )


def _write_file(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding="utf-8")


def run(marker: str, target: str, timeout: int, json_path: Path | None, log_path: Path | None) -> int:
    env = os.environ.copy()
    result = _invoke_smoke(marker, target, env, timeout)

    payload = {
        "timestamp_utc": _timestamp(),
        "marker": marker,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }

    json_target = json_path or _default_json_path()
    log_target = log_path or _default_log_path()

    _write_file(json_target, json.dumps(payload, ensure_ascii=False, indent=2))

    log_lines = [
        f"[smoke] marker={marker}",
        f"returncode={result.returncode}",
        "--- stdout ---",
        result.stdout.strip(),
        "--- stderr ---",
        result.stderr.strip(),
        "",
    ]
    _write_file(log_target, "\n".join(log_lines))

    if result.returncode != 0:
        print(f"Smoke run failed (marker={marker}). See {json_target} / {log_target}", file=sys.stderr)
        return result.returncode or 1

    print(f"Smoke run succeeded (marker={marker}). Results -> {json_target}")
    return 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run smoke-level pytest via invoke and persist results.",
    )
    parser.add_argument(
        "--marker",
        default="smoke",
        help="pytest -k marker to execute (default: smoke)",
    )
    parser.add_argument(
        "--target",
        default="tests/smoke",
        help="Test directory or nodeid to execute (default: tests/smoke)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=3600,
        help="Timeout in seconds for the smoke run (default: 3600)",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Optional path for the JSON report (defaults to reports/smoke/smoke_<ts>.json)",
    )
    parser.add_argument(
        "--log-output",
        type=Path,
        help="Optional path for the text log (defaults to reports/smoke/smoke_<ts>.log)",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    args = parse_args()
    json_target = args.json_output
    log_target = args.log_output
    raise SystemExit(run(args.marker, args.target, args.timeout, json_target, log_target))
