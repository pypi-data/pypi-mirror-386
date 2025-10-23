#!/usr/bin/env python3
# File: scripts/run_pytest.py
# Purpose: Single source of truth (SSOT) runner for pytest. Normalizes env,
#          routes all human/LLM/CI invocations through one place, and provides
#          convenience options like --changed/--last-failed.
# Context: Replace ad-hoc `python -m pytest ...` calls with this wrapper.

from __future__ import annotations

import argparse
import json
import os
import shlex
import signal
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
import importlib.util as _util

_SIGALRM_SUPPORTED = hasattr(signal, "SIGALRM")


def _bool_env(val: str | None, default: bool) -> bool:
    if val is None:
        return default
    v = val.strip().lower()
    if v in {"1", "true", "yes", "on"}:  # truthy
        return True
    if v in {"0", "false", "no", "off"}:  # falsey
        return False
    return default


def _project_root() -> Path:
    # scripts/ の親がプロジェクトルート
    return Path(__file__).resolve().parent.parent


def _supports_sigalrm() -> bool:
    """Return True when the current platform exposes signal.SIGALRM."""
    return _SIGALRM_SUPPORTED


def _contains_timeout_flag(args: List[str]) -> bool:
    """Check whether any timeout-method flags are already provided."""
    for token in args:
        if token == "--timeout-method":
            return True
        if token.startswith("--timeout-method="):
            return True
    return False


def _normalize_timeout_name(value: object | None) -> Optional[str]:
    """Normalize timeout method names for comparisons."""
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    return text.lower() or None


def _addopts_contains_timeout_flag(env: dict) -> bool:
    """Check PYTEST_ADDOPTS for an existing timeout flag."""
    addopts = env.get("PYTEST_ADDOPTS", "")
    if not addopts:
        return False
    try:
        tokens = shlex.split(addopts)
    except ValueError:
        return "--timeout-method" in addopts
    return _contains_timeout_flag(tokens)


def _normalize_env(env: dict) -> dict:
    root = _project_root()
    src = root / "src"

    # PYTHONPATH: prepend project root and src
    pp = env.get("PYTHONPATH", "")
    parts = [str(root), str(src)] + ([pp] if pp else [])
    env["PYTHONPATH"] = os.pathsep.join(parts)

    # MCP / stdout safety
    env.setdefault("MCP_LIGHTWEIGHT_DEFAULT", "1")
    env.setdefault("MCP_STRICT_STDOUT", "1")
    env.setdefault("MCP_STDIO_SAFE", "1")
    env.setdefault("PYTHONUNBUFFERED", "1")

    # LLM reporting (summary text/jsonl handled elsewhere if present)
    env.setdefault("LLM_REPORT", "1")
    env.setdefault("LLM_REPORT_DIR", "reports")
    env.setdefault("LLM_REPORT_FORMAT", "jsonl,txt")

    # Suppress noisy progress prints from E2E/session hooks by default
    env.setdefault("LLM_SILENT_PROGRESS", "1")

    # Mark that we used the wrapper (tests/conftest.py can show hint otherwise)
    env["LLM_TEST_RUNNER"] = "1"

    default_timeout = "signal" if _SIGALRM_SUPPORTED else "thread"
    configured_timeout = env.setdefault("PYTEST_TIMEOUT_METHOD", default_timeout)
    configured_timeout_normalized = _normalize_timeout_name(configured_timeout)
    if not _SIGALRM_SUPPORTED and configured_timeout_normalized != "thread":
        env["PYTEST_TIMEOUT_METHOD"] = "thread"

    return env


def _collect_changed_tests(git_range: str | None) -> list[str]:
    # Return list of test files under tests/ changed in the given range
    try:
        if git_range:
            cmd = ["git", "diff", "--name-only", "--diff-filter=ACMRTUXB", git_range]
        else:
            cmd = ["git", "diff", "--name-only", "--diff-filter=ACMRTUXB"]
        cp = subprocess.run(cmd, cwd=_project_root(), capture_output=True, text=True, check=False)
        files = [l.strip() for l in cp.stdout.splitlines() if l.strip()]
        tests = [f for f in files if f.startswith("tests/") and f.endswith(".py")]
        return tests
    except Exception:
        return []


def _xdist_available() -> bool:
    return _util.find_spec("xdist") is not None


def _read_last_nonempty_line(path: Path) -> str | None:
    try:
        if not path.exists():
            return None
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return None

    for line in reversed(lines):
        if line.strip():
            return line
    return None


def _read_summary_run_id(report_dir: Path) -> Optional[str]:
    summary_path = report_dir / "llm_summary.jsonl"
    last_line = _read_last_nonempty_line(summary_path)
    if not last_line:
        return None
    try:
        data = json.loads(last_line)
    except Exception:
        return None
    run_id = data.get("run_id")
    if isinstance(run_id, str) and run_id.strip():
        return run_id
    return None


def _verify_directory_writable(path: Path, label: str) -> Path:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write_probe"
        probe.write_bytes(b"")
        probe.unlink(missing_ok=True)
        return path
    except OSError as exc:
        raise RuntimeError(
            f"[run_pytest] {label} に書き込めません: {path} ({exc.strerror or exc})"
        ) from exc


def _prepare_log_environment(env: dict[str, str]) -> tuple[bool, Optional[str], Optional[Path]]:
    attach_logs = _bool_env(env.get("LLM_ATTACH_LOGS"), True)
    if not attach_logs:
        return False, None, None

    report_dir = Path(env["LLM_REPORT_DIR"]).expanduser().resolve()
    report_dir = _verify_directory_writable(report_dir, "LLM_REPORT_DIR")
    env["LLM_REPORT_DIR"] = str(report_dir)
    run_id = env.get("LLM_RUN_ID") or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    env.setdefault("LLM_RUN_ID", run_id)
    default_log_dir = report_dir / "artifacts" / run_id
    env.setdefault("NOVEL_LOG_DIR", str(default_log_dir))
    env.setdefault("NOVEL_LOG_FILE", "pytest.log")

    log_dir_candidate = Path(env.get("NOVEL_LOG_DIR", str(default_log_dir))).expanduser()
    if not log_dir_candidate.is_absolute():
        log_dir_candidate = report_dir / log_dir_candidate
    log_dir_candidate = _verify_directory_writable(log_dir_candidate, "NOVEL_LOG_DIR")
    env["NOVEL_LOG_DIR"] = str(log_dir_candidate)

    return True, env.get("LLM_RUN_ID"), log_dir_candidate.resolve()


def _maybe_align_log_dir(report_dir: Path, log_dir: Path, run_id: str) -> Path:
    try:
        log_dir.relative_to(report_dir)
    except ValueError:
        return log_dir

    desired_dir = report_dir / "artifacts" / run_id
    if desired_dir == log_dir:
        return log_dir

    desired_dir_parent = desired_dir.parent
    desired_dir_parent.mkdir(parents=True, exist_ok=True)

    if not desired_dir.exists():
        try:
            log_dir.rename(desired_dir)
            return desired_dir
        except OSError:
            desired_dir.mkdir(parents=True, exist_ok=True)

    desired_dir.mkdir(parents=True, exist_ok=True)
    for source in log_dir.glob("*"):
        destination = desired_dir / source.name
        if destination.exists():
            continue
        try:
            source.replace(destination)
        except Exception:
            continue
    try:
        log_dir.rmdir()
    except OSError:
        pass
    return desired_dir


def _relative_to_report(report_dir: Path, file_path: Path) -> str:
    try:
        return str(file_path.relative_to(report_dir))
    except ValueError:
        return str(file_path)


def _append_log_manifest(report_dir: Path, run_id: str, log_dir: Path) -> None:
    if not log_dir.exists():
        return

    log_files = sorted(log_dir.glob("*.log"))
    if not log_files:
        return

    manifest_path = report_dir / "llm_summary.attachments.jsonl"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    with manifest_path.open("a", encoding="utf-8") as manifest:
        for log_file in log_files:
            record = {
                "run_id": run_id,
                "kind": "pytest-log",
                "path": _relative_to_report(report_dir, log_file),
            }
            manifest.write(json.dumps(record, ensure_ascii=False) + "\n")


def _finalize_log_attachments(env: dict[str, str], report_dir: Path, log_dir: Optional[Path], run_id_hint: Optional[str], attach_logs: bool) -> None:
    if not attach_logs or log_dir is None:
        return

    actual_run_id = _read_summary_run_id(report_dir) or env.get("LLM_RUN_ID") or run_id_hint
    if not actual_run_id:
        return

    finalized_dir = _maybe_align_log_dir(report_dir, log_dir, actual_run_id)
    _append_log_manifest(report_dir, actual_run_id, finalized_dir)


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Unified pytest runner (LLM-aware)")
    parser.add_argument("targets", nargs="*", help="Test paths or nodeids (optional)")
    parser.add_argument("-k", "--k", dest="kexpr", default=None, help="-k expression")
    parser.add_argument("-m", dest="mexpr", default=None, help="-m marker expression")
    parser.add_argument("-x", dest="failfast", action="store_true", help="Stop after first failure")
    parser.add_argument("-q", dest="quiet", action="store_true", help="Quiet mode")
    parser.add_argument("-v", dest="verbosity", action="count", default=0, help="Increase verbosity (-v/-vv/-vvv)")

    parser.add_argument("--last-failed", dest="last_failed", action="store_true", help="Re-run last failed tests first")
    parser.add_argument("--changed", dest="changed", action="store_true", help="Run tests changed in git (filters to tests/*.py)")
    parser.add_argument("--range", dest="range", default=None, help="Git diff range for --changed (e.g., origin/master...HEAD)")

    parser.add_argument("--xdist-auto", dest="xdist_auto", action="store_true", help="Use -n auto if pytest-xdist is available")
    parser.add_argument("--json-only", dest="json_only", action="store_true", help="Print only the final LLM summary JSON to stdout")
    parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Print command and env without execution")
    parser.add_argument("--timeout-method", dest="timeout_method_override", default=None, help="Override pytest-timeout method (e.g., signal, thread)")

    args, unknown = parser.parse_known_args(argv)

    env = _normalize_env(dict(os.environ))
    sigalrm_supported = _supports_sigalrm()

    # Ensure report dir exists before log setup
    report_dir = Path(env["LLM_REPORT_DIR"]).expanduser()
    report_dir.mkdir(parents=True, exist_ok=True)
    report_dir = report_dir.resolve()
    env["LLM_REPORT_DIR"] = str(report_dir)

    try:
        attach_logs, run_id_hint, log_dir = _prepare_log_environment(env)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    # Determine targets
    targets: list[str] = list(args.targets)

    if args.changed:
        changed = _collect_changed_tests(args.range)
        if changed:
            targets = changed
        else:
            # Fallback to last-failed if nothing changed
            args.last_failed = True

    # Base pytest command
    cmd = [sys.executable, "-m", "pytest"]

    if args.quiet and args.verbosity == 0:
        cmd.append("-q")

    if args.verbosity:
        cmd.append("-" + ("v" * args.verbosity))

    if args.kexpr:
        cmd.extend(["-k", args.kexpr])
    if args.mexpr:
        cmd.extend(["-m", args.mexpr])
    if args.failfast:
        cmd.append("-x")

    if args.last_failed:
        cmd.extend(["--ff", "--last-failed"])  # fast feedback

    if args.xdist_auto and _xdist_available():
        cmd.extend(["-n", "auto"])  # parallel if available

    # Targets (default to 'tests' when none specified and no special mode)
    if targets:
        cmd.extend(targets)
    else:
        # run whole suite by default
        cmd.append("-q") if "-q" not in cmd else None
        cmd.append("tests")

    # Pass-through any unknown args to pytest
    if unknown:
        cmd.extend(unknown)

    timeout_override_raw = args.timeout_method_override
    timeout_override_normalized = _normalize_timeout_name(timeout_override_raw)

    if timeout_override_raw is not None:
        if timeout_override_normalized is None:
            env.pop("PYTEST_TIMEOUT_METHOD", None)
        else:
            env["PYTEST_TIMEOUT_METHOD"] = timeout_override_normalized

    timeout_method_env = env.get("PYTEST_TIMEOUT_METHOD")
    timeout_method_normalized = _normalize_timeout_name(timeout_method_env)
    if timeout_method_normalized is None:
        default_timeout = "signal" if sigalrm_supported else "thread"
        timeout_method_normalized = default_timeout
        env["PYTEST_TIMEOUT_METHOD"] = timeout_method_normalized

    if not sigalrm_supported and timeout_method_normalized != "thread":
        if timeout_override_normalized and timeout_override_normalized != "thread":
            print(
                "[run_pytest] --timeout-method 'signal' は現在のプラットフォームでサポートされないため 'thread' にフォールバックします。",
                file=sys.stderr,
            )
        timeout_method_normalized = "thread"
        env["PYTEST_TIMEOUT_METHOD"] = timeout_method_normalized

    timeout_flag_present = _contains_timeout_flag(cmd) or _addopts_contains_timeout_flag(env)
    if timeout_override_raw is not None:
        if not timeout_flag_present:
            cmd.extend(["--timeout-method", timeout_method_normalized])
    elif not sigalrm_supported and not timeout_flag_present:
        cmd.extend(["--timeout-method", timeout_method_normalized])

    if args.dry_run:
        print("[dry-run] cwd=", _project_root())
        print("[dry-run] env overrides:")
        for k in [
            "PYTHONPATH",
            "MCP_LIGHTWEIGHT_DEFAULT",
            "MCP_STRICT_STDOUT",
            "MCP_STDIO_SAFE",
            "PYTHONUNBUFFERED",
            "LLM_REPORT",
            "LLM_REPORT_DIR",
            "LLM_REPORT_FORMAT",
            "LLM_TEST_RUNNER",
        ]:
            print(f"  {k}={env.get(k)}")
        print("[dry-run] cmd=", " ".join(shlex.quote(c) for c in cmd))
        return 0

    # Execute
    import sys as _sys; _sys.stderr.write("[runner] " + " ".join(shlex.quote(c) for c in cmd) + "\n")
    if args.json_only:
        env["LLM_REPORT"] = "1"
        env.setdefault("LLM_REPORT_DIR", "reports")
        cp = subprocess.run(cmd, cwd=_project_root(), env=env, stdout=subprocess.DEVNULL)
        last = _read_last_nonempty_line(report_dir / "llm_summary.jsonl")
        _finalize_log_attachments(env, report_dir, log_dir, run_id_hint, attach_logs)
        print(last or "{}")
        return cp.returncode

    cp = subprocess.run(cmd, cwd=_project_root(), env=env)
    _finalize_log_attachments(env, report_dir, log_dir, run_id_hint, attach_logs)
    return cp.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
