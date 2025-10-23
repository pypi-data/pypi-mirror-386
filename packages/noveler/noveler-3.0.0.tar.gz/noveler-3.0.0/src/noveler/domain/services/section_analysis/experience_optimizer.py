"""読者体験最適化サービス

巨大なSectionBalanceOptimizerServiceから読者体験最適化機能を抽出。
エンゲージメント向上と読者満足度最適化を担当。
"""

from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
from typing import Any

from noveler.domain.interfaces.logger_service_protocol import ILoggerService


@dataclass
class ExperienceMetrics:
    """読者体験メトリクス"""

    engagement_levels: list[float]
    satisfaction_points: list[float]
    cognitive_load: list[float]
    emotional_journey: list[float]
    immersion_consistency: float
    overall_experience_score: float


@dataclass
class ExperienceOptimizationResult:
    """読者体験最適化結果"""

    optimized_sections: list[dict[str, Any]]
    experience_metrics: ExperienceMetrics
    recommendations: list[dict[str, Any]]
    experience_issues: list[str]
    improvement_score: float


class ExperienceOptimizer:
    """読者体験最適化サービス

    責任:
    - 読者エンゲージメント最適化
    - 認知負荷管理
    - 感情的な旅路の設計
    - 没入感の一貫性保持
    """

    def __init__(self, logger_service: ILoggerService | None = None) -> None:
        """読者体験最適化サービス初期化

        Args:
            logger_service: ロガーサービス
        """
        self._logger = logger_service

    def optimize_reader_experience(
        self,
        sections: list[dict[str, Any]],
        reader_preferences: dict[str, Any] | None = None,
        genre_constraints: dict[str, Any] | None = None,
        *,
        log: Callable[[str, str], None] | None = None,
    ) -> ExperienceOptimizationResult:
        """読者体験最適化実行

        Args:
            sections: セクション情報
            reader_preferences: 読者嗜好設定
            genre_constraints: ジャンル制約
            log: ログ収集用コールバック

        Returns:
            読者体験最適化結果
        """
        self._emit_log("info", "👥 読者体験最適化を開始...", log)

        reader_preferences = reader_preferences or {}
        genre_constraints = genre_constraints or {}

        # エンゲージメントレベル分析
        engagement_analysis = self._analyze_engagement_patterns(sections)

        # 認知負荷分析
        cognitive_load_analysis = self._analyze_cognitive_load(sections)

        # 感情的旅路分析
        emotional_journey_analysis = self._analyze_emotional_journey(sections)

        # 最適化実行
        optimized_sections = self._apply_experience_optimizations(
            sections,
            engagement_analysis,
            cognitive_load_analysis,
            emotional_journey_analysis,
            reader_preferences,
            genre_constraints,
        )

        # 最適化後のメトリクス計算
        experience_metrics = self._calculate_experience_metrics(optimized_sections)

        # 推奨事項の生成
        recommendations = self._generate_experience_recommendations(sections, optimized_sections, experience_metrics)

        # 問題点の特定
        experience_issues = self._identify_experience_issues(optimized_sections, experience_metrics)

        # 改善スコア計算
        improvement_score = self._calculate_improvement_score(sections, optimized_sections)

        return ExperienceOptimizationResult(
            optimized_sections=optimized_sections,
            experience_metrics=experience_metrics,
            recommendations=recommendations,
            experience_issues=experience_issues,
            improvement_score=improvement_score,
        )

    def _emit_log(
        self,
        level: str,
        message: str,
        log: Callable[[str, str], None] | None = None,
    ) -> None:
        """Emit log messages to callback and optional logger service."""
        if log is not None:
            with suppress(Exception):
                log(level, message)
        if self._logger is None:
            return
        log_method = getattr(self._logger, level, None)
        if callable(log_method):
            with suppress(Exception):  # pragma: no cover - logger misconfiguration
                log_method(message)

    def _analyze_engagement_patterns(self, sections: list[dict[str, Any]]) -> dict[str, Any]:
        """エンゲージメントパターン分析

        Args:
            sections: セクション情報

        Returns:
            エンゲージメント分析結果
        """
        engagement_levels = []
        engagement_variations = []

        for i, section in enumerate(sections):
            # 基本エンゲージメントレベル
            base_engagement = section.get("engagement_level", 0.5)

            # セクション特性による調整
            characteristics = section.get("characteristics", {})
            dialogue_bonus = characteristics.get("dialogue_ratio", 0.4) * 0.2
            action_bonus = characteristics.get("action_ratio", 0.3) * 0.15

            adjusted_engagement = min(1.0, base_engagement + dialogue_bonus + action_bonus)
            engagement_levels.append(adjusted_engagement)

            # 前セクションとの変化を分析
            if i > 0:
                variation = adjusted_engagement - engagement_levels[i - 1]
                engagement_variations.append(variation)

        return {
            "levels": engagement_levels,
            "variations": engagement_variations,
            "average_level": sum(engagement_levels) / len(engagement_levels) if engagement_levels else 0.5,
            "variation_smoothness": self._calculate_variation_smoothness(engagement_variations),
        }

    def _analyze_cognitive_load(self, sections: list[dict[str, Any]]) -> dict[str, Any]:
        """認知負荷分析

        Args:
            sections: セクション情報

        Returns:
            認知負荷分析結果
        """
        cognitive_loads = []

        for section in sections:
            # 基本認知負荷の計算
            complexity = section.get("complexity", "medium")
            complexity_score = {"low": 0.3, "medium": 0.6, "high": 0.9}.get(complexity, 0.6)

            # 長さによる負荷調整
            length = section.get("estimated_length", 1000)
            length_factor = min(1.0, length / 1500)  # 1500文字を基準とした負荷

            # コンテンツタイプによる調整
            characteristics = section.get("characteristics", {})
            description_ratio = characteristics.get("description_ratio", 0.2)
            internal_thought_ratio = characteristics.get("internal_thought_ratio", 0.1)

            # 描写と内的思考は認知負荷を上げる
            content_factor = 1.0 + (description_ratio * 0.3) + (internal_thought_ratio * 0.4)

            cognitive_load = complexity_score * length_factor * content_factor
            cognitive_loads.append(min(1.0, cognitive_load))

        return {
            "loads": cognitive_loads,
            "average_load": sum(cognitive_loads) / len(cognitive_loads) if cognitive_loads else 0.5,
            "peak_load": max(cognitive_loads) if cognitive_loads else 0.5,
            "load_distribution": self._analyze_load_distribution(cognitive_loads),
        }

    def _analyze_emotional_journey(self, sections: list[dict[str, Any]]) -> dict[str, Any]:
        """感情的旅路分析

        Args:
            sections: セクション情報

        Returns:
            感情的旅路分析結果
        """
        emotional_curve = []
        emotional_transitions = []

        for i, section in enumerate(sections):
            intensity = section.get("emotional_intensity", 0.5)
            emotional_curve.append(intensity)

            # 感情的遷移の分析
            if i > 0:
                transition = intensity - emotional_curve[i - 1]
                emotional_transitions.append(
                    {
                        "from_section": i - 1,
                        "to_section": i,
                        "intensity_change": transition,
                        "transition_type": self._classify_emotional_transition(transition),
                    }
                )

        return {
            "emotional_curve": emotional_curve,
            "transitions": emotional_transitions,
            "curve_smoothness": self._calculate_curve_smoothness(emotional_curve),
            "emotional_range": max(emotional_curve) - min(emotional_curve) if emotional_curve else 0.0,
        }

    def _apply_experience_optimizations(
        self,
        sections: list[dict[str, Any]],
        engagement_analysis: dict[str, Any],
        cognitive_load_analysis: dict[str, Any],
        emotional_journey_analysis: dict[str, Any],
        reader_preferences: dict[str, Any],
        genre_constraints: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """読者体験最適化の適用

        Args:
            sections: セクション情報
            engagement_analysis: エンゲージメント分析
            cognitive_load_analysis: 認知負荷分析
            emotional_journey_analysis: 感情的旅路分析
            reader_preferences: 読者嗜好
            genre_constraints: ジャンル制約

        Returns:
            最適化されたセクション
        """
        optimized_sections = []

        for i, section in enumerate(sections):
            optimized_section = section.copy()

            # エンゲージメント最適化
            optimized_section = self._optimize_section_engagement(optimized_section, i, engagement_analysis)

            # 認知負荷最適化
            optimized_section = self._optimize_cognitive_load(optimized_section, i, cognitive_load_analysis)

            # 感情的遷移最適化
            optimized_section = self._optimize_emotional_transition(optimized_section, i, emotional_journey_analysis)

            # 読者嗜好の適用
            optimized_section = self._apply_reader_preferences(optimized_section, reader_preferences)

            # ジャンル制約の適用
            optimized_section = self._apply_genre_constraints(optimized_section, genre_constraints)

            optimized_sections.append(optimized_section)

        return optimized_sections

    def _optimize_section_engagement(
        self, section: dict[str, Any], section_index: int, engagement_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """セクションエンゲージメント最適化"""
        engagement_levels = engagement_analysis.get("levels", [])

        if section_index < len(engagement_levels):
            current_engagement = engagement_levels[section_index]
            target_engagement = self._calculate_target_engagement(section_index, len(engagement_levels))

            if abs(current_engagement - target_engagement) > 0.1:
                section["target_engagement_level"] = target_engagement
                section["engagement_optimization_needed"] = True

                # エンゲージメント向上のための調整提案
                if target_engagement > current_engagement:
                    section["engagement_boost_suggestions"] = [
                        "対話を増やしてキャラクター間の関係性を強化",
                        "読者の関心を引く謎や疑問を提示",
                        "アクション要素を追加して緊張感を創出",
                    ]
                else:
                    section["engagement_balance_suggestions"] = [
                        "リフレクションの時間を設けて読者に余韻を与える",
                        "情報整理のための描写的な場面を追加",
                        "キャラクターの内面的な成長を描写",
                    ]

        return section

    def _optimize_cognitive_load(
        self, section: dict[str, Any], section_index: int, cognitive_load_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """認知負荷最適化"""
        cognitive_loads = cognitive_load_analysis.get("loads", [])

        if section_index < len(cognitive_loads):
            current_load = cognitive_loads[section_index]

            # 高すぎる認知負荷の調整
            if current_load > 0.8:
                section["cognitive_load_reduction_needed"] = True
                section["load_reduction_suggestions"] = [
                    "複雑な描写を簡潔に整理",
                    "情報の提示順序を最適化",
                    "理解しやすい文章構造に調整",
                ]

            # 低すぎる認知負荷の調整
            elif current_load < 0.3:
                section["cognitive_load_increase_needed"] = True
                section["load_increase_suggestions"] = [
                    "より詳細な描写で世界観を充実",
                    "キャラクターの心理描写を深化",
                    "背景情報を適度に追加",
                ]

        return section

    def _optimize_emotional_transition(
        self, section: dict[str, Any], section_index: int, emotional_journey_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """感情的遷移最適化"""
        transitions = emotional_journey_analysis.get("transitions", [])

        # 該当する遷移を検索
        relevant_transition = None
        for transition in transitions:
            if transition["to_section"] == section_index:
                relevant_transition = transition
                break

        if relevant_transition:
            relevant_transition["transition_type"]
            intensity_change = relevant_transition["intensity_change"]

            # 急激な変化の調整
            if abs(intensity_change) > 0.4:
                section["emotional_transition_smoothing_needed"] = True
                section["transition_smoothing_suggestions"] = [
                    "段階的な感情変化を挿入",
                    "遷移のための橋渡し要素を追加",
                    "キャラクターの感情変化の理由を明確化",
                ]

        return section

    def _apply_reader_preferences(self, section: dict[str, Any], reader_preferences: dict[str, Any]) -> dict[str, Any]:
        """読者嗜好の適用"""
        # 読者が好む要素の強化
        preferred_elements = reader_preferences.get("preferred_elements", [])

        for element in preferred_elements:
            if element == "dialogue":
                characteristics = section.get("characteristics", {})
                current_dialogue = characteristics.get("dialogue_ratio", 0.4)
                if current_dialogue < 0.5:
                    section["dialogue_enhancement_suggested"] = True

            elif element == "action":
                characteristics = section.get("characteristics", {})
                current_action = characteristics.get("action_ratio", 0.3)
                if current_action < 0.4:
                    section["action_enhancement_suggested"] = True

        return section

    def _apply_genre_constraints(self, section: dict[str, Any], genre_constraints: dict[str, Any]) -> dict[str, Any]:
        """ジャンル制約の適用"""
        genre = genre_constraints.get("genre")

        if genre == "romance":
            # ロマンス特化調整
            characteristics = section.get("characteristics", {})
            dialogue_ratio = characteristics.get("dialogue_ratio", 0.4)
            if dialogue_ratio < 0.5:
                section["genre_dialogue_boost_needed"] = True

        elif genre == "action":
            # アクション特化調整
            characteristics = section.get("characteristics", {})
            action_ratio = characteristics.get("action_ratio", 0.3)
            if action_ratio < 0.5:
                section["genre_action_boost_needed"] = True

        elif genre == "mystery":
            # ミステリー特化調整
            characteristics = section.get("characteristics", {})
            internal_thought_ratio = characteristics.get("internal_thought_ratio", 0.1)
            if internal_thought_ratio < 0.2:
                section["genre_mystery_thinking_boost_needed"] = True

        return section

    def _calculate_experience_metrics(self, sections: list[dict[str, Any]]) -> ExperienceMetrics:
        """読者体験メトリクス計算"""
        engagement_levels = [section.get("engagement_level", 0.5) for section in sections]
        emotional_intensities = [section.get("emotional_intensity", 0.5) for section in sections]

        # 満足度ポイントの計算
        satisfaction_points = self._calculate_satisfaction_points(sections)

        # 認知負荷の計算
        cognitive_load = self._calculate_section_cognitive_loads(sections)

        # 没入感一貫性の計算
        immersion_consistency = self._calculate_immersion_consistency(sections)

        # 全体体験スコア
        overall_score = (
            (
                sum(engagement_levels) / len(engagement_levels) * 0.3
                + sum(satisfaction_points) / len(satisfaction_points) * 0.3
                + (1.0 - sum(cognitive_load) / len(cognitive_load)) * 0.2  # 認知負荷は低い方が良い
                + immersion_consistency * 0.2
            )
            if sections
            else 0.5
        )

        return ExperienceMetrics(
            engagement_levels=engagement_levels,
            satisfaction_points=satisfaction_points,
            cognitive_load=cognitive_load,
            emotional_journey=emotional_intensities,
            immersion_consistency=immersion_consistency,
            overall_experience_score=overall_score,
        )

    def _calculate_satisfaction_points(self, sections: list[dict[str, Any]]) -> list[float]:
        """満足度ポイント計算"""
        satisfaction_points = []

        for section in sections:
            base_satisfaction = section.get("engagement_level", 0.5)

            # プロット要素による満足度向上
            plot_points = len(section.get("plot_points", []))
            plot_bonus = min(0.3, plot_points * 0.1)

            # バランスの良さによる満足度
            characteristics = section.get("characteristics", {})
            balance_score = self._calculate_content_balance_score(characteristics)

            satisfaction = min(1.0, base_satisfaction + plot_bonus + balance_score * 0.2)
            satisfaction_points.append(satisfaction)

        return satisfaction_points

    def _calculate_section_cognitive_loads(self, sections: list[dict[str, Any]]) -> list[float]:
        """セクション別認知負荷計算"""
        loads = []

        for section in sections:
            # 複雑さによる負荷
            complexity = section.get("complexity", "medium")
            complexity_load = {"low": 0.2, "medium": 0.5, "high": 0.8}.get(complexity, 0.5)

            # 長さによる負荷
            length = section.get("estimated_length", 1000)
            length_load = min(0.3, length / 2000)

            # 情報密度による負荷
            info_density = self._calculate_information_density(section)

            total_load = min(1.0, complexity_load + length_load + info_density)
            loads.append(total_load)

        return loads

    def _calculate_immersion_consistency(self, sections: list[dict[str, Any]]) -> float:
        """没入感一貫性計算"""
        if not sections:
            return 0.5

        # 文体の一貫性
        style_consistency = 0.8  # プレースホルダー値

        # テンポの一貫性
        pace_values = []
        pace_map = {"slow": 0.3, "medium": 0.6, "fast": 0.9}

        for section in sections:
            pacing = section.get("pacing_requirements", {})
            speed = pacing.get("speed", "medium")
            pace_values.append(pace_map.get(speed, 0.6))

        if len(pace_values) > 1:
            pace_variance = sum((pace_values[i + 1] - pace_values[i]) ** 2 for i in range(len(pace_values) - 1)) / (
                len(pace_values) - 1
            )
            pace_consistency = max(0.0, 1.0 - pace_variance)
        else:
            pace_consistency = 1.0

        return (style_consistency + pace_consistency) / 2

    def _generate_experience_recommendations(
        self,
        original_sections: list[dict[str, Any]],
        optimized_sections: list[dict[str, Any]],
        metrics: ExperienceMetrics,
    ) -> list[dict[str, Any]]:
        """読者体験改善推奨事項生成"""
        recommendations = []

        # エンゲージメントレベルの改善推奨
        if metrics.overall_experience_score < 0.7:
            recommendations.append(
                {
                    "category": "overall_experience",
                    "priority": "high",
                    "description": "全体的な読者体験スコアが低いため、包括的な改善が必要",
                    "suggestions": [
                        "キャラクター間の対話を増やして関係性を深化",
                        "読者の興味を引く謎や伏線を効果的に配置",
                        "感情的な起伏を適切に設計して飽きさせない工夫",
                    ],
                }
            )

        # 認知負荷の改善推奨
        high_load_sections = [i for i, load in enumerate(metrics.cognitive_load) if load > 0.8]
        if high_load_sections:
            recommendations.append(
                {
                    "category": "cognitive_load",
                    "priority": "medium",
                    "description": f"セクション {', '.join(map(str, high_load_sections))} の認知負荷が高すぎます",
                    "suggestions": [
                        "複雑な描写をより理解しやすく整理",
                        "情報の提示順序を最適化",
                        "適度な休息ポイントを設ける",
                    ],
                }
            )

        return recommendations

    def _identify_experience_issues(self, sections: list[dict[str, Any]], metrics: ExperienceMetrics) -> list[str]:
        """読者体験の問題点特定"""
        issues = []

        # エンゲージメントの低下
        low_engagement_sections = [i for i, level in enumerate(metrics.engagement_levels) if level < 0.4]
        if low_engagement_sections:
            issues.append(f"セクション {', '.join(map(str, low_engagement_sections))} でエンゲージメントが低下")

        # 認知負荷の問題
        if max(metrics.cognitive_load) > 0.9:
            issues.append("一部セクションで認知負荷が過度に高い")

        # 没入感の一貫性の問題
        if metrics.immersion_consistency < 0.6:
            issues.append("没入感の一貫性に問題あり")

        return issues

    def _calculate_improvement_score(
        self, original_sections: list[dict[str, Any]], optimized_sections: list[dict[str, Any]]
    ) -> float:
        """改善スコア計算"""
        # 最適化による改善度を計算
        original_metrics = self._calculate_experience_metrics(original_sections)
        optimized_metrics = self._calculate_experience_metrics(optimized_sections)

        improvement = optimized_metrics.overall_experience_score - original_metrics.overall_experience_score

        # 改善度を0-1スケールに正規化
        return max(0.0, min(1.0, (improvement + 0.5) / 1.0))

    # ヘルパーメソッド群
    def _calculate_variation_smoothness(self, variations: list[float]) -> float:
        """変動の滑らかさ計算"""
        if not variations:
            return 1.0

        # 急激な変動をペナルティとして計算
        abrupt_changes = sum(1 for var in variations if abs(var) > 0.3)
        return max(0.0, 1.0 - (abrupt_changes / len(variations)))

    def _analyze_load_distribution(self, loads: list[float]) -> dict[str, Any]:
        """負荷分布分析"""
        if not loads:
            return {"mean": 0.5, "std": 0.0, "peak_count": 0}

        mean_load = sum(loads) / len(loads)
        variance = sum((load - mean_load) ** 2 for load in loads) / len(loads)
        std_load = variance**0.5

        # ピーク負荷の数
        peak_count = sum(1 for load in loads if load > 0.8)

        return {"mean": mean_load, "std": std_load, "peak_count": peak_count}

    def _classify_emotional_transition(self, intensity_change: float) -> str:
        """感情的遷移の分類"""
        if intensity_change > 0.3:
            return "sharp_increase"
        if intensity_change > 0.1:
            return "gradual_increase"
        if intensity_change < -0.3:
            return "sharp_decrease"
        if intensity_change < -0.1:
            return "gradual_decrease"
        return "stable"

    def _calculate_curve_smoothness(self, curve: list[float]) -> float:
        """カーブの滑らかさ計算"""
        if len(curve) < 3:
            return 1.0

        # 2階差分による滑らかさ評価
        second_diffs = []
        for i in range(2, len(curve)):
            diff = curve[i] - 2 * curve[i - 1] + curve[i - 2]
            second_diffs.append(abs(diff))

        if not second_diffs:
            return 1.0

        avg_curvature = sum(second_diffs) / len(second_diffs)
        return max(0.0, 1.0 - avg_curvature * 5)  # スケーリング係数

    def _calculate_target_engagement(self, section_index: int, total_sections: int) -> float:
        """目標エンゲージメント計算"""
        # 理想的なエンゲージメントカーブ
        if total_sections == 1:
            return 0.7

        position = section_index / (total_sections - 1)

        # 上昇カーブで設計
        target = 0.5 + 0.3 * (position / 0.7) if position <= 0.7 else 0.8 + 0.1 * ((position - 0.7) / 0.3)

        return min(1.0, target)

    def _calculate_information_density(self, section: dict[str, Any]) -> float:
        """情報密度計算"""
        # プロットポイント、設定情報などの密度
        plot_points = len(section.get("plot_points", []))
        themes = len(section.get("themes", []))

        # 文字数あたりの情報量
        length = section.get("estimated_length", 1000)
        info_count = plot_points + themes

        return min(0.5, info_count / (length / 1000))  # 1000文字あたりの情報量

    def _calculate_content_balance_score(self, characteristics: dict[str, Any]) -> float:
        """コンテンツバランススコア計算"""
        dialogue_ratio = characteristics.get("dialogue_ratio", 0.4)
        action_ratio = characteristics.get("action_ratio", 0.3)
        description_ratio = characteristics.get("description_ratio", 0.2)
        internal_ratio = characteristics.get("internal_thought_ratio", 0.1)

        # 理想的な比率からの偏差を計算
        ideal_ratios = {"dialogue": 0.4, "action": 0.3, "description": 0.2, "internal": 0.1}
        current_ratios = {
            "dialogue": dialogue_ratio,
            "action": action_ratio,
            "description": description_ratio,
            "internal": internal_ratio,
        }

        total_deviation = sum(abs(current_ratios[key] - ideal_ratios[key]) for key in ideal_ratios)

        return max(0.0, 1.0 - total_deviation)
