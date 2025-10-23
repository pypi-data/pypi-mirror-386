"""Infrastructure.services.codemap_parallel_processor
Where: Infrastructure service processing codemap tasks in parallel.
What: Distributes codemap computations across workers to reduce build times.
Why: Enhances scalability for large codemap generation workloads.
"""

from __future__ import annotations

from noveler.presentation.shared.shared_utilities import console

"CODEMAP並列処理サービス\n\nPhase 3: 並列処理による高速化実装\n大規模コードベースの依存関係解析を並列化。\n\n設計原則:\n    - マルチプロセッシングによる並列解析\n    - ワーカープール管理\n    - 結果の統合とマージ\n"
import ast
import multiprocessing as mp
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from noveler.infrastructure.logging.unified_logger import get_logger


@dataclass
class AnalysisTask:
    """解析タスク定義"""

    file_path: Path
    task_type: str
    priority: int = 5


@dataclass
class AnalysisResult:
    """解析結果"""

    file_path: Path
    dependencies: dict[str, list[str]]
    violations: list[dict[str, str]]
    metrics: dict[str, Any]
    execution_time: float


class CodeMapParallelProcessor:
    """CODEMAP並列処理サービス

    責務:
        - ファイル単位の並列解析
        - ワーカープール管理
        - 結果の統合
        - エラーハンドリング
    """

    def __init__(self, project_root: Path, max_workers: int | None = None) -> None:
        """初期化

        Args:
            project_root: プロジェクトルート
            max_workers: 最大ワーカー数（Noneの場合はCPU数）
        """
        self.project_root = project_root
        self.max_workers = max_workers or mp.cpu_count()
        self.logger = get_logger(__name__)
        self._results_cache: dict[str, AnalysisResult] = {}

    def analyze_parallel(self, file_paths: list[Path], analysis_type: str = "full") -> dict[str, Any]:
        """並列解析実行

        Args:
            file_paths: 解析対象ファイルリスト
            analysis_type: 解析タイプ ('dependencies', 'violations', 'metrics', 'full')

        Returns:
            統合された解析結果
        """
        start_time = time.time()
        tasks = self._create_analysis_tasks(file_paths, analysis_type)
        results: Any = self._execute_parallel_tasks(tasks)
        merged_result = self._merge_results(results)
        execution_time = time.time() - start_time
        console.print(f"Parallel analysis completed: {len(file_paths)} files in {execution_time:.2f}s")
        return merged_result

    def _create_analysis_tasks(self, file_paths: list[Path], analysis_type: str) -> list[AnalysisTask]:
        """解析タスクを生成"""
        tasks = []
        for file_path in file_paths:
            priority = self._calculate_priority(file_path)
            task = AnalysisTask(file_path=file_path, task_type=analysis_type, priority=priority)
            tasks.append(task)
        tasks.sort(key=lambda t: t.priority)
        return tasks

    def _calculate_priority(self, file_path: Path) -> int:
        """ファイルの解析優先度を計算"""
        if not file_path.exists():
            return 10
        size = file_path.stat().st_size
        if size > 100000:
            return 1
        if size > 50000:
            return 3
        if size > 10000:
            return 5
        return 7

    def _execute_parallel_tasks(self, tasks: list[AnalysisTask]) -> list[AnalysisResult]:
        """並列でタスクを実行"""
        results: list[Any] = []
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {executor.submit(self._analyze_file_worker, task): task for task in tasks}
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result(timeout=30)
                    results.append(result)
                except Exception:
                    self.logger.exception("Failed to analyze %s", task.file_path)
                    results.append(self._create_empty_result(task.file_path))
        return results

    @staticmethod
    def _analyze_file_worker(task: AnalysisTask) -> AnalysisResult:
        """ワーカープロセスで実行される解析処理"""
        start_time = time.time()
        dependencies: dict[str, list[str]] = {}
        violations: list[dict[str, str]] = []
        metrics: dict[str, Any] = {}
        try:
            with open(task.file_path, encoding="utf-8") as f:
                content = f.read()
            tree = ast.parse(content)
            if task.task_type in ["dependencies", "full"]:
                dependencies = CodeMapParallelProcessor._extract_dependencies(tree)
            if task.task_type in ["violations", "full"]:
                violations: Any = CodeMapParallelProcessor._detect_violations(task.file_path, tree)
            if task.task_type in ["metrics", "full"]:
                metrics = CodeMapParallelProcessor._calculate_metrics(tree, content)
        except Exception:
            pass
        execution_time = time.time() - start_time
        return AnalysisResult(
            file_path=task.file_path,
            dependencies=dependencies,
            violations=violations,
            metrics=metrics,
            execution_time=execution_time,
        )

    @staticmethod
    def _extract_dependencies(tree: ast.AST) -> dict[str, list[str]]:
        """依存関係を抽出"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        return {"imports": imports, "imported_by": []}

    @staticmethod
    def _detect_violations(file_path: Path, tree: ast.AST) -> list[dict[str, str]]:
        """アーキテクチャ違反を検出"""
        violations: list[Any] = []
        path_str = str(file_path)
        source_layer = None
        if "domain" in path_str:
            source_layer = "domain"
        elif "application" in path_str:
            source_layer = "application"
        elif "infrastructure" in path_str:
            source_layer = "infrastructure"
        elif "presentation" in path_str:
            source_layer = "presentation"
        if not source_layer:
            return violations
        for node in ast.walk(tree):
            if isinstance(node, ast.Import | ast.ImportFrom):
                module_name = ""
                if isinstance(node, ast.Import):
                    if node.names:
                        module_name = node.names[0].name
                else:
                    module_name = node.module or ""
                if source_layer == "domain":
                    if any(layer in module_name for layer in ["application", "infrastructure", "presentation"]):
                        violations.append(
                            {
                                "from": str(file_path),
                                "to": module_name,
                                "violation": f"domain -> {(module_name.split('.')[1] if '.' in module_name else 'unknown')}",
                            }
                        )
                elif source_layer == "application":
                    if any(layer in module_name for layer in ["infrastructure", "presentation"]):
                        violations.append(
                            {
                                "from": str(file_path),
                                "to": module_name,
                                "violation": f"application -> {(module_name.split('.')[1] if '.' in module_name else 'unknown')}",
                            }
                        )
        return violations

    @staticmethod
    def _calculate_metrics(tree: ast.AST, content: str) -> dict[str, Any]:
        """メトリクスを計算"""
        lines = content.split("\n")
        metrics = {
            "lines_of_code": len(lines),
            "num_functions": sum(1 for _ in ast.walk(tree) if isinstance(_, ast.FunctionDef)),
            "num_classes": sum(1 for _ in ast.walk(tree) if isinstance(_, ast.ClassDef)),
            "num_imports": sum(1 for _ in ast.walk(tree) if isinstance(_, ast.Import | ast.ImportFrom)),
        }
        complexity = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.If | ast.For | ast.While | ast.ExceptHandler):
                complexity += 1
        metrics["cyclomatic_complexity"] = complexity
        return metrics

    def _merge_results(self, results: list[AnalysisResult]) -> dict[str, Any]:
        """解析結果を統合"""
        merged = {
            "dependency_map": {
                "version": "1.0.0",
                "core_dependencies": {},
                "dependency_issues": {"layer_violations": []},
                "dependency_statistics": {"total_modules": 0, "total_imports": 0, "total_violations": 0},
            },
            "quality_metrics": {"total_lines": 0, "total_functions": 0, "total_classes": 0, "average_complexity": 0.0},
            "performance": {"total_execution_time": 0.0, "files_analyzed": 0, "parallel_efficiency": 0.0},
        }
        total_complexity = 0
        for result in results:
            module_name = str(result.file_path.relative_to(self.project_root))
            module_name = module_name.replace("/", ".").replace(".py", "")
            if result.dependencies:
                merged["dependency_map"]["core_dependencies"][module_name] = result.dependencies
            merged["dependency_map"]["dependency_issues"]["layer_violations"].extend(result.violations)
            if result.metrics:
                merged["quality_metrics"]["total_lines"] += result.metrics.get("lines_of_code", 0)
                merged["quality_metrics"]["total_functions"] += result.metrics.get("num_functions", 0)
                merged["quality_metrics"]["total_classes"] += result.metrics.get("num_classes", 0)
                total_complexity += result.metrics.get("cyclomatic_complexity", 0)
            merged["performance"]["total_execution_time"] += result.execution_time
            merged["performance"]["files_analyzed"] += 1
        merged["dependency_map"]["dependency_statistics"]["total_modules"] = len(
            merged["dependency_map"]["core_dependencies"]
        )
        merged["dependency_map"]["dependency_statistics"]["total_violations"] = len(
            merged["dependency_map"]["dependency_issues"]["layer_violations"]
        )
        if merged["performance"]["files_analyzed"] > 0:
            merged["quality_metrics"]["average_complexity"] = total_complexity / merged["performance"]["files_analyzed"]
            sequential_estimate = merged["performance"]["files_analyzed"] * 0.1
            merged["performance"]["parallel_efficiency"] = (
                sequential_estimate / merged["performance"]["total_execution_time"]
            )
        return merged

    def _create_empty_result(self, file_path: Path) -> AnalysisResult:
        """空の結果を生成"""
        return AnalysisResult(file_path=file_path, dependencies={}, violations=[], metrics={}, execution_time=0.0)


def get_parallel_processor() -> CodeMapParallelProcessor:
    """並列処理サービスのインスタンスを取得"""
    try:
        from noveler.presentation.shared.shared_utilities import get_common_path_service

        path_service = get_common_path_service()
        project_root = path_service.get_project_root()
    except ImportError:
        project_root = Path(os.environ.get("PROJECT_ROOT", Path.cwd()))
    return CodeMapParallelProcessor(project_root)
