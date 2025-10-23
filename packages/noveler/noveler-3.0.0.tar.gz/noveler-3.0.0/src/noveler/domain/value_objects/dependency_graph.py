"""Domain.value_objects.dependency_graph
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

from typing import TYPE_CHECKING, Any

"""依存関係グラフValue Object

仕様書: SPEC-CIRCULAR-IMPORT-DETECTION-001
"""


from dataclasses import dataclass, field

# NetworkX機能はシンプルなグラフ実装で代替
from noveler.domain.value_objects.import_statement import ImportStatement

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class DependencyNode:
    """依存関係グラフのノード"""

    module_name: str
    file_path: Path
    layer: str | None = None
    imports: list[ImportStatement] = field(default_factory=list)
    is_external: bool = False

    def add_import(self, import_stmt: ImportStatement) -> None:
        """インポート文の追加"""
        self.imports.append(import_stmt)

    def get_dependencies(self) -> set[str]:
        """依存先モジュール一覧の取得"""
        dependencies = set()
        for import_stmt in self.imports:
            dependencies.add(import_stmt.module_name)
            dependencies.update(import_stmt.get_potential_circular_targets())
        return dependencies


@dataclass(frozen=True)
class CircularPath:
    """循環パス情報"""

    modules: list[str]
    import_chain: list[ImportStatement]
    risk_level: int  # 1(低) - 5(高)
    fix_suggestions: list[str]

    def get_path_length(self) -> int:
        """循環パスの長さ"""
        return len(self.modules)

    def contains_module(self, module_name: str) -> bool:
        """指定モジュールを含むかチェック"""
        return module_name in self.modules

    def get_critical_edge(self) -> tuple[str, str] | None:
        """最も問題となるエッジを特定"""
        if len(self.modules) < 2:
            return None

        # 最もリスクの高いインポート文を見つける
        max_risk_import = max(
            self.import_chain,
            key=lambda imp: (
                5
                if imp.import_scope.name == "LOCAL"
                else 0 + 3
                if imp.is_ddd_layer_violation("")
                else 0 + 2
                if imp.import_type.name == "RELATIVE"
                else 0
            ),
            default=self.import_chain[0] if self.import_chain else None,
        )

        if max_risk_import:
            source_module = str(max_risk_import.source_file.stem)
            target_module = max_risk_import.module_name
            return (source_module, target_module)

        return (self.modules[0], self.modules[1])


@dataclass
class DependencyGraph:
    """依存関係グラフ"""

    nodes: dict[str, DependencyNode] = field(default_factory=dict)
    _adjacency_list: dict[str, set[str]] | None = field(default=None, init=False)

    def add_node(self, node: DependencyNode) -> None:
        """ノードの追加"""
        self.nodes[node.module_name] = node
        self._nx_graph = None  # グラフを無効化（再構築が必要）

    def add_dependency(self, source: str, target: str, import_stmt: ImportStatement) -> None:
        """依存関係の追加"""
        if source not in self.nodes:
            self.nodes[source] = DependencyNode(module_name=source, file_path=import_stmt.source_file)

        self.nodes[source].add_import(import_stmt)
        self._adjacency_list = None  # グラフを無効化

    def get_adjacency_list(self) -> dict[str, set[str]]:
        """隣接リストの取得（キャッシュ付き）"""
        if self._adjacency_list is None:
            self._build_adjacency_list()
        return self._adjacency_list

    def _build_adjacency_list(self) -> None:
        """隣接リストの構築"""
        self._adjacency_list = {}

        # 全ノードを初期化
        for module_name in self.nodes:
            self._adjacency_list[module_name] = set()

        # エッジ追加
        for source_name, source_node in self.nodes.items():
            for dependency in source_node.get_dependencies():
                if dependency in self.nodes:
                    self._adjacency_list[source_name].add(dependency)

    def detect_cycles(self) -> list[CircularPath]:
        """循環依存の検出（DFSベース実装）"""
        cycles = []
        adjacency_list = self.get_adjacency_list()

        # 強連結成分の検出（Tarjan's アルゴリズム簡易版）
        visited = set()
        stack = []
        low_links = {}
        indices = {}
        on_stack = set()
        index_counter = [0]

        def tarjan_scc(node: str) -> None:
            """Tarjan's アルゴリズムによる強連結成分検出"""
            indices[node] = index_counter[0]
            low_links[node] = index_counter[0]
            index_counter[0] += 1
            stack.append(node)
            on_stack.add(node)

            # 隣接ノードを探索
            for neighbor in adjacency_list.get(node, set()):
                if neighbor not in indices:
                    # 未訪問の場合は再帰的に探索
                    tarjan_scc(neighbor)
                    low_links[node] = min(low_links[node], low_links[neighbor])
                elif neighbor in on_stack:
                    # スタック上のノードの場合は low_link を更新
                    low_links[node] = min(low_links[node], indices[neighbor])

            # 強連結成分のルートノードの場合
            if low_links[node] == indices[node]:
                component = []
                while True:
                    current = stack.pop()
                    on_stack.remove(current)
                    component.append(current)
                    if current == node:
                        break

                # 複数のノードからなる強連結成分は循環
                if len(component) > 1:
                    import_chain = self._build_import_chain(component)
                    risk_level = self._calculate_risk_level(import_chain)
                    suggestions = self._generate_fix_suggestions(component, import_chain)

                    cycles.append(
                        CircularPath(
                            modules=component,
                            import_chain=import_chain,
                            risk_level=risk_level,
                            fix_suggestions=suggestions,
                        )
                    )

        # 全ノードに対してアルゴリズム実行
        for node_name in self.nodes:
            if node_name not in visited:
                tarjan_scc(node_name)
                visited.add(node_name)

        return cycles

    def _build_import_chain(self, cycle_modules: list[str]) -> list[ImportStatement]:
        """循環パスのインポートチェーン構築"""
        import_chain = []

        for i, module in enumerate(cycle_modules):
            next_module = cycle_modules[(i + 1) % len(cycle_modules)]

            # module から next_module へのインポート文を探す
            if module in self.nodes:
                for import_stmt in self.nodes[module].imports:
                    if (
                        import_stmt.module_name == next_module
                        or next_module in import_stmt.get_potential_circular_targets()
                    ):
                        import_chain.append(import_stmt)
                        break

        return import_chain

    def _calculate_risk_level(self, import_chain: list[ImportStatement]) -> int:
        """リスクレベルの計算"""
        if not import_chain:
            return 1

        risk_factors = 0

        for import_stmt in import_chain:
            # ローカルインポート
            if import_stmt.import_scope.name == "LOCAL":
                risk_factors += 2

            # 相対インポート
            if import_stmt.import_type.name == "RELATIVE":
                risk_factors += 1

            # DDD層違反
            if import_stmt.is_ddd_layer_violation(""):
                risk_factors += 3

        # 循環の長さも考慮
        path_length_factor = max(1, 6 - len(import_chain))

        total_risk = min(5, (risk_factors // len(import_chain)) + path_length_factor)
        return max(1, total_risk)

    def _generate_fix_suggestions(self, cycle_modules: list[str], import_chain: list[ImportStatement]) -> list[str]:
        """修正提案の生成"""
        suggestions = []

        # 一般的な修正提案
        suggestions.append("依存注入パターン(Protocol-based DI)による疎結合の実現")
        suggestions.append("共通のインターフェース層の抽出")

        # 特定の問題に対する提案
        has_relative = any(imp.import_type.name == "RELATIVE" for imp in import_chain)
        if has_relative:
            suggestions.append("相対インポートを絶対インポートに変更")

        has_layer_violation = any(imp.is_ddd_layer_violation("") for imp in import_chain)
        if has_layer_violation:
            suggestions.append("DDD層アーキテクチャに従った依存関係の見直し")

        # 循環が短い場合の具体的提案
        if len(cycle_modules) == 2:
            suggestions.append(
                f"'{cycle_modules[0]}'と'{cycle_modules[1]}'間の直接依存を避け、共通基底クラス/プロトコルを使用"
            )

        return suggestions

    def _fallback_cycle_detection(self) -> list[CircularPath]:
        """フォールバック循環検出"""
        # 簡易的なDFS による循環検出
        cycles = []
        visited = set()

        for start_module in self.nodes:
            if start_module not in visited:
                path = []
                cycle = self._dfs_cycle_detection(start_module, visited, path)
                if cycle:
                    cycles.append(cycle)

        return cycles

    def _dfs_cycle_detection(self, current: str, visited: set[str], path: list[str]) -> CircularPath | None:
        """深さ優先探索による循環検出"""
        if current in path:
            # 循環発見
            cycle_start = path.index(current)
            cycle_modules = [*path[cycle_start:], current]

            import_chain = self._build_import_chain(cycle_modules[:-1])  # 重複を除く
            risk_level = self._calculate_risk_level(import_chain)
            suggestions = self._generate_fix_suggestions(cycle_modules[:-1], import_chain)

            return CircularPath(
                modules=cycle_modules[:-1],
                import_chain=import_chain,
                risk_level=risk_level,
                fix_suggestions=suggestions,
            )

        if current in visited:
            return None

        visited.add(current)
        path.append(current)

        # 隣接ノードを探索
        if current in self.nodes:
            for dependency in self.nodes[current].get_dependencies():
                if dependency in self.nodes:
                    cycle = self._dfs_cycle_detection(dependency, visited, path)
                    if cycle:
                        return cycle

        path.pop()
        return None

    def get_module_stats(self) -> dict[str, dict]:
        """モジュール統計の取得"""
        stats = {}

        for module_name, node in self.nodes.items():
            stats[module_name] = {
                "import_count": len(node.imports),
                "dependencies": len(node.get_dependencies()),
                "layer": node.layer,
                "is_external": node.is_external,
            }

        return stats

    def find_shortest_path(self, source: str, target: str) -> list[str] | None:
        """最短依存パスの検索（BFS実装）"""
        if source not in self.nodes or target not in self.nodes:
            return None

        if source == target:
            return [source]

        adjacency_list = self.get_adjacency_list()
        queue = [(source, [source])]
        visited = {source}

        while queue:
            current, path = queue.pop(0)

            for neighbor in adjacency_list.get(current, set()):
                if neighbor == target:
                    return [*path, neighbor]

                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, [*path, neighbor]))

        return None

    def get_layer_violations(self) -> list[tuple[str, str, str]]:
        """DDD層違反の一覧取得"""
        violations: list[Any] = []

        layer_hierarchy = {"domain": 0, "application": 1, "infrastructure": 2, "presentation": 3}

        for source_name, source_node in self.nodes.items():
            source_layer = source_node.layer
            if source_layer not in layer_hierarchy:
                continue

            for import_stmt in source_node.imports:
                target_layer = import_stmt._infer_layer_from_module(import_stmt.module_name)
                if target_layer not in layer_hierarchy:
                    continue

                source_level = layer_hierarchy[source_layer]
                target_level = layer_hierarchy[target_layer]

                if source_level > target_level:
                    violations.append((source_name, import_stmt.module_name, f"{source_layer} -> {target_layer} 違反"))

        return violations
