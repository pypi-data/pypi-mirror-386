#!/usr/bin/env python3
"""アーキテクチャ依存関係分析器

仕様書: SPEC-DDD-AUTO-COMPLIANCE-001
依存関係方向の自動分析とアーキテクチャ健全性評価
"""

import ast
import re
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

try:
    import networkx as nx
except ImportError:
    # NetworkXが利用できない場合は基本的な依存関係分析のみ実行
    nx = None

# B30品質作業指示書遵守: Domain純粋性回復
# DDD準拠: Domain層はInfrastructure依存を排除
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from noveler.domain.interfaces.logger_service import ILoggerService


class DependencyType(Enum):
    """依存関係タイプ"""

    IMPORT = "import"
    INHERITANCE = "inheritance"
    COMPOSITION = "composition"
    AGGREGATION = "aggregation"
    USAGE = "usage"


class LayerDirection(Enum):
    """層間依存方向"""

    CORRECT = "correct"  # 正しい方向
    VIOLATION = "violation"  # 違反（逆方向）
    CIRCULAR = "circular"  # 循環依存
    SKIP_LAYER = "skip_layer"  # 層をスキップ


@dataclass
class DependencyEdge:
    """依存関係エッジ"""

    source_file: str
    target_file: str
    source_layer: str
    target_layer: str
    dependency_type: DependencyType
    line_number: int
    details: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LayerViolation:
    """層間違反"""

    source_layer: str
    target_layer: str
    violation_type: LayerDirection
    severity: str
    count: int
    examples: list[DependencyEdge]
    recommendation: str


@dataclass
class ArchitectureAnalysisResult:
    """アーキテクチャ分析結果"""

    project_root: str
    total_files_analyzed: int
    dependency_graph: Any  # nx.DiGraph when available
    layer_violations: list[LayerViolation]
    circular_dependencies: list[list[str]]
    architecture_health_score: float
    layer_metrics: dict[str, dict[str, Any]]
    recommendations: list[str]


class ArchitectureDependencyAnalyzer:
    """アーキテクチャ依存関係分析器

    責務:
        - プロジェクト全体の依存関係グラフ構築
        - DDD層間依存方向の検証
        - 循環依存の検出
        - アーキテクチャ健全性評価
        - 依存関係メトリクス算出

    設計原則:
        - 厳密なDDD層分離原則
        - グラフ理論による高精度分析
        - 拡張可能な分析ルール
    """

    def __init__(self, project_root: Path, logger: "ILoggerService | None" = None) -> None:
        """初期化

        Args:
            project_root: プロジェクトルートパス
            logger: ロガーインスタンス（依存性注入）
        """
        self.project_root = project_root
        # B20/DDD準拠: Domain層はInfrastructure層に依存しない（依存性注入）
        self.logger = logger

        # DDD層定義と階層順序
        self.layer_hierarchy = [
            "presentation",  # 最上位層
            "application",  # アプリケーション層
            "domain",  # ドメイン層（最も独立）
            "infrastructure",  # インフラ層（最下位、ただし上位層から呼ばれる）
        ]

        # 層間依存ルール定義
        self._initialize_dependency_rules()

        # 依存関係グラフ（NetworkXが利用可能な場合のみ）
        if nx is not None:
            self.dependency_graph = nx.DiGraph()
        else:
            # 基本的な辞書ベースの依存関係記録
            self.dependency_graph = {"nodes": set(), "edges": defaultdict(set)}
            if self.logger:
                self.logger.warning("NetworkXが利用できません。基本的な依存関係分析のみ実行します")

        # 分析結果キャッシュ
        self._analysis_cache = {}

    def _initialize_dependency_rules(self) -> None:
        """依存関係ルールの初期化"""
        # 許可される依存関係方向（from -> to）
        self.allowed_dependencies = {
            "presentation": ["application", "domain", "infrastructure.factories"],
            "application": ["domain"],
            "domain": [],  # ドメインは他の層に依存しない
            "infrastructure": ["domain", "application"],
        }

        # 禁止される依存関係
        self.forbidden_dependencies = {
            "domain": ["application", "infrastructure", "presentation"],
            "application": ["infrastructure.services", "presentation"],
            "infrastructure": ["presentation"],
        }

        # 例外許可パターン
        self.exception_patterns = {
            "presentation": [
                r"scripts\.infrastructure\.factories\.",  # DIファクトリーのみ許可
                r"scripts\.domain\.interfaces\.",  # ドメインインターフェースは許可
            ],
            "application": [
                r"scripts\.infrastructure\.adapters\.",  # アダプターは許可（インターフェース経由）
            ],
        }

    async def analyze_project_architecture(self) -> ArchitectureAnalysisResult:
        """プロジェクト全体のアーキテクチャ分析

        Returns:
            ArchitectureAnalysisResult: 分析結果
        """
        if self.logger:
            self.logger.info("アーキテクチャ依存関係分析開始")

        # 1. 依存関係グラフ構築
        await self._build_dependency_graph()

        # 2. 層間違反検出
        layer_violations = await self._detect_layer_violations()

        # 3. 循環依存検出
        circular_dependencies = self._detect_circular_dependencies()

        # 4. アーキテクチャ健全性評価
        health_score = self._calculate_architecture_health_score(layer_violations, circular_dependencies)

        # 5. 層別メトリクス算出
        layer_metrics = self._calculate_layer_metrics()

        # 6. 推奨事項生成
        recommendations = self._generate_architecture_recommendations(layer_violations, circular_dependencies)

        return ArchitectureAnalysisResult(
            project_root=str(self.project_root),
            total_files_analyzed=len(self.dependency_graph["nodes"])
            if not hasattr(self.dependency_graph, "nodes")
            else len(self.dependency_graph.nodes),
            dependency_graph=self.dependency_graph,
            layer_violations=layer_violations,
            circular_dependencies=circular_dependencies,
            architecture_health_score=health_score,
            layer_metrics=layer_metrics,
            recommendations=recommendations,
        )

    async def _build_dependency_graph(self) -> None:
        """依存関係グラフ構築"""
        if self.logger:
            self.logger.info("依存関係グラフ構築開始")

        # Pythonファイルを再帰的に検索
        python_files = list(self.project_root.rglob("*.py"))

        for file_path in python_files:
            if self._should_analyze_file(file_path):
                await self._analyze_file_dependencies(file_path)

        # NetworkX使用可否に応じた統計情報出力
        if nx is not None and hasattr(self.dependency_graph, "nodes"):
            nodes_count = len(self.dependency_graph.nodes)
            edges_count = len(self.dependency_graph.edges)
        else:
            nodes_count = len(self.dependency_graph["nodes"])
            edges_count = sum(len(edges) for edges in self.dependency_graph["edges"].values())

        if self.logger:
            self.logger.info("依存関係グラフ構築完了: %sノード, %sエッジ", nodes_count, edges_count)

    def _should_analyze_file(self, file_path: Path) -> bool:
        """ファイル分析対象判定

        Args:
            file_path: ファイルパス

        Returns:
            分析対象かどうか
        """
        # 除外パターン
        exclude_patterns = [r"__pycache__", r"\.git", r"test_.*\.py$", r".*_test\.py$", r"conftest\.py$"]

        file_str = str(file_path)
        return all(not re.search(pattern, file_str) for pattern in exclude_patterns)

    async def _analyze_file_dependencies(self, file_path: Path) -> None:
        """単一ファイルの依存関係分析

        Args:
            file_path: ファイルパス
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            # ファイルをグラフノードとして追加
            relative_path = str(file_path.relative_to(self.project_root))
            layer = self._determine_file_layer(relative_path)

            # NetworkX/辞書構造両対応でノード追加
            self._add_node(relative_path, layer=layer, file_path=str(file_path))

            # インポート依存関係を分析
            for node in ast.walk(tree):
                if (isinstance(node, ast.ImportFrom) and node.module) or isinstance(node, ast.Import):
                    await self._process_import_dependency(relative_path, node, file_path)

            # クラス継承関係を分析
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    await self._process_inheritance_dependency(relative_path, node, file_path)

        except (FileNotFoundError, SyntaxError, UnicodeDecodeError) as e:
            if self.logger:
                self.logger.warning("ファイル分析エラー: %s - %s", file_path, e)

    def _determine_file_layer(self, file_path: str) -> str:
        """ファイルの層判定

        Args:
            file_path: ファイルパス

        Returns:
            層名
        """
        for layer in self.layer_hierarchy:
            if f"noveler/{layer}" in file_path:
                return layer

        return "unknown"

    def _add_node(self, node_id: str, **attributes) -> None:
        """NetworkX/辞書構造両対応でノード追加

        Args:
            node_id: ノードID
            **attributes: ノード属性
        """
        if nx is not None and hasattr(self.dependency_graph, "add_node"):
            # NetworkX使用時
            self.dependency_graph.add_node(node_id, **attributes)
        else:
            # 辞書構造使用時
            self.dependency_graph["nodes"].add(node_id)
            # 属性は別途管理（必要に応じて拡張）
            if "node_attributes" not in self.dependency_graph:
                self.dependency_graph["node_attributes"] = {}
            self.dependency_graph["node_attributes"][node_id] = attributes

    def _add_edge(self, source: str, target: str, **attributes) -> None:
        """NetworkX/辞書構造両対応でエッジ追加

        Args:
            source: ソースノード
            target: ターゲットノード
            **attributes: エッジ属性
        """
        if nx is not None and hasattr(self.dependency_graph, "add_edge"):
            # NetworkX使用時
            self.dependency_graph.add_edge(source, target, **attributes)
        else:
            # 辞書構造使用時
            self.dependency_graph["edges"][source].add(target)
            # エッジ属性は別途管理（必要に応じて拡張）
            if "edge_attributes" not in self.dependency_graph:
                self.dependency_graph["edge_attributes"] = {}
            self.dependency_graph["edge_attributes"][(source, target)] = attributes

    def _get_edges_with_data(self):
        """NetworkX/辞書構造両対応でエッジとデータを取得

        Returns:
            エッジとデータのイテレータ
        """
        if nx is not None and hasattr(self.dependency_graph, "edges"):
            # NetworkX使用時
            return self.dependency_graph.edges(data=True)
        else:
            # 辞書構造使用時
            edge_attributes = self.dependency_graph.get("edge_attributes", {})
            for source, targets in self.dependency_graph["edges"].items():
                for target in targets:
                    edge_data = edge_attributes.get((source, target), {})
                    yield source, target, edge_data

    def _get_nodes_with_data(self):
        """NetworkX/辞書構造両対応でノードとデータを取得

        Returns:
            ノードとデータのイテレータ
        """
        if nx is not None and hasattr(self.dependency_graph, "nodes"):
            # NetworkX使用時
            return self.dependency_graph.nodes(data=True)
        else:
            # 辞書構造使用時
            node_attributes = self.dependency_graph.get("node_attributes", {})
            for node in self.dependency_graph["nodes"]:
                node_data = node_attributes.get(node, {})
                yield node, node_data

    def _get_in_degree(self, node: str) -> int:
        """NetworkX/辞書構造両対応でノードの入次数を取得"""
        if nx is not None and hasattr(self.dependency_graph, "in_degree"):
            return self.dependency_graph.in_degree(node)
        # 辞書構造での入次数計算
        count = 0
        for targets in self.dependency_graph["edges"].values():
            if node in targets:
                count += 1
        return count

    def _get_out_degree(self, node: str) -> int:
        """NetworkX/辞書構造両対応でノードの出次数を取得"""
        if nx is not None and hasattr(self.dependency_graph, "out_degree"):
            return self.dependency_graph.out_degree(node)
        # 辞書構造での出次数計算
        return len(self.dependency_graph["edges"].get(node, set()))

    async def _process_import_dependency(self, source_file: str, import_node: ast.AST, file_path: Path) -> None:
        """インポート依存関係処理

        Args:
            source_file: ソースファイル
            import_node: インポートノード
            file_path: ファイルパス
        """
        if isinstance(import_node, ast.ImportFrom) and import_node.module:
            target_module = import_node.module
        elif isinstance(import_node, ast.Import):
            if import_node.names:
                target_module = import_node.names[0].name
            else:
                return
        else:
            return

        # プロジェクト内モジュールのみ処理
        if not target_module.startswith("scripts"):
            return

        # ターゲットファイルパスを推定
        target_file = self._resolve_module_to_file(target_module)
        if target_file and target_file != source_file:
            # 依存関係エッジを追加
            edge_data: dict[str, Any] = DependencyEdge(
                source_file=source_file,
                target_file=target_file,
                source_layer=self._determine_file_layer(source_file),
                target_layer=self._determine_file_layer(target_file),
                dependency_type=DependencyType.IMPORT,
                line_number=import_node.lineno,
                details=f"import {target_module}",
                metadata={"module": target_module},
            )

            self._add_edge(source_file, target_file, **edge_data.__dict__)

    def _resolve_module_to_file(self, module_name: str) -> str | None:
        """モジュール名からファイルパス推定

        Args:
            module_name: モジュール名

        Returns:
            ファイルパス（推定できない場合はNone）
        """
        # noveler.domain.entities.user -> scripts/domain/entities/user.py
        path_parts = module_name.split(".")
        relative_path = "/".join(path_parts) + ".py"

        full_path = self.project_root / relative_path
        if full_path.exists():
            return relative_path

        # __init__.pyファイルの可能性
        init_path = "/".join(path_parts) + "/__init__.py"
        full_init_path = self.project_root / init_path
        if full_init_path.exists():
            return init_path

        return None

    async def _process_inheritance_dependency(
        self, source_file: str, class_node: ast.ClassDef, file_path: Path
    ) -> None:
        """継承依存関係処理

        Args:
            source_file: ソースファイル
            class_node: クラスノード
            file_path: ファイルパス
        """
        for base in class_node.bases:
            if isinstance(base, ast.Attribute):
                # module.ClassName形式
                ast.unparse(base.value) if hasattr(base, "value") else None
            elif isinstance(base, ast.Name):
                # ClassName形式（同一ファイル内またはimport済み）
                pass
            else:
                continue

            # 継承関係をエッジとして追加（詳細な実装は省略）
            # 実際の実装では、ベースクラスの定義ファイルを特定し、
            # 継承関係としてグラフに追加する

    async def _detect_layer_violations(self) -> list[LayerViolation]:
        """層間違反検出

        Returns:
            層間違反リスト
        """
        violations: list[Any] = []
        violation_groups = defaultdict(list)

        # 各エッジについて層間依存チェック
        for _source, _target, edge_data in self._get_edges_with_data():
            source_layer = edge_data.get("source_layer", "unknown")
            target_layer = edge_data.get("target_layer", "unknown")

            violation_type = self._check_layer_dependency(source_layer, target_layer, edge_data.get("details", ""))

            if violation_type != LayerDirection.CORRECT:
                violation_key = (source_layer, target_layer, violation_type)
                violation_groups[violation_key].append(DependencyEdge(**edge_data))

        # 違反グループを LayerViolation として整理
        for (source_layer, target_layer, violation_type), edges in violation_groups.items():
            violations.append(
                LayerViolation(
                    source_layer=source_layer,
                    target_layer=target_layer,
                    violation_type=violation_type,
                    severity=self._determine_violation_severity(violation_type, len(edges)),
                    count=len(edges),
                    examples=edges[:5],  # 最大5個の例
                    recommendation=self._get_layer_violation_recommendation(source_layer, target_layer, violation_type),
                )
            )

        return violations

    def _check_layer_dependency(self, source_layer: str, target_layer: str, details: str) -> LayerDirection:
        """層間依存関係チェック

        Args:
            source_layer: ソース層
            target_layer: ターゲット層
            details: 依存詳細

        Returns:
            依存方向の評価結果
        """
        # 同一層内は許可
        if source_layer == target_layer:
            return LayerDirection.CORRECT

        # 未知の層は除外
        if source_layer == "unknown" or target_layer == "unknown":
            return LayerDirection.CORRECT

        # 例外パターンチェック
        if self._is_exception_allowed(source_layer, details):
            return LayerDirection.CORRECT

        # 許可された依存関係チェック
        allowed = self.allowed_dependencies.get(source_layer, [])

        for allowed_target in allowed:
            if target_layer == allowed_target or target_layer.startswith(allowed_target + "."):
                return LayerDirection.CORRECT

        # 禁止された依存関係チェック
        forbidden = self.forbidden_dependencies.get(source_layer, [])

        for forbidden_target in forbidden:
            if target_layer == forbidden_target or target_layer.startswith(forbidden_target + "."):
                return LayerDirection.VIOLATION

        # 層階層違反チェック
        try:
            source_index = self.layer_hierarchy.index(source_layer)
            target_index = self.layer_hierarchy.index(target_layer)

            # ドメイン層への依存は常に許可（interface経由）
            if target_layer == "domain":
                return LayerDirection.CORRECT

            # infrastructureから上位層への依存は違反
            if source_layer == "infrastructure" and target_index < source_index:
                return LayerDirection.VIOLATION

            # 上位層から下位層への依存は基本的に許可
            if source_index <= target_index:
                return LayerDirection.CORRECT
            return LayerDirection.SKIP_LAYER

        except ValueError:
            # 層階層に含まれない場合は許可
            return LayerDirection.CORRECT

    def _is_exception_allowed(self, source_layer: str, details: str) -> bool:
        """例外許可パターンチェック

        Args:
            source_layer: ソース層
            details: 依存詳細

        Returns:
            例外として許可されるかどうか
        """
        exception_patterns = self.exception_patterns.get(source_layer, [])

        return any(re.search(pattern, details) for pattern in exception_patterns)

    def _detect_circular_dependencies(self) -> list[list[str]]:
        """循環依存検出

        Returns:
            循環依存パスのリスト
        """
        try:
            if nx is not None and hasattr(self.dependency_graph, "nodes"):
                # NetworkXの循環検出機能を使用
                cycles = list(nx.simple_cycles(self.dependency_graph))

                # 長い循環を短いものでフィルタリング
                filtered_cycles = []
                for cycle in cycles:
                    if len(cycle) <= 10:  # 10ファイル以下の循環のみ:
                        filtered_cycles.append(cycle)

                # 重要度でソート（短い循環ほど重要）
                filtered_cycles.sort(key=len)

                return filtered_cycles[:20]  # 最大20個まで
            # 基本的な循環検出（DFS使用）
            return self._detect_cycles_basic()

        except Exception as e:
            if self.logger:
                self.logger.exception("循環依存検出エラー: %s", e)
            return []

    def _detect_cycles_basic(self) -> list[list[str]]:
        """基本的な循環検出（NetworkX不使用）"""
        cycles = []
        visited = set()
        rec_stack = set()
        path = []

        def dfs_visit(node: str) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            # 隣接ノードを探索
            neighbors = self.dependency_graph["edges"].get(node, set())
            for neighbor in neighbors:
                if neighbor not in visited:
                    dfs_visit(neighbor)
                elif neighbor in rec_stack:
                    # 循環検出
                    cycle_start = path.index(neighbor)
                    cycle = [*path[cycle_start:], neighbor]
                    if len(cycle) <= 10:  # 短い循環のみ記録:
                        cycles.append(cycle)

            path.pop()
            rec_stack.remove(node)

        # 全ノードを探索
        for node in self.dependency_graph["nodes"]:
            if node not in visited:
                dfs_visit(node)

        # 重要度でソートして上位20個を返す
        cycles.sort(key=len)
        return cycles[:20]

    def _calculate_architecture_health_score(
        self, layer_violations: list[LayerViolation], circular_dependencies: list[list[str]]
    ) -> float:
        """アーキテクチャ健全性スコア算出

        Args:
            layer_violations: 層間違反リスト
            circular_dependencies: 循環依存リスト

        Returns:
            健全性スコア（0.0-1.0）
        """
        base_score = 1.0

        # 層間違反ペナルティ
        for violation in layer_violations:
            if violation.violation_type == LayerDirection.VIOLATION:
                if violation.severity == "CRITICAL":
                    base_score -= 0.1 * violation.count
                elif violation.severity == "HIGH":
                    base_score -= 0.05 * violation.count
                else:
                    base_score -= 0.02 * violation.count

        # 循環依存ペナルティ
        for cycle in circular_dependencies:
            cycle_penalty = min(0.1, 0.02 * len(cycle))
            base_score -= cycle_penalty

        return max(0.0, min(1.0, base_score))

    def _calculate_layer_metrics(self) -> dict[str, dict[str, Any]]:
        """層別メトリクス算出

        Returns:
            層別メトリクス
        """
        metrics = {}

        for layer in self.layer_hierarchy:
            layer_nodes = [node for node, data in self._get_nodes_with_data() if data.get("layer") == layer]

            if layer_nodes:
                # 入次数（依存される数）
                in_degrees = [self._get_in_degree(node) for node in layer_nodes]
                # 出次数（依存する数）
                out_degrees = [self._get_out_degree(node) for node in layer_nodes]

                metrics[layer] = {
                    "file_count": len(layer_nodes),
                    "avg_incoming_dependencies": sum(in_degrees) / len(in_degrees) if in_degrees else 0,
                    "avg_outgoing_dependencies": sum(out_degrees) / len(out_degrees) if out_degrees else 0,
                    "max_incoming_dependencies": max(in_degrees) if in_degrees else 0,
                    "max_outgoing_dependencies": max(out_degrees) if out_degrees else 0,
                    "total_dependencies": sum(in_degrees) + sum(out_degrees),
                }

        return metrics

    def _determine_violation_severity(self, violation_type: LayerDirection, count: int) -> str:
        """違反重要度決定

        Args:
            violation_type: 違反タイプ
            count: 違反数

        Returns:
            重要度
        """
        if violation_type == LayerDirection.VIOLATION:
            if count >= 10:
                return "CRITICAL"
            if count >= 5:
                return "HIGH"
            return "MEDIUM"
        if violation_type == LayerDirection.CIRCULAR:
            return "HIGH"
        if violation_type == LayerDirection.SKIP_LAYER:
            return "MEDIUM"
        return "LOW"

    def _get_layer_violation_recommendation(
        self, source_layer: str, target_layer: str, violation_type: LayerDirection
    ) -> str:
        """層間違反推奨事項取得

        Args:
            source_layer: ソース層
            target_layer: ターゲット層
            violation_type: 違反タイプ

        Returns:
            推奨事項
        """
        recommendations = {
            (
                "domain",
                "infrastructure",
            ): "ドメインインターフェースを定義し、インフラ層でアダプターとして実装してください",
            ("domain", "application"): "ドメインサービスまたはアプリケーションサービスに機能を移動してください",
            ("domain", "presentation"): "プレゼンテーション関連のロジックをドメインから分離してください",
            ("application", "presentation"): "プレゼンテーション層からアプリケーション層を呼び出すよう変更してください",
            (
                "infrastructure",
                "presentation",
            ): "プレゼンテーション層とインフラ層の直接連携を避け、アプリケーション層を経由してください",
        }

        recommendation = recommendations.get((source_layer, target_layer))
        if recommendation:
            return recommendation

        if violation_type == LayerDirection.CIRCULAR:
            return "循環依存を解消するため、インターフェースの抽出や層の再設計を検討してください"
        if violation_type == LayerDirection.SKIP_LAYER:
            return "適切な層を経由した依存関係に変更し、層の責務を明確にしてください"
        return f"{source_layer}層から{target_layer}層への依存関係を見直し、DDD原則に従った設計に修正してください"

    def _generate_architecture_recommendations(
        self, layer_violations: list[LayerViolation], circular_dependencies: list[list[str]]
    ) -> list[str]:
        """アーキテクチャ推奨事項生成

        Args:
            layer_violations: 層間違反リスト
            circular_dependencies: 循環依存リスト

        Returns:
            推奨事項リスト
        """
        recommendations = []

        # 重要な違反への対応
        critical_violations = [v for v in layer_violations if v.severity == "CRITICAL"]
        if critical_violations:
            recommendations.append(f"クリティカルな層間違反 {len(critical_violations)} 件の即座な修正が必要です")

        # 循環依存への対応
        if circular_dependencies:
            recommendations.append(
                f"循環依存 {len(circular_dependencies)} 件の解消が必要です。インターフェース抽出を検討してください"
            )

        # ドメイン層の独立性
        domain_violations = [v for v in layer_violations if v.source_layer == "domain"]
        if domain_violations:
            recommendations.append("ドメイン層の独立性を保つため、外部層への依存を排除してください")

        # インフラ層の逆転
        infra_violations = [
            v
            for v in layer_violations
            if v.source_layer == "infrastructure" and v.target_layer in ["presentation", "application"]
        ]
        if infra_violations:
            recommendations.append("インフラ層から上位層への依存を避け、依存関係逆転原則を適用してください")

        return recommendations

    def export_dependency_graph(self, output_path: Path, format_type: str = "graphml") -> None:
        """依存関係グラフエクスポート

        Args:
            output_path: 出力パス
            format_type: フォーマット（graphml/gexf/dot）
        """
        if format_type == "graphml":
            nx.write_graphml(self.dependency_graph, output_path)
        elif format_type == "gexf":
            nx.write_gexf(self.dependency_graph, output_path)
        elif format_type == "dot":
            nx.drawing.nx_pydot.write_dot(self.dependency_graph, output_path)
        else:
            msg = f"サポートされていないフォーマット: {format_type}"
            raise ValueError(msg)

        if self.logger:
            self.logger.info("依存関係グラフをエクスポートしました: %s", output_path)
