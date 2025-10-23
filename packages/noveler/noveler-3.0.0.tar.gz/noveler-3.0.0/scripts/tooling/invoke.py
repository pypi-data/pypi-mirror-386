# File: scripts/tooling/invoke.py
# Purpose: Provide a Windows-friendly alternative to Makefile targets with Python-first execution.
# Context: Acts as the main entrypoint for bin/invoke wrappers to keep automation consistent across shells.

"""Cross-platform task runner for common project automation.

This module implements a Python-native substitute for frequently used Makefile
targets so Windows installations without GNU Make can execute the same
automation as WSL users. Tasks spawn subprocesses via ``sys.executable`` and
normalise environment defaults such as cache locations and LLM reporting flags.
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, MutableMapping, Sequence

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.tooling.cache_root import CacheRootResult, ensure_cache_root

PYTHON_BIN = sys.executable or "python"


@dataclass(frozen=True)
class TaskDefinition:
    """Metadata for an invoke task."""

    name: str
    description: str
    handler: Callable[[Sequence[str], MutableMapping[str, str]], int]
    allow_args: bool = False


def _log(message: str) -> None:
    """Emit a lightweight status line."""

    print(f"[invoke] {message}")


def _quoted(command: Sequence[str]) -> str:
    """Return a shell-escaped representation of *command*."""

    return " ".join(shlex.quote(part) for part in command)


def _run(command: Sequence[str], env: MutableMapping[str, str]) -> int:
    """Execute *command* inside the repository root with *env*."""

    _log(f"run {_quoted(command)}")
    completed = subprocess.run(
        list(command),
        cwd=str(ROOT_DIR),
        env=dict(env),
        check=False,
    )
    return completed.returncode


def _python_command(*parts: str) -> list[str]:
    """Build a python invocation for the relative path described by *parts*."""

    script_path = ROOT_DIR.joinpath(*parts)
    return [PYTHON_BIN, str(script_path)]


def _ensure_report_defaults(env: MutableMapping[str, str]) -> Path:
    """Ensure LLM reporting defaults and output directory exist."""

    env.setdefault("LLM_REPORT", "1")
    env.setdefault("LLM_REPORT_DIR", "reports")
    env.setdefault("LLM_REPORT_FORMAT", "jsonl,txt")
    report_dir = Path(env["LLM_REPORT_DIR"])
    if not report_dir.is_absolute():
        report_dir = ROOT_DIR / report_dir
    report_dir.mkdir(parents=True, exist_ok=True)
    return report_dir


def _run_ensure_dist_wrapper(env: MutableMapping[str, str]) -> int:
    """Invoke the dist wrapper bootstrapper prior to running tests."""

    return _run(_python_command("scripts", "ci", "ensure_dist_wrapper.py"), env)


def _unexpected_args(name: str, args: Sequence[str]) -> int:
    """Report unexpected arguments for a task."""

    _log(f"{name} does not accept extra arguments: {args}")
    return 2


def _task_build(args: Sequence[str], env: MutableMapping[str, str]) -> int:
    if args:
        return _unexpected_args("build", args)

    # Run main build
    code = _run(_python_command("scripts", "build.py"), env)
    if code != 0:
        return code

    # Sync global slash commands after successful build
    _log("Syncing global slash commands...")
    sync_code = _run(
        _python_command("scripts", "setup", "build_slash_commands.py") + ["--sync-global"],
        env
    )
    if sync_code != 0:
        _log("Warning: Slash command sync failed (non-fatal)")

    return code


def _task_test(args: Sequence[str], env: MutableMapping[str, str]) -> int:
    _ensure_report_defaults(env)
    code = _run_ensure_dist_wrapper(env)
    if code != 0:
        return code
    command = _python_command("scripts", "tooling", "test_runner.py")
    if args:
        command.append("--")
        command.extend(args)
    return _run(command, env)




def _task_test_smoke(args: Sequence[str], env: MutableMapping[str, str]) -> int:
    command = _python_command("scripts", "diagnostics", "run_smoke_suite.py")
    command.extend(args)
    return _run(command, env)
def _task_test_fast(args: Sequence[str], env: MutableMapping[str, str]) -> int:
    _ensure_report_defaults(env)
    command = _python_command("scripts", "run_pytest.py")
    command.extend(["-m", "not slow", "--durations=10", "-q"])
    command.extend(args)
    return _run(command, env)


def _task_test_slow(args: Sequence[str], env: MutableMapping[str, str]) -> int:
    _ensure_report_defaults(env)
    command = _python_command("scripts", "run_pytest.py")
    command.extend(["-m", "slow", "--maxfail=1", "--durations=10", "-q"])
    command.extend(args)
    return _run(command, env)


def _task_test_last(args: Sequence[str], env: MutableMapping[str, str]) -> int:
    _ensure_report_defaults(env)
    code = _run_ensure_dist_wrapper(env)
    if code != 0:
        return code
    command = _python_command("scripts", "run_pytest.py")
    command.extend(["-q", "--last-failed", "-x"])
    command.extend(args)
    return _run(command, env)


def _task_test_changed(args: Sequence[str], env: MutableMapping[str, str]) -> int:
    parser = argparse.ArgumentParser(
        prog="invoke test-changed",
        description="Run pytest for tests touched in the current diff.",
    )
    parser.add_argument("--range", dest="range_expr", help="Git range passed to --range")
    parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="Additional pytest arguments (prefix with -- to separate)",
    )
    parsed = parser.parse_args(list(args))

    _ensure_report_defaults(env)
    command = _python_command("scripts", "run_pytest.py")
    command.extend(["-q", "--changed"])
    if parsed.range_expr:
        command.extend(["--range", parsed.range_expr])
    extra = list(parsed.pytest_args)
    if extra and extra[0] == "--":
        extra = extra[1:]
    command.extend(extra)
    return _run(command, env)


def _task_lint(args: Sequence[str], env: MutableMapping[str, str]) -> int:
    if args:
        return _unexpected_args("lint", args)

    for tool, command in (
        ("ruff", ["ruff", "check"]),
        ("mypy", ["mypy"]),
    ):
        try:
            result = subprocess.run(
                command,
                cwd=str(ROOT_DIR),
                env=dict(env),
                check=False,
            )
        except FileNotFoundError:
            _log(f"[skip] {tool} not installed")
            continue
        if result.returncode != 0:
            return result.returncode
    return 0


def _task_lint_imports(args: Sequence[str], env: MutableMapping[str, str]) -> int:
    if args:
        return _unexpected_args("lint-imports", args)

    try:
        result = subprocess.run(
            ["lint-imports"],
            cwd=str(ROOT_DIR),
            env=dict(env),
            check=False,
        )
        if result.returncode == 0:
            return 0
    except FileNotFoundError:
        pass

    code = (
        "import importlib.util as u, sys\n"
        "spec = u.find_spec('importlinter')\n"
        "if spec is None:\n"
        "    print('[lint-imports] not available: skipping')\n"
        "else:\n"
        "    print('[lint-imports] importlinter installed but CLI not found: install console script to run contracts')\n"
    )
    fallback = [PYTHON_BIN, "-c", code]
    return _run(fallback, env)


def _task_validate_templates(args: Sequence[str], env: MutableMapping[str, str]) -> int:
    if args:
        return _unexpected_args("validate-templates", args)

    command_env = dict(env)
    command_env["LLM_FAST_CLEANUP"] = "1"
    command_env["LLM_REPORT"] = "0"
    command = _python_command("scripts", "run_pytest.py")
    command.extend(["-q", "tests/unit/templates/test_quality_check_schema_v2.py"])
    return _run(command, command_env)




def _task_diagnose(args: Sequence[str], env: MutableMapping[str, str]) -> int:
    command = _python_command("scripts", "diagnostics", "check_env.py")
    command.extend(args)
    return _run(command, env)

def _task_validate_artifacts(args: Sequence[str], env: MutableMapping[str, str]) -> int:
    if args:
        return _unexpected_args("validate-artifacts", args)

    command = _python_command("scripts", "validate_artifacts.py")
    command.extend(
        [
            "--manifest",
            "docs/examples/acceptance/validation_manifest.yaml",
            "--output-prefix",
            "acceptance_validation_ci",
        ]
    )
    return _run(command, env)


def _ensure_temp_ci() -> Path:
    path = ROOT_DIR / "temp" / "ci"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _task_impact_audit(args: Sequence[str], env: MutableMapping[str, str]) -> int:
    if args:
        return _unexpected_args("impact-audit", args)

    _ensure_temp_ci()
    command = _python_command("scripts", "tools", "impact_audit.py")
    command.extend(["--output", "temp/ci/impact-summary.md"])
    return _run(command, env)


def _task_ci(args: Sequence[str], env: MutableMapping[str, str]) -> int:
    if args:
        return _unexpected_args("ci", args)

    pipeline = [
        "lint",
        "lint-imports",
        "validate-templates",
        "validate-artifacts",
        "test",
        "impact-audit",
    ]
    for name in pipeline:
        task = TASKS[name]
        _log(f"== {name} ==")
        code = task.handler([], env)
        if code != 0:
            return code
    _log("✅ Local CI completed")
    return 0


def _build_tasks() -> Dict[str, TaskDefinition]:
    return {
        "build": TaskDefinition("build", "Build distribution artifacts (scripts/build.py)", _task_build),
        "test": TaskDefinition("test", "Run pytest suite with common defaults", _task_test, allow_args=True),
        "test-smoke": TaskDefinition("test-smoke", "Run standardized smoke pytest suite", _task_test_smoke, allow_args=True),
        "test-fast": TaskDefinition("test-fast", "Run pytest without slow tests", _task_test_fast, allow_args=True),
        "test-slow": TaskDefinition("test-slow", "Run only slow-marked pytest cases", _task_test_slow, allow_args=True),
        "test-last": TaskDefinition("test-last", "Re-run last failed pytest cases", _task_test_last, allow_args=True),
        "test-changed": TaskDefinition("test-changed", "Run pytest for files changed in git", _task_test_changed, allow_args=True),
        "lint": TaskDefinition("lint", "Run code quality linters", _task_lint),
        "lint-imports": TaskDefinition("lint-imports", "Validate import contracts", _task_lint_imports),
        "validate-templates": TaskDefinition("validate-templates", "Run schema validation smoke tests", _task_validate_templates),
        "validate-artifacts": TaskDefinition("validate-artifacts", "Validate acceptance artifact manifest", _task_validate_artifacts),
        "diagnose": TaskDefinition("diagnose", "Run cross-platform environment diagnostics", _task_diagnose, allow_args=True),
        "impact-audit": TaskDefinition("impact-audit", "Generate impact summary report", _task_impact_audit),
        "ci": TaskDefinition("ci", "Run the default local CI pipeline", _task_ci),
    }


TASKS = _build_tasks()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Invoke common project tasks without relying on GNU Make.",
    )
    parser.add_argument("--list", action="store_true", help="List available tasks")
    parser.add_argument("task", nargs="?", choices=sorted(TASKS))
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments forwarded to the chosen task")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    parsed = parser.parse_args(argv)

    env = os.environ.copy()
    cache_result: CacheRootResult = ensure_cache_root(env)
    if cache_result.source != "env":
        _log(f"cache root -> {cache_result.path} ({cache_result.source})")

    if parsed.list:
        width = max((len(name) for name in TASKS), default=0)
        for name in sorted(TASKS):
            task = TASKS[name]
            padding = " " * (width - len(name))
            print(f"{name}{padding}  {task.description}")
        return 0

    if not parsed.task:
        parser.error("task argument is required unless --list is provided")

    extras = list(parsed.args)
    if extras and extras[0] == "--":
        extras = extras[1:]

    task = TASKS[parsed.task]
    if extras and not task.allow_args:
        parser.error(f"{parsed.task} does not accept additional arguments: {extras}")

    return task.handler(extras, env)


if __name__ == "__main__":
    raise SystemExit(main())
