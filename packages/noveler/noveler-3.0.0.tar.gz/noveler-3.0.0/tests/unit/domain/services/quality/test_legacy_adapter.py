# File: tests/unit/domain/services/quality/test_legacy_adapter.py
# Purpose: Test legacy API compatibility adapter - TDD RED phase
# Context: Ensure 100% backward compatibility during migration

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

# These imports will fail initially (RED phase)
from src.noveler.domain.services.quality.adapters.legacy_adapter import (
    RhythmAnalysisServiceAdapter,
    ReadabilityAnalysisServiceAdapter,
    GrammarCheckServiceAdapter,
    IntegratedQualityServiceAdapter
)


class TestLegacyQualityServiceAdapter:
    """Test suite for legacy API compatibility"""

    def setup_method(self):
        """Setup test dependencies"""
        self.rhythm_adapter = RhythmAnalysisServiceAdapter()
        self.readability_adapter = ReadabilityAnalysisServiceAdapter()
        self.grammar_adapter = GrammarCheckServiceAdapter()
        self.integrated_adapter = IntegratedQualityServiceAdapter()

    @pytest.mark.spec("SPEC-LEGACY-COMPAT-001")
    def test_rhythm_analysis_service_compatibility(self):
        """Test RhythmAnalysisService API compatibility"""
        # Old API signature
        score, issues = self.rhythm_adapter.analyze_rhythm(
            text="これは長い文です。短い文。また長い文が続きます。",
            episode_number=1
        )

        assert isinstance(score, float)
        assert isinstance(issues, list)

    @pytest.mark.spec("SPEC-LEGACY-COMPAT-002")
    def test_readability_check_service_compatibility(self):
        """Test ReadabilityCheckService API compatibility"""
        # Old API signature
        score, issues = self.readability_adapter.check_readability(
            text="これは非常に長い文で読みにくいかもしれません。",
            episode_number=1
        )

        assert isinstance(score, float)
        assert isinstance(issues, list)

    @pytest.mark.spec("SPEC-LEGACY-COMPAT-003")
    def test_grammar_check_service_compatibility(self):
        """Test GrammarCheckService API compatibility"""
        # Old API signature
        result = self.grammar_adapter.check_grammar(
            text="文法をを確認します。",
            episode_number=1
        )

        assert 'score' in result
        assert 'issues' in result
        assert 'summary' in result

    @pytest.mark.spec("SPEC-LEGACY-COMPAT-004")
    def test_integrated_quality_service_compatibility(self):
        """Test IntegratedQualityService API compatibility"""
        # Old API signature
        result = self.integrated_adapter.run_all_checks(
            text="統合チェックのテキスト",
            episode_number=1
        )

        assert 'overall_score' in result
        assert 'aspect_scores' in result
        assert 'issues' in result
        assert 'report' in result


