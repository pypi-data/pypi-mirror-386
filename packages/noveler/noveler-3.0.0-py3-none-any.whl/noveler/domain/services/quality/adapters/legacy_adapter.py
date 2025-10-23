# File: src/noveler/domain/services/quality/adapters/legacy_adapter.py
# Purpose: Adapter for backward compatibility with existing services
# Context: Enables gradual migration from old to new quality services

from typing import Dict, List, Tuple, Optional
from src.noveler.domain.services.quality.core.quality_check_core import QualityCheckCore
from src.noveler.domain.services.quality.core.quality_configuration_manager import QualityConfigurationManager
from src.noveler.domain.services.quality.reporting.quality_reporting_service import QualityReportingService
from src.noveler.domain.services.quality.value_objects.quality_value_objects import (
    QualityCheckRequest,
    QualityCheckResult
)


class RhythmAnalysisServiceAdapter:
    """Adapter for rhythm analysis service"""

    def __init__(self):
        self._core = QualityCheckCore()

    def analyze_rhythm(self, text: str, episode_number: int) -> Tuple[float, List]:
        """Legacy interface for rhythm analysis"""
        request = QualityCheckRequest(
            text=text,
            episode_number=episode_number,
            check_types=['rhythm']
        )
        result = self._core.analyze_quality(request)
        rhythm_score = result.aspect_scores.get('rhythm', 0.0)
        rhythm_issues = [i for i in result.issues if i.aspect == 'rhythm']
        return rhythm_score, rhythm_issues


class ReadabilityAnalysisServiceAdapter:
    """Adapter for readability analysis service"""

    def __init__(self):
        self._core = QualityCheckCore()

    def check_readability(self, text: str, episode_number: int) -> Tuple[float, List]:
        """Legacy interface for readability check"""
        request = QualityCheckRequest(
            text=text,
            episode_number=episode_number,
            check_types=['readability']
        )
        result = self._core.analyze_quality(request)
        readability_score = result.aspect_scores.get('readability', 0.0)
        readability_issues = [i for i in result.issues if i.aspect == 'readability']
        return readability_score, readability_issues


class GrammarCheckServiceAdapter:
    """Adapter for grammar check service"""

    def __init__(self):
        self._core = QualityCheckCore()

    def check_grammar(self, text: str, episode_number: int) -> Dict:
        """Legacy interface for grammar check"""
        request = QualityCheckRequest(
            text=text,
            episode_number=episode_number,
            check_types=['grammar']
        )
        result = self._core.analyze_quality(request)

        return {
            'score': result.aspect_scores.get('grammar', 0.0),
            'issues': [i for i in result.issues if i.aspect == 'grammar'],
            'summary': f"Grammar score: {result.aspect_scores.get('grammar', 0.0):.1f}"
        }


class IntegratedQualityServiceAdapter:
    """Adapter for integrated quality service"""

    def __init__(self):
        self._core = QualityCheckCore()
        self._reporter = QualityReportingService()

    def run_all_checks(
        self,
        text: str,
        episode_number: int,
        aspects: Optional[List[str]] = None
    ) -> Dict:
        """Legacy interface for running all checks"""
        if aspects is None:
            aspects = ['rhythm', 'readability', 'grammar', 'style']

        request = QualityCheckRequest(
            text=text,
            episode_number=episode_number,
            check_types=aspects
        )
        result = self._core.analyze_quality(request)

        return {
            'overall_score': result.overall_score,
            'aspect_scores': result.aspect_scores,
            'issues': result.issues,
            'report': self._reporter.generate_report(result, format='summary')
        }