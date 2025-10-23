"""A28 Workflow Integration Tests

Test A28 turning point template loading and usage.
Based on: docs/drafts/a28_case_study_draft.md
"""

import pytest
from pathlib import Path

from noveler.domain.services.a28_template_loader_service import (
    A28TemplateLoaderService,
    A28TemplateData,
    A28TurningPointData,
)


class TestA28TemplateLoader:
    """A28テンプレート読み込みテスト"""

    def test_load_default_turning_point_template(self):
        """デフォルトの転機型テンプレートが正しく読み込めることを確認"""
        # Arrange
        loader = A28TemplateLoaderService()

        # Act
        template_data = loader.load_default_turning_point_template()

        # Assert
        assert isinstance(template_data, A28TemplateData)
        assert template_data.metadata["pattern_type"] == "転機型導入"
        assert template_data.metadata["template_version"] == "1.0"

    def test_turning_point_structure_loaded(self):
        """転機構造が正しく読み込まれることを確認"""
        # Arrange
        loader = A28TemplateLoaderService()

        # Act
        template_data = loader.load_default_turning_point_template()
        tp = template_data.turning_point

        # Assert
        assert isinstance(tp, A28TurningPointData)
        assert tp.title == "運命の出会い - 能力の授与"
        assert tp.timing == "第一幕終盤"
        assert "Brain Burst" in tp.trigger_event
        assert len(tp.before_state) > 0
        assert len(tp.transformation_moment) > 0
        assert len(tp.after_state) > 0

    def test_emotional_journey_structure(self):
        """感情の旅程が3段階で構成されていることを確認"""
        # Arrange
        loader = A28TemplateLoaderService()

        # Act
        template_data = loader.load_default_turning_point_template()
        journey = template_data.turning_point.emotional_journey

        # Assert
        assert len(journey) == 3
        assert journey[0]["stage"] == "恐怖/不安"
        assert journey[0]["emotion_level"] == 2
        assert journey[1]["stage"] == "決意/理解"
        assert journey[1]["emotion_level"] == 6
        assert journey[2]["stage"] == "希望/成長"
        assert journey[2]["emotion_level"] == 8

    def test_scene_structure_loaded(self):
        """シーン構造が正しく読み込まれることを確認"""
        # Arrange
        loader = A28TemplateLoaderService()

        # Act
        template_data = loader.load_default_turning_point_template()
        scenes = template_data.scenes

        # Assert
        assert len(scenes) >= 3  # 最低3シーンは必要

        # scene_001: 弱点提示
        scene_001 = next(s for s in scenes if s.scene_id == "scene_001")
        assert scene_001.scene_purpose == "主人公の弱点提示と共感獲得"
        assert scene_001.importance_rank == "A"
        assert scene_001.estimated_words == 800

        # scene_002: 転機
        scene_002 = next(s for s in scenes if s.scene_id == "scene_002")
        assert scene_002.scene_purpose == "転機 - 能力授与と世界の転換"
        assert scene_002.importance_rank == "S"
        assert scene_002.estimated_words == 1200

    def test_five_elements_checklist_loaded(self):
        """5要素チェックリストが正しく読み込まれることを確認"""
        # Arrange
        loader = A28TemplateLoaderService()

        # Act
        template_data = loader.load_default_turning_point_template()
        checklist = template_data.five_elements_checklist

        # Assert
        assert "weakness_presentation" in checklist
        assert "turning_point_structure" in checklist
        assert "dual_motivation" in checklist
        assert "show_dont_tell" in checklist
        assert "emotion_curve" in checklist

        # 弱点提示の検証基準
        weakness = checklist["weakness_presentation"]
        assert weakness["target_scene"] == "scene_001"
        assert len(weakness["validation_criteria"]) >= 3

    def test_eighteen_step_mapping_loaded(self):
        """18-Step Workflow マッピングが正しく読み込まれることを確認"""
        # Arrange
        loader = A28TemplateLoaderService()

        # Act
        template_data = loader.load_default_turning_point_template()
        mapping = template_data.eighteen_step_mapping

        # Assert
        assert mapping is not None
        assert "step_3_character" in mapping
        assert "step_6_turning_point" in mapping
        assert "step_7_dialogue" in mapping
        assert "step_8_emotion_curve" in mapping
        assert "step_10_sensory_design" in mapping

        # Step 6 転機設計の検証
        step_6 = mapping["step_6_turning_point"]
        assert "before_state" in step_6["structure"]
        assert "transition" in step_6["structure"]
        assert "after_state" in step_6["structure"]

    def test_post_apply_review_loaded(self):
        """Post-Apply Review チェックリストが正しく読み込まれることを確認"""
        # Arrange
        loader = A28TemplateLoaderService()

        # Act
        template_data = loader.load_default_turning_point_template()
        review = template_data.post_apply_review

        # Assert
        assert review is not None
        assert "gate_w1_five_elements" in review
        assert "troubleshooting" in review

        # 5要素チェック
        gate_w1 = review["gate_w1_five_elements"]
        assert len(gate_w1) == 5

        # 各要素に element, check, pass_criteria が存在
        for check_item in gate_w1:
            assert "element" in check_item
            assert "check" in check_item
            assert "pass_criteria" in check_item

    def test_generate_prompt_from_template(self):
        """テンプレートからプロンプトが正しく生成されることを確認"""
        # Arrange
        loader = A28TemplateLoaderService()
        template_data = loader.load_default_turning_point_template()

        # Act
        prompt = loader.generate_prompt_from_template(template_data)

        # Assert
        assert isinstance(prompt, str)
        assert len(prompt) > 1000  # 十分な長さのプロンプト
        assert "A28 転機型導入パターン" in prompt
        assert "転機構造" in prompt
        assert "シーン構成" in prompt
        assert "5要素チェックリスト" in prompt
        assert template_data.turning_point.title in prompt

    def test_emotion_tech_fusion_optional(self):
        """emotion_tech_fusion がオプショナルフィールドとして扱われることを確認"""
        # Arrange
        loader = A28TemplateLoaderService()

        # Act
        template_data = loader.load_default_turning_point_template()
        fusion = template_data.emotion_tech_fusion

        # Assert
        assert fusion is not None  # デフォルトテンプレートには存在
        assert fusion["enabled"] is True  # SF作品用として有効
        assert "peak_moments" in fusion

    def test_template_validation_missing_required_fields(self):
        """必須フィールドが欠けている場合にエラーが発生することを確認"""
        # Arrange
        loader = A28TemplateLoaderService()
        invalid_template_path = Path(__file__).parent.parent / "fixtures" / "invalid_a28_template.yaml"

        # Act & Assert
        with pytest.raises((ValueError, FileNotFoundError)):
            # ファイルが存在しないか、必須フィールドが欠けているはず
            loader.load_template(invalid_template_path)


class TestA28WorkflowIntegration:
    """A28ワークフロー統合テスト"""

    @pytest.mark.integration
    async def test_a28_template_integration_with_plot_generation(self):
        """A28テンプレートとプロット生成UseCaseの統合動作を確認

        Note: この tests では実際のプロット生成は行わず、
        テンプレート読み込みとプロンプト生成のみをテストする。
        完全なE2Eテストは別途 test_a28_e2e.py で実装予定。
        """
        # Arrange
        loader = A28TemplateLoaderService()

        # Act
        template_data = loader.load_default_turning_point_template()
        prompt = loader.generate_prompt_from_template(template_data)

        # Assert
        assert template_data is not None
        assert prompt is not None
        assert len(template_data.scenes) >= 3

        # プロンプトが18-Step Workflow と統合可能な構造を持つことを確認
        # 「転機構造」は必ず含まれる
        assert "転機構造" in prompt
        # 感情関連の記述も含まれる
        assert "感情" in prompt


@pytest.mark.integration
class TestA28QualityValidation:
    """A28品質検証テスト（将来実装予定）"""

    @pytest.mark.skip(reason="A28QualityValidatorService implementation pending")
    async def test_a28_five_elements_validation(self):
        """5要素チェックリストの自動検証テスト

        TODO: A28QualityValidatorService 実装後に有効化
        """
        pass

    @pytest.mark.skip(reason="A28QualityValidatorService implementation pending")
    async def test_a28_emotion_curve_validation(self):
        """感情曲線の変化幅検証テスト

        TODO: A28QualityValidatorService 実装後に有効化
        要件: emotion_level の変化幅が±2以上
        """
        pass
