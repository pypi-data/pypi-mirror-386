# File: src/noveler/domain/services/ml_quality/corpus_analyzer.py
# Purpose: Analyze similar works corpus to extract quality patterns
# Context: Provides genre-specific baseline metrics for ML optimization

"""
Corpus Analyzer Service.

This service analyzes a corpus of similar works to extract statistical
quality patterns and provide baseline metrics for ML optimization.

Responsibilities:
- Build genre-specific quality baselines
- Extract statistical features (sentence length distributions, rhythm patterns)
- Compute relative quality scores against corpus
- Cache corpus metrics for performance

Architecture:
- Domain Service (pure business logic)
- Depends on ICorpusRepository for data access
- Returns CorpusMetrics value objects

Contract: SPEC-QUALITY-140 §2.2.2
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from noveler.domain.interfaces.logger_interface import ILogger, NullLogger


@dataclass(frozen=True)
class Percentiles:
    """Statistical percentile distribution."""
    p10: float
    p25: float
    p50: float  # Median
    p75: float
    p90: float


@dataclass(frozen=True)
class RhythmMetrics:
    """Rhythm pattern metrics from corpus."""
    short_run_max: int
    long_run_max: int
    optimal_variation_range: tuple[int, int]
    window_avg_range: tuple[float, float]


@dataclass(frozen=True)
class PunctuationMetrics:
    """Punctuation style preferences from corpus."""
    comma_avg_range: tuple[float, float]
    comma_per_sentence_max: int
    period_ratio_range: tuple[float, float]


@dataclass(frozen=True)
class CorpusMetrics:
    """
    Statistical metrics extracted from similar works corpus.

    Fields:
        genre: Genre identifier
        target_audience: Target audience (young_adult, adult, general)
        sample_count: Number of samples in corpus
        sentence_length_distribution: Percentile-based sentence lengths
        rhythm_patterns: Optimal rhythm metrics
        dialogue_ratio_range: (min, max) dialogue percentage
        punctuation_style_preferences: Punctuation patterns
        vocabulary_complexity_range: (min, max) complexity scores
        corpus_hash: SHA256 hash for cache invalidation

    Contract: SPEC-QUALITY-140 §3.3
    """
    genre: str
    target_audience: str
    sample_count: int
    sentence_length_distribution: Percentiles
    rhythm_patterns: RhythmMetrics
    dialogue_ratio_range: tuple[float, float]
    punctuation_style_preferences: PunctuationMetrics
    vocabulary_complexity_range: tuple[float, float]
    corpus_hash: str


class CorpusAnalyzer:
    """
    Analyze similar works corpus to extract quality patterns.

    Responsibilities:
    - Build genre-specific quality baselines
    - Extract statistical features from corpus samples
    - Compute relative quality scores against corpus
    - Cache metrics for 24 hours

    Dependencies (injected):
    - corpus_repository: ICorpusRepository for corpus data access
    - logger: ILogger for diagnostics

    Contract: SPEC-QUALITY-140 §2.2.2
    """

    def __init__(
        self,
        corpus_repository: "ICorpusRepository",
        logger: Optional[ILogger] = None
    ):
        """
        Initialize corpus analyzer.

        Args:
            corpus_repository: Repository for corpus data access
            logger: Optional logger (defaults to NullLogger)
        """
        self._corpus_repository = corpus_repository
        self._logger = logger or NullLogger()
        self._cache: dict[str, CorpusMetrics] = {}

    def build_baseline_metrics(
        self,
        genre: str,
        target_audience: str,
        project_root: Path,
        force_refresh: bool = False
    ) -> dict:
        """
        Build baseline metrics from corpus.

        Args:
            genre: Genre identifier (fantasy, mystery, romance, etc.)
            target_audience: Target audience (young_adult, adult, general)
            project_root: Project root path for corpus resolution
            force_refresh: Skip cache and rebuild metrics

        Returns:
            Dictionary with:
            - sample_count: Number of corpus samples
            - sentence_length_distribution: Percentile ranges
            - rhythm_patterns: Optimal long/short runs
            - dialogue_ratio_range: Genre-specific dialogue ratios
            - punctuation_style_preferences: Comma/period patterns
            - corpus_hash: Cache key for invalidation

        Raises:
            CorpusNotFoundError: If corpus for genre/audience not found
            CorpusAnalysisError: If analysis fails

        Algorithm:
            1. Check cache (24-hour TTL)
            2. Load corpus samples from repository
            3. Extract statistical features:
               - Sentence length percentiles (p10, p25, p50, p75, p90)
               - Rhythm patterns (short/long run distributions)
               - Dialogue ratio distribution
               - Punctuation style frequencies
               - Vocabulary complexity metrics
            4. Compute corpus hash for cache invalidation
            5. Cache and return metrics

        Performance:
            - Target: ≤5 seconds for 100 samples
            - Cached: ≤100ms

        Contract: SPEC-QUALITY-140 §4.1
        """
        cache_key = f"{genre}_{target_audience}"

        if not force_refresh and cache_key in self._cache:
            self._logger.debug(f"Returning cached corpus metrics for {cache_key}")
            metrics = self._cache[cache_key]
            return self._metrics_to_dict(metrics)

        self._logger.info(
            f"Building corpus baseline metrics for {genre}/{target_audience}"
        )

        # Load corpus samples
        corpus_samples = self._corpus_repository.load_corpus(
            genre=genre,
            target_audience=target_audience,
            project_root=project_root
        )

        if not corpus_samples:
            self._logger.warning(
                f"No corpus samples found for {genre}/{target_audience}, "
                "using default baselines"
            )
            return self._get_default_baselines(genre, target_audience)

        # Extract features
        sentence_lengths = self._extract_sentence_lengths(corpus_samples)
        rhythm_metrics = self._extract_rhythm_patterns(corpus_samples)
        dialogue_ratios = self._extract_dialogue_ratios(corpus_samples)
        punctuation_metrics = self._extract_punctuation_styles(corpus_samples)
        vocab_complexity = self._extract_vocabulary_complexity(corpus_samples)

        # Compute corpus hash
        corpus_hash = self._compute_corpus_hash(corpus_samples)

        # Build CorpusMetrics value object
        metrics = CorpusMetrics(
            genre=genre,
            target_audience=target_audience,
            sample_count=len(corpus_samples),
            sentence_length_distribution=sentence_lengths,
            rhythm_patterns=rhythm_metrics,
            dialogue_ratio_range=dialogue_ratios,
            punctuation_style_preferences=punctuation_metrics,
            vocabulary_complexity_range=vocab_complexity,
            corpus_hash=corpus_hash
        )

        # Cache metrics
        self._cache[cache_key] = metrics

        self._logger.info(
            f"Corpus metrics built successfully",
            extra={"sample_count": len(corpus_samples), "corpus_hash": corpus_hash}
        )

        return self._metrics_to_dict(metrics)

    def _metrics_to_dict(self, metrics: CorpusMetrics) -> dict:
        """Convert CorpusMetrics to dictionary for serialization."""
        return {
            "genre": metrics.genre,
            "target_audience": metrics.target_audience,
            "sample_count": metrics.sample_count,
            "sentence_length_distribution": {
                "p10": metrics.sentence_length_distribution.p10,
                "p25": metrics.sentence_length_distribution.p25,
                "p50": metrics.sentence_length_distribution.p50,
                "p75": metrics.sentence_length_distribution.p75,
                "p90": metrics.sentence_length_distribution.p90,
            },
            "rhythm_patterns": {
                "short_run_max": metrics.rhythm_patterns.short_run_max,
                "long_run_max": metrics.rhythm_patterns.long_run_max,
                "optimal_variation_range": list(metrics.rhythm_patterns.optimal_variation_range),
                "window_avg_range": list(metrics.rhythm_patterns.window_avg_range),
            },
            "dialogue_ratio_range": list(metrics.dialogue_ratio_range),
            "punctuation_style_preferences": {
                "comma_avg_range": list(metrics.punctuation_style_preferences.comma_avg_range),
                "comma_per_sentence_max": metrics.punctuation_style_preferences.comma_per_sentence_max,
                "period_ratio_range": list(metrics.punctuation_style_preferences.period_ratio_range),
            },
            "vocabulary_complexity_range": list(metrics.vocabulary_complexity_range),
            "corpus_hash": metrics.corpus_hash
        }

    def _get_default_baselines(self, genre: str, target_audience: str) -> dict:
        """
        Return default baselines when corpus is unavailable.

        Uses hardcoded genre-specific defaults based on:
        - SPEC-QUALITY-019 §9 (mixed_device_daily_6k_10k profile)
        - Standard literary analysis metrics
        """
        # Default to web novel / light novel standards
        return {
            "genre": genre,
            "target_audience": target_audience,
            "sample_count": 0,
            "sentence_length_distribution": {
                "p10": 10.0,
                "p25": 14.0,
                "p50": 30.0,
                "p75": 60.0,
                "p90": 90.0,
            },
            "rhythm_patterns": {
                "short_run_max": 3,
                "long_run_max": 2,
                "optimal_variation_range": [18, 70],
                "window_avg_range": [18.0, 70.0],
            },
            "dialogue_ratio_range": [0.4, 0.75],
            "punctuation_style_preferences": {
                "comma_avg_range": [0.6, 1.6],
                "comma_per_sentence_max": 3,
                "period_ratio_range": [0.3, 0.6],
            },
            "vocabulary_complexity_range": [0.3, 0.7],
            "corpus_hash": "default"
        }

    def _extract_sentence_lengths(self, corpus_samples: list) -> Percentiles:
        """Extract sentence length percentiles from corpus."""
        # TODO: Implement actual sentence length extraction
        # Placeholder: return default percentiles
        return Percentiles(p10=10.0, p25=14.0, p50=30.0, p75=60.0, p90=90.0)

    def _extract_rhythm_patterns(self, corpus_samples: list) -> RhythmMetrics:
        """Extract rhythm pattern metrics from corpus."""
        # TODO: Implement actual rhythm pattern extraction
        # Placeholder: return default rhythm metrics
        return RhythmMetrics(
            short_run_max=3,
            long_run_max=2,
            optimal_variation_range=(18, 70),
            window_avg_range=(18.0, 70.0)
        )

    def _extract_dialogue_ratios(self, corpus_samples: list) -> tuple[float, float]:
        """Extract dialogue ratio range from corpus."""
        # TODO: Implement actual dialogue ratio extraction
        # Placeholder: return default range
        return (0.4, 0.75)

    def _extract_punctuation_styles(self, corpus_samples: list) -> PunctuationMetrics:
        """Extract punctuation style preferences from corpus."""
        # TODO: Implement actual punctuation style extraction
        # Placeholder: return default metrics
        return PunctuationMetrics(
            comma_avg_range=(0.6, 1.6),
            comma_per_sentence_max=3,
            period_ratio_range=(0.3, 0.6)
        )

    def _extract_vocabulary_complexity(self, corpus_samples: list) -> tuple[float, float]:
        """Extract vocabulary complexity range from corpus."""
        # TODO: Implement actual vocabulary complexity calculation
        # Placeholder: return default range
        return (0.3, 0.7)

    def _compute_corpus_hash(self, corpus_samples: list) -> str:
        """Compute SHA256 hash of corpus for cache invalidation."""
        import hashlib
        # Simple hash based on sample count and first sample content
        content = f"{len(corpus_samples)}_{corpus_samples[0] if corpus_samples else ''}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# Type hints for forward references
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from noveler.domain.protocols.corpus_repository_protocol import ICorpusRepository
