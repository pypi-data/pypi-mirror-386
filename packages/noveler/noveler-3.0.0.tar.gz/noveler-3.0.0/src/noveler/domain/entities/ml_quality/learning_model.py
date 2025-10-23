# File: src/noveler/domain/entities/ml_quality/learning_model.py
# Purpose: Learning model entity for ML quality optimization
# Context: Represents trained ML models with metadata and validation metrics

"""
Learning Model Entity.

This entity represents a trained ML model used in quality optimization,
including metadata, training history, and validation metrics.

Contract: SPEC-QUALITY-140 §3.1
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class ModelType(Enum):
    """Type of ML model."""
    THRESHOLD_OPTIMIZER = "threshold_optimizer"
    WEIGHT_OPTIMIZER = "weight_optimizer"
    SEVERITY_ESTIMATOR = "severity_estimator"
    CORPUS_ANALYZER = "corpus_analyzer"


@dataclass(frozen=True)
class LearningModel:
    """
    Trained ML model entity.

    This entity represents a trained model with full metadata,
    training history, and validation metrics.

    Attributes:
        model_id: Unique identifier
        model_type: Type of model (threshold_optimizer, etc.)
        genre: Genre classification
        target_audience: Target audience classification
        training_date: When the model was trained
        training_samples: Number of samples used for training
        validation_metrics: Performance metrics (F1, RMSE, etc.)
        model_artifact_path: Path to serialized model file
        feature_schema: Schema of input features
        model_version: Model version string (semver)
        created_by: User or system that created the model
        notes: Optional training notes

    Invariants:
        - model_id must be unique
        - training_samples must be > 0
        - validation_metrics must contain at least one metric
        - model_artifact_path must exist if model is deployed

    Contract: SPEC-QUALITY-140 §3.1
    """
    model_id: str
    model_type: ModelType
    genre: str
    target_audience: str
    training_date: datetime
    training_samples: int
    validation_metrics: dict[str, float]
    model_artifact_path: Path
    feature_schema: dict[str, str]
    model_version: str = "1.0.0"
    created_by: str = "system"
    notes: Optional[str] = None

    def __post_init__(self):
        """Validate invariants."""
        if not self.model_id:
            raise ValueError("model_id cannot be empty")

        if self.training_samples <= 0:
            raise ValueError(f"training_samples must be > 0, got {self.training_samples}")

        if not self.validation_metrics:
            raise ValueError("validation_metrics cannot be empty")

        # Validate model_version format (semver)
        parts = self.model_version.split('.')
        if len(parts) != 3:
            raise ValueError(f"model_version must be semver format (x.y.z), got {self.model_version}")

    def is_better_than(self, other: "LearningModel", metric: str = "f1_score") -> bool:
        """
        Compare this model with another based on a validation metric.

        Args:
            other: Another LearningModel to compare
            metric: Metric to use for comparison (default: f1_score)

        Returns:
            True if this model performs better on the given metric

        Raises:
            ValueError: If metric not found in validation_metrics
        """
        if metric not in self.validation_metrics:
            raise ValueError(f"Metric '{metric}' not found in validation_metrics")

        if metric not in other.validation_metrics:
            raise ValueError(f"Metric '{metric}' not found in other.validation_metrics")

        return self.validation_metrics[metric] > other.validation_metrics[metric]

    def to_dict(self) -> dict:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the model entity
        """
        return {
            "model_id": self.model_id,
            "model_type": self.model_type.value,
            "genre": self.genre,
            "target_audience": self.target_audience,
            "training_date": self.training_date.isoformat(),
            "training_samples": self.training_samples,
            "validation_metrics": self.validation_metrics,
            "model_artifact_path": str(self.model_artifact_path),
            "feature_schema": self.feature_schema,
            "model_version": self.model_version,
            "created_by": self.created_by,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LearningModel":
        """
        Create LearningModel from dictionary.

        Args:
            data: Dictionary with model data

        Returns:
            LearningModel instance

        Raises:
            ValueError: If required fields are missing
        """
        return cls(
            model_id=data["model_id"],
            model_type=ModelType(data["model_type"]),
            genre=data["genre"],
            target_audience=data["target_audience"],
            training_date=datetime.fromisoformat(data["training_date"]),
            training_samples=data["training_samples"],
            validation_metrics=data["validation_metrics"],
            model_artifact_path=Path(data["model_artifact_path"]),
            feature_schema=data["feature_schema"],
            model_version=data.get("model_version", "1.0.0"),
            created_by=data.get("created_by", "system"),
            notes=data.get("notes")
        )

    def get_summary(self) -> str:
        """
        Get human-readable summary of the model.

        Returns:
            Summary string
        """
        metrics_str = ", ".join(
            f"{k}={v:.3f}" for k, v in self.validation_metrics.items()
        )
        return (
            f"{self.model_type.value} for {self.genre}/{self.target_audience} "
            f"(v{self.model_version}, {self.training_samples} samples, {metrics_str})"
        )
