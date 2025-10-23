#!/usr/bin/env python3
# File: scripts/setup_venv.py
# Purpose: Cross-platform virtual environment setup script for Windows and WSL
# Context: Handles platform-specific venv creation and dependency installation

"""Cross-platform venv setup utility.

This script creates and maintains separate virtual environments for:
- Windows (.venv.win)
- WSL/Linux (.venv.wsl)

Both environments can coexist and are automatically selected based on the
current platform.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path

# Force UTF-8 encoding for Windows console to handle Japanese paths
if platform.system() == "Windows":
    # Set environment variables before any output
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

    # Reconfigure sys.stdout/stderr to use UTF-8
    if sys.stdout.encoding.lower() != "utf-8":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


class VenvManager:
    """Manage cross-platform virtual environments."""

    def __init__(self, project_root: Path | None = None):
        """Initialize venv manager.

        Args:
            project_root: Project root directory. Defaults to script's parent.
        """
        if project_root is None:
            # Script is in scripts/, project root is parent
            project_root = Path(__file__).parent.parent
        self.project_root = project_root.resolve()
        self.pyproject_toml = self.project_root / "pyproject.toml"

        # Detect platform
        self.is_wsl = self._detect_wsl()
        self.is_windows = platform.system() == "Windows" and not self.is_wsl

        # Select appropriate venv path
        if self.is_windows:
            self.venv_name = ".venv.win"
            self.python_cmd = self._find_windows_python()
            self.venv_python = self.venv_path / "Scripts" / "python.exe"
            self.venv_pip = self.venv_path / "Scripts" / "pip.exe"
        else:  # WSL or Linux
            self.venv_name = ".venv.wsl"
            self.python_cmd = "python3"
            self.venv_python = self.venv_path / "bin" / "python"
            self.venv_pip = self.venv_path / "bin" / "pip"

    @property
    def venv_path(self) -> Path:
        """Get platform-specific venv path."""
        return self.project_root / self.venv_name

    def _detect_wsl(self) -> bool:
        """Detect if running in WSL environment."""
        try:
            with open("/proc/version", "r") as f:
                return "microsoft" in f.read().lower()
        except FileNotFoundError:
            return False

    def _find_windows_python(self) -> str:
        """Find appropriate Python executable on Windows.

        Returns:
            Python command (py, python, python3).

        Raises:
            RuntimeError: If no Python found.
        """
        # Try py launcher first (recommended for Windows)
        for cmd in ["py", "python", "python3"]:
            try:
                result = subprocess.run(
                    [cmd, "--version"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode == 0:
                    return cmd
            except FileNotFoundError:
                continue

        raise RuntimeError("No Python executable found. Install Python 3.10+")

    def create_venv(self, force: bool = False) -> None:
        """Create platform-specific virtual environment.

        Args:
            force: If True, recreate venv even if it exists.
        """
        if self.venv_path.exists() and not force:
            print(f"[OK] Virtual environment already exists: {self.venv_name}")
            return

        if self.venv_path.exists() and force:
            print(f"[CLEAN] Removing existing venv: {self.venv_name}")
            import shutil
            shutil.rmtree(self.venv_path)

        print(f"[CREATE] Creating virtual environment: {self.venv_name}")
        print(f"         Platform: {'Windows' if self.is_windows else 'WSL/Linux'}")
        print(f"         Python: {self.python_cmd}")

        try:
            subprocess.run(
                [self.python_cmd, "-m", "venv", str(self.venv_path)],
                check=True,
                cwd=self.project_root,
            )
            print(f"[OK] Virtual environment created successfully")
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"Failed to create venv: {exc}") from exc

    def install_dependencies(self, dev: bool = True) -> None:
        """Install dependencies from pyproject.toml.

        Args:
            dev: If True, install development dependencies.
        """
        if not self.venv_path.exists():
            raise RuntimeError(f"Virtual environment not found: {self.venv_name}")

        print(f"[INSTALL] Installing dependencies...")

        # Upgrade pip first
        print("   Upgrading pip...")
        subprocess.run(
            [str(self.venv_python), "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            capture_output=True,
        )

        # Install package in editable mode with dependencies
        package_spec = ".[dev]" if dev else "."
        install_cmd = [str(self.venv_pip), "install", "-e", package_spec]

        print(f"   Installing noveler{' [dev]' if dev else ''}...")
        subprocess.run(
            install_cmd,
            check=True,
            cwd=self.project_root,
        )

        print("[OK] Dependencies installed successfully")

    def print_activation_instructions(self) -> None:
        """Print instructions for activating the venv."""
        print("\n" + "=" * 60)
        print("Virtual Environment Setup Complete!")
        print("=" * 60)

        if self.is_windows:
            print("\nTo activate (PowerShell):")
            print(f"  .\\{self.venv_name}\\Scripts\\Activate.ps1")
            print("\nTo activate (Command Prompt):")
            print(f"  {self.venv_name}\\Scripts\\activate.bat")
        else:
            print("\nTo activate:")
            print(f"  source {self.venv_name}/bin/activate")

        print("\nTo deactivate:")
        print("  deactivate")
        print("\n" + "=" * 60)

    def verify_installation(self) -> bool:
        """Verify that the venv is properly configured.

        Returns:
            True if verification passes.
        """
        print(f"\n[VERIFY] Checking installation...")

        checks = [
            (self.venv_path.exists(), f"Venv directory exists: {self.venv_name}"),
            (self.venv_python.exists(), f"Python executable exists"),
            (self.venv_pip.exists(), f"Pip executable exists"),
        ]

        # Check if noveler is importable
        try:
            result = subprocess.run(
                [str(self.venv_python), "-c", "import noveler; import sys; print('OK')"],
                capture_output=True,
                text=True,
                check=True,
            )
            if result.stdout.strip() == "OK":
                checks.append((True, "Noveler package installed and importable"))
            else:
                checks.append((False, f"Unexpected output: {result.stdout.strip()}"))
        except subprocess.CalledProcessError as exc:
            checks.append((False, f"Noveler package NOT importable: {exc.stderr}"))

        all_passed = all(passed for passed, _ in checks)

        for passed, message in checks:
            print(f"  {'[OK]' if passed else '[FAIL]'} {message}")

        if all_passed:
            print("\n[OK] All checks passed!")
        else:
            print("\n[FAIL] Some checks failed. Please review the output above.")

        return all_passed


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success).
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Setup cross-platform virtual environment for noveler project"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force recreate venv even if it exists",
    )
    parser.add_argument(
        "--no-dev",
        action="store_true",
        help="Skip development dependencies",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing venv, don't create or install",
    )
    args = parser.parse_args()

    try:
        manager = VenvManager()

        print("Noveler Virtual Environment Setup")
        print(f"  Project: {manager.project_root}")
        print(f"  Platform: {'Windows' if manager.is_windows else 'WSL/Linux'}")
        print(f"  Target: {manager.venv_name}\n")

        if args.verify_only:
            if not manager.venv_path.exists():
                print(f"[FAIL] Virtual environment not found: {manager.venv_name}")
                return 1
            return 0 if manager.verify_installation() else 1

        # Create venv
        manager.create_venv(force=args.force)

        # Install dependencies
        manager.install_dependencies(dev=not args.no_dev)

        # Verify
        if not manager.verify_installation():
            return 1

        # Print activation instructions
        manager.print_activation_instructions()

        return 0

    except Exception as exc:
        print(f"\n[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
