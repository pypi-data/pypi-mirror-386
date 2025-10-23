# File: src/noveler/domain/services/quality/core/analyzers/rhythm_analyzer.py
# Purpose: Analyze text rhythm (sentence length variation, dialogue ratio)
# Context: Extracted from original rhythm analysis services

from typing import Tuple, List
import re
from src.noveler.domain.services.quality.core.analyzers.base_analyzer import BaseAnalyzer
from src.noveler.domain.services.quality.value_objects.quality_value_objects import (
    QualityIssue,
    IssueSeverity
)


class RhythmAnalyzer(BaseAnalyzer):
    """Analyzer for text rhythm quality"""

    def analyze(self, text: str, episode_number: int) -> Tuple[float, List[QualityIssue]]:
        """Analyze text rhythm"""
        if not text.strip():
            return 100.0, []

        issues = []
        lines = self._split_into_lines(text)

        # Check sentence length variation
        sentence_issues = self._check_sentence_length_variation(lines)
        issues.extend(sentence_issues)

        # Check dialogue ratio
        dialogue_issues = self._check_dialogue_ratio(lines)
        issues.extend(dialogue_issues)

        # Calculate score
        score = self._calculate_score_from_issues(issues)

        return score, issues

    def _check_sentence_length_variation(self, lines: List[str]) -> List[QualityIssue]:
        """Check for monotonous sentence lengths"""
        issues = []
        sentences = []

        for line_num, line in enumerate(lines, 1):
            if line.strip():
                # Split by Japanese sentence endings
                parts = re.split(r'[。！？]', line)
                for part in parts:
                    if part.strip():
                        sentences.append((len(part), line_num))

        # Check for consecutive sentences with similar length
        consecutive_similar = 0
        for i in range(1, len(sentences)):
            prev_len = sentences[i-1][0]
            curr_len = sentences[i][0]

            if abs(prev_len - curr_len) < 5:
                consecutive_similar += 1
                if consecutive_similar >= 3:
                    issues.append(QualityIssue(
                        aspect='rhythm',
                        severity=IssueSeverity.MEDIUM,
                        line_number=sentences[i][1],
                        description='文長の変化が少なくリズムが単調です',
                        suggestion='文の長さにバリエーションを持たせましょう',
                        reason_code='MONOTONOUS_SENTENCE_LENGTH'
                    ))
                    consecutive_similar = 0
            else:
                consecutive_similar = 0

        return issues

    def _check_dialogue_ratio(self, lines: List[str]) -> List[QualityIssue]:
        """Check dialogue to narration ratio"""
        issues = []
        dialogue_lines = 0
        total_lines = 0

        for line in lines:
            if line.strip():
                total_lines += 1
                if '「' in line or '」' in line:
                    dialogue_lines += 1

        if total_lines > 0:
            ratio = dialogue_lines / total_lines
            if ratio > 0.75:
                issues.append(QualityIssue(
                    aspect='rhythm',
                    severity=IssueSeverity.MEDIUM,
                    line_number=None,
                    description=f'会話文の比率が{ratio:.1%}と高すぎます',
                    suggestion='地の文を増やしてバランスを改善しましょう',
                    reason_code='HIGH_DIALOGUE_RATIO'
                ))
            elif ratio < 0.25:
                issues.append(QualityIssue(
                    aspect='rhythm',
                    severity=IssueSeverity.MEDIUM,
                    line_number=None,
                    description=f'会話文の比率が{ratio:.1%}と低すぎます',
                    suggestion='会話文を増やして動きを出しましょう',
                    reason_code='LOW_DIALOGUE_RATIO'
                ))

        return issues