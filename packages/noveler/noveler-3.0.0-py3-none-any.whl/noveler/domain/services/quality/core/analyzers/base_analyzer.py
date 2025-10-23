# File: src/noveler/domain/services/quality/core/analyzers/base_analyzer.py
# Purpose: Base class for quality analyzers
# Context: Common interface for all analyzers

from abc import ABC, abstractmethod
from typing import Tuple, List
from src.noveler.domain.services.quality.value_objects.quality_value_objects import QualityIssue


class BaseAnalyzer(ABC):
    """Base class for quality analyzers"""

    @abstractmethod
    def analyze(self, text: str, episode_number: int) -> Tuple[float, List[QualityIssue]]:
        """
        Analyze text for quality issues

        Args:
            text: Text to analyze
            episode_number: Episode number for context

        Returns:
            Tuple of (score, list of issues)
        """
        pass

    def _split_into_lines(self, text: str) -> List[str]:
        """Split text into lines for analysis"""
        return text.strip().split('\n') if text else []

    def _calculate_score_from_issues(
        self,
        issues: List[QualityIssue],
        base_score: float = 100.0
    ) -> float:
        """Calculate score based on issues found"""
        if not issues:
            return base_score

        # Deduct points based on severity
        deductions = {
            'critical': 10,
            'high': 5,
            'medium': 3,
            'low': 1
        }

        total_deduction = sum(
            deductions.get(issue.severity.value, 0)
            for issue in issues
        )

        return max(0, base_score - total_deduction)