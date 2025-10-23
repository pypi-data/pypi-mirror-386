# File: tests/unit/domain/services/quality/test_quality_check_core.py
# Purpose: Test QualityCheckCore unified service - TDD RED phase
# Context: B20-compliant test-first implementation for quality service consolidation

import pytest
from unittest.mock import Mock, MagicMock
from typing import List, Dict, Any

# These imports will fail initially (RED phase)
from src.noveler.domain.services.quality.core.quality_check_core import QualityCheckCore
from src.noveler.domain.services.quality.value_objects.quality_value_objects import (
    QualityCheckRequest,
    QualityCheckResult,
    QualityIssue,
    QualityScore
)


class TestQualityCheckCore:
    """Test suite for unified quality check service"""

    def setup_method(self):
        """Setup test dependencies"""
        self.quality_core = QualityCheckCore()
        self.sample_text = """
        これはテスト用のサンプルテキストです。
        短い文。とても長い文章がここにありまして、読みづらいかもしれません。
        「会話文です」と彼は言った。
        """

    @pytest.mark.spec("SPEC-QUALITY-CORE-001")
    def test_quality_check_core_exists(self):
        """Verify QualityCheckCore service exists"""
        assert self.quality_core is not None
        assert hasattr(self.quality_core, 'analyze_quality')

    @pytest.mark.spec("SPEC-QUALITY-CORE-002")
    def test_analyze_quality_returns_result(self):
        """Test that analyze_quality returns proper result structure"""
        request = QualityCheckRequest(
            text=self.sample_text,
            episode_number=1,
            check_types=['rhythm', 'readability', 'grammar']
        )

        result = self.quality_core.analyze_quality(request)

        assert isinstance(result, QualityCheckResult)
        assert result.total_score >= 0
        assert result.total_score <= 100
        assert len(result.issues) >= 0
        assert result.check_types == request.check_types

    @pytest.mark.spec("SPEC-QUALITY-CORE-003")
    def test_rhythm_analysis_integration(self):
        """Test rhythm analysis is properly integrated"""
        request = QualityCheckRequest(
            text=self.sample_text,
            episode_number=1,
            check_types=['rhythm']
        )

        result = self.quality_core.analyze_quality(request)

        assert 'rhythm' in result.aspect_scores
        rhythm_score = result.aspect_scores['rhythm']
        assert 0 <= rhythm_score <= 100

        # Check for rhythm-specific issues
        rhythm_issues = [i for i in result.issues if i.aspect == 'rhythm']
        assert len(rhythm_issues) >= 0

    @pytest.mark.spec("SPEC-QUALITY-CORE-004")
    def test_readability_analysis_integration(self):
        """Test readability analysis is properly integrated"""
        request = QualityCheckRequest(
            text=self.sample_text,
            episode_number=1,
            check_types=['readability']
        )

        result = self.quality_core.analyze_quality(request)

        assert 'readability' in result.aspect_scores
        readability_score = result.aspect_scores['readability']
        assert 0 <= readability_score <= 100

    @pytest.mark.spec("SPEC-QUALITY-CORE-005")
    def test_grammar_analysis_integration(self):
        """Test grammar analysis is properly integrated"""
        request = QualityCheckRequest(
            text=self.sample_text,
            episode_number=1,
            check_types=['grammar']
        )

        result = self.quality_core.analyze_quality(request)

        assert 'grammar' in result.aspect_scores
        grammar_score = result.aspect_scores['grammar']
        assert 0 <= grammar_score <= 100

    @pytest.mark.spec("SPEC-QUALITY-CORE-006")
    def test_style_analysis_integration(self):
        """Test style analysis is properly integrated"""
        request = QualityCheckRequest(
            text=self.sample_text,
            episode_number=1,
            check_types=['style']
        )

        result = self.quality_core.analyze_quality(request)

        assert 'style' in result.aspect_scores
        style_score = result.aspect_scores['style']
        assert 0 <= style_score <= 100

    @pytest.mark.spec("SPEC-QUALITY-CORE-007")
    def test_weighted_scoring(self):
        """Test weighted scoring calculation"""
        request = QualityCheckRequest(
            text=self.sample_text,
            episode_number=1,
            check_types=['rhythm', 'readability'],
            weights={'rhythm': 0.6, 'readability': 0.4}
        )

        result = self.quality_core.analyze_quality(request)

        # Verify weighted average is calculated correctly
        expected_score = (
            result.aspect_scores['rhythm'] * 0.6 +
            result.aspect_scores['readability'] * 0.4
        )
        assert abs(result.total_score - expected_score) < 0.01

    @pytest.mark.spec("SPEC-QUALITY-CORE-008")
    def test_empty_text_handling(self):
        """Test handling of empty text"""
        request = QualityCheckRequest(
            text="",
            episode_number=1,
            check_types=['rhythm']
        )

        result = self.quality_core.analyze_quality(request)

        assert result.total_score == 100  # Empty text gets perfect score
        assert len(result.issues) == 0

    @pytest.mark.spec("SPEC-QUALITY-CORE-009")
    def test_invalid_check_type(self):
        """Test handling of invalid check type"""
        request = QualityCheckRequest(
            text=self.sample_text,
            episode_number=1,
            check_types=['invalid_type']
        )

        with pytest.raises(ValueError, match="Invalid check type"):
            self.quality_core.analyze_quality(request)

    @pytest.mark.spec("SPEC-QUALITY-CORE-010")
    def test_analyzer_delegation(self):
        """Test that core properly delegates to analyzers"""
        # This test verifies the internal structure
        assert hasattr(self.quality_core, '_rhythm_analyzer')
        assert hasattr(self.quality_core, '_readability_analyzer')
        assert hasattr(self.quality_core, '_grammar_analyzer')
        assert hasattr(self.quality_core, '_style_analyzer')