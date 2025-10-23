#!/usr/bin/env python3
"""A30ガイドコンテンツエンティティのテスト

SPEC-A30-STEPWISE-001に基づく統合ガイドコンテンツエンティティのテスト実装
"""

import pytest

from noveler.domain.entities.a30_guide_content import A30GuideContent
from noveler.domain.value_objects.writing_phase import WritingPhase


@pytest.mark.spec("SPEC-A30-STEPWISE-001")
class TestA30GuideContent:
    """A30ガイドコンテンツエンティティテスト"""

    @pytest.mark.spec("SPEC-A30_GUIDE_CONTENT-CREATE_DRAFT_PHASE_C")
    def test_create_draft_phase_content_with_master_only(self):
        """初稿フェーズのコンテンツ作成確認"""
        # Arrange
        master_guide = {"rules": ["rule1", "rule2"]}

        # Act
        content = A30GuideContent(
            master_guide=master_guide,
            phase=WritingPhase.DRAFT
        )

        # Assert
        assert content.master_guide == master_guide
        assert content.detailed_rules is None
        assert content.quality_checklist is None
        assert content.troubleshooting_guide is None
        assert content.phase == WritingPhase.DRAFT

    @pytest.mark.spec("SPEC-A30_GUIDE_CONTENT-CREATE_REFINEMENT_PH")
    def test_create_refinement_phase_content_with_all_details(self):
        """仕上げフェーズのコンテンツ作成確認"""
        # Arrange
        master_guide = {"rules": ["rule1", "rule2"]}
        detailed_rules = {"forbidden_expressions": ["思った", "感じた"]}
        quality_checklist = {"common": [{"id": "pov", "name": "視点統一"}]}

        # Act
        content = A30GuideContent(
            master_guide=master_guide,
            detailed_rules=detailed_rules,
            quality_checklist=quality_checklist,
            phase=WritingPhase.REFINEMENT
        )

        # Assert
        assert content.master_guide == master_guide
        assert content.detailed_rules == detailed_rules
        assert content.quality_checklist == quality_checklist
        assert content.troubleshooting_guide is None
        assert content.phase == WritingPhase.REFINEMENT

    @pytest.mark.spec("SPEC-A30_GUIDE_CONTENT-IS_COMPLETE_FOR_PHAS")
    def test_is_complete_for_phase_draft_returns_true_with_master(self):
        """初稿フェーズの完全性チェック"""
        # Arrange
        content = A30GuideContent(
            master_guide={"rules": []},
            phase=WritingPhase.DRAFT
        )

        # Act
        is_complete = content.is_complete_for_phase()

        # Assert
        assert is_complete is True

    @pytest.mark.spec("SPEC-A30_GUIDE_CONTENT-IS_COMPLETE_FOR_PHAS")
    def test_is_complete_for_phase_refinement_returns_false_without_details(self):
        """仕上げフェーズの完全性チェック（詳細情報不足）"""
        # Arrange
        content = A30GuideContent(
            master_guide={"rules": []},
            phase=WritingPhase.REFINEMENT
        )

        # Act
        is_complete = content.is_complete_for_phase()

        # Assert
        assert is_complete is False

    @pytest.mark.spec("SPEC-A30_GUIDE_CONTENT-IS_COMPLETE_FOR_PHAS")
    def test_is_complete_for_phase_refinement_returns_true_with_all_details(self):
        """仕上げフェーズの完全性チェック（完全）"""
        # Arrange
        content = A30GuideContent(
            master_guide={"rules": []},
            detailed_rules={"rules": []},
            quality_checklist={"items": []},
            phase=WritingPhase.REFINEMENT
        )

        # Act
        is_complete = content.is_complete_for_phase()

        # Assert
        assert is_complete is True

    @pytest.mark.spec("SPEC-A30_GUIDE_CONTENT-GET_CONTENT_SIZE_RET")
    def test_get_content_size_returns_correct_estimation(self):
        """コンテンツサイズ推定確認"""
        # Arrange
        content = A30GuideContent(
            master_guide={"data": "a" * 1000},
            detailed_rules={"data": "b" * 2000},
            phase=WritingPhase.REFINEMENT
        )

        # Act
        size = content.get_content_size_estimation()

        # Assert
        assert size > 3000  # 概算でマスター1000 + 詳細2000以上

    @pytest.mark.spec("SPEC-A30_GUIDE_CONTENT-MERGE_WITH_OTHER_CON")
    def test_merge_with_other_content_combines_guides(self):
        """複数コンテンツのマージ機能"""
        # Arrange
        base_content = A30GuideContent(
            master_guide={"base": "data"},
            phase=WritingPhase.DRAFT
        )
        additional_content = A30GuideContent(
            master_guide={"additional": "data"},
            detailed_rules={"rules": []},
            phase=WritingPhase.REFINEMENT
        )

        # Act
        merged_content = base_content.merge_with(additional_content)

        # Assert
        assert merged_content.phase == WritingPhase.REFINEMENT
        assert merged_content.detailed_rules is not None
        assert "base" in str(merged_content.master_guide)
        assert "additional" in str(merged_content.master_guide)
