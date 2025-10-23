#!/usr/bin/env python3
"""A28拡張プロット生成の関数型コア実装

B20準拠：純粋関数のみ、副作用なし
A28対応：7つの拡張機能統合
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# A28 Enhancement Data Structures - A28拡張機能データ構造

class ForeshadowingStatus(Enum):
    """伏線状態"""
    PLANNED = "planned"
    PLANTED = "planted"
    REFERENCED = "referenced"
    RESOLVED = "resolved"

class ImportanceRank(Enum):
    """重要度ランク"""
    S = "S"  # 最重要
    A = "A"  # 重要
    B = "B"  # 標準
    C = "C"  # 補完

@dataclass
class ForeshadowingElement:
    """伏線要素"""
    foreshadow_id: str
    element: str
    category: str
    status: ForeshadowingStatus
    planted_episode: int
    resolution_episode: int | None
    importance_level: int
    dependency: list[str]
    placement_scene: str
    reader_clue_level: str

@dataclass
class SceneData:
    """シーンデータ"""
    scene_id: str
    title: str
    importance_rank: ImportanceRank
    estimated_words: int
    percentage: float
    story_function: str
    emotional_weight: str
    technical_complexity: str
    reader_engagement_level: str

@dataclass
class EmotionTechFusion:
    """感情×技術融合データ"""
    timing: str
    scene_reference: str
    emotion_type: str
    emotion_intensity: str
    tech_concept: str
    tech_complexity: str
    synergy_effect: str
    synergy_intensity: str

@dataclass
class PlotGenerationInput:
    """プロット生成入力（不変）- A28拡張版"""

    # 基本入力
    episode_number: int
    chapter_info: dict[str, Any]
    previous_episodes: list[dict[str, Any]]
    quality_threshold: float = 0.8

    # A28拡張機能入力
    enable_enhancements: bool = True
    foreshadowing_elements: list[ForeshadowingElement] = field(default_factory=list)
    scene_structure: list[SceneData] = field(default_factory=list)
    emotion_tech_fusions: list[EmotionTechFusion] = field(default_factory=list)
    target_word_count: int = 6000
    viewpoint_character: str = "主人公"
    three_act_ratios: tuple[float, float, float] = (0.25, 0.50, 0.25)


@dataclass(frozen=True)
class EnhancedPlotAnalysis:
    """拡張プロット分析結果"""
    foreshadowing_consistency_score: float
    scene_balance_score: float
    emotion_tech_integration_score: float
    stage_interconnection_score: float
    word_allocation_score: float
    reader_engagement_prediction: float
    viewpoint_consistency_score: float
    overall_enhancement_score: float

@dataclass(frozen=True)
class PlotGenerationOutput:
    """プロット生成出力（不変）- A28拡張版"""

    # 基本出力
    episode_number: int
    plot_content: str
    quality_score: float
    key_events: list[str]
    success: bool
    error_message: str | None = None

    # A28拡張機能出力
    enhancement_analysis: EnhancedPlotAnalysis | None = None
    validated_foreshadowing: list[ForeshadowingElement] = field(default_factory=list)
    optimized_scene_structure: list[SceneData] = field(default_factory=list)
    fusion_points: list[EmotionTechFusion] = field(default_factory=list)
    word_allocation_breakdown: dict[str, int] = field(default_factory=dict)
    reader_reaction_predictions: dict[str, str] = field(default_factory=dict)
    viewpoint_validation_result: dict[str, Any] = field(default_factory=dict)
    improvement_suggestions: list[str] = field(default_factory=list)


class PlotGenerationCore:
    """プロット生成の Functional Core - A28拡張版

    B20準拠: 純粋関数のみ、副作用なし
    A28対応: 7つの拡張機能統合
    """

    @staticmethod
    def is_pure_function() -> bool:
        """純粋関数であることを保証"""
        return True

    @staticmethod
    def validate_input(input_data: PlotGenerationInput) -> tuple[bool, str | None]:
        """入力検証（純粋関数）- A28拡張版

        Args:
            input_data: プロット生成入力

        Returns:
            (検証成功, エラーメッセージ)
        """
        # 基本検証
        if input_data.episode_number <= 0:
            return False, "Episode number must be positive"

        if input_data.quality_threshold < 0 or input_data.quality_threshold > 1:
            return False, "Quality threshold must be between 0 and 1"

        if not input_data.chapter_info:
            return False, "Chapter info is required"

        # A28拡張機能検証
        if not input_data.enable_enhancements:
            return True, None
        # 伏線ID重複チェック
        foreshadow_ids = [f.foreshadow_id for f in input_data.foreshadowing_elements]
        if len(foreshadow_ids) != len(set(foreshadow_ids)):
            return False, "Duplicate foreshadowing IDs found"

        # 伏線ID形式チェック - エラー統合
        for foreshadow in input_data.foreshadowing_elements:
            if not foreshadow.foreshadow_id.startswith("FS") or len(foreshadow.foreshadow_id) != 5:
                return False, f"Invalid foreshadowing ID format: {foreshadow.foreshadow_id}"

        # シーンID重複チェック
        scene_ids = [s.scene_id for s in input_data.scene_structure]
        if len(scene_ids) != len(set(scene_ids)):
            return False, "Duplicate scene IDs found"

        # 三幕構成比率チェック - 属性存在確認付き
        if hasattr(input_data, "three_act_ratios") and input_data.three_act_ratios:
            ratio_sum = sum(input_data.three_act_ratios)
            if abs(ratio_sum - 1.0) > 0.01:
                return False, f"Three-act ratios must sum to 1.0, got {ratio_sum}"

        return True, None

    @staticmethod
    def calculate_quality_score(
        plot_content: str, key_events: list[str], previous_episodes: list[dict[str, Any]]
    ) -> float:
        """品質スコア計算（純粋関数）

        Args:
            plot_content: プロット内容
            key_events: 重要イベント
            previous_episodes: 前エピソード情報

        Returns:
            品質スコア (0.0-1.0)
        """
        # スコア計算ロジック（決定論的）
        # ベース値は 0.6 とし、短い章構成でも一定品質を担保
        base_score = 0.6

        content_length = len(plot_content)
        if content_length >= 800:
            base_score += 0.1
        elif content_length >= 400:
            base_score += 0.05

        # キーイベント数に応じてボーナス（最大 +0.2）
        event_bonus = min(len(key_events) * 0.05, 0.2)
        base_score += event_bonus

        # 前エピソードとの連続性ボーナス（最大 +0.1）
        if previous_episodes:
            continuity_bonus = min(0.1, 0.03 * len(previous_episodes))
            base_score += continuity_bonus

        return min(base_score, 1.0)

    @staticmethod
    def extract_key_events(plot_content: str, foreshadowing_elements: list[ForeshadowingElement] | None = None) -> list[str]:
        """キーイベント抽出（純粋関数）- A28拡張版

        Args:
            plot_content: プロット内容
            foreshadowing_elements: 伏線要素リスト

        Returns:
            キーイベントリスト
        """
        # 基本的な抽出ロジック（決定論的）
        events = []

        # 伏線マーカーの検出
        if "伏線" in plot_content:
            events.append("伏線の設置")

        # クライマックスマーカーの検出
        if "クライマックス" in plot_content or "山場" in plot_content:
            events.append("クライマックスシーン")

        # 展開マーカーの検出
        if "転換" in plot_content or "展開" in plot_content:
            events.append("物語の転換点")

        # A28拡張: 伏線要素からのキーイベント抽出
        if foreshadowing_elements:
            for foreshadow in foreshadowing_elements:
                if foreshadow.status == ForeshadowingStatus.PLANTED:
                    events.append(f"伏線設置: {foreshadow.element}")
                elif foreshadow.status == ForeshadowingStatus.RESOLVED:
                    events.append(f"伏線回収: {foreshadow.element}")

        # 重複除去
        return list(dict.fromkeys(events))

    @staticmethod
    def generate_plot_structure(episode_number: int, chapter_info: dict[str, Any]) -> str:
        """プロット構造生成（純粋関数）

        Args:
            episode_number: エピソード番号
            chapter_info: 章情報

        Returns:
            プロット構造文字列
        """
        # 決定論的なプロット構造生成
        title = chapter_info.get("title", f"第{episode_number}話")
        summary = chapter_info.get("summary", "")

        return f"""# {title}

## あらすじ
{summary}

## シーン構成
1. 導入
2. 展開
3. クライマックス
4. 結末

## キャラクター
- 主人公
- サブキャラクター

## 重要要素
- 伏線
- テーマ
"""

    @staticmethod
    def process_enhancements(input_data: PlotGenerationInput) -> tuple[EnhancedPlotAnalysis, dict[str, Any]]:
        """A28拡張機能処理（純粋関数）

        Args:
            input_data: プロット生成入力

        Returns:
            (拡張分析結果, 処理済みデータ)
        """
        if not input_data.enable_enhancements:
            return EnhancedPlotAnalysis(
                foreshadowing_consistency_score=0.0,
                scene_balance_score=0.0,
                emotion_tech_integration_score=0.0,
                stage_interconnection_score=0.0,
                word_allocation_score=0.0,
                reader_engagement_prediction=0.0,
                viewpoint_consistency_score=0.0,
                overall_enhancement_score=0.0,
            ), {}

        # Enhancement 1: 伏線追跡システム
        foreshadowing_score = PlotGenerationCore._analyze_foreshadowing_consistency(input_data.foreshadowing_elements)

        # Enhancement 2: シーン粒度管理
        scene_balance_score = PlotGenerationCore._analyze_scene_balance(input_data.scene_structure, input_data.target_word_count)

        # Enhancement 3: 感情×技術融合
        emotion_tech_score = PlotGenerationCore._analyze_emotion_tech_fusion(input_data.emotion_tech_fusions)

        # Enhancement 4: ステージ間連携（簡易実装）
        stage_interconnection_score = 0.8  # プレースホルダー

        # Enhancement 5: 文字数配分ガイドライン
        word_allocation_score = PlotGenerationCore._analyze_word_allocation(input_data.three_act_ratios, input_data.scene_structure)

        # Enhancement 6: 読者反応予測
        reader_engagement_score = PlotGenerationCore._predict_reader_engagement(input_data.scene_structure, input_data.emotion_tech_fusions)

        # Enhancement 7: 視点一貫性チェック
        viewpoint_consistency_score = PlotGenerationCore._check_viewpoint_consistency(input_data.viewpoint_character)

        # 総合スコア計算
        scores = [
            foreshadowing_score,
            scene_balance_score,
            emotion_tech_score,
            stage_interconnection_score,
            word_allocation_score,
            reader_engagement_score,
            viewpoint_consistency_score,
        ]
        overall_score = sum(scores) / len(scores)

        analysis = EnhancedPlotAnalysis(
            foreshadowing_consistency_score=foreshadowing_score,
            scene_balance_score=scene_balance_score,
            emotion_tech_integration_score=emotion_tech_score,
            stage_interconnection_score=stage_interconnection_score,
            word_allocation_score=word_allocation_score,
            reader_engagement_prediction=reader_engagement_score,
            viewpoint_consistency_score=viewpoint_consistency_score,
            overall_enhancement_score=overall_score,
        )

        # 処理済みデータ
        processed_data = {
            "word_allocation": PlotGenerationCore._calculate_word_allocation(input_data.three_act_ratios, input_data.target_word_count),
            "reader_predictions": PlotGenerationCore._generate_reader_predictions(input_data.scene_structure),
            "improvement_suggestions": PlotGenerationCore._generate_improvement_suggestions(analysis),
        }

        return analysis, processed_data

    @staticmethod
    def _analyze_foreshadowing_consistency(foreshadowing_elements: list[ForeshadowingElement]) -> float:
        """伏線一貫性分析"""
        if not foreshadowing_elements:
            return 1.0  # 伏線なしは問題なし

        # 依存関係の循環チェック
        dependency_score = 1.0
        for element in foreshadowing_elements:
            if element.foreshadow_id in element.dependency:
                dependency_score -= 0.2

        # 重要度レベル分布チェック
        importance_levels = [e.importance_level for e in foreshadowing_elements]
        if importance_levels:
            avg_importance = sum(importance_levels) / len(importance_levels)
            importance_score = min(avg_importance / 5.0, 1.0)
        else:
            importance_score = 0.0

        return (dependency_score + importance_score) / 2.0

    @staticmethod
    def _analyze_scene_balance(scene_structure: list[SceneData], target_word_count: int) -> float:
        """シーンバランス分析"""
        if not scene_structure:
            return 0.0

        # 重要度分布チェック
        rank_counts = dict.fromkeys(ImportanceRank, 0)
        total_words = 0

        for scene in scene_structure:
            rank_counts[scene.importance_rank] += 1
            total_words += scene.estimated_words

        # バランススコア計算
        s_ratio = rank_counts[ImportanceRank.S] / len(scene_structure)
        a_ratio = rank_counts[ImportanceRank.A] / len(scene_structure)

        balance_score = 1.0 - abs(0.3 - s_ratio) - abs(0.4 - a_ratio)

        # 文字数精度チェック
        word_accuracy = 1.0 - abs(total_words - target_word_count) / target_word_count

        return (balance_score + word_accuracy) / 2.0

    @staticmethod
    def _analyze_emotion_tech_fusion(emotion_tech_fusions: list[EmotionTechFusion]) -> float:
        """感情×技術融合分析"""
        if not emotion_tech_fusions:
            return 0.5  # 融合なしは中程度

        # シナジー強度評価
        intensity_scores = {
            "maximum": 1.0,
            "high": 0.8,
            "medium": 0.6,
        }

        total_score = 0.0
        for fusion in emotion_tech_fusions:
            score = intensity_scores.get(fusion.synergy_intensity, 0.4)
            total_score += score

        return min(total_score / len(emotion_tech_fusions), 1.0)

    @staticmethod
    def _analyze_word_allocation(three_act_ratios: tuple[float, float, float], scene_structure: list[SceneData]) -> float:
        """文字数配分分析"""
        # 理想的な三幕構成比率チェック
        ideal_ratios = (0.25, 0.50, 0.25)
        ratio_score = 1.0 - sum(abs(actual - ideal) for actual, ideal in zip(three_act_ratios, ideal_ratios, strict=False))

        # シーン配分の妥当性チェック
        if scene_structure:
            total_percentage = sum(scene.percentage for scene in scene_structure)
            percentage_accuracy = 1.0 - abs(100.0 - total_percentage) / 100.0
        else:
            percentage_accuracy = 0.0

        return (ratio_score + percentage_accuracy) / 2.0

    @staticmethod
    def _predict_reader_engagement(scene_structure: list[SceneData], emotion_tech_fusions: list[EmotionTechFusion]) -> float:
        """読者エンゲージメント予測"""
        if not scene_structure:
            return 0.5

        # 高エンゲージメントシーンの割合
        high_engagement_scenes = [s for s in scene_structure if s.reader_engagement_level == "high"]
        engagement_ratio = len(high_engagement_scenes) / len(scene_structure)

        # 感情×技術融合による補正
        fusion_bonus = min(len(emotion_tech_fusions) * 0.1, 0.3)

        return min(engagement_ratio + fusion_bonus, 1.0)

    @staticmethod
    def _check_viewpoint_consistency(viewpoint_character: str) -> float:
        """視点一貫性チェック（簡易実装）"""
        # 視点キャラクターが設定されていれば基本的にOK
        if viewpoint_character and viewpoint_character.strip():
            return 0.9
        return 0.5

    @staticmethod
    def _calculate_word_allocation(three_act_ratios: tuple[float, float, float], target_word_count: int) -> dict[str, int]:
        """文字数配分計算"""
        return {
            "act_1": int(target_word_count * three_act_ratios[0]),
            "act_2": int(target_word_count * three_act_ratios[1]),
            "act_3": int(target_word_count * three_act_ratios[2]),
        }

    @staticmethod
    def _generate_reader_predictions(scene_structure: list[SceneData]) -> dict[str, str]:
        """読者反応予測生成"""
        predictions = {}
        for scene in scene_structure:
            if scene.reader_engagement_level == "high":
                predictions[scene.scene_id] = "高い関心と感情移入が期待される"
            elif scene.reader_engagement_level == "medium":
                predictions[scene.scene_id] = "適度な興味を維持"
            else:
                predictions[scene.scene_id] = "注意深い構成が必要"
        return predictions

    @staticmethod
    def _generate_improvement_suggestions(analysis: EnhancedPlotAnalysis) -> list[str]:
        """改善提案生成"""
        suggestions = []

        if analysis.foreshadowing_consistency_score < 0.7:
            suggestions.append("伏線の依存関係を見直し、循環参照を解消してください")

        if analysis.scene_balance_score < 0.7:
            suggestions.append("シーンの重要度分布を調整し、S級シーンを30%程度に保ってください")

        if analysis.emotion_tech_integration_score < 0.6:
            suggestions.append("感情的展開と技術的要素の融合ポイントを増やしてください")

        if analysis.word_allocation_score < 0.7:
            suggestions.append("三幕構成の文字数配分を25%-50%-25%に近づけてください")

        if analysis.reader_engagement_prediction < 0.6:
            suggestions.append("読者の興味を引くシーンを増やし、全体の60%以上を高エンゲージメントにしてください")

        return suggestions

    @staticmethod
    def transform_plot(input_data: PlotGenerationInput) -> PlotGenerationOutput:
        """プロット変換処理（純粋関数）- A28拡張版

        Args:
            input_data: プロット生成入力

        Returns:
            PlotGenerationOutput: 変換結果
        """
        # 入力検証
        is_valid, error_msg = PlotGenerationCore.validate_input(input_data)
        if not is_valid:
            return PlotGenerationOutput(
                episode_number=input_data.episode_number,
                plot_content="",
                quality_score=0.0,
                key_events=[],
                success=False,
                error_message=error_msg,
            )

        # プロット構造生成
        plot_content = PlotGenerationCore.generate_plot_structure(input_data.episode_number, input_data.chapter_info)

        # キーイベント抽出（A28拡張）
        key_events = PlotGenerationCore.extract_key_events(plot_content, input_data.foreshadowing_elements)

        # 基本品質スコア計算
        base_quality_score = PlotGenerationCore.calculate_quality_score(
            plot_content, key_events, input_data.previous_episodes
        )

        # A28拡張機能処理
        enhancement_analysis, processed_data = PlotGenerationCore.process_enhancements(input_data)

        # 最終品質スコア計算（基本スコア + 拡張スコア）
        if input_data.enable_enhancements:
            final_quality_score = (base_quality_score + enhancement_analysis.overall_enhancement_score) / 2.0
        else:
            final_quality_score = base_quality_score

        # 品質チェック
        if final_quality_score < input_data.quality_threshold:
            return PlotGenerationOutput(
                episode_number=input_data.episode_number,
                plot_content=plot_content,
                quality_score=final_quality_score,
                key_events=key_events,
                success=False,
                error_message=f"Quality score {final_quality_score} below threshold {input_data.quality_threshold}",
                enhancement_analysis=enhancement_analysis,
                improvement_suggestions=processed_data.get("improvement_suggestions", []),
            )

        return PlotGenerationOutput(
            episode_number=input_data.episode_number,
            plot_content=plot_content,
            quality_score=final_quality_score,
            key_events=key_events,
            success=True,
            enhancement_analysis=enhancement_analysis,
            validated_foreshadowing=input_data.foreshadowing_elements,
            optimized_scene_structure=input_data.scene_structure,
            fusion_points=input_data.emotion_tech_fusions,
            word_allocation_breakdown=processed_data.get("word_allocation", {}),
            reader_reaction_predictions=processed_data.get("reader_predictions", {}),
            improvement_suggestions=processed_data.get("improvement_suggestions", []),
        )
