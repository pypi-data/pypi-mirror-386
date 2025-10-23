"""Domain.services.enhanced_staged_prompt_generation_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

"高度化された段階的プロンプト生成サービス"
import collections.abc as cabc
from pathlib import Path
from typing import Any

from noveler.domain.entities.chapter_plot import ChapterPlot
from noveler.domain.entities.previous_episode_context import PreviousEpisodeContext
from noveler.domain.entities.staged_prompt import StagedPrompt
from noveler.domain.services.contextual_inference_engine import ContextualInferenceEngine, DynamicPromptContext
from noveler.domain.services.previous_episode_extraction_service import PreviousEpisodeExtractionService
from noveler.domain.services.staged_prompt_generation_service import (
    PromptGenerationResult,
    StagedPromptGenerationService,
    StagedPromptTemplateRepository,
)
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.prompt_stage import PromptStage


class EnhancedStagedPromptGenerationService(StagedPromptGenerationService):
    """高度化された段階的プロンプト生成サービス

    既存のStagedPromptGenerationServiceを拡張し、以下の高度化機能を追加:
    - 前話情報の自動抽出・統合
    - 動的コンテキスト推論による適応的プロンプト生成
    - エピソード進行に応じた段階的品質基準の調整
    - キャラクター成長段階に対応したコンテンツ生成
    """

    def __init__(
        self, template_repository: StagedPromptTemplateRepository, quality_validator, project_root: Path
    ) -> None:
        """高度化サービス初期化

        Args:
            template_repository: テンプレートリポジトリ
            quality_validator: 品質検証サービス
            project_root: プロジェクトルートパス
        """
        super().__init__(template_repository, quality_validator)
        self._previous_extractor = PreviousEpisodeExtractionService()
        self._inference_engine = ContextualInferenceEngine()
        self._project_root = project_root

    def generate_enhanced_stage_prompt(
        self,
        staged_prompt: StagedPrompt,
        target_stage: PromptStage,
        chapter_plot: ChapterPlot | None,
        base_context: dict[str, Any],
    ) -> PromptGenerationResult:
        """高度化された段階別プロンプト生成（包括的エラー対応版）

        Args:
            staged_prompt: 段階的プロンプトエンティティ
            target_stage: 目標段階
            chapter_plot: 章別プロット情報
            base_context: ベースコンテキスト

        Returns:
            高度化されたプロンプト生成結果
        """
        try:
            episode_number = EpisodeNumber(staged_prompt.episode_number)
            previous_context, extraction_logs = self._extract_previous_context(episode_number)
            try:
                dynamic_context = self._generate_dynamic_context(episode_number, chapter_plot, previous_context)
            except Exception:
                fallback = self._generate_fallback_prompt(staged_prompt, target_stage, base_context)
                return self._append_log_warnings(fallback, previous_context, extraction_logs)
            try:
                enhanced_context = self._build_enhanced_context(
                    base_context, previous_context, dynamic_context, target_stage
                )
            except Exception:
                enhanced_context = base_context.copy()
            try:
                adjusted_quality_criteria = self._adjust_quality_criteria_for_stage(target_stage, dynamic_context)
            except Exception:
                adjusted_quality_criteria = {}
            try:
                generation_result = self._generate_adaptive_prompt(
                    staged_prompt, target_stage, enhanced_context, adjusted_quality_criteria
                )
            except Exception as e:
                if "'<' not supported between instances of" in str(e):
                    fallback = self._generate_fallback_prompt(staged_prompt, target_stage, base_context)
                    return self._append_log_warnings(fallback, previous_context, extraction_logs)
                raise
            try:
                generation_result = self._enrich_generation_result(
                    generation_result, previous_context, dynamic_context, target_stage
                )
            except Exception:
                generation_result.warnings.append("一部高度化情報の付加に失敗しました")
            return self._append_log_warnings(generation_result, previous_context, extraction_logs)
        except TypeError as te:
            if "'<' not supported between instances of" in str(te):
                try:
                    fallback_result = self._generate_fallback_prompt(staged_prompt, target_stage, base_context)
                    fallback_result.warnings.append(
                        f"Stage {target_stage.stage_number}で型エラーが発生したため、代替実行しました"
                    )
                    return self._append_log_warnings(fallback_result, previous_context, extraction_logs)
                except Exception:
                    pass
        except Exception as e:
            error_msg = str(e)
            if "'<' not supported between instances of" in error_msg:
                try:
                    fallback_result = self._generate_fallback_prompt(staged_prompt, target_stage, base_context)
                    fallback_result.warnings.append(f"型比較エラーにより代替実行: {error_msg}")
                    return self._append_log_warnings(fallback_result, previous_context, extraction_logs)
                except Exception:
                    error_msg = f"Type comparison error detected and fallback failed: {error_msg}"
            failure_result = PromptGenerationResult(
                success=False,
                generated_prompt="",
                quality_score=0.0,
                execution_time_minutes=0,
                stage_content={},
                warnings=[],
                error_message=f"Enhanced prompt generation failed: {error_msg}",
            )
            return self._append_log_warnings(failure_result, previous_context, extraction_logs)

    def _generate_fallback_prompt(
        self, staged_prompt: StagedPrompt, fallback_stage: PromptStage, base_context: dict[str, Any]
    ) -> PromptGenerationResult:
        """型エラー時の代替プロンプト生成

        Args:
            staged_prompt: 段階的プロンプトエンティティ
            fallback_stage: 代替段階
            base_context: ベースコンテキスト

        Returns:
            代替プロンプト生成結果
        """
        try:
            fallback_prompt = f"\n第{staged_prompt.episode_number}話のプロット作成\n\n## 基本要素\n- エピソード番号: {staged_prompt.episode_number}\n- 段階: {fallback_stage.stage_name}\n- 推定作成時間: {fallback_stage.estimated_duration_minutes}分\n\n## 作成指針\n{fallback_stage.stage_name}の段階として、以下の要素を重視してプロットを作成してください：\n\n{chr(10).join(f'- {element}' for element in fallback_stage.required_elements)}\n\n## 完了条件\n{chr(10).join(f'- {criteria}' for criteria in fallback_stage.completion_criteria)}\n\n型エラーにより高度化機能が一時的に無効化されていますが、\n基本的なプロット生成機能は正常に動作します。\n            ".strip()
            return PromptGenerationResult(
                success=True,
                generated_prompt=fallback_prompt,
                quality_score=65.0,
                execution_time_minutes=fallback_stage.estimated_duration_minutes,
                stage_content={"fallback_mode": True, "original_context": base_context},
                warnings=["高度化機能が一時的に無効化されています"],
            )
        except Exception as e:
            return PromptGenerationResult(
                success=False,
                generated_prompt="",
                quality_score=0.0,
                execution_time_minutes=0,
                stage_content={},
                warnings=[],
                error_message=f"Fallback prompt generation failed: {e!s}",
            )

    def _extract_previous_context(
        self,
        episode_number: EpisodeNumber,
    ) -> tuple[PreviousEpisodeContext | None, list[dict[str, str]]]:
        """Extract previous context while capturing diagnostic messages."""
        logs: list[dict[str, str]] = []
        try:
            context = self._previous_extractor.extract_previous_episode_context(
                episode_number,
                self._project_root,
                log=lambda level, message: logs.append({"level": level, "message": message}),
            )
            return context, logs
        except Exception as exc:  # pragma: no cover - defensive guard
            logs.append({"level": "error", "message": f"前話コンテキスト抽出エラー: {exc}"})
            return None, logs

    def _generate_dynamic_context(
        self,
        episode_number: EpisodeNumber,
        chapter_plot: ChapterPlot | None,
        previous_context: PreviousEpisodeContext | None,
    ) -> DynamicPromptContext:
        """動的コンテキスト生成

        Args:
            episode_number: エピソード番号
            chapter_plot: 章別プロット
            previous_context: 前話コンテキスト

        Returns:
            動的プロンプトコンテキスト
        """
        return self._inference_engine.generate_dynamic_context(episode_number, chapter_plot, previous_context)

    @staticmethod
    def _append_log_warnings(
        result: PromptGenerationResult,
        previous_context: PreviousEpisodeContext | None,
        extraction_logs: list[dict[str, str]],
    ) -> PromptGenerationResult:
        """Propagate diagnostic messages into the result warnings."""
        log_entries: list[dict[str, str]] = list(extraction_logs)
        if previous_context is not None:
            log_entries.extend(getattr(previous_context, "log_messages", []))

        if not log_entries:
            return result

        warnings = list(result.warnings or [])
        warnings.extend(
            entry["message"]
            for entry in log_entries
            if entry.get("message") and entry.get("level") in {"warning", "error"}
        )
        result.warnings = warnings
        return result

    def _build_enhanced_context(
        self,
        base_context: dict[str, Any],
        previous_context: PreviousEpisodeContext | None,
        dynamic_context: DynamicPromptContext,
        target_stage: PromptStage,
    ) -> dict[str, Any]:
        """拡張コンテキスト構築

        Args:
            base_context: ベースコンテキスト
            previous_context: 前話コンテキスト
            dynamic_context: 動的コンテキスト
            target_stage: 目標段階

        Returns:
            拡張コンテキスト辞書
        """
        enhanced_context = base_context.copy()
        if previous_context and previous_context.has_sufficient_context():
            enhanced_context["previous_episode"] = {
                "context_summary": previous_context.get_contextual_summary(),
                "character_states": {
                    name: state.to_yaml_dict() for (name, state) in previous_context.character_states.items()
                },
                "story_progression": previous_context.story_progression.to_yaml_dict(),
                "technical_learning": previous_context.technical_learning.to_yaml_dict(),
                "emotional_flow": previous_context.emotional_flow,
                "unresolved_elements": previous_context.unresolved_elements,
                "scene_continuity": previous_context.scene_continuity_notes,
            }
        else:
            enhanced_context["previous_episode"] = {
                "context_summary": "前話情報は利用できません（第1話または抽出失敗）",
                "character_states": {},
                "story_progression": {},
                "technical_learning": {},
                "emotional_flow": [],
                "unresolved_elements": [],
                "scene_continuity": [],
            }
        enhanced_context["dynamic_context"] = {
            "story_phase": dynamic_context.story_phase,
            "character_growth_stage": dynamic_context.character_growth_stage,
            "technical_complexity_level": dynamic_context.technical_complexity_level,
            "emotional_focus_areas": dynamic_context.emotional_focus_areas,
            "adaptive_elements": dynamic_context.adaptive_elements,
            "high_confidence_inferences": [
                inf.to_yaml_dict() for inf in dynamic_context.get_high_confidence_inferences()
            ],
        }
        enhanced_context["stage_specific"] = self._build_stage_specific_context(target_stage, dynamic_context)
        return enhanced_context

    def _build_stage_specific_context(
        self, target_stage: PromptStage, dynamic_context: DynamicPromptContext
    ) -> dict[str, Any]:
        """段階別特化コンテキスト構築

        Args:
            target_stage: 目標段階
            dynamic_context: 動的コンテキスト

        Returns:
            段階別特化コンテキスト
        """
        stage_specific = {}
        stage_number = target_stage.stage_number
        adaptive_elements = dynamic_context.adaptive_elements
        if stage_number == 1:
            stage_specific["focus"] = "基本構造と必須要素"
            stage_specific["detail_level"] = adaptive_elements.get("prompt_detail_level", "balanced")
            stage_specific["explanation_depth"] = adaptive_elements.get("explanation_depth", "moderate")
        elif stage_number == 2:
            stage_specific["focus"] = "三幕構成とシーン構造"
            stage_specific["structure_emphasis"] = True
            if adaptive_elements.get("continuity_emphasis") == "high":
                stage_specific["scene_transition_support"] = True
        elif stage_number == 3:
            stage_specific["focus"] = "詳細描写と感情表現"
            stage_specific["emotional_focus_areas"] = dynamic_context.emotional_focus_areas
            stage_specific["emotional_depth"] = adaptive_elements.get("emotional_depth", "enhanced")
        elif stage_number == 4:
            stage_specific["focus"] = "技術要素統合と伏線回収"
            stage_specific["technical_complexity"] = dynamic_context.technical_complexity_level
            stage_specific["unresolved_integration"] = adaptive_elements.get("unresolved_integration", False)
        elif stage_number == 5:
            stage_specific["focus"] = "最終品質チェックと完成度向上"
            stage_specific["quality_criteria_level"] = self._determine_quality_level(dynamic_context)
        if adaptive_elements.get("milestone_episode"):
            stage_specific["milestone_considerations"] = True
            stage_specific["reflection_enhancement"] = True
        if adaptive_elements.get("introduction_mode"):
            stage_specific["introduction_support"] = True
            stage_specific["world_building_emphasis"] = True
        return stage_specific

    def _adjust_quality_criteria_for_stage(
        self, target_stage: PromptStage, dynamic_context: DynamicPromptContext
    ) -> dict[str, Any]:
        """段階的品質基準の調整

        Args:
            target_stage: 目標段階
            dynamic_context: 動的コンテキスト

        Returns:
            調整された品質基準
        """
        base_criteria = {1: 70.0, 2: 75.0, 3: 80.0, 4: 85.0, 5: 90.0}
        target_score = base_criteria.get(target_stage.stage_number, 80.0)
        growth_adjustments = {"beginner": -5.0, "learning": 0.0, "practicing": 2.0, "competent": 5.0, "expert": 8.0}
        growth_stage = dynamic_context.character_growth_stage
        adjustment = growth_adjustments.get(growth_stage, 0.0)
        adjusted_score = target_score + adjustment
        complexity_adjustments = {"basic": -3.0, "intermediate": 0.0, "advanced": 3.0, "expert": 5.0}
        complexity_level = dynamic_context.technical_complexity_level
        complexity_adjustment = complexity_adjustments.get(complexity_level, 0.0)
        adjusted_score += complexity_adjustment
        phase_adjustments = {"introduction": -2.0, "development": 0.0, "climax": 3.0, "resolution": 2.0}
        phase_adjustment = phase_adjustments.get(dynamic_context.story_phase, 0.0)
        adjusted_score += phase_adjustment
        final_score = min(adjusted_score, 100.0)
        return {
            "target_quality_score": final_score,
            "base_score": target_score,
            "growth_adjustment": adjustment,
            "complexity_adjustment": complexity_adjustment,
            "phase_adjustment": phase_adjustment,
            "reasoning": f"基準{target_score}点から成長段階({growth_stage}), 技術複雑度({complexity_level}), ストーリーフェーズ({dynamic_context.story_phase})により調整",
        }

    def _generate_adaptive_prompt(
        self,
        staged_prompt: StagedPrompt,
        target_stage: PromptStage,
        enhanced_context: dict[str, Any],
        quality_criteria: dict[str, Any],
    ) -> PromptGenerationResult:
        """適応的プロンプト生成

        Args:
            staged_prompt: 段階的プロンプト
            target_stage: 目標段階
            enhanced_context: 拡張コンテキスト
            quality_criteria: 品質基準

        Returns:
            プロンプト生成結果
        """
        base_result = super().generate_stage_prompt(staged_prompt, target_stage, enhanced_context)
        if not base_result.success:
            return base_result
        adaptive_elements = enhanced_context.get("dynamic_context", {}).get("adaptive_elements", {})
        adjusted_prompt = self._apply_adaptive_adjustments(
            base_result.generated_prompt, adaptive_elements, target_stage
        )
        adjusted_quality_score = self._calculate_adjusted_quality_score(
            base_result.quality_score, quality_criteria, enhanced_context
        )
        return PromptGenerationResult(
            success=True,
            generated_prompt=adjusted_prompt,
            quality_score=adjusted_quality_score,
            execution_time_minutes=base_result.execution_time_minutes,
            stage_content=enhanced_context,
            warnings=base_result.warnings,
        )

    def _apply_adaptive_adjustments(
        self, base_prompt: str, adaptive_elements: dict[str, Any], target_stage: PromptStage
    ) -> str:
        """適応的調整をプロンプトに適用

        Args:
            base_prompt: ベースプロンプト
            adaptive_elements: 適応的要素
            target_stage: 目標段階

        Returns:
            調整済みプロンプト
        """
        adjusted_prompt = base_prompt
        detail_level = adaptive_elements.get("prompt_detail_level", "balanced")
        if detail_level == "detailed":
            adjusted_prompt += "\n\n【詳細モード】具体的な描写と丁寧な説明を重視してください。"
        elif detail_level == "concise":
            adjusted_prompt += "\n\n【簡潔モード】要点を押さえた効率的な表現を心がけてください。"
        if adaptive_elements.get("continuity_emphasis") == "high":
            adjusted_prompt += "\n\n【継続性重視】前話からの自然な流れを特に意識してください。"
        emotional_depth = adaptive_elements.get("emotional_depth")
        if emotional_depth == "enhanced":
            adjusted_prompt += "\n\n【感情描写強化】キャラクターの内面と感情の変化を丁寧に描写してください。"
        elif emotional_depth == "basic":
            adjusted_prompt += "\n\n【アクション重視】動作と出来事を中心とした展開を心がけてください。"
        if adaptive_elements.get("milestone_episode"):
            adjusted_prompt += (
                "\n\n【節目エピソード】これまでの成長と今後への展望を含めた特別な意味を持たせてください。"
            )
        if adaptive_elements.get("introduction_mode"):
            adjusted_prompt += "\n\n【導入エピソード】世界観とキャラクターの魅力的な紹介を重視してください。"
        return adjusted_prompt

    def _calculate_adjusted_quality_score(
        self, base_score: float, quality_criteria: dict[str, Any], enhanced_context: dict[str, Any]
    ) -> float:
        """調整済み品質スコア計算

        Args:
            base_score: ベーススコア
            quality_criteria: 品質基準
            enhanced_context: 拡張コンテキスト

        Returns:
            調整済み品質スコア
        """
        target_score = quality_criteria.get("target_quality_score", 80.0)
        score_ratio = target_score / 80.0
        adjusted_score = base_score * score_ratio
        previous_info = enhanced_context.get("previous_episode", {})
        if previous_info.get("character_states") or previous_info.get("unresolved_elements"):
            adjusted_score *= 1.05
        high_confidence_inferences = enhanced_context.get("dynamic_context", {}).get("high_confidence_inferences", [])
        if isinstance(high_confidence_inferences, list) and len(high_confidence_inferences) >= 3:
            adjusted_score *= 1.03
        return min(adjusted_score, 100.0)

    def _enrich_generation_result(
        self,
        result: PromptGenerationResult,
        previous_context: PreviousEpisodeContext | None,
        dynamic_context: DynamicPromptContext,
        target_stage: PromptStage,
    ) -> PromptGenerationResult:
        """生成結果の情報拡充（型安全性強化版）

        Args:
            result: 生成結果
            previous_context: 前話コンテキスト
            dynamic_context: 動的コンテキスト
            target_stage: 目標段階

        Returns:
            拡充された生成結果
        """
        try:
            additional_warnings = []
            if not previous_context or not previous_context.has_sufficient_context():
                additional_warnings.append("前話情報が不十分です。手動での補完を推奨します。")
            low_confidence_inferences = []
            for inf in dynamic_context.inferences:
                try:
                    score = inf.confidence_score
                    if isinstance(score, list):
                        score = float(score[0]) if len(score) > 0 else 0.0
                    elif not isinstance(score, int | float):
                        score = 0.0
                    if score < 0.7:
                        low_confidence_inferences.append(inf)
                except (TypeError, ValueError):
                    low_confidence_inferences.append(inf)
            if len(low_confidence_inferences) > 2:
                additional_warnings.append("複数の推論結果で信頼度が低くなっています。生成内容を確認してください。")
            enriched_stage_content = result.stage_content.copy()
            try:
                high_confidence_count = len(dynamic_context.get_high_confidence_inferences())
            except Exception:
                high_confidence_count = 0
            try:
                adaptive_elements_count = len(dynamic_context.adaptive_elements)
            except Exception:
                adaptive_elements_count = 0
            enriched_stage_content["enhancement_metadata"] = {
                "previous_context_available": previous_context is not None
                and previous_context.has_sufficient_context(),
                "inference_count": len(dynamic_context.inferences),
                "high_confidence_inference_count": high_confidence_count,
                "adaptive_elements_count": adaptive_elements_count,
                "stage_specific_adjustments": True,
            }
            return PromptGenerationResult(
                success=result.success,
                generated_prompt=result.generated_prompt,
                quality_score=result.quality_score,
                execution_time_minutes=result.execution_time_minutes,
                stage_content=enriched_stage_content,
                warnings=result.warnings + additional_warnings,
                error_message=result.error_message,
            )
        except Exception as e:
            return PromptGenerationResult(
                success=result.success,
                generated_prompt=result.generated_prompt,
                quality_score=result.quality_score,
                execution_time_minutes=result.execution_time_minutes,
                stage_content=result.stage_content,
                warnings=[*result.warnings, "エラーにより一部拡充情報を省略しました"],
                error_message=result.error_message or f"Enhancement error: {e!s}",
            )

    def _determine_quality_level(self, dynamic_context: DynamicPromptContext) -> str:
        """品質レベル判定

        Args:
            dynamic_context: 動的コンテキスト

        Returns:
            品質レベル文字列
        """
        growth_stage = dynamic_context.character_growth_stage
        complexity_level = dynamic_context.technical_complexity_level
        if growth_stage in ["expert", "competent"] and complexity_level in ["advanced", "expert"]:
            return "premium"
        if growth_stage in ["practicing", "competent"] and complexity_level in ["intermediate", "advanced"]:
            return "standard"
        return "basic"
