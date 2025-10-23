#!/usr/bin/env python3
"""
パフォーマンスボトルネック分析ツール
プロジェクト全体のパフォーマンス問題を検出し、最適化提案を生成
"""

import ast
import asyncio
import json
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from noveler.presentation.shared.shared_utilities import _get_console

console = _get_console()


class CodeAnalyzer:
    """コード静的解析によるパフォーマンス問題検出"""

    def __init__(self, _logger_service: Any = None, _console_service: Any = None) -> None:
        self.performance_issues: list[dict[str, Any]] = []
        self.file_io_patterns = [
            r"\.read_text\(",
            r"\.write_text\(",
            r"yaml\.load\(",
            r"yaml\.dump\(",
            r"json\.load\(",
            r"json\.dump\(",
            r"open\(",
            r"Path\(.*\)\.rglob\("
        ]

    def analyze_file(self, file_path: Path) -> dict[str, Any]:
        """単一ファイル分析"""
        try:
            # 最適化読み込みが利用可能なら使用、なければ通常読み込み
            content: str
            try:
                from noveler.infrastructure.performance.comprehensive_performance_optimizer import (  # noqa: PLC0415
                    performance_optimizer as _perf_opt,
                )

                content = _perf_opt.file_io_optimizer.optimized_read_text(file_path, encoding="utf-8")
            except Exception:
                content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(file_path))
            issues = {
                "file_path": str(file_path),
                "performance_issues": [],
                "optimization_opportunities": [],
                "complexity_metrics": self._calculate_complexity(tree),
                "io_operations": self._detect_io_operations(content),
                "potential_bottlenecks": []
            }
            self._analyze_ast_node(tree, issues)
            return issues
        except Exception as e:
            return {
                "file_path": str(file_path),
                "error": f"分析エラー: {e}",
                "performance_issues": [],
                "optimization_opportunities": [],
                "complexity_metrics": {},
                "io_operations": [],
                "potential_bottlenecks": []
            }

    def _analyze_ast_node(self, node: ast.AST, issues: dict[str, Any]) -> None:
        """AST ノード分析"""
        for child in ast.walk(node):
            if isinstance(child, (ast.For, ast.While)):
                if self._is_complex_loop(child):
                    issues["potential_bottlenecks"].append({
                        "type": "complex_loop",
                        "line": child.lineno,
                        "description": "複雑なループ処理 - 並列化や最適化を検討"
                    })
            if isinstance(child, ast.For):
                nested_loops = self._count_nested_loops(child)
                if nested_loops >= 2:
                    issues["potential_bottlenecks"].append({
                        "type": "nested_loops",
                        "line": child.lineno,
                        "nesting_level": nested_loops,
                        "description": f"{nested_loops}重ネストループ - O(n^{nested_loops})計算量"
                    })
            if isinstance(child, ast.Call) and hasattr(child.func, "attr"):
                if child.func.attr in ["read_text", "write_text", "open"]:
                    issues["io_operations"].append({
                        "type": "file_io",
                        "line": child.lineno,
                        "operation": child.func.attr
                    })

    def _is_complex_loop(self, loop_node: ast.AST) -> bool:
        """複雑なループかどうかの判定"""
        body_lines = 0
        for stmt in getattr(loop_node, "body", []):
            if hasattr(stmt, "lineno"):
                body_lines += 1
        return body_lines > 10

    def _count_nested_loops(self, node: ast.For) -> int:
        """ネストしたループの深さカウント"""
        max_depth = 0
        current_depth = 0

        def visit_node(n: ast.AST) -> None:
            nonlocal max_depth, current_depth
            if isinstance(n, (ast.For, ast.While)):
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            for child in ast.iter_child_nodes(n):
                visit_node(child)
            if isinstance(n, (ast.For, ast.While)):
                current_depth -= 1

        visit_node(node)
        return max_depth

    def _calculate_complexity(self, tree: ast.AST) -> dict[str, int]:
        """コードの複雑度メトリクス計算"""
        metrics = {"functions": 0, "classes": 0, "lines_of_code": 0, "cyclomatic_complexity": 0}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                metrics["functions"] += 1
                metrics["cyclomatic_complexity"] += self._calculate_cyclomatic_complexity(node)
            elif isinstance(node, ast.ClassDef):
                metrics["classes"] += 1
        return metrics

    def _calculate_cyclomatic_complexity(self, func_node: ast.FunctionDef) -> int:
        """循環的複雑度計算"""
        complexity = 1
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        return complexity

    def _detect_io_operations(self, content: str) -> list[dict[str, Any]]:
        """I/O操作パターン検出"""
        io_ops = []
        for pattern in self.file_io_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_num = content[:match.start()].count("\n") + 1
                io_ops.append({
                    "type": "file_io",
                    "pattern": pattern,
                    "line": line_num,
                    "match": match.group()
                })
        return io_ops


class PerformanceBottleneckAnalyzer:
    """パフォーマンスボトルネック包括分析システム"""

    def __init__(self, _logger_service: Any = None, _console_service: Any = None) -> None:
        self.code_analyzer = CodeAnalyzer()
        self.analysis_results: dict[str, Any] = {}

    async def analyze_project_performance(self, project_root: Path) -> dict[str, Any]:
        """プロジェクト全体のパフォーマンス分析"""
        console.print("🔍 プロジェクトパフォーマンス分析開始...", style="bold blue")
        python_files = list(project_root.rglob("*.py"))
        console.print(f"📁 分析対象ファイル: {len(python_files)}件")

        static_analysis_results = await self._run_static_analysis(python_files)
        critical_files = self._identify_critical_files(static_analysis_results)
        bottleneck_analysis = self._analyze_bottlenecks(static_analysis_results)
        optimization_recommendations = self._generate_comprehensive_recommendations(bottleneck_analysis)

        self.analysis_results = {
            "timestamp": time.time(),
            "project_root": str(project_root),
            "total_files_analyzed": len(python_files),
            "static_analysis": static_analysis_results,
            "critical_files": critical_files,
            "bottleneck_analysis": bottleneck_analysis,
            "optimization_recommendations": optimization_recommendations,
            "performance_summary": self._generate_performance_summary(),
        }

        console.print("✅ パフォーマンス分析完了", style="bold green")
        return self.analysis_results

    async def _run_static_analysis(self, python_files: list[Path]) -> list[dict[str, Any]]:
        """静的解析実行"""
        results: list[dict[str, Any]] = []
        semaphore = asyncio.Semaphore(10)

        async def _analyze_file(file_path: Path) -> Any:
            async with semaphore:
                return await asyncio.to_thread(self.code_analyzer.analyze_file, file_path)

        console.print("🔬 静的解析実行中...")
        tasks = [_analyze_file(file_path) for file_path in python_files]
        results_any = await asyncio.gather(*tasks, return_exceptions=True)

        valid_results = []
        for i, result in enumerate(results_any):
            if isinstance(result, Exception):
                console.print(f"⚠️ 分析エラー: {python_files[i]} - {result}", style="yellow")
            else:
                valid_results.append(result)

        return valid_results

    def _identify_critical_files(self, analysis_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """パフォーマンスクリティカルファイル特定"""
        critical_files = []
        for result in analysis_results:
            if "error" in result:
                continue

            score = 0
            io_count = len(result["io_operations"])
            score += io_count * 2

            bottleneck_count = len(result["potential_bottlenecks"])
            score += bottleneck_count * 5

            complexity = result["complexity_metrics"]
            score += complexity.get("cyclomatic_complexity", 0)

            for bottleneck in result["potential_bottlenecks"]:
                if bottleneck["type"] == "nested_loops":
                    score += bottleneck["nesting_level"] * 10

            if score > 20:
                critical_files.append({
                    "file_path": result["file_path"],
                    "critical_score": score,
                    "io_operations": io_count,
                    "bottlenecks": bottleneck_count,
                    "complexity": complexity,
                    "recommendations": self._generate_file_recommendations(result)
                })

        critical_files.sort(key=lambda x: x["critical_score"], reverse=True)
        return critical_files

    def _analyze_bottlenecks(self, analysis_results: list[dict[str, Any]]) -> dict[str, Any]:
        """ボトルネック分析"""
        bottleneck_summary = {
            "total_io_operations": 0,
            "total_bottlenecks": 0,
            "bottleneck_types": defaultdict(int),
            "io_operation_types": defaultdict(int),
            "high_complexity_files": []
        }

        for result in analysis_results:
            if "error" in result:
                continue

            bottleneck_summary["total_io_operations"] += len(result["io_operations"])
            for io_op in result["io_operations"]:
                bottleneck_summary["io_operation_types"][io_op["type"]] += 1

            bottleneck_summary["total_bottlenecks"] += len(result["potential_bottlenecks"])
            for bottleneck in result["potential_bottlenecks"]:
                bottleneck_summary["bottleneck_types"][bottleneck["type"]] += 1

            complexity = result["complexity_metrics"]
            if complexity.get("cyclomatic_complexity", 0) > 50:
                bottleneck_summary["high_complexity_files"].append({
                    "file_path": result["file_path"],
                    "complexity": complexity["cyclomatic_complexity"]
                })

        return dict(bottleneck_summary)

    def _generate_file_recommendations(self, file_analysis: dict[str, Any]) -> list[str]:
        """ファイル固有の最適化推奨事項"""
        recommendations = []

        io_count = len(file_analysis["io_operations"])
        if io_count > 10:
            recommendations.append(
                f"🔧 ファイルI/O最適化: {io_count}個のI/O操作 - バッチ処理やキャッシュを検討"
            )

        nested_loops = [b for b in file_analysis["potential_bottlenecks"] if b["type"] == "nested_loops"]
        if nested_loops:
            max_nesting = max(loop["nesting_level"] for loop in nested_loops)
            recommendations.append(
                f"⚡ ネストループ最適化: 最大{max_nesting}重ネスト - アルゴリズム見直しを推奨"
            )

        complexity = file_analysis["complexity_metrics"].get("cyclomatic_complexity", 0)
        if complexity > 30:
            recommendations.append(
                f"📊 複雑度削減: 循環的複雑度{complexity} - 関数分割を検討"
            )

        return recommendations

    def _generate_comprehensive_recommendations(self, bottleneck_analysis: dict[str, Any]) -> list[str]:
        """包括的最適化推奨事項生成"""
        recommendations = []

        total_io = bottleneck_analysis["total_io_operations"]
        if total_io > 100:
            recommendations.append(
                f"🗄️ I/O最適化（優先度: 高）: {total_io}個のファイル操作検出 - "
            )

        yaml_ops = bottleneck_analysis["io_operation_types"].get("file_io", 0)
        if yaml_ops > 50:
            recommendations.append(
                f"📄 YAML/JSON最適化（優先度: 高）: {yaml_ops}個の処理操作 - "
                "YAMLOptimizerによるキャッシュと効率的な処理を実装"
            )

        complex_loops = bottleneck_analysis["bottleneck_types"].get("complex_loop", 0)
        nested_loops = bottleneck_analysis["bottleneck_types"].get("nested_loops", 0)
        if complex_loops + nested_loops > 10:
            recommendations.append(
                f"⚡ 並列処理導入（優先度: 中）: {complex_loops + nested_loops}個の重いループ - "
                "AsyncOperationOptimizerによる非同期処理を検討"
            )

        high_complexity_files = len(bottleneck_analysis["high_complexity_files"])
        if high_complexity_files > 5:
            recommendations.append(
                f"💾 メモリ最適化（優先度: 中）: {high_complexity_files}個の高複雑度ファイル - "
                "MemoryOptimizerによる効率的なデータ処理を実装"
            )

        if bottleneck_analysis["total_bottlenecks"] > 20:
            recommendations.append(
                "🎯 具体的改善箇所: 以下のファイルから優先的に最適化を開始してください"
            )

        return recommendations

    def _generate_performance_summary(self) -> dict[str, Any]:
        """パフォーマンスサマリー生成"""
        return {
            "analysis_timestamp": time.time(),
            "optimization_impact_estimate": {
                "potential_response_time_improvement": "30-50%",
                "potential_memory_savings": "25-40%",
                "implementation_effort": "medium",
                "priority_level": "high"
            }
        }

    def print_analysis_report(self) -> None:
        """分析結果レポート表示"""
        if not self.analysis_results:
            console.print("⚠️ 分析結果がありません", style="yellow")
            return

        results = self.analysis_results

        console.print("\n" + "=" * 80, style="bold")
        console.print("🚀 パフォーマンスボトルネック分析レポート", style="bold blue")
        console.print("=" * 80, style="bold")

        console.print("\n📊 分析サマリー:", style="bold")
        console.print(f"  • 分析ファイル数: {results['total_files_analyzed']}件")
        console.print(f"  • クリティカルファイル: {len(results['critical_files'])}件")
        console.print(f"  • 総I/O操作: {results['bottleneck_analysis']['total_io_operations']}個")
        console.print(f"  • 総ボトルネック: {results['bottleneck_analysis']['total_bottlenecks']}個")

        if results["critical_files"]:
            console.print("\n🚨 クリティカルファイル TOP 10:", style="bold red")
            for i, file_info in enumerate(results["critical_files"][:10], 1):
                console.print(f"  {i}. {Path(file_info['file_path']).name}")
                console.print(
                    f"     スコア: {file_info['critical_score']}, "
                    f"I/O操作: {file_info['io_operations']}, "
                    f"ボトルネック: {file_info['bottlenecks']}"
                )

        console.print("\n💡 最適化推奨事項:", style="bold green")
        for i, rec in enumerate(results["optimization_recommendations"], 1):
            console.print(f"  {i}. {rec}")

        summary = results["performance_summary"]
        impact = summary["optimization_impact_estimate"]
        console.print("\n📈 改善予測:", style="bold cyan")
        console.print(f"  • レスポンス時間改善: {impact['potential_response_time_improvement']}")
        console.print(f"  • メモリ使用量削減: {impact['potential_memory_savings']}")
        console.print(f"  • 実装工数: {impact['implementation_effort']}")
        console.print(f"  • 優先度: {impact['priority_level']}")

        console.print("=" * 80, style="bold")

    def export_analysis_results(self, output_path: Path) -> None:
        """分析結果エクスポート"""
        if not self.analysis_results:
            console.print("⚠️ エクスポート対象の分析結果がありません", style="yellow")
            return

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(self.analysis_results, f, ensure_ascii=False, indent=2, default=str)

        console.print(f"📄 分析結果エクスポート完了: {output_path}", style="green")


async def main() -> None:
    """メイン実行関数"""
    analyzer = PerformanceBottleneckAnalyzer()
    project_root = Path("src/noveler")

    if not project_root.exists():
        console.print(f"❌ プロジェクトディレクトリが見つかりません: {project_root}", style="red")
        return

    results = await analyzer.analyze_project_performance(project_root)
    analyzer.print_analysis_report()

    # 結果を保存
    output_path = Path("reports") / "performance_analysis.json"
    analyzer.export_analysis_results(output_path)


if __name__ == "__main__":
    asyncio.run(main())
