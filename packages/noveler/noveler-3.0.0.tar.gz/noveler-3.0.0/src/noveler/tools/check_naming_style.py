#!/usr/bin/env python3
"""Python命名規則チェックツール

Pythonコードのファイル名、クラス名、関数名が英語で記述されているかをチェックします。
"""

import ast
import os
import re
import sys
from pathlib import Path
from typing import Any

# 許可される文字パターン(英数字、アンダースコア)
VALID_NAME_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

# 除外ディレクトリ
EXCLUDE_DIRS = {".git", "__pycache__", ".pytest_cache", "temp", ".serena", "serena"}

# 除外ファイル
EXCLUDE_FILES = {"__init__.py"}


class NamingStyleChecker(ast.NodeVisitor):
    """ASTを解析して命名規則をチェック"""

    def __init__(self, filename: str, logger_service: Any | None = None, console_service: Any | None = None) -> None:
        self.filename = filename
        self.errors: list[tuple[int, str, str]] = []

        self.logger_service = logger_service
        self.console_service = console_service
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """クラス定義をチェック"""
        if not VALID_NAME_PATTERN.match(node.name):
            self.errors.append((node.lineno, f"クラス名 '{node.name}' に非英語文字が含まれています", node.name))
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """関数定義をチェック"""
        if not VALID_NAME_PATTERN.match(node.name):
            self.errors.append((node.lineno, f"関数名 '{node.name}' に非英語文字が含まれています", node.name))
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """非同期関数定義をチェック"""
        if not VALID_NAME_PATTERN.match(node.name):
            self.errors.append((node.lineno, f"非同期関数名 '{node.name}' に非英語文字が含まれています", node.name))
        self.generic_visit(node)


def check_filename(filepath: Path) -> list[str]:
    """ファイル名をチェック"""
    errors = []
    filename = filepath.stem  # 拡張子を除いたファイル名

    if filename not in EXCLUDE_FILES and not VALID_NAME_PATTERN.match(filename):
        errors.append(f"ファイル名 '{filepath.name}' に非英語文字が含まれています")

    return errors


def check_file(filepath: Path) -> dict[str, Any]:
    """単一ファイルをチェック"""
    result = {"filepath": str(filepath), "filename_errors": [], "content_errors": []}

    # ファイル名チェック
    result["filename_errors"] = check_filename(filepath)

    # ファイル内容チェック
    try:
        content = filepath.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(filepath))
        checker = NamingStyleChecker(str(filepath))
        checker.visit(tree)

        result["content_errors"] = [
            {"line": line, "message": message, "name": name} for line, message, name in checker.errors
        ]
    except Exception as e:
        result["content_errors"] = [{"error": f"ファイル解析エラー: {e!s}"}]

    return result


def find_python_files(root_dir: Path) -> list[Path]:
    """Pythonファイルを再帰的に検索"""
    python_files = []

    for root, dirs, files in os.walk(root_dir):
        # 除外ディレクトリをスキップ
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        python_files.extend(Path(root) / file for file in files if file.endswith(".py"))

    return python_files


def main():
    """メイン処理"""
    # B20/B30準拠: 共有コンソールサービス必須使用
    from noveler.presentation.shared.shared_utilities import console  # noqa: PLC0415

    console_service = console

    # スクリプトのルートディレクトリを取得
    script_dir = Path(__file__).parent.parent  # scripts/

    # Pythonファイルを検索
    python_files = find_python_files(script_dir)

    # 各ファイルをチェック
    total_errors = 0
    file_errors = []

    for filepath in python_files:
        result = check_file(filepath)

        has_errors = bool(result["filename_errors"] or result["content_errors"])
        if has_errors:
            file_errors.append(result)
            total_errors += len(result["filename_errors"]) + len(result["content_errors"])

    # 結果を出力
    if total_errors > 0:
        console_service.print(f"\n❌ 命名規則エラーが {total_errors} 件見つかりました\n")

        for file_result in file_errors:
            console_service.print(f"📁 {file_result['filepath']}")

            # ファイル名エラー
            for error in file_result["filename_errors"]:
                console_service.print(f"  ⚠️  {error}")

            # コンテンツエラー
            for error in file_result["content_errors"]:
                if "error" in error:
                    console_service.print(f"  ❗ {error['error']}")
                else:
                    console_service.print(f"  ⚠️  行 {error['line']}: {error['message']}")

            console_service.print()

        console_service.print(f"修正が必要なファイル数: {len(file_errors)}")
        return 1
    console_service.print("✅ すべてのPythonファイルが命名規則に準拠しています")
    return 0


if __name__ == "__main__":
    sys.exit(main())
