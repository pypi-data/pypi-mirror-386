#!/usr/bin/env python3
"""依存関係分析ドメインサービス - Command Pattern適用

DDD設計とCommand Patternを使用して複雑度を削減
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class ViolationType(Enum):
    """違反タイプ"""

    LAYER_VIOLATION = "layer_violation"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    EXTERNAL_DEPENDENCY = "external_dependency"


@dataclass
class DependencyViolation:
    """依存関係違反"""

    message: str
    violation_type: ViolationType
    severity: str = "medium"


@dataclass
class AnalysisResult:
    """分析結果"""

    violations: list[DependencyViolation] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    graph_data: dict[str, Any] = field(default_factory=dict)


class DependencyAnalysisCommand(ABC):
    """依存関係分析コマンドの基底クラス"""

    @abstractmethod
    def execute(self, project_root: Path) -> AnalysisResult:
        """分析を実行"""

    @abstractmethod
    def get_name(self) -> str:
        """分析名を取得"""


class LayerViolationAnalysisCommand(DependencyAnalysisCommand):
    """レイヤー違反分析コマンド"""

    def __init__(self) -> None:
        self.layer_hierarchy = ["domain", "application", "infrastructure", "presentation"]

    def execute(self, project_root: Path) -> AnalysisResult:
        """レイヤー違反分析を実行"""
        violations: list[DependencyViolation] = []

        # 簡略化された実装例
        # 実際の実装では、PythonファイルのASTを解析する
        for py_file in project_root.rglob("*.py"):
            if self._should_exclude(py_file):
                continue

            layer = self._detect_layer(py_file)
            dependencies = self._extract_imports(py_file)

            for dep in dependencies:
                dep_layer = self._detect_layer_from_import(dep, project_root)
                if self._is_layer_violation(layer, dep_layer):
                    violations.append(
                        DependencyViolation(
                            message=f"Layer violation: {layer} -> {dep_layer} ({py_file.name} -> {dep})",
                            violation_type=ViolationType.LAYER_VIOLATION,
                            severity="error",
                        )
                    )

        return AnalysisResult(violations=violations, metrics={"layer_violations": len(violations)}, graph_data={})

    def get_name(self) -> str:
        return "layer_violation_analysis"

    def _should_exclude(self, file_path: Path) -> bool:
        """ファイルを除外すべきか判定"""
        return "__pycache__" in str(file_path) or file_path.name.startswith("test_")

    def _detect_layer(self, file_path: Path) -> str:
        """ファイルのレイヤーを検出"""
        path_str = str(file_path)

        if "/domain/" in path_str:
            return "domain"
        if "/application/" in path_str:
            return "application"
        if "/infrastructure/" in path_str:
            return "infrastructure"
        if "/presentation/" in path_str:
            return "presentation"
        return "unknown"

    def _extract_imports(self, file_path: Path) -> list[str]:
        """インポート文を抽出(簡易版)"""
        imports = []
        try:
            with file_path.open("r", encoding="utf-8") as f:
                for line in f:
                    stripped_line = line.strip()
                    if stripped_line.startswith("from noveler.") and " import " in stripped_line:

                        module = stripped_line.split(" import ")[0].replace("from ", "")
                        imports.append(module)
                    elif stripped_line.startswith("import noveler."):
                        module = stripped_line.replace("import ", "")
                        imports.append(module)
        except (OSError, UnicodeDecodeError, PermissionError):
            # ファイル読み込みエラーは無視して空のインポートリストを返す
            pass

        return imports

    def _detect_layer_from_import(self, import_path: str, _project_root: Path) -> str:
        """インポートパスからレイヤーを検出"""
        if ".domain." in import_path:
            return "domain"
        if ".application." in import_path:
            return "application"
        if ".infrastructure." in import_path:
            return "infrastructure"
        if ".presentation." in import_path:
            return "presentation"
        return "unknown"

    def _is_layer_violation(self, source_layer: str, target_layer: str) -> bool:
        """レイヤー違反かどうか判定"""
        if source_layer == "unknown" or target_layer == "unknown":
            return False

        # ドメインは他の層に依存してはいけない
        if source_layer == "domain" and target_layer in ["application", "infrastructure", "presentation"]:
            return True

        # アプリケーション層はインフラ層・プレゼンテーション層に依存してはいけない
        return bool(source_layer == "application" and target_layer in ["infrastructure", "presentation"])


class CircularDependencyAnalysisCommand(DependencyAnalysisCommand):
    """循環依存分析コマンド"""

    def execute(self, project_root: Path) -> AnalysisResult:
        """循環依存分析を実行"""
        violations: list[DependencyViolation] = []

        # 簡略化された実装
        # 実際にはグラフアルゴリズム(DFS、Tarjan等)を使用
        dependency_graph = self._build_dependency_graph(project_root)
        cycles = self._find_cycles(dependency_graph)

        violations.extend(
            DependencyViolation(
                message=f"Circular dependency: {' -> '.join(cycle)}",
                violation_type=ViolationType.CIRCULAR_DEPENDENCY,
                severity="error",
            )
            for cycle in cycles
        )

        return AnalysisResult(
            violations=violations, metrics={"circular_dependencies": len(cycles)}, graph_data={"cycles": cycles}
        )

    def get_name(self) -> str:
        return "circular_dependency_analysis"

    def _build_dependency_graph(self, project_root: Path) -> dict[str, list[str]]:
        """依存関係グラフを構築(簡易版)"""
        graph = {}

        for py_file in project_root.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            module_name = str(py_file.relative_to(project_root)).replace("/", ".").replace(".py", "")
            imports = self._extract_project_imports(py_file)
            graph[module_name] = imports

        return graph

    def _extract_project_imports(self, file_path: Path) -> list[str]:
        """プロジェクト内のインポートのみを抽出"""
        imports = []
        try:
            with file_path.open("r", encoding="utf-8") as f:
                for line in f:
                    stripped_line = line.strip()
                    if stripped_line.startswith("from noveler.") and " import " in stripped_line:
                        module = stripped_line.split(" import ")[0].replace("from ", "").replace("noveler.", "")
                        imports.append(module)
        except (OSError, UnicodeDecodeError, PermissionError):
            # ファイル読み込みエラーは無視して空のインポートリストを返す
            pass

        return imports

    def _find_cycles(self, graph: dict[str, list[str]]) -> list[list[str]]:
        """循環依存を検出(簡易版)"""
        cycles = []
        visited = set()
        recursion_stack = set()

        def dfs(node: str, path: list[str]) -> None:
            if node in recursion_stack:
                # 循環発見
                cycle_start = path.index(node)
                cycle = [*path[cycle_start:], node]
                cycles.append(cycle)
                return

            if node in visited:
                return

            visited.add(node)
            recursion_stack.add(node)

            for neighbor in graph.get(node, []):
                dfs(neighbor, [*path, node])

            recursion_stack.remove(node)

        for node in graph:
            if node not in visited:
                dfs(node, [])

        return cycles


class ExternalDependencyAnalysisCommand(DependencyAnalysisCommand):
    """外部依存分析コマンド"""

    def execute(self, project_root: Path) -> AnalysisResult:
        """外部依存分析を実行"""
        violations: list[DependencyViolation] = []
        external_deps = {}

        for py_file in project_root.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            layer = self._detect_layer(py_file)
            imports = self._extract_external_imports(py_file)

            external_deps[str(py_file)] = imports

            # ドメイン層での外部依存は警告
            if layer == "domain" and imports:
                violations.extend(
                    DependencyViolation(
                        message=f"External dependency in domain layer: {py_file.name} -> {imp}",
                        violation_type=ViolationType.EXTERNAL_DEPENDENCY,
                        severity="warning",
                    )
                    for imp in imports
                )

        return AnalysisResult(
            violations=violations,
            metrics={"external_dependencies": len(external_deps)},
            graph_data={"external_deps": external_deps},
        )

    def get_name(self) -> str:
        return "external_dependency_analysis"

    def _detect_layer(self, file_path: Path) -> str:
        """ファイルのレイヤーを検出"""
        path_str = str(file_path)

        if "/domain/" in path_str:
            return "domain"
        if "/application/" in path_str:
            return "application"
        if "/infrastructure/" in path_str:
            return "infrastructure"
        if "/presentation/" in path_str:
            return "presentation"
        return "unknown"

    def _extract_external_imports(self, file_path: Path) -> list[str]:
        """外部パッケージのインポートを抽出"""
        external_imports = []
        standard_libs = {"os", "sys", "json", "pathlib", "typing", "dataclasses", "abc", "enum"}

        try:
            with file_path.open("r", encoding="utf-8") as f:
                for line in f:
                    stripped_line = line.strip()
                    if stripped_line.startswith("import ") and not stripped_line.startswith("import noveler"):
                        package = stripped_line.replace("import ", "").split(".")[0]
                        if package not in standard_libs:
                            external_imports.append(package)
                    elif line.startswith("from ") and not line.startswith("from noveler"):
                        package = line.split(" ")[1].split(".")[0]
                        if package not in standard_libs:
                            external_imports.append(package)
        except (OSError, UnicodeDecodeError, PermissionError, IndexError):
            # ファイル読み込みまたは文字列分析エラーは無視
            pass

        return list(set(external_imports))


class DependencyAnalysisService:
    """依存関係分析ドメインサービス - Command Patternコーディネーター"""

    def __init__(self) -> None:
        self.commands: list[DependencyAnalysisCommand] = []

    def add_command(self, command: DependencyAnalysisCommand) -> None:
        """分析コマンドを追加"""
        self.commands.append(command)

    def execute_all(self, project_root: Path) -> dict[str, AnalysisResult]:
        """すべての分析コマンドを実行"""
        results: dict[str, AnalysisResult] = {}

        for command in self.commands:
            try:
                result = command.execute(project_root)
                results[command.get_name()] = result
            except Exception as e:
                results[command.get_name()] = AnalysisResult(
                    violations=[
                        DependencyViolation(
                            message=f"分析エラー: {e}", violation_type=ViolationType.LAYER_VIOLATION, severity="error"
                        )
                    ],
                    metrics={},
                    graph_data={},
                )

        return results

    def get_total_violations(self, results: dict[str, AnalysisResult]) -> list[DependencyViolation]:
        """すべての違反を取得"""
        all_violations = []

        for result in results.values():
            all_violations.extend(result.violations)

        return all_violations

    def get_summary_metrics(self, results: dict[str, AnalysisResult]) -> dict[str, Any]:
        """サマリーメトリクスを取得"""
        total_violations = len(self.get_total_violations(results))

        metrics = {
            "total_violations": total_violations,
            "analysis_types": list(results.keys()),
        }

        for name, result in results.items():
            metrics[f"{name}_violations"] = len(result.violations)

        return metrics
