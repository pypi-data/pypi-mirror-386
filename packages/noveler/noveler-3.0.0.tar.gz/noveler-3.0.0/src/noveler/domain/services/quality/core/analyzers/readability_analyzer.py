# File: src/noveler/domain/services/quality/core/analyzers/readability_analyzer.py
# Purpose: Analyze text readability (sentence length, complexity)
# Context: Extracted from original readability services

from typing import Tuple, List
from src.noveler.domain.services.quality.core.analyzers.base_analyzer import BaseAnalyzer
from src.noveler.domain.services.quality.value_objects.quality_value_objects import (
    QualityIssue,
    IssueSeverity
)


class ReadabilityAnalyzer(BaseAnalyzer):
    """Analyzer for text readability"""

    MAX_SENTENCE_LENGTH = 45  # characters
    MIN_SENTENCE_LENGTH = 10

    def analyze(self, text: str, episode_number: int) -> Tuple[float, List[QualityIssue]]:
        """Analyze text readability"""
        if not text.strip():
            return 100.0, []

        issues = []
        lines = self._split_into_lines(text)

        for line_num, line in enumerate(lines, 1):
            if not line.strip():
                continue

            # Check sentence length
            length = len(line.strip())
            if length > self.MAX_SENTENCE_LENGTH:
                issues.append(QualityIssue(
                    aspect='readability',
                    severity=IssueSeverity.MEDIUM,
                    line_number=line_num,
                    description=f'文が長すぎます（{length}文字）',
                    suggestion='文を分割して読みやすくしましょう',
                    reason_code='LONG_SENTENCE'
                ))
            elif length < self.MIN_SENTENCE_LENGTH and '「' not in line:
                issues.append(QualityIssue(
                    aspect='readability',
                    severity=IssueSeverity.LOW,
                    line_number=line_num,
                    description=f'文が短すぎます（{length}文字）',
                    suggestion='もう少し詳しく描写しましょう',
                    reason_code='SHORT_SENTENCE'
                ))

        score = self._calculate_score_from_issues(issues)
        return score, issues