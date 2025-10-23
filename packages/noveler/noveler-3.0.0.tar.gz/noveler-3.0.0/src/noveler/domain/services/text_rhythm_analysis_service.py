#!/usr/bin/env python3
"""文章リズム・読みやすさ分析サービス

各文の文字数分析、連続パターン検出、視覚化機能を提供する
高精度な文章リズム分析システム
"""

import re
import statistics
from typing import Any

from noveler.domain.value_objects.text_rhythm_analysis import (
    RhythmIssue,
    RhythmIssueType,
    RhythmSeverity,
    RhythmStatistics,
    SentenceAnalysis,
    TextRhythmReport,
)


class TextRhythmAnalysisService:
    """文章リズム分析サービス

    文字数の詳細分析、問題パターンの検出、
    読みやすさの総合評価を行う
    """

    def __init__(self) -> None:
        """初期化"""
        # 文分割パターン（日本語に最適化）
        self.sentence_pattern = re.compile(r"[。！？\n]+")

        # 会話文パターン
        self.dialogue_pattern = re.compile(r"「[^」]*」")

        # 文末パターン
        self.ending_patterns = {
            "。": "declarative",  # 平叙文
            "！": "exclamatory",  # 感嘆文
            "？": "interrogative",  # 疑問文
            "た": "past",  # 過去形
            "る": "present",  # 現在形
            "だ": "assertive",  # 断定
        }

    def analyze_text_rhythm(self, content: str) -> TextRhythmReport:
        """文章リズムの総合分析

        Args:
            content: 分析対象テキスト

        Returns:
            TextRhythmReport: 分析結果レポート
        """
        # 1. 文の分析
        sentences = self._analyze_sentences(content)

        # 2. 統計情報の計算
        statistics_data: dict[str, Any] = self._calculate_statistics(sentences)

        # 3. 問題の検出
        issues = self._detect_rhythm_issues(sentences)

        # 4. 総合スコアの計算
        overall_score = self._calculate_overall_score(statistics_data, issues)

        # 5. 読みやすさランクの決定
        readability_grade = self._determine_readability_grade(overall_score)

        return TextRhythmReport(
            sentences=sentences,
            statistics=statistics_data,
            issues=issues,
            overall_score=overall_score,
            readability_grade=readability_grade,
        )

    def _analyze_sentences(self, content: str) -> list[SentenceAnalysis]:
        """個別文の詳細分析

        Args:
            content: 分析対象テキスト

        Returns:
            list[SentenceAnalysis]: 各文の分析結果
        """
        # テキストのクリーンアップ
        cleaned_content = self._clean_text(content)

        # 文の分割
        sentences_raw = self._split_into_sentences(cleaned_content)

        sentence_analyses = []
        for i, sentence_text in enumerate(sentences_raw):
            if not sentence_text.strip():
                continue

            analysis = SentenceAnalysis(
                index=i,
                content=sentence_text.strip(),
                character_count=len(sentence_text.strip()),
                is_dialogue=self._is_dialogue(sentence_text),
                sentence_type=self._determine_sentence_type(sentence_text),
                ending_pattern=self._extract_ending_pattern(sentence_text),
            )

            sentence_analyses.append(analysis)

        return sentence_analyses

    def _clean_text(self, content: str) -> str:
        """テキストのクリーンアップ"""
        # Markdownヘッダーの除去
        content = re.sub(r"^#+\s.*$", "", content, flags=re.MULTILINE)
        # 空行の正規化
        content = re.sub(r"\n\s*\n", "\n", content)

        # 全角スペースの正規化
        content = re.sub(r"　+", "　", content)

        return content.strip()

    def _split_into_sentences(self, content: str) -> list[str]:
        """文への分割"""
        # 改行で分割してから、さらに句点等で分割
        lines = content.split("\n")
        sentences = []

        for line in lines:
            if not line.strip():
                continue

            # 句点等での分割
            parts = self.sentence_pattern.split(line)

            for part in parts:
                if part.strip():
                    sentences.append(part.strip())

        return sentences

    def _is_dialogue(self, sentence: str) -> bool:
        """会話文の判定"""
        return bool(self.dialogue_pattern.search(sentence))

    def _determine_sentence_type(self, sentence: str) -> str:
        """文種別の判定"""
        if sentence.endswith("？"):
            return "interrogative"
        if sentence.endswith("！"):
            return "exclamatory"
        if sentence.endswith("。"):
            return "declarative"
        return "fragment"

    def _extract_ending_pattern(self, sentence: str) -> str:
        """文末パターンの抽出"""
        if len(sentence) < 2:
            return "unknown"

        # 最後の2文字をチェック
        ending = sentence[-2:]

        for pattern, pattern_type in self.ending_patterns.items():
            if pattern in ending:
                return pattern_type

        return "other"

    def _calculate_statistics(self, sentences: list[SentenceAnalysis]) -> RhythmStatistics:
        """統計情報の計算"""
        if not sentences:
            return RhythmStatistics(
                total_sentences=0,
                average_length=0.0,
                median_length=0.0,
                std_deviation=0.0,
                min_length=0,
                max_length=0,
                very_short_count=0,
                short_count=0,
                medium_count=0,
                long_count=0,
                very_long_count=0,
                length_variance=0.0,
                rhythm_score=0.0,
            )

        lengths = [s.character_count for s in sentences]

        # 基本統計
        avg_length = statistics.mean(lengths)
        median_length = statistics.median(lengths)
        std_dev = statistics.stdev(lengths) if len(lengths) > 1 else 0.0

        # 分布の計算
        very_short = sum(1 for s in sentences if s.character_count <= 15)
        short = sum(1 for s in sentences if 16 <= s.character_count <= 25)
        medium = sum(1 for s in sentences if 26 <= s.character_count <= 40)
        long_sentences = sum(1 for s in sentences if 41 <= s.character_count <= 60)
        very_long = sum(1 for s in sentences if s.character_count >= 61)

        # バラエティスコアの計算
        length_variance = self._calculate_length_variance(lengths)
        rhythm_score = self._calculate_rhythm_score(lengths, length_variance)

        return RhythmStatistics(
            total_sentences=len(sentences),
            average_length=avg_length,
            median_length=median_length,
            std_deviation=std_dev,
            min_length=min(lengths),
            max_length=max(lengths),
            very_short_count=very_short,
            short_count=short,
            medium_count=medium,
            long_count=long_sentences,
            very_long_count=very_long,
            length_variance=length_variance,
            rhythm_score=rhythm_score,
        )

    def _calculate_length_variance(self, lengths: list[int]) -> float:
        """文字数のバラエティ度計算"""
        if len(lengths) <= 1:
            return 0.0

        # 正規化された標準偏差
        mean_length = statistics.mean(lengths)
        if mean_length == 0:
            return 0.0

        std_dev = statistics.stdev(lengths)
        return min(100.0, (std_dev / mean_length) * 100)

    def _calculate_rhythm_score(self, lengths: list[int], variance: float) -> float:
        """リズムスコアの計算"""
        if not lengths:
            return 0.0

        # 理想的な分布からの偏差を計算
        ideal_avg = 35  # 理想的な平均文字数
        actual_avg = statistics.mean(lengths)

        # 平均値スコア（理想値からの距離）
        avg_score = max(0, 100 - abs(actual_avg - ideal_avg) * 2)

        # バラエティスコア（適度なばらつき）
        ideal_variance = 25  # 理想的なバラエティ度
        variance_score = max(0, 100 - abs(variance - ideal_variance) * 2)

        # 極端値の影響を考慮
        extreme_penalty = 0
        for length in lengths:
            if length > 80:  # 非常に長い文:
                extreme_penalty += 5
            elif length < 10:  # 非常に短い文
                extreme_penalty += 3

        final_score = (avg_score * 0.4 + variance_score * 0.6) - extreme_penalty
        return max(0.0, min(100.0, final_score))

    def _detect_rhythm_issues(self, sentences: list[SentenceAnalysis]) -> list[RhythmIssue]:
        """リズム問題の検出"""
        issues = []

        # 連続長文の検出
        issues.extend(self._detect_consecutive_long_sentences(sentences))

        # 連続短文の検出
        issues.extend(self._detect_consecutive_short_sentences(sentences))

        # 単調なパターンの検出
        issues.extend(self._detect_monotonous_patterns(sentences))

        return issues

    def _detect_consecutive_long_sentences(self, sentences: list[SentenceAnalysis]) -> list[RhythmIssue]:
        """連続長文パターンの検出"""
        issues = []
        consecutive_count = 0
        start_index = 0
        long_sentences = []

        for i, sentence in enumerate(sentences):
            if sentence.is_long_sentence(60):
                if consecutive_count == 0:
                    start_index = i
                    long_sentences = []
                consecutive_count += 1
                long_sentences.append(sentence)
            else:
                if consecutive_count >= 5:  # 5文連続以上:
                    severity = self._determine_consecutive_severity(consecutive_count, "long")
                    issue = RhythmIssue(
                        issue_type=RhythmIssueType.CONSECUTIVE_LONG,
                        severity=severity,
                        start_index=start_index,
                        end_index=i - 1,
                        description=f"{consecutive_count}文連続で60文字以上の長文が続いています",
                        suggestion="長文を短く分割するか、間に短い文を挿入して読者の負荷を軽減してください",
                        affected_sentences=long_sentences.copy(),
                    )

                    issues.append(issue)

                consecutive_count = 0
                long_sentences = []

        # 最後まで連続している場合
        if consecutive_count >= 5:
            severity = self._determine_consecutive_severity(consecutive_count, "long")
            issue = RhythmIssue(
                issue_type=RhythmIssueType.CONSECUTIVE_LONG,
                severity=severity,
                start_index=start_index,
                end_index=len(sentences) - 1,
                description=f"{consecutive_count}文連続で60文字以上の長文が続いています",
                suggestion="長文を短く分割するか、間に短い文を挿入して読者の負荷を軽減してください",
                affected_sentences=long_sentences,
            )

            issues.append(issue)

        return issues

    def _detect_consecutive_short_sentences(self, sentences: list[SentenceAnalysis]) -> list[RhythmIssue]:
        """連続短文パターンの検出"""
        issues = []
        consecutive_count = 0
        start_index = 0
        short_sentences = []

        for i, sentence in enumerate(sentences):
            if sentence.is_short_sentence(20):
                if consecutive_count == 0:
                    start_index = i
                    short_sentences = []
                consecutive_count += 1
                short_sentences.append(sentence)
            else:
                if consecutive_count >= 5:  # 5文連続以上:
                    severity = self._determine_consecutive_severity(consecutive_count, "short")
                    issue = RhythmIssue(
                        issue_type=RhythmIssueType.CONSECUTIVE_SHORT,
                        severity=severity,
                        start_index=start_index,
                        end_index=i - 1,
                        description=f"{consecutive_count}文連続で20文字以下の短文が続いています",
                        suggestion="短文を統合するか、詳細な描写を追加してブツ切れ感を解消してください",
                        affected_sentences=short_sentences.copy(),
                    )

                    issues.append(issue)

                consecutive_count = 0
                short_sentences = []

        # 最後まで連続している場合
        if consecutive_count >= 5:
            severity = self._determine_consecutive_severity(consecutive_count, "short")
            issue = RhythmIssue(
                issue_type=RhythmIssueType.CONSECUTIVE_SHORT,
                severity=severity,
                start_index=start_index,
                end_index=len(sentences) - 1,
                description=f"{consecutive_count}文連続で20文字以下の短文が続いています",
                suggestion="短文を統合するか、詳細な描写を追加してブツ切れ感を解消してください",
                affected_sentences=short_sentences,
            )

            issues.append(issue)

        return issues

    def _detect_monotonous_patterns(self, sentences: list[SentenceAnalysis]) -> list[RhythmIssue]:
        """単調なパターンの検出"""
        issues = []

        if len(sentences) < 10:
            return issues

        # 文末パターンの単調性チェック
        ending_pattern_issues = self._check_ending_pattern_monotony(sentences)
        issues.extend(ending_pattern_issues)

        # 文字数の単調性チェック
        length_monotony_issues = self._check_length_monotony(sentences)
        issues.extend(length_monotony_issues)

        return issues

    def _check_ending_pattern_monotony(self, sentences: list[SentenceAnalysis]) -> list[RhythmIssue]:
        """文末パターンの単調性チェック"""
        issues = []

        # 連続する同じ文末パターンを検出
        consecutive_count = 1
        current_pattern = sentences[0].ending_pattern
        start_index = 0

        for i in range(1, len(sentences)):
            if sentences[i].ending_pattern == current_pattern:
                consecutive_count += 1
            else:
                if consecutive_count >= 7:  # 7文連続以上同じパターン:
                    issue = RhythmIssue(
                        issue_type=RhythmIssueType.MONOTONOUS_LENGTH,
                        severity=RhythmSeverity.MEDIUM,
                        start_index=start_index,
                        end_index=i - 1,
                        description=f"文末パターン「{current_pattern}」が{consecutive_count}文連続しています",
                        suggestion="文末のバリエーションを増やして単調さを改善してください",
                        affected_sentences=sentences[start_index:i],
                    )

                    issues.append(issue)

                consecutive_count = 1
                current_pattern = sentences[i].ending_pattern
                start_index = i

        return issues

    def _check_length_monotony(self, sentences: list[SentenceAnalysis]) -> list[RhythmIssue]:
        """文字数の単調性チェック"""
        issues = []

        # 似たような文字数が続く場合を検出
        window_size = 8
        for i in range(len(sentences) - window_size + 1):
            window = sentences[i : i + window_size]
            lengths = [s.character_count for s in window]

            # 標準偏差が小さすぎる場合（単調）
            if len(set(lengths)) <= 3 and statistics.stdev(lengths) < 5:
                avg_length = statistics.mean(lengths)
                issue = RhythmIssue(
                    issue_type=RhythmIssueType.MONOTONOUS_LENGTH,
                    severity=RhythmSeverity.LOW,
                    start_index=i,
                    end_index=i + window_size - 1,
                    description=f"文字数が{avg_length:.1f}文字前後で単調になっています",
                    suggestion="文の長さにバリエーションを加えてリズムを改善してください",
                    affected_sentences=window,
                )

                issues.append(issue)
                break  # 重複検出を避ける

        return issues

    def _determine_consecutive_severity(self, count: int, pattern_type: str) -> RhythmSeverity:
        """連続パターンの深刻度判定"""
        if pattern_type == "long":
            if count >= 10:
                return RhythmSeverity.CRITICAL
            if count >= 7:
                return RhythmSeverity.HIGH
            return RhythmSeverity.MEDIUM
        if count >= 12:
            return RhythmSeverity.CRITICAL
        if count >= 8:
            return RhythmSeverity.HIGH
        return RhythmSeverity.MEDIUM

    def _calculate_overall_score(self, statistics: RhythmStatistics, issues: list[RhythmIssue]) -> float:
        """総合スコアの計算"""
        base_score = statistics.rhythm_score

        # 問題による減点
        penalty = 0
        for issue in issues:
            if issue.severity == RhythmSeverity.CRITICAL:
                penalty += 15
            elif issue.severity == RhythmSeverity.HIGH:
                penalty += 10
            elif issue.severity == RhythmSeverity.MEDIUM:
                penalty += 5
            else:
                penalty += 2

        final_score = max(0.0, base_score - penalty)
        return min(100.0, final_score)

    def _determine_readability_grade(self, score: float) -> str:
        """読みやすさランクの決定"""
        if score >= 90:
            return "excellent"  # 優秀
        if score >= 80:
            return "good"  # 良好
        if score >= 70:
            return "fair"  # 普通
        if score >= 60:
            return "poor"  # 要改善
        return "critical"  # 要修正
