"""微細A/B感情テストツール

複数の感情表現候補から最適解を選択するための
微細比較とランキング機能を提供する。
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .base_emotion_tool import BaseEmotionTool, EmotionToolInput, EmotionToolOutput


class EvaluationCriterion(Enum):
    """評価基準"""
    EMOTIONAL_IMPACT = "emotional_impact"      # 感情的インパクト
    READABILITY = "readability"               # 読みやすさ
    ORIGINALITY = "originality"               # 独創性
    GENRE_FITNESS = "genre_fitness"           # ジャンル適合性
    AUDIENCE_FITNESS = "audience_fitness"     # 読者層適合性
    STYLISTIC_CONSISTENCY = "stylistic_consistency"  # 文体一貫性


@dataclass
class VariantAnalysis:
    """表現候補分析結果"""
    variant_text: str
    scores: dict[str, float]  # 基準別スコア
    total_score: float
    strengths: list[str]
    weaknesses: list[str]
    detailed_metrics: dict[str, Any]


class MicroABEmotionTestTool(BaseEmotionTool):
    """微細A/B感情テストツール

    感情表現の複数候補を多角的に評価し、
    最適な表現を科学的に選択する支援を行う。
    """

    def __init__(self) -> None:
        super().__init__("micro_ab_emotion_test")
        self._initialize_evaluation_metrics()

    def _initialize_tool(self) -> None:
        """ツール初期化"""
        self.logger.info("A/Bテスト評価基準データベース初期化")

    def _initialize_evaluation_metrics(self) -> None:
        """評価指標の初期化"""
        # 基準別重要度（デフォルト）
        self.default_criterion_weights = {
            EvaluationCriterion.EMOTIONAL_IMPACT: 0.25,
            EvaluationCriterion.READABILITY: 0.20,
            EvaluationCriterion.ORIGINALITY: 0.15,
            EvaluationCriterion.GENRE_FITNESS: 0.15,
            EvaluationCriterion.AUDIENCE_FITNESS: 0.15,
            EvaluationCriterion.STYLISTIC_CONSISTENCY: 0.10
        }

        # 感情的インパクト評価パターン
        self.emotional_impact_patterns = {
            "strong_verbs": [r"震える|炸裂|突き刺す|激流|嵐", r"燃え上がる|凍りつく|砕ける"],
            "sensory_details": [r"熱い|冷たい|痛い|甘い|苦い", r"鋭い|重い|軽い|粗い|滑らか"],
            "physiological": [r"心臓|脈|息|血|汗", r"震え|痙攣|麻痺|硬直"],
            "metaphorical": [r"まるで|のような|のように|さながら", r"あたかも|いわば"]
        }

        # 読みやすさ評価指標
        self.readability_metrics = {
            "sentence_length": {"ideal_min": 10, "ideal_max": 25, "penalty_factor": 0.02},
            "kanji_ratio": {"ideal_min": 0.2, "ideal_max": 0.4, "penalty_factor": 0.5},
            "punctuation_balance": {"comma_frequency": 0.03, "period_frequency": 0.08},
            "repetition_penalty": {"same_word": 0.1, "similar_structure": 0.05}
        }

        # 独創性評価パターン
        self.originality_indicators = {
            "common_phrases": [  # よくある表現（減点対象）
                "心が躍る", "胸が熱い", "血が騒ぐ", "涙があふれる",
                "怒りがこみ上げる", "不安になる", "嬉しくなる"
            ],
            "creative_elements": {  # 創造的要素（加点対象）
                "synesthesia": r"音.*見える|色.*聞こえる|匂い.*響く",
                "unexpected_combination": r"静かな.*炎|冷たい.*情熱|透明な.*重さ",
                "novel_metaphor": r"デジタル.*心|量子.*愛|アルゴリズム.*感情"
            }
        }

        # ジャンル別特徴パターン
        self.genre_patterns = {
            "romance": {
                "preferred": [r"甘い|温かい|柔らか|優しい", r"包まれる|溶ける|響く"],
                "avoid": [r"冷酷|残酷|血|暴力"]
            },
            "mystery": {
                "preferred": [r"鋭い|冷たい|張り詰める|緊迫", r"影|闇|沈黙"],
                "avoid": [r"甘い|温かい|ふわふわ|キラキラ"]
            },
            "fantasy": {
                "preferred": [r"魔法|神秘|古代|永遠", r"光|闇|力|運命"],
                "avoid": [r"現実的|日常|普通|ありふれた"]
            }
        }

    async def execute(self, input_data: EmotionToolInput) -> EmotionToolOutput:
        """微細A/Bテストの実行

        Args:
            input_data: 比較対象の表現候補と評価設定

        Returns:
            A/B比較結果と推奨候補
        """
        metadata = input_data.metadata or {}

        variant_a = metadata.get("variant_a", "")
        variant_b = metadata.get("variant_b", "")
        evaluation_criteria = metadata.get("evaluation_criteria", list(self.default_criterion_weights.keys()))
        context_weight = metadata.get("context_weight", 1.0)

        if not variant_a or not variant_b:
            return self.create_error_output(
                "A/Bテストには2つの表現候補が必要です",
                ["variant_aまたはvariant_bが指定されていません"]
            )

        # 各候補の詳細分析
        analysis_a = await self._analyze_variant(variant_a, evaluation_criteria, metadata)
        analysis_b = await self._analyze_variant(variant_b, evaluation_criteria, metadata)

        # 比較評価実行
        comparison_result = self._compare_variants(analysis_a, analysis_b, context_weight)

        # ハイブリッド提案生成
        hybrid_suggestion = self._generate_hybrid_suggestion(analysis_a, analysis_b)

        analysis = {
            "variant_a_analysis": {
                "text": analysis_a.variant_text,
                "total_score": analysis_a.total_score,
                "criterion_scores": analysis_a.scores,
                "strengths": analysis_a.strengths,
                "weaknesses": analysis_a.weaknesses
            },
            "variant_b_analysis": {
                "text": analysis_b.variant_text,
                "total_score": analysis_b.total_score,
                "criterion_scores": analysis_b.scores,
                "strengths": analysis_b.strengths,
                "weaknesses": analysis_b.weaknesses
            },
            "winner": comparison_result["winner"],
            "score_difference": comparison_result["score_difference"],
            "confidence_level": comparison_result["confidence"],
            "detailed_comparison": comparison_result["details"]
        }

        suggestions = [
            f"推奨候補: {comparison_result['winner']}",
            f"信頼度: {comparison_result['confidence']}",
            comparison_result["reasoning"],
            f"ハイブリッド提案: {hybrid_suggestion}"
        ]

        # 総合スコア（勝者のスコア）
        winner_analysis = analysis_a if comparison_result["winner"] == "A" else analysis_b
        score = winner_analysis.total_score

        return self.create_success_output(
            score=score,
            analysis=analysis,
            suggestions=suggestions,
            metadata={
                "variants_compared": 2,
                "winner": comparison_result["winner"],
                "confidence": comparison_result["confidence"],
                "hybrid_available": bool(hybrid_suggestion)
            }
        )

    async def _analyze_variant(self, text: str, criteria: list[str],
                             metadata: dict[str, Any]) -> VariantAnalysis:
        """表現候補の詳細分析

        Args:
            text: 分析対象テキスト
            criteria: 評価基準リスト
            metadata: 評価コンテキスト

        Returns:
            分析結果
        """
        scores = {}
        strengths = []
        weaknesses = []
        detailed_metrics = {}

        # 感情的インパクト評価
        if EvaluationCriterion.EMOTIONAL_IMPACT in criteria:
            impact_score = self._evaluate_emotional_impact(text)
            scores["emotional_impact"] = impact_score
            detailed_metrics["emotional_impact"] = self._get_impact_details(text)

            if impact_score >= 75:
                strengths.append("強い感情的インパクト")
            elif impact_score < 50:
                weaknesses.append("感情的インパクトが弱い")

        # 読みやすさ評価
        if EvaluationCriterion.READABILITY in criteria:
            readability_score = self._evaluate_readability(text)
            scores["readability"] = readability_score
            detailed_metrics["readability"] = self._get_readability_details(text)

            if readability_score >= 80:
                strengths.append("優れた読みやすさ")
            elif readability_score < 60:
                weaknesses.append("読みにくい構造")

        # 独創性評価
        if EvaluationCriterion.ORIGINALITY in criteria:
            originality_score = self._evaluate_originality(text)
            scores["originality"] = originality_score
            detailed_metrics["originality"] = self._get_originality_details(text)

            if originality_score >= 70:
                strengths.append("独創的な表現")
            elif originality_score < 40:
                weaknesses.append("ありきたりな表現")

        # ジャンル適合性評価
        if EvaluationCriterion.GENRE_FITNESS in criteria:
            genre = metadata.get("genre")
            fitness_score = self._evaluate_genre_fitness(text, genre)
            scores["genre_fitness"] = fitness_score
            detailed_metrics["genre_fitness"] = {"genre": genre, "fitness": fitness_score}

            if fitness_score >= 75:
                strengths.append(f"{genre}ジャンルに適合")
            elif fitness_score < 50:
                weaknesses.append(f"{genre}ジャンルに不適合")

        # 読者層適合性評価
        if EvaluationCriterion.AUDIENCE_FITNESS in criteria:
            audience = metadata.get("target_audience")
            audience_score = self._evaluate_audience_fitness(text, audience)
            scores["audience_fitness"] = audience_score

            if audience_score >= 75:
                strengths.append(f"{audience}読者に適合")
            elif audience_score < 50:
                weaknesses.append(f"{audience}読者に不適合")

        # 文体一貫性評価
        if EvaluationCriterion.STYLISTIC_CONSISTENCY in criteria:
            consistency_score = self._evaluate_stylistic_consistency(text)
            scores["stylistic_consistency"] = consistency_score

            if consistency_score >= 80:
                strengths.append("文体の一貫性")
            elif consistency_score < 60:
                weaknesses.append("文体の不一致")

        # 重み付き総合スコア計算
        weights = self.default_criterion_weights
        total_score = sum(
            scores.get(criterion.value, 50) * weights.get(criterion, 0.1)
            for criterion in EvaluationCriterion
        )

        return VariantAnalysis(
            variant_text=text,
            scores=scores,
            total_score=total_score,
            strengths=strengths,
            weaknesses=weaknesses,
            detailed_metrics=detailed_metrics
        )

    def _evaluate_emotional_impact(self, text: str) -> float:
        """感情的インパクトの評価

        Args:
            text: 評価対象テキスト

        Returns:
            インパクトスコア（0-100）
        """
        score = 50  # ベーススコア

        # 強い動詞の使用
        for pattern_list in self.emotional_impact_patterns.values():
            for pattern in pattern_list:
                matches = len(re.findall(pattern, text))
                score += matches * 5  # マッチごとに5点加算

        # 生理学的描写の存在
        physio_matches = len(re.findall(r"心臓|脈|息|血|汗|震え", text))
        score += physio_matches * 8

        # 比喻表現の使用
        metaphor_matches = len(re.findall(r"のような|のように|まるで|あたかも", text))
        score += metaphor_matches * 6

        return min(100, score)

    def _evaluate_readability(self, text: str) -> float:
        """読みやすさの評価

        Args:
            text: 評価対象テキスト

        Returns:
            読みやすさスコア（0-100）
        """
        score = 80  # ベーススコア

        # 文の長さ評価
        sentences = re.split(r"[。！？]", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if sentences:
            avg_length = sum(len(s) for s in sentences) / len(sentences)
            metrics = self.readability_metrics["sentence_length"]

            if avg_length < metrics["ideal_min"] or avg_length > metrics["ideal_max"]:
                penalty = abs(avg_length - (metrics["ideal_min"] + metrics["ideal_max"]) / 2)
                score -= penalty * metrics["penalty_factor"]

        # 漢字比率評価
        kanji_count = len(re.findall(r"[一-龯]", text))
        total_chars = len(text)
        kanji_ratio = kanji_count / max(total_chars, 1)

        metrics = self.readability_metrics["kanji_ratio"]
        if kanji_ratio < metrics["ideal_min"] or kanji_ratio > metrics["ideal_max"]:
            score -= abs(kanji_ratio - 0.3) * 100 * metrics["penalty_factor"]

        return max(0, min(100, score))

    def _evaluate_originality(self, text: str) -> float:
        """独創性の評価

        Args:
            text: 評価対象テキスト

        Returns:
            独創性スコア（0-100）
        """
        score = 60  # ベーススコア

        # 一般的表現の減点
        for common_phrase in self.originality_indicators["common_phrases"]:
            if common_phrase in text:
                score -= 15

        # 創造的要素の加点
        for element_type, pattern in self.originality_indicators["creative_elements"].items():
            matches = len(re.findall(pattern, text))
            if matches > 0:
                if element_type == "synesthesia":
                    score += 20  # 共感覚は高得点
                elif element_type == "unexpected_combination":
                    score += 15
                elif element_type == "novel_metaphor":
                    score += 25  # 新奇比喩は最高得点

        return max(0, min(100, score))

    def _evaluate_genre_fitness(self, text: str, genre: str | None) -> float:
        """ジャンル適合性の評価

        Args:
            text: 評価対象テキスト
            genre: ジャンル名

        Returns:
            適合性スコア（0-100）
        """
        if not genre or genre not in self.genre_patterns:
            return 50  # 中立スコア

        score = 50
        patterns = self.genre_patterns[genre]

        # 推奨パターンの加点
        for pattern_list in patterns["preferred"]:
            matches = len(re.findall(pattern_list, text))
            score += matches * 10

        # 避けるべきパターンの減点
        for pattern_list in patterns["avoid"]:
            matches = len(re.findall(pattern_list, text))
            score -= matches * 15

        return max(0, min(100, score))

    def _evaluate_audience_fitness(self, text: str, audience: str | None) -> float:
        """読者層適合性の評価

        Args:
            text: 評価対象テキスト
            audience: 対象読者層

        Returns:
            適合性スコア（0-100）
        """
        # 簡化実装（実際にはより詳細な分析が必要）
        if not audience:
            return 50

        score = 60

        # 年齢層に応じた語彙レベルチェック
        if audience == "teen":
            # 難しい漢字や表現の減点
            difficult_patterns = [r"憂鬱|慚愧|懺悔|慙惶", r"恍惚|茫然|唖然"]
            for pattern in difficult_patterns:
                matches = len(re.findall(pattern, text))
                score -= matches * 10
        elif audience == "adult":
            # 幼稚な表現の減点
            childish_patterns = [r"すごく|とっても|めちゃくちゃ|びっくり"]
            for pattern in childish_patterns:
                matches = len(re.findall(pattern, text))
                score -= matches * 5

        return max(0, min(100, score))

    def _evaluate_stylistic_consistency(self, text: str) -> float:
        """文体一貫性の評価

        Args:
            text: 評価対象テキスト

        Returns:
            一貫性スコア（0-100）
        """
        # 簡化実装：敬語レベルの一貫性チェック
        formal_patterns = [r"です|ます|であります|ございます"]
        casual_patterns = [r"だ|である|だよ|だね|じゃん"]

        formal_count = sum(len(re.findall(pattern, text)) for pattern in formal_patterns)
        casual_count = sum(len(re.findall(pattern, text)) for pattern in casual_patterns)

        if formal_count == 0 and casual_count == 0:
            return 70  # 中立的な文体

        total = formal_count + casual_count
        if total == 0:
            return 70

        # 混在度が高いほどスコアが低い
        mix_ratio = min(formal_count, casual_count) / total
        consistency_score = 100 - (mix_ratio * 60)  # 混在があると減点

        return max(40, consistency_score)

    def _get_impact_details(self, text: str) -> dict[str, Any]:
        """感情的インパクトの詳細データ取得"""
        return {
            "strong_verb_count": len(re.findall(r"震える|炸裂|突き刺す|燃え上がる", text)),
            "physiological_count": len(re.findall(r"心臓|脈|息|血|汗", text)),
            "metaphor_count": len(re.findall(r"のような|のように|まるで", text))
        }

    def _get_readability_details(self, text: str) -> dict[str, Any]:
        """読みやすさの詳細データ取得"""
        sentences = re.split(r"[。！？]", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        return {
            "sentence_count": len(sentences),
            "average_sentence_length": sum(len(s) for s in sentences) / max(len(sentences), 1),
            "kanji_ratio": len(re.findall(r"[一-龯]", text)) / max(len(text), 1),
            "character_count": len(text)
        }

    def _get_originality_details(self, text: str) -> dict[str, Any]:
        """独創性の詳細データ取得"""
        return {
            "common_phrase_count": sum(1 for phrase in self.originality_indicators["common_phrases"] if phrase in text),
            "synesthesia_detected": len(re.findall(r"音.*見える|色.*聞こえる", text)) > 0,
            "novel_metaphor_detected": len(re.findall(r"デジタル.*心|量子.*愛", text)) > 0
        }

    def _compare_variants(self, analysis_a: VariantAnalysis,
                         analysis_b: VariantAnalysis,
                         context_weight: float) -> dict[str, Any]:
        """候補の比較評価

        Args:
            analysis_a: 候補Aの分析結果
            analysis_b: 候補Bの分析結果
            context_weight: 文脈重要度

        Returns:
            比較結果
        """
        score_diff = analysis_a.total_score - analysis_b.total_score

        # 文脈重要度による調整
        adjusted_diff = score_diff * context_weight

        # 勝者決定
        if abs(adjusted_diff) < 3:  # 3点以下の差は引き分け
            winner = "tie"
            confidence = "低"
        elif adjusted_diff > 0:
            winner = "A"
            confidence = "高" if abs(adjusted_diff) > 10 else "中"
        else:
            winner = "B"
            confidence = "高" if abs(adjusted_diff) > 10 else "中"

        # 詳細な比較理由
        reasoning = self._generate_comparison_reasoning(analysis_a, analysis_b, winner)

        return {
            "winner": winner,
            "score_difference": abs(adjusted_diff),
            "confidence": confidence,
            "reasoning": reasoning,
            "details": {
                "variant_a_total": analysis_a.total_score,
                "variant_b_total": analysis_b.total_score,
                "context_adjusted_diff": adjusted_diff
            }
        }

    def _generate_comparison_reasoning(self, analysis_a: VariantAnalysis,
                                     analysis_b: VariantAnalysis,
                                     winner: str) -> str:
        """比較理由の生成

        Args:
            analysis_a: 候補Aの分析
            analysis_b: 候補Bの分析
            winner: 勝者

        Returns:
            比較理由の説明文
        """
        if winner == "tie":
            return "両候補の品質が拮抗しており、文脈や好みに応じて選択してください"

        winner_analysis = analysis_a if winner == "A" else analysis_b
        loser_analysis = analysis_b if winner == "A" else analysis_a

        # 主な勝因を特定
        score_gaps = {}
        for criterion in winner_analysis.scores:
            winner_score = winner_analysis.scores.get(criterion, 0)
            loser_score = loser_analysis.scores.get(criterion, 0)
            score_gaps[criterion] = winner_score - loser_score

        # 最も差が大きい基準を特定
        max_gap_criterion = max(score_gaps.items(), key=lambda x: abs(x[1]))

        reason = f"候補{winner}が{max_gap_criterion[0]}で{abs(max_gap_criterion[1]):.1f}点上回っています"

        # 勝者の主要な強み追加
        if winner_analysis.strengths:
            reason += f"。特に「{winner_analysis.strengths[0]}」が優秀です"

        return reason

    def _generate_hybrid_suggestion(self, analysis_a: VariantAnalysis,
                                  analysis_b: VariantAnalysis) -> str:
        """ハイブリッド提案の生成

        Args:
            analysis_a: 候補Aの分析
            analysis_b: 候補Bの分析

        Returns:
            ハイブリッド提案文
        """
        # 各候補の最高スコア基準を特定
        a_best = max(analysis_a.scores.items(), key=lambda x: x[1])
        b_best = max(analysis_b.scores.items(), key=lambda x: x[1])

        if a_best[0] != b_best[0]:
            return f"候補Aの{a_best[0]}要素と候補Bの{b_best[0]}要素を組み合わせることで、より優れた表現になる可能性があります"
        # 同じ基準が最高の場合は、2番目を比較
        a_scores = sorted(analysis_a.scores.items(), key=lambda x: x[1], reverse=True)
        b_scores = sorted(analysis_b.scores.items(), key=lambda x: x[1], reverse=True)

        if len(a_scores) > 1 and len(b_scores) > 1:
            return f"候補Aの{a_scores[0][0]}と候補Bの{b_scores[1][0]}を融合してみてください"

        return "両候補の優れた要素を組み合わせることで、さらに改善できる可能性があります"
