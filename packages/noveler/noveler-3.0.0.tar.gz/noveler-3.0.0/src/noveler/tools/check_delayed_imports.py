#!/usr/bin/env python3
"""遅延インポート検出ツール

関数内でのインポート（遅延インポート）を検出し、
DDD準拠のためのリファクタリングを促す。
"""

import ast
import sys
from pathlib import Path
from typing import Any

from noveler.presentation.shared.shared_utilities import console


class DelayedImportDetector(ast.NodeVisitor):
    """遅延インポート検出器"""

    def __init__(self, file_path: Path, logger_service: Any | None = None, console_service: Any | None = None) -> None:
        self.file_path = file_path
        self.violations = []
        self.current_function = None
        self.current_class = None

        self.logger_service = logger_service
        self.console_service = console_service
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """関数定義を訪問"""
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """非同期関数定義を訪問"""
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function

    def visit_ClassDef(self, node: ast.ClassDef):
        """クラス定義を訪問"""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_Import(self, node: ast.Import):
        """import文を訪問"""
        if self.current_function:
            location = self._get_location()
            for alias in node.names:
                self.violations.append(
                    {
                        "type": "delayed_import",
                        "line": node.lineno,
                        "location": location,
                        "import": f"import {alias.name}",
                        "severity": self._get_severity(alias.name),
                    }
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """from ... import文を訪問"""
        if self.current_function:
            location = self._get_location()
            module = node.module or ""
            for alias in node.names:
                import_str = f"from {module} import {alias.name}"
                self.violations.append(
                    {
                        "type": "delayed_import",
                        "line": node.lineno,
                        "location": location,
                        "import": import_str,
                        "severity": self._get_severity(module),
                    }
                )
        self.generic_visit(node)

    def _get_location(self):
        """現在の位置を取得"""
        if self.current_class and self.current_function:
            return f"{self.current_class}.{self.current_function}"
        if self.current_function:
            return self.current_function
        return "module"

    def _get_severity(self, module_name: str) -> str:
        """違反の重要度を判定"""
        if not module_name:
            return "LOW"

        # ファイルパスから層を安全に抽出
        try:
            file_parts = str(self.file_path).split("/")
            if len(file_parts) >= 2 and file_parts[0] == "scripts":
                source_layer = file_parts[1]
            else:
                return "MEDIUM"

            # DDD層違反の場合は重要度が高い
            if "noveler.presentation" in module_name:
                if source_layer in ["domain", "application"]:
                    return "CRITICAL"
            elif "noveler.infrastructure" in module_name or "noveler.application" in module_name:
                if source_layer == "domain":
                    return "CRITICAL"
        except (IndexError, AttributeError):
            return "MEDIUM"

        return "MEDIUM"


def check_file(file_path: Path) -> list[dict[str, Any]]:
    """ファイルをチェック"""
    try:
        with file_path.open(encoding="utf-8") as f:
            tree = ast.parse(f.read())

        # プロジェクトルートからの相対パスを安全に計算
        try:
            project_root = Path.cwd()
            relative_path = file_path.relative_to(project_root)
        except ValueError:
            # プロジェクトルート外の場合は絶対パスを使用
            relative_path = file_path

        detector = DelayedImportDetector(relative_path)
        detector.visit(tree)

        return detector.violations

    except SyntaxError as e:
        console.print(f"構文エラー: {file_path}: {e}")
        return []
    except Exception as e:
        console.print(f"エラー: {file_path}: {e}")
        return []


def main():
    """メイン処理"""
    # スクリプトディレクトリ配下のすべてのPythonファイルをチェック
    scripts_dir = Path("scripts")
    if not scripts_dir.exists():
        console.print("scriptsディレクトリが見つかりません")
        return 1

    all_violations = []
    file_count = 0

    for py_file in scripts_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue

        violations = check_file(py_file)
        if violations:
            # ファイルパスを安全に処理
            try:
                relative_file_path = str(py_file.relative_to(Path.cwd()))
            except ValueError:
                relative_file_path = str(py_file)

            all_violations.extend([{**v, "file": relative_file_path} for v in violations])
        file_count += 1

    # 結果の表示
    if all_violations:
        console.print(f"\n🚨 遅延インポート検出: {len(all_violations)}件\n")

        # 重要度別に分類
        critical = [v for v in all_violations if v["severity"] == "CRITICAL"]
        medium = [v for v in all_violations if v["severity"] == "MEDIUM"]
        low = [v for v in all_violations if v["severity"] == "LOW"]

        if critical:
            console.print(f"🔴 CRITICAL（DDD層違反）: {len(critical)}件")
            for v in critical[:10]:  # 最初の10件を表示
                console.print(f"  {v['file']}:{v['line']} in {v['location']}")
                console.print(f"    {v['import']}")

        if medium:
            console.print(f"\n🟡 MEDIUM: {len(medium)}件")
            for v in medium[:5]:  # 最初の5件を表示
                console.print(f"  {v['file']}:{v['line']} in {v['location']}")

        if low:
            console.print(f"\n🟢 LOW: {len(low)}件")

        console.print("\n💡 推奨事項:")
        console.print("  1. CRITICAL違反は即座に修正してください（DDD準拠違反）")
        console.print("  2. 遅延インポートを削除し、ファイル先頭でインポートしてください")
        console.print("  3. 循環インポートの場合は、インターフェースを使用してください")

        return 1  # エラーコード

    console.print(f"✅ {file_count}ファイルをチェック: 遅延インポートなし")
    return 0


if __name__ == "__main__":
    sys.exit(main())
