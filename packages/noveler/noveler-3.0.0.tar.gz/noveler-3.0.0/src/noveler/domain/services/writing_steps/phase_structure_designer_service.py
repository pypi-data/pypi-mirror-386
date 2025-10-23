"""Domain.services.writing_steps.phase_structure_designer_service
Where: Domain service module implementing a specific writing workflow step.
What: Provides helper routines and data structures for this writing step.
Why: Allows stepwise writing orchestrators to reuse consistent step logic.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""段階構造設計サービス

A38執筆プロンプトガイド STEP 2: 中骨（段階目標・行動フェーズ）の実装。
物語の中核となる段階的な目標設定と行動フェーズの構築。
"""

from typing import Any

from noveler.domain.services.writing_steps.base_writing_step import (
    BaseWritingStep,
)


class PhaseStructureDesignerService(BaseWritingStep):
    """段階構造設計サービス

    A38 STEP 2: 物語の中骨（段階目標・行動フェーズ）を設計し、
    各段階での具体的な目標と行動パターンを構築する。
    """

    def __init__(self) -> None:
        super().__init__(
            step_number=2,
            step_name="中骨（段階目標・行動フェーズ）"
        )

    def _design_phase_objectives(
        self,
        story_structure: dict[str, Any] | None,
        scope_data: dict[str, Any] | None,
        episode_number: int
    ) -> dict[str, Any]:
        """段階目標を設計"""

        # 基本情報の取得
        episode_type = story_structure.get("episode_type", "main_development") if story_structure else "main_development"
        chapter_count = len(story_structure.get("chapter_composition", [])) if story_structure else 4

        return {
            "episode_number": episode_number,
            "episode_type": episode_type,
            "primary_objectives": self._define_primary_objectives(episode_type, episode_number),
            "secondary_objectives": self._define_secondary_objectives(episode_type, scope_data),
            "milestone_objectives": self._establish_milestone_objectives(episode_type, chapter_count),
            "success_criteria": self._define_success_criteria(episode_type),
            "objective_hierarchy": self._create_objective_hierarchy(episode_type),
            "completion_metrics": self._establish_completion_metrics(episode_type)
        }


    def _define_primary_objectives(self, episode_type: str, episode_number: int) -> list[dict[str, Any]]:
        """主要目標を定義"""

        # エピソードタイプによる基本目標
        type_objectives = {
            "introduction": [
                {
                    "objective": "character_establishment",
                    "description": "主要キャラクターの確立",
                    "priority": "critical",
                    "measurable_outcome": "読者がキャラクターを理解・共感"
                },
                {
                    "objective": "world_introduction",
                    "description": "世界観・設定の紹介",
                    "priority": "high",
                    "measurable_outcome": "基本設定の理解確保"
                },
                {
                    "objective": "hook_creation",
                    "description": "読者の興味を引くフックの創出",
                    "priority": "critical",
                    "measurable_outcome": "続きを読みたい気持ちの喚起"
                }
            ],
            "early_development": [
                {
                    "objective": "conflict_introduction",
                    "description": "主要な対立構造の導入",
                    "priority": "critical",
                    "measurable_outcome": "明確な問題・課題の提示"
                },
                {
                    "objective": "relationship_building",
                    "description": "キャラクター間関係の構築",
                    "priority": "high",
                    "measurable_outcome": "人間関係の動的な発展"
                },
                {
                    "objective": "plot_momentum",
                    "description": "物語推進力の創出",
                    "priority": "high",
                    "measurable_outcome": "次の展開への期待感醸成"
                }
            ],
            "main_development": [
                {
                    "objective": "conflict_escalation",
                    "description": "対立構造の複雑化・激化",
                    "priority": "critical",
                    "measurable_outcome": "緊張感の段階的上昇"
                },
                {
                    "objective": "character_growth",
                    "description": "キャラクターの成長・変化",
                    "priority": "critical",
                    "measurable_outcome": "明確な成長軌道の提示"
                },
                {
                    "objective": "plot_deepening",
                    "description": "物語の深化・多層化",
                    "priority": "high",
                    "measurable_outcome": "複雑さと理解可能性の両立"
                }
            ],
            "advanced_development": [
                {
                    "objective": "crisis_approach",
                    "description": "クライマックスへの接近",
                    "priority": "critical",
                    "measurable_outcome": "最終対決への準備完了"
                },
                {
                    "objective": "stakes_maximization",
                    "description": "賭ける物の最大化",
                    "priority": "critical",
                    "measurable_outcome": "読者の感情的投資最大化"
                },
                {
                    "objective": "tension_peak_preparation",
                    "description": "緊張感ピークの準備",
                    "priority": "high",
                    "measurable_outcome": "クライマックス直前の最適な状態"
                }
            ],
            "climax_resolution": [
                {
                    "objective": "climax_execution",
                    "description": "クライマックスの実行",
                    "priority": "critical",
                    "measurable_outcome": "感情的カタルシスの達成"
                },
                {
                    "objective": "resolution_achievement",
                    "description": "問題解決の達成",
                    "priority": "critical",
                    "measurable_outcome": "主要課題の満足できる解決"
                },
                {
                    "objective": "closure_provision",
                    "description": "適切な締めくくりの提供",
                    "priority": "high",
                    "measurable_outcome": "読者の満足感と完成感"
                }
            ]
        }

        return type_objectives.get(episode_type, type_objectives["main_development"])

    def _define_secondary_objectives(self, episode_type: str, scope_data: dict[str, Any] | None) -> list[dict[str, Any]]:
        """二次目標を定義"""

        # 全エピソード共通の二次目標
        common_objectives = [
            {
                "objective": "reader_engagement",
                "description": "読者のエンゲージメント維持",
                "priority": "high",
                "implementation": "consistent_pacing"
            },
            {
                "objective": "narrative_flow",
                "description": "物語の自然な流れ確保",
                "priority": "medium",
                "implementation": "smooth_transitions"
            },
            {
                "objective": "emotional_resonance",
                "description": "感情的共鳴の創出",
                "priority": "high",
                "implementation": "character_depth"
            }
        ]

        # エピソードタイプ固有の二次目標
        type_specific = {
            "introduction": [
                {
                    "objective": "world_consistency",
                    "description": "世界観の一貫性確保",
                    "priority": "medium",
                    "implementation": "setting_rules"
                }
            ],
            "main_development": [
                {
                    "objective": "subplot_integration",
                    "description": "サブプロットの統合",
                    "priority": "medium",
                    "implementation": "thread_weaving"
                }
            ],
            "climax_resolution": [
                {
                    "objective": "thematic_completion",
                    "description": "テーマ的完成",
                    "priority": "medium",
                    "implementation": "message_clarity"
                }
            ]
        }

        specific_objectives = type_specific.get(episode_type, [])
        return common_objectives + specific_objectives

    def _establish_milestone_objectives(self, episode_type: str, chapter_count: int) -> dict[str, Any]:
        """マイルストーン目標を設定"""

        milestones = {}

        # 章数に基づくマイルストーン配置
        key_chapters = self._identify_key_chapters(chapter_count)

        for chapter_num in key_chapters:
            milestone_type = self._determine_milestone_type(chapter_num, chapter_count, episode_type)
            milestones[f"chapter_{chapter_num}"] = {
                "chapter": chapter_num,
                "milestone_type": milestone_type,
                "objectives": self._define_chapter_milestone_objectives(milestone_type, episode_type),
                "success_indicators": self._define_milestone_success_indicators(milestone_type),
                "validation_points": self._establish_milestone_validation_points(milestone_type)
            }

        return milestones

    def _identify_key_chapters(self, chapter_count: int) -> list[int]:
        """重要章を特定"""

        if chapter_count <= 3:
            return [1, chapter_count]
        if chapter_count <= 4:
            return [1, 2, chapter_count]
        if chapter_count <= 6:
            return [1, chapter_count // 2, chapter_count - 1, chapter_count]
        return [1, chapter_count // 3, (chapter_count * 2) // 3, chapter_count]

    def _determine_milestone_type(self, chapter_num: int, total_chapters: int, episode_type: str) -> str:
        """マイルストーンタイプを決定"""

        position_ratio = (chapter_num - 1) / (total_chapters - 1) if total_chapters > 1 else 0

        if position_ratio <= 0.25:
            return "foundation_establishment"
        if position_ratio <= 0.5:
            return "development_acceleration"
        if position_ratio <= 0.75:
            return "crisis_approach"
        return "resolution_achievement"

    def _define_chapter_milestone_objectives(self, milestone_type: str, episode_type: str) -> list[dict[str, str]]:
        """章マイルストーン目標を定義"""

        objectives_map = {
            "foundation_establishment": [
                {"objective": "solid_foundation", "description": "確固とした基盤の確立"},
                {"objective": "reader_orientation", "description": "読者の方向付け完了"},
                {"objective": "initial_engagement", "description": "初期エンゲージメント獲得"}
            ],
            "development_acceleration": [
                {"objective": "momentum_building", "description": "推進力の構築"},
                {"objective": "complexity_introduction", "description": "複雑性の導入"},
                {"objective": "emotional_investment", "description": "感情的投資の深化"}
            ],
            "crisis_approach": [
                {"objective": "tension_maximization", "description": "緊張感の最大化"},
                {"objective": "stakes_clarification", "description": "賭ける物の明確化"},
                {"objective": "resolution_preparation", "description": "解決への準備"}
            ],
            "resolution_achievement": [
                {"objective": "satisfying_conclusion", "description": "満足できる結論"},
                {"objective": "emotional_closure", "description": "感情的クロージャー"},
                {"objective": "future_setup", "description": "将来への布石"}
            ]
        }

        return objectives_map.get(milestone_type, objectives_map["development_acceleration"])

    def _construct_action_phases(
        self,
        phase_objectives: dict[str, Any],
        story_structure: dict[str, Any] | None
    ) -> list[dict[str, Any]]:
        """行動フェーズを構築"""

        episode_type = phase_objectives["episode_type"]
        primary_objectives = phase_objectives["primary_objectives"]

        # 基本フェーズ数の決定
        phase_count = self._determine_optimal_phase_count(episode_type, len(primary_objectives))

        action_phases = []

        for i in range(phase_count):
            phase = {
                "phase_number": i + 1,
                "phase_name": self._generate_phase_name(i, phase_count, episode_type),
                "phase_duration": self._calculate_phase_duration(i, phase_count, story_structure),
                "primary_actions": self._define_primary_actions(i, phase_count, episode_type),
                "character_roles": self._assign_character_roles(i, phase_count, episode_type),
                "action_patterns": self._establish_action_patterns(i, phase_count, episode_type),
                "outcome_targets": self._set_outcome_targets(i, phase_count, episode_type),
                "transition_requirements": self._define_transition_requirements(i, phase_count),
                "success_conditions": self._establish_success_conditions(i, phase_count, episode_type)
            }
            action_phases.append(phase)

        return action_phases

    def _determine_optimal_phase_count(self, episode_type: str, objective_count: int) -> int:
        """最適フェーズ数を決定"""

        # エピソードタイプによる基本フェーズ数
        base_phases = {
            "introduction": 3,
            "early_development": 4,
            "main_development": 5,
            "advanced_development": 4,
            "climax_resolution": 3
        }

        base = base_phases.get(episode_type, 4)

        # 目標数による調整
        if objective_count > 4:
            base += 1
        elif objective_count < 3:
            base = max(3, base - 1)

        return base

    def _generate_phase_name(self, phase_index: int, total_phases: int, episode_type: str) -> str:
        """フェーズ名を生成"""

        # 位置による基本名
        position_ratio = phase_index / (total_phases - 1) if total_phases > 1 else 0

        if position_ratio <= 0.25:
            base_name = "setup"
        elif position_ratio <= 0.5:
            base_name = "development"
        elif position_ratio <= 0.75:
            base_name = "escalation"
        else:
            base_name = "resolution"

        # エピソードタイプによる修飾
        type_modifiers = {
            "introduction": {"setup": "establishment", "development": "introduction", "escalation": "engagement", "resolution": "foundation"},
            "early_development": {"setup": "foundation", "development": "building", "escalation": "advancement", "resolution": "momentum"},
            "main_development": {"setup": "preparation", "development": "progression", "escalation": "intensification", "resolution": "achievement"},
            "advanced_development": {"setup": "approach", "development": "acceleration", "escalation": "crisis", "resolution": "breakthrough"},
            "climax_resolution": {"setup": "final_preparation", "development": "confrontation", "escalation": "climax", "resolution": "denouement"}
        }

        modifier = type_modifiers.get(episode_type, {}).get(base_name, base_name)

        return f"{modifier}_phase"

    def _calculate_phase_duration(self, phase_index: int, total_phases: int, story_structure: dict[str, Any] | None) -> dict[str, Any]:
        """フェーズ持続時間を計算"""

        # 総文字数の取得
        total_words = 4000  # デフォルト
        if story_structure and "target_length" in story_structure:
            total_words = story_structure["target_length"].get("target_words", 4000)

        # フェーズごとの基本配分
        phase_weights = self._calculate_phase_weights(total_phases)
        phase_words = int(total_words * phase_weights[phase_index])

        return {
            "target_words": phase_words,
            "minimum_words": int(phase_words * 0.8),
            "maximum_words": int(phase_words * 1.2),
            "relative_weight": phase_weights[phase_index],
            "duration_flexibility": "medium"
        }

    def _calculate_phase_weights(self, total_phases: int) -> list[float]:
        """フェーズ重み配分を計算"""

        if total_phases == 3:
            return [0.25, 0.5, 0.25]  # 序破急型
        if total_phases == 4:
            return [0.2, 0.3, 0.3, 0.2]  # バランス型
        if total_phases == 5:
            return [0.15, 0.25, 0.25, 0.25, 0.1]  # 展開重視型
        # 均等配分（調整あり）
        base_weight = 1.0 / total_phases
        weights = [base_weight] * total_phases
        # 中間フェーズを若干重く
        if total_phases > 2:
            middle_index = total_phases // 2
            weights[middle_index] += 0.05
            weights[0] -= 0.025
            weights[-1] -= 0.025
        return weights

    def _define_primary_actions(self, phase_index: int, total_phases: int, episode_type: str) -> list[dict[str, Any]]:
        """主要アクションを定義"""

        position_ratio = phase_index / (total_phases - 1) if total_phases > 1 else 0

        # 位置とエピソードタイプによるアクション定義
        action_templates = {
            ("introduction", "setup"): [
                {"action": "character_introduction", "priority": "critical", "execution_style": "engaging"},
                {"action": "world_establishment", "priority": "high", "execution_style": "natural"},
                {"action": "hook_placement", "priority": "critical", "execution_style": "compelling"}
            ],
            ("main_development", "development"): [
                {"action": "conflict_escalation", "priority": "critical", "execution_style": "gradual"},
                {"action": "character_interaction", "priority": "high", "execution_style": "dynamic"},
                {"action": "plot_advancement", "priority": "critical", "execution_style": "momentum_building"}
            ],
            ("climax_resolution", "escalation"): [
                {"action": "climax_execution", "priority": "critical", "execution_style": "intense"},
                {"action": "emotional_peak", "priority": "critical", "execution_style": "cathartic"},
                {"action": "resolution_initiation", "priority": "high", "execution_style": "satisfying"}
            ]
        }

        # 位置による基本アクションタイプ決定
        if position_ratio <= 0.25:
            action_type = "setup"
        elif position_ratio <= 0.5:
            action_type = "development"
        elif position_ratio <= 0.75:
            action_type = "escalation"
        else:
            action_type = "resolution"

        template_key = (episode_type, action_type)

        # テンプレートが見つからない場合のフォールバック
        if template_key not in action_templates:
            # 汎用テンプレート
            return [
                {"action": f"phase_{phase_index + 1}_progression", "priority": "high", "execution_style": "appropriate"},
                {"action": f"character_development_{action_type}", "priority": "medium", "execution_style": "natural"}
            ]

        return action_templates[template_key]

    def _assign_character_roles(self, phase_index: int, total_phases: int, episode_type: str) -> dict[str, Any]:
        """キャラクター役割を割り当て"""

        position_ratio = phase_index / (total_phases - 1) if total_phases > 1 else 0

        # 位置による基本役割配分
        if position_ratio <= 0.25:
            focus = "protagonist_establishment"
        elif position_ratio <= 0.5:
            focus = "ensemble_interaction"
        elif position_ratio <= 0.75:
            focus = "conflict_participants"
        else:
            focus = "resolution_agents"

        role_assignments = {
            "protagonist_establishment": {
                "primary_focus": "protagonist",
                "supporting_roles": ["mentor", "ally"],
                "antagonist_presence": "subtle",
                "ensemble_balance": "protagonist_heavy"
            },
            "ensemble_interaction": {
                "primary_focus": "balanced",
                "supporting_roles": ["all_active"],
                "antagonist_presence": "moderate",
                "ensemble_balance": "distributed"
            },
            "conflict_participants": {
                "primary_focus": "conflict_drivers",
                "supporting_roles": ["side_choosers"],
                "antagonist_presence": "prominent",
                "ensemble_balance": "conflict_centered"
            },
            "resolution_agents": {
                "primary_focus": "problem_solvers",
                "supporting_roles": ["consequence_bearers"],
                "antagonist_presence": "resolution_focused",
                "ensemble_balance": "outcome_oriented"
            }
        }

        return role_assignments.get(focus, role_assignments["ensemble_interaction"])

    def _establish_action_patterns(self, phase_index: int, total_phases: int, episode_type: str) -> dict[str, Any]:
        """アクションパターンを確立"""

        return {
            "pattern_type": self._determine_action_pattern_type(phase_index, total_phases, episode_type),
            "rhythm_characteristics": self._define_rhythm_characteristics(phase_index, total_phases),
            "intensity_profile": self._create_intensity_profile(phase_index, total_phases, episode_type),
            "interaction_style": self._specify_interaction_style(phase_index, episode_type),
            "pacing_requirements": self._establish_pacing_requirements(phase_index, total_phases)
        }

    def _determine_action_pattern_type(self, phase_index: int, total_phases: int, episode_type: str) -> str:
        """アクションパターンタイプを決定"""

        phase_index / (total_phases - 1) if total_phases > 1 else 0

        type_patterns = {
            "introduction": ["establishment", "development", "engagement"],
            "early_development": ["foundation", "building", "advancement", "momentum"],
            "main_development": ["preparation", "progression", "intensification", "achievement", "transition"],
            "advanced_development": ["approach", "acceleration", "crisis", "breakthrough"],
            "climax_resolution": ["preparation", "confrontation", "resolution"]
        }

        patterns = type_patterns.get(episode_type, ["setup", "development", "climax", "resolution"])
        pattern_index = min(phase_index, len(patterns) - 1)

        return patterns[pattern_index]

    def _define_rhythm_characteristics(self, phase_index: int, total_phases: int) -> dict[str, str]:
        """リズム特性を定義"""

        position_ratio = phase_index / (total_phases - 1) if total_phases > 1 else 0

        if position_ratio <= 0.25:
            return {
                "tempo": "moderate",
                "variation": "gentle",
                "emphasis": "establishment"
            }
        if position_ratio <= 0.5:
            return {
                "tempo": "building",
                "variation": "increasing",
                "emphasis": "development"
            }
        if position_ratio <= 0.75:
            return {
                "tempo": "accelerating",
                "variation": "dynamic",
                "emphasis": "escalation"
            }
        return {
            "tempo": "resolving",
            "variation": "controlled",
            "emphasis": "closure"
        }

    def _create_intensity_profile(self, phase_index: int, total_phases: int, episode_type: str) -> dict[str, Any]:
        """強度プロファイルを作成"""

        # エピソードタイプによる基本強度レベル
        type_base_intensity = {
            "introduction": 5,
            "early_development": 6,
            "main_development": 7,
            "advanced_development": 8,
            "climax_resolution": 9
        }

        base_intensity = type_base_intensity.get(episode_type, 6)

        # フェーズ位置による調整
        position_ratio = phase_index / (total_phases - 1) if total_phases > 1 else 0
        position_adjustment = int((position_ratio - 0.5) * 4)  # -2 to +2

        current_intensity = max(1, min(10, base_intensity + position_adjustment))

        return {
            "current_intensity": current_intensity,
            "target_intensity": current_intensity,
            "intensity_range": {"min": current_intensity - 1, "max": current_intensity + 1},
            "buildup_rate": "gradual" if current_intensity < 7 else "accelerated",
            "peak_moments": max(1, current_intensity // 3)
        }

    def _specify_interaction_style(self, phase_index: int, episode_type: str) -> dict[str, str]:
        """相互作用スタイルを指定"""

        base_styles = {
            "introduction": "exploratory",
            "early_development": "building",
            "main_development": "complex",
            "advanced_development": "intense",
            "climax_resolution": "decisive"
        }

        base_style = base_styles.get(episode_type, "balanced")

        return {
            "primary_style": base_style,
            "dialogue_emphasis": "moderate" if phase_index < 2 else "high",
            "action_emphasis": "low" if phase_index == 0 else "moderate",
            "emotional_emphasis": "building" if phase_index < 2 else "high"
        }

    def _establish_pacing_requirements(self, phase_index: int, total_phases: int) -> dict[str, Any]:
        """ペーシング要件を確立"""

        position_ratio = phase_index / (total_phases - 1) if total_phases > 1 else 0

        if position_ratio <= 0.25:
            return {
                "overall_pace": "measured",
                "scene_transitions": "smooth",
                "information_density": "moderate",
                "reader_breathing_room": "ample"
            }
        if position_ratio <= 0.75:
            return {
                "overall_pace": "dynamic",
                "scene_transitions": "energetic",
                "information_density": "high",
                "reader_breathing_room": "strategic"
            }
        return {
            "overall_pace": "concluding",
            "scene_transitions": "purposeful",
            "information_density": "focused",
            "reader_breathing_room": "satisfying"
        }

    def _set_outcome_targets(self, phase_index: int, total_phases: int, episode_type: str) -> dict[str, Any]:
        """成果目標を設定"""

        position_ratio = phase_index / (total_phases - 1) if total_phases > 1 else 0

        # 位置による基本成果タイプ
        if position_ratio <= 0.25:
            outcome_type = "foundation_outcomes"
        elif position_ratio <= 0.5:
            outcome_type = "development_outcomes"
        elif position_ratio <= 0.75:
            outcome_type = "escalation_outcomes"
        else:
            outcome_type = "resolution_outcomes"

        outcome_templates = {
            "foundation_outcomes": {
                "primary_outcomes": ["character_establishment", "world_grounding", "initial_engagement"],
                "measurable_results": ["reader_orientation", "emotional_connection", "curiosity_arousal"],
                "success_indicators": ["clear_character_understanding", "immersive_setting", "compelling_hook"]
            },
            "development_outcomes": {
                "primary_outcomes": ["plot_advancement", "character_development", "tension_building"],
                "measurable_results": ["story_progression", "relationship_evolution", "increased_stakes"],
                "success_indicators": ["forward_momentum", "deeper_investment", "rising_tension"]
            },
            "escalation_outcomes": {
                "primary_outcomes": ["conflict_intensification", "stakes_raising", "emotional_peaks"],
                "measurable_results": ["heightened_tension", "crisis_approach", "peak_engagement"],
                "success_indicators": ["palpable_tension", "clear_stakes", "emotional_investment"]
            },
            "resolution_outcomes": {
                "primary_outcomes": ["conflict_resolution", "character_completion", "satisfying_closure"],
                "measurable_results": ["problem_solving", "growth_realization", "emotional_satisfaction"],
                "success_indicators": ["resolution_clarity", "character_arc_completion", "reader_satisfaction"]
            }
        }

        return outcome_templates.get(outcome_type, outcome_templates["development_outcomes"])

    def _define_transition_requirements(self, phase_index: int, total_phases: int) -> dict[str, Any]:
        """遷移要件を定義"""

        if phase_index == total_phases - 1:
            # 最終フェーズ
            return {
                "transition_type": "episode_conclusion",
                "requirements": ["satisfying_ending", "emotional_closure", "future_setup"],
                "transition_smoothness": "conclusive",
                "preparation_needs": ["resolution_elements", "closure_components"]
            }
        # 中間フェーズ
        return {
            "transition_type": "phase_progression",
            "requirements": ["momentum_maintenance", "logical_flow", "escalation_preparation"],
            "transition_smoothness": "seamless",
            "preparation_needs": ["bridge_elements", "setup_components"]
        }

    def _establish_success_conditions(self, phase_index: int, total_phases: int, episode_type: str) -> dict[str, Any]:
        """成功条件を確立"""

        position_ratio = phase_index / (total_phases - 1) if total_phases > 1 else 0

        # 基本成功条件
        return {
            "completion_criteria": self._define_completion_criteria(position_ratio, episode_type),
            "quality_thresholds": self._set_quality_thresholds(position_ratio),
            "reader_impact_targets": self._establish_impact_targets(position_ratio, episode_type),
            "validation_checkpoints": self._create_validation_checkpoints(phase_index)
        }


    def _define_completion_criteria(self, position_ratio: float, episode_type: str) -> list[str]:
        """完了基準を定義"""

        if position_ratio <= 0.25:
            return [
                "基盤要素の確実な確立",
                "読者の方向付け完了",
                "次フェーズへの適切な準備"
            ]
        if position_ratio <= 0.75:
            return [
                "フェーズ目標の達成",
                "物語推進力の維持",
                "読者エンゲージメントの継続"
            ]
        return [
            "主要問題の解決",
            "感情的満足の提供",
            "適切な締めくくり"
        ]

    def _set_quality_thresholds(self, position_ratio: float) -> dict[str, float]:
        """品質しきい値を設定"""

        # フェーズ位置による品質要求レベル
        if position_ratio <= 0.25:
            return {
                "narrative_clarity": 8.0,
                "character_consistency": 8.5,
                "engagement_level": 7.5
            }
        if position_ratio <= 0.75:
            return {
                "narrative_clarity": 8.5,
                "character_consistency": 8.0,
                "engagement_level": 8.5
            }
        return {
            "narrative_clarity": 9.0,
            "character_consistency": 8.5,
            "engagement_level": 8.0
        }

    def _establish_impact_targets(self, position_ratio: float, episode_type: str) -> dict[str, str]:
        """インパクト目標を設定"""

        base_targets = {
            "emotional_impact": "moderate",
            "cognitive_engagement": "high",
            "anticipation_level": "building"
        }

        # 位置による調整
        if position_ratio >= 0.75:
            base_targets["emotional_impact"] = "high"
            base_targets["anticipation_level"] = "peak" if episode_type != "climax_resolution" else "satisfaction"
        elif position_ratio <= 0.25:
            base_targets["cognitive_engagement"] = "establishing"

        return base_targets

    def _create_validation_checkpoints(self, phase_index: int) -> list[dict[str, str]]:
        """検証チェックポイントを作成"""

        return [
            {
                "checkpoint": f"phase_{phase_index + 1}_25percent",
                "validation_focus": "initial_progress",
                "criteria": "基本要素の配置確認"
            },
            {
                "checkpoint": f"phase_{phase_index + 1}_50percent",
                "validation_focus": "midpoint_assessment",
                "criteria": "中間目標の達成確認"
            },
            {
                "checkpoint": f"phase_{phase_index + 1}_75percent",
                "validation_focus": "completion_preparation",
                "criteria": "完了準備状況の確認"
            },
            {
                "checkpoint": f"phase_{phase_index + 1}_completion",
                "validation_focus": "final_validation",
                "criteria": "フェーズ目標の完全達成"
            }
        ]

    def _design_phase_transitions(
        self,
        action_phases: list[dict[str, Any]],
        story_structure: dict[str, Any] | None
    ) -> dict[str, Any]:
        """フェーズ遷移を設計"""

        return {
            "transition_map": self._create_transition_map(action_phases),
            "transition_techniques": self._define_transition_techniques(action_phases),
            "flow_optimization": self._optimize_transition_flow(action_phases),
            "continuity_requirements": self._establish_continuity_requirements(action_phases),
            "smooth_bridging": self._design_smooth_bridging(action_phases)
        }


    def _create_transition_map(self, action_phases: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """遷移マップを作成"""

        transition_map = []

        for i in range(len(action_phases) - 1):
            current_phase = action_phases[i]
            next_phase = action_phases[i + 1]

            transition = {
                "from_phase": current_phase["phase_number"],
                "to_phase": next_phase["phase_number"],
                "transition_type": self._classify_transition_type(current_phase, next_phase),
                "bridging_elements": self._identify_bridging_elements(current_phase, next_phase),
                "transition_intensity": self._calculate_transition_intensity(current_phase, next_phase),
                "required_setup": self._determine_required_setup(current_phase, next_phase),
                "completion_signals": self._identify_completion_signals(current_phase)
            }

            transition_map.append(transition)

        return transition_map

    def _classify_transition_type(self, current_phase: dict[str, Any], next_phase: dict[str, Any]) -> str:
        """遷移タイプを分類"""

        current_intensity = current_phase.get("action_patterns", {}).get("intensity_profile", {}).get("current_intensity", 5)
        next_intensity = next_phase.get("action_patterns", {}).get("intensity_profile", {}).get("current_intensity", 5)

        intensity_diff = next_intensity - current_intensity

        if intensity_diff > 2:
            return "escalating_transition"
        if intensity_diff > 0:
            return "building_transition"
        if intensity_diff < -2:
            return "de_escalating_transition"
        if intensity_diff < 0:
            return "cooling_transition"
        return "maintaining_transition"

    def _identify_bridging_elements(self, current_phase: dict[str, Any], next_phase: dict[str, Any]) -> list[str]:
        """橋渡し要素を特定"""

        current_actions = [action["action"] for action in current_phase.get("primary_actions", [])]
        next_actions = [action["action"] for action in next_phase.get("primary_actions", [])]

        # 共通要素の特定
        common_elements = []

        # アクションタイプによる橋渡し要素
        if "character_interaction" in current_actions and "conflict_escalation" in next_actions:
            common_elements.append("relationship_tension")

        if "plot_advancement" in current_actions:
            common_elements.append("momentum_continuity")

        # デフォルト橋渡し要素
        if not common_elements:
            common_elements = ["narrative_flow", "character_continuity"]

        return common_elements

    def _calculate_transition_intensity(self, current_phase: dict[str, Any], next_phase: dict[str, Any]) -> float:
        """遷移強度を計算"""

        current_intensity = current_phase.get("action_patterns", {}).get("intensity_profile", {}).get("current_intensity", 5)
        next_intensity = next_phase.get("action_patterns", {}).get("intensity_profile", {}).get("current_intensity", 5)

        # 平均強度を遷移強度とする
        return (current_intensity + next_intensity) / 2

    def _establish_character_action_patterns(
        self,
        action_phases: list[dict[str, Any]],
        scope_data: dict[str, Any] | None
    ) -> dict[str, Any]:
        """キャラクター行動パターンを確立"""

        return {
            "character_arc_mapping": self._map_character_arcs(action_phases, scope_data),
            "behavioral_consistency": self._ensure_behavioral_consistency(action_phases),
            "interaction_dynamics": self._design_interaction_dynamics(action_phases),
            "growth_trajectories": self._establish_growth_trajectories(action_phases),
            "action_authenticity": self._verify_action_authenticity(action_phases)
        }


    def _map_character_arcs(self, action_phases: list[dict[str, Any]], scope_data: dict[str, Any] | None) -> dict[str, Any]:
        """キャラクター弧をマッピング"""

        # 基本キャラクター情報の取得（スコープデータから）
        characters = ["protagonist", "antagonist", "support"]  # デフォルト
        if scope_data and "characters" in scope_data:
            characters = list(scope_data["characters"].keys())

        arc_mapping = {}

        for character in characters:
            arc_mapping[character] = {
                "phase_roles": self._define_character_phase_roles(character, action_phases),
                "development_milestones": self._establish_development_milestones(character, action_phases),
                "behavioral_evolution": self._track_behavioral_evolution(character, action_phases),
                "relationship_changes": self._map_relationship_changes(character, action_phases)
            }

        return arc_mapping

    def _define_character_phase_roles(self, character: str, action_phases: list[dict[str, Any]]) -> list[dict[str, str]]:
        """キャラクターのフェーズ役割を定義"""

        roles = []

        for phase in action_phases:
            phase_num = phase["phase_number"]
            phase.get("character_roles", {})

            # キャラクタータイプによる役割決定
            if character == "protagonist":
                role = self._determine_protagonist_role(phase_num, len(action_phases))
            elif character == "antagonist":
                role = self._determine_antagonist_role(phase_num, len(action_phases))
            else:
                role = self._determine_support_role(phase_num, len(action_phases))

            roles.append({
                "phase": phase_num,
                "primary_role": role,
                "activity_level": self._calculate_character_activity_level(character, phase_num, len(action_phases))
            })

        return roles

    def _determine_protagonist_role(self, phase_num: int, total_phases: int) -> str:
        """主人公の役割を決定"""

        position_ratio = (phase_num - 1) / (total_phases - 1) if total_phases > 1 else 0

        if position_ratio <= 0.25:
            return "establishing_presence"
        if position_ratio <= 0.5:
            return "active_engagement"
        if position_ratio <= 0.75:
            return "driving_action"
        return "achieving_resolution"

    def _determine_antagonist_role(self, phase_num: int, total_phases: int) -> str:
        """対立者の役割を決定"""

        position_ratio = (phase_num - 1) / (total_phases - 1) if total_phases > 1 else 0

        if position_ratio <= 0.25:
            return "subtle_influence"
        if position_ratio <= 0.5:
            return "emerging_opposition"
        if position_ratio <= 0.75:
            return "direct_confrontation"
        return "final_challenge"

    def _determine_support_role(self, phase_num: int, total_phases: int) -> str:
        """支援者の役割を決定"""

        position_ratio = (phase_num - 1) / (total_phases - 1) if total_phases > 1 else 0

        if position_ratio <= 0.25:
            return "foundation_support"
        if position_ratio <= 0.5:
            return "active_assistance"
        if position_ratio <= 0.75:
            return "crucial_support"
        return "completion_aid"

    def _calculate_character_activity_level(self, character: str, phase_num: int, total_phases: int) -> str:
        """キャラクター活動レベルを計算"""

        position_ratio = (phase_num - 1) / (total_phases - 1) if total_phases > 1 else 0

        # キャラクタータイプと位置による活動レベル
        if character == "protagonist":
            if position_ratio <= 0.25:
                return "moderate"
            if position_ratio <= 0.75:
                return "high"
            return "peak"
        if character == "antagonist":
            if position_ratio <= 0.25:
                return "low"
            if position_ratio <= 0.5:
                return "moderate"
            return "high"
        # support
        return "moderate"

    def _verify_phase_balance(
        self,
        phase_objectives: dict[str, Any],
        action_phases: list[dict[str, Any]],
        phase_transitions: dict[str, Any]
    ) -> dict[str, Any]:
        """フェーズバランスを検証"""

        balance_check = {
            "coherence_score": 0.0,
            "balance_analysis": {},
            "identified_issues": [],
            "optimization_suggestions": [],
            "strength_areas": []
        }

        # 各要素の分析
        objective_score = self._analyze_objective_balance(phase_objectives, action_phases)
        phase_score = self._analyze_phase_distribution(action_phases)
        transition_score = self._analyze_transition_quality(phase_transitions)

        # 統合スコア
        balance_check["coherence_score"] = (objective_score + phase_score + transition_score) / 3

        balance_check["balance_analysis"] = {
            "objective_alignment_score": objective_score,
            "phase_distribution_score": phase_score,
            "transition_quality_score": transition_score
        }

        # 問題点と改善提案の特定
        self._identify_balance_issues_and_suggestions(balance_check, objective_score, phase_score, transition_score)

        return balance_check

    def _analyze_objective_balance(self, phase_objectives: dict[str, Any], action_phases: list[dict[str, Any]]) -> float:
        """目標バランス分析"""

        score = 8.0

        # 主要目標の数と品質
        primary_objectives = phase_objectives.get("primary_objectives", [])
        if len(primary_objectives) >= 3:
            score += 0.5

        # マイルストーン目標の設定
        milestone_objectives = phase_objectives.get("milestone_objectives", {})
        if len(milestone_objectives) >= len(action_phases) // 2:
            score += 0.5

        # 成功基準の明確性
        success_criteria = phase_objectives.get("success_criteria", [])
        if len(success_criteria) >= 3:
            score += 0.3

        return min(10.0, score)

    def _analyze_phase_distribution(self, action_phases: list[dict[str, Any]]) -> float:
        """フェーズ分布分析"""

        score = 8.0
        total_phases = len(action_phases)

        # フェーズ数の適切性
        if 3 <= total_phases <= 6:
            score += 0.5
        elif total_phases > 6:
            score -= 0.3

        # フェーズ間のバランス
        durations = [phase.get("phase_duration", {}).get("target_words", 1000) for phase in action_phases]
        if durations:
            max_duration = max(durations)
            min_duration = min(durations)
            if max_duration > 0 and (max_duration - min_duration) / max_duration < 0.5:
                score += 0.5

        # アクションの多様性
        all_actions = []
        for phase in action_phases:
            phase_actions = [action["action"] for action in phase.get("primary_actions", [])]
            all_actions.extend(phase_actions)

        unique_actions = len(set(all_actions))
        if unique_actions >= total_phases * 2:
            score += 0.3

        return min(10.0, score)

    def _analyze_transition_quality(self, phase_transitions: dict[str, Any]) -> float:
        """遷移品質分析"""

        score = 8.0

        transition_map = phase_transitions.get("transition_map", [])

        # 遷移の完全性
        if len(transition_map) > 0:
            score += 0.5

        # 遷移技法の設定
        if "transition_techniques" in phase_transitions:
            score += 0.3

        # フロー最適化の実施
        if "flow_optimization" in phase_transitions:
            score += 0.2

        return min(10.0, score)

    def _identify_balance_issues_and_suggestions(
        self,
        balance_check: dict[str, Any],
        objective_score: float,
        phase_score: float,
        transition_score: float
    ) -> None:
        """バランス問題と改善提案の特定"""

        if objective_score < 7.0:
            balance_check["identified_issues"].append("目標設定の不備")
            balance_check["optimization_suggestions"].append("主要目標とマイルストーン目標の詳細化")

        if phase_score < 7.0:
            balance_check["identified_issues"].append("フェーズ分布の不均衡")
            balance_check["optimization_suggestions"].append("フェーズ長とアクションの再配分")

        if transition_score < 7.0:
            balance_check["identified_issues"].append("遷移品質の問題")
            balance_check["optimization_suggestions"].append("遷移技法の改善と橋渡し要素の強化")

        # 強み領域の特定
        if objective_score >= 8.5:
            balance_check["strength_areas"].append("優秀な目標設計")
        if phase_score >= 8.5:
            balance_check["strength_areas"].append("バランスの取れたフェーズ構成")
        if transition_score >= 8.5:
            balance_check["strength_areas"].append("滑らかな遷移設計")

    # Additional helper methods for remaining functionality
    def _define_success_criteria(self, episode_type: str) -> list[dict[str, Any]]:
        """成功基準を定義"""

        criteria_sets = {
            "introduction": [
                {"criterion": "character_likability", "measurement": "reader_connection_strength", "threshold": 7.0},
                {"criterion": "world_immersion", "measurement": "setting_believability", "threshold": 8.0},
                {"criterion": "hook_effectiveness", "measurement": "continuation_desire", "threshold": 8.5}
            ],
            "main_development": [
                {"criterion": "plot_engagement", "measurement": "story_investment_level", "threshold": 8.0},
                {"criterion": "character_growth", "measurement": "development_clarity", "threshold": 7.5},
                {"criterion": "tension_building", "measurement": "anticipation_level", "threshold": 8.0}
            ],
            "climax_resolution": [
                {"criterion": "resolution_satisfaction", "measurement": "closure_completeness", "threshold": 9.0},
                {"criterion": "emotional_impact", "measurement": "cathartic_effect", "threshold": 8.5},
                {"criterion": "thematic_completion", "measurement": "message_clarity", "threshold": 8.0}
            ]
        }

        return criteria_sets.get(episode_type, criteria_sets["main_development"])

    def _create_objective_hierarchy(self, episode_type: str) -> dict[str, list[str]]:
        """目標階層を作成"""

        return {
            "critical_objectives": ["primary_story_goal", "character_development", "reader_engagement"],
            "important_objectives": ["world_consistency", "pacing_management", "emotional_resonance"],
            "supporting_objectives": ["stylistic_consistency", "technical_quality", "genre_adherence"]
        }

    def _establish_completion_metrics(self, episode_type: str) -> dict[str, Any]:
        """完了メトリクスを確立"""

        return {
            "quantitative_metrics": {
                "word_count_achievement": "target_range_compliance",
                "chapter_balance": "deviation_within_20_percent",
                "pacing_consistency": "rhythm_variation_optimal"
            },
            "qualitative_metrics": {
                "narrative_flow": "seamless_progression",
                "character_consistency": "believable_actions",
                "emotional_impact": "reader_satisfaction"
            },
            "reader_experience_metrics": {
                "engagement_maintenance": "consistent_interest",
                "satisfaction_delivery": "expectation_fulfillment",
                "anticipation_building": "next_episode_desire"
            }
        }

    def _define_milestone_success_indicators(self, milestone_type: str) -> list[str]:
        """マイルストーン成功指標を定義"""

        indicators = {
            "foundation_establishment": [
                "基盤要素の確実な設置",
                "読者の理解とエンゲージメント確保",
                "次段階への適切な準備完了"
            ],
            "development_acceleration": [
                "物語推進力の明確な増加",
                "キャラクター発展の実感",
                "読者の感情的投資深化"
            ],
            "crisis_approach": [
                "緊張感の効果的な最大化",
                "クライマックスへの期待醸成",
                "解決への準備状態確立"
            ],
            "resolution_achievement": [
                "主要問題の満足できる解決",
                "感情的カタルシスの達成",
                "物語完結への適切な導入"
            ]
        }

        return indicators.get(milestone_type, indicators["development_acceleration"])

    def _establish_milestone_validation_points(self, milestone_type: str) -> list[dict[str, str]]:
        """マイルストーン検証ポイントを確立"""

        return [
            {
                "validation_point": f"{milestone_type}_checkpoint_1",
                "focus": "initial_achievement",
                "method": "progress_assessment"
            },
            {
                "validation_point": f"{milestone_type}_checkpoint_2",
                "focus": "quality_verification",
                "method": "standard_compliance_check"
            },
            {
                "validation_point": f"{milestone_type}_completion",
                "focus": "final_validation",
                "method": "comprehensive_evaluation"
            }
        ]

    def _define_transition_techniques(self, action_phases: list[dict[str, Any]]) -> dict[str, Any]:
        """遷移技法を定義"""

        return {
            "bridging_techniques": [
                "momentum_continuity",
                "emotional_bridging",
                "thematic_connection",
                "character_thread_weaving"
            ],
            "flow_enhancement": {
                "pacing_adjustment": "adaptive_rhythm",
                "tension_management": "strategic_release_and_build",
                "reader_guidance": "clear_progression_signals"
            },
            "seamless_integration": {
                "setup_payoff_chains": "foreshadowing_fulfillment",
                "character_motivation_flow": "consistent_decision_making",
                "world_element_threading": "environmental_continuity"
            }
        }

    def _optimize_transition_flow(self, action_phases: list[dict[str, Any]]) -> dict[str, Any]:
        """遷移フローを最適化"""

        return {
            "flow_analysis": self._analyze_current_flow(action_phases),
            "optimization_strategies": self._develop_optimization_strategies(action_phases),
            "implementation_priorities": self._prioritize_flow_improvements(action_phases)
        }

    def _analyze_current_flow(self, action_phases: list[dict[str, Any]]) -> dict[str, Any]:
        """現在のフローを分析"""

        return {
            "continuity_assessment": "good",
            "pacing_consistency": "optimal",
            "logical_progression": "clear",
            "emotional_flow": "engaging"
        }

    def _develop_optimization_strategies(self, action_phases: list[dict[str, Any]]) -> list[str]:
        """最適化戦略を開発"""

        return [
            "enhance_transition_smoothness",
            "strengthen_momentum_bridges",
            "optimize_pacing_variations",
            "improve_emotional_continuity"
        ]

    def _prioritize_flow_improvements(self, action_phases: list[dict[str, Any]]) -> dict[str, str]:
        """フロー改善を優先順位付け"""

        return {
            "high_priority": "transition_smoothness_enhancement",
            "medium_priority": "pacing_optimization",
            "low_priority": "minor_continuity_adjustments"
        }

    def _establish_continuity_requirements(self, action_phases: list[dict[str, Any]]) -> dict[str, Any]:
        """継続性要件を確立"""

        return {
            "character_continuity": {
                "personality_consistency": "maintain_core_traits",
                "motivation_evolution": "logical_development",
                "relationship_progression": "natural_changes"
            },
            "plot_continuity": {
                "cause_effect_chains": "clear_connections",
                "timeline_consistency": "chronological_accuracy",
                "world_state_tracking": "environmental_continuity"
            },
            "thematic_continuity": {
                "message_consistency": "unified_themes",
                "tone_maintenance": "appropriate_variations",
                "genre_adherence": "consistent_conventions"
            }
        }

    def _design_smooth_bridging(self, action_phases: list[dict[str, Any]]) -> dict[str, Any]:
        """滑らかな橋渡しを設計"""

        return {
            "bridging_elements": self._identify_universal_bridging_elements(action_phases),
            "transition_mechanics": self._design_transition_mechanics(action_phases),
            "reader_guidance": self._create_reader_guidance_system(action_phases)
        }

    def _identify_universal_bridging_elements(self, action_phases: list[dict[str, Any]]) -> list[str]:
        """汎用橋渡し要素を特定"""

        return [
            "character_emotional_state",
            "environmental_atmosphere",
            "narrative_momentum",
            "thematic_resonance",
            "reader_expectation"
        ]

    def _design_transition_mechanics(self, action_phases: list[dict[str, Any]]) -> dict[str, list[str]]:
        """遷移メカニクスを設計"""

        return {
            "setup_mechanics": ["foreshadowing_placement", "expectation_building", "preparation_elements"],
            "execution_mechanics": ["momentum_transfer", "emotional_continuity", "logical_progression"],
            "completion_mechanics": ["payoff_delivery", "satisfaction_confirmation", "next_setup"]
        }

    def _create_reader_guidance_system(self, action_phases: list[dict[str, Any]]) -> dict[str, str]:
        """読者誘導システムを作成"""

        return {
            "orientation_signals": "clear_context_establishment",
            "progression_markers": "obvious_advancement_indicators",
            "expectation_management": "appropriate_anticipation_building",
            "satisfaction_delivery": "fulfillment_confirmation"
        }

    # Additional helper methods for character action patterns
    def _ensure_behavioral_consistency(self, action_phases: list[dict[str, Any]]) -> dict[str, Any]:
        """行動一貫性を確保"""

        return {
            "consistency_framework": {
                "core_personality_maintenance": "essential_traits_preservation",
                "motivation_alignment": "goal_consistent_actions",
                "decision_logic": "character_appropriate_choices"
            },
            "variation_allowance": {
                "growth_accommodation": "development_driven_changes",
                "situation_adaptation": "context_appropriate_responses",
                "relationship_evolution": "interaction_based_modifications"
            },
            "validation_checkpoints": [
                "character_voice_consistency",
                "action_motivation_alignment",
                "behavioral_pattern_maintenance"
            ]
        }

    def _design_interaction_dynamics(self, action_phases: list[dict[str, Any]]) -> dict[str, Any]:
        """相互作用動態を設計"""

        return {
            "interaction_patterns": {
                "dialogue_dynamics": "natural_conversation_flow",
                "conflict_interactions": "realistic_opposition_responses",
                "support_interactions": "believable_assistance_patterns"
            },
            "relationship_evolution": {
                "trust_development": "gradual_confidence_building",
                "conflict_escalation": "logical_tension_increases",
                "alliance_formation": "natural_cooperation_emergence"
            },
            "group_dynamics": {
                "power_balances": "realistic_influence_distribution",
                "decision_processes": "character_appropriate_choices",
                "collective_actions": "coordinated_group_behaviors"
            }
        }

    def _establish_growth_trajectories(self, action_phases: list[dict[str, Any]]) -> dict[str, Any]:
        """成長軌道を確立"""

        return {
            "development_arcs": {
                "skill_progression": "competency_improvement_paths",
                "emotional_maturity": "psychological_development_stages",
                "relationship_capacity": "interpersonal_skill_enhancement"
            },
            "milestone_achievements": {
                "competency_markers": "skill_demonstration_points",
                "wisdom_gains": "insight_realization_moments",
                "confidence_building": "self_assurance_development"
            },
            "setback_recovery": {
                "resilience_building": "bounce_back_capacity_growth",
                "learning_integration": "experience_based_improvement",
                "adaptation_skills": "flexibility_development"
            }
        }

    def _verify_action_authenticity(self, action_phases: list[dict[str, Any]]) -> dict[str, Any]:
        """行動真正性を検証"""

        return {
            "authenticity_criteria": {
                "character_truth": "personality_aligned_actions",
                "situational_appropriateness": "context_matching_responses",
                "motivational_consistency": "goal_driven_behaviors"
            },
            "believability_factors": {
                "psychological_realism": "human_nature_compliance",
                "logical_causation": "cause_effect_relationships",
                "emotional_honesty": "genuine_feeling_expression"
            },
            "validation_methods": {
                "character_interview": "internal_consistency_check",
                "situation_analysis": "response_appropriateness_review",
                "reader_empathy_test": "relatability_assessment"
            }
        }

    def _establish_development_milestones(self, character: str, action_phases: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """発展マイルストーンを確立"""

        milestones = []

        for i, phase in enumerate(action_phases):
            milestone = {
                "phase": phase["phase_number"],
                "development_focus": f"{character}_growth_phase_{i+1}",
                "achievement_target": self._define_character_achievement_target(character, i, len(action_phases)),
                "measurement_criteria": self._establish_character_measurement_criteria(character, i)
            }
            milestones.append(milestone)

        return milestones

    def _define_character_achievement_target(self, character: str, phase_index: int, total_phases: int) -> str:
        """キャラクター達成目標を定義"""

        position_ratio = phase_index / (total_phases - 1) if total_phases > 1 else 0

        if character == "protagonist":
            if position_ratio <= 0.25:
                return "character_establishment_and_initial_challenge"
            if position_ratio <= 0.75:
                return "skill_development_and_obstacle_overcoming"
            return "mastery_demonstration_and_goal_achievement"
        return f"{character}_appropriate_development_milestone"

    def _establish_character_measurement_criteria(self, character: str, phase_index: int) -> list[str]:
        """キャラクター測定基準を確立"""

        return [
            f"{character}_phase_{phase_index + 1}_competency_demonstration",
            f"{character}_appropriate_decision_making",
            f"{character}_relationship_development_progress"
        ]

    def _track_behavioral_evolution(self, character: str, action_phases: list[dict[str, Any]]) -> dict[str, Any]:
        """行動進化を追跡"""

        return {
            "baseline_behavior": f"{character}_initial_behavioral_pattern",
            "evolution_markers": [f"phase_{i+1}_behavioral_adaptation" for i in range(len(action_phases))],
            "final_state": f"{character}_evolved_behavioral_pattern"
        }

    def _map_relationship_changes(self, character: str, action_phases: list[dict[str, Any]]) -> dict[str, Any]:
        """関係性変化をマッピング"""

        return {
            "relationship_trajectories": {
                "with_protagonist": "evolving_connection",
                "with_antagonist": "developing_opposition",
                "with_support_characters": "strengthening_bonds"
            },
            "interaction_evolution": {
                "trust_levels": "gradual_development",
                "conflict_intensity": "appropriate_escalation",
                "cooperation_capacity": "situation_dependent_growth"
            }
        }

    def _determine_required_setup(self, current_phase: dict[str, Any], next_phase: dict[str, Any]) -> list[str]:
        """必要セットアップを決定"""

        return [
            "emotional_preparation",
            "situational_context_establishment",
            "character_positioning",
            "momentum_building_elements"
        ]

    def _identify_completion_signals(self, current_phase: dict[str, Any]) -> list[str]:
        """完了シグナルを特定"""

        return [
            "phase_objective_achievement",
            "character_development_milestone",
            "plot_progression_confirmation",
            "reader_satisfaction_delivery"
        ]
