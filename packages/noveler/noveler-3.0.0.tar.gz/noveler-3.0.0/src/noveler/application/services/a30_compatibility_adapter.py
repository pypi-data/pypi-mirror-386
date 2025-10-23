"""Compatibility adapter bridging legacy five-stage and A30 ten-stage systems."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar

from noveler.domain.value_objects.a30_prompt_template import A30PromptTemplateRegistry, PromptTemplateType
from noveler.domain.value_objects.detailed_execution_stage import DetailedExecutionStage
from noveler.domain.value_objects.five_stage_writing_execution import ExecutionStage
from noveler.domain.value_objects.structured_step_output import (
    NextStepInstructions,
    QualityMetrics,
    StepCompletionStatus,
    StructuredStepOutput,
)


class CompatibilityMode(Enum):
    """Available compatibility modes used during migration."""

    LEGACY_FIVE_STAGE = "legacy_five_stage"  # 既存5段階モード
    A30_DETAILED_TEN_STAGE = "a30_detailed_ten_stage"  # A30準拠10段階モード
    HYBRID_GRADUAL_MIGRATION = "hybrid_gradual_migration"  # ハイブリッド段階移行モード


@dataclass
class ExecutionStageMapping:
    """Mapping between legacy execution stages and detailed stages."""

    legacy_stage: ExecutionStage
    detailed_stages: list[DetailedExecutionStage]
    a30_steps: list[int]
    migration_priority: int  # 移行優先度 (1=高, 3=低)

    @property
    def expansion_ratio(self) -> float:
        """Return the expansion ratio from legacy to detailed stages."""
        return len(self.detailed_stages)


class A30CompatibilityAdapter:
    """Provide bridging functions between legacy and A30 prompt workflows."""

    # 段階マッピングテーブル
    STAGE_MAPPINGS: ClassVar[list[ExecutionStageMapping]] = [
        ExecutionStageMapping(
            legacy_stage=ExecutionStage.DATA_COLLECTION,
            detailed_stages=[DetailedExecutionStage.DATA_COLLECTION],
            a30_steps=[0, 1, 2],
            migration_priority=3,
        ),
        ExecutionStageMapping(
            legacy_stage=ExecutionStage.PLOT_ANALYSIS,
            detailed_stages=[DetailedExecutionStage.PLOT_ANALYSIS],
            a30_steps=[3, 4],
            migration_priority=2,
        ),
        ExecutionStageMapping(
            legacy_stage=ExecutionStage.EPISODE_DESIGN,
            detailed_stages=[
                DetailedExecutionStage.LOGIC_VERIFICATION,
                DetailedExecutionStage.CHARACTER_CONSISTENCY,
                DetailedExecutionStage.DIALOGUE_DESIGN,
                DetailedExecutionStage.EMOTION_CURVE,
                DetailedExecutionStage.SCENE_ATMOSPHERE,
            ],
            a30_steps=[5, 6, 7, 8, 9],
            migration_priority=1,  # 最高優先度（最大の改善効果）
        ),
        ExecutionStageMapping(
            legacy_stage=ExecutionStage.MANUSCRIPT_WRITING,
            detailed_stages=[DetailedExecutionStage.MANUSCRIPT_WRITING],
            a30_steps=[10],
            migration_priority=3,
        ),
        ExecutionStageMapping(
            legacy_stage=ExecutionStage.QUALITY_FINALIZATION,
            detailed_stages=[DetailedExecutionStage.QUALITY_FINALIZATION],
            a30_steps=[11, 12, 13, 14, 15],
            migration_priority=2,
        ),
    ]

    def __init__(self, compatibility_mode: CompatibilityMode = CompatibilityMode.HYBRID_GRADUAL_MIGRATION) -> None:
        """Initialize the adapter with the desired compatibility mode."""
        self.compatibility_mode = compatibility_mode
        self._legacy_to_detailed_map = self._build_stage_mapping()
        self._detailed_to_legacy_map = self._build_reverse_mapping()

    def convert_legacy_to_detailed(self, legacy_stage: ExecutionStage) -> list[DetailedExecutionStage]:
        """Return detailed stages mapped from a legacy execution stage."""
        if self.compatibility_mode == CompatibilityMode.LEGACY_FIVE_STAGE:
            # レガシーモードでは1:1マッピングを維持
            return [self._get_equivalent_detailed_stage(legacy_stage)]

        return self._legacy_to_detailed_map.get(legacy_stage, [])

    def convert_detailed_to_legacy(self, detailed_stage: DetailedExecutionStage) -> ExecutionStage:
        """Return the legacy stage corresponding to a detailed stage."""
        return self._detailed_to_legacy_map.get(detailed_stage, ExecutionStage.EPISODE_DESIGN)

    def get_execution_plan(self, target_episode: int) -> dict[str, Any]:
        """Return an execution plan tailored to the current compatibility mode."""
        if self.compatibility_mode == CompatibilityMode.LEGACY_FIVE_STAGE:
            return self._get_legacy_execution_plan(target_episode)
        if self.compatibility_mode == CompatibilityMode.A30_DETAILED_TEN_STAGE:
            return self._get_a30_detailed_execution_plan(target_episode)
        return self._get_hybrid_execution_plan(target_episode)

    def create_stage_specific_prompt(
        self, stage: DetailedExecutionStage, context_data: dict[str, Any]
    ) -> dict[str, str]:
        """Generate a prompt tailored to the provided detailed stage."""
        if not stage.is_new_detailed_stage or self.compatibility_mode == CompatibilityMode.LEGACY_FIVE_STAGE:
            # レガシーモードまたは既存段階の場合はフォールバック
            return self._create_fallback_prompt(stage, context_data)

        # A30準拠プロンプトテンプレートを使用
        template_type = self._determine_template_type(stage)
        template = A30PromptTemplateRegistry.get_template(stage, template_type)

        # テンプレートが必要とする変数を補完
        enhanced_context = self._enhance_context_data(stage, context_data)

        try:
            user_prompt = template.format_user_prompt(**enhanced_context)
        except KeyError:
            # 必要な変数が不足している場合はフォールバックプロンプトを使用
            return self._create_fallback_prompt(stage, context_data)

        return {
            "system": template.system_prompt,
            "user": user_prompt,
            "expected_format": template.expected_output_format,
            "quality_criteria": template.quality_criteria,
        }

    def create_compatible_output(
        self, stage: DetailedExecutionStage, raw_output: dict[str, Any], quality_scores: dict[str, float]
    ) -> StructuredStepOutput:
        """Produce structured output compatible with both legacy and A30 flows."""
        # quality_scoresからQualityMetricsオブジェクトを作成
        overall_score = quality_scores.get("overall", 0.0) if quality_scores else 0.0
        quality_metrics = QualityMetrics(
            overall_score=overall_score, specific_metrics=quality_scores if quality_scores else {}
        )

        # NextStepInstructionsを生成
        next_step_context = self._generate_next_step_context(stage, raw_output)
        if isinstance(next_step_context, dict):
            # 辞書形式の場合はNextStepInstructionsオブジェクトに変換
            next_step_instructions = NextStepInstructions(
                focus_areas=next_step_context.get("focus_areas", []),
                constraints=next_step_context.get("constraints", []),
                quality_threshold=next_step_context.get("quality_threshold", 0.8),
                additional_context=next_step_context.get("additional_context", {}),
            )
        else:
            next_step_instructions = next_step_context

        return StructuredStepOutput(
            step_id=f"step_{stage.value}",
            step_name=stage.display_name,
            completion_status=StepCompletionStatus.COMPLETED,
            structured_data=raw_output,
            quality_metrics=quality_metrics,
            next_step_context=next_step_instructions,
            validation_passed=self._validate_output(stage, raw_output),
            execution_metadata={
                "compatibility_mode": self.compatibility_mode.value,
                "a30_compliance": stage.is_new_detailed_stage,
                "legacy_equivalent": self.convert_detailed_to_legacy(stage).value,
            },
        )

    def get_migration_recommendations(self) -> dict[str, Any]:
        """Return recommendations for migrating between compatibility modes."""
        return {
            "current_mode": self.compatibility_mode.value,
            "recommended_next_step": self._get_next_migration_step(),
            "high_priority_improvements": self._get_high_priority_stages(),
            "expected_benefits": self._calculate_migration_benefits(),
            "implementation_effort": self._estimate_implementation_effort(),
        }

    def _build_stage_mapping(self) -> dict[ExecutionStage, list[DetailedExecutionStage]]:
        """Construct the legacy-to-detailed stage mapping table."""
        mapping = {}
        for stage_mapping in self.STAGE_MAPPINGS:
            mapping[stage_mapping.legacy_stage] = stage_mapping.detailed_stages
        return mapping

    def _build_reverse_mapping(self) -> dict[DetailedExecutionStage, ExecutionStage]:
        """Construct the detailed-to-legacy stage mapping table."""
        reverse_mapping = {}
        for stage_mapping in self.STAGE_MAPPINGS:
            for detailed_stage in stage_mapping.detailed_stages:
                reverse_mapping[detailed_stage] = stage_mapping.legacy_stage
        return reverse_mapping

    def _get_equivalent_detailed_stage(self, legacy_stage: ExecutionStage) -> DetailedExecutionStage:
        """Return the default detailed stage equivalent for pure legacy mode."""
        equivalents = {
            ExecutionStage.DATA_COLLECTION: DetailedExecutionStage.DATA_COLLECTION,
            ExecutionStage.PLOT_ANALYSIS: DetailedExecutionStage.PLOT_ANALYSIS,
            ExecutionStage.EPISODE_DESIGN: DetailedExecutionStage.LOGIC_VERIFICATION,  # 代表として
            ExecutionStage.MANUSCRIPT_WRITING: DetailedExecutionStage.MANUSCRIPT_WRITING,
            ExecutionStage.QUALITY_FINALIZATION: DetailedExecutionStage.QUALITY_FINALIZATION,
        }
        return equivalents[legacy_stage]

    def _get_legacy_execution_plan(self, episode: int) -> dict[str, Any]:
        """Return an execution plan compatible with the legacy five-stage flow."""
        return {
            "mode": "legacy_five_stage",
            "total_stages": 5,
            "expected_turns": 16,
            "stages": [stage.value for stage in ExecutionStage],
            "a30_coverage": 0.30,
            "episode": episode,
        }

    def _get_a30_detailed_execution_plan(self, episode: int) -> dict[str, Any]:
        """Return an execution plan compatible with the detailed A30 flow."""
        return {
            "mode": "a30_detailed_ten_stage",
            "total_stages": len(DetailedExecutionStage),
            "expected_turns": DetailedExecutionStage.get_total_expected_turns(),
            "stages": [stage.value for stage in DetailedExecutionStage],
            "a30_coverage": 0.80,
            "episode": episode,
            "new_detailed_stages": [stage.value for stage in DetailedExecutionStage if stage.is_new_detailed_stage],
        }

    def _get_hybrid_execution_plan(self, episode: int) -> dict[str, Any]:
        """Return a hybrid execution plan mixing legacy and detailed stages."""
        high_priority = self._get_high_priority_stages()

        return {
            "mode": "hybrid_gradual_migration",
            "total_stages": 5 + len(high_priority),  # 基本5段階 + 優先詳細段階
            "expected_turns": 16 + len(high_priority) * 2,
            "priority_migrations": high_priority,
            "a30_coverage": 0.60,  # 段階的向上
            "episode": episode,
        }

    def _determine_template_type(self, stage: DetailedExecutionStage) -> PromptTemplateType:
        """Determine which prompt template type should be used for a stage."""
        type_mapping = {
            DetailedExecutionStage.LOGIC_VERIFICATION: PromptTemplateType.VERIFICATION,
            DetailedExecutionStage.CHARACTER_CONSISTENCY: PromptTemplateType.VERIFICATION,
            DetailedExecutionStage.DIALOGUE_DESIGN: PromptTemplateType.DESIGN,
            DetailedExecutionStage.EMOTION_CURVE: PromptTemplateType.DESIGN,
            DetailedExecutionStage.SCENE_ATMOSPHERE: PromptTemplateType.DESIGN,
        }
        return type_mapping.get(stage, PromptTemplateType.STRUCTURE_ANALYSIS)

    def _create_fallback_prompt(self, stage: DetailedExecutionStage, context: dict[str, Any]) -> dict[str, str]:
        """Create a simple fallback prompt when no detailed template is available."""
        return {
            "system": f"あなたは{stage.display_name}の専門家です。",
            "user": f"{stage.get_stage_description()}\n\n以下の情報を基に処理してください：\n{context}",
            "expected_format": "YAML形式で結果を出力してください。",
            "quality_criteria": ["基本的な品質基準を満たす"],
        }

    def _enhance_context_data(self, stage: DetailedExecutionStage, context_data: dict[str, Any]) -> dict[str, Any]:
        """Augment context data with defaults required by prompt templates."""
        enhanced = context_data.copy()

        # A30テンプレートで使用されるすべての変数のデフォルト値
        default_values = {
            # 基本情報
            "plot_content": enhanced.get("plot_content", "プロット内容は利用できません"),
            "character_settings": enhanced.get("character_settings", "キャラクター設定は利用できません"),
            "world_settings": enhanced.get("world_settings", "世界設定は利用できません"),
            "expected_output_format": enhanced.get("expected_output_format", "YAML形式"),
            "character_growth_history": enhanced.get(
                "character_growth_history", "前エピソードでのキャラクター成長履歴は利用できません"
            ),
            "scene_setting": enhanced.get("scene_setting", "シーン設定の詳細情報は利用できません"),
            "participating_characters": enhanced.get(
                "participating_characters", "参加キャラクターの詳細は利用できません"
            ),
            "dialogue_purpose": enhanced.get("dialogue_purpose", "対話の目的・意図は特に設定されていません"),
            "required_information": enhanced.get("required_information", "必要情報は特に指定されていません"),
            "scene_structure": enhanced.get("scene_structure", "シーン構造は特に設定されていません"),
            "main_characters": enhanced.get("main_characters", "主要キャラクターの詳細は利用できません"),
            "emotional_turning_points": enhanced.get(
                "emotional_turning_points", "感情的な転換点は特に設定されていません"
            ),
            "scene_basic_setting": enhanced.get("scene_basic_setting", "シーンの基本設定は利用できません"),
            "world_details": enhanced.get("world_details", "世界観の詳細は利用できません"),
            "atmosphere_requirements": enhanced.get("atmosphere_requirements", "雰囲気要件は特に設定されていません"),
            # 追加の共通変数
            "previous_plot_elements": enhanced.get("previous_plot_elements", "前エピソードの情報は利用できません"),
            "story_progression": enhanced.get("story_progression", "物語の進行状況は利用できません"),
            "world_state_changes": enhanced.get("world_state_changes", "世界設定の変更はありません"),
            "conflict_resolution_status": enhanced.get("conflict_resolution_status", "未解決の対立要素はありません"),
            "emotional_arc_context": enhanced.get("emotional_arc_context", "感情的なアーク情報は利用できません"),
            "dialogue_style_preferences": enhanced.get("dialogue_style_preferences", "デフォルトの対話スタイルを使用"),
            "scene_atmosphere_requirements": enhanced.get(
                "scene_atmosphere_requirements", "特別な雰囲気要件はありません"
            ),
            "target_word_count": enhanced.get("target_word_count", 3500),
            "episode_number": enhanced.get("episode_number", 1),
            "genre_specific_elements": enhanced.get(
                "genre_specific_elements", "ジャンル固有要素の情報は利用できません"
            ),
            "current_conflict": enhanced.get("current_conflict", "現在の対立要素は特定されていません"),
            "mood_requirements": enhanced.get("mood_requirements", "ムード要件は特に設定されていません"),
            "pacing_requirements": enhanced.get("pacing_requirements", "ペース要件は特に設定されていません"),
            "tension_level": enhanced.get("tension_level", "標準"),
            "quality_standards": enhanced.get("quality_standards", "標準的な品質基準を適用"),
            "narrative_voice": enhanced.get("narrative_voice", "三人称視点"),
            "time_setting": enhanced.get("time_setting", "時間設定の詳細は利用できません"),
            "location_details": enhanced.get("location_details", "場所の詳細情報は利用できません"),
            "theme_elements": enhanced.get("theme_elements", "テーマ要素は特に設定されていません"),
            "foreshadowing_elements": enhanced.get("foreshadowing_elements", "伏線要素は特に設定されていません"),
            "reader_experience_goals": enhanced.get("reader_experience_goals", "読者体験目標は特に設定されていません"),
            "chapter_context": enhanced.get("chapter_context", "章のコンテキスト情報は利用できません"),
            "series_context": enhanced.get("series_context", "シリーズのコンテキスト情報は利用できません"),
        }

        # 段階固有の拡張
        if stage == DetailedExecutionStage.CHARACTER_CONSISTENCY:
            default_values.update(
                {
                    "character_relationship_matrix": enhanced.get(
                        "character_relationship_matrix", "キャラクター関係図は利用できません"
                    ),
                    "personality_consistency_checklist": enhanced.get(
                        "personality_consistency_checklist", "一貫性チェックリストはありません"
                    ),
                    "character_arc_progression": enhanced.get(
                        "character_arc_progression", "キャラクターアーク進行情報は利用できません"
                    ),
                }
            )
        elif stage == DetailedExecutionStage.DIALOGUE_DESIGN:
            default_values.update(
                {
                    "character_voice_profiles": enhanced.get(
                        "character_voice_profiles", "キャラクターの声質プロファイルは利用できません"
                    ),
                    "dialogue_tension_requirements": enhanced.get(
                        "dialogue_tension_requirements", "特別な緊張感要件はありません"
                    ),
                    "speech_patterns": enhanced.get("speech_patterns", "話し方パターンは特に設定されていません"),
                }
            )
        elif stage == DetailedExecutionStage.EMOTION_CURVE:
            default_values.update(
                {
                    "emotional_peak_targets": enhanced.get(
                        "emotional_peak_targets", "感情の頂点ターゲットは設定されていません"
                    ),
                    "reader_engagement_goals": enhanced.get(
                        "reader_engagement_goals", "読者エンゲージメント目標は設定されていません"
                    ),
                    "emotional_transitions": enhanced.get(
                        "emotional_transitions", "感情遷移の詳細は設定されていません"
                    ),
                }
            )
        elif stage == DetailedExecutionStage.SCENE_ATMOSPHERE:
            default_values.update(
                {
                    "sensory_detail_requirements": enhanced.get(
                        "sensory_detail_requirements", "感覚的描写要件は特にありません"
                    ),
                    "mood_transition_plan": enhanced.get("mood_transition_plan", "ムード転換計画はありません"),
                    "atmosphere_keywords": enhanced.get("atmosphere_keywords", "雰囲気キーワードは設定されていません"),
                }
            )

        # デフォルト値で不足している変数を補完
        for key, default_value in default_values.items():
            if key not in enhanced:
                enhanced[key] = default_value

        return enhanced

    def _generate_next_step_context(
        self, current_stage: DetailedExecutionStage, output: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate metadata describing instructions for the next step."""
        return {
            "completed_stage": current_stage.value,
            "key_outputs": list(output.keys()) if output else [],
            "stage_specific_context": self._extract_stage_context(current_stage, output),
            "ready_for_next": True,
        }

    def _extract_stage_context(self, stage: DetailedExecutionStage, output: dict[str, Any]) -> dict[str, Any]:
        """Extract context tailored to the specified detailed stage."""
        if stage == DetailedExecutionStage.LOGIC_VERIFICATION:
            return {"verified_logic": output.get("logic_verification_result", {})}
        if stage == DetailedExecutionStage.CHARACTER_CONSISTENCY:
            return {"character_analysis": output.get("character_consistency_result", {})}
        if stage == DetailedExecutionStage.DIALOGUE_DESIGN:
            return {"dialogue_structure": output.get("dialogue_design_result", {})}
        # その他の段階の処理...
        return {"generic_output": output}

    def _validate_output(self, stage: DetailedExecutionStage, output: dict[str, Any]) -> bool:
        """Perform stage-aware validation of generated output."""
        if not output:
            return False

        # 段階固有の検証
        if stage.is_new_detailed_stage:
            # A30準拠段階の詳細検証
            return self._validate_a30_stage_output(stage, output)

        # 基本検証
        return len(output) > 0

    def _validate_a30_stage_output(self, stage: DetailedExecutionStage, output: dict[str, Any]) -> bool:
        """Validate detailed-stage output against expected keys."""
        required_keys = {
            DetailedExecutionStage.LOGIC_VERIFICATION: ["logic_verification_result"],
            DetailedExecutionStage.CHARACTER_CONSISTENCY: ["character_consistency_result"],
            DetailedExecutionStage.DIALOGUE_DESIGN: ["dialogue_design_result"],
            DetailedExecutionStage.EMOTION_CURVE: ["emotion_curve_result"],
            DetailedExecutionStage.SCENE_ATMOSPHERE: ["scene_atmosphere_result"],
        }

        stage_requirements = required_keys.get(stage, [])
        return all(key in output for key in stage_requirements)

    def _get_next_migration_step(self) -> str:
        """Return a textual recommendation for the next migration step."""
        if self.compatibility_mode == CompatibilityMode.LEGACY_FIVE_STAGE:
            return "HYBRID_GRADUAL_MIGRATIONモードへの移行を推奨"
        if self.compatibility_mode == CompatibilityMode.HYBRID_GRADUAL_MIGRATION:
            return "A30_DETAILED_TEN_STAGEモードへの完全移行を推奨"
        return "現在のモードを継続"

    def _get_high_priority_stages(self) -> list[str]:
        """Return detailed stages marked as highest priority for migration."""
        return [mapping.detailed_stages[0].value for mapping in self.STAGE_MAPPINGS if mapping.migration_priority == 1]

    def _calculate_migration_benefits(self) -> dict[str, float]:
        """Return illustrative benefit metrics when adopting detailed stages."""
        return {
            "a30_compliance_improvement": 0.50,  # 50ポイント向上
            "execution_precision_gain": 0.40,  # 40%精度向上
            "quality_consistency_boost": 0.35,  # 35%品質向上
            "total_roi": 2.67,  # 2.67倍の効果
        }

    def _estimate_implementation_effort(self) -> dict[str, Any]:
        """Provide a coarse estimate of effort required for migration."""
        return {
            "development_days": 7,
            "testing_days": 3,
            "migration_days": 2,
            "total_effort": 12,
            "complexity": "medium",
            "risk_level": "low",
        }
