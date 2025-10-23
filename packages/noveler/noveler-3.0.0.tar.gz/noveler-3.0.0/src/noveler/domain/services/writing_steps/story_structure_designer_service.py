"""Domain.services.writing_steps.story_structure_designer_service
Where: Domain service module implementing a specific writing workflow step.
What: Provides helper routines and data structures for this writing step.
Why: Allows stepwise writing orchestrators to reuse consistent step logic.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""物語構造設計サービス

A38執筆プロンプトガイド STEP 1: 大骨（章の目的線）の実装。
物語の骨組みとなる章構成と目的設定。
"""

import time
from typing import Any

from noveler.domain.services.writing_steps.base_writing_step import (
    BaseWritingStep,
    WritingStepResponse,
)


class StoryStructureDesignerService(BaseWritingStep):
    """物語構造設計サービス

    A38 STEP 1: 物語の大骨（章の目的線）を設計し、
    エピソード全体の構造的な骨組みを構築する。
    """

    def __init__(self) -> None:
        super().__init__(
            step_number=1,
            step_name="大骨（章の目的線）"
        )

    async def execute(
        self,
        episode_number: int,
        previous_results: dict[int, Any] | None = None
    ) -> WritingStepResponse:
        """物語構造設計を実行

        Args:
            episode_number: エピソード番号
            previous_results: 前のステップの実行結果

        Returns:
            物語構造設計結果
        """
        start_time = time.time()

        try:
            # STEP 0からスコープ情報を取得
            scope_data = self.extract_data_from_previous_step(
                previous_results, 0, "data"
            )

            # 物語構造の基本設計
            story_structure = self._design_basic_structure(
                episode_number, scope_data
            )

            # 章構成の設計
            chapter_composition = self._design_chapter_composition(
                story_structure, episode_number
            )

            # 目的線の設定
            purpose_lines = self._establish_purpose_lines(
                chapter_composition, scope_data
            )

            # 構造バランスの検証
            balance_check = self._verify_structural_balance(
                story_structure, chapter_composition, purpose_lines
            )

            # 実行時間計算
            execution_time = (time.time() - start_time) * 1000

            return WritingStepResponse(
                success=True,
                step_number=self.step_number,
                step_name=self.step_name,
                execution_time_ms=execution_time,
                data={
                    "story_structure": story_structure,
                    "chapter_composition": chapter_composition,
                    "purpose_lines": purpose_lines,
                    "balance_check": balance_check,
                    "total_chapters": len(chapter_composition),
                    "structural_integrity": balance_check.get("overall_score", 7.0)
                }
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return WritingStepResponse(
                success=False,
                step_number=self.step_number,
                step_name=self.step_name,
                execution_time_ms=execution_time,
                error_message=str(e)
            )

    def _design_basic_structure(self, episode_number: int, scope_data: dict[str, Any] | None) -> dict[str, Any]:
        """基本的な物語構造を設計"""

        # スコープデータから基本情報を抽出
        episode_type = self._determine_episode_type(episode_number, scope_data)
        target_length = self._estimate_target_length(episode_type, scope_data)
        narrative_style = self._select_narrative_style(episode_type, episode_number)

        return {
            "episode_number": episode_number,
            "episode_type": episode_type,
            "narrative_style": narrative_style,
            "target_length": target_length,
            "structural_approach": self._choose_structural_approach(episode_type),
            "pacing_strategy": self._determine_pacing_strategy(episode_type, episode_number),
            "tension_arc": self._design_tension_arc(episode_type),
            "climax_positioning": self._calculate_climax_position(target_length),
            "resolution_approach": self._plan_resolution_approach(episode_type, episode_number)
        }


    def _determine_episode_type(self, episode_number: int, scope_data: dict[str, Any] | None) -> str:
        """エピソードタイプを決定"""

        # スコープデータから情報を取得
        if scope_data and "episode_classification" in scope_data:
            return scope_data["episode_classification"]

        # エピソード番号による基本分類
        if episode_number == 1:
            return "introduction"
        if episode_number <= 3:
            return "early_development"
        if episode_number <= 7:
            return "main_development"
        if episode_number <= 12:
            return "advanced_development"
        return "climax_resolution"

    def _estimate_target_length(self, episode_type: str, scope_data: dict[str, Any] | None) -> dict[str, Any]:
        """目標文字数を推定"""

        # スコープデータからの情報優先
        if scope_data and "target_word_count" in scope_data:
            base_count = scope_data["target_word_count"]
        else:
            # エピソードタイプによるデフォルト設定
            type_defaults = {
                "introduction": 3500,
                "early_development": 4000,
                "main_development": 4500,
                "advanced_development": 5000,
                "climax_resolution": 5500
            }
            base_count = type_defaults.get(episode_type, 4000)

        return {
            "target_words": base_count,
            "minimum_words": int(base_count * 0.8),
            "maximum_words": int(base_count * 1.2),
            "flexibility_range": int(base_count * 0.1)
        }

    def _select_narrative_style(self, episode_type: str, episode_number: int) -> dict[str, str]:
        """語りスタイルを選択"""

        style_combinations = {
            "introduction": {
                "perspective": "third_person_limited",
                "tense": "past",
                "voice": "descriptive",
                "focus": "character_establishment"
            },
            "early_development": {
                "perspective": "third_person_limited",
                "tense": "past",
                "voice": "engaging",
                "focus": "world_building"
            },
            "main_development": {
                "perspective": "third_person_limited",
                "tense": "past",
                "voice": "dynamic",
                "focus": "plot_progression"
            },
            "advanced_development": {
                "perspective": "third_person_limited",
                "tense": "past",
                "voice": "intense",
                "focus": "conflict_escalation"
            },
            "climax_resolution": {
                "perspective": "third_person_limited",
                "tense": "past",
                "voice": "dramatic",
                "focus": "resolution_catharsis"
            }
        }

        return style_combinations.get(episode_type, style_combinations["main_development"])

    def _choose_structural_approach(self, episode_type: str) -> dict[str, Any]:
        """構造的アプローチを選択"""

        approaches = {
            "introduction": {
                "structure_type": "gradual_introduction",
                "opening_hook": "character_intrigue",
                "development_pattern": "linear_exposition",
                "conflict_introduction": "subtle_hints"
            },
            "early_development": {
                "structure_type": "building_momentum",
                "opening_hook": "situation_development",
                "development_pattern": "ascending_tension",
                "conflict_introduction": "clear_obstacles"
            },
            "main_development": {
                "structure_type": "multi_layered_progression",
                "opening_hook": "immediate_engagement",
                "development_pattern": "complex_weaving",
                "conflict_introduction": "full_confrontation"
            },
            "advanced_development": {
                "structure_type": "escalating_drama",
                "opening_hook": "high_stakes_opening",
                "development_pattern": "intensifying_pressure",
                "conflict_introduction": "crisis_convergence"
            },
            "climax_resolution": {
                "structure_type": "climactic_resolution",
                "opening_hook": "final_challenge",
                "development_pattern": "resolution_sequence",
                "conflict_introduction": "ultimate_confrontation"
            }
        }

        return approaches.get(episode_type, approaches["main_development"])

    def _determine_pacing_strategy(self, episode_type: str, episode_number: int) -> dict[str, Any]:
        """ペーシング戦略を決定"""

        return {
            "overall_tempo": self._calculate_overall_tempo(episode_type),
            "acceleration_points": self._identify_acceleration_points(episode_type),
            "deceleration_zones": self._identify_deceleration_zones(episode_type),
            "rhythm_variations": self._plan_rhythm_variations(episode_type),
            "pacing_techniques": self._select_pacing_techniques(episode_type)
        }

    def _calculate_overall_tempo(self, episode_type: str) -> str:
        """全体テンポを計算"""

        tempo_map = {
            "introduction": "moderate",
            "early_development": "building",
            "main_development": "dynamic",
            "advanced_development": "fast",
            "climax_resolution": "variable"
        }

        return tempo_map.get(episode_type, "moderate")

    def _identify_acceleration_points(self, episode_type: str) -> list[dict[str, Any]]:
        """加速ポイントを特定"""

        acceleration_patterns = {
            "introduction": [
                {"location": "hook", "intensity": "medium", "technique": "curiosity_spike"},
                {"location": "character_reveal", "intensity": "low", "technique": "personality_glimpse"}
            ],
            "early_development": [
                {"location": "plot_point", "intensity": "medium", "technique": "conflict_introduction"},
                {"location": "character_decision", "intensity": "high", "technique": "action_sequence"}
            ],
            "main_development": [
                {"location": "major_revelation", "intensity": "high", "technique": "information_burst"},
                {"location": "confrontation", "intensity": "very_high", "technique": "dialogue_rapid_fire"}
            ],
            "advanced_development": [
                {"location": "crisis_escalation", "intensity": "very_high", "technique": "time_pressure"},
                {"location": "stakes_raising", "intensity": "extreme", "technique": "parallel_tension"}
            ],
            "climax_resolution": [
                {"location": "final_confrontation", "intensity": "extreme", "technique": "maximum_intensity"},
                {"location": "resolution_sequence", "intensity": "high", "technique": "rapid_conclusion"}
            ]
        }

        return acceleration_patterns.get(episode_type, acceleration_patterns["main_development"])

    def _identify_deceleration_zones(self, episode_type: str) -> list[dict[str, Any]]:
        """減速ゾーンを特定"""

        deceleration_patterns = {
            "introduction": [
                {"location": "world_building", "purpose": "information_absorption", "technique": "descriptive_passages"},
                {"location": "character_depth", "purpose": "emotional_connection", "technique": "internal_monologue"}
            ],
            "early_development": [
                {"location": "reflection_moment", "purpose": "character_processing", "technique": "contemplative_scenes"},
                {"location": "relationship_building", "purpose": "bond_strengthening", "technique": "dialogue_development"}
            ],
            "main_development": [
                {"location": "strategy_planning", "purpose": "tactical_thinking", "technique": "analytical_sequences"},
                {"location": "emotional_processing", "purpose": "character_growth", "technique": "introspective_moments"}
            ],
            "advanced_development": [
                {"location": "calm_before_storm", "purpose": "tension_building", "technique": "ominous_quiet"},
                {"location": "character_preparation", "purpose": "final_readiness", "technique": "determination_scenes"}
            ],
            "climax_resolution": [
                {"location": "aftermath_processing", "purpose": "impact_absorption", "technique": "reflective_conclusion"},
                {"location": "new_equilibrium", "purpose": "closure_establishment", "technique": "peaceful_resolution"}
            ]
        }

        return deceleration_patterns.get(episode_type, deceleration_patterns["main_development"])

    def _plan_rhythm_variations(self, episode_type: str) -> dict[str, Any]:
        """リズム変化を計画"""

        return {
            "pattern_type": self._determine_rhythm_pattern(episode_type),
            "variation_frequency": self._calculate_variation_frequency(episode_type),
            "intensity_range": self._define_intensity_range(episode_type),
            "transition_smoothness": self._set_transition_smoothness(episode_type)
        }

    def _determine_rhythm_pattern(self, episode_type: str) -> str:
        """リズムパターン決定"""

        patterns = {
            "introduction": "gradual_build",
            "early_development": "wave_pattern",
            "main_development": "escalating_peaks",
            "advanced_development": "high_frequency_peaks",
            "climax_resolution": "mountain_peak_pattern"
        }

        return patterns.get(episode_type, "wave_pattern")

    def _select_pacing_techniques(self, episode_type: str) -> list[str]:
        """ペーシング技法を選択"""

        technique_sets = {
            "introduction": [
                "descriptive_establishment",
                "character_voice_development",
                "world_immersion",
                "curiosity_hooks"
            ],
            "early_development": [
                "momentum_building",
                "conflict_seeding",
                "character_interaction",
                "plot_thread_weaving"
            ],
            "main_development": [
                "tension_escalation",
                "multi_thread_juggling",
                "rapid_scene_cuts",
                "emotional_peaks"
            ],
            "advanced_development": [
                "crisis_intensification",
                "time_pressure_creation",
                "stakes_amplification",
                "parallel_tension_building"
            ],
            "climax_resolution": [
                "climactic_convergence",
                "resolution_orchestration",
                "emotional_catharsis",
                "narrative_closure"
            ]
        }

        return technique_sets.get(episode_type, technique_sets["main_development"])

    def _design_tension_arc(self, episode_type: str) -> dict[str, Any]:
        """緊張弧を設計"""

        return {
            "starting_tension": self._calculate_starting_tension(episode_type),
            "peak_tension": self._calculate_peak_tension(episode_type),
            "tension_progression": self._map_tension_progression(episode_type),
            "release_points": self._identify_tension_release_points(episode_type),
            "sustained_levels": self._define_sustained_tension_levels(episode_type)
        }

    def _calculate_starting_tension(self, episode_type: str) -> int:
        """開始時緊張度計算（1-10スケール）"""

        starting_levels = {
            "introduction": 3,
            "early_development": 4,
            "main_development": 5,
            "advanced_development": 7,
            "climax_resolution": 8
        }

        return starting_levels.get(episode_type, 5)

    def _calculate_peak_tension(self, episode_type: str) -> int:
        """ピーク緊張度計算（1-10スケール）"""

        peak_levels = {
            "introduction": 6,
            "early_development": 7,
            "main_development": 8,
            "advanced_development": 9,
            "climax_resolution": 10
        }

        return peak_levels.get(episode_type, 8)

    def _calculate_climax_position(self, target_length: dict[str, Any]) -> dict[str, Any]:
        """クライマックス位置を計算"""

        target_words = target_length["target_words"]

        return {
            "optimal_position": int(target_words * 0.75),  # 75%位置
            "acceptable_range": {
                "earliest": int(target_words * 0.65),      # 65%位置
                "latest": int(target_words * 0.85)         # 85%位置
            },
            "buildup_zone": {
                "start": int(target_words * 0.45),         # 45%位置から
                "peak": int(target_words * 0.75)           # 75%位置まで
            },
            "resolution_zone": {
                "start": int(target_words * 0.75),         # 75%位置から
                "end": target_words                        # 最後まで
            }
        }

    def _plan_resolution_approach(self, episode_type: str, episode_number: int) -> dict[str, Any]:
        """解決アプローチを計画"""

        return {
            "resolution_style": self._determine_resolution_style(episode_type, episode_number),
            "loose_ends_handling": self._plan_loose_ends_handling(episode_type, episode_number),
            "emotional_closure": self._design_emotional_closure(episode_type),
            "future_setup": self._plan_future_setup(episode_type, episode_number),
            "satisfaction_level": self._target_satisfaction_level(episode_type)
        }

    def _determine_resolution_style(self, episode_type: str, episode_number: int) -> str:
        """解決スタイル決定"""

        # エピソード番号による調整
        if episode_number % 5 == 0:  # 5話ごとの区切り
            return "major_resolution"
        if episode_number % 3 == 0:  # 3話ごとの区切り
            return "moderate_resolution"

        # エピソードタイプによる基本設定
        styles = {
            "introduction": "open_ended",
            "early_development": "partial_resolution",
            "main_development": "progressive_resolution",
            "advanced_development": "significant_resolution",
            "climax_resolution": "complete_resolution"
        }

        return styles.get(episode_type, "progressive_resolution")

    def _design_chapter_composition(self, story_structure: dict[str, Any], episode_number: int) -> list[dict[str, Any]]:
        """章構成を設計"""

        episode_type = story_structure["episode_type"]
        target_length = story_structure["target_length"]["target_words"]

        # 基本章数の決定
        base_chapters = self._calculate_base_chapters(episode_type, target_length)

        chapters = []
        words_per_chapter = target_length // base_chapters

        for i in range(base_chapters):
            chapter = {
                "chapter_number": i + 1,
                "chapter_purpose": self._determine_chapter_purpose(i, base_chapters, episode_type),
                "estimated_length": words_per_chapter,
                "narrative_function": self._assign_narrative_function(i, base_chapters, episode_type),
                "key_elements": self._identify_chapter_key_elements(i, base_chapters, episode_type),
                "pacing_role": self._define_chapter_pacing_role(i, base_chapters, episode_type),
                "tension_contribution": self._calculate_chapter_tension_contribution(i, base_chapters, story_structure)
            }
            chapters.append(chapter)

        return chapters

    def _calculate_base_chapters(self, episode_type: str, target_length: int) -> int:
        """基本章数を計算"""

        # 文字数による基本章数
        if target_length <= 3000:
            base_chapters = 3
        elif target_length <= 4000:
            base_chapters = 4
        elif target_length <= 5000:
            base_chapters = 5
        else:
            base_chapters = 6

        # エピソードタイプによる調整
        type_adjustments = {
            "introduction": 0,      # そのまま
            "early_development": 0, # そのまま
            "main_development": 1,  # +1章
            "advanced_development": 1, # +1章
            "climax_resolution": 0  # そのまま
        }

        adjustment = type_adjustments.get(episode_type, 0)
        return max(3, base_chapters + adjustment)  # 最低3章

    def _determine_chapter_purpose(self, chapter_index: int, total_chapters: int, episode_type: str) -> str:
        """章の目的を決定"""

        # 基本的な3幕構成ベース
        if chapter_index == 0:
            return "opening_establishment"
        if chapter_index == total_chapters - 1:
            return "resolution_closure"
        if chapter_index <= total_chapters * 0.3:
            return "setup_development"
        if chapter_index >= total_chapters * 0.7:
            return "climax_resolution"
        return "main_development"

    def _assign_narrative_function(self, chapter_index: int, total_chapters: int, episode_type: str) -> str:
        """物語機能を割り当て"""

        functions = {
            0: "hook_and_setup",
            1: "character_establishment" if total_chapters > 3 else "development_advancement",
            2: "plot_advancement" if total_chapters > 4 else "climax_approach",
        }

        # 中間章
        if chapter_index not in functions:
            if chapter_index < total_chapters - 2:
                functions[chapter_index] = "conflict_escalation"
            elif chapter_index == total_chapters - 2:
                functions[chapter_index] = "climax_buildup"

        # 最終章
        functions[total_chapters - 1] = "resolution_denouement"

        return functions.get(chapter_index, "plot_advancement")

    def _identify_chapter_key_elements(self, chapter_index: int, total_chapters: int, episode_type: str) -> list[str]:
        """章の重要要素を特定"""

        element_sets = {
            "hook_and_setup": [
                "attention_grabbing_opening",
                "character_introduction",
                "setting_establishment",
                "initial_conflict_hint"
            ],
            "character_establishment": [
                "character_depth_exploration",
                "relationship_dynamics",
                "motivation_clarification",
                "personality_showcase"
            ],
            "plot_advancement": [
                "conflict_development",
                "obstacle_introduction",
                "character_decision_points",
                "plot_thread_weaving"
            ],
            "conflict_escalation": [
                "tension_heightening",
                "stakes_raising",
                "complication_introduction",
                "pressure_building"
            ],
            "climax_buildup": [
                "final_preparation",
                "tension_peak_approach",
                "critical_moment_setup",
                "decisive_action_lead_in"
            ],
            "climax_approach": [
                "confrontation_setup",
                "peak_tension_creation",
                "critical_decisions",
                "turning_point_execution"
            ],
            "resolution_denouement": [
                "conflict_resolution",
                "character_arc_completion",
                "loose_ends_tying",
                "future_implications"
            ]
        }

        function = self._assign_narrative_function(chapter_index, total_chapters, episode_type)
        return element_sets.get(function, element_sets["plot_advancement"])

    def _define_chapter_pacing_role(self, chapter_index: int, total_chapters: int, episode_type: str) -> str:
        """章のペーシング役割を定義"""

        # 章位置による基本役割
        position_ratio = chapter_index / (total_chapters - 1) if total_chapters > 1 else 0

        if position_ratio < 0.25:
            return "pace_establishment"
        if position_ratio < 0.5:
            return "pace_building"
        if position_ratio < 0.75:
            return "pace_intensification"
        return "pace_resolution"

    def _calculate_chapter_tension_contribution(
        self,
        chapter_index: int,
        total_chapters: int,
        story_structure: dict[str, Any]
    ) -> dict[str, Any]:
        """章の緊張貢献度を計算"""

        tension_arc = story_structure["tension_arc"]
        starting_tension = tension_arc["starting_tension"]
        peak_tension = tension_arc["peak_tension"]

        # 章位置による緊張度計算
        position_ratio = chapter_index / (total_chapters - 1) if total_chapters > 1 else 0

        # 基本的な上昇カーブ（75%位置でピーク）
        if position_ratio <= 0.75:
            tension_level = starting_tension + (peak_tension - starting_tension) * (position_ratio / 0.75)
        else:
            # ピーク後の下降
            descent_ratio = (position_ratio - 0.75) / 0.25
            tension_level = peak_tension - (peak_tension - starting_tension) * 0.4 * descent_ratio

        return {
            "tension_level": round(tension_level, 1),
            "contribution_type": self._classify_tension_contribution(position_ratio),
            "tension_techniques": self._suggest_tension_techniques(position_ratio, tension_level),
            "transition_role": self._define_transition_role(chapter_index, total_chapters)
        }

    def _classify_tension_contribution(self, position_ratio: float) -> str:
        """緊張貢献タイプを分類"""

        if position_ratio < 0.25:
            return "foundation_building"
        if position_ratio < 0.5:
            return "momentum_creation"
        if position_ratio < 0.75:
            return "peak_building"
        return "resolution_guiding"

    def _suggest_tension_techniques(self, position_ratio: float, tension_level: float) -> list[str]:
        """緊張技法を提案"""

        base_techniques = []

        # 位置による技法
        if position_ratio < 0.25:
            base_techniques.extend(["subtle_foreshadowing", "character_establishment_tension"])
        elif position_ratio < 0.5:
            base_techniques.extend(["conflict_introduction", "obstacle_placement"])
        elif position_ratio < 0.75:
            base_techniques.extend(["escalation_techniques", "stakes_raising"])
        else:
            base_techniques.extend(["climax_orchestration", "resolution_preparation"])

        # 緊張レベルによる追加技法
        if tension_level >= 8:
            base_techniques.extend(["high_intensity_pacing", "dramatic_confrontation"])
        elif tension_level >= 6:
            base_techniques.extend(["moderate_tension_sustaining", "strategic_pausing"])
        else:
            base_techniques.extend(["gentle_building", "character_development_focus"])

        return base_techniques

    def _define_transition_role(self, chapter_index: int, total_chapters: int) -> str:
        """遷移役割を定義"""

        if chapter_index == 0:
            return "story_entry"
        if chapter_index == total_chapters - 1:
            return "story_exit"
        return "story_bridge"

    def _establish_purpose_lines(
        self,
        chapter_composition: list[dict[str, Any]],
        scope_data: dict[str, Any] | None
    ) -> dict[str, Any]:
        """目的線を設定"""

        return {
            "primary_purpose_line": self._define_primary_purpose_line(chapter_composition, scope_data),
            "secondary_purpose_lines": self._define_secondary_purpose_lines(chapter_composition),
            "chapter_purpose_mapping": self._create_chapter_purpose_mapping(chapter_composition),
            "purpose_coherence": self._verify_purpose_coherence(chapter_composition),
            "reader_journey": self._design_reader_journey(chapter_composition)
        }


    def _define_primary_purpose_line(self, chapter_composition: list[dict[str, Any]], scope_data: dict[str, Any] | None) -> dict[str, Any]:
        """主要目的線を定義"""

        # スコープデータから主目的を抽出
        primary_objective = "character_growth"  # デフォルト
        if scope_data and "primary_objective" in scope_data:
            primary_objective = scope_data["primary_objective"]

        return {
            "objective": primary_objective,
            "progression_method": self._determine_progression_method(primary_objective),
            "milestone_chapters": self._identify_milestone_chapters(chapter_composition, primary_objective),
            "completion_criteria": self._define_completion_criteria(primary_objective),
            "measurement_points": self._establish_measurement_points(chapter_composition, primary_objective)
        }

    def _determine_progression_method(self, objective: str) -> str:
        """進行方法を決定"""

        methods = {
            "character_growth": "incremental_development",
            "plot_resolution": "obstacle_overcoming",
            "mystery_solving": "clue_accumulation",
            "relationship_building": "interaction_deepening",
            "world_exploration": "discovery_expansion"
        }

        return methods.get(objective, "incremental_development")

    def _identify_milestone_chapters(self, chapter_composition: list[dict[str, Any]], objective: str) -> list[int]:
        """マイルストーン章を特定"""

        total_chapters = len(chapter_composition)

        # 目的によるマイルストーン配置
        if objective == "character_growth":
            return [1, total_chapters // 2, total_chapters - 1]
        if objective == "plot_resolution":
            return [1, total_chapters // 3, (total_chapters * 2) // 3, total_chapters - 1]
        return [1, total_chapters // 2, total_chapters - 1]

    def _define_secondary_purpose_lines(self, chapter_composition: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """副次目的線を定義"""

        return [
            {
                "purpose": "emotional_engagement",
                "method": "reader_connection_building",
                "distribution": "throughout"
            },
            {
                "purpose": "world_immersion",
                "method": "environmental_detail_integration",
                "distribution": "early_middle_chapters"
            },
            {
                "purpose": "tension_management",
                "method": "pacing_variation",
                "distribution": "strategic_placement"
            }
        ]


    def _create_chapter_purpose_mapping(self, chapter_composition: list[dict[str, Any]]) -> dict[int, list[str]]:
        """章目的マッピングを作成"""

        mapping = {}

        for chapter in chapter_composition:
            chapter_num = chapter["chapter_number"]
            purposes = []

            # 章機能による目的追加
            function = chapter["narrative_function"]

            function_purposes = {
                "hook_and_setup": ["reader_engagement", "story_establishment"],
                "character_establishment": ["character_development", "relationship_setup"],
                "plot_advancement": ["story_progression", "conflict_development"],
                "conflict_escalation": ["tension_building", "stakes_raising"],
                "climax_buildup": ["peak_preparation", "dramatic_tension"],
                "climax_approach": ["confrontation_setup", "resolution_initiation"],
                "resolution_denouement": ["conflict_resolution", "story_closure"]
            }

            purposes.extend(function_purposes.get(function, ["general_progression"]))
            mapping[chapter_num] = purposes

        return mapping

    def _verify_purpose_coherence(self, chapter_composition: list[dict[str, Any]]) -> dict[str, Any]:
        """目的一貫性を検証"""

        coherence_check = {
            "coherence_score": 8.0,  # デフォルトスコア
            "consistency_issues": [],
            "improvement_suggestions": [],
            "flow_assessment": "good"
        }

        # 章間の整合性チェック
        for i in range(len(chapter_composition) - 1):
            current_chapter = chapter_composition[i]
            next_chapter = chapter_composition[i + 1]

            # 機能の論理的順序チェック
            if not self._is_logical_progression(current_chapter["narrative_function"], next_chapter["narrative_function"]):
                coherence_check["consistency_issues"].append(
                    f"第{current_chapter['chapter_number']}章から第{next_chapter['chapter_number']}章への論理的飛躍"
                )
                coherence_check["coherence_score"] -= 0.5

        # 改善提案生成
        if coherence_check["coherence_score"] < 7.0:
            coherence_check["improvement_suggestions"].append("章間の論理的つながりの強化が必要")

        if coherence_check["coherence_score"] >= 8.0:
            coherence_check["flow_assessment"] = "excellent"
        elif coherence_check["coherence_score"] >= 7.0:
            coherence_check["flow_assessment"] = "good"
        else:
            coherence_check["flow_assessment"] = "needs_improvement"

        return coherence_check

    def _is_logical_progression(self, current_function: str, next_function: str) -> bool:
        """論理的進行の判定"""

        logical_sequences = {
            "hook_and_setup": ["character_establishment", "plot_advancement"],
            "character_establishment": ["plot_advancement", "conflict_escalation"],
            "plot_advancement": ["conflict_escalation", "climax_buildup"],
            "conflict_escalation": ["climax_buildup", "climax_approach"],
            "climax_buildup": ["climax_approach", "resolution_denouement"],
            "climax_approach": ["resolution_denouement"],
            "resolution_denouement": []  # 最終章
        }

        valid_next = logical_sequences.get(current_function, [])
        return next_function in valid_next or current_function == next_function

    def _design_reader_journey(self, chapter_composition: list[dict[str, Any]]) -> dict[str, Any]:
        """読者ジャーニーを設計"""

        return {
            "engagement_arc": self._map_engagement_arc(chapter_composition),
            "emotional_journey": self._design_emotional_journey(chapter_composition),
            "curiosity_management": self._plan_curiosity_management(chapter_composition),
            "satisfaction_points": self._identify_satisfaction_points(chapter_composition),
            "anticipation_building": self._structure_anticipation_building(chapter_composition)
        }

    def _map_engagement_arc(self, chapter_composition: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """エンゲージメント弧をマッピング"""

        arc = []
        for chapter in chapter_composition:
            engagement_level = self._calculate_chapter_engagement_level(chapter)
            arc.append({
                "chapter": chapter["chapter_number"],
                "engagement_level": engagement_level,
                "engagement_drivers": self._identify_engagement_drivers(chapter),
                "reader_attention_focus": self._determine_attention_focus(chapter)
            })

        return arc

    def _calculate_chapter_engagement_level(self, chapter: dict[str, Any]) -> int:
        """章のエンゲージメントレベル計算（1-10）"""

        function = chapter["narrative_function"]
        tension_level = chapter.get("tension_contribution", {}).get("tension_level", 5)

        # 基本エンゲージメントレベル
        base_levels = {
            "hook_and_setup": 8,
            "character_establishment": 6,
            "plot_advancement": 7,
            "conflict_escalation": 8,
            "climax_buildup": 9,
            "climax_approach": 10,
            "resolution_denouement": 7
        }

        base_level = base_levels.get(function, 7)

        # 緊張レベルによる調整
        tension_adjustment = (tension_level - 5) * 0.2

        return max(1, min(10, round(base_level + tension_adjustment)))

    def _identify_engagement_drivers(self, chapter: dict[str, Any]) -> list[str]:
        """エンゲージメント駆動要因を特定"""

        function = chapter["narrative_function"]

        drivers_map = {
            "hook_and_setup": ["curiosity", "novelty", "character_appeal"],
            "character_establishment": ["empathy", "relatability", "character_depth"],
            "plot_advancement": ["progression", "discovery", "anticipation"],
            "conflict_escalation": ["tension", "stakes", "uncertainty"],
            "climax_buildup": ["anticipation", "excitement", "emotional_investment"],
            "climax_approach": ["peak_excitement", "resolution_desire", "emotional_climax"],
            "resolution_denouement": ["satisfaction", "closure", "emotional_resolution"]
        }

        return drivers_map.get(function, ["general_interest"])

    def _determine_attention_focus(self, chapter: dict[str, Any]) -> str:
        """注意焦点を決定"""

        function = chapter["narrative_function"]

        focus_map = {
            "hook_and_setup": "character_and_situation",
            "character_establishment": "character_development",
            "plot_advancement": "story_progression",
            "conflict_escalation": "conflict_dynamics",
            "climax_buildup": "tension_building",
            "climax_approach": "climax_execution",
            "resolution_denouement": "resolution_satisfaction"
        }

        return focus_map.get(function, "story_progression")

    def _verify_structural_balance(
        self,
        story_structure: dict[str, Any],
        chapter_composition: list[dict[str, Any]],
        purpose_lines: dict[str, Any]
    ) -> dict[str, Any]:
        """構造バランスを検証"""

        balance_check = {
            "overall_score": 0.0,
            "structure_analysis": {},
            "balance_issues": [],
            "optimization_recommendations": [],
            "structural_strengths": []
        }

        # 各要素の分析
        structure_score = self._analyze_structure_balance(story_structure)
        chapter_score = self._analyze_chapter_balance(chapter_composition)
        purpose_score = self._analyze_purpose_balance(purpose_lines)

        # 統合スコア計算
        balance_check["overall_score"] = (structure_score + chapter_score + purpose_score) / 3

        balance_check["structure_analysis"] = {
            "story_structure_score": structure_score,
            "chapter_composition_score": chapter_score,
            "purpose_coherence_score": purpose_score
        }

        # 問題点と推奨事項の特定
        if balance_check["overall_score"] < 7.0:
            balance_check["balance_issues"].append("全体的な構造バランス改善が必要")
            balance_check["optimization_recommendations"].append("各構成要素間の調整を検討")

        if structure_score < 7.0:
            balance_check["optimization_recommendations"].append("物語構造の基本設計見直し")

        if chapter_score < 7.0:
            balance_check["optimization_recommendations"].append("章構成のバランス調整")

        if purpose_score < 7.0:
            balance_check["optimization_recommendations"].append("目的線の一貫性向上")

        # 強み特定
        if structure_score >= 8.0:
            balance_check["structural_strengths"].append("優れた基本構造設計")
        if chapter_score >= 8.0:
            balance_check["structural_strengths"].append("バランスの取れた章構成")
        if purpose_score >= 8.0:
            balance_check["structural_strengths"].append("明確で一貫した目的設定")

        return balance_check

    def _analyze_structure_balance(self, story_structure: dict[str, Any]) -> float:
        """構造バランス分析"""

        score = 8.0  # 基本スコア

        # ペーシング戦略の妥当性
        pacing = story_structure.get("pacing_strategy", {})
        if "overall_tempo" in pacing and "acceleration_points" in pacing:
            score += 0.5

        # 緊張弧の設計品質
        tension_arc = story_structure.get("tension_arc", {})
        starting = tension_arc.get("starting_tension", 5)
        peak = tension_arc.get("peak_tension", 8)

        if peak - starting >= 3:  # 適切な緊張上昇
            score += 0.5

        # クライマックス位置の適切性
        climax_pos = story_structure.get("climax_positioning", {})
        if "optimal_position" in climax_pos:
            score += 0.3

        return min(10.0, score)

    def _analyze_chapter_balance(self, chapter_composition: list[dict[str, Any]]) -> float:
        """章バランス分析"""

        score = 8.0
        total_chapters = len(chapter_composition)

        # 章数の適切性
        if 3 <= total_chapters <= 6:
            score += 0.5
        elif total_chapters > 6:
            score -= 0.3

        # 章長バランス
        lengths = [ch.get("estimated_length", 1000) for ch in chapter_composition]
        length_variance = max(lengths) - min(lengths)
        avg_length = sum(lengths) / len(lengths)

        if length_variance / avg_length < 0.3:  # 30%以内のバラつき
            score += 0.5

        # 機能分布の適切性
        functions = [ch["narrative_function"] for ch in chapter_composition]
        unique_functions = len(set(functions))

        if unique_functions >= total_chapters * 0.7:  # 70%以上がユニーク
            score += 0.3

        return min(10.0, score)

    def _analyze_purpose_balance(self, purpose_lines: dict[str, Any]) -> float:
        """目的バランス分析"""

        coherence = purpose_lines.get("purpose_coherence", {})
        coherence_score = coherence.get("coherence_score", 7.0)

        # 一貫性スコアをそのまま使用（調整あり）
        return min(10.0, coherence_score + 0.5)

    # Helper methods
    def _calculate_variation_frequency(self, episode_type: str) -> str:
        """変化頻度を計算"""
        frequencies = {
            "introduction": "low",
            "early_development": "medium",
            "main_development": "high",
            "advanced_development": "very_high",
            "climax_resolution": "variable"
        }
        return frequencies.get(episode_type, "medium")

    def _define_intensity_range(self, episode_type: str) -> dict[str, int]:
        """強度範囲を定義"""
        ranges = {
            "introduction": {"min": 2, "max": 6},
            "early_development": {"min": 3, "max": 7},
            "main_development": {"min": 4, "max": 8},
            "advanced_development": {"min": 6, "max": 9},
            "climax_resolution": {"min": 7, "max": 10}
        }
        return ranges.get(episode_type, {"min": 4, "max": 8})

    def _set_transition_smoothness(self, episode_type: str) -> str:
        """遷移滑らかさを設定"""
        smoothness = {
            "introduction": "very_smooth",
            "early_development": "smooth",
            "main_development": "dynamic",
            "advanced_development": "sharp",
            "climax_resolution": "variable"
        }
        return smoothness.get(episode_type, "smooth")

    def _map_tension_progression(self, episode_type: str) -> list[dict[str, Any]]:
        """緊張進行をマッピング"""
        return [
            {"phase": "opening", "target_tension": self._calculate_starting_tension(episode_type)},
            {"phase": "development", "target_tension": self._calculate_starting_tension(episode_type) + 2},
            {"phase": "climax", "target_tension": self._calculate_peak_tension(episode_type)},
            {"phase": "resolution", "target_tension": self._calculate_starting_tension(episode_type) + 1}
        ]

    def _identify_tension_release_points(self, episode_type: str) -> list[dict[str, str]]:
        """緊張解放点を特定"""
        return [
            {"location": "mid_development", "type": "brief_relief"},
            {"location": "pre_climax", "type": "calm_before_storm"},
            {"location": "post_climax", "type": "major_release"}
        ]

    def _define_sustained_tension_levels(self, episode_type: str) -> dict[str, int]:
        """持続緊張レベルを定義"""
        levels = {
            "introduction": 4,
            "early_development": 5,
            "main_development": 6,
            "advanced_development": 7,
            "climax_resolution": 8
        }
        return {"baseline_tension": levels.get(episode_type, 5)}

    def _plan_loose_ends_handling(self, episode_type: str, episode_number: int) -> str:
        """未解決要素処理を計画"""
        if episode_number % 10 == 0:  # 10話区切り
            return "major_resolution"
        if episode_number % 5 == 0:  # 5話区切り
            return "moderate_resolution"
        return "progressive_resolution"

    def _design_emotional_closure(self, episode_type: str) -> dict[str, str]:
        """感情的クロージャーを設計"""
        return {
            "closure_type": "satisfying" if episode_type == "climax_resolution" else "progressive",
            "emotional_tone": "uplifting" if episode_type != "advanced_development" else "intense",
            "reader_satisfaction": "high" if episode_type == "climax_resolution" else "moderate"
        }

    def _plan_future_setup(self, episode_type: str, episode_number: int) -> dict[str, Any]:
        """将来設定を計画"""
        return {
            "setup_intensity": "high" if episode_type in ["early_development", "main_development"] else "low",
            "foreshadowing_elements": 2 if episode_type == "main_development" else 1,
            "hook_for_next": episode_type != "climax_resolution"
        }

    def _target_satisfaction_level(self, episode_type: str) -> str:
        """満足度目標を設定"""
        levels = {
            "introduction": "high_curiosity",
            "early_development": "engaged_interest",
            "main_development": "compelling_involvement",
            "advanced_development": "intense_anticipation",
            "climax_resolution": "complete_satisfaction"
        }
        return levels.get(episode_type, "engaged_interest")

    def _define_completion_criteria(self, objective: str) -> list[str]:
        """完了基準を定義"""
        criteria_map = {
            "character_growth": ["明確な成長実感", "変化の具体的表現", "読者の共感獲得"],
            "plot_resolution": ["主要問題の解決", "論理的な結末", "納得できる決着"],
            "mystery_solving": ["謎の完全解明", "手がかりの論理的統合", "読者の理解獲得"],
            "relationship_building": ["関係性の明確な変化", "相互理解の深化", "感情的つながりの確立"],
            "world_exploration": ["世界観の充実", "設定の一貫性確保", "没入感の創出"]
        }
        return criteria_map.get(objective, ["基本目標の達成", "読者満足度確保"])

    def _establish_measurement_points(self, chapter_composition: list[dict[str, Any]], objective: str) -> list[dict[str, Any]]:
        """測定ポイントを設定"""
        points = []
        milestone_chapters = self._identify_milestone_chapters(chapter_composition, objective)

        for chapter_num in milestone_chapters:
            points.append({
                "chapter": chapter_num,
                "measurement_focus": f"{objective}_progress_check",
                "success_indicators": self._define_success_indicators_for_chapter(chapter_num, objective),
                "evaluation_criteria": self._define_evaluation_criteria_for_chapter(chapter_num, objective)
            })

        return points

    def _define_success_indicators_for_chapter(self, chapter_num: int, objective: str) -> list[str]:
        """章別成功指標を定義"""
        base_indicators = {
            "character_growth": [f"第{chapter_num}章での成長要素明確化", "読者の感情移入維持"],
            "plot_resolution": [f"第{chapter_num}章での進展実感", "論理的整合性確保"],
        }
        return base_indicators.get(objective, ["基本進捗確認", "品質基準達成"])

    def _define_evaluation_criteria_for_chapter(self, chapter_num: int, objective: str) -> list[str]:
        """章別評価基準を定義"""
        return [
            "目標達成度70%以上",
            "読者満足度良好",
            "次章への適切な橋渡し"
        ]

    def _design_emotional_journey(self, chapter_composition: list[dict[str, Any]]) -> list[dict[str, str]]:
        """感情ジャーニーを設計"""
        journey = []
        for chapter in chapter_composition:
            chapter_num = chapter["chapter_number"]
            function = chapter["narrative_function"]

            emotion_map = {
                "hook_and_setup": "curiosity_excitement",
                "character_establishment": "empathy_connection",
                "plot_advancement": "anticipation_engagement",
                "conflict_escalation": "tension_concern",
                "climax_buildup": "anxiety_anticipation",
                "climax_approach": "peak_excitement",
                "resolution_denouement": "satisfaction_closure"
            }

            journey.append({
                "chapter": str(chapter_num),
                "target_emotion": emotion_map.get(function, "general_interest"),
                "emotion_technique": f"{function}_emotional_design"
            })

        return journey

    def _plan_curiosity_management(self, chapter_composition: list[dict[str, Any]]) -> dict[str, Any]:
        """好奇心管理を計画"""
        return {
            "curiosity_hooks": [f"第{i+1}章フック" for i in range(len(chapter_composition))],
            "mystery_elements": "progressive_revelation",
            "information_timing": "strategic_disclosure"
        }

    def _identify_satisfaction_points(self, chapter_composition: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """満足ポイントを特定"""
        points = []
        for _i, chapter in enumerate(chapter_composition):
            if chapter["narrative_function"] in ["plot_advancement", "climax_approach", "resolution_denouement"]:
                points.append({
                    "chapter": chapter["chapter_number"],
                    "satisfaction_type": "progression_reward",
                    "delivery_method": "achievement_moment"
                })
        return points

    def _structure_anticipation_building(self, chapter_composition: list[dict[str, Any]]) -> dict[str, list[str]]:
        """期待構築を構造化"""
        return {
            "short_term_anticipation": [f"第{i+1}章展開期待" for i in range(min(3, len(chapter_composition)))],
            "medium_term_anticipation": ["中盤クライマックス期待", "主要対立解決期待"],
            "long_term_anticipation": ["物語完結期待", "キャラクター成長完成期待"]
        }
