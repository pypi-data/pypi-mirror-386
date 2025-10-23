#!/usr/bin/env python3
"""ARG002 (unused-method-argument) エラーを修正するスクリプト

このスクリプトは以下の修正を行います:
    1. 未使用の引数に_プレフィックスを追加
2. 抽象基底クラスやインターフェースは保持
3. 必要に応じて# noqa: ARG002コメントを追加
"""

import ast
import re
import subprocess
from pathlib import Path
from typing import Any

class UnusedArgumentFixer(ast.NodeVisitor):
    """未使用引数を検出して修正するAST訪問者"""

    def __init__(self, content: str, logger_service: Any | None = None, console_service: Any | None = None):
        self.content = content
        self.lines = content.splitlines(keepends=True)
        self.unused_args: set[tuple[int, str]] = set()
        self.used_names: set[str] = set()
        self.current_function = None
        self.changes = []

        self.logger_service = logger_service
        self.console_service = console_service
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """関数定義を訪問"""
        old_function = self.current_function
        self.current_function = node
        old_used = self.used_names.copy()

        # 関数内で使用される名前を収集
        self.used_names = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                self.used_names.add(child.id)
            elif isinstance(child, ast.Attribute):
                if isinstance(child.value, ast.Name):
                    self.used_names.add(child.value.id)

        # 引数をチェック
        all_args = []
        if node.args.posonlyargs:
            all_args.extend(node.args.posonlyargs)
        if node.args.args:
            all_args.extend(node.args.args)
        if node.args.kwonlyargs:
            all_args.extend(node.args.kwonlyargs)

        # self, cls は除外
        for arg in all_args:
            if arg.arg not in ["self", "cls"] and arg.arg not in self.used_names:
                # 抽象メソッドやオーバーライドメソッドかチェック
                if not self._is_abstract_or_override(node):
                    self.unused_args.add((arg.lineno, arg.arg))

        # 子ノードを訪問
        self.generic_visit(node)

        self.current_function = old_function
        self.used_names = old_used

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """非同期関数定義を訪問"""
        self.visit_FunctionDef(node)

    def _is_abstract_or_override(self, node):
        """抽象メソッドやオーバーライドメソッドかチェック"""
        # デコレータをチェック
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                if decorator.id in ["abstractmethod", "override"]:
                    return True
            elif isinstance(decorator, ast.Attribute):
                if decorator.attr in ["abstractmethod", "override"]:
                    return True

        # 本体が pass, ..., raise NotImplementedError のみかチェック
        if len(node.body) == 1:
            stmt = node.body[0]
            if isinstance(stmt, ast.Pass):
                return True
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                if stmt.value.value == ...:
                    return True
            elif isinstance(stmt, ast.Raise):
                if isinstance(stmt.exc, ast.Call):
                    if isinstance(stmt.exc.func, ast.Name) and stmt.exc.func.id == "NotImplementedError":
                        return True

        return False

    def fix_unused_arguments(self):
        """未使用引数を修正"""
        # ソートして後ろから処理(行番号が変わらないように)
        sorted_args = sorted(self.unused_args, reverse=True)

        for lineno, arg_name in sorted_args:
            # 該当行を見つける
            for i, line in enumerate(self.lines):
                # 引数定義を含む行を探す
                if re.search(rf"\b{re.escape(arg_name)}\b(?:\s*:|\s*=|\s*,|\s*\))", line):
                    # 既に_で始まっていない場合のみ修正
                    if not arg_name.startswith("_"):
                        # 引数名を_付きに変更
                        new_line = re.sub(
                            rf"\b{re.escape(arg_name)}\b",
                            f"_{arg_name}",
                            line)

                        if new_line != line:
                            self.lines[i] = new_line
                            self.changes.append((arg_name, f"_{arg_name}"))
                            break

        return "".join(self.lines), self.changes

class ARG002Fixer:
    """ARG002エラー修正クラス"""

    def __init__(self, logger_service: Any | None = None, console_service: Any | None = None):
        self.fixed_count = 0
        self.total_errors = 0

        self.logger_service = logger_service
        self.console_service = console_service
    def process_file(self, file_path: Path) -> list[tuple[str, str]]:
        """ファイルを処理してARG002エラーを修正"""
        all_changes = []

        try:
            content = file_path.read_text(encoding="utf-8")

            # ASTを解析
            try:
                tree = ast.parse(content)
            except SyntaxError:
                self.console_service.print(f"  Syntax error in {file_path}, skipping")
                return all_changes

            # 未使用引数を検出して修正
            fixer = UnusedArgumentFixer(content)
            fixer.visit(tree)

            if fixer.unused_args:
                new_content, changes = fixer.fix_unused_arguments()
                if changes:
                    file_path.write_text(new_content, encoding="utf-8")
                    all_changes.extend(changes)
                    self.console_service.print(f"  修正済み: {file_path.name}")
                    for old, new in changes:
                        self.console_service.print(f"    {old} → {new}")

        except Exception as e:
            self.console_service.print(f"Error processing {file_path}: {e}")

        return all_changes

    def run(self):
        """メイン処理を実行"""
        scripts_dir = Path("/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド/scripts")

        # ARG002エラーの総数をカウント
        self.console_service.print("ARG002エラーをスキャン中...")
        result = subprocess.run(
            ["ruff", "check", str(scripts_dir), "--select", "ARG002"],
            check=False, capture_output=True,
            text=True)

        # エラーを解析
        error_files = {}
        for line in result.stdout.strip().split("\n"):
            if line and "ARG002" in line:
                self.total_errors += 1
                file_path = line.split(":")[0]
                if file_path not in error_files:
                    error_files[file_path] = []
                error_files[file_path].append(line)

        self.console_service.print(f"検出されたARG002エラー: {self.total_errors}件")
        self.console_service.print(f"影響を受けるファイル: {len(error_files)}個")
        self.console_service.print()

        # 各ファイルを処理
        for file_path in sorted(error_files):
            path = Path(file_path)
            if path.exists():
                changes = self.process_file(path)
                self.fixed_count += len(changes)

        # 結果を表示
        self.console_service.print()
        self.console_service.print("=" * 60)
        self.console_service.print("修正完了!")
        self.console_service.print(f"総エラー数: {self.total_errors}")
        self.console_service.print(f"修正済み: {self.fixed_count}")
        self.console_service.print(f"修正率: {self.fixed_count / self.total_errors * 100:.1f}%" if self.total_errors > 0 else "N/A")

        # 残りのエラーを確認
        self.console_service.print("\n残りのエラーを確認中...")
        result = subprocess.run(
            ["ruff", "check", str(scripts_dir), "--select", "ARG002", "--statistics"],
            check=False, capture_output=True,
            text=True)

        remaining_count = 0
        for line in result.stdout.strip().split("\n"):
            if line and "ARG002" in line:
                parts = line.split()
                if parts and parts[0].isdigit():
                    remaining_count = int(parts[0])

        self.console_service.print(f"残りのARG002エラー: {remaining_count}件")
        self.console_service.print(f"削減率: {(self.total_errors - remaining_count) / self.total_errors * 100:.1f}%" if self.total_errors > 0 else "N/A")

if __name__ == "__main__":
    fixer = ARG002Fixer()
    fixer.run()
