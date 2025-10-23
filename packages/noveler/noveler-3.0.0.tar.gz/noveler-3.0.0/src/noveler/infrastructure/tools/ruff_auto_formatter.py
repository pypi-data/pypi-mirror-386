"""Infrastructure.tools.ruff_auto_formatter
Where: Infrastructure tool wrapping Ruff auto-formatting operations.
What: Runs Ruff to apply formatting across the project.
Why: Provides a consistent interface for automated formatting.
"""

from noveler.presentation.shared.shared_utilities import console

"\nRuffベースのファイル自動修正システム\n\nファイル保存時の末尾空白削除とファイル末尾改行修正を自動実行\n既存のRuffImportOrganizerを拡張して実装\n"
import subprocess
import sys
from pathlib import Path
from typing import Any


class RuffAutoFormatter:
    """Ruffを使用したファイル自動修正システム"""

    def __init__(self, project_root: Path | None = None, logger_service=None, console_service=None) -> None:
        self.project_root = project_root or Path.cwd()
        self.logger_service = logger_service
        self.console_service = console_service

    def format_file_on_save(self, file_path: Path | str) -> dict[str, Any]:
        """ファイル保存時の自動修正を実行

        Args:
            file_path: 修正対象ファイルパス

        Returns:
            修正結果の詳細情報
        """
        file_path = Path(file_path)
        result = {"success": False, "file_path": str(file_path), "fixes_applied": [], "errors": []}
        try:
            whitespace_result = self._fix_trailing_whitespace(file_path)
            if whitespace_result["success"]:
                result["fixes_applied"].append("trailing_whitespace_removed")
            else:
                result["errors"].extend(whitespace_result["errors"])
            newline_result = self._fix_file_ending_newline(file_path)
            if newline_result["success"]:
                result["fixes_applied"].append("file_ending_newline_fixed")
            else:
                result["errors"].extend(newline_result["errors"])
            syntax_result = self._fix_basic_syntax_errors(file_path)
            if syntax_result["success"]:
                result["fixes_applied"].append("basic_syntax_fixed")
            else:
                result["errors"].extend(syntax_result["errors"])
            result["success"] = len(result["fixes_applied"]) > 0 and len(result["errors"]) == 0
        except Exception as e:
            result["errors"].append(f"予期しないエラー: {e}")
        return result

    def _fix_trailing_whitespace(self, file_path: Path) -> dict[str, Any]:
        """末尾空白を削除"""
        try:
            cmd = ["ruff", "check", str(file_path), "--select", "W291,W293", "--fix", "--quiet"]
            result = subprocess.run(cmd, check=False, capture_output=True, text=True)
            return {"success": result.returncode == 0, "errors": [result.stderr] if result.stderr else []}
        except Exception as e:
            return {"success": False, "errors": [str(e)]}

    def _fix_file_ending_newline(self, file_path: Path) -> dict[str, Any]:
        """ファイル末尾改行を修正"""
        try:
            cmd = ["ruff", "check", str(file_path), "--select", "W292", "--fix", "--quiet"]
            result = subprocess.run(cmd, check=False, capture_output=True, text=True)
            return {"success": result.returncode == 0, "errors": [result.stderr] if result.stderr else []}
        except Exception as e:
            return {"success": False, "errors": [str(e)]}

    def _fix_basic_syntax_errors(self, file_path: Path) -> dict[str, Any]:
        """基本的な構文エラーを修正"""
        try:
            cmd = ["ruff", "check", str(file_path), "--select", "E,W", "--fix", "--quiet"]
            result = subprocess.run(cmd, check=False, capture_output=True, text=True)
            return {"success": result.returncode == 0, "errors": [result.stderr] if result.stderr else []}
        except Exception as e:
            return {"success": False, "errors": [str(e)]}

    def batch_format_files(self, file_paths: list[Path | str]) -> dict[str, Any]:
        """複数ファイルの一括自動修正"""
        results: dict[str, Any] = {
            "total_files": len(file_paths),
            "successful_files": 0,
            "failed_files": 0,
            "file_results": [],
            "summary": {"trailing_whitespace_fixed": 0, "file_ending_newline_fixed": 0, "basic_syntax_fixed": 0},
        }
        for file_path in file_paths:
            file_result = self.format_file_on_save(file_path)
            results["file_results"].append(file_result)
            if file_result["success"]:
                results["successful_files"] += 1
                for fix_type in file_result["fixes_applied"]:
                    if fix_type == "trailing_whitespace_removed":
                        results["summary"]["trailing_whitespace_fixed"] += 1
                    elif fix_type == "file_ending_newline_fixed":
                        results["summary"]["file_ending_newline_fixed"] += 1
                    elif fix_type == "basic_syntax_fixed":
                        results["summary"]["basic_syntax_fixed"] += 1
            else:
                results["failed_files"] += 1
        return results

    def check_ruff_availability(self) -> dict[str, Any]:
        """Ruffの利用可能性をチェック"""
        try:
            result = subprocess.run(["ruff", "--version"], check=False, capture_output=True, text=True)
            return {
                "available": result.returncode == 0,
                "version": result.stdout.strip() if result.returncode == 0 else None,
                "error": result.stderr if result.returncode != 0 else None,
            }
        except FileNotFoundError:
            return {
                "available": False,
                "version": None,
                "error": "Ruff not found. Please install with: pip install ruff",
            }
        except Exception as e:
            return {"available": False, "version": None, "error": str(e)}


def main() -> None:
    """CLI エントリポイント"""
    import argparse

    parser = argparse.ArgumentParser(description="Ruffベースのファイル自動修正システム")
    parser.add_argument("files", nargs="*", help="修正対象ファイル")
    parser.add_argument("--check", action="store_true", help="Ruffの利用可能性をチェック")
    parser.add_argument("--batch", action="store_true", help="複数ファイルの一括処理")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細な出力を表示")
    args = parser.parse_args()
    from noveler.infrastructure.di.container import resolve_service

    try:
        console_service = resolve_service("IConsoleService")
    except ValueError:
        from noveler.infrastructure.adapters.console_service_adapter import ConsoleServiceAdapter

        console_service = ConsoleServiceAdapter()
    formatter = RuffAutoFormatter(console_service=console_service)
    if args.check:
        check_result = formatter.check_ruff_availability()
        if check_result["available"]:
            console.print(f"✅ Ruff is available: {check_result['version']}")
        else:
            console.print(f"❌ Ruff is not available: {check_result['error']}")
        sys.exit(0 if check_result["available"] else 1)
    if not args.files:
        console.print("❌ ファイルを指定してください")
        sys.exit(1)
    if args.batch:
        results: Any = formatter.batch_format_files(args.files)
        console.print(f"📊 処理結果: {results['successful_files']}/{results['total_files']} ファイル成功")
        console.print(f"   末尾空白修正: {results['summary']['trailing_whitespace_fixed']} ファイル")
        console.print(f"   ファイル末尾改行修正: {results['summary']['file_ending_newline_fixed']} ファイル")
        console.print(f"   基本構文修正: {results['summary']['basic_syntax_fixed']} ファイル")
        if args.verbose:
            for file_result in results["file_results"]:
                status = "✅" if file_result["success"] else "❌"
                console.print(f"   {status} {file_result['file_path']}")
                if file_result["errors"] and args.verbose:
                    for error in file_result["errors"]:
                        console.print(f"      エラー: {error}")
        sys.exit(0 if results["failed_files"] == 0 else 1)
    else:
        for file_path in args.files:
            result = formatter.format_file_on_save(file_path)
            if result["success"]:
                console.print(f"✅ {file_path}: {', '.join(result['fixes_applied'])}")
            else:
                console.print(f"❌ {file_path}: 修正失敗")
                if args.verbose:
                    for error in result["errors"]:
                        console.print(f"   エラー: {error}")


if __name__ == "__main__":
    main()
