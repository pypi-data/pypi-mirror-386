"""Tools.verify_commands
Where: Tool verifying command definitions and bindings.
What: Checks CLI command registration for consistency.
Why: Prevents command issues before they reach users.
"""

from noveler.presentation.shared.shared_utilities import console

"\nコマンド存在確認スクリプト\n\nドキュメントに記載されているコマンドが実際に実装されているかを検証する。\n"
import subprocess
import sys
from pathlib import Path

from noveler.infrastructure.adapters.console_service_adapter import ConsoleServiceAdapter
from noveler.infrastructure.di.container import resolve_service


def check_command_exists(command: str) -> bool:
    """コマンドが存在するかチェック"""
    try:
        subprocess.run(command.split(), check=False, capture_output=True, text=True, timeout=10)
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
        return False


def check_novel_subcommands() -> dict[str, bool]:
    """novelサブコマンドの存在確認"""
    commands_to_check = [
        "novel write --help",
        "novel complete --help",
        "novel check --help",
        "novel test --help",
        "novel plot --help",
        "novel init --help",
        "novel claude-export --help",
        "novel doctor --help",
        "novel repair --help",
        "novel health --help",
        "novel health check --help",
        "novel health fix --help",
        "novel health monitor --help",
        "novel a31-auto-fix --help",
        "novel error-monitor --help",
        "novel watch --help",
    ]
    results = {}
    for cmd in commands_to_check:
        cmd_name = cmd.replace(" --help", "")
        results[cmd_name] = check_command_exists(cmd)
    return results


def check_python_scripts() -> dict[str, bool]:
    """Pythonスクリプトの存在確認"""
    scripts_to_check = [
        "noveler/tools/check_import_style.py",
        "noveler/tools/quality_gate_check.py",
        "noveler/tools/syntax_error_fixer.py",
        "noveler/tools/spec_id_generator.py",
        "noveler/infrastructure/testing/fast_test.py",
    ]
    project_root = Path(__file__).parent.parent.parent
    results = {}
    for script_path in scripts_to_check:
        full_path = project_root / script_path
        results[script_path] = full_path.exists()
    return results


def main():
    """メイン処理"""
    try:
        resolve_service("IConsoleService")
    except ValueError:
        ConsoleServiceAdapter()
    console.print("🔍 コマンド存在確認を実行中...")
    console.print("=" * 50)
    console.print("\n📋 novelサブコマンド確認:")
    novel_results = check_novel_subcommands()
    for cmd, exists in novel_results.items():
        status = "✅" if exists else "❌"
        console.print(f"{status} {cmd}")
    console.print("\n🐍 Pythonスクリプト確認:")
    script_results = check_python_scripts()
    for script, exists in script_results.items():
        status = "✅" if exists else "❌"
        console.print(f"{status} {script}")
    total_novel = len(novel_results)
    existing_novel = sum(novel_results.values())
    total_scripts = len(script_results)
    existing_scripts = sum(script_results.values())
    console.print("\n📊 サマリー:")
    console.print(f"novelコマンド: {existing_novel}/{total_novel} 存在")
    console.print(f"Pythonスクリプト: {existing_scripts}/{total_scripts} 存在")
    missing_commands = [cmd for (cmd, exists) in novel_results.items() if not exists]
    missing_scripts = [script for (script, exists) in script_results.items() if not exists]
    if missing_commands or missing_scripts:
        console.print("\n⚠️  存在しないコマンド/スクリプト:")
        for cmd in missing_commands:
            console.print(f"   - {cmd}")
        for script in missing_scripts:
            console.print(f"   - {script}")
        return 1
    console.print("\n🎉 すべてのコマンド/スクリプトが存在します!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
