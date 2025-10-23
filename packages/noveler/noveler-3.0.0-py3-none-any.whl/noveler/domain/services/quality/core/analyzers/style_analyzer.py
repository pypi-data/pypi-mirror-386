# File: src/noveler/domain/services/quality/core/analyzers/style_analyzer.py
# Purpose: Analyze text style (spacing, empty lines, formatting)
# Context: Extracted from original style checking services

from typing import Tuple, List
import re
from src.noveler.domain.services.quality.core.analyzers.base_analyzer import BaseAnalyzer
from src.noveler.domain.services.quality.value_objects.quality_value_objects import (
    QualityIssue,
    IssueSeverity
)


class StyleAnalyzer(BaseAnalyzer):
    """Analyzer for text style and formatting"""

    def analyze(self, text: str, episode_number: int) -> Tuple[float, List[QualityIssue]]:
        """Analyze style issues"""
        if not text.strip():
            return 100.0, []

        issues = []
        lines = self._split_into_lines(text)

        # Check for empty line issues
        issues.extend(self._check_empty_lines(lines))

        # Check for spacing issues
        issues.extend(self._check_spacing_issues(lines))

        # Check for bracket balance
        issues.extend(self._check_bracket_balance(lines))

        score = self._calculate_score_from_issues(issues)
        return score, issues

    def _check_empty_lines(self, lines: List[str]) -> List[QualityIssue]:
        """Check for excessive empty lines and leading whitespace"""
        issues = []
        consecutive_empty = 0

        # Check for leading empty lines (file should not start with whitespace)
        for line_num, line in enumerate(lines, 1):
            if not line.strip():
                issues.append(QualityIssue(
                    aspect='style',
                    severity=IssueSeverity.MEDIUM,
                    line_number=line_num,
                    description='ファイル先頭に空白行があります',
                    suggestion='ファイルは本文から開始してください',
                    reason_code='LEADING_WHITESPACE'
                ))
            else:
                # Found first non-empty line, stop checking for leading whitespace
                break

        # Check for consecutive empty lines (3+ in a row)
        for line_num, line in enumerate(lines, 1):
            if not line.strip():
                consecutive_empty += 1
                if consecutive_empty > 2:
                    issues.append(QualityIssue(
                        aspect='style',
                        severity=IssueSeverity.LOW,
                        line_number=line_num,
                        description='連続した空行が多すぎます',
                        suggestion='空行は最大2行までにしましょう',
                        reason_code='EXCESSIVE_EMPTY_LINES'
                    ))
            else:
                consecutive_empty = 0

        return issues

    def _check_spacing_issues(self, lines: List[str]) -> List[QualityIssue]:
        """Check for spacing issues"""
        issues = []

        for line_num, line in enumerate(lines, 1):
            if not line.strip():
                continue

            # Check for tab characters
            if '\t' in line:
                issues.append(QualityIssue(
                    aspect='style',
                    severity=IssueSeverity.LOW,
                    line_number=line_num,
                    description='タブ文字が使用されています',
                    suggestion='スペースを使用してください',
                    reason_code='TAB_CHARACTER'
                ))

            # Check for trailing whitespace
            if line != line.rstrip():
                issues.append(QualityIssue(
                    aspect='style',
                    severity=IssueSeverity.LOW,
                    line_number=line_num,
                    description='行末に余分なスペースがあります',
                    suggestion='行末のスペースを削除しましょう',
                    reason_code='TRAILING_WHITESPACE'
                ))

        return issues

    def _check_bracket_balance(self, lines: List[str]) -> List[QualityIssue]:
        """Check for bracket balance"""
        issues = []

        for line_num, line in enumerate(lines, 1):
            if not line.strip():
                continue

            # Check Japanese quotation marks
            opening_count = line.count('「')
            closing_count = line.count('」')

            if opening_count != closing_count:
                issues.append(QualityIssue(
                    aspect='style',
                    severity=IssueSeverity.HIGH,
                    line_number=line_num,
                    description='括弧の対応が取れていません',
                    suggestion='開き括弧と閉じ括弧を確認してください',
                    reason_code='UNBALANCED_BRACKETS'
                ))

        return issues