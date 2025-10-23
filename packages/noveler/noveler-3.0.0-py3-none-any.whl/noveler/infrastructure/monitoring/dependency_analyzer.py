"""Infrastructure.monitoring.dependency_analyzer
Where: Infrastructure module analysing project dependencies.
What: Builds dependency graphs, detects cycles, and generates reports.
Why: Helps enforce architectural boundaries and highlight risks.
"""

from noveler.presentation.shared.shared_utilities import console

"依存関係分析ツール - DDD層間の依存関係を詳細に分析\n\n主な機能:\n    1. 層間依存関係の可視化(グラフ生成)\n2. 循環依存の検出(高度なアルゴリズム)\n3. 外部パッケージ依存の層別分析\n4. 依存関係の深さ分析\n5. 違反の自動修正提案\n"
import argparse
import ast
import json
import sys
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class ViolationType(Enum):
    """違反タイプ"""

    LAYER_VIOLATION = "layer_violation"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    EXTERNAL_DEPENDENCY = "external_dependency"
    CUSTOM = "custom"


class DependencyViolation:
    """依存関係違反の基底クラス"""

    def __init__(
        self,
        message: str,
        violation_type: ViolationType,
        severity: str = "medium",
        logger_service=None,
        console_service=None,
    ) -> None:
        self.message = message
        self.violation_type = violation_type
        self.severity = severity
        self.logger_service = logger_service
        self.console_service = console_service


class LayerViolation(DependencyViolation):
    """レイヤー違反"""

    def __init__(
        self,
        source_module: str,
        target_module: str,
        source_layer: str,
        target_layer: str,
        logger_service=None,
        console_service=None,
    ) -> None:
        super().__init__(
            f"Layer violation: {source_layer} layer ({source_module}) depends on {target_layer} layer ({target_module})",
            ViolationType.LAYER_VIOLATION,
        )
        self.source_module = source_module
        self.target_module = target_module
        self.source_layer = source_layer
        self.target_layer = target_layer
        self.logger_service = logger_service
        self.console_service = console_service


class CircularDependency(DependencyViolation):
    """循環依存"""

    def __init__(self, cycle: list[str], logger_service=None, console_service=None) -> None:
        cycle_str = " -> ".join([*cycle, cycle[0]])
        super().__init__(f"Circular dependency detected: {cycle_str}", ViolationType.CIRCULAR_DEPENDENCY)
        self.cycle = cycle
        self.logger_service = logger_service
        self.console_service = console_service


class ExternalDependency(DependencyViolation):
    """外部パッケージ依存"""

    def __init__(
        self, module: str, external_package: str, layer: str = "unknown", logger_service=None, console_service=None
    ) -> None:
        severity = "warning" if layer != "domain" else "error"
        super().__init__(
            f"External dependency in {layer} layer: {module} imports {external_package}",
            ViolationType.EXTERNAL_DEPENDENCY,
            severity,
        )
        self.module = module
        self.external_package = external_package
        self.layer = layer
        self.logger_service = logger_service
        self.console_service = console_service


@dataclass
class FixSuggestion:
    """修正提案"""

    violation: DependencyViolation
    description: str
    code_example: str = ""


@dataclass
class DependencyMetrics:
    """依存関係メトリクス"""

    coupling: float = 0.0
    cohesion: float = 0.0
    max_depth: int = 0
    fan_in: dict[str, int] = field(default_factory=dict)
    fan_out: dict[str, int] = field(default_factory=dict)
    internal_dependencies: dict[str, int] = field(default_factory=dict)
    external_dependencies: dict[str, int] = field(default_factory=dict)

    def calculate_coupling(self) -> float:
        """結合度を計算"""
        if not self.fan_out:
            return 0.0
        total_dependencies = sum(self.fan_out.values())
        total_modules = len(self.fan_out)
        return total_dependencies / total_modules if total_modules > 0 else 0.0

    def calculate_cohesion(self, package: str) -> float:
        """凝集度を計算"""
        internal = self.internal_dependencies.get(package, 0)
        external = self.external_dependencies.get(package, 0)
        total = internal + external
        return internal / total if total > 0 else 0.0


class DependencyGraph:
    """依存関係グラフ"""

    def __init__(self, logger_service=None, console_service=None) -> None:
        self.nodes: dict[str, dict[str, object]] = {}
        self.edges: dict[str, set[str]] = defaultdict(set)
        self.reverse_edges: dict[str, set[str]] = defaultdict(set)
        self.logger_service = logger_service
        self.console_service = console_service

    def add_node(
        self, node: str, layer: str | None = None, attributes: dict[str, object] | None = None
    ) -> None:
        """Add a node to the graph.

        The layer argument is optional; if omitted, the existing layer value is kept while
        attributes can still be merged.
        """
        node_attributes = self.nodes.setdefault(node, {})
        if layer is not None:
            node_attributes["layer"] = layer
        if attributes:
            node_attributes.update(attributes)

    def add_edge(self, from_node: str, to_node: str) -> None:
        """エッジを追加"""
        self.edges[from_node].add(to_node)
        self.reverse_edges[to_node].add(from_node)

    def get_layer(self, node: str) -> str | None:
        """ノードのレイヤーを取得"""
        return self.nodes.get(node, {}).get("layer")

    def has_dependency(self, from_node: str, to_node: str) -> bool:
        """依存関係の存在確認"""
        return to_node in self.edges.get(from_node, set())

    def get_dependencies(self, node: str) -> set[str]:
        """ノードが依存するモジュールを取得"""
        return self.edges.get(node, set())

    def get_dependents(self, node: str) -> set[str]:
        """ノードに依存するモジュールを取得"""
        return self.reverse_edges.get(node, set())

    def find_cycles(self) -> list[list[str]]:
        """循環依存を検出(Tarjanのアルゴリズム)"""
        index_counter = [0]
        stack = []
        lowlinks = {}
        index = {}
        on_stack = {}
        cycles = []

        def strongconnect(node: str) -> None:
            index[node] = index_counter[0]
            lowlinks[node] = index_counter[0]
            index_counter[0] += 1
            stack.append(node)
            on_stack[node] = True
            for successor in self.edges.get(node, []):
                if successor not in index:
                    strongconnect(successor)
                    lowlinks[node] = min(lowlinks[node], lowlinks[successor])
                elif on_stack.get(successor, False):
                    lowlinks[node] = min(lowlinks[node], index[successor])
            if lowlinks[node] == index[node]:
                component = []
                while True:
                    w = stack.pop()
                    on_stack[w] = False
                    component.append(w)
                    if w == node:
                        break
                if len(component) > 1:
                    cycles.append(component)

        for node in self.nodes:
            if node not in index:
                strongconnect(node)
        return cycles

    def topological_sort(self) -> list[str]:
        """Return nodes ordered so dependencies appear before dependents."""
        dependency_counts = {node: len(self.edges.get(node, set())) for node in self.nodes}
        queue = deque(node for node, count in dependency_counts.items() if count == 0)
        ordered_nodes: list[str] = []

        while queue:
            node = queue.popleft()
            ordered_nodes.append(node)
            for dependent in self.reverse_edges.get(node, set()):
                dependency_counts[dependent] -= 1
                if dependency_counts[dependent] == 0:
                    queue.append(dependent)

        if len(ordered_nodes) != len(self.nodes):
            remaining = [node for node in self.nodes if node not in ordered_nodes]
            ordered_nodes.extend(remaining)

        return ordered_nodes


class DependencyAnalyzer:
    """依存関係アナライザー"""

    def __init__(self, logger_service=None, console_service=None) -> None:
        self.layer_hierarchy = ["domain", "application", "infrastructure", "presentation"]
        self.violations: list[DependencyViolation] = []
        self.exclusion_patterns: list[str] = []
        self.custom_rules: dict[str, Callable] = {}
        self.standard_libs = set(sys.stdlib_module_names)
        self.logger_service = logger_service
        self.console_service = console_service

    def add_exclusion_pattern(self, pattern: str) -> None:
        """除外パターンを追加"""
        self.exclusion_patterns.append(pattern)

    def add_custom_rule(self, name: str, rule_func: Callable) -> None:
        """カスタムルールを追加"""
        self.custom_rules[name] = rule_func

    def analyze_project(self, project_root: Path) -> DependencyGraph:
        """プロジェクトを分析"""
        graph = DependencyGraph()
        for py_file in project_root.rglob("*.py"):
            if self._should_exclude(py_file):
                continue
            module_path = self._get_module_path(py_file, project_root)
            layer = self._detect_layer(py_file)
            graph.add_node(module_path, layer=layer)
            dependencies = self._extract_dependencies(py_file)
            for dep in dependencies:
                dep_module = self._resolve_module_path(dep, project_root)
                if dep_module:
                    graph.add_edge(module_path, dep_module)
        return graph

    def detect_violations(self, graph: DependencyGraph) -> list[DependencyViolation]:
        """違反を検出"""
        violations: list[Any] = []
        violations.extend(self._check_layer_violations(graph))
        violations.extend(self._check_circular_dependencies(graph))
        violations.extend(self._apply_custom_rules(graph))
        self.violations = violations
        return violations

    def analyze_external_dependencies(self, graph: DependencyGraph) -> dict[str, list[str]]:
        """外部パッケージ依存を分析"""
        external_deps = defaultdict(list)
        for node in graph.nodes:
            layer = graph.get_layer(node)
            if not layer:
                continue
            for dep in graph.get_dependencies(node):
                if self._is_external_package(dep):
                    external_deps[layer].append(dep)
                    if layer == "domain" and dep not in self.standard_libs:
                        self.violations.append(ExternalDependency(node, dep, layer))
        return dict(external_deps)

    def calculate_metrics(self, graph: DependencyGraph) -> DependencyMetrics:
        """メトリクスを計算"""
        metrics = DependencyMetrics()
        for node in graph.nodes:
            metrics.fan_in[node] = len(graph.get_dependents(node))
            metrics.fan_out[node] = len(graph.get_dependencies(node))
        metrics.coupling = metrics.calculate_coupling()
        metrics.max_depth = self._calculate_max_depth(graph)
        self._calculate_package_dependencies(graph, metrics)
        return metrics

    def generate_fix_suggestions(self, violations: list[DependencyViolation]) -> list[FixSuggestion]:
        """修正提案を生成"""
        suggestions = []
        for violation in violations:
            if isinstance(violation, LayerViolation):
                suggestions.append(self._suggest_layer_fix(violation))
            elif isinstance(violation, CircularDependency):
                suggestions.append(self._suggest_circular_fix(violation))
            elif isinstance(violation, ExternalDependency):
                suggestions.append(self._suggest_external_fix(violation))
        return suggestions

    def export_to_mermaid(self, graph: DependencyGraph) -> str:
        """Mermaid形式でエクスポート"""
        lines = ["graph TD"]
        for node in graph.nodes:
            layer = graph.get_layer(node)
            style = self._get_mermaid_style(layer)
            lines.append(f'    {node}["{node}"]')
            if style:
                lines.append(f"    class {node} {style}")
        lines.extend(
            [f"    {from_node} --> {to_node}" for (from_node, to_nodes) in graph.edges.items() for to_node in to_nodes]
        )
        lines.extend(
            [
                "",
                "classDef domain fill:#f9f9f9,stroke:#333,stroke-width:2px",
                "classDef application fill:#e1f5fe,stroke:#01579b,stroke-width:2px",
                "classDef infrastructure fill:#fff3e0,stroke:#ef6c00,stroke-width:2px",
            ]
        )
        return "\n".join(lines)

    def export_to_graphviz(self, graph: DependencyGraph) -> str:
        """Graphviz DOT形式でエクスポート"""
        lines = ["digraph dependencies {"]
        lines.append("    rankdir=TB;")
        lines.append("    node [shape=box];")
        layers = defaultdict(list)
        for node in graph.nodes:
            layer = graph.get_layer(node) or "unknown"
            layers[layer].append(node)
        for layer, nodes in layers.items():
            lines.append(f"    subgraph cluster_{layer} {{")
            lines.append(f'        label="{layer}";')
            lines.append("        style=filled;")
            lines.append("        color=lightgrey;")
            lines.extend(f'        "{node}";' for node in nodes)
            lines.append("    }")
        lines.extend(
            [
                f'    "{from_node}" -> "{to_node}";'
                for (from_node, to_nodes) in graph.edges.items()
                for to_node in to_nodes
            ]
        )
        lines.append("}")
        return "\n".join(lines)

    def export_to_junit_xml(self, violations: list[DependencyViolation]) -> str:
        """JUnit XML形式でエクスポート"""
        lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        lines.append('<testsuites name="Dependency Analysis">')
        lines.append('  <testsuite name="DependencyChecks" tests="1">')
        if violations:
            lines.append('    <testcase name="dependency_violations" classname="DependencyAnalyzer">')
            for violation in violations:
                lines.append(f'      <failure message="{violation.message}" type="{violation.violation_type.value}">')
                lines.append(f"        {violation.message}")
                lines.append("      </failure>")
            lines.append("    </testcase>")
        else:
            lines.append('    <testcase name="no_violations" classname="DependencyAnalyzer"/>')
        lines.append("  </testsuite>")
        lines.append("</testsuites>")
        return "\n".join(lines)

    def export_to_json(
        self, graph: DependencyGraph, violations: list[DependencyViolation], metrics: DependencyMetrics
    ) -> str:
        """JSON形式でエクスポート"""
        data = {
            "dependencies": {node: list(deps) for (node, deps) in graph.edges.items()},
            "violations": [
                {
                    "type": v.violation_type.value,
                    "message": v.message,
                    "severity": v.severity,
                    "details": self._violation_to_dict(v),
                }
                for v in violations
            ],
            "metrics": {
                "coupling": metrics.coupling,
                "cohesion": metrics.cohesion,
                "max_depth": metrics.max_depth,
                "fan_in": metrics.fan_in,
                "fan_out": metrics.fan_out,
            },
        }
        return json.dumps(data, indent=2)

    def _should_exclude(self, file_path: Path) -> bool:
        """ファイルを除外すべきか判定"""
        if "__pycache__" in str(file_path):
            return True
        for pattern in self.exclusion_patterns:
            if pattern.startswith("*"):
                if str(file_path).endswith(pattern[1:]):
                    return True
            elif pattern.endswith("*"):
                if file_path.name.startswith(pattern[:-1]):
                    return True
            elif pattern in str(file_path):
                return True
        return False

    def _get_module_path(self, file_path: Path, project_root: Path) -> str:
        """ファイルパスからモジュールパスを取得"""
        relative_path = file_path.relative_to(project_root)
        module_path = str(relative_path).replace("/", ".").replace("\\", ".")
        if module_path.endswith(".py"):
            module_path = module_path[:-3]
        return module_path

    def _detect_layer(self, file_path: Path) -> str | None:
        """ファイルのレイヤーを検出"""
        path_str = str(file_path).replace("\\", "/")
        for layer in self.layer_hierarchy:
            if f"/{layer}/" in path_str:
                return layer
        return None

    def _extract_dependencies(self, file_path: Path) -> list[str]:
        """ファイルから依存関係を抽出"""
        dependencies = []
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    dependencies.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dependencies.append(node.module)
        except Exception:
            pass
        return dependencies

    def _resolve_module_path(self, import_path: str, _project_root: Path) -> str | None:
        """インポートパスを解決"""
        normalized = import_path
        if normalized.startswith("noveler."):
            normalized = normalized[len("noveler.") :]
        for layer in self.layer_hierarchy:
            if normalized.startswith(layer):
                return normalized
        if not normalized.startswith("."):
            return normalized
        return None

    def _is_external_package(self, module_path: str) -> bool:
        """外部パッケージかどうか判定"""
        for layer in self.layer_hierarchy:
            if module_path.startswith(layer):
                return False
        base_module = module_path.split(".")[0]
        return base_module not in self.standard_libs

    def _check_layer_violations(self, graph: DependencyGraph) -> list[LayerViolation]:
        """レイヤー違反をチェック"""
        violations: list[Any] = []
        for from_node in graph.nodes:
            from_layer = graph.get_layer(from_node)
            if not from_layer:
                continue
            from_index = self.layer_hierarchy.index(from_layer)
            for to_node in graph.get_dependencies(from_node):
                to_layer = graph.get_layer(to_node)
                if not to_layer:
                    continue
                to_index = self.layer_hierarchy.index(to_layer)
                if from_index < to_index:
                    violations.append(LayerViolation(from_node, to_node, from_layer, to_layer))
        return violations

    def _check_circular_dependencies(self, graph: DependencyGraph) -> list[CircularDependency]:
        """循環依存をチェック"""
        violations: list[Any] = []
        cycles = graph.find_cycles()
        violations.extend(CircularDependency(cycle) for cycle in cycles)
        return violations

    def _apply_custom_rules(self, graph: DependencyGraph) -> list[DependencyViolation]:
        """カスタムルールを適用"""
        violations: list[Any] = []
        for node in graph.nodes:
            dependencies = list(graph.get_dependencies(node))
            for rule_func in self.custom_rules.values():
                try:
                    rule_violations = rule_func(node, dependencies)
                    violations.extend(
                        DependencyViolation(violation_msg, ViolationType.CUSTOM, "warning")
                        for violation_msg in rule_violations
                    )
                except Exception:
                    pass
        return violations

    def _calculate_max_depth(self, graph: DependencyGraph) -> int:
        """最大依存深度を計算"""
        sorted_nodes = graph.topological_sort()
        depths = {}
        for node in sorted_nodes:
            deps = graph.get_dependencies(node)
            if not deps:
                depths[node] = 0
            else:
                depths[node] = max(depths.get(dep, 0) for dep in deps) + 1
        return max(depths.values()) if depths else 0

    def _calculate_package_dependencies(self, graph: DependencyGraph, metrics: DependencyMetrics) -> None:
        """パッケージ内外の依存を計算"""
        for node in graph.nodes:
            package = ".".join(node.split(".")[:2])
            internal_count = 0
            external_count = 0
            for dep in graph.get_dependencies(node):
                dep_package = ".".join(dep.split(".")[:2])
                if package == dep_package:
                    internal_count += 1
                else:
                    external_count += 1
            metrics.internal_dependencies[package] = metrics.internal_dependencies.get(package, 0) + internal_count
            metrics.external_dependencies[package] = metrics.external_dependencies.get(package, 0) + external_count

    def _suggest_layer_fix(self, violation: LayerViolation) -> FixSuggestion:
        """レイヤー違反の修正提案"""
        return FixSuggestion(
            violation=violation,
            description=f"Use dependency injection to remove direct dependency from {violation.source_layer} to {violation.target_layer}",
            code_example=f"\n# Instead of direct import):\n    @abstractmethod\n    def some_method(self):\n        pass\n\n# Inject dependency:\n    class {violation.source_module.split('.')[-1]}:\n    def __init__(self, dependency, logger_service=None, console_service=None):\n        self.dependency = dependency\n",
        )

    def _suggest_circular_fix(self, violation: CircularDependency) -> FixSuggestion:
        """循環依存の修正提案"""
        return FixSuggestion(
            violation=violation,
            description="Break circular dependency by introducing an interface or moving shared code to a common module",
            code_example="\n# Create a common module or interface to break the cycle\n# Move shared functionality to a separate module that both can import\n",
        )

    def _suggest_external_fix(self, violation: ExternalDependency) -> FixSuggestion:
        """外部依存の修正提案"""
        return FixSuggestion(
            violation=violation,
            description=f"Move external dependency '{violation.external_package}' usage to infrastructure layer",
            code_example=f"\n# Define interface in domain):\n    @abstractmethod\n    def do_something(self):\n        pass\n\n# Implement in infrastructure:\n    class ExternalServiceAdapter(ExternalServiceInterface):\n    def do_something(self):\n        # import {violation.external_package}  # Moved to top-level\n        # Use external package here\n",
        )

    def _get_mermaid_style(self, layer: str | None) -> str:
        """Mermaidのスタイルを取得"""
        styles = {
            "domain": "domain",
            "application": "application",
            "infrastructure": "infrastructure",
            "presentation": "presentation",
        }
        return styles.get(layer, "default")

    def _violation_to_dict(self, violation: DependencyViolation) -> dict:
        """違反を辞書に変換"""
        if isinstance(violation, LayerViolation):
            return {
                "source_module": violation.source_module,
                "target_module": violation.target_module,
                "source_layer": violation.source_layer,
                "target_layer": violation.target_layer,
            }
        if isinstance(violation, CircularDependency):
            return {"cycle": violation.cycle}
        if isinstance(violation, ExternalDependency):
            return {
                "module": violation.module,
                "external_package": violation.external_package,
                "layer": violation.layer,
            }
        return {}


def main() -> None:
    """メイン処理"""
    from noveler.infrastructure.di.container import resolve_service

    try:
        resolve_service("IConsoleService")
    except ValueError:
        from noveler.infrastructure.adapters.console_service_adapter import ConsoleServiceAdapter

        ConsoleServiceAdapter()
    parser = argparse.ArgumentParser(description="DDD依存関係分析ツール")
    parser.add_argument("path", help="分析対象のプロジェクトパス", nargs="?", default=".")
    parser.add_argument(
        "--format", choices=["text", "mermaid", "graphviz", "json", "junit"], default="text", help="出力形式"
    )
    parser.add_argument("--output", help="出力ファイル")
    parser.add_argument("--exclude", action="append", help="除外パターン")
    parser.add_argument("--fix-suggestions", action="store_true", help="修正提案を表示")
    args = parser.parse_args()
    analyzer = DependencyAnalyzer()
    if args.exclude:
        for pattern in args.exclude:
            analyzer.add_exclusion_pattern(pattern)
    project_root = Path(args.path)
    graph = analyzer.analyze_project(project_root)
    violations: Any = analyzer.detect_violations(graph)
    external_deps = analyzer.analyze_external_dependencies(graph)
    metrics = analyzer.calculate_metrics(graph)
    if args.format == "mermaid":
        output = analyzer.export_to_mermaid(graph)
    elif args.format == "graphviz":
        output = analyzer.export_to_graphviz(graph)
    elif args.format == "json":
        output = analyzer.export_to_json(graph, violations, metrics)
    elif args.format == "junit":
        output = analyzer.export_to_junit_xml(violations)
    else:
        output_lines = [
            "# Dependency Analysis Report",
            "",
            "## Summary",
            f"- Total modules: {len(graph.nodes)}",
            f"- Total dependencies: {sum(len(deps) for deps in graph.edges.values())}",
            f"- Violations found: {len(violations)}",
            f"- Coupling: {metrics.coupling:.2f}",
            f"- Max dependency depth: {metrics.max_depth}",
            "",
        ]
        if violations:
            output_lines.extend(["## Violations", ""])
            output_lines.extend(f"- [{v.severity.upper()}] {v.message}" for v in violations)
            output_lines.append("")
        if external_deps:
            output_lines.extend(["## External Dependencies by Layer", ""])
            for layer, deps in external_deps.items():
                output_lines.append(f"### {layer}")
                output_lines.extend(f"- {dep}" for dep in sorted(set(deps)))
                output_lines.append("")
        if args.fix_suggestions and violations:
            suggestions = analyzer.generate_fix_suggestions(violations)
            output_lines.extend(["## Fix Suggestions", ""])
            for s in suggestions:
                output_lines.append(f"### {s.violation.message}")
                output_lines.append(f"{s.description}")
                if s.code_example:
                    output_lines.append("```python")
                    output_lines.append(s.code_example.strip())
                    output_lines.append("```")
                output_lines.append("")
        output = "\n".join(output_lines)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        console.print(f"Report written to {args.output}")
    else:
        console.print(output)
    sys.exit(1 if violations else 0)


if __name__ == "__main__":
    main()
