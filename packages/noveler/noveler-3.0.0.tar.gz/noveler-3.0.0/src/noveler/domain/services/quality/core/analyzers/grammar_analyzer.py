# File: src/noveler/domain/services/quality/core/analyzers/grammar_analyzer.py
# Purpose: Analyze grammar and punctuation issues
# Context: Extracted from original grammar checking services

from typing import Tuple, List
import re
from src.noveler.domain.services.quality.core.analyzers.base_analyzer import BaseAnalyzer
from src.noveler.domain.services.quality.value_objects.quality_value_objects import (
    QualityIssue,
    IssueSeverity
)


class GrammarAnalyzer(BaseAnalyzer):
    """Analyzer for grammar and punctuation"""

    def analyze(self, text: str, episode_number: int) -> Tuple[float, List[QualityIssue]]:
        """Analyze grammar issues"""
        if not text.strip():
            return 100.0, []

        issues = []
        lines = self._split_into_lines(text)

        for line_num, line in enumerate(lines, 1):
            if not line.strip():
                continue

            # Check for common grammar issues
            issues.extend(self._check_punctuation(line, line_num))
            issues.extend(self._check_particle_errors(line, line_num))

        score = self._calculate_score_from_issues(issues)
        return score, issues

    def _check_punctuation(self, line: str, line_num: int) -> List[QualityIssue]:
        """Check punctuation issues"""
        issues = []

        # Check for multiple consecutive punctuation
        if re.search(r'[。、！？]{2,}', line):
            issues.append(QualityIssue(
                aspect='grammar',
                severity=IssueSeverity.LOW,
                line_number=line_num,
                description='句読点が連続しています',
                suggestion='句読点の重複を削除しましょう',
                reason_code='DUPLICATE_PUNCTUATION'
            ))

        # Check comma density
        comma_count = line.count('、')
        if comma_count > 3:
            issues.append(QualityIssue(
                aspect='grammar',
                severity=IssueSeverity.MEDIUM,
                line_number=line_num,
                description=f'読点が多すぎます（{comma_count}個）',
                suggestion='文を分割することを検討しましょう',
                reason_code='EXCESSIVE_COMMAS'
            ))

        return issues

    def _check_particle_errors(self, line: str, line_num: int) -> List[QualityIssue]:
        """Check for common particle errors"""
        issues = []

        # Check for common particle mistakes (simplified)
        if re.search(r'を を|が が|に に|で で', line):
            issues.append(QualityIssue(
                aspect='grammar',
                severity=IssueSeverity.HIGH,
                line_number=line_num,
                description='助詞が重複しています',
                suggestion='重複した助詞を削除しましょう',
                reason_code='DUPLICATE_PARTICLE'
            ))

        return issues