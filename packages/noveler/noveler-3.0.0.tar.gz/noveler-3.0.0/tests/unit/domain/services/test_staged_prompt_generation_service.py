"""
SPEC-STAGED-003: StagedPromptGenerationServiceのテスト

段階的プロンプト生成ドメインサービスの
プロンプト生成、品質検証、統合機能をテストする。
"""

from unittest.mock import Mock

import pytest

from noveler.domain.entities.staged_prompt import StagedPrompt
from noveler.domain.services.staged_prompt_generation_service import (
    PromptGenerationResult,
    StagedPromptGenerationService,
    StageQualityValidator,
    ValidationResult,
)
from noveler.domain.value_objects.prompt_stage import PromptStage


class TestPromptGenerationResult:
    """PromptGenerationResult値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-STAGED-003")
    def test_prompt_generation_result_creation(self):
        """PromptGenerationResult作成テスト"""
        result = PromptGenerationResult(
            success=True,
            generated_prompt="生成されたプロンプト",
            quality_score=85.0,
            execution_time_minutes=15,
            stage_content={"key": "value"},
            warnings=["警告1"],
            error_message=None,
        )

        assert result.success is True
        assert result.generated_prompt == "生成されたプロンプト"
        assert result.quality_score == 85.0
        assert result.execution_time_minutes == 15
        assert result.stage_content == {"key": "value"}
        assert result.warnings == ["警告1"]
        assert result.error_message is None


class TestValidationResult:
    """ValidationResult値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-STAGED-003")
    def test_validation_result_creation(self):
        """ValidationResult作成テスト"""
        result = ValidationResult(
            is_valid=True,
            quality_score=88.0,
            validation_errors=[],
            validation_warnings=["警告"],
            improvement_suggestions=["改善提案"],
        )

        assert result.is_valid is True
        assert result.quality_score == 88.0
        assert result.validation_errors == []
        assert result.validation_warnings == ["警告"]
        assert result.improvement_suggestions == ["改善提案"]


class TestStagedPromptGenerationServiceInitialization:
    """StagedPromptGenerationService初期化のテスト"""

    @pytest.mark.spec("SPEC-STAGED-003")
    def test_service_initialization(self):
        """サービス初期化テスト"""
        template_repository = Mock()
        quality_validator = Mock(spec=StageQualityValidator)

        service = StagedPromptGenerationService(
            template_repository=template_repository, quality_validator=quality_validator
        )

        assert service._template_repository == template_repository
        assert service._quality_validator == quality_validator


class TestStagedPromptGenerationServicePromptGeneration:
    """プロンプト生成機能のテスト"""

    def setup_method(self):
        """テスト準備"""
        self.template_repository = Mock()
        self.quality_validator = Mock(spec=StageQualityValidator)
        self.service = StagedPromptGenerationService(
            template_repository=self.template_repository, quality_validator=self.quality_validator
        )

        self.staged_prompt = StagedPrompt(episode_number=1, project_name="テストプロジェクト")

        # Stage 1を完了してStage 2に進行可能にする
        self.staged_prompt.complete_current_stage(
            stage_result={"stage1": "completed"}, quality_score=80.0, execution_time_minutes=15
        )

    @pytest.mark.spec("SPEC-STAGED-003")
    def test_successful_prompt_generation(self):
        """成功するプロンプト生成テスト"""
        # モックの設定
        template_content = "テストテンプレート: {episode_number} - {project_name}"
        self.template_repository.find_template_by_stage.return_value = template_content
        self.template_repository.get_template_context_keys.return_value = ["episode_number", "project_name"]

        context = {"episode_number": 1, "project_name": "テストプロジェクト"}

        result = self.service.generate_stage_prompt(
            staged_prompt=self.staged_prompt, target_stage=PromptStage.STAGE_2, context=context
        )

        assert result.success is True
        assert "テストテンプレート: 1 - テストプロジェクト" in result.generated_prompt
        assert result.quality_score > 0
        assert result.execution_time_minutes == PromptStage.STAGE_2.estimated_duration_minutes
        assert result.error_message is None

    @pytest.mark.spec("SPEC-STAGED-003")
    def test_prompt_generation_invalid_stage_transition(self):
        """無効な段階移行でのプロンプト生成テスト"""
        # Stage 1を完了していない状態でStage 3へ進行しようとする
        fresh_prompt = StagedPrompt(1, "テストプロジェクト")

        result = self.service.generate_stage_prompt(
            staged_prompt=fresh_prompt, target_stage=PromptStage.STAGE_3, context={}
        )

        assert result.success is False
        assert "Cannot advance to stage 3" in result.error_message
        assert result.generated_prompt == ""
        assert result.quality_score == 0.0

    @pytest.mark.spec("SPEC-STAGED-003")
    def test_prompt_generation_template_not_found(self):
        """テンプレート未発見でのプロンプト生成テスト"""
        self.template_repository.find_template_by_stage.return_value = None

        result = self.service.generate_stage_prompt(
            staged_prompt=self.staged_prompt, target_stage=PromptStage.STAGE_2, context={}
        )

        assert result.success is False
        assert "Template not found for stage 2" in result.error_message
        assert result.generated_prompt == ""

    @pytest.mark.spec("SPEC-STAGED-003")
    def test_prompt_generation_context_validation_failure(self):
        """コンテキスト検証失敗でのプロンプト生成テスト"""
        self.template_repository.find_template_by_stage.return_value = "テンプレート"
        self.template_repository.get_template_context_keys.return_value = ["required_key"]

        # 必須キーが不足したコンテキスト
        incomplete_context = {"other_key": "value"}

        result = self.service.generate_stage_prompt(
            staged_prompt=self.staged_prompt, target_stage=PromptStage.STAGE_2, context=incomplete_context
        )

        assert result.success is False
        assert "Context validation failed" in result.error_message
        assert "Required context key missing: required_key" in result.error_message

    @pytest.mark.spec("SPEC-STAGED-003")
    def test_prompt_generation_exception_handling(self):
        """例外処理テスト"""
        # テンプレートリポジトリで例外を発生させる
        self.template_repository.find_template_by_stage.side_effect = RuntimeError("テスト例外")

        result = self.service.generate_stage_prompt(
            staged_prompt=self.staged_prompt, target_stage=PromptStage.STAGE_2, context={}
        )

        assert result.success is False
        assert "Unexpected error in prompt generation" in result.error_message
        assert "テスト例外" in result.error_message


class TestStagedPromptGenerationServiceValidation:
    """段階完了検証機能のテスト"""

    def setup_method(self):
        """テスト準備"""
        self.template_repository = Mock()
        self.quality_validator = Mock(spec=StageQualityValidator)
        self.service = StagedPromptGenerationService(
            template_repository=self.template_repository, quality_validator=self.quality_validator
        )

        self.staged_prompt = StagedPrompt(episode_number=1, project_name="テストプロジェクト")

    @pytest.mark.spec("SPEC-STAGED-003")
    def test_successful_stage_validation(self):
        """成功する段階検証テスト"""
        # staged_promptのvalidate_stage_completion_criteriaをモック
        self.staged_prompt.validate_stage_completion_criteria = Mock(return_value=[])

        # quality_validatorのモック設定
        quality_validation_result = ValidationResult(
            is_valid=True,
            quality_score=85.0,
            validation_errors=[],
            validation_warnings=["軽微な警告"],
            improvement_suggestions=["改善提案"],
        )

        self.quality_validator.validate.return_value = quality_validation_result

        generated_content = {"test_key": "test_value"}

        result = self.service.validate_stage_completion(
            staged_prompt=self.staged_prompt, stage=PromptStage.STAGE_1, generated_content=generated_content
        )

        assert result.is_valid is True
        assert result.quality_score == 85.0
        assert result.validation_errors == []
        assert result.validation_warnings == ["軽微な警告"]
        assert result.improvement_suggestions == ["改善提案"]

    @pytest.mark.spec("SPEC-STAGED-003")
    def test_stage_validation_with_basic_errors(self):
        """基本エラーありの段階検証テスト"""
        # staged_promptから基本エラーを返す
        basic_errors = ["必須項目不足", "形式エラー"]
        self.staged_prompt.validate_stage_completion_criteria = Mock(return_value=basic_errors)

        # quality_validatorは正常
        quality_validation_result = ValidationResult(
            is_valid=True, quality_score=80.0, validation_errors=[], validation_warnings=[], improvement_suggestions=[]
        )

        self.quality_validator.validate.return_value = quality_validation_result

        generated_content = {"test_key": "test_value"}

        result = self.service.validate_stage_completion(
            staged_prompt=self.staged_prompt, stage=PromptStage.STAGE_1, generated_content=generated_content
        )

        assert result.is_valid is False
        assert len(result.validation_errors) == 2
        assert "必須項目不足" in result.validation_errors
        assert "形式エラー" in result.validation_errors

    @pytest.mark.spec("SPEC-STAGED-003")
    def test_stage_validation_with_quality_errors(self):
        """品質エラーありの段階検証テスト"""
        # staged_promptは正常
        self.staged_prompt.validate_stage_completion_criteria = Mock(return_value=[])

        # quality_validatorからエラー
        quality_validation_result = ValidationResult(
            is_valid=False,
            quality_score=60.0,
            validation_errors=["品質不足"],
            validation_warnings=["品質警告"],
            improvement_suggestions=["品質改善提案"],
        )

        self.quality_validator.validate.return_value = quality_validation_result

        generated_content = {"test_key": "test_value"}

        result = self.service.validate_stage_completion(
            staged_prompt=self.staged_prompt, stage=PromptStage.STAGE_1, generated_content=generated_content
        )

        assert result.is_valid is False
        assert result.quality_score == 60.0
        assert "品質不足" in result.validation_errors
        assert "品質警告" in result.validation_warnings
        assert "品質改善提案" in result.improvement_suggestions


class TestStagedPromptGenerationServiceRecommendations:
    """段階進行推奨機能のテスト"""

    def setup_method(self):
        """テスト準備"""
        self.template_repository = Mock()
        self.quality_validator = Mock(spec=StageQualityValidator)
        self.service = StagedPromptGenerationService(
            template_repository=self.template_repository, quality_validator=self.quality_validator
        )

        self.staged_prompt = StagedPrompt(episode_number=1, project_name="テストプロジェクト")

    @pytest.mark.spec("SPEC-STAGED-003")
    def test_stage_progression_recommendation_initial_state(self):
        """初期状態の段階進行推奨テスト"""
        recommendations = self.service.get_stage_progression_recommendation(staged_prompt=self.staged_prompt)

        assert recommendations["current_stage"]["number"] == 1
        assert recommendations["current_stage"]["name"] == "基本骨格設定"
        assert recommendations["current_stage"]["is_completed"] is False
        assert recommendations["can_advance"] is False
        assert recommendations["completion_percentage"] == 0.0
        assert recommendations["average_quality_score"] == 0.0
        assert "next_stage" not in recommendations

    @pytest.mark.spec("SPEC-STAGED-003")
    def test_stage_progression_recommendation_after_completion(self):
        """段階完了後の進行推奨テスト"""
        # Stage 1を完了
        self.staged_prompt.complete_current_stage(
            stage_result={"stage1": "completed"}, quality_score=85.0, execution_time_minutes=15
        )

        recommendations = self.service.get_stage_progression_recommendation(staged_prompt=self.staged_prompt)

        assert recommendations["current_stage"]["is_completed"] is True
        assert recommendations["can_advance"] is True
        assert recommendations["completion_percentage"] == 0.2  # 1/5
        assert recommendations["average_quality_score"] == 85.0

        assert "next_stage" in recommendations
        assert recommendations["next_stage"]["number"] == 2
        assert recommendations["next_stage"]["name"] == "構造展開"

    @pytest.mark.spec("SPEC-STAGED-003")
    def test_stage_progression_recommendation_low_quality(self):
        """低品質時の進行推奨テスト"""
        # 低品質でStage 1を完了
        self.staged_prompt.complete_current_stage(
            stage_result={"stage1": "completed"},
            quality_score=70.0,  # 80未満
            execution_time_minutes=15,
        )

        recommendations = self.service.get_stage_progression_recommendation(staged_prompt=self.staged_prompt)

        assert recommendations["quality_improvement_needed"] is True
        assert "recommendations" in recommendations
        improvement_recs = recommendations["recommendations"]
        assert any("improving content quality" in rec for rec in improvement_recs)

    @pytest.mark.spec("SPEC-STAGED-003")
    def test_stage_progression_recommendation_final_stage(self):
        """最終段階での進行推奨テスト"""
        # 全段階を完了してStage 5に到達
        for stage_num in range(1, 6):
            self.staged_prompt.complete_current_stage(
                stage_result={f"stage{stage_num}": "completed"}, quality_score=85.0, execution_time_minutes=15
            )

            if stage_num < 5:
                next_stage = (
                    PromptStage.STAGE_2
                    if stage_num == 1
                    else PromptStage.STAGE_3
                    if stage_num == 2
                    else PromptStage.STAGE_4
                    if stage_num == 3
                    else PromptStage.STAGE_5
                )
                self.staged_prompt.advance_to_stage(next_stage)

        recommendations = self.service.get_stage_progression_recommendation(staged_prompt=self.staged_prompt)

        assert recommendations["current_stage"]["number"] == 5
        assert recommendations["can_advance"] is False
        assert recommendations["completion_percentage"] == 1.0
        assert "next_stage" not in recommendations


class TestStagedPromptGenerationServiceContextValidation:
    """コンテキスト検証機能のテスト"""

    def setup_method(self):
        """テスト準備"""
        self.template_repository = Mock()
        self.quality_validator = Mock(spec=StageQualityValidator)
        self.service = StagedPromptGenerationService(
            template_repository=self.template_repository, quality_validator=self.quality_validator
        )

    @pytest.mark.spec("SPEC-STAGED-003")
    def test_context_validation_success(self):
        """コンテキスト検証成功テスト"""
        self.template_repository.get_template_context_keys.return_value = ["key1", "key2"]

        context = {"key1": "value1", "key2": "value2"}
        errors = self.service._validate_context(PromptStage.STAGE_1, context)

        assert len(errors) == 0

    @pytest.mark.spec("SPEC-STAGED-003")
    def test_context_validation_missing_keys(self):
        """必須キー不足のコンテキスト検証テスト"""
        self.template_repository.get_template_context_keys.return_value = ["key1", "key2", "key3"]

        context = {"key1": "value1"}  # key2, key3が不足
        errors = self.service._validate_context(PromptStage.STAGE_1, context)

        assert len(errors) == 2
        assert "Required context key missing: key2" in errors
        assert "Required context key missing: key3" in errors

    @pytest.mark.spec("SPEC-STAGED-003")
    def test_context_validation_empty_values(self):
        """空値のコンテキスト検証テスト"""
        self.template_repository.get_template_context_keys.return_value = ["key1", "key2"]

        context = {"key1": "value1", "key2": ""}  # key2が空
        errors = self.service._validate_context(PromptStage.STAGE_1, context)

        assert len(errors) == 1
        assert "Required context key is empty: key2" in errors

    @pytest.mark.spec("SPEC-STAGED-003")
    def test_context_validation_stage_specific_requirements(self):
        """段階固有要件のコンテキスト検証テスト"""
        self.template_repository.get_template_context_keys.return_value = []

        # Stage 3では character_settings が必要
        context = {}
        errors = self.service._validate_context(PromptStage.STAGE_3, context)

        assert len(errors) >= 1
        assert any("Character settings required for stage 3" in error for error in errors)


class TestStagedPromptGenerationServiceTemplateRendering:
    """テンプレートレンダリング機能のテスト"""

    def setup_method(self):
        """テスト準備"""
        self.template_repository = Mock()
        self.quality_validator = Mock(spec=StageQualityValidator)
        self.service = StagedPromptGenerationService(
            template_repository=self.template_repository, quality_validator=self.quality_validator
        )

    @pytest.mark.spec("SPEC-STAGED-003")
    def test_template_rendering_success(self):
        """テンプレートレンダリング成功テスト"""
        template = "エピソード{episode_number}: {title} - テーマ: {theme}"
        context = {"episode_number": 5, "title": "テストタイトル", "theme": "友情"}

        rendered = self.service._render_template(template, context)
        expected = "エピソード5: テストタイトル - テーマ: 友情"

        assert rendered == expected

    @pytest.mark.spec("SPEC-STAGED-003")
    def test_template_rendering_missing_placeholder(self):
        """プレースホルダー不足のテンプレートレンダリングテスト"""
        template = "エピソード{episode_number}: {title}"
        context = {"episode_number": 5}  # titleが不足

        # 不足したプレースホルダーはそのまま残る
        rendered = self.service._render_template(template, context)
        assert rendered == "エピソード5: {title}"

    @pytest.mark.spec("SPEC-STAGED-003")
    def test_template_rendering_exception_handling(self):
        """テンプレートレンダリング例外処理テスト"""
        template = None  # 無効なテンプレート
        context = {}

        with pytest.raises(ValueError, match="Template rendering failed"):
            self.service._render_template(template, context)


class TestStagedPromptGenerationServiceQualityEstimation:
    """品質スコア推定機能のテスト"""

    def setup_method(self):
        """テスト準備"""
        self.template_repository = Mock()
        self.quality_validator = Mock(spec=StageQualityValidator)
        self.service = StagedPromptGenerationService(
            template_repository=self.template_repository, quality_validator=self.quality_validator
        )

    @pytest.mark.spec("SPEC-STAGED-003")
    def test_quality_score_estimation_stage1(self):
        """Stage 1の品質スコア推定テスト"""
        context = {"episode_info": {"episode_number": 1, "project_name": "テストプロジェクト"}}

        score = self.service._estimate_quality_score(PromptStage.STAGE_1, context)

        # Stage 1の基本スコア70.0 + エピソード情報完全性ボーナス5%
        assert score >= 70.0
        assert score <= 100.0

    @pytest.mark.spec("SPEC-STAGED-003")
    def test_quality_score_estimation_stage5(self):
        """Stage 5の品質スコア推定テスト"""
        context = {
            "episode_info": {"episode_number": 1, "project_name": "テストプロジェクト"},
            "stage_1_result": {},
            "stage_2_result": {},
            "stage_3_result": {},
            "stage_4_result": {},
            "include_foreshadowing": True,
        }

        score = self.service._estimate_quality_score(PromptStage.STAGE_5, context)

        # Stage 5の基本スコア90.0 + 各種ボーナス
        assert score >= 90.0
        assert score <= 100.0

    @pytest.mark.spec("SPEC-STAGED-003")
    def test_quality_score_estimation_with_completed_stages(self):
        """完了段階を含む品質スコア推定テスト"""
        context = {"stage_1_result": {}, "stage_2_result": {}, "stage_3_result": {}}

        score = self.service._estimate_quality_score(PromptStage.STAGE_4, context)

        # 完了段階によるボーナス（段階あたり+2%）が適用される
        base_score = 85.0  # Stage 4基本スコア
        completed_stages_bonus = 1.0 + 3 * 0.02  # 3段階完了で+6%
        expected_minimum = base_score * completed_stages_bonus

        assert score >= expected_minimum

    @pytest.mark.spec("SPEC-STAGED-003")
    def test_quality_score_estimation_maximum_cap(self):
        """品質スコア上限テスト"""
        # 非常に多くのボーナス要素を含むコンテキスト
        context = {
            "episode_info": {"episode_number": 1, "project_name": "テストプロジェクト"},
            "stage_1_result": {},
            "stage_2_result": {},
            "stage_3_result": {},
            "stage_4_result": {},
            "include_emotional_elements": True,
            "include_foreshadowing": True,
        }

        score = self.service._estimate_quality_score(PromptStage.STAGE_5, context)

        # 100点を超えない
        assert score <= 100.0
