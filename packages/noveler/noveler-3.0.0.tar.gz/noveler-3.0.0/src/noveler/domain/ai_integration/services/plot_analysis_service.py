#!/usr/bin/env python3

"""Domain.ai_integration.services.plot_analysis_service
Where: Domain service performing detailed plot analysis for AI integration.
What: Evaluates plot structures against benchmarks and extracts comparative metrics.
Why: Supplies reusable plot analysis logic for AI-assisted evaluation workflows.
"""

from __future__ import annotations

"""プロット分析ドメインサービス

プロット内容の評価ロジックを実装
"""


from typing import Any

from noveler.domain.ai_integration.value_objects.analysis_result import AnalysisResult, ImprovementPoint, StrengthPoint
from noveler.domain.ai_integration.value_objects.plot_score import PlotScore


class PlotAnalysisService:
    """プロット分析サービス

    各観点からプロットを評価し、総合的な分析結果を生成
    """

    # 評価基準定数
    BASE_SCORE = 50
    ELEMENT_SCORE = 10
    DETAIL_SCORE = 5
    MOTIVATION_SCORE = 15
    ARC_SCORE = 10
    CONFLICT_SCORE = 10
    ANTAGONIST_MOTIVATION_SCORE = 10
    RELATIONSHIP_SCORE = 5
    THEME_BASE_SCORE = 60
    MAIN_THEME_SCORE = 20
    SUB_THEME_SCORE = 10
    MAX_SUB_THEME_SCORE = 20
    HIGH_SCORE_THRESHOLD = 80
    LOW_SCORE_THRESHOLD = 70
    WEIGHT_STRUCTURE = 0.35
    WEIGHT_CHARACTERS = 0.35
    WEIGHT_THEMES = 0.30

    def analyze(self, plot_content: dict[str, Any]) -> AnalysisResult:
        """プロット全体を分析

        Args:
            plot_content: プロットのYAMLコンテンツ

        Returns:
            分析結果
        """
        # 各カテゴリーの評価
        structure_score = self.evaluate_structure(plot_content.get("structure", {}))
        character_score = self.evaluate_characters(plot_content.get("characters", {}))
        theme_score = self.evaluate_themes(plot_content.get("themes", {}))

        # 重み付け平均で総合スコアを計算
        total_score = self._calculate_weighted_score(
            {
                "structure": (structure_score, self.WEIGHT_STRUCTURE),
                "characters": (character_score, self.WEIGHT_CHARACTERS),
                "themes": (theme_score, self.WEIGHT_THEMES),
            },
        )

        # 強みと改善点を特定
        strengths = self._identify_strengths({"構成": structure_score, "キャラクター": character_score})

        improvements = self._identify_improvements({"構成": structure_score, "キャラクター": character_score})

        # 総合アドバイスを生成
        advice = self._generate_overall_advice(total_score, strengths, improvements)

        return AnalysisResult(
            total_score=total_score,
            strengths=strengths,
            improvements=improvements,
            overall_advice=advice,
        )

    def evaluate_structure(self, structure_data: dict[str, Any]) -> PlotScore:
        """構成を評価

        起承転結、ペーシング、クライマックスの構築を評価
        """
        score = 50  # 基準点

        # 起承転結の要素チェック
        required_elements = ["setup", "development", "climax", "resolution"]
        present_elements = sum(1 for elem in required_elements if elem in structure_data)
        score += present_elements * 10

        # 各要素の充実度をチェック
        if "setup" in structure_data and structure_data["setup"].get("description"):
            score += 5

        if "development" in structure_data:
            events = structure_data["development"].get("events", [])
            MIN_EVENTS_FOR_BONUS = 3
            if len(events) >= MIN_EVENTS_FOR_BONUS:
                score += 10
            elif len(events) >= 1:
                score += 5

        if "climax" in structure_data and structure_data["climax"].get("description"):
            score += 5

        if "resolution" in structure_data and structure_data["resolution"].get("description"):
            score += 5

        # スコアを0-100の範囲に正規化
        return PlotScore(min(100, max(0, score)))

    def evaluate_characters(self, character_data: dict[str, Any]) -> PlotScore:
        """キャラクターを評価

        動機の明確さ、キャラクターアーク、関係性を評価
        """
        score = 50  # 基準点

        # 主人公の評価
        if "protagonist" in character_data or "main" in character_data:
            protagonist_data: dict[str, Any] = character_data.get("protagonist") or character_data.get("main", {}).get(
                "protagonist",
                {},
            )

            if protagonist_data.get("motivation"):
                score += 15

            if protagonist_data.get("arc"):
                score += self.ARC_SCORE

            if protagonist_data.get("conflicts"):
                score += self.CONFLICT_SCORE

        # 敵対者の評価
        if "antagonist" in character_data:
            antagonist_data: dict[str, Any] = character_data["antagonist"]

            if antagonist_data.get("motivation"):
                score += self.ANTAGONIST_MOTIVATION_SCORE

            if antagonist_data.get("relationship"):
                score += self.RELATIONSHIP_SCORE

        return PlotScore(min(100, max(0, score)))

    def evaluate_themes(self, theme_data: dict[str, Any]) -> PlotScore:
        """テーマを評価

        テーマの一貫性、明確さ、深さを評価
        """
        score = self.THEME_BASE_SCORE  # 基準点

        if theme_data.get("main_theme"):
            score += self.MAIN_THEME_SCORE

        sub_themes = theme_data.get("sub_themes", [])
        if sub_themes:
            score += min(self.MAX_SUB_THEME_SCORE, len(sub_themes) * self.SUB_THEME_SCORE)

        return PlotScore(min(100, max(0, score)))

    def _calculate_weighted_score(self, scores: dict[str, tuple[PlotScore, float]]) -> PlotScore:
        """重み付け平均スコアを計算"""
        total = 0.0
        total_weight = 0.0

        for score, weight in scores.values():
            total += score.value * weight
            total_weight += weight

        if total_weight > 0:
            return PlotScore(int(total / total_weight))
        return PlotScore(0)

    def _identify_strengths(self, scores: dict[str, PlotScore]) -> list[StrengthPoint]:
        """強みを特定(80点以上)"""
        strengths = []

        for category, score in scores.items():
            if score.value >= self.HIGH_SCORE_THRESHOLD:
                description = f"{category}が優れている"
                strengths.append(StrengthPoint(description, score.value))

        return strengths

    def _identify_improvements(self, scores: dict[str, PlotScore]) -> list[ImprovementPoint]:
        """改善点を特定(70点未満)"""
        improvements = []

        suggestions = {
            "構成": "起承転結を明確にし、各パートの役割を強化してください",
            "キャラクター": "主人公の動機と成長をより明確に描写してください",
            "テーマ": "作品を通じて伝えたいメッセージを一貫させてください",
        }

        for category, score in scores.items():
            if score.value < self.LOW_SCORE_THRESHOLD:
                description = f"{category}の改善が必要"
                suggestion = suggestions.get(category, "より詳細な設定を追加してください")
                improvements.append(ImprovementPoint(description, score.value, suggestion))

        return improvements

    def _generate_overall_advice(
        self, total_score: PlotScore, strengths: list[StrengthPoint], improvements: list[ImprovementPoint]
    ) -> str:
        """総合的なアドバイスを生成"""
        if total_score.value >= self.HIGH_SCORE_THRESHOLD:
            base_advice = "素晴らしいプロットです。"
        elif total_score.value >= self.LOW_SCORE_THRESHOLD:
            base_advice = "良いプロットですが、いくつか改善の余地があります。"
        elif total_score.value >= self.THEME_BASE_SCORE:
            base_advice = "基本的な要素は揃っていますが、さらなる工夫が必要です。"
        else:
            base_advice = "プロットの基本構造を見直すことをお勧めします。"

        if strengths:
            base_advice += f" 特に{strengths[0].description.replace('が優れている', '')}の部分が良くできています。"

        if improvements:
            base_advice += (
                f" {improvements[0].description.replace('の改善が必要', '')}を強化することで、さらに良くなるでしょう。"
            )

        return base_advice
