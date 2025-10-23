# File: tests/unit/domain/services/ml_quality/test_corpus_analyzer.py
# Purpose: Unit tests for CorpusAnalyzer service
# Context: Test corpus baseline extraction and statistical feature computation

"""
Unit tests for CorpusAnalyzer service.

Test coverage:
- Corpus baseline metrics building
- Cache behavior (24-hour TTL)
- Statistical feature extraction
- Default baselines fallback
- SPEC-QUALITY-140 compliance
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock

from noveler.domain.services.ml_quality.corpus_analyzer import (
    CorpusAnalyzer,
    CorpusMetrics,
    Percentiles,
    RhythmMetrics,
    PunctuationMetrics
)


@pytest.fixture
def mock_corpus_repository():
    """Create mock corpus repository."""
    repo = Mock()
    repo.load_corpus = Mock(return_value=[
        {"content": "Sample text 1", "metadata": {"genre": "fantasy"}},
        {"content": "Sample text 2", "metadata": {"genre": "fantasy"}},
        {"content": "Sample text 3", "metadata": {"genre": "fantasy"}},
    ])
    return repo


@pytest.fixture
def mock_logger():
    """Create mock logger."""
    logger = Mock()
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    return logger


@pytest.fixture
def corpus_analyzer(mock_corpus_repository, mock_logger):
    """Create CorpusAnalyzer with mocked dependencies."""
    return CorpusAnalyzer(
        corpus_repository=mock_corpus_repository,
        logger=mock_logger
    )


class TestCorpusAnalyzerBasicWorkflow:
    """Test basic corpus analysis workflow."""

    def test_build_baseline_metrics_success(
        self,
        corpus_analyzer,
        mock_corpus_repository,
        mock_logger
    ):
        """Test successful corpus baseline metrics building."""
        result = corpus_analyzer.build_baseline_metrics(
            genre="fantasy",
            target_audience="young_adult",
            project_root=Path("/tmp/test_project")
        )

        # Verify repository was called
        mock_corpus_repository.load_corpus.assert_called_once_with(
            genre="fantasy",
            target_audience="young_adult",
            project_root=Path("/tmp/test_project")
        )

        # Verify result structure
        assert isinstance(result, dict)
        assert result["genre"] == "fantasy"
        assert result["target_audience"] == "young_adult"
        assert result["sample_count"] == 3
        assert "sentence_length_distribution" in result
        assert "rhythm_patterns" in result
        assert "dialogue_ratio_range" in result
        assert "punctuation_style_preferences" in result
        assert "vocabulary_complexity_range" in result
        assert "corpus_hash" in result

        # Verify logger was called
        assert mock_logger.info.called

    def test_build_baseline_metrics_with_empty_corpus(
        self,
        corpus_analyzer,
        mock_corpus_repository,
        mock_logger
    ):
        """Test fallback to defaults when corpus is empty."""
        # Simulate empty corpus
        mock_corpus_repository.load_corpus.return_value = []

        result = corpus_analyzer.build_baseline_metrics(
            genre="mystery",
            target_audience="adult",
            project_root=Path("/tmp/test_project")
        )

        # Verify fallback to defaults
        assert result["sample_count"] == 0
        assert result["corpus_hash"] == "default"
        assert mock_logger.warning.called

    def test_build_baseline_metrics_caching(
        self,
        corpus_analyzer,
        mock_corpus_repository
    ):
        """Test that metrics are cached after first build."""
        # First call - should hit repository
        result1 = corpus_analyzer.build_baseline_metrics(
            genre="fantasy",
            target_audience="young_adult",
            project_root=Path("/tmp/test_project")
        )

        # Second call - should use cache
        result2 = corpus_analyzer.build_baseline_metrics(
            genre="fantasy",
            target_audience="young_adult",
            project_root=Path("/tmp/test_project")
        )

        # Verify repository was only called once
        assert mock_corpus_repository.load_corpus.call_count == 1

        # Verify results are identical
        assert result1 == result2

    def test_build_baseline_metrics_force_refresh(
        self,
        corpus_analyzer,
        mock_corpus_repository
    ):
        """Test force_refresh bypasses cache."""
        # First call - populates cache
        corpus_analyzer.build_baseline_metrics(
            genre="fantasy",
            target_audience="young_adult",
            project_root=Path("/tmp/test_project")
        )

        # Second call with force_refresh - should bypass cache
        corpus_analyzer.build_baseline_metrics(
            genre="fantasy",
            target_audience="young_adult",
            project_root=Path("/tmp/test_project"),
            force_refresh=True
        )

        # Verify repository was called twice
        assert mock_corpus_repository.load_corpus.call_count == 2


class TestCorpusAnalyzerMetricsConversion:
    """Test metrics to dictionary conversion."""

    def test_metrics_to_dict_structure(self, corpus_analyzer):
        """Test CorpusMetrics is correctly converted to dict."""
        metrics = CorpusMetrics(
            genre="fantasy",
            target_audience="young_adult",
            sample_count=10,
            sentence_length_distribution=Percentiles(
                p10=10.0, p25=14.0, p50=30.0, p75=60.0, p90=90.0
            ),
            rhythm_patterns=RhythmMetrics(
                short_run_max=3,
                long_run_max=2,
                optimal_variation_range=(18, 70),
                window_avg_range=(18.0, 70.0)
            ),
            dialogue_ratio_range=(0.4, 0.75),
            punctuation_style_preferences=PunctuationMetrics(
                comma_avg_range=(0.6, 1.6),
                comma_per_sentence_max=3,
                period_ratio_range=(0.3, 0.6)
            ),
            vocabulary_complexity_range=(0.3, 0.7),
            corpus_hash="abc123def456"
        )

        result = corpus_analyzer._metrics_to_dict(metrics)

        # Verify structure
        assert result["genre"] == "fantasy"
        assert result["target_audience"] == "young_adult"
        assert result["sample_count"] == 10
        assert result["sentence_length_distribution"]["p50"] == 30.0
        assert result["rhythm_patterns"]["short_run_max"] == 3
        assert result["dialogue_ratio_range"] == [0.4, 0.75]
        assert result["punctuation_style_preferences"]["comma_per_sentence_max"] == 3
        assert result["vocabulary_complexity_range"] == [0.3, 0.7]
        assert result["corpus_hash"] == "abc123def456"


class TestCorpusAnalyzerDefaultBaselines:
    """Test default baseline fallback."""

    def test_get_default_baselines_structure(self, corpus_analyzer):
        """Test default baselines have correct structure."""
        result = corpus_analyzer._get_default_baselines(
            genre="fantasy",
            target_audience="young_adult"
        )

        # Verify all required fields are present
        assert result["genre"] == "fantasy"
        assert result["target_audience"] == "young_adult"
        assert result["sample_count"] == 0
        assert result["corpus_hash"] == "default"

        # Verify sentence length distribution
        assert "sentence_length_distribution" in result
        assert result["sentence_length_distribution"]["p50"] == 30.0

        # Verify rhythm patterns
        assert "rhythm_patterns" in result
        assert result["rhythm_patterns"]["short_run_max"] == 3

        # Verify dialogue ratio
        assert result["dialogue_ratio_range"] == [0.4, 0.75]

        # Verify punctuation preferences
        assert "punctuation_style_preferences" in result
        assert result["punctuation_style_preferences"]["comma_per_sentence_max"] == 3

        # Verify vocabulary complexity
        assert result["vocabulary_complexity_range"] == [0.3, 0.7]


class TestCorpusAnalyzerFeatureExtraction:
    """Test statistical feature extraction methods."""

    def test_extract_sentence_lengths(self, corpus_analyzer):
        """Test sentence length percentile extraction."""
        corpus_samples = [
            {"content": "Short sentence."},
            {"content": "This is a medium length sentence with some words."},
            {"content": "Very long sentence with many many words to make it longer."}
        ]

        result = corpus_analyzer._extract_sentence_lengths(corpus_samples)

        # Verify Percentiles object is returned
        assert isinstance(result, Percentiles)
        assert result.p10 > 0
        assert result.p25 > 0
        assert result.p50 > 0  # Median
        assert result.p75 > 0
        assert result.p90 > 0

        # Verify percentiles are in ascending order
        assert result.p10 <= result.p25 <= result.p50 <= result.p75 <= result.p90

    def test_extract_rhythm_patterns(self, corpus_analyzer):
        """Test rhythm pattern metrics extraction."""
        corpus_samples = [{"content": "Sample text"}]

        result = corpus_analyzer._extract_rhythm_patterns(corpus_samples)

        # Verify RhythmMetrics object is returned
        assert isinstance(result, RhythmMetrics)
        assert result.short_run_max > 0
        assert result.long_run_max > 0
        assert len(result.optimal_variation_range) == 2
        assert len(result.window_avg_range) == 2

    def test_extract_dialogue_ratios(self, corpus_analyzer):
        """Test dialogue ratio range extraction."""
        corpus_samples = [{"content": "「Hello」 said the character."}]

        result = corpus_analyzer._extract_dialogue_ratios(corpus_samples)

        # Verify tuple is returned
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert 0.0 <= result[0] <= 1.0
        assert 0.0 <= result[1] <= 1.0
        assert result[0] <= result[1]

    def test_extract_punctuation_styles(self, corpus_analyzer):
        """Test punctuation style preferences extraction."""
        corpus_samples = [{"content": "Sentence with, commas, and periods."}]

        result = corpus_analyzer._extract_punctuation_styles(corpus_samples)

        # Verify PunctuationMetrics object is returned
        assert isinstance(result, PunctuationMetrics)
        assert len(result.comma_avg_range) == 2
        assert result.comma_per_sentence_max > 0
        assert len(result.period_ratio_range) == 2

    def test_extract_vocabulary_complexity(self, corpus_analyzer):
        """Test vocabulary complexity range extraction."""
        corpus_samples = [{"content": "Simple words and complex terminology."}]

        result = corpus_analyzer._extract_vocabulary_complexity(corpus_samples)

        # Verify tuple is returned
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert 0.0 <= result[0] <= 1.0
        assert 0.0 <= result[1] <= 1.0
        assert result[0] <= result[1]


class TestCorpusAnalyzerCorpusHash:
    """Test corpus hash computation."""

    def test_compute_corpus_hash_consistency(self, corpus_analyzer):
        """Test corpus hash is consistent for same corpus."""
        corpus_samples1 = [{"content": "Sample 1"}, {"content": "Sample 2"}]
        corpus_samples2 = [{"content": "Sample 1"}, {"content": "Sample 2"}]

        hash1 = corpus_analyzer._compute_corpus_hash(corpus_samples1)
        hash2 = corpus_analyzer._compute_corpus_hash(corpus_samples2)

        # Verify hashes are identical for same corpus
        assert hash1 == hash2

    def test_compute_corpus_hash_uniqueness(self, corpus_analyzer):
        """Test corpus hash changes when corpus changes."""
        corpus_samples1 = [{"content": "Sample 1"}]
        corpus_samples2 = [{"content": "Sample 2"}]

        hash1 = corpus_analyzer._compute_corpus_hash(corpus_samples1)
        hash2 = corpus_analyzer._compute_corpus_hash(corpus_samples2)

        # Verify hashes are different for different corpus
        assert hash1 != hash2

    def test_compute_corpus_hash_format(self, corpus_analyzer):
        """Test corpus hash has correct format."""
        corpus_samples = [{"content": "Sample"}]

        corpus_hash = corpus_analyzer._compute_corpus_hash(corpus_samples)

        # Verify hash is 16 characters hex string
        assert isinstance(corpus_hash, str)
        assert len(corpus_hash) == 16
        assert all(c in "0123456789abcdef" for c in corpus_hash)


@pytest.mark.spec("SPEC-QUALITY-140")
class TestCorpusAnalyzerSpecCompliance:
    """Test SPEC-QUALITY-140 compliance."""

    def test_spec_corpus_baseline_extraction(
        self,
        corpus_analyzer,
        mock_corpus_repository
    ):
        """SPEC-QUALITY-140 §2.2.2: Verify corpus baseline extraction."""
        result = corpus_analyzer.build_baseline_metrics(
            genre="fantasy",
            target_audience="young_adult",
            project_root=Path("/tmp/test_project")
        )

        # Verify all required baseline metrics are present
        required_fields = [
            "genre",
            "target_audience",
            "sample_count",
            "sentence_length_distribution",
            "rhythm_patterns",
            "dialogue_ratio_range",
            "punctuation_style_preferences",
            "vocabulary_complexity_range",
            "corpus_hash"
        ]

        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

    def test_spec_cache_performance(self, corpus_analyzer, mock_corpus_repository):
        """SPEC-QUALITY-140 §4.1: Verify cache provides fast access."""
        import time

        # First call - populates cache
        start1 = time.time()
        corpus_analyzer.build_baseline_metrics(
            genre="fantasy",
            target_audience="young_adult",
            project_root=Path("/tmp/test_project")
        )
        duration1 = time.time() - start1

        # Second call - uses cache
        start2 = time.time()
        corpus_analyzer.build_baseline_metrics(
            genre="fantasy",
            target_audience="young_adult",
            project_root=Path("/tmp/test_project")
        )
        duration2 = time.time() - start2

        # Verify cache was used (repository called only once)
        assert mock_corpus_repository.load_corpus.call_count == 1, "Cache should prevent second repository call"

        # SPEC requires ≤100ms for cached access
        assert duration2 < 0.1, f"Cached access took {duration2}s, expected <100ms"

        # Note: We don't compare duration2 < duration1 because timing tests are flaky
        # at microsecond level due to system scheduler and load variations.
        # The functional test (repository call count) is more reliable.

    def test_spec_default_baselines_fallback(self, corpus_analyzer, mock_corpus_repository):
        """SPEC-QUALITY-140 §4.1: Verify default baselines when corpus unavailable."""
        # Simulate no corpus available
        mock_corpus_repository.load_corpus.return_value = []

        result = corpus_analyzer.build_baseline_metrics(
            genre="mystery",
            target_audience="adult",
            project_root=Path("/tmp/test_project")
        )

        # Verify default baselines are returned
        assert result["sample_count"] == 0
        assert result["corpus_hash"] == "default"
        assert result["genre"] == "mystery"
        assert result["target_audience"] == "adult"

        # Verify all required fields still present
        assert "sentence_length_distribution" in result
        assert "rhythm_patterns" in result
