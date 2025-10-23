# File: scripts/tooling/install_cli.py
# Purpose: Cross-platform installer entrypoint for project tooling.
# Context: Invoked by shell wrappers (bash / PowerShell) to provision dependencies uniformly.

"""Install project dependencies and configure PATH in a cross-platform manner."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

ROOT_DIR = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT_DIR / "scripts"
BIN_DIR = ROOT_DIR / "bin"
REQUIREMENTS_FILE = SCRIPTS_DIR / "requirements.txt"
NOVEL_CONFIG_SCRIPT = SCRIPTS_DIR / "setup" / "novel_config.py"


class InstallError(RuntimeError):
    """Raised when installation prerequisites cannot be satisfied."""


def _title(message: str) -> None:
    print(f"\n{message}")


def _info(message: str) -> None:
    print(f"   {message}")


def _run(command: list[str], *, cwd: Path | None = None) -> None:
    result = subprocess.run(command, cwd=str(cwd) if cwd else None, check=False)
    if result.returncode != 0:
        joined = " ".join(command)
        raise InstallError(f"Command failed ({result.returncode}): {joined}")


def _ensure_python_version() -> None:
    if sys.version_info < (3, 8):
        version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        raise InstallError(f"Python 3.8+ required (detected {version})")


def _install_requirements(extra_args: list[str]) -> None:
    if not REQUIREMENTS_FILE.exists():
        raise InstallError(f"Requirements file not found: {REQUIREMENTS_FILE}")
    command = [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)] + extra_args
    _run(command)


def _ensure_unix_path(bin_dir: Path) -> None:
    shell = Path(os.environ.get("SHELL", "")).name
    candidates: Iterable[Path]
    if shell == "zsh":
        candidates = [Path.home() / ".zshrc"]
    elif shell == "bash":
        candidates = [Path.home() / ".bashrc"]
    else:
        candidates = [Path.home() / ".profile"]

    line = f'export PATH="{bin_dir}:$PATH"'
    for rc in candidates:
        rc.parent.mkdir(parents=True, exist_ok=True)
        if rc.exists() and line in rc.read_text(encoding="utf-8").splitlines():
            _info(f"PATH already configured in {rc}")
            return
        with rc.open("a", encoding="utf-8") as handle:
            handle.write("\n" + line + "\n")
        _info(f"Added PATH entry to {rc}")
        return

    _info("Unable to update shell profile automatically. Please add bin/ to PATH manually.")


def _powershell_profile_candidates() -> list[Path]:
    locations: list[Path] = []
    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        base = Path(user_profile) / "Documents"
        locations.append(base / "PowerShell" / "Microsoft.PowerShell_profile.ps1")
        locations.append(base / "WindowsPowerShell" / "Microsoft.PowerShell_profile.ps1")
    home = Path.home() / "Documents"
    locations.append(home / "PowerShell" / "Microsoft.PowerShell_profile.ps1")
    locations.append(home / "WindowsPowerShell" / "Microsoft.PowerShell_profile.ps1")
    return locations


def _ensure_windows_path(bin_dir: Path) -> None:
    path_text = str(bin_dir)
    line = (
        f"if (-not ($env:PATH -split ';' | Where-Object {{ $_ -eq '{path_text}' }})) {{"
        f" $env:PATH = '{path_text};' + $env:PATH }}"
    )

    for profile in _powershell_profile_candidates():
        profile.parent.mkdir(parents=True, exist_ok=True)
        if profile.exists():
            content = profile.read_text(encoding="utf-8")
            if path_text in content:
                _info(f"PATH already configured in {profile}")
                return
        with profile.open("a", encoding="utf-8") as handle:
            handle.write("\n# Added by install_cli.py\n")
            handle.write(line + "\n")
        _info(f"Added PATH entry to {profile}")
        return

    _info("Unable to update PowerShell profile automatically. Please add bin/ to PATH manually.")


def _ensure_path(bin_dir: Path) -> None:
    os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")
    if os.name == "nt":
        _ensure_windows_path(bin_dir)
    else:
        _ensure_unix_path(bin_dir)


def _ensure_executable_bits(bin_dir: Path) -> None:
    if os.name == "nt":
        return
    for entry in bin_dir.iterdir():
        try:
            entry.chmod(entry.stat().st_mode | 0o111)
        except OSError:
            continue


def _initialise_config() -> None:
    if not NOVEL_CONFIG_SCRIPT.exists():
        _info("Configuration script not found; skipping")
        return
    try:
        _run([sys.executable, str(NOVEL_CONFIG_SCRIPT), "init", "--auto"], cwd=SCRIPTS_DIR)
        _info("Global configuration initialised")
    except InstallError as exc:
        _info(f"Configuration initialisation skipped: {exc}")


def _check_noveler() -> None:
    path = shutil.which("noveler")
    if path:
        _info(f"noveler command available at {path}")
    else:
        _info("noveler command not found on PATH. Open a new shell or source your profile.")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install Novel project tooling")
    parser.add_argument(
        "--pip-arg",
        dest="pip_args",
        action="append",
        default=[],
        help="Additional arguments forwarded to pip (repeatable)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    _title("📚 Installing Novel support toolkit…")
    _ensure_python_version()
    _info(f"Python {sys.version_info.major}.{sys.version_info.minor} detected: {sys.executable}")

    _title("📦 Installing Python dependencies…")
    _install_requirements(args.pip_args)
    _info("Python packages installed")

    _title("🔧 Configuring PATH…")
    _ensure_path(BIN_DIR)
    _ensure_executable_bits(BIN_DIR)

    _title("⚙️  Initialising optional configuration…")
    _initialise_config()

    _title("🧪 Verifying CLI availability…")
    _check_noveler()

    _title("🎉 Installation complete!")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except InstallError as exc:
        print(f"❌ {exc}")
        raise SystemExit(1)
