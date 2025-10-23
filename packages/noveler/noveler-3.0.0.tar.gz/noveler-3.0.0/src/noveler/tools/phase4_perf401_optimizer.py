#!/usr/bin/env python3
"""Phase 4+ PERF401パフォーマンス最適化ツール

104件のPERF401（手動リスト内包表記）を自動修正する。

対象パターン:
- for文でリストをappendする → リスト内包表記に変換
- for文で条件付きappendする → 条件付きリスト内包表記に変換
"""

import ast
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from noveler.infrastructure.logging.unified_logger import get_logger
from noveler.presentation.shared.shared_utilities import get_console


class PERF401Optimizer(ast.NodeTransformer):
    """PERF401最適化AST変換器"""

    def __init__(self) -> None:
        self.optimizations: list[str] = []

    def visit_For(self, node: ast.For) -> Any:
        """for文を解析してリスト内包表記に変換可能か判定"""
        self.generic_visit(node)

        # 基本的なパターン: for item in iterable: list.append(item)
        if self._is_simple_append_pattern(node):
            return self._convert_to_list_comprehension(node)

        # 条件付きパターン: for item in iterable: if condition: list.append(item)
        if self._is_conditional_append_pattern(node):
            return self._convert_to_conditional_list_comprehension(node)

        return node

    def _is_simple_append_pattern(self, node: ast.For) -> bool:
        """シンプルなappendパターンかチェック"""
        if len(node.body) != 1:
            return False

        stmt = node.body[0]
        if not isinstance(stmt, ast.Expr):
            return False

        if not isinstance(stmt.value, ast.Call):
            return False

        call = stmt.value
        return isinstance(call.func, ast.Attribute) and call.func.attr == "append"

    def _is_conditional_append_pattern(self, node: ast.For) -> bool:
        """条件付きappendパターンかチェック"""
        if len(node.body) != 1:
            return False

        stmt = node.body[0]
        if not isinstance(stmt, ast.If):
            return False

        if len(stmt.body) != 1:
            return False

        inner_stmt = stmt.body[0]
        if not isinstance(inner_stmt, ast.Expr):
            return False

        if not isinstance(inner_stmt.value, ast.Call):
            return False

        call = inner_stmt.value
        return isinstance(call.func, ast.Attribute) and call.func.attr == "append"

    def _convert_to_list_comprehension(self, node: ast.For) -> ast.Assign:
        """シンプルなfor文をリスト内包表記に変換"""
        stmt = node.body[0]
        call = stmt.value

        # [expr for item in iterable]
        comprehension = ast.ListComp(
            elt=call.args[0],
            generators=[ast.comprehension(
                target=node.target,
                iter=node.iter,
                ifs=[],
                is_async=0
            )]
        )

        # target = [comprehension]
        assign = ast.Assign(
            targets=[call.func.value],
            value=comprehension
        )

        self.optimizations.append("for文をリスト内包表記に最適化")
        return assign

    def _convert_to_conditional_list_comprehension(self, node: ast.For) -> ast.Assign:
        """条件付きfor文をリスト内包表記に変換"""
        if_stmt = node.body[0]
        inner_stmt = if_stmt.body[0]
        call = inner_stmt.value

        # [expr for item in iterable if condition]
        comprehension = ast.ListComp(
            elt=call.args[0],
            generators=[ast.comprehension(
                target=node.target,
                iter=node.iter,
                ifs=[if_stmt.test],
                is_async=0
            )]
        )

        # target = [comprehension]
        assign = ast.Assign(
            targets=[call.func.value],
            value=comprehension
        )

        self.optimizations.append("条件付きfor文をリスト内包表記に最適化")
        return assign


class Phase4PERF401Optimizer:
    """Phase 4+ PERF401パフォーマンス最適化エンジン"""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.console = get_console()
        self.optimized_files: list[Path] = []
        self.optimization_count = 0

    def optimize_all_perf401(self, project_root: Path) -> dict[str, Any]:
        """全PERF401を最適化"""
        self.console.print("[yellow]⚡ Phase 4+ PERF401パフォーマンス最適化開始...[/yellow]")

        # PERF401対象ファイルを特定
        perf401_files = self._find_perf401_files(project_root)
        self.console.print(f"🎯 PERF401対象ファイル: {len(perf401_files)}件")

        for py_file in perf401_files:
            try:
                if self._optimize_single_file(py_file):
                    self.optimized_files.append(py_file)
            except Exception as e:
                self.logger.exception(f"PERF401最適化エラー {py_file}: {e}")

        return self._generate_optimization_report()

    def _find_perf401_files(self, project_root: Path) -> list[Path]:
        """PERF401エラーを含むファイルを特定"""

        try:
            # ruff checkでPERF401ファイルを特定
            result = subprocess.run([
                "ruff", "check", str(project_root / "src"),
                "--select=PERF401", "--output-format=json"
            ], check=False, capture_output=True, text=True)

            if result.returncode == 0:
                return []  # エラーなし

            # JSONパースしてファイル一覧を取得
            errors = json.loads(result.stdout)
            return list({Path(error["filename"]) for error in errors})


        except Exception as e:
            self.logger.warning(f"PERF401ファイル特定失敗: {e}")
            # フォールバック: 全Pythonファイル
            return list((project_root / "src").rglob("*.py"))

    def _optimize_single_file(self, file_path: Path) -> bool:
        """単一ファイルのPERF401最適化"""
        if not file_path.exists():
            return False

        try:
            with file_path.open(encoding="utf-8") as f:
                content = f.read()

            # AST変換による最適化
            tree = ast.parse(content)
            optimizer = PERF401Optimizer()
            optimized_tree = optimizer.visit(tree)

            if not optimizer.optimizations:
                return False  # 最適化不要

            # 最適化されたコードを生成
            optimized_code = ast.unparse(optimized_tree)

            return self._save_optimized_file(file_path, optimized_code, optimizer.optimizations)

        except Exception as e:
            self.logger.exception(f"PERF401最適化失敗 {file_path}: {e}")
            return False

    def _save_optimized_file(self, file_path: Path, optimized_code: str, optimizations: list[str]) -> bool:
        """最適化されたファイルを保存"""
        try:
            # バックアップ作成
            backup_path = file_path.with_suffix(file_path.suffix + ".perf401_backup")
            backup_path.write_text(file_path.read_text(encoding="utf-8"), encoding="utf-8")

            # 最適化版を書き込み
            file_path.write_text(optimized_code, encoding="utf-8")

            # 構文チェック
            ast.parse(optimized_code)

            self.optimization_count += len(optimizations)
            self.console.print(f"⚡ PERF401最適化完了: {file_path.name} ({len(optimizations)}箇所)")

            return True

        except Exception as e:
            # 最適化失敗時はバックアップから復元
            if backup_path.exists():
                file_path.write_text(backup_path.read_text(encoding="utf-8"), encoding="utf-8")
                backup_path.unlink()

            self.logger.exception(f"PERF401最適化保存失敗 {file_path}: {e}")
            return False

    def _generate_optimization_report(self) -> dict[str, Any]:
        """最適化結果レポート生成"""
        return {
            "optimized_files_count": len(self.optimized_files),
            "total_optimizations": self.optimization_count,
            "optimized_files": [str(f) for f in self.optimized_files],
            "average_optimizations_per_file": self.optimization_count / max(1, len(self.optimized_files))
        }


def main() -> None:
    """メイン実行関数"""
    console = get_console()
    logger = get_logger(__name__)

    try:
        # プロジェクトルート検出
        project_root = Path.cwd()

        console.print("[blue]🚀 Phase 4+ リファクタリング: PERF401パフォーマンス最適化開始[/blue]")

        # PERF401最適化実行
        optimizer = Phase4PERF401Optimizer()
        result = optimizer.optimize_all_perf401(project_root)

        # 結果レポート
        console.print("\n📊 [green]Phase 4+ PERF401最適化完了[/green]")
        console.print(f"⚡ 最適化ファイル: {result['optimized_files_count']}件")
        console.print(f"🔧 総最適化箇所: {result['total_optimizations']}箇所")
        console.print(f"📈 ファイル当たり平均: {result['average_optimizations_per_file']:.1f}箇所")

        if result["optimized_files"]:
            console.print("\n⚡ 最適化ファイル一覧:")
            for file_path in result["optimized_files"][:10]:  # 上位10件表示
                console.print(f"  - {Path(file_path).name}")

        logger.info(f"Phase 4+ PERF401最適化完了: {result['total_optimizations']}箇所最適化")

    except Exception as e:
        console.print(f"[red]❌ Phase 4+ PERF401最適化失敗: {e}[/red]")
        logger.exception(f"PERF401最適化失敗: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
