#!/usr/bin/env python3
"""B20準拠: print文の自動リファクタリングツール

すべてのprint文をlogger_serviceまたはconsole_serviceに自動変換
"""

import ast
from pathlib import Path
from typing import Any


class PrintStatementRefactorer(ast.NodeTransformer):
    """print文をlogger/console呼び出しに変換するAST変換器"""

    def __init__(self, use_console: bool = False):
        self.use_console = use_console
        self.has_console_import = False
        self.has_logger_import = False
        self.print_count = 0

    def visit_Call(self, node: ast.Call) -> Any:
        """print関数呼び出しを変換"""
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            self.print_count += 1

            # print文の内容を解析
            if node.args:
                first_arg = node.args[0]

                # エラーメッセージパターンの検出
                is_error = self._is_error_message(first_arg)
                is_warning = self._is_warning_message(first_arg)
                is_success = self._is_success_message(first_arg)

                if self.use_console:
                    # console_serviceを使用
                    return self._create_console_call(node, is_error, is_warning, is_success)
                # logger_serviceを使用
                return self._create_logger_call(node, is_error, is_warning)

        return self.generic_visit(node)

    def _is_error_message(self, node: ast.AST) -> bool:
        """エラーメッセージかどうかを判定"""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            error_patterns = ["エラー", "error", "失敗", "failed", "❌", "⚠️"]
            return any(pattern in node.value.lower() for pattern in error_patterns)
        return False

    def _is_warning_message(self, node: ast.AST) -> bool:
        """警告メッセージかどうかを判定"""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            warning_patterns = ["警告", "warning", "注意", "⚠️"]
            return any(pattern in node.value.lower() for pattern in warning_patterns)
        return False

    def _is_success_message(self, node: ast.AST) -> bool:
        """成功メッセージかどうかを判定"""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            success_patterns = ["成功", "success", "完了", "completed", "✅", "✓"]
            return any(pattern in node.value.lower() for pattern in success_patterns)
        return False

    def _create_console_call(self, print_node: ast.Call, is_error: bool, is_warning: bool, is_success: bool) -> ast.AST:
        """console_service呼び出しを作成"""
        # Rich形式のカラー付けを追加
        if is_error:
            color = "red"
        elif is_warning:
            color = "yellow"
        elif is_success:
            color = "green"
        else:
            color = "cyan"

        # console.print("[color]message[/color]") 形式に変換
        if print_node.args:
            # f-string or 通常の文字列を処理
            args = []
            for arg in print_node.args:
                if isinstance(arg, (ast.Constant, ast.JoinedStr)):
                    # 色タグを追加
                    wrapped = ast.JoinedStr(
                        values=[
                            ast.Constant(value=f"[{color}]"),
                            arg,
                            ast.Constant(value=f"[/{color}]")
                        ]
                    )
                    args.append(wrapped)
                else:
                    args.append(arg)

            return ast.Call(
                func=ast.Attribute(
                    value=ast.Name(id="console", ctx=ast.Load()),
                    attr="print",
                    ctx=ast.Load()
                ),
                args=args,
                keywords=[]
            )

        return print_node

    def _create_logger_call(self, print_node: ast.Call, is_error: bool, is_warning: bool) -> ast.AST:
        """logger_service呼び出しを作成"""
        if is_error:
            method = "error"
        elif is_warning:
            method = "warning"
        else:
            method = "info"

        return ast.Call(
            func=ast.Attribute(
                value=ast.Name(id="self._logger_service" if self._in_class() else "logger", ctx=ast.Load()),
                attr=method,
                ctx=ast.Load()
            ),
            args=print_node.args,
            keywords=[]
        )

    def _in_class(self) -> bool:
        """クラス内かどうかを判定（簡易版）"""
        # TODO: より正確な判定を実装
        return True


def refactor_file(file_path: Path, use_console: bool = False) -> tuple[bool, int]:
    """ファイル内のprint文をリファクタリング

    Returns:
        tuple[bool, int]: (成功フラグ, 変換したprint文の数)
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content)

        # ASTを変換
        refactorer = PrintStatementRefactorer(use_console=use_console)
        new_tree = refactorer.visit(tree)

        if refactorer.print_count > 0:
            # コードを生成
            new_code = ast.unparse(new_tree)

            # 必要なインポートを追加
            imports_to_add = []
            if use_console and "from rich.console import Console" not in content:
                imports_to_add.append("from rich.console import Console")
                imports_to_add.append("console = Console()")
            elif not use_console and "from noveler.infrastructure.logging.unified_logger import get_logger" not in content:
                imports_to_add.append("from noveler.infrastructure.logging.unified_logger import get_logger")
                imports_to_add.append("logger = get_logger(__name__)")

            if imports_to_add:
                # インポート文を適切な位置に挿入
                lines = new_code.split("\n")
                import_index = 0
                for i, line in enumerate(lines):
                    if line.startswith("import ") or line.startswith("from "):
                        import_index = i + 1
                    elif line and not line.startswith("#"):
                        break

                for imp in imports_to_add:
                    lines.insert(import_index, imp)
                    import_index += 1

                new_code = "\n".join(lines)

            # ファイルを書き戻し
            file_path.write_text(new_code, encoding="utf-8")
            return True, refactorer.print_count

        return False, 0

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False, 0


def main():
    """メイン処理"""
    import argparse

    parser = argparse.ArgumentParser(description="B20準拠print文リファクタリング")
    parser.add_argument("--path", type=Path, default=Path("src/noveler"), help="対象パス")
    parser.add_argument("--use-console", action="store_true", help="console_serviceを使用")
    parser.add_argument("--dry-run", action="store_true", help="変更を実際に適用しない")

    args = parser.parse_args()

    # 対象ファイルを収集
    if args.path.is_file():
        files = [args.path]
    else:
        files = list(args.path.rglob("*.py"))

    # テストファイルを除外
    files = [f for f in files if "test_" not in f.name]

    total_files = 0
    total_prints = 0

    for file_path in files:
        if args.dry_run:
            # ドライラン: print文の数をカウントするだけ
            content = file_path.read_text(encoding="utf-8")
            count = content.count("print(")
            if count > 0:
                print(f"{file_path}: {count} print statements")
                total_prints += count
                total_files += 1
        else:
            success, count = refactor_file(file_path, args.use_console)
            if success:
                print(f"✅ {file_path}: {count} print statements refactored")
                total_prints += count
                total_files += 1

    print(f"\n📊 Summary: {total_prints} print statements in {total_files} files")


if __name__ == "__main__":
    main()
