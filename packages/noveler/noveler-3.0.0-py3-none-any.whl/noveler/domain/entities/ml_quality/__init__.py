# File: src/noveler/domain/entities/ml_quality/__init__.py
# Purpose: ML quality entities module exports
# Context: Provides ML-enhanced quality evaluation entities

"""
ML Quality Entities.

This module provides entities for ML-enhanced quality evaluation:
- LearningModel: Trained ML model with metadata
- QualityFeedback: Evaluation feedback for learning
- CorrectionRecord: User correction record

Contract: SPEC-QUALITY-140 §3
"""

from noveler.domain.entities.ml_quality.learning_model import (
    LearningModel,
    ModelType,
)

from noveler.domain.entities.ml_quality.quality_feedback import (
    QualityFeedback,
    CorrectionRecord,
    EvaluationOutcome,
    FeedbackSource,
)

__all__ = [
    # Learning model
    "LearningModel",
    "ModelType",

    # Quality feedback
    "QualityFeedback",
    "CorrectionRecord",
    "EvaluationOutcome",
    "FeedbackSource",
]
