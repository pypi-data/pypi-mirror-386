#!/usr/bin/env python3
"""高度文章リズム分析エンジン

手動Claude Code分析レベルの文章リズム・テンポ分析を実現する
ドメインサービス。文の長短バランス、読点配置、呼吸感を定量化。
"""

import re
from dataclasses import dataclass
from statistics import mean, stdev

from noveler.domain.value_objects.improvement_suggestion import ImprovementSuggestion


@dataclass
class RhythmAnalysisResult:
    """文章リズム分析結果"""

    overall_score: float
    short_sentence_ratio: float  # 短文比率
    medium_sentence_ratio: float  # 中文比率
    long_sentence_ratio: float  # 長文比率
    punctuation_density: float  # 読点密度
    rhythm_variation_score: float  # リズム変化スコア
    tempo_consistency: float  # テンポ一貫性
    breathing_points_score: float  # 呼吸点スコア
    problematic_lines: list[int]  # 問題のある行番号
    specific_suggestions: list[ImprovementSuggestion]

    def get_detailed_feedback(self) -> str:
        """詳細フィードバックを生成"""
        feedback_parts = []

        # 文長バランス評価
        if self.short_sentence_ratio < 0.2:
            feedback_parts.append("短文が不足しています。テンポを生むため、簡潔な文を追加してください。")
        elif self.short_sentence_ratio > 0.6:
            feedback_parts.append("短文が過多です。内容の深みを出すため、長めの文も織り交ぜてください。")

        # リズム変化評価
        if self.rhythm_variation_score < 60:
            feedback_parts.append("文章のリズムが単調です。文の長さに変化をつけて読みやすさを向上させてください。")

        # 読点密度評価
        if self.punctuation_density < 0.1:
            feedback_parts.append("読点が不足しています。適切な区切りで読者の理解を助けてください。")
        elif self.punctuation_density > 0.4:
            feedback_parts.append("読点が多すぎます。文の流れを阻害しない程度に調整してください。")

        return " ".join(feedback_parts) if feedback_parts else "文章リズムは良好です。"


class AdvancedRhythmAnalyzer:
    """高度文章リズム分析エンジン

    手動分析レベルの詳細なリズム・テンポ分析を実行。
    文の長短、読点配置、呼吸感を総合的に評価。
    """

    def __init__(self) -> None:
        """高度リズム分析エンジン初期化"""
        self._sentence_length_thresholds = {
            "short": 15,  # 15文字以下は短文
            "medium": 40,  # 16-40文字は中文
            "long": 40,  # 41文字以上は長文
        }
        self._ideal_ratios = {
            "short": 0.3,  # 理想短文比率
            "medium": 0.5,  # 理想中文比率
            "long": 0.2,  # 理想長文比率
        }

    def analyze_rhythm(self, content: str) -> RhythmAnalysisResult:
        """文章リズムの詳細分析

        Args:
            content: 分析対象テキスト

        Returns:
            RhythmAnalysisResult: リズム分析結果
        """
        sentences = self._extract_sentences(content)
        if len(sentences) < 3:
            return self._create_insufficient_data_result()

        # 文長分析
        sentence_lengths = [len(s.strip()) for s in sentences if s.strip()]
        length_ratios = self._calculate_length_ratios(sentence_lengths)

        # 読点密度分析
        punctuation_density = self._calculate_punctuation_density(content)

        # リズム変化分析
        rhythm_variation = self._analyze_rhythm_variation(sentence_lengths)

        # テンポ一貫性分析
        tempo_consistency = self._analyze_tempo_consistency(sentences)

        # 呼吸点分析
        breathing_score = self._analyze_breathing_points(content)

        # 問題箇所特定
        problematic_lines = self._identify_problematic_lines(content, sentences)

        # 具体的改善提案生成
        suggestions = self._generate_rhythm_suggestions(length_ratios, punctuation_density, rhythm_variation)

        # 総合スコア計算
        overall_score = self._calculate_overall_rhythm_score(
            length_ratios, punctuation_density, rhythm_variation, tempo_consistency, breathing_score
        )

        return RhythmAnalysisResult(
            overall_score=overall_score,
            short_sentence_ratio=length_ratios["short"],
            medium_sentence_ratio=length_ratios["medium"],
            long_sentence_ratio=length_ratios["long"],
            punctuation_density=punctuation_density,
            rhythm_variation_score=rhythm_variation,
            tempo_consistency=tempo_consistency,
            breathing_points_score=breathing_score,
            problematic_lines=problematic_lines,
            specific_suggestions=suggestions,
        )

    def _extract_sentences(self, content: str) -> list[str]:
        """文の抽出"""
        # 日本語の文境界を考慮した分割
        sentences = re.split(r"[。！？](?![」』）])", content)
        return [s.strip() for s in sentences if s.strip()]

    def _calculate_length_ratios(self, sentence_lengths: list[int]) -> dict[str, float]:
        """文長比率の計算"""
        if not sentence_lengths:
            return {"short": 0.0, "medium": 0.0, "long": 0.0}

        short_count = sum(1 for length in sentence_lengths if length <= self._sentence_length_thresholds["short"])
        long_count = sum(1 for length in sentence_lengths if length > self._sentence_length_thresholds["long"])
        medium_count = len(sentence_lengths) - short_count - long_count

        total = len(sentence_lengths)
        return {"short": short_count / total, "medium": medium_count / total, "long": long_count / total}

    def _calculate_punctuation_density(self, content: str) -> float:
        """読点密度の計算"""
        comma_count = content.count("、")
        char_count = len(content)
        return comma_count / char_count if char_count > 0 else 0.0

    def _analyze_rhythm_variation(self, sentence_lengths: list[int]) -> float:
        """リズム変化の分析"""
        if len(sentence_lengths) < 3:
            return 50.0

        # 連続する文の長さの変化を分析
        length_changes = []
        for i in range(1, len(sentence_lengths)):
            change = abs(sentence_lengths[i] - sentence_lengths[i - 1])
            length_changes.append(change)

        if not length_changes:
            return 50.0

        # 変化の標準偏差が大きいほど良いリズム
        avg_change = mean(length_changes)
        return min(100.0, avg_change * 2)  # スケーリング

    def _analyze_tempo_consistency(self, sentences: list[str]) -> float:
        """テンポ一貫性の分析"""
        if len(sentences) < 3:
            return 80.0

        # 各文の「テンポ感」を分析
        tempo_scores = []
        for sentence in sentences:
            # 短文・会話文は高テンポ
            tempo = 50.0
            if len(sentence) < 20:
                tempo += 20
            if "「" in sentence:
                tempo += 15
            if any(word in sentence for word in ["！", "？", "だ", "した"]):
                tempo += 10

            tempo_scores.append(min(100.0, tempo))

        # テンポの標準偏差が小さいほど一貫性が高い
        if len(tempo_scores) > 1:
            tempo_stdev = stdev(tempo_scores)
            consistency = max(0.0, 100.0 - tempo_stdev * 2)
        else:
            consistency = 80.0

        return consistency

    def _analyze_breathing_points(self, content: str) -> float:
        """呼吸点（自然な区切り）の分析"""
        lines = content.split("\n")
        paragraph_count = len([line for line in lines if line.strip()])

        if paragraph_count == 0:
            return 0.0

        # 段落区切り、読点、接続詞による呼吸点を評価
        breathing_points = 0

        # 段落区切りによる呼吸点
        empty_lines = content.count("\n\n")
        breathing_points += empty_lines * 10

        # 読点による呼吸点
        commas = content.count("、")
        breathing_points += commas * 2

        # 接続詞による呼吸点
        conjunctions = len(re.findall(r"(しかし|そして|だから|それで|ところが)", content))
        breathing_points += conjunctions * 5

        # 長さに対する適切性を評価
        content_length = len(content)
        if content_length > 0:
            breathing_density = breathing_points / (content_length / 100)
            return min(100.0, breathing_density * 20)

        return 50.0

    def _identify_problematic_lines(self, content: str, sentences: list[str]) -> list[int]:
        """問題のある行を特定"""
        lines = content.split("\n")
        problematic_lines = []

        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            # 極端に長い文（80文字以上）
            if len(line) > 80:
                problematic_lines.append(i)

            # 読点が多すぎる文（8個以上）
            if line.count("、") > 8:
                problematic_lines.append(i)

            # 単調な文末パターン
            if line.endswith(("だった。", "だった。", "だった。")):
                # 前後の行も同じパターンかチェック
                prev_line = lines[i - 2].strip() if i > 1 else ""
                next_line = lines[i].strip() if i < len(lines) else ""

                if prev_line.endswith("だった。") or next_line.endswith("だった。"):
                    problematic_lines.append(i)

        return problematic_lines

    def _generate_rhythm_suggestions(
        self, length_ratios: dict[str, float], punctuation_density: float, rhythm_variation: float
    ) -> list[ImprovementSuggestion]:
        """リズム改善提案の生成"""
        suggestions = []

        # 文長バランス提案
        if length_ratios["short"] < 0.2:
            suggestions.append(
                ImprovementSuggestion.create(
                    content="テンポ向上のため、短文（15文字以下）を増やしてください。例：「彼は振り返った。」",
                    suggestion_type="style",
                )
            )

        if length_ratios["long"] > 0.4:
            suggestions.append(
                ImprovementSuggestion.create(
                    content="読みやすさのため、長文を短く分割してください。読点で区切られる部分を独立した文にできます。",
                    suggestion_type="style",
                )
            )

        # 読点密度提案
        if punctuation_density < 0.1:
            suggestions.append(
                ImprovementSuggestion.create(
                    content="文の区切りを明確にするため、適切な位置に読点「、」を追加してください。",
                    suggestion_type="style",
                )
            )

        # リズム変化提案
        if rhythm_variation < 60:
            suggestions.append(
                ImprovementSuggestion.create(
                    content="文章のリズムに変化をつけてください。短文・中文・長文を効果的に組み合わせることで読者を飽きさせません。",
                    suggestion_type="enhancement",
                )
            )

        return suggestions

    def _calculate_overall_rhythm_score(
        self,
        length_ratios: dict[str, float],
        punctuation_density: float,
        rhythm_variation: float,
        tempo_consistency: float,
        breathing_score: float,
    ) -> float:
        """総合リズムスコアの計算"""

        # 文長バランス評価（30%重み）
        balance_score = 100.0
        for ratio_type, actual_ratio in length_ratios.items():
            ideal_ratio = self._ideal_ratios[ratio_type]
            deviation = abs(actual_ratio - ideal_ratio)
            balance_score -= deviation * 100  # 偏差をペナライズ

        balance_contribution = max(0.0, balance_score) * 0.3

        # 読点密度評価（20%重み）
        ideal_punctuation = 0.15  # 理想的な読点密度
        punctuation_deviation = abs(punctuation_density - ideal_punctuation)
        punctuation_contribution = max(0.0, 100.0 - punctuation_deviation * 200) * 0.2

        # リズム変化評価（25%重み）
        rhythm_contribution = rhythm_variation * 0.25

        # テンポ一貫性評価（15%重み）
        tempo_contribution = tempo_consistency * 0.15

        # 呼吸点評価（10%重み）
        breathing_contribution = breathing_score * 0.1

        final_score = (
            balance_contribution
            + punctuation_contribution
            + rhythm_contribution
            + tempo_contribution
            + breathing_contribution
        )

        return max(0.0, min(100.0, final_score))

    def _create_insufficient_data_result(self) -> RhythmAnalysisResult:
        """データ不足時の結果作成"""
        return RhythmAnalysisResult(
            overall_score=70.0,
            short_sentence_ratio=0.0,
            medium_sentence_ratio=0.0,
            long_sentence_ratio=0.0,
            punctuation_density=0.0,
            rhythm_variation_score=50.0,
            tempo_consistency=70.0,
            breathing_points_score=50.0,
            problematic_lines=[],
            specific_suggestions=[
                ImprovementSuggestion.create(
                    content="分析に十分なテキスト量がありません。より多くの文章でリズム分析の精度が向上します。",
                    suggestion_type="enhancement",
                )
            ],
        )
