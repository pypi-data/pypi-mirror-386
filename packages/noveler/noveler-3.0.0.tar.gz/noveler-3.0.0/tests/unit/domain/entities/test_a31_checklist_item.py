#!/usr/bin/env python3
"""A31ChecklistItemエンティティのユニットテスト

SPEC-QUALITY-001に基づくA31チェックリスト項目エンティティのテスト
"""

import pytest

from noveler.domain.entities.a31_checklist_item import A31ChecklistItem, ChecklistItemType
from noveler.domain.value_objects.a31_auto_fix_strategy import AutoFixStrategy
from noveler.domain.value_objects.a31_threshold import Threshold, ThresholdType


@pytest.mark.spec("SPEC-QUALITY-001")
class TestA31ChecklistItem:
    """A31ChecklistItemエンティティのテスト"""

    @pytest.mark.spec("SPEC-A31_CHECKLIST_ITEM-CREATE_FORMAT_CHECK_")
    def test_create_format_check_item(self) -> None:
        """フォーマット系チェック項目の作成テスト"""
        # RED段階: まだ実装されていない
        threshold = Threshold(threshold_type=ThresholdType.PERCENTAGE, value=100.0)

        auto_fix_strategy = AutoFixStrategy(supported=True, fix_level="safe", priority=1)

        item = A31ChecklistItem(
            item_id="A31-045",
            title="段落頭の字下げを確認",
            required=True,
            item_type=ChecklistItemType.FORMAT_CHECK,
            threshold=threshold,
            auto_fix_strategy=auto_fix_strategy,
        )

        assert item.item_id == "A31-045"
        assert item.title == "段落頭の字下げを確認"
        assert item.required is True
        assert item.item_type == ChecklistItemType.FORMAT_CHECK
        assert item.threshold.value == 100.0
        assert item.auto_fix_strategy.supported is True

    @pytest.mark.spec("SPEC-A31_CHECKLIST_ITEM-CREATE_QUALITY_THRES")
    def test_create_quality_threshold_item(self) -> None:
        """品質閾値系チェック項目の作成テスト"""
        threshold = Threshold(threshold_type=ThresholdType.SCORE, value=70.0)

        auto_fix_strategy = AutoFixStrategy(supported=True, fix_level="standard", priority=2)

        item = A31ChecklistItem(
            item_id="A31-042",
            title="品質スコア70点以上を達成",
            required=True,
            item_type=ChecklistItemType.QUALITY_THRESHOLD,
            threshold=threshold,
            auto_fix_strategy=auto_fix_strategy,
        )

        assert item.item_id == "A31-042"
        assert item.threshold.threshold_type == ThresholdType.SCORE
        assert item.auto_fix_strategy.fix_level == "standard"

    @pytest.mark.spec("SPEC-A31_CHECKLIST_ITEM-CREATE_MANUAL_CHECK_")
    def test_create_manual_check_item(self) -> None:
        """手動チェック項目の作成テスト"""
        threshold = Threshold(
            threshold_type=ThresholdType.BOOLEAN,
            value=1.0,  # True相当
        )

        auto_fix_strategy = AutoFixStrategy(supported=False, fix_level="none", priority=0)

        item = A31ChecklistItem(
            item_id="A31-012",
            title="前話からの流れを確認",
            required=True,
            item_type=ChecklistItemType.CONTENT_REVIEW,
            threshold=threshold,
            auto_fix_strategy=auto_fix_strategy,
        )

        assert item.auto_fix_strategy.supported is False
        assert item.item_type == ChecklistItemType.CONTENT_REVIEW

    @pytest.mark.spec("SPEC-A31_CHECKLIST_ITEM-IS_AUTO_FIXABLE")
    def test_is_auto_fixable(self) -> None:
        """自動修正可能かの判定テスト"""
        # 自動修正対応項目
        safe_item = A31ChecklistItem(
            item_id="A31-045",
            title="段落頭の字下げを確認",
            required=True,
            item_type=ChecklistItemType.FORMAT_CHECK,
            threshold=Threshold(ThresholdType.PERCENTAGE, 100.0),
            auto_fix_strategy=AutoFixStrategy(True, "safe", 1),
        )

        # 手動チェック項目
        manual_item = A31ChecklistItem(
            item_id="A31-012",
            title="前話からの流れを確認",
            required=True,
            item_type=ChecklistItemType.CONTENT_REVIEW,
            threshold=Threshold(ThresholdType.BOOLEAN, 1.0),
            auto_fix_strategy=AutoFixStrategy(False, "none", 0),
        )

        assert safe_item.is_auto_fixable() is True
        assert manual_item.is_auto_fixable() is False

    @pytest.mark.spec("SPEC-A31_CHECKLIST_ITEM-GET_FIX_PRIORITY")
    def test_get_fix_priority(self) -> None:
        """修正優先度取得テスト"""
        high_priority_item = A31ChecklistItem(
            item_id="A31-045",
            title="段落頭の字下げを確認",
            required=True,
            item_type=ChecklistItemType.FORMAT_CHECK,
            threshold=Threshold(ThresholdType.PERCENTAGE, 100.0),
            auto_fix_strategy=AutoFixStrategy(True, "safe", 1),
        )

        low_priority_item = A31ChecklistItem(
            item_id="A31-022",
            title="会話と地の文バランス確認",
            required=True,
            item_type=ChecklistItemType.CONTENT_BALANCE,
            threshold=Threshold.create_range(30.0, 40.0),
            auto_fix_strategy=AutoFixStrategy(True, "standard", 3),
        )

        assert high_priority_item.get_fix_priority() == 1
        assert low_priority_item.get_fix_priority() == 3

    @pytest.mark.spec("SPEC-A31_CHECKLIST_ITEM-INVALID_ITEM_ID_FORM")
    def test_invalid_item_id_format(self) -> None:
        """不正なitem_id形式のテスト"""
        with pytest.raises(ValueError, match="A31-XXX形式である必要があります"):
            A31ChecklistItem(
                item_id="INVALID-001",  # 不正な形式
                title="テスト項目",
                required=True,
                item_type=ChecklistItemType.FORMAT_CHECK,
                threshold=Threshold(ThresholdType.PERCENTAGE, 100.0),
                auto_fix_strategy=AutoFixStrategy(True, "safe", 1),
            )

    @pytest.mark.spec("SPEC-A31_CHECKLIST_ITEM-RANGE_THRESHOLD_VALI")
    def test_range_threshold_validation(self) -> None:
        """範囲閾値の検証テスト"""
        # 正常な範囲閾値
        valid_item = A31ChecklistItem(
            item_id="A31-022",
            title="会話と地の文バランス確認",
            required=True,
            item_type=ChecklistItemType.CONTENT_BALANCE,
            threshold=Threshold.create_range(30.0, 40.0),
            auto_fix_strategy=AutoFixStrategy(True, "standard", 2),
        )

        assert valid_item.threshold.min_value == 30.0
        assert valid_item.threshold.max_value == 40.0

    @pytest.mark.spec("SPEC-A31_CHECKLIST_ITEM-TO_DICT")
    def test_to_dict(self) -> None:
        """辞書形式への変換テスト"""
        item = A31ChecklistItem(
            item_id="A31-045",
            title="段落頭の字下げを確認",
            required=True,
            item_type=ChecklistItemType.FORMAT_CHECK,
            threshold=Threshold(ThresholdType.PERCENTAGE, 100.0),
            auto_fix_strategy=AutoFixStrategy(True, "safe", 1),
        )

        result = item.to_dict()

        assert result["item_id"] == "A31-045"
        assert result["title"] == "段落頭の字下げを確認"
        assert result["required"] is True
        assert result["item_type"] == "format_check"
        assert result["auto_fix_supported"] is True
        assert result["auto_fix_level"] == "safe"

    @pytest.mark.spec("SPEC-A31_CHECKLIST_ITEM-FROM_DICT")
    def test_from_dict(self) -> None:
        """辞書からの復元テスト"""
        data = {
            "item_id": "A31-045",
            "title": "段落頭の字下げを確認",
            "required": True,
            "item_type": "format_check",
            "threshold": {"type": "percentage", "value": 100.0},
            "auto_fix_strategy": {"supported": True, "fix_level": "safe", "priority": 1},
        }

        item = A31ChecklistItem.from_dict(data)

        assert item.item_id == "A31-045"
        assert item.title == "段落頭の字下げを確認"
        assert item.threshold.value == 100.0
        assert item.auto_fix_strategy.supported is True
