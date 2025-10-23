# File: src/noveler/domain/services/ml_quality/__init__.py
# Purpose: ML quality optimization services module exports
# Context: Provides ML-enhanced quality evaluation services

"""
ML Quality Optimization Services.

This module provides ML-enhanced quality evaluation services including:
- MLQualityOptimizer: Orchestrator for ML-based optimization
- CorpusAnalyzer: Extract baseline metrics from similar works
- DynamicThresholdAdjuster: Auto-tune quality gate thresholds
- WeightOptimizer: Learn optimal aspect weights
- SeverityEstimator: Context-aware severity estimation

Contract: SPEC-QUALITY-140
"""

from noveler.domain.services.ml_quality.ml_quality_optimizer import (
    MLQualityOptimizer,
    LearningMode,
    ProjectContext,
    OptimizedQualityResult,
)

from noveler.domain.services.ml_quality.corpus_analyzer import (
    CorpusAnalyzer,
    CorpusMetrics,
    Percentiles,
    RhythmMetrics,
    PunctuationMetrics,
)

from noveler.domain.services.ml_quality.dynamic_threshold_adjuster import (
    DynamicThresholdAdjuster,
    AdjustmentPolicy,
    AdjustedThresholds,
)

from noveler.domain.services.ml_quality.weight_optimizer import (
    WeightOptimizer,
    OptimizationObjective,
    OptimizedWeights,
)

from noveler.domain.services.ml_quality.severity_estimator import (
    SeverityEstimator,
    SeverityEstimate,
)

__all__ = [
    # Main orchestrator
    "MLQualityOptimizer",
    "LearningMode",
    "ProjectContext",
    "OptimizedQualityResult",

    # Corpus analysis
    "CorpusAnalyzer",
    "CorpusMetrics",
    "Percentiles",
    "RhythmMetrics",
    "PunctuationMetrics",

    # Threshold adjustment
    "DynamicThresholdAdjuster",
    "AdjustmentPolicy",
    "AdjustedThresholds",

    # Weight optimization
    "WeightOptimizer",
    "OptimizationObjective",
    "OptimizedWeights",

    # Severity estimation
    "SeverityEstimator",
    "SeverityEstimate",
]
