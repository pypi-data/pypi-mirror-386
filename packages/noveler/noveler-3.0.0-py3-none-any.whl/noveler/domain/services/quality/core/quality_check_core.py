# File: src/noveler/domain/services/quality/core/quality_check_core.py
# Purpose: Unified quality check service core implementation
# Context: Consolidates 19 quality services into single responsibility

from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from src.noveler.domain.services.quality.value_objects.quality_value_objects import (
    QualityCheckRequest,
    QualityCheckResult,
    QualityIssue,
    QualityScore,
    IssueSeverity
)

# Import analyzers (will be implemented next)
from src.noveler.domain.services.quality.core.analyzers.rhythm_analyzer import RhythmAnalyzer
from src.noveler.domain.services.quality.core.analyzers.readability_analyzer import ReadabilityAnalyzer
from src.noveler.domain.services.quality.core.analyzers.grammar_analyzer import GrammarAnalyzer
from src.noveler.domain.services.quality.core.analyzers.style_analyzer import StyleAnalyzer


class QualityCheckCore:
    """
    Unified quality check service

    Consolidates quality analysis, evaluation, and checking into single service
    with clear responsibility boundaries.
    """

    VALID_CHECK_TYPES = {'rhythm', 'readability', 'grammar', 'style'}

    def __init__(self):
        """Initialize with analyzer instances"""
        self._rhythm_analyzer = RhythmAnalyzer()
        self._readability_analyzer = ReadabilityAnalyzer()
        self._grammar_analyzer = GrammarAnalyzer()
        self._style_analyzer = StyleAnalyzer()

        self._analyzers = {
            'rhythm': self._rhythm_analyzer,
            'readability': self._readability_analyzer,
            'grammar': self._grammar_analyzer,
            'style': self._style_analyzer
        }

    def analyze_quality(self, request: QualityCheckRequest) -> QualityCheckResult:
        """
        Main entry point for quality analysis

        Args:
            request: Quality check request with text and parameters

        Returns:
            QualityCheckResult with scores and issues
        """
        # Validate check types
        self._validate_check_types(request.check_types)

        # Handle empty text
        if not request.text or request.text.strip() == '':
            return self._create_empty_result(request.check_types)

        # Run requested analyzers
        aspect_scores = {}
        all_issues = []

        for check_type in request.check_types:
            analyzer = self._analyzers[check_type]
            score, issues = analyzer.analyze(request.text, request.episode_number)

            aspect_scores[check_type] = score
            all_issues.extend(issues)

        # Calculate total score
        total_score = self._calculate_total_score(
            aspect_scores,
            request.weights
        )

        return QualityCheckResult(
            total_score=total_score,
            aspect_scores=aspect_scores,
            issues=all_issues,
            check_types=request.check_types,
            metadata={
                'episode_number': request.episode_number,
                'preset': request.preset
            }
        )

    def _validate_check_types(self, check_types: List[str]) -> None:
        """Validate that all check types are valid"""
        invalid_types = set(check_types) - self.VALID_CHECK_TYPES
        if invalid_types:
            raise ValueError(f"Invalid check type(s): {invalid_types}")

    def _create_empty_result(self, check_types: List[str]) -> QualityCheckResult:
        """Create result for empty text (perfect score, no issues)"""
        aspect_scores = {check_type: 100.0 for check_type in check_types}

        return QualityCheckResult(
            total_score=100.0,
            aspect_scores=aspect_scores,
            issues=[],
            check_types=check_types
        )

    def _calculate_total_score(
        self,
        aspect_scores: Dict[str, float],
        weights: Optional[Dict[str, float]]
    ) -> float:
        """
        Calculate weighted total score

        Args:
            aspect_scores: Individual aspect scores
            weights: Optional weights for aspects

        Returns:
            Weighted average score
        """
        if not aspect_scores:
            return 100.0

        if weights:
            # Use provided weights
            total_weight = sum(weights.get(k, 0) for k in aspect_scores)
            if total_weight == 0:
                return sum(aspect_scores.values()) / len(aspect_scores)

            weighted_sum = sum(
                aspect_scores[k] * weights.get(k, 0)
                for k in aspect_scores
            )
            return weighted_sum / total_weight
        else:
            # Simple average
            return sum(aspect_scores.values()) / len(aspect_scores)