"""Infrastructure.tools.ruff_import_organizer
Where: Infrastructure tool orchestrating Ruff import sorting.
What: Applies Ruff's import organization to maintain consistent import order.
Why: Keeps import statements standardised across the codebase.
"""

from noveler.presentation.shared.shared_utilities import console

"Ruffを使用した統合インポート管理システム\n\nRuffのisort機能とカスタムルールを組み合わせて、\nプロジェクト固有のインポートスタイルを管理します。\n"
import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


class RuffImportOrganizer:
    """Ruffベースのインポート管理システム"""

    def __init__(self, project_root: Path | None = None, logger_service=None, console_service=None) -> None:
        self.project_root = project_root or Path.cwd()
        logger_service = logger_service
        console_service = console_service

    def organize_imports(self, target: Path | str | None = None) -> dict[str, Any]:
        """Ruffを使用してインポートを整理"""
        if target is None:
            target = self.project_root / "scripts"
        target_path = Path(target)
        result = {"success": False, "files_modified": 0, "errors": []}
        try:
            self.console_service.print("🔧 構文エラーを修正中...")
            syntax_cmd = ["ruff", "check", str(target_path), "--select", "E,W,F", "--fix", "--unsafe-fixes"]
            subprocess.run(syntax_cmd, check=False, capture_output=True, text=True)
            self.console_service.print("📦 インポートを整理中...")
            import_cmd = ["ruff", "check", str(target_path), "--select", "I", "--fix"]
            import_result = subprocess.run(import_cmd, check=False, capture_output=True, text=True)
            self.console_service.print("🔍 カスタムルールを適用中...")
            custom_result = self._apply_custom_rules(target_path)
            if import_result.returncode == 0 and custom_result["success"]:
                result["success"] = True
                result["files_modified"] = custom_result.get("files_modified", 0)
                self.console_service.print("✅ インポート整理完了")
            else:
                result["errors"].append(import_result.stderr)
                if not custom_result["success"]:
                    result["errors"].extend(custom_result.get("errors", []))
        except subprocess.CalledProcessError as e:
            result["errors"].append(str(e))
        except Exception as e:
            result["errors"].append(f"予期しないエラー: {e}")
        return result

    def _apply_custom_rules(self, target_path: Path) -> dict[str, Any]:
        """カスタムインポートルールを適用"""
        custom_cmd = [
            sys.executable,
            str(self.project_root / "scripts" / "tools" / "check_import_style.py"),
            str(target_path),
            "--fix",
        ]
        try:
            result = subprocess.run(custom_cmd, check=False, capture_output=True, text=True)
            return {
                "success": result.returncode == 0,
                "files_modified": self._parse_modified_count(result.stdout),
                "errors": [result.stderr] if result.stderr else [],
            }
        except Exception as e:
            return {"success": False, "files_modified": 0, "errors": [str(e)]}

    def _parse_modified_count(self, output: str) -> int:
        """修正されたファイル数を解析"""
        match = re.search("成功 (\\d+)件", output)
        if match:
            return int(match.group(1))
        return 0

    def check_imports(self, target: Path | str | None = None) -> dict[str, Any]:
        """インポートスタイルをチェック(修正なし)"""
        if target is None:
            target = self.project_root / "scripts"
        target_path = Path(target)
        ruff_cmd = ["ruff", "check", str(target_path), "--select", "I"]
        ruff_result = subprocess.run(ruff_cmd, check=False, capture_output=True, text=True)
        custom_cmd = [
            sys.executable,
            str(self.project_root / "scripts" / "tools" / "check_import_style.py"),
            str(target_path),
        ]
        custom_result = subprocess.run(custom_cmd, check=False, capture_output=True, text=True)
        return {
            "ruff_violations": ruff_result.returncode != 0,
            "custom_violations": custom_result.returncode != 0,
            "ruff_output": ruff_result.stdout,
            "custom_output": custom_result.stdout,
        }


def main() -> None:
    """CLI エントリポイント"""
    from noveler.infrastructure.di.container import resolve_service

    try:
        resolve_service("IConsoleService")
    except ValueError:
        from noveler.infrastructure.adapters.console_service_adapter import ConsoleServiceAdapter

        ConsoleServiceAdapter()
    parser = argparse.ArgumentParser(description="Ruffベースの統合インポート管理システム")
    parser.add_argument("command", choices=["check", "fix", "organize"], help="実行するコマンド")
    parser.add_argument("target", nargs="?", help="対象ファイルまたはディレクトリ")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細な出力を表示")
    args = parser.parse_args()
    organizer = RuffImportOrganizer()
    if args.command == "check":
        result = organizer.check_imports(args.target)
        if result["ruff_violations"] or result["custom_violations"]:
            console.print("❌ インポートスタイル違反が見つかりました")
            if args.verbose:
                console.print("\n[Ruff violations]")
                console.print(result["ruff_output"])
                console.print("\n[Custom violations]")
                console.print(result["custom_output"])
            sys.exit(1)
        else:
            console.print("✅ すべてのインポートが正しく整理されています")
            sys.exit(0)
    elif args.command in ["fix", "organize"]:
        result = organizer.organize_imports(args.target)
        if result["success"]:
            console.print(f"✅ 完了: {result['files_modified']}ファイル修正")
            sys.exit(0)
        else:
            console.print("❌ エラーが発生しました:")
            for error in result["errors"]:
                console.print(f"  - {error}")
            sys.exit(1)


if __name__ == "__main__":
    main()
