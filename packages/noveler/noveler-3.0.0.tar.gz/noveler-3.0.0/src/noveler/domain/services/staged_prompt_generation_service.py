"""
段階的プロンプト生成のドメインサービス

SPEC-STAGED-003: StagedPromptGenerationServiceの実装
- 段階別プロンプト生成ロジック
- 品質検証の統合
- テンプレート適用
"""

from dataclasses import dataclass
from typing import Any

from noveler.domain.entities.staged_prompt import StagedPrompt
from noveler.domain.value_objects.prompt_stage import PromptStage


@dataclass
class PromptGenerationResult:
    """プロンプト生成結果"""

    success: bool
    generated_prompt: str
    quality_score: float
    execution_time_minutes: int
    stage_content: dict[str, Any]
    warnings: list[str]
    error_message: str | None = None


@dataclass
class ValidationResult:
    """品質検証結果"""

    is_valid: bool
    quality_score: float
    validation_errors: list[str]
    validation_warnings: list[str]
    improvement_suggestions: list[str]


class StagedPromptTemplateRepository:
    """段階別プロンプトテンプレートリポジトリインターフェース

    WARNING: このクラスは未実装です。
    実装が完了するまでNotImplementedErrorが発生します。
    """

    def find_template_by_stage(self, stage: PromptStage) -> str | None:
        """段階別テンプレート取得

        Note: 実装待ち。現在はデフォルトテンプレートを返します。
        """
        return f"Default template for stage {stage.stage_number if hasattr(stage, 'stage_number') else 'unknown'}"

    def get_template_context_keys(self, stage: PromptStage) -> list[str]:
        """テンプレート必須コンテキストキー取得

        Note: 実装待ち。現在は基本キーのみ返します。
        """
        return ["episode_number", "project_name", "stage_info"]


class StageQualityValidator:
    """段階別品質検証インターフェース

    WARNING: このクラスは未実装です。
    実装が完了するまで基本的な検証のみ行います。
    """

    def validate(self, stage: PromptStage, content: dict[str, Any]) -> ValidationResult:
        """段階別品質検証実行

        Note: 実装待ち。現在は基本的な検証のみ行います。
        """
        # 基本的な検証のみ
        errors: list[Any] = []
        warnings = []

        if not content:
            errors.append("Content is empty")

        return ValidationResult(
            is_valid=len(errors) == 0,
            quality_score=75.0,  # デフォルトスコア
            validation_errors=errors,
            validation_warnings=warnings,
            improvement_suggestions=["Implement full validation logic"],
        )


class StagedPromptGenerationService:
    """段階的プロンプト生成のドメインサービス

    各段階でのプロンプト生成、品質検証、テンプレート適用を統合管理する。
    ビジネスルールに従って段階的な品質向上を実現する。
    """

    def __init__(self, template_repository: StagedPromptTemplateRepository, quality_validator: StageQualityValidator) -> None:
        """サービス初期化

        Args:
            template_repository: テンプレートリポジトリ
            quality_validator: 品質検証サービス
        """
        self._template_repository = template_repository
        self._quality_validator = quality_validator

    def generate_stage_prompt(
        self, staged_prompt: StagedPrompt, target_stage: PromptStage, context: dict[str, Any]
    ) -> PromptGenerationResult:
        """段階別プロンプト生成

        Args:
            staged_prompt: 段階的プロンプトエンティティ
            target_stage: 目標段階
            context: 生成コンテキスト

        Returns:
            プロンプト生成結果
        """
        try:
            # 段階移行可能性確認
            if not staged_prompt.can_advance_to_stage(target_stage):
                return PromptGenerationResult(
                    success=False,
                    generated_prompt="",
                    quality_score=0.0,
                    execution_time_minutes=0,
                    stage_content={},
                    warnings=[],
                    error_message=f"Cannot advance to stage {target_stage.stage_number}",
                )

            # テンプレート取得
            template = self._template_repository.find_template_by_stage(target_stage)
            if not template:
                return PromptGenerationResult(
                    success=False,
                    generated_prompt="",
                    quality_score=0.0,
                    execution_time_minutes=0,
                    stage_content={},
                    warnings=[],
                    error_message=f"Template not found for stage {target_stage.stage_number}",
                )

            # コンテキスト検証
            validation_errors = self._validate_context(target_stage, context)
            if validation_errors:
                return PromptGenerationResult(
                    success=False,
                    generated_prompt="",
                    quality_score=0.0,
                    execution_time_minutes=0,
                    stage_content={},
                    warnings=[],
                    error_message=f"Context validation failed: {', '.join(validation_errors)}",
                )

            # 段階別コンテキスト構築
            stage_context = self._build_stage_context(staged_prompt, target_stage, context)

            # プロンプト生成
            generated_prompt = self._render_template(template, stage_context)

            # 品質評価（暫定）
            quality_score = self._estimate_quality_score(target_stage, stage_context)

            return PromptGenerationResult(
                success=True,
                generated_prompt=generated_prompt,
                quality_score=quality_score,
                execution_time_minutes=target_stage.estimated_duration_minutes,
                stage_content=stage_context,
                warnings=[],
            )

        except Exception as e:
            return PromptGenerationResult(
                success=False,
                generated_prompt="",
                quality_score=0.0,
                execution_time_minutes=0,
                stage_content={},
                warnings=[],
                error_message=f"Unexpected error in prompt generation: {e!s}",
            )

    def validate_stage_completion(
        self, staged_prompt: StagedPrompt, stage: PromptStage, generated_content: dict[str, Any]
    ) -> ValidationResult:
        """段階完了検証

        Args:
            staged_prompt: 段階的プロンプトエンティティ
            stage: 検証対象段階
            generated_content: 生成されたコンテンツ

        Returns:
            検証結果
        """
        # 基本的な完了基準チェック
        basic_errors = staged_prompt.validate_stage_completion_criteria(stage, generated_content)

        # 品質検証サービスによる詳細検証
        quality_validation = self._quality_validator.validate(stage, generated_content)

        # 結果統合
        all_errors = basic_errors + quality_validation.validation_errors
        all_warnings = quality_validation.validation_warnings

        return ValidationResult(
            is_valid=len(all_errors) == 0,
            quality_score=quality_validation.quality_score,
            validation_errors=all_errors,
            validation_warnings=all_warnings,
            improvement_suggestions=quality_validation.improvement_suggestions,
        )

    def get_stage_progression_recommendation(self, staged_prompt: StagedPrompt) -> dict[str, Any]:
        """段階進行推奨事項取得"""
        current_stage = staged_prompt.current_stage
        next_stage = staged_prompt.get_next_stage()

        can_advance = next_stage is not None and staged_prompt.can_advance_to_stage(next_stage)

        recommendations = {
            "current_stage": {
                "number": current_stage.stage_number,
                "name": current_stage.stage_name,
                "is_completed": staged_prompt.is_stage_completed(current_stage),
            },
            "can_advance": can_advance,
            "completion_percentage": staged_prompt.get_completion_percentage(),
            "average_quality_score": staged_prompt.get_average_quality_score(),
        }

        if can_advance and next_stage:
            recommendations["next_stage"] = {
                "number": next_stage.stage_number,
                "name": next_stage.stage_name,
                "estimated_duration": next_stage.estimated_duration_minutes,
                "required_elements": next_stage.required_elements,
            }

        if recommendations["average_quality_score"] < 80.0:
            recommendations["quality_improvement_needed"] = True
            recommendations["recommendations"] = [
                "Consider improving content quality before advancing",
                "Review completion criteria for current stage",
                "Consider rolling back to previous stage for refinement",
            ]

        return recommendations

    def _validate_context(self, stage: PromptStage, context: dict[str, Any]) -> list[str]:
        """コンテキスト検証"""
        errors: list[Any] = []

        required_keys = self._template_repository.get_template_context_keys(stage)
        for key in required_keys:
            if key not in context:
                errors.append(f"Required context key missing: {key}")
            elif not context[key]:
                errors.append(f"Required context key is empty: {key}")

        stage_number = stage.stage_number

        if stage_number >= 3 and "character_settings" not in context:
            errors.append("Character settings required for stage 3 and above")

        if stage_number >= 4 and "foreshadowing_data" not in context:
            errors.append("Foreshadowing data required for stage 4 and above")

        return errors

    def _build_stage_context(
        self, staged_prompt: StagedPrompt, target_stage: PromptStage, base_context: dict[str, Any]
    ) -> dict[str, Any]:
        """段階別コンテキスト構築

        Args:
            staged_prompt: 段階的プロンプトエンティティ
            target_stage: 目標段階
            base_context: ベースコンテキスト

        Returns:
            段階別コンテキスト
        """
        stage_context = base_context.copy()

        # 段階情報の追加
        stage_context["stage_info"] = {
            "current_stage": target_stage.stage_number,
            "stage_name": target_stage.stage_name,
            "estimated_duration": target_stage.estimated_duration_minutes,
            "required_elements": target_stage.required_elements,
            "completion_criteria": target_stage.completion_criteria,
        }

        # エピソード基本情報
        stage_context["episode_info"] = {
            "episode_number": staged_prompt.episode_number,
            "project_name": staged_prompt.project_name,
        }

        # 前段階結果の統合
        for completed_stage in staged_prompt.completed_stages:
            stage_result = staged_prompt.get_stage_result(completed_stage)
            if stage_result:
                stage_context[f"stage_{completed_stage.stage_number}_result"] = stage_result

        # 段階別の特殊コンテキスト
        if target_stage.stage_number >= 2:
            stage_context["include_structure_elements"] = True

        if target_stage.stage_number >= 3:
            stage_context["include_detailed_scenes"] = True
            stage_context["include_emotional_elements"] = True

        if target_stage.stage_number >= 4:
            stage_context["include_integration_elements"] = True
            stage_context["include_foreshadowing"] = True

        if target_stage.stage_number == 5:
            stage_context["include_quality_metrics"] = True
            stage_context["finalize_content"] = True

        return stage_context

    def _render_template(self, template: str, context: dict[str, Any]) -> str:
        """テンプレートレンダリング"""
        if not isinstance(template, str) or not template:
            raise ValueError("Template rendering failed: invalid template content")

        try:
            rendered = template
            for key, value in context.items():
                placeholder = f"{{{key}}}"
                if placeholder in rendered:
                    rendered = rendered.replace(placeholder, str(value))
            return rendered
        except Exception as e:
            msg = f"Template rendering failed: {e!s}"
            raise ValueError(msg)

    def _estimate_quality_score(self, stage: PromptStage, context: dict[str, Any]) -> float:
        """品質スコア推定

        Args:
            stage: 対象段階
            context: コンテキスト

        Returns:
            推定品質スコア（0-100）
        """
        # 基本スコア（段階別）
        base_scores = {
            1: 70.0,  # Stage 1: 基本的な品質
            2: 75.0,  # Stage 2: 構造品質
            3: 80.0,  # Stage 3: 表現品質
            4: 85.0,  # Stage 4: 統合品質
            5: 90.0,  # Stage 5: 完成品質
        }

        base_score = base_scores.get(stage.stage_number, 70.0)

        # コンテキスト品質による調整
        quality_factors = []

        # エピソード情報の完全性
        episode_info = context.get("episode_info", {})
        if episode_info.get("episode_number") and episode_info.get("project_name"):
            quality_factors.append(1.05)  # +5%

        # 前段階結果の存在
        completed_stages_count = len([k for k in context if k.startswith("stage_") and k.endswith("_result")])
        if completed_stages_count > 0:
            quality_factors.append(1.0 + completed_stages_count * 0.02)  # 段階あたり+2%

        # 段階別特殊要素
        if stage.stage_number >= 3 and context.get("include_emotional_elements"):
            quality_factors.append(1.03)  # +3%

        if stage.stage_number >= 4 and context.get("include_foreshadowing"):
            quality_factors.append(1.03)  # +3%

        # 調整の適用
        adjusted_score = base_score
        for factor in quality_factors:
            adjusted_score *= factor

        # 100点を上限とする
        return min(adjusted_score, 100.0)
