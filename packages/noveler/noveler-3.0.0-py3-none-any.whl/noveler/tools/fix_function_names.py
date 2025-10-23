#!/usr/bin/env python3
"""関数名をsnake_caseに自動修正するスクリプト

N802エラー(invalid-function-name)を修正します。
"""

from typing import Any
import ast
import re
from pathlib import Path

from noveler.presentation.shared.shared_utilities import console

class FunctionNameFixer(ast.NodeTransformer):
    """関数名をsnake_caseに変換するAST変換器"""

    def __init__(self, logger_service: Any | None = None, console_service: Any | None = None):
        self.renamed_functions = {}

        self.logger_service = logger_service
        self.console_service = console_service
    def visit_FunctionDef(self, node: ast.FunctionDef) -> str | int | bool | dict | list | None:
        """関数定義を訪問して名前を修正"""
        original_name = node.name

        # 特殊メソッドやプライベートメソッドは除外
        if original_name.startswith("__") and original_name.endswith("__"):
            return self.generic_visit(node)

        # すでにsnake_caseの場合はスキップ
        if original_name == self._to_snake_case(original_name):
            return self.generic_visit(node)

        # 名前を変換
        new_name = self._to_snake_case(original_name)
        self.renamed_functions[original_name] = new_name
        node.name = new_name

        return self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> str | int | bool | dict | list | None:
        """非同期関数定義も同様に処理"""
        return self.visit_FunctionDef(node)

    def visit_Name(self, node: ast.Name) -> str | int | bool | dict | list | None:
        """関数呼び出しの名前も修正"""
        if node.id in self.renamed_functions:
            node.id = self.renamed_functions[node.id]
        return self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> str | int | bool | dict | list | None:
        """メソッド呼び出しの名前も修正"""
        if node.attr in self.renamed_functions:
            node.attr = self.renamed_functions[node.attr]
        return self.generic_visit(node)

    def _to_snake_case(self, name: str) -> str:
        """CamelCaseをsnake_caseに変換"""
        # 先頭が大文字の場合は小文字に
        name = name[0].lower() + name[1:] if name else name
        # 大文字の前にアンダースコアを挿入
        result = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
        # 連続するアンダースコアを単一に
        result = re.sub(r"__+", "_", result)
        return result

def fix_file(file_path: Path) -> tuple[bool, int]:
    """ファイルの関数名を修正

    Returns:
        (修正があったか, 修正数)
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))
    except Exception:
        return False, 0

    fixer = FunctionNameFixer()
    new_tree = fixer.visit(tree)

    if not fixer.renamed_functions:
        return False, 0

    # ASTをコードに戻す(ast.unparsing使用)
    try:
        new_content = ast.unparse(new_tree)
    except AttributeError:
        # Python 3.8以前の場合は対応なし
        console.print(f"⚠️ {file_path}: ast.unparse not available")
        return False, 0

    # ファイルを更新
    file_path.write_text(new_content, encoding="utf-8")

    return True, len(fixer.renamed_functions)

def main():
    """メイン処理"""
    scripts_dir = Path(__file__).parent.parent
    python_files = list(scripts_dir.rglob("*.py"))

    total_files = 0
    total_fixes = 0

    console.print("🔧 関数名の修正を開始します...")

    for py_file in python_files:
        # テストファイルとツール自身は除外
        if "tests" in py_file.parts or py_file == Path(__file__):
            continue

        fixed, count = fix_file(py_file)
        if fixed:
            total_files += 1
            total_fixes += count
            console.print(f"✅ {py_file.relative_to(scripts_dir)}: {count}個の関数名を修正")

    console.print(f"\n📊 修正完了: {total_files}ファイル、{total_fixes}個の関数名")

if __name__ == "__main__":
    main()
