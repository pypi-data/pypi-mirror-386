#!/usr/bin/env python3
"""A31重点項目エンティティ テスト

A31PriorityItem エンティティの振る舞いをテストし、
ビジネスルールとドメイン制約の妥当性を検証する。
"""

import pytest

from noveler.domain.entities.a31_priority_item import (
    A31CheckPhase,
    A31PriorityItem,
    ClaudeAnalysisSuitability,
    PriorityItemId,
)
from noveler.domain.value_objects.a31_evaluation_category import A31EvaluationCategory


@pytest.mark.spec("SPEC-A31-EXT-001")
class TestA31PriorityItem:
    """A31重点項目エンティティのテスト"""

    @pytest.mark.spec("SPEC-A31_PRIORITY_ITEM-CREATE_PRIORITY_ITEM")
    def test_create_priority_item_with_valid_data(self) -> None:
        """有効なデータでA31重点項目を作成できる"""
        # Arrange
        item_id = "A31-021"
        content = "冒頭3行で読者を引き込む工夫"
        phase = A31CheckPhase.PHASE2_WRITING
        category = A31EvaluationCategory.BASIC_WRITING_STYLE
        priority_score = 0.85

        # Act
        priority_item = A31PriorityItem.create(
            item_id=item_id, content=content, phase=phase, category=category, priority_score=priority_score
        )

        # Assert
        assert priority_item.item_id.value == item_id
        assert priority_item.content == content
        assert priority_item.phase == phase
        assert priority_item.category == category
        assert priority_item.priority_score == priority_score
        assert priority_item.is_high_priority() is True  # >= 0.7

    @pytest.mark.spec("SPEC-A31_PRIORITY_ITEM-PRIORITY_SCORE_VALID")
    def test_priority_score_validation(self) -> None:
        """priority_score の範囲検証"""
        with pytest.raises(ValueError, match="priority_score は 0.0 から 1.0 の範囲"):
            A31PriorityItem.create(
                item_id="A31-021",
                content="テスト項目",
                phase=A31CheckPhase.PHASE2_WRITING,
                category=A31EvaluationCategory.BASIC_WRITING_STYLE,
                priority_score=1.5,  # 範囲外
            )

        with pytest.raises(ValueError, match="priority_score は 0.0 から 1.0 の範囲"):
            A31PriorityItem.create(
                item_id="A31-021",
                content="テスト項目",
                phase=A31CheckPhase.PHASE2_WRITING,
                category=A31EvaluationCategory.BASIC_WRITING_STYLE,
                priority_score=-0.1,  # 範囲外
            )

    @pytest.mark.spec("SPEC-A31_PRIORITY_ITEM-CLAUDE_ANALYSIS_SUIT")
    def test_claude_analysis_suitability_detection(self) -> None:
        """Claude分析適性の自動判定"""
        # 適性の高い項目タイプ
        suitable_item = A31PriorityItem.create(
            item_id="A31-022",
            content="会話と地の文のバランスを確認",
            phase=A31CheckPhase.PHASE2_WRITING,
            category=A31EvaluationCategory.CONTENT_BALANCE,
            priority_score=0.8,
        )

        assert suitable_item.claude_analysis_suitability == ClaudeAnalysisSuitability.HIGH
        assert suitable_item.is_claude_suitable() is True

    @pytest.mark.spec("SPEC-A31_PRIORITY_ITEM-PRIORITY_ITEM_BUSINE")
    def test_priority_item_business_rules(self) -> None:
        """ビジネスルールの検証"""
        # Phase2項目は優先度ボーナスを受ける
        phase2_item = A31PriorityItem.create(
            item_id="A31-021",
            content="冒頭3行で読者を引き込む工夫",
            phase=A31CheckPhase.PHASE2_WRITING,
            category=A31EvaluationCategory.BASIC_WRITING_STYLE,
            priority_score=0.6,
        )

        # Phase2ボーナス適用で高優先度になる
        adjusted_score = phase2_item.calculate_adjusted_priority_score()
        assert adjusted_score >= 0.7  # ボーナス適用で閾値越え
        assert phase2_item.is_high_priority_with_bonus() is True

    @pytest.mark.spec("SPEC-A31_PRIORITY_ITEM-GENERATE_CLAUDE_PROM")
    def test_generate_claude_prompt_template(self) -> None:
        """Claude分析用プロンプトテンプレート生成"""
        priority_item = A31PriorityItem.create(
            item_id="A31-023",
            content="五感描写を適切に配置",
            phase=A31CheckPhase.PHASE2_WRITING,
            category=A31EvaluationCategory.SENSORY_DESCRIPTION,
            priority_score=0.8,
        )

        prompt_template = priority_item.generate_claude_prompt_template()

        assert "五感描写" in prompt_template
        assert "分析してください" in prompt_template
        assert len(prompt_template) > 100  # 十分な詳細度

    @pytest.mark.spec("SPEC-A31_PRIORITY_ITEM-PRIORITY_ITEM_EQUALI")
    def test_priority_item_equality(self) -> None:
        """A31重点項目の同値性判定"""
        item1 = A31PriorityItem.create(
            item_id="A31-021",
            content="冒頭3行で読者を引き込む工夫",
            phase=A31CheckPhase.PHASE2_WRITING,
            category=A31EvaluationCategory.BASIC_WRITING_STYLE,
            priority_score=0.85,
        )

        item2 = A31PriorityItem.create(
            item_id="A31-021",  # 同じID
            content="異なる内容",  # 内容が異なっても
            phase=A31CheckPhase.PHASE3_REVISION,
            category=A31EvaluationCategory.CHARACTER_CONSISTENCY,
            priority_score=0.6,
        )

        # IDが同じなら同一エンティティ
        assert item1 == item2
        assert hash(item1) == hash(item2)

    @pytest.mark.parametrize(("score", "expected"), [(0.0, False), (0.6, False), (0.7, True), (0.85, True), (1.0, True)])
    def test_high_priority_threshold(self, score: float, expected: bool) -> None:
        """高優先度閾値(0.7)の境界値テスト"""
        # B30品質作業指示書遵守: 有効なID形式に修正
        item = A31PriorityItem.create(
            item_id="A31-001",
            content="テスト項目",
            phase=A31CheckPhase.PHASE2_WRITING,
            category=A31EvaluationCategory.BASIC_WRITING_STYLE,
            priority_score=score,
        )

        assert item.is_high_priority() == expected


@pytest.mark.spec("SPEC-A31-EXT-001")
class TestPriorityItemId:
    """優先度項目ID バリューオブジェクトのテスト"""

    @pytest.mark.spec("SPEC-A31_PRIORITY_ITEM-VALID_PRIORITY_ITEM_")
    def test_valid_priority_item_id_creation(self) -> None:
        """有効な優先度項目IDの作成"""
        valid_ids = ["A31-021", "A31-055", "A41-023"]

        for item_id in valid_ids:
            priority_id = PriorityItemId(item_id)
            assert priority_id.value == item_id

    @pytest.mark.spec("SPEC-A31_PRIORITY_ITEM-INVALID_PRIORITY_ITE")
    def test_invalid_priority_item_id_validation(self) -> None:
        """無効な優先度項目IDの検証"""
        invalid_ids = ["", "   ", "INVALID", "31-021"]

        for invalid_id in invalid_ids:
            with pytest.raises(ValueError):
                PriorityItemId(invalid_id)


@pytest.mark.spec("SPEC-A31-EXT-001")
class TestA31CheckPhase:
    """A31チェックフェーズ 列挙型のテスト"""

    @pytest.mark.spec("SPEC-A31_PRIORITY_ITEM-PHASE_PRIORITY_WEIGH")
    def test_phase_priority_weights(self) -> None:
        """フェーズ別優先度重みの検証"""
        assert A31CheckPhase.PHASE2_WRITING.get_priority_weight() == 0.9
        assert A31CheckPhase.PHASE3_REVISION.get_priority_weight() == 0.8
        assert A31CheckPhase.PHASE1_PLANNING.get_priority_weight() < 0.7

    @pytest.mark.spec("SPEC-A31_PRIORITY_ITEM-PHASE_DISPLAY_NAMES")
    def test_phase_display_names(self) -> None:
        """フェーズ表示名の確認"""
        assert "執筆段階" in A31CheckPhase.PHASE2_WRITING.get_display_name()
        assert "推敲段階" in A31CheckPhase.PHASE3_REVISION.get_display_name()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
