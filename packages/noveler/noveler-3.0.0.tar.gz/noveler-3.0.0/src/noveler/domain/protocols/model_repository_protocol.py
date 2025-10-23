# File: src/noveler/domain/protocols/model_repository_protocol.py
# Purpose: Protocol definition for ML model repository
# Context: Define interface for trained model storage and retrieval

"""
Model Repository Protocol.

This protocol defines the interface for accessing and managing trained ML models
used in quality optimization.

Contract: SPEC-QUALITY-140 §6.2.3
"""

from pathlib import Path
from typing import Optional, Protocol


class IModelRepository(Protocol):
    """
    Protocol for ML model repository.

    This protocol defines methods for accessing and managing trained ML models
    (threshold optimizers, weight optimizers, severity estimators).

    Implementations:
    - FileModelRepository: File-based model storage
    - S3ModelRepository: Cloud-based model storage (future)

    Contract: SPEC-QUALITY-140 §6.2.3
    """

    def save_model(
        self,
        model_metadata: dict,
        model_artifact: bytes,
        project_root: Path
    ) -> str:
        """
        Save trained model and return model_id.

        Args:
            model_metadata: Model metadata dict with:
                - model_type: str (THRESHOLD_OPTIMIZER, WEIGHT_OPTIMIZER, SEVERITY_ESTIMATOR)
                - genre: str
                - target_audience: str
                - training_date: datetime
                - training_samples: int
                - validation_metrics: dict[str, float]
                - feature_schema: dict[str, str]
            model_artifact: Serialized model bytes (pickle, joblib, etc.)
            project_root: Project root for model resolution

        Returns:
            model_id: Unique identifier for saved model

        Raises:
            ModelSaveError: If save operation fails
        """
        ...

    def load_model(
        self,
        model_id: str,
        project_root: Path
    ) -> tuple[dict, bytes]:
        """
        Load model metadata and artifact.

        Args:
            model_id: Model identifier
            project_root: Project root for model resolution

        Returns:
            (model_metadata, model_artifact) tuple

        Raises:
            ModelNotFoundError: If model not found
            ModelLoadError: If load operation fails
        """
        ...

    def list_models(
        self,
        project_root: Path,
        model_type: Optional[str] = None,
        genre: Optional[str] = None
    ) -> list[dict]:
        """
        List available models with optional filters.

        Args:
            project_root: Project root for model resolution
            model_type: Optional filter by model type
            genre: Optional filter by genre

        Returns:
            List of model metadata dictionaries

        Raises:
            ModelListError: If list operation fails
        """
        ...

    def delete_model(
        self,
        model_id: str,
        project_root: Path
    ) -> bool:
        """
        Delete a model by ID.

        Args:
            model_id: Model identifier
            project_root: Project root for model resolution

        Returns:
            True if deleted, False if not found

        Raises:
            ModelDeleteError: If delete operation fails
        """
        ...

    def get_latest_model(
        self,
        model_type: str,
        genre: str,
        target_audience: str,
        project_root: Path
    ) -> Optional[tuple[dict, bytes]]:
        """
        Get the latest model for given type/genre/audience.

        This is a convenience method for fetching the most recent model
        without knowing the model_id.

        Args:
            model_type: Model type (THRESHOLD_OPTIMIZER, etc.)
            genre: Genre classification
            target_audience: Target audience
            project_root: Project root for model resolution

        Returns:
            (model_metadata, model_artifact) tuple, or None if not found

        Raises:
            ModelLoadError: If load operation fails
        """
        ...
