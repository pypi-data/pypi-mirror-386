"""Domain.services.writing_steps.emotion_curve_designer_service
Where: Domain service module implementing a specific writing workflow step.
What: Provides helper routines and data structures for this writing step.
Why: Allows stepwise writing orchestrators to reuse consistent step logic.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""感情曲線設計サービス

A38執筆プロンプトガイド STEP 8: 感情曲線の実装。
読者の感情変化と登場人物の感情推移を設計。
"""

import time
from dataclasses import dataclass
from typing import Any

from noveler.domain.services.writing_steps.base_writing_step import (
    BaseWritingStep,
    WritingStepResponse,
)
from noveler.domain.interfaces.logger_interface import ILogger, NullLogger
from src.mcp_servers.noveler.tools.emotion.base_emotion_tool import EmotionIntensity, EmotionLayer, EmotionToolInput
from src.mcp_servers.noveler.tools.emotion.emotion_pipeline_coordinator import EmotionPipelineCoordinator


@dataclass
class EmotionalMoment:
    """感情的瞬間データ構造"""
    moment: str
    intensity: int  # 1-10
    emotion_type: str


@dataclass
class CharacterEmotionArc:
    """キャラクター感情弧データ構造"""
    starting_emotion: str
    ending_emotion: str
    journey_points: list[dict[str, str | int]]
    emotional_range: list[str]
    key_transitions: list[str]


@dataclass
class ReaderEmotionJourney:
    """読者感情ジャーニーデータ構造"""
    opening_hook: int
    engagement_curve: list[dict[str, str | int]]
    emotional_payoffs: list[str]
    satisfaction_points: list[str]
    cliffhanger_potential: int


@dataclass
class EmotionTransition:
    """感情遷移データ構造"""
    from_emotion: str
    to_emotion: str
    transition_type: str
    method: str
    pacing: str


@dataclass
class EmotionCurveDesign:
    """感情曲線設計データ構造"""
    episode_number: int
    overall_arc: str
    pattern_type: str
    peak_moments: list[EmotionalMoment]
    valley_moments: list[EmotionalMoment]
    transitions: list[EmotionTransition]
    character_emotions: dict[str, CharacterEmotionArc]
    reader_journey: ReaderEmotionJourney
    pacing_points: list[dict[str, str | int]]


@dataclass
class EmotionQualityAssessment:
    """感情表現品質評価データ構造"""
    overall_score: float
    cliche_score: float
    physiology_score: float
    diversity_score: float
    register_score: float
    contextual_score: float
    ab_test_score: float
    optimization_suggestions: list[str]
    detailed_reports: dict[str, dict[str, str | float | int | list[str]]]


class EmotionCurveDesignerService(BaseWritingStep):
    """感情曲線設計サービス

    A38 STEP 8: エピソード全体の感情的な起伏を設計し、
    読者の感情移入と興味維持を最適化する。
    """

    def __init__(self) -> None:
        super().__init__(
            step_number=8,
            step_name="感情曲線"
        )
        self.emotion_pipeline = EmotionPipelineCoordinator()
        # Domain-friendly default logger (no infra dependency)
        self.logger: ILogger = NullLogger()

    async def execute(
        self,
        episode_number: int,
        previous_results: dict[int, WritingStepResponse] | None = None
    ) -> WritingStepResponse:
        """感情曲線設計を実行

        Args:
            episode_number: エピソード番号
            previous_results: 前のステップの実行結果

        Returns:
            感情曲線設計結果
        """
        start_time = time.time()

        try:
            # 前ステップから必要情報を抽出
            story_context = self._extract_story_context(previous_results)
            characters = self._extract_characters(previous_results)
            dialogue_structure = self._extract_dialogue_structure(previous_results)

            # 感情曲線設計
            emotion_design = self._design_emotion_curve(
                story_context, characters, dialogue_structure, episode_number
            )

            # 感情ポイントのマッピング
            emotion_mapping = self._create_emotion_mapping(emotion_design)

            # 読者感情予測
            reader_emotion_prediction = self._predict_reader_emotions(emotion_design)

            # 感情表現品質評価と最適化（新機能）
            emotion_quality_assessment = await self._assess_and_optimize_emotion_expressions(
                emotion_design, story_context, characters
            )

            # 実行時間計算
            execution_time = (time.time() - start_time) * 1000

            return WritingStepResponse(
                success=True,
                step_number=self.step_number,
                step_name=self.step_name,
                execution_time_ms=execution_time,
                data={
                    "emotion_curve": emotion_design,
                    "emotion_mapping": emotion_mapping,
                    "reader_emotions": reader_emotion_prediction,
                    "emotion_quality": emotion_quality_assessment,
                    "peak_moments": emotion_design.get("peak_moments", []),
                    "emotional_transitions": len(emotion_design.get("transitions", []))
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

    def _extract_story_context(self, previous_results: dict[int, WritingStepResponse] | None) -> dict[str, str | int | list[str]]:
        """前ステップから物語コンテキストを抽出"""
        if not previous_results:
            return {}

        context = {}

        # STEP 0-7から関連情報を収集
        for result in previous_results.values():
            if hasattr(result, "data") and result.data:
                if "story_structure" in result.data:
                    context.update(result.data["story_structure"])
                elif "plot_points" in result.data:
                    context["plot_points"] = result.data["plot_points"]
                elif "scene_structure" in result.data:
                    context["scenes"] = result.data["scene_structure"]

        return context

    def _extract_characters(self, previous_results: dict[int, WritingStepResponse] | None) -> dict[str, dict[str, str | int | list[str]]]:
        """キャラクター情報を抽出"""
        if not previous_results:
            return {}

        characters = {}

        for step_num, result in previous_results.items():
            if hasattr(result, "data") and result.data:
                if "characters" in result.data:
                    characters.update(result.data["characters"])
                elif step_num == 6 and "validated_characters" in result.data:  # STEP 6結果
                    characters.update(result.data.get("character_consistency", {}))

        return characters

    def _extract_dialogue_structure(self, previous_results: dict[int, WritingStepResponse] | None) -> dict[str, str | int | list[dict[str, str | int]]]:
        """会話構造を抽出（STEP 7結果）"""
        if not previous_results or 7 not in previous_results:
            return {}

        step7_result = previous_results[7]
        if hasattr(step7_result, "data") and step7_result.data:
            return step7_result.data.get("dialogue_design", {})

        return {}

    def _design_emotion_curve(
        self,
        story_context: dict[str, Any],
        characters: dict[str, Any],
        dialogue_structure: dict[str, Any],
        episode_number: int
    ) -> dict[str, Any]:
        """感情曲線を設計"""

        # 基本感情曲線構造
        emotion_curve = {
            "episode_number": episode_number,
            "overall_arc": "rising_action",  # 基本的な感情弧
            "peak_moments": [],
            "valley_moments": [],
            "transitions": [],
            "character_emotions": {},
            "reader_journey": {},
            "pacing_points": []
        }

        # エピソードタイプに基づく感情パターン決定
        episode_pattern = self._determine_episode_pattern(episode_number, story_context)
        emotion_curve["pattern_type"] = episode_pattern

        # 感情ピーク・谷の特定
        peak_moments, valley_moments = self._identify_emotional_peaks_valleys(
            story_context, dialogue_structure, episode_pattern
        )
        emotion_curve["peak_moments"] = peak_moments
        emotion_curve["valley_moments"] = valley_moments

        # キャラクター別感情推移
        emotion_curve["character_emotions"] = self._design_character_emotion_arcs(
            characters, peak_moments, valley_moments
        )

        # 読者感情ジャーニー
        emotion_curve["reader_journey"] = self._design_reader_emotion_journey(
            episode_pattern, peak_moments, valley_moments
        )

        # 感情遷移ポイント
        emotion_curve["transitions"] = self._create_emotion_transitions(
            peak_moments, valley_moments, dialogue_structure
        )

        # ペーシング調整ポイント
        emotion_curve["pacing_points"] = self._determine_pacing_points(
            emotion_curve["transitions"]
        )

        return emotion_curve

    def _determine_episode_pattern(self, episode_number: int, story_context: dict[str, Any]) -> str:
        """エピソードパターンを決定"""
        # エピソード番号による基本パターン
        if episode_number == 1:
            return "introduction_excitement"
        if episode_number <= 3:
            return "building_tension"
        if episode_number <= 7:
            return "development_conflict"
        if episode_number <= 10:
            return "escalating_drama"
        return "climax_resolution"

    def _identify_emotional_peaks_valleys(
        self,
        story_context: dict[str, Any],
        dialogue_structure: dict[str, Any],
        pattern: str
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """感情のピークと谷を特定"""

        peaks = []
        valleys = []

        # パターン別のピーク・谷設定
        pattern_configs = {
            "introduction_excitement": {
                "peaks": [{"moment": "character_introduction", "intensity": 7, "type": "curiosity"}],
                "valleys": [{"moment": "setting_establishment", "intensity": 3, "type": "calm"}]
            },
            "building_tension": {
                "peaks": [{"moment": "first_conflict", "intensity": 8, "type": "tension"}],
                "valleys": [{"moment": "character_reflection", "intensity": 4, "type": "contemplation"}]
            },
            "development_conflict": {
                "peaks": [
                    {"moment": "major_revelation", "intensity": 8, "type": "shock"},
                    {"moment": "character_confrontation", "intensity": 9, "type": "conflict"}
                ],
                "valleys": [{"moment": "emotional_processing", "intensity": 3, "type": "processing"}]
            },
            "escalating_drama": {
                "peaks": [
                    {"moment": "crisis_peak", "intensity": 9, "type": "crisis"},
                    {"moment": "emotional_climax", "intensity": 10, "type": "catharsis"}
                ],
                "valleys": [{"moment": "before_storm", "intensity": 2, "type": "calm_before_storm"}]
            },
            "climax_resolution": {
                "peaks": [
                    {"moment": "final_confrontation", "intensity": 10, "type": "climax"},
                    {"moment": "resolution_joy", "intensity": 8, "type": "satisfaction"}
                ],
                "valleys": [{"moment": "aftermath_reflection", "intensity": 5, "type": "resolution"}]
            }
        }

        config = pattern_configs.get(pattern, pattern_configs["development_conflict"])
        peaks = config["peaks"]
        valleys = config["valleys"]

        # 会話構造から追加のピーク・谷を特定
        if dialogue_structure.get("high_tension_dialogues"):
            peaks.append({
                "moment": "dialogue_peak",
                "intensity": 8,
                "type": "verbal_conflict"
            })

        return peaks, valleys

    def _design_character_emotion_arcs(
        self,
        characters: dict[str, Any],
        peaks: list[dict[str, Any]],
        valleys: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """キャラクター別感情弧を設計"""

        character_arcs = {}

        for char_name, char_data in characters.items():
            arc = {
                "starting_emotion": "neutral",
                "ending_emotion": "transformed",
                "journey_points": [],
                "emotional_range": [],
                "key_transitions": []
            }

            # キャラクター役割による感情パターン
            role = char_data.get("role", "support")

            if role == "protagonist":
                arc["emotional_range"] = ["anxiety", "determination", "conflict", "growth", "resolution"]
            elif role == "antagonist":
                arc["emotional_range"] = ["confidence", "challenge", "frustration", "desperation", "defeat_or_victory"]
            elif role == "support":
                arc["emotional_range"] = ["concern", "support", "worry", "relief", "celebration"]
            else:
                arc["emotional_range"] = ["observation", "reaction", "involvement", "impact", "acceptance"]

            # 感情変化ポイント
            for i, emotion in enumerate(arc["emotional_range"]):
                arc["journey_points"].append({
                    "sequence": i + 1,
                    "emotion": emotion,
                    "intensity": 5 + (i * 2) % 6,  # 5-10の範囲
                    "trigger": peaks[min(i, len(peaks)-1)]["moment"] if peaks else "story_progression"
                })

            character_arcs[char_name] = arc

        return character_arcs

    def _design_reader_emotion_journey(
        self,
        pattern: str,
        peaks: list[dict[str, Any]],
        valleys: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """読者感情ジャーニーを設計"""

        journey = {
            "opening_hook": 7,  # 1-10スケール
            "engagement_curve": [],
            "emotional_payoffs": [],
            "satisfaction_points": [],
            "cliffhanger_potential": 0
        }

        # パターン別読者体験設計
        pattern_journeys = {
            "introduction_excitement": {
                "opening_hook": 8,
                "cliffhanger_potential": 7,
                "satisfaction_points": ["character_likeability", "world_intrigue"]
            },
            "building_tension": {
                "opening_hook": 7,
                "cliffhanger_potential": 8,
                "satisfaction_points": ["mystery_deepening", "relationship_development"]
            },
            "development_conflict": {
                "opening_hook": 6,
                "cliffhanger_potential": 9,
                "satisfaction_points": ["conflict_escalation", "character_growth"]
            },
            "escalating_drama": {
                "opening_hook": 9,
                "cliffhanger_potential": 10,
                "satisfaction_points": ["emotional_catharsis", "plot_revelation"]
            },
            "climax_resolution": {
                "opening_hook": 8,
                "cliffhanger_potential": 5,
                "satisfaction_points": ["resolution_satisfaction", "character_completion"]
            }
        }

        config = pattern_journeys.get(pattern, pattern_journeys["development_conflict"])
        journey.update(config)

        # エンゲージメント曲線（時系列）
        journey["engagement_curve"] = [
            {"section": "opening", "engagement": journey["opening_hook"]},
            {"section": "development", "engagement": 6},
            {"section": "conflict", "engagement": 9},
            {"section": "climax", "engagement": 10},
            {"section": "resolution", "engagement": 7}
        ]

        return journey

    def _create_emotion_transitions(
        self,
        peaks: list[dict[str, Any]],
        valleys: list[dict[str, Any]],
        dialogue_structure: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """感情遷移ポイントを作成"""

        transitions = []

        # ピーク間の遷移
        for i in range(len(peaks) - 1):
            current_peak = peaks[i]
            next_peak = peaks[i + 1]

            transition = {
                "from_emotion": current_peak["type"],
                "to_emotion": next_peak["type"],
                "transition_type": self._determine_transition_type(
                    current_peak["intensity"],
                    next_peak["intensity"]
                ),
                "method": "gradual_shift",
                "pacing": "medium"
            }
            transitions.append(transition)

        # ピークから谷への遷移
        for peak in peaks:
            for valley in valleys:
                if valley["intensity"] < peak["intensity"]:
                    transition = {
                        "from_emotion": peak["type"],
                        "to_emotion": valley["type"],
                        "transition_type": "descending",
                        "method": "emotional_release",
                        "pacing": "slow"
                    }
                    transitions.append(transition)

        return transitions

    def _determine_transition_type(self, from_intensity: int, to_intensity: int) -> str:
        """遷移タイプを決定"""
        diff = to_intensity - from_intensity

        if diff > 3:
            return "dramatic_rise"
        if diff > 0:
            return "gradual_rise"
        if diff < -3:
            return "dramatic_fall"
        if diff < 0:
            return "gradual_fall"
        return "stable"

    def _determine_pacing_points(self, transitions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """ペーシング調整ポイントを決定"""

        pacing_points = []

        for transition in transitions:
            pacing_point = {
                "location": f"transition_to_{transition['to_emotion']}",
                "adjustment": self._calculate_pacing_adjustment(transition),
                "technique": self._suggest_pacing_technique(transition),
                "priority": self._assess_pacing_priority(transition)
            }
            pacing_points.append(pacing_point)

        return pacing_points

    def _calculate_pacing_adjustment(self, transition: dict[str, Any]) -> str:
        """ペーシング調整を計算"""
        transition_type = transition["transition_type"]

        adjustments = {
            "dramatic_rise": "accelerate",
            "gradual_rise": "steady",
            "dramatic_fall": "decelerate_sharp",
            "gradual_fall": "decelerate_smooth",
            "stable": "maintain"
        }

        return adjustments.get(transition_type, "maintain")

    def _suggest_pacing_technique(self, transition: dict[str, Any]) -> list[str]:
        """ペーシング技法を提案"""

        adjustment = self._calculate_pacing_adjustment(transition)

        technique_map = {
            "accelerate": ["短文使用", "行動描写増加", "対話テンポ向上"],
            "steady": ["バランス維持", "自然な流れ", "適度な描写"],
            "decelerate_sharp": ["長文使用", "内省描写", "時間的余韻"],
            "decelerate_smooth": ["段階的減速", "情景描写", "感情処理"],
            "maintain": ["現状維持", "安定したリズム", "読みやすさ重視"]
        }

        return technique_map.get(adjustment, ["標準的な技法"])

    def _assess_pacing_priority(self, transition: dict[str, Any]) -> str:
        """ペーシング優先度を評価"""
        if transition["transition_type"] in ["dramatic_rise", "dramatic_fall"]:
            return "high"
        if transition["pacing"] == "slow":
            return "medium"
        return "low"

    def _create_emotion_mapping(self, emotion_design: dict[str, Any]) -> dict[str, Any]:
        """感情マッピングを作成"""
        mapping = {
            "scene_emotion_map": {},
            "character_state_map": {},
            "reader_engagement_map": {},
            "transition_map": {}
        }

        # シーン別感情マッピング
        for i, transition in enumerate(emotion_design.get("transitions", [])):
            scene_key = f"scene_{i+1}"
            mapping["scene_emotion_map"][scene_key] = {
                "primary_emotion": transition["to_emotion"],
                "intensity": 7,  # デフォルト
                "techniques": transition.get("method", "standard")
            }

        # キャラクター状態マッピング
        character_emotions = emotion_design.get("character_emotions", {})
        for char_name, arc in character_emotions.items():
            mapping["character_state_map"][char_name] = {
                "emotional_states": [point["emotion"] for point in arc["journey_points"]],
                "key_moments": [point["trigger"] for point in arc["journey_points"]],
                "intensity_range": [point["intensity"] for point in arc["journey_points"]]
            }

        # 読者エンゲージメントマッピング
        reader_journey = emotion_design.get("reader_journey", {})
        mapping["reader_engagement_map"] = {
            "engagement_levels": reader_journey.get("engagement_curve", []),
            "payoff_moments": reader_journey.get("satisfaction_points", []),
            "hook_strength": reader_journey.get("opening_hook", 7)
        }

        return mapping

    def _predict_reader_emotions(self, emotion_design: dict[str, Any]) -> dict[str, Any]:
        """読者感情を予測"""
        prediction = {
            "emotional_impact_score": 0.0,
            "engagement_prediction": {},
            "satisfaction_likelihood": 0.0,
            "potential_concerns": [],
            "optimization_suggestions": []
        }

        # 感情インパクトスコア計算
        peaks = emotion_design.get("peak_moments", [])
        if peaks:
            avg_intensity = sum(peak["intensity"] for peak in peaks) / len(peaks)
            prediction["emotional_impact_score"] = avg_intensity / 10.0
        else:
            prediction["emotional_impact_score"] = 0.5

        # エンゲージメント予測
        reader_journey = emotion_design.get("reader_journey", {})
        prediction["engagement_prediction"] = {
            "opening_engagement": reader_journey.get("opening_hook", 7) / 10.0,
            "sustained_interest": 0.75,  # デフォルト
            "climax_impact": prediction["emotional_impact_score"],
            "resolution_satisfaction": 0.8
        }

        # 満足度予測
        satisfaction_factors = [
            reader_journey.get("opening_hook", 7) / 10.0,
            prediction["emotional_impact_score"],
            len(reader_journey.get("satisfaction_points", [])) * 0.1
        ]
        prediction["satisfaction_likelihood"] = sum(satisfaction_factors) / len(satisfaction_factors)

        # 潜在的懸念
        if prediction["emotional_impact_score"] < 0.6:
            prediction["potential_concerns"].append("感情的インパクトが不足している可能性")

        if len(peaks) < 2:
            prediction["potential_concerns"].append("感情の起伏が少ない可能性")

        if reader_journey.get("cliffhanger_potential", 0) < 5:
            prediction["potential_concerns"].append("次話への引きが弱い可能性")

        # 最適化提案
        if prediction["emotional_impact_score"] < 0.7:
            prediction["optimization_suggestions"].append("感情ピークの強化を検討")

        if len(emotion_design.get("transitions", [])) < 3:
            prediction["optimization_suggestions"].append("感情遷移の多様化を検討")

        return prediction

    async def _assess_and_optimize_emotion_expressions(
        self,
        emotion_design: EmotionCurveDesign,
        story_context: dict[str, str | int | list[str]],
        characters: dict[str, dict[str, str | int | list[str]]]
    ) -> EmotionQualityAssessment:
        """6つのMCPツールを使用した感情表現の品質評価と最適化

        Args:
            emotion_design: 設計された感情曲線
            story_context: 物語コンテキスト
            characters: キャラクター情報

        Returns:
            品質評価結果と最適化提案
        """
        self.logger.info("感情表現品質評価開始")

        # テスト用感情表現テキスト生成
        sample_emotion_texts = self._generate_sample_emotion_texts(emotion_design)

        total_scores = []
        all_suggestions = []
        detailed_reports = {}

        for idx, text_sample in enumerate(sample_emotion_texts):
            try:
                # EmotionPipelineCoordinatorを使用した統合評価
                emotion_input = EmotionToolInput(
                    text=text_sample["text"],
                    emotion_layer=EmotionLayer.ALL,
                    intensity=EmotionIntensity.MODERATE,
                    metadata={
                        "emotion": text_sample["emotion_type"],
                        "target_audience": story_context.get("target_audience", "adult"),
                        "genre": story_context.get("genre", "general"),
                        "scene_setting": text_sample.get("scene_context", "")
                    }
                )

                # 統合評価実行（全6ツール）
                evaluation_result = await self.emotion_pipeline.execute(emotion_input)

                if evaluation_result.success:
                    total_scores.append(evaluation_result.score)
                    all_suggestions.extend(evaluation_result.suggestions)
                    detailed_reports[f"sample_{idx}"] = evaluation_result.analysis

                    self.logger.info(f"感情表現サンプル{idx}評価完了: スコア{evaluation_result.score}")
                else:
                    self.logger.warning(f"感情表現サンプル{idx}評価エラー: {evaluation_result.error_message}")

            except Exception as e:
                self.logger.exception(f"感情表現評価中にエラー: {e!s}")
                continue

        # 統合スコア計算
        overall_score = sum(total_scores) / len(total_scores) if total_scores else 0.0

        # ツール別スコア集約
        tool_scores = self._aggregate_tool_scores(detailed_reports)

        # 最適化提案統合
        optimization_suggestions = self._consolidate_optimization_suggestions(all_suggestions)

        assessment = EmotionQualityAssessment(
            overall_score=overall_score,
            cliche_score=tool_scores.get("cliche_detector", 0.0),
            physiology_score=tool_scores.get("physiology_checker", 0.0),
            diversity_score=tool_scores.get("metaphor_diversity_scorer", 0.0),
            register_score=tool_scores.get("register_verifier", 0.0),
            contextual_score=tool_scores.get("contextual_cue_retriever", 0.0),
            ab_test_score=tool_scores.get("micro_ab_emotion_test", 0.0),
            optimization_suggestions=optimization_suggestions,
            detailed_reports=detailed_reports
        )

        self.logger.info(f"感情表現品質評価完了: 総合スコア{overall_score:.2f}")
        return assessment

    def _generate_sample_emotion_texts(
        self,
        emotion_design: EmotionCurveDesign
    ) -> list[dict[str, str | int]]:
        """感情表現サンプルテキストの生成

        Args:
            emotion_design: 感情曲線設計

        Returns:
            評価用サンプルテキストリスト
        """
        samples = []

        # ピーク感情からサンプル生成
        for peak in emotion_design.peak_moments:
            sample_text = self._create_emotion_sample_text(
                peak.emotion_type,
                peak.intensity,
                peak.moment
            )
            samples.append({
                "text": sample_text,
                "emotion_type": peak.emotion_type,
                "intensity": peak.intensity,
                "scene_context": peak.moment
            })

        # 谷感情からもサンプル生成
        for valley in emotion_design.valley_moments:
            sample_text = self._create_emotion_sample_text(
                valley.emotion_type,
                valley.intensity,
                valley.moment
            )
            samples.append({
                "text": sample_text,
                "emotion_type": valley.emotion_type,
                "intensity": valley.intensity,
                "scene_context": valley.moment
            })

        return samples

    def _create_emotion_sample_text(
        self,
        emotion_type: str,
        intensity: int,
        scene_context: str
    ) -> str:
        """具体的な感情表現テキストサンプルを生成

        Args:
            emotion_type: 感情タイプ
            intensity: 感情強度
            scene_context: シーンコンテキスト

        Returns:
            生成されたサンプルテキスト
        """
        # 感情タイプ別テンプレート
        emotion_templates = {
            "fear": "心臓が激しく鼓動し、{context}で震えが止まらない。",
            "joy": "胸が暖かくなり、{context}で自然と笑顔がこぼれる。",
            "anger": "血が煮えたぎり、{context}で拳を強く握りしめる。",
            "sadness": "涙が頬を伝い、{context}で深い溜息をつく。",
            "tension": "空気が張り詰め、{context}で全身が緊張する。",
            "shock": "言葉を失い、{context}で愕然と立ち尽くす。",
            "curiosity": "興味が湧き上がり、{context}で身を乗り出す。"
        }

        template = emotion_templates.get(emotion_type, "感情が湧き上がり、{context}で心が動く。")

        # 強度による修飾語調整
        intensity_modifiers = {
            1: "かすかに", 2: "わずかに", 3: "少し",
            4: "やや", 5: "程よく", 6: "強く",
            7: "激しく", 8: "非常に", 9: "極めて", 10: "限界まで"
        }

        modifier = intensity_modifiers.get(intensity, "")
        sample_text = template.format(context=scene_context)

        if modifier:
            sample_text = sample_text.replace("激しく", modifier).replace("強く", modifier)

        return sample_text

    def _aggregate_tool_scores(
        self,
        detailed_reports: dict[str, dict[str, str | float | int | list[str]]]
    ) -> dict[str, float]:
        """ツール別スコアの集約

        Args:
            detailed_reports: 詳細レポート

        Returns:
            ツール別平均スコア
        """
        tool_scores = {}

        # ツール名マッピング（EmotionPipelineCoordinatorからの結果構造に基づく）
        tool_mapping = {
            "cliche_detector": "cliche_detector",
            "physiology_checker": "physiology_checker",
            "metaphor_diversity_scorer": "metaphor_diversity_scorer",
            "register_verifier": "register_verifier",
            "contextual_cue_retriever": "contextual_cue_retriever",
            "micro_ab_emotion_test": "micro_ab_emotion_test"
        }

        for tool_key in tool_mapping:
            scores = []
            for report in detailed_reports.values():
                tool_data = report.get(tool_key, {})
                if isinstance(tool_data, dict) and "score" in tool_data:
                    scores.append(float(tool_data["score"]))

            tool_scores[tool_key] = sum(scores) / len(scores) if scores else 0.0

        return tool_scores

    def _consolidate_optimization_suggestions(
        self,
        all_suggestions: list[str]
    ) -> list[str]:
        """最適化提案の統合と重複除去

        Args:
            all_suggestions: 全提案リスト

        Returns:
            統合された最適化提案
        """
        # 重複除去と優先度付け
        unique_suggestions = list(set(all_suggestions))

        # 提案を重要度でソート（キーワードベース）
        priority_keywords = ["陳腐", "生理", "多様性", "適性", "文脈", "比較"]

        prioritized = []
        standard = []

        for suggestion in unique_suggestions:
            is_high_priority = any(keyword in suggestion for keyword in priority_keywords)
            if is_high_priority:
                prioritized.append(suggestion)
            else:
                standard.append(suggestion)

        # 上位提案を最大10個に制限
        return prioritized[:5] + standard[:5]
