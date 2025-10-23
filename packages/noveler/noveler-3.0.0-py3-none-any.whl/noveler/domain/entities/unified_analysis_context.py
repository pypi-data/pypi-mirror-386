#!/usr/bin/env python3

"""Domain.entities.unified_analysis_context
Where: Domain entity describing context used in unified analysis.
What: Aggregates contextual data fed into analysis engines.
Why: Ensures analyses operate on consistent context information.
"""

from __future__ import annotations

"""統合分析コンテキストエンティティ

統合コンテキスト分析で使用する全ての情報を保持・管理するドメインエンティティ。
全A31項目（68項目）の完全コンテキスト保持と段階間関係性維持を実現。
"""


import hashlib
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from collections.abc import Mapping

from noveler.domain.value_objects.analysis_scope import AnalysisScope

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class A31ChecklistItem:
    """A31チェックリスト項目"""

    id: str
    item: str
    phase: str
    required: bool
    item_type: str
    reference_guides: list[str] = field(default_factory=list)
    input_files: list[str] = field(default_factory=list)
    output_files: list[str] = field(default_factory=list)
    output_validation: list[str] = field(default_factory=list)
    status: bool = False
    auto_fix_supported: bool = False
    auto_fix_level: str | None = None

    def get_priority_score(self) -> float:
        """優先度スコアの計算

        Returns:
            float: 優先度スコア（高いほど重要）
        """
        base_score = 10.0 if self.required else 5.0

        # Phase別重み付け
        phase_weights = {
            "Phase2_執筆段階": 3.0,
            "Phase3_推敲段階": 2.5,
            "Phase4_品質チェック段階": 2.0,
            "Phase1_設計・下書き段階": 1.5,
            "Phase5_完成処理段階": 1.0,
            "Phase0_自動執筆開始": 1.0,
            "公開前最終確認": 1.2,
        }

        phase_weight = phase_weights.get(self.phase, 1.0)
        return base_score * phase_weight

    def has_cross_references(self) -> bool:
        """相互参照の有無

        Returns:
            bool: 相互参照があるかどうか
        """
        return len(self.input_files) > 0 or len(self.output_files) > 0


@dataclass
class ProjectContext:
    """プロジェクトコンテキスト"""

    project_name: str
    project_root: Path
    episode_number: int
    manuscript_path: Path
    character_settings: dict[str, Any] = field(default_factory=dict)
    plot_context: dict[str, Any] = field(default_factory=dict)
    world_settings: dict[str, Any] = field(default_factory=dict)
    previous_episodes: list[dict[str, Any]] = field(default_factory=list)

    def get_context_fingerprint(self) -> str:
        """コンテキストフィンガープリントの生成

        Returns:
            str: ユニークなコンテキスト識別子
        """
        context_data: dict[str, Any] = (
            f"{self.project_name}_{self.episode_number}_{len(self.character_settings)}_{len(self.plot_context)}"
        )
        return hashlib.md5(context_data.encode()).hexdigest()[:12]


@dataclass
class CrossReferenceData:
    """相互参照データ"""

    relationship_count: int
    file_dependencies: dict[str, list[str]] = field(default_factory=dict)
    content_relationships: dict[str, list[str]] = field(default_factory=dict)
    phase_interactions: dict[str, list[str]] = field(default_factory=dict)

    def get_relationship_density(self) -> float:
        """関係密度の計算

        Returns:
            float: 関係密度（0.0-1.0）
        """
        if self.relationship_count == 0:
            return 0.0

        total_possible = 68 * (68 - 1) // 2  # 68項目の完全グラフ
        return min(self.relationship_count / total_possible, 1.0)


@dataclass
class UnifiedAnalysisContext:
    """統合分析コンテキストエンティティ

    統合コンテキスト分析で使用する全ての情報を統合管理。
    全A31項目（68項目）の完全コンテキスト保持と関係性維持を実現。
    """

    manuscript_content: str
    a31_checklist: dict[str, list[A31ChecklistItem]] | Any
    project_context: ProjectContext
    episode_context: dict[str, Any]
    cross_reference_data: CrossReferenceData
    preservation_scope: AnalysisScope

    # メタデータ
    context_version: str = "1.0"
    creation_timestamp: str | None = None
    content_hash: str | None = None

    def __post_init__(self) -> None:
        """初期化後処理"""
        if not isinstance(self.a31_checklist, Mapping):
            self.a31_checklist = {}

        if self.content_hash is None:
            self.content_hash = self._calculate_content_hash()

    # ---- checklist helpers -------------------------------------------------
    def _iter_checklist_groups(self) -> list[list[A31ChecklistItem]]:
        """安全にチェックリスト群をイテレートする。

        Mock が渡された場合やリスト以外の値が含まれる場合でも
        可能な範囲で変換し、問題がある項目は無視する。
        """

        if not getattr(self, "a31_checklist", None):
            return []

        try:
            values = self.a31_checklist.values()
        except AttributeError:
            return []

        try:
            iterable_values = list(values)
        except TypeError:
            return []

        groups: list[list[A31ChecklistItem]] = []
        for items in iterable_values:
            if isinstance(items, list):
                groups.append(items)
                continue
            try:
                converted = list(items)
            except TypeError:
                continue
            groups.append(converted)  # type: ignore[arg-type]
        return groups

    @classmethod
    def from_a31_yaml(
        cls,
        a31_yaml_content: dict[str, Any],
        manuscript_content: str,
        project_context: ProjectContext,
        preservation_scope: AnalysisScope = AnalysisScope.COMPREHENSIVE,
    ) -> UnifiedAnalysisContext:
        """A31 YAMLからコンテキスト生成

        Args:
            a31_yaml_content: A31チェックリストYAML内容
            manuscript_content: 原稿内容
            project_context: プロジェクトコンテキスト
            preservation_scope: 保持範囲

        Returns:
            UnifiedAnalysisContext: 統合分析コンテキスト
        """
        # A31項目のパース
        checklist_items = {}
        checklist_raw = a31_yaml_content.get("checklist_items", {})

        for phase_name, items in checklist_raw.items():
            if phase_name in {"metadata", "validation_summary"}:
                continue

            parsed_items = []
            for item_data in items:
                if isinstance(item_data, dict) and "id" in item_data:
                    parsed_items.append(
                        A31ChecklistItem(
                            id=item_data.get("id", ""),
                            item=item_data.get("item", ""),
                            phase=phase_name,
                            required=item_data.get("required", False),
                            item_type=item_data.get("type", "unknown"),
                            reference_guides=item_data.get("reference_guides", []),
                            input_files=item_data.get("input_files", []),
                            output_files=item_data.get("output_files", []),
                            output_validation=item_data.get("output_validation", []),
                            status=item_data.get("status", False),
                            auto_fix_supported=item_data.get("auto_fix_supported", False),
                            auto_fix_level=item_data.get("auto_fix_level"),
                        )
                    )

            if parsed_items:
                checklist_items[phase_name] = parsed_items

        # 相互参照データの構築
        relationship_count = 0
        file_dependencies = {}
        content_relationships = {}
        phase_interactions = {}

        for phase_name, items in checklist_items.items():
            phase_interactions[phase_name] = []
            for item in items:
                if item.has_cross_references():
                    relationship_count += 1
                    file_dependencies[item.id] = item.input_files + item.output_files

                    # 他項目との関係性分析
                    for other_phase_name, other_items in checklist_items.items():
                        if other_phase_name != phase_name:
                            for other_item in other_items:
                                if any(ref in other_item.input_files for ref in item.output_files):
                                    if item.id not in content_relationships:
                                        content_relationships[item.id] = []
                                    content_relationships[item.id].append(other_item.id)
                                    phase_interactions[phase_name].append(other_phase_name)

        cross_reference_data: dict[str, Any] = CrossReferenceData(
            relationship_count=relationship_count,
            file_dependencies=file_dependencies,
            content_relationships=content_relationships,
            phase_interactions=phase_interactions,
        )

        # エピソードコンテキストの構築
        episode_context = {
            "episode_number": project_context.episode_number,
            "manuscript_length": len(manuscript_content),
            "total_items": sum(len(items) for items in checklist_items.values()),
            "required_items": sum(1 for items in checklist_items.values() for item in items if item.required),
            "auto_fixable_items": sum(
                1 for items in checklist_items.values() for item in items if item.auto_fix_supported
            ),
        }

        return cls(
            manuscript_content=manuscript_content,
            a31_checklist=checklist_items,
            project_context=project_context,
            episode_context=episode_context,
            cross_reference_data=cross_reference_data,
            preservation_scope=preservation_scope,
        )

    def get_total_items_count(self) -> int:
        """総項目数の取得

        Returns:
            int: 総項目数
        """
        return sum(len(items) for items in self._iter_checklist_groups())

    def get_required_items_count(self) -> int:
        """必須項目数の取得

        Returns:
            int: 必須項目数
        """
        return sum(
            1 for items in self._iter_checklist_groups() for item in items if getattr(item, "required", False)
        )

    def get_priority_items(self, limit: int = 0) -> list[A31ChecklistItem]:
        """優先度順項目リストの取得

        Args:
            limit: 取得制限数（0は無制限）

        Returns:
            List[A31ChecklistItem]: 優先度順項目リスト
        """
        all_items: list[A31ChecklistItem] = []
        for items in self._iter_checklist_groups():
            all_items.extend(items)

        # 優先度でソート
        sorted_items = sorted(all_items, key=lambda x: x.get_priority_score(), reverse=True)

        if limit > 0:
            return sorted_items[:limit]
        return sorted_items

    def get_phase_items(self, phase_name: str) -> list[A31ChecklistItem]:
        """段階別項目の取得

        Args:
            phase_name: 段階名

        Returns:
            List[A31ChecklistItem]: 段階別項目リスト
        """
        if hasattr(self.a31_checklist, "get"):
            items = self.a31_checklist.get(phase_name, [])
            if isinstance(items, list):
                return items
            try:
                return list(items)
            except TypeError:
                return []
        return []

    def get_cross_phase_relationships(self) -> dict[str, list[str]]:
        """段階間関係の取得

        Returns:
            Dict[str, List[str]]: 段階間関係マップ
        """
        return self.cross_reference_data.phase_interactions

    def should_preserve_full_context(self) -> bool:
        """完全コンテキスト保持判定

        Returns:
            bool: 完全コンテキスト保持を行うかどうか
        """
        return self.preservation_scope.includes_context_preservation()

    def get_analysis_item_limit(self) -> int:
        """分析項目制限の取得

        Returns:
            int: 分析項目数制限（0は無制限）
        """
        return self.preservation_scope.get_item_limit()

    def generate_context_summary(self) -> dict[str, Any]:
        """コンテキストサマリーの生成

        Returns:
            Dict[str, Any]: コンテキストサマリー
        """
        return {
            "project_name": self.project_context.project_name,
            "episode_number": self.project_context.episode_number,
            "manuscript_length": len(self.manuscript_content),
            "total_items": self.get_total_items_count(),
            "required_items": self.get_required_items_count(),
            "phase_count": len(self._iter_checklist_groups()),
            "relationship_count": self.cross_reference_data.relationship_count,
            "relationship_density": self.cross_reference_data.get_relationship_density(),
            "preservation_scope": self.preservation_scope.value,
            "full_context_preservation": self.should_preserve_full_context(),
            "context_fingerprint": self.project_context.get_context_fingerprint(),
            "content_hash": self.content_hash,
        }

    def validate_context_integrity(self) -> dict[str, Any]:
        """コンテキスト整合性の検証

        Returns:
            Dict[str, Any]: 検証結果
        """
        issues = []
        warnings = []

        # 基本検証
        if not self.manuscript_content:
            issues.append("原稿内容が空です")

        if not self._iter_checklist_groups():
            issues.append("A31チェックリストが空です")

        if self.get_total_items_count() != 68:
            warnings.append(f"項目数が期待値（68）と異なります: {self.get_total_items_count()}")

        # コンテキスト保持検証
        if self.should_preserve_full_context() and len(self.manuscript_content) < 1000:
            warnings.append("完全コンテキスト保持モードですが原稿が短すぎます")

        # 関係性検証
        if self.cross_reference_data.relationship_count == 0:
            warnings.append("項目間の関係性が検出されていません")

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "validation_summary": {
                "manuscript_ok": bool(self.manuscript_content),
                "checklist_ok": bool(self._iter_checklist_groups()),
                "relationships_ok": self.cross_reference_data.relationship_count > 0,
                "context_preservation_ok": self.should_preserve_full_context() or len(self.manuscript_content) > 0,
            },
        }

    def _calculate_content_hash(self) -> str:
        """コンテンツハッシュの計算

        Returns:
            str: コンテンツハッシュ
        """
        content_data: dict[str, Any] = (
            f"{self.manuscript_content}_{self.get_total_items_count()}_{self.preservation_scope.value}"
        )
        return hashlib.sha256(content_data.encode()).hexdigest()[:16]

    def __str__(self) -> str:
        """文字列表現"""
        return f"UnifiedAnalysisContext(episode={self.project_context.episode_number}, items={self.get_total_items_count()}, scope={self.preservation_scope.value})"

    def __repr__(self) -> str:
        """開発者向け表現"""
        return f"UnifiedAnalysisContext(project='{self.project_context.project_name}', episode={self.project_context.episode_number}, total_items={self.get_total_items_count()}, preservation_scope={self.preservation_scope})"
