#!/usr/bin/env python3
"""品質チェックリスト項目エンティティ（旧称A31ChecklistItem）

SPEC-QUALITY-001に基づくチェックリスト項目の表現。
自動修正機能と閾値判定を含む豊富なビジネスロジックを提供。
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from noveler.domain.value_objects.a31_auto_fix_strategy import AutoFixStrategy
from noveler.domain.value_objects.a31_evaluation_category import (
    QualityEvaluationCategory as A31EvaluationCategory,  # compat import name
)
from noveler.domain.value_objects.a31_threshold import Threshold


class ChecklistItemType(Enum):
    """チェックリスト項目タイプ"""

    FORMAT_CHECK = "format_check"
    QUALITY_THRESHOLD = "quality_threshold"
    CONTENT_REVIEW = "content_review"
    CONTENT_BALANCE = "content_balance"
    CONSISTENCY_CHECK = "consistency_check"
    CLAUDE_CODE_EVALUATION = "claude_code_evaluation"
    SENSORY_CHECK = "sensory_check"
    TRANSITION_QUALITY = "transition_quality"
    STYLE_VARIETY = "style_variety"
    BASIC_PROOFREAD = "basic_proofread"
    READABILITY_CHECK = "readability_check"
    CHARACTER_CONSISTENCY = "character_consistency"
    STYLE_CONSISTENCY = "style_consistency"
    COMMAND_EXECUTION = "command_execution"
    SYSTEM_FUNCTION = "system_function"
    TERMINOLOGY_CHECK = "terminology_check"
    DOCUMENT_REVIEW = "document_review"
    FILE_UPDATE = "file_update"
    CONTENT_PLANNING = "content_planning"
    RISK_ASSESSMENT = "risk_assessment"
    SCENE_DESIGN = "scene_design"
    CONTENT_QUALITY = "content_quality"
    AUTO_SYSTEM_FUNCTION = "auto_system_function"
    FILE_REVIEW = "file_review"
    FILE_UPDATE_CHECK = "file_update_check"
    AUTO_RECORD_CHECK = "auto_record_check"
    CROSS_REFERENCE_UPDATE = "cross_reference_update"
    PLOT_SYNC_CHECK = "plot_sync_check"
    CONTENT_ADDITION = "content_addition"
    MANUAL_ENTRY = "manual_entry"


@dataclass
class QualityChecklistItem:
    """A31チェックリスト項目エンティティ

    チェックリスト項目の自動修正機能と閾値判定を管理。
    各項目の修正可能性と優先度を提供する。
    """

    item_id: str
    title: str
    required: bool
    item_type: ChecklistItemType
    threshold: Threshold | None = None
    auto_fix_strategy: AutoFixStrategy | None = None

    def __post_init__(self) -> None:
        """初期化後の検証"""
        self._validate_item_id()

    def _validate_item_id(self) -> None:
        """item_idの形式検証"""
        if not re.match(r"^A31-\d{3}$", self.item_id):
            msg = f"item_id '{self.item_id}' はA31-XXX形式である必要があります"
            raise ValueError(msg)

    def is_auto_fixable(self) -> bool:
        """自動修正可能かの判定

        Returns:
            bool: 自動修正対応の場合True
        """
        return self.auto_fix_strategy is not None and self.auto_fix_strategy.supported

    def get_fix_priority(self) -> int:
        """修正優先度の取得

        Returns:
            int: 優先度(1が最高優先度)
        """
        if self.auto_fix_strategy:
            priority = getattr(self.auto_fix_strategy, "priority", None)
            if isinstance(priority, (int, float)):
                return max(1, int(priority))
        return 5  # デフォルト優先度

    @property
    def category(self) -> A31EvaluationCategory:
        """詳細評価システム互換用カテゴリプロパティ

        Returns:
            A31EvaluationCategory: 対応する評価カテゴリ
        """
        return A31EvaluationCategory.from_checklist_item_type(self.item_type.value)

    def to_dict(self) -> dict[str, Any]:
        """辞書形式への変換

        Returns:
            Dict[str, Any]: 項目データの辞書表現
        """
        result = {
            "item_id": self.item_id,
            "title": self.title,
            "required": self.required,
            "item_type": self.item_type.value,
        }

        if self.threshold:
            result["threshold"] = self.threshold.to_dict()

        if self.auto_fix_strategy:
            result["auto_fix_supported"] = self.auto_fix_strategy.supported
            result["auto_fix_level"] = self.auto_fix_strategy.fix_level
            result["auto_fix_priority"] = self.auto_fix_strategy.priority
        else:
            result["auto_fix_supported"] = False
            result["auto_fix_level"] = "none"
            result["auto_fix_priority"] = 5

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QualityChecklistItem":
        """辞書からの復元

        Args:
            data: 項目データの辞書

        Returns:
            QualityChecklistItem: 復元された項目インスタンス
        """
        threshold = None
        if data.get("threshold"):
            threshold = Threshold.from_dict(data["threshold"])

        auto_fix_strategy = None
        if data.get("auto_fix_strategy"):
            auto_fix_strategy = AutoFixStrategy.from_dict(data["auto_fix_strategy"])

        return cls(
            item_id=data["item_id"],
            title=data["title"],
            required=data["required"],
            item_type=ChecklistItemType(data["item_type"]),
            threshold=threshold,
            auto_fix_strategy=auto_fix_strategy,
        )

# Backward compatibility alias
A31ChecklistItem = QualityChecklistItem
