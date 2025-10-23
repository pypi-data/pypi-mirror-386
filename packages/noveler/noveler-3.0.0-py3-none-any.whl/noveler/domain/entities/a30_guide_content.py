#!/usr/bin/env python3

"""Domain.entities.a30_guide_content
Where: Domain entity representing A30 guide content.
What: Stores guide information and progress for A30 workflows.
Why: Provides structured state for A30 guide-related operations.
"""

from __future__ import annotations

"""A30ガイドコンテンツエンティティ

SPEC-A30-STEPWISE-001に基づく統合A30ガイドコンテンツの実装
"""


import json
from dataclasses import dataclass
from typing import Any

from noveler.domain.value_objects.writing_phase import WritingPhase


@dataclass
class A30GuideContent:
    """A30ガイドコンテンツエンティティ

    段階的読み込みで取得したA30ガイドの各種コンテンツを統合管理
    """

    master_guide: dict[str, Any]
    detailed_rules: dict[str, Any] | None = None
    quality_checklist: dict[str, Any] | None = None
    troubleshooting_guide: dict[str, Any] | None = None
    phase: WritingPhase = WritingPhase.DRAFT

    def is_complete_for_phase(self) -> bool:
        """指定フェーズに対してコンテンツが完全かどうかを判定

        Returns:
            bool: コンテンツが完全な場合True
        """
        if not self.master_guide:
            return False

        match self.phase:
            case WritingPhase.DRAFT:
                return True  # マスターガイドのみで十分

            case WritingPhase.REFINEMENT:
                return self.detailed_rules is not None and self.quality_checklist is not None

            case WritingPhase.TROUBLESHOOTING:
                return self.troubleshooting_guide is not None

            case _:
                return False

    def get_content_size_estimation(self) -> int:
        """コンテンツサイズの推定値を取得

        Returns:
            int: 推定バイトサイズ
        """
        total_size = 0

        if self.master_guide:
            total_size += len(json.dumps(self.master_guide, ensure_ascii=False))

        if self.detailed_rules:
            total_size += len(json.dumps(self.detailed_rules, ensure_ascii=False))

        if self.quality_checklist:
            total_size += len(json.dumps(self.quality_checklist, ensure_ascii=False))

        if self.troubleshooting_guide:
            total_size += len(json.dumps(self.troubleshooting_guide, ensure_ascii=False))

        return total_size

    def merge_with(self, other: A30GuideContent) -> A30GuideContent:
        """他のA30ガイドコンテンツとマージ

        Args:
            other: マージ対象のA30ガイドコンテンツ

        Returns:
            A30GuideContent: マージされた新しいコンテンツ
        """
        # マスターガイドのマージ
        merged_master = {**self.master_guide}
        if other.master_guide:
            merged_master.update(other.master_guide)

        # その他のコンテンツは、より詳細な方を優先
        merged_detailed_rules = other.detailed_rules or self.detailed_rules
        merged_quality_checklist = other.quality_checklist or self.quality_checklist
        merged_troubleshooting_guide = other.troubleshooting_guide or self.troubleshooting_guide

        # より高度なフェーズを選択
        merged_phase = (
            other.phase if self._phase_priority(other.phase) > self._phase_priority(self.phase) else self.phase
        )

        return A30GuideContent(
            master_guide=merged_master,
            detailed_rules=merged_detailed_rules,
            quality_checklist=merged_quality_checklist,
            troubleshooting_guide=merged_troubleshooting_guide,
            phase=merged_phase,
        )

    def _phase_priority(self, phase: WritingPhase) -> int:
        """フェーズの優先度を取得（数値が大きいほど高優先度）

        Args:
            phase: 対象フェーズ

        Returns:
            int: 優先度
        """
        priority_map = {WritingPhase.DRAFT: 1, WritingPhase.REFINEMENT: 2, WritingPhase.TROUBLESHOOTING: 3}
        return priority_map.get(phase, 0)

    def get_available_content_types(self) -> list[str]:
        """利用可能なコンテンツタイプの一覧を取得

        Returns:
            list[str]: 利用可能なコンテンツタイプ
        """
        available_types = []

        if self.master_guide:
            available_types.append("master_guide")

        if self.detailed_rules:
            available_types.append("detailed_rules")

        if self.quality_checklist:
            available_types.append("quality_checklist")

        if self.troubleshooting_guide:
            available_types.append("troubleshooting_guide")

        return available_types
