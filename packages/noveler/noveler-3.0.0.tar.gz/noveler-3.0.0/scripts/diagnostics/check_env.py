# File: scripts/diagnostics/check_env.py
# Purpose: Collect cross-platform diagnostics covering caches, git worktree, and CLI smoke checks.
# Context: Invoked by bin/invoke diagnose so Windows / WSL environments can be validated consistently.

"""Cross-platform environment diagnostics for Noveler development workflows.

This script inspects Python interpreter metadata, cache placement, git worktree
alignment, and representative CLI commands. The results can be emitted as JSON
for automation or formatted text for quick manual reviews.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, MutableMapping, Optional, Sequence

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:  # pragma: no cover - defensive import guard
    from noveler.infrastructure.utils.platform import PlatformInfo, detect_platform
except Exception:  # pragma: no cover - diagnostics should continue even if imports fail
    PlatformInfo = None  # type: ignore[assignment]
    detect_platform = None  # type: ignore[assignment]

try:  # pragma: no cover - guard for optional dependency
    from scripts.tooling.cache_root import CacheRootResult, ensure_cache_root
except Exception as exc:  # pragma: no cover - propagate a clear failure
    raise RuntimeError("Unable to import scripts.tooling.cache_root") from exc

PYTHON_BIN = sys.executable or "python"
DEFAULT_TIMEOUT = 60
DEFAULT_MAX_OUTPUT = 800
CACHE_ENV_MAP = {
    "HYPOTHESIS_STORAGE_DIRECTORY": "hypothesis",
    "MYPY_CACHE_DIR": "mypy",
    "RUFF_CACHE_DIR": "ruff",
    "PIP_CACHE_DIR": "pip",
    "UV_CACHE_DIR": "uv",
    "IMPORT_LINTER_CACHE_DIR": "import_linter",
}


@dataclass
class PythonInfo:
    """Snapshot of the current Python interpreter."""

    executable: str
    version: str
    prefix: str
    base_prefix: str
    cwd: str
    is_venv: bool


@dataclass
class CacheEntry:
    """Single cache directory resolved from environment variables."""

    name: str
    env_var: str
    path: str
    exists: bool


@dataclass
class CacheReport:
    """Summary of cache configuration."""

    root: str
    source: str
    created: bool
    entries: List[CacheEntry]
    pytest_cache_dir: Optional[str]


@dataclass
class GitReport:
    """Details about the git repository configuration."""

    git_dir: Optional[str]
    work_tree: Optional[str]
    core_worktree: Optional[str]
    status_returncode: Optional[int]
    status_output: Optional[str]


@dataclass
class CommandReport:
    """Result from executing a representative command."""

    command: List[str]
    returncode: Optional[int]
    stdout: str
    stderr: str
    timed_out: bool
    error: Optional[str]

    @property
    def success(self) -> bool:
        return (
            not self.timed_out
            and self.error is None
            and self.returncode is not None
            and self.returncode == 0
        )


@dataclass
class EnvironmentReport:
    """Aggregate diagnostics data."""

    python: PythonInfo
    platform: Optional[Dict[str, str]]
    cache: CacheReport
    git: GitReport
    commands: List[CommandReport]

    def to_dict(self) -> Dict[str, object]:
        return {
            "python": asdict(self.python),
            "platform": self.platform,
            "cache": {
                "root": self.cache.root,
                "source": self.cache.source,
                "created": self.cache.created,
                "entries": [asdict(entry) for entry in self.cache.entries],
                "pytest_cache_dir": self.cache.pytest_cache_dir,
            },
            "git": asdict(self.git),
            "commands": [
                {
                    "command": report.command,
                    "returncode": report.returncode,
                    "stdout": report.stdout,
                    "stderr": report.stderr,
                    "timed_out": report.timed_out,
                    "error": report.error,
                }
                for report in self.commands
            ],
        }

    def has_failures(self) -> bool:
        if any(not command.success for command in self.commands):
            return True
        if self.git.status_returncode is not None and self.git.status_returncode != 0:
            return True
        return False


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return f"{text[:limit]}... (truncated {len(text) - limit} chars)"


def gather_python_info() -> PythonInfo:
    return PythonInfo(
        executable=sys.executable or "<unknown>",
        version=sys.version.replace("\n", " "),
        prefix=sys.prefix,
        base_prefix=getattr(sys, "base_prefix", sys.prefix),
        cwd=str(Path.cwd()),
        is_venv=(getattr(sys, "base_prefix", sys.prefix) != sys.prefix),
    )


def _parse_pytest_cache_dir(env: MutableMapping[str, str], cache_root: Path) -> Optional[str]:
    addopts = env.get("PYTEST_ADDOPTS", "")
    match = re.search(r"cache_dir=([^\s]+)", addopts)
    if match:
        return Path(match.group(1)).as_posix()
    potential = cache_root / "pytest"
    return potential.as_posix() if potential.exists() else None


def gather_cache_info(env: MutableMapping[str, str]) -> CacheReport:
    cache_result: CacheRootResult = ensure_cache_root(env)
    cache_root_path = Path(cache_result.path)
    entries: List[CacheEntry] = []

    for env_var, default_dir in CACHE_ENV_MAP.items():
        value = env.get(env_var)
        if value:
            path = Path(value)
        else:
            path = cache_root_path / default_dir
        entries.append(
            CacheEntry(
                name=default_dir,
                env_var=env_var,
                path=path.as_posix(),
                exists=path.exists(),
            )
        )

    pytest_dir = _parse_pytest_cache_dir(env, cache_root_path)

    return CacheReport(
        root=cache_root_path.as_posix(),
        source=cache_result.source,
        created=cache_result.created,
        entries=entries,
        pytest_cache_dir=pytest_dir,
    )


def _run_subprocess(
    command: Sequence[str],
    env: MutableMapping[str, str],
    *,
    timeout: int,
    max_output: int,
) -> CommandReport:
    try:
        local_env = dict(env)
        local_env.setdefault("PYTHONIOENCODING", "utf-8")
        result = subprocess.run(  # noqa: S603 - intentional diagnostic execution
            list(command),
            cwd=str(ROOT_DIR),
            env=local_env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return CommandReport(
            command=list(command),
            returncode=result.returncode,
            stdout=_truncate(result.stdout.strip(), max_output),
            stderr=_truncate(result.stderr.strip(), max_output),
            timed_out=False,
            error=None,
        )
    except FileNotFoundError as exc:
        return CommandReport(
            command=list(command),
            returncode=None,
            stdout="",
            stderr="",
            timed_out=False,
            error=str(exc),
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        return CommandReport(
            command=list(command),
            returncode=None,
            stdout=_truncate(stdout.strip(), max_output),
            stderr=_truncate(stderr.strip(), max_output),
            timed_out=True,
            error="timeout",
        )


def gather_platform_info() -> Optional[Dict[str, str]]:
    if detect_platform is None:
        return None
    info = detect_platform()
    data = {
        "kind": info.kind.name,
        "is_wsl": info.is_wsl,
        "is_windows": info.is_windows,
        "is_unix": info.is_unix,
        "raw_system": info.raw_system,
    }
    data.update(info.details)
    return data


def gather_git_info(env: MutableMapping[str, str], max_output: int, timeout: int) -> GitReport:
    git_dir = None
    work_tree = None
    core_worktree = None
    status_returncode = None
    status_output = None

    git_dir_report = _run_subprocess(["git", "rev-parse", "--git-dir"], env, timeout=timeout, max_output=max_output)
    if git_dir_report.success:
        git_dir = git_dir_report.stdout.strip()
    work_tree_report = _run_subprocess(["git", "rev-parse", "--show-toplevel"], env, timeout=timeout, max_output=max_output)
    if work_tree_report.success:
        work_tree = work_tree_report.stdout.strip()
    core_worktree_report = _run_subprocess(["git", "config", "--get", "core.worktree"], env, timeout=timeout, max_output=max_output)
    if core_worktree_report.returncode == 0:
        core_worktree = core_worktree_report.stdout.strip() or None

    status_report = _run_subprocess(["git", "status", "--short"], env, timeout=timeout, max_output=max_output)
    status_returncode = status_report.returncode
    status_output = status_report.stdout if status_report.stdout else status_report.stderr

    return GitReport(
        git_dir=git_dir,
        work_tree=work_tree,
        core_worktree=core_worktree,
        status_returncode=status_returncode,
        status_output=status_output,
    )


def gather_command_reports(
    env: MutableMapping[str, str],
    extra_commands: Iterable[Sequence[str]],
    *,
    timeout: int,
    max_output: int,
) -> List[CommandReport]:
    default_commands: List[List[str]] = [
        [PYTHON_BIN, str(ROOT_DIR / "scripts" / "tooling" / "invoke.py"), "--list"],
        [PYTHON_BIN, str(ROOT_DIR / "bin" / "noveler"), "--help"],
    ]
    reports: List[CommandReport] = []
    for command in list(default_commands) + [list(cmd) for cmd in extra_commands]:
        reports.append(_run_subprocess(command, env, timeout=timeout, max_output=max_output))
    return reports


def render_text(report: EnvironmentReport) -> str:
    lines: List[str] = []
    lines.append("=== Platform ===")
    if report.platform is None:
        lines.append("- platform detection unavailable (import failed)")
    else:
        for key, value in report.platform.items():
            lines.append(f"- {key}: {value}")

    lines.append("")
    lines.append("=== Python ===")
    lines.append(f"- executable : {report.python.executable}")
    lines.append(f"- version    : {report.python.version}")
    lines.append(f"- prefix     : {report.python.prefix}")
    lines.append(f"- base_prefix: {report.python.base_prefix}")
    lines.append(f"- cwd        : {report.python.cwd}")
    lines.append(f"- in venv    : {report.python.is_venv}")

    lines.append("")
    lines.append("=== Caches ===")
    lines.append(f"- root   : {report.cache.root} (source={report.cache.source}, created={report.cache.created})")
    if report.cache.pytest_cache_dir:
        lines.append(f"- pytest : {report.cache.pytest_cache_dir}")
    for entry in report.cache.entries:
        status = "exists" if entry.exists else "missing"
        lines.append(f"  * {entry.env_var} -> {entry.path} ({status})")

    lines.append("")
    lines.append("=== Git ===")
    lines.append(f"- git dir       : {report.git.git_dir or '<unset>'}")
    lines.append(f"- work tree     : {report.git.work_tree or '<unset>'}")
    lines.append(f"- core.worktree : {report.git.core_worktree or '<unset>'}")
    lines.append(f"- status exit   : {report.git.status_returncode}")
    if report.git.status_output:
        for line in report.git.status_output.splitlines():
            lines.append(f"  > {line}")

    lines.append("")
    lines.append("=== Commands ===")
    if not report.commands:
        lines.append("(skipped)")
    else:
        for command in report.commands:
            cmd_text = " ".join(command.command)
            lines.append(f"- {cmd_text}")
            lines.append(f"  exit={command.returncode} timed_out={command.timed_out} error={command.error or 'None'}")
            if command.stdout:
                for line in command.stdout.splitlines():
                    lines.append(f"    {line}")
            if command.stderr:
                for line in command.stderr.splitlines():
                    lines.append(f"    [stderr] {line}")

    return "\n".join(lines)


def parse_args(argv: Optional[Sequence[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect cross-platform diagnostics for Noveler development environments.",
    )
    parser.add_argument("--json", action="store_true", help="Output report as JSON")
    parser.add_argument("--no-commands", action="store_true", help="Skip representative command execution")
    parser.add_argument(
        "--command",
        action="append",
        metavar="CMD",
        help="Additional command (quoted string) to execute; parsed with shlex",
    )
    parser.add_argument(
        "--max-output",
        type=int,
        default=DEFAULT_MAX_OUTPUT,
        help=f"Maximum characters per command/stdout entry (default: {DEFAULT_MAX_OUTPUT})",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Timeout in seconds for each command (default: {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--allow-failures",
        action="store_true",
        help="Always exit 0 even if diagnostics report failures",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    env = os.environ.copy()

    python_info = gather_python_info()
    cache_report = gather_cache_info(env)
    platform_data = gather_platform_info()
    git_report = gather_git_info(env, max_output=args.max_output, timeout=args.timeout)

    extra_commands: List[Sequence[str]] = []
    if args.command:
        import shlex

        for command in args.command:
            extra_commands.append(shlex.split(command))

    command_reports: List[CommandReport] = []
    if not args.no_commands:
        command_reports = gather_command_reports(
            env,
            extra_commands,
            timeout=args.timeout,
            max_output=args.max_output,
        )

    report = EnvironmentReport(
        python=python_info,
        platform=platform_data,
        cache=cache_report,
        git=git_report,
        commands=command_reports,
    )

    if args.json:
        payload = json.dumps(report.to_dict(), ensure_ascii=False, indent=2).encode("utf-8")
        sys.stdout.buffer.write(payload + b"\n")
    else:
        print(render_text(report))

    if report.has_failures() and not args.allow_failures:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
