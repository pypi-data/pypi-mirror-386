#!/usr/bin/env python3
"""コンソール出力移行ツール

print()やconsole_service.print()を共通基盤console.print()へ自動変換
B30品質作業指示書準拠の統一出力システム実現

変換対象:
    - print() → console.print()
    - console_service.print() → console.print()
    - console.print() → console.print()

使用例:
    python src/noveler/tools/console_migration_tool.py src/noveler/tools/
"""

import argparse
import ast
import shutil
from pathlib import Path

from noveler.presentation.shared.shared_utilities import console


class PrintToConsoleMigrator(ast.NodeTransformer):
    """print()やconsole_service.print()をconsole.print()へ変換するASTトランスフォーマー"""

    def __init__(self) -> None:
        self.has_console_import = False
        self.print_count = 0
        self.console_service_count = 0
        self.needs_console_import = False

    def visit_ImportFrom(self, node):
        """インポート文をチェックしてconsoleインポートを確認"""
        if node.module == "noveler.presentation.shared.shared_utilities" and any(
            alias.name == "console" for alias in node.names
        ):
            self.has_console_import = True
        return node

    def visit_Call(self, node):
        """Call文を変換（print → console.print, console_service.print_ → console.print）"""
        self.generic_visit(node)  # 子ノードも処理

        # print()の変換
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            self.print_count += 1
            self.needs_console_import = True

            # console.print()に変換
            return ast.Call(
                func=ast.Attribute(value=ast.Name(id="console", ctx=ast.Load()), attr="print", ctx=ast.Load()),
                args=node.args,
                keywords=node.keywords,
            )

        # console_service.print()の変換
        if (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "console_service"
            and node.func.attr == "print_"
        ):
            self.console_service_count += 1
            self.needs_console_import = True

            # console.print()に変換
            return ast.Call(
                func=ast.Attribute(value=ast.Name(id="console", ctx=ast.Load()), attr="print", ctx=ast.Load()),
                args=node.args,
                keywords=node.keywords,
            )

        # console.print()の変換
        if (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "console"
            and node.func.attr == "print_"
        ):
            self.console_service_count += 1
            self.needs_console_import = True

            # console.print()に変換
            return ast.Call(
                func=ast.Attribute(value=ast.Name(id="console", ctx=ast.Load()), attr="print", ctx=ast.Load()),
                args=node.args,
                keywords=node.keywords,
            )

        return node


class ConsoleMigrationTool:
    """コンソール出力移行ツール"""

    def __init__(self) -> None:
        self.total_files = 0
        self.modified_files = 0
        self.total_conversions = 0

    def migrate_file(self, file_path: Path) -> bool:
        """単一ファイルを移行"""
        try:
            console.print(f"[blue]処理中: {file_path.name}[/blue]")

            # ファイル読み込み
            content = file_path.read_text(encoding="utf-8")

            # ASTパース
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                console.print(f"[yellow]構文エラーでスキップ: {file_path.name} - {e}[/yellow]")
                return False

            # 変換実行
            migrator = PrintToConsoleMigrator()
            new_tree = migrator.visit(tree)

            total_changes = migrator.print_count + migrator.console_service_count
            if total_changes == 0:
                console.print(f"[dim]変更なし: {file_path.name}[/dim]")
                return False

            # consoleインポートを追加（必要な場合）
            if migrator.needs_console_import and not migrator.has_console_import:
                self._add_console_import(new_tree)
                console.print(f"[green]consoleインポート追加: {file_path.name}[/green]")

            # バックアップ作成
            backup_path = file_path.with_suffix(".py.backup")
            shutil.copy2(file_path, backup_path)

            # 変換後のコードを生成
            try:
                # ast.unparsを使用（Python 3.9+）
                if hasattr(ast, "unparse"):
                    new_content = ast.unparse(new_tree)
                else:
                    # フォールバック用（astor使用）
                    import astor  # noqa: PLC0415

                    new_content = astor.to_source(new_tree)

                # ファイル書き込み
                file_path.write_text(new_content, encoding="utf-8")

                change_details = []
                if migrator.print_count > 0:
                    change_details.append(f"print():{migrator.print_count}")
                if migrator.console_service_count > 0:
                    change_details.append(f"console_service:{migrator.console_service_count}")

                console.print(f"[green]✅ 変換完了: {file_path.name} ({', '.join(change_details)})[/green]")
                self.total_conversions += total_changes
                return True

            except Exception as e:
                # エラー時はバックアップから復元
                shutil.copy2(backup_path, file_path)
                console.print(f"[red]変換エラー（復元済み）: {file_path.name} - {e}[/red]")
                return False

        except Exception as e:
            console.print(f"[red]ファイル処理エラー: {file_path.name} - {e}[/red]")
            return False

    def _add_console_import(self, tree: ast.Module) -> None:
        """consoleインポート文を追加"""
        console_import = ast.ImportFrom(
            module="noveler.presentation.shared.shared_utilities", names=[ast.alias(name="console", asname=None)], level=0
        )

        # 既存のインポート文の後に挿入
        insert_pos = 0
        for i, node in enumerate(tree.body):
            if isinstance(node, ast.Import | ast.ImportFrom):
                insert_pos = i + 1
            else:
                break

        tree.body.insert(insert_pos, console_import)

    def migrate_directory(self, directory_path: Path, recursive: bool = True) -> None:
        """ディレクトリ内のファイルを移行"""
        console.print(f"[bold blue]🔄 コンソール出力移行開始: {directory_path}[/bold blue]")

        # Pythonファイルを検索
        pattern = "**/*.py" if recursive else "*.py"
        python_files = list(directory_path.glob(pattern))

        # テストファイルやバックアップファイルを除外
        python_files = [
            f
            for f in python_files
            if not any(part.startswith("test_") for part in f.parts)
            and not f.name.endswith(".backup")
            and f.name != "__pycache__"
        ]

        self.total_files = len(python_files)
        console.print(f"[info]対象ファイル数: {self.total_files}[/info]")

        # 各ファイルを処理
        for file_path in python_files:
            if self.migrate_file(file_path):
                self.modified_files += 1

        # 結果サマリー
        console.print("\n[bold green]📊 移行完了サマリー[/bold green]")
        console.print(f"• 対象ファイル: {self.total_files}")
        console.print(f"• 変更ファイル: {self.modified_files}")
        console.print(f"• 変換箇所数: {self.total_conversions}")

        if self.modified_files > 0:
            console.print("\n[yellow]⚠️ バックアップファイル（.backup）が作成されています[/yellow]")
            console.print("[yellow]問題がなければ削除してください[/yellow]")


def main() -> None:
    """メイン関数"""
    parser = argparse.ArgumentParser(description="print()やconsole_service.print()をconsole.print()へ自動変換")
    parser.add_argument("target_path", type=Path, help="変換対象のファイルまたはディレクトリ")
    parser.add_argument("--no-recursive", action="store_true", help="ディレクトリの場合、再帰的に処理しない")

    args = parser.parse_args()

    if not args.target_path.exists():
        console.print(f"[red]エラー: {args.target_path} が見つかりません[/red]")
        return

    tool = ConsoleMigrationTool()

    if args.target_path.is_file():
        tool.migrate_file(args.target_path)
    elif args.target_path.is_dir():
        tool.migrate_directory(args.target_path, recursive=not args.no_recursive)
    else:
        console.print(f"[red]エラー: {args.target_path} は有効なファイルまたはディレクトリではありません[/red]")


if __name__ == "__main__":
    main()
