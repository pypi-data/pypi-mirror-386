#!/usr/bin/env python3

"""Domain.services.infrastructure_coordination_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

from typing import Any

"""インフラ協調サービス(ドメインサービス)

サービス間の協調・調整を行うドメインサービス。
依存関係の解決、実行順序の最適化を担当。
"""


from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from noveler.domain.value_objects.infrastructure_configuration import ServiceConfiguration


@dataclass
class DependencyGraph:
    """依存関係グラフ(値オブジェクト)"""

    nodes: set[str]
    edges: dict[str, list[str]]

    def add_dependency(self, service: str, dependency: str) -> None:
        """依存関係を追加"""
        self.nodes.add(service)
        self.nodes.add(dependency)

        if service not in self.edges:
            self.edges[service] = []
        self.edges[service].append(dependency)

    def has_cycle(self) -> bool:
        """循環依存をチェック"""
        visited = set()
        rec_stack = set()

        def has_cycle_util(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in self.edges.get(node, []):
                if neighbor not in visited:
                    if has_cycle_util(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        return any(node not in visited and has_cycle_util(node) for node in self.nodes)


class InfrastructureCoordinationService:
    """インフラ協調サービス

    ビジネスルール:
    1. サービス間の依存関係を解決する
    2. 実行順序を最適化する
    3. 循環依存を検出・防止する
    4. 並列実行可能なサービスを特定する
    """

    def resolve_dependencies(
        self,
        service_configs: list[ServiceConfiguration],
    ) -> list[ServiceConfiguration]:
        """依存関係を解決して実行順序を決定

        Args:
            service_configs: サービス設定のリスト

        Returns:
            実行順序に並び替えられたサービス設定のリスト

        Raises:
            ValueError: 循環依存が検出された場合
        """
        # 依存関係グラフを構築
        dependency_graph = self._build_dependency_graph(service_configs)

        # 循環依存をチェック
        if dependency_graph.has_cycle():
            msg = "サービス間に循環依存が検出されました"
            raise ValueError(msg)

        # トポロジカルソートで実行順序を決定
        return self._topological_sort(service_configs, dependency_graph)

    def get_parallel_execution_groups(
        self,
        service_configs: list[ServiceConfiguration],
    ) -> list[list[ServiceConfiguration]]:
        """並列実行可能なサービスグループを取得

        Args:
            service_configs: サービス設定のリスト

        Returns:
            並列実行可能なサービスのグループのリスト
        """
        ordered_services = self.resolve_dependencies(service_configs)
        service_map = {config.name: config for config in ordered_services}

        # 依存関係のレベルを計算
        levels = self._calculate_dependency_levels(ordered_services)

        # レベル別にグループ化
        groups = {}
        for service_name, level in levels.items():
            if level not in groups:
                groups[level] = []
            groups[level].append(service_map[service_name])

        # レベル順でソート
        return [groups[level] for level in sorted(groups.keys())]

    def validate_service_configuration(
        self, service_config: ServiceConfiguration, existing_configs: list[ServiceConfiguration]
    ) -> list[str]:
        """サービス設定の妥当性を検証

        Args:
            service_config: 検証するサービス設定
            existing_configs: 既存のサービス設定のリスト

        Returns:
            検証エラーメッセージのリスト(空の場合は妥当)
        """
        errors: list[Any] = []
        existing_names = {config.name for config in existing_configs}

        # 名前の重複チェック
        if service_config.name in existing_names:
            errors.append(f"サービス名 '{service_config.name}' は既に存在します")

        # 依存関係の存在チェック
        errors.extend(
            f"依存サービス '{dependency}' が見つかりません"
            for dependency in service_config.dependencies
            if dependency not in existing_names and dependency != service_config.name
        )

        # フォールバックサービスの存在チェック
        if service_config.fallback_service:
            if service_config.fallback_service not in existing_names:
                errors.append(f"フォールバックサービス '{service_config.fallback_service}' が見つかりません")

            # フォールバックサービスが同じタイプかチェック
            fallback_config: dict[str, Any] = next(
                (config for config in existing_configs if config.name == service_config.fallback_service), None
            )

            if fallback_config and fallback_config.service_type != service_config.service_type:
                errors.append(f"フォールバックサービスのタイプが一致しません: {service_config.name}")

        # 自己依存のチェック
        if service_config.name in service_config.dependencies:
            errors.append("サービスは自分自身に依存できません")

        return errors

    def optimize_execution_order(
        self, service_configs: list[ServiceConfiguration], optimization_criteria: str
    ) -> list[ServiceConfiguration]:
        """実行順序を最適化

        Args:
            service_configs: サービス設定のリスト
            optimization_criteria: 最適化基準 ("priority", "execution_time", "resource_usage")

        Returns:
            最適化された実行順序のサービス設定のリスト
        """
        # まず依存関係を解決
        base_order = self.resolve_dependencies(service_configs)

        if optimization_criteria == "priority":
            # 依存関係を保ちつつ優先度でソート
            return self._optimize_by_priority(base_order)
        if optimization_criteria == "execution_time":
            # 実行時間を考慮した最適化(仮実装)
            return self._optimize_by_execution_time(base_order)
        if optimization_criteria == "resource_usage":
            # リソース使用量を考慮した最適化(仮実装)
            return self._optimize_by_resource_usage(base_order)
        return base_order

    def _build_dependency_graph(
        self,
        service_configs: list[ServiceConfiguration],
    ) -> DependencyGraph:
        """依存関係グラフを構築"""
        graph = DependencyGraph(nodes=set(), edges={})

        for config in service_configs:
            graph.nodes.add(config.name)
            for dependency in config.dependencies:
                graph.add_dependency(config.name, dependency)

        return graph

    def _topological_sort(
        self, service_configs: list[ServiceConfiguration], dependency_graph: DependencyGraph
    ) -> list[ServiceConfiguration]:
        """トポロジカルソートで実行順序を決定"""
        service_map = {config.name: config for config in service_configs}
        in_degree = dict.fromkeys(dependency_graph.nodes, 0)

        # 入次数を計算
        for node in dependency_graph.nodes:
            for neighbor in dependency_graph.edges.get(node, []):
                in_degree[neighbor] += 1

        # 入次数0のノードをキューに追加
        queue = [node for node, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            # 優先度でソート(同じレベルの場合)
            queue.sort(key=lambda name: service_map[name].priority, reverse=True)
            current = queue.pop(0)
            result.append(service_map[current])

            # 隣接ノードの入次数を減らす
            for neighbor in dependency_graph.edges.get(current, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return result

    def _calculate_dependency_levels(
        self,
        ordered_services: list[ServiceConfiguration],
    ) -> dict[str, int]:
        """依存関係のレベルを計算"""
        levels = {}
        service_map = {config.name: config for config in ordered_services}

        def calculate_level(service_name: str) -> int:
            if service_name in levels:
                return levels[service_name]

            config = service_map[service_name]
            if not config.dependencies:
                levels[service_name] = 0
                return 0

            max_dependency_level = max(calculate_level(dep) for dep in config.dependencies)
            levels[service_name] = max_dependency_level + 1
            return levels[service_name]

        for config in ordered_services:
            calculate_level(config.name)

        return levels

    def _optimize_by_priority(
        self,
        base_order: list[ServiceConfiguration],
    ) -> list[ServiceConfiguration]:
        """優先度による最適化"""
        {config.name: config for config in base_order}
        levels = self._calculate_dependency_levels(base_order)

        # レベル別にグループ化
        level_groups = {}
        for config in base_order:
            level = levels[config.name]
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(config)

        # 各レベル内で優先度でソート
        result = []
        for level in sorted(level_groups.keys()):
            group = level_groups[level]
            group.sort(key=lambda config: config.priority, reverse=True)
            result.extend(group)

        return result

    def _optimize_by_execution_time(
        self,
        base_order: list[ServiceConfiguration],
    ) -> list[ServiceConfiguration]:
        """実行時間による最適化(仮実装)"""
        # 実際の実装では、過去の実行時間統計を使用
        return sorted(base_order, key=lambda config: config.priority)

    def _optimize_by_resource_usage(
        self,
        base_order: list[ServiceConfiguration],
    ) -> list[ServiceConfiguration]:
        """リソース使用量による最適化(仮実装)"""
        # 実際の実装では、メモリ使用量やCPU使用量を考慮
        return sorted(base_order, key=lambda config: config.batch_size, reverse=True)
