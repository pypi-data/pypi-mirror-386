# File: tests/contracts/test_model_repository_contract.py
# Purpose: Contract tests for IModelRepository Protocol
# Context: Validates that any implementation of IModelRepository satisfies the expected interface

"""
Contract tests for IModelRepository.

These tests ensure that any implementation of IModelRepository adheres to the Protocol's contract:
- save_model(): Stores model metadata and artifact, returns ID
- load_model(): Retrieves model by ID (metadata + artifact bytes)
- list_models(): Lists models by genre/type
- delete_model(): Removes model by ID
- get_latest_model(): Retrieves newest model matching criteria
"""

import pytest
from pathlib import Path
from typing import Optional
from datetime import datetime


# Minimal in-memory implementation for contract testing
class InMemoryModelRepository:
    """Minimal in-memory implementation for contract validation."""

    def __init__(self):
        self._models: dict[str, tuple[dict, bytes]] = {}

    def save_model(
        self,
        model_metadata: dict,
        model_artifact: bytes,
        project_root: Optional[Path] = None
    ) -> str:
        """Save model metadata and artifact, return model ID."""
        model_id = f"model_{len(self._models) + 1:04d}"
        metadata_with_id = {
            **model_metadata,
            "model_id": model_id,
            "created_at": datetime.now().isoformat()
        }
        self._models[model_id] = (metadata_with_id, model_artifact)
        return model_id

    def load_model(
        self,
        model_id: str,
        project_root: Optional[Path] = None
    ) -> tuple[dict, bytes]:
        """Load model by ID. Returns (metadata, artifact_bytes)."""
        if model_id not in self._models:
            raise FileNotFoundError(f"Model not found: {model_id}")
        return self._models[model_id]

    def list_models(
        self,
        genre: Optional[str] = None,
        model_type: Optional[str] = None,
        project_root: Optional[Path] = None
    ) -> list[dict]:
        """List models matching filters (returns metadata only, not artifacts)."""
        results = []

        for model_id, (metadata, _) in self._models.items():
            if genre is not None and metadata.get("genre") != genre:
                continue
            if model_type is not None and metadata.get("model_type") != model_type:
                continue
            results.append(metadata)

        return results

    def delete_model(
        self,
        model_id: str,
        project_root: Optional[Path] = None
    ) -> bool:
        """Delete model by ID. Returns True if deleted, False if not found."""
        if model_id in self._models:
            del self._models[model_id]
            return True
        return False

    def get_latest_model(
        self,
        genre: str,
        model_type: str,
        project_root: Optional[Path] = None
    ) -> Optional[tuple[dict, bytes]]:
        """Get the latest model matching genre and type."""
        matches = [
            (metadata, artifact)
            for metadata, artifact in self._models.values()
            if metadata.get("genre") == genre and metadata.get("model_type") == model_type
        ]

        if not matches:
            return None

        # Sort by created_at descending (newest first)
        matches.sort(key=lambda x: x[0]["created_at"], reverse=True)
        return matches[0]


@pytest.fixture
def model_repo():
    """Provide an in-memory model repository for testing."""
    return InMemoryModelRepository()


class TestModelRepositoryContract:
    """Contract tests for IModelRepository Protocol."""

    def test_save_model_returns_string_id(self, model_repo, tmp_path):
        """Contract: save_model must return a non-empty string ID."""
        metadata = {
            "genre": "fantasy",
            "model_type": "THRESHOLD",
            "training_samples": 100
        }
        artifact = b"mock_model_data"

        model_id = model_repo.save_model(
            model_metadata=metadata,
            model_artifact=artifact,
            project_root=tmp_path
        )

        assert isinstance(model_id, str), "save_model must return string ID"
        assert len(model_id) > 0, "Model ID must not be empty"

    def test_load_model_returns_tuple(self, model_repo, tmp_path):
        """Contract: load_model must return (dict, bytes) tuple."""
        metadata = {"genre": "fantasy", "model_type": "THRESHOLD"}
        artifact = b"model_bytes"

        model_id = model_repo.save_model(
            model_metadata=metadata,
            model_artifact=artifact,
            project_root=tmp_path
        )

        loaded_metadata, loaded_artifact = model_repo.load_model(
            model_id=model_id,
            project_root=tmp_path
        )

        assert isinstance(loaded_metadata, dict), "Metadata must be dict"
        assert isinstance(loaded_artifact, bytes), "Artifact must be bytes"
        assert loaded_artifact == artifact, "Artifact must match saved data"

    def test_load_model_raises_on_nonexistent_id(self, model_repo, tmp_path):
        """Contract: load_model must raise exception for nonexistent model ID."""
        with pytest.raises((FileNotFoundError, KeyError)):
            model_repo.load_model(
                model_id="nonexistent",
                project_root=tmp_path
            )

    def test_list_models_returns_list_of_dicts(self, model_repo, tmp_path):
        """Contract: list_models must return list of metadata dicts."""
        # Save some models
        for i in range(3):
            model_repo.save_model(
                model_metadata={"genre": "fantasy", "model_type": "THRESHOLD", "index": i},
                model_artifact=b"data",
                project_root=tmp_path
            )

        results = model_repo.list_models(project_root=tmp_path)

        assert isinstance(results, list), "list_models must return list"
        assert len(results) == 3, "Should return all saved models"
        assert all(isinstance(m, dict) for m in results), "All items must be dicts"

    def test_list_models_filters_by_genre(self, model_repo, tmp_path):
        """Contract: list_models must filter by genre when specified."""
        # Save models with different genres
        model_repo.save_model(
            model_metadata={"genre": "fantasy", "model_type": "THRESHOLD"},
            model_artifact=b"data1",
            project_root=tmp_path
        )
        model_repo.save_model(
            model_metadata={"genre": "scifi", "model_type": "THRESHOLD"},
            model_artifact=b"data2",
            project_root=tmp_path
        )

        # Filter by genre
        results = model_repo.list_models(
            genre="fantasy",
            project_root=tmp_path
        )

        assert len(results) == 1, "Should return only matching genre"
        assert results[0]["genre"] == "fantasy", "Result must match genre filter"

    def test_list_models_filters_by_model_type(self, model_repo, tmp_path):
        """Contract: list_models must filter by model_type when specified."""
        # Save models with different types
        model_repo.save_model(
            model_metadata={"genre": "fantasy", "model_type": "THRESHOLD"},
            model_artifact=b"data1",
            project_root=tmp_path
        )
        model_repo.save_model(
            model_metadata={"genre": "fantasy", "model_type": "WEIGHT"},
            model_artifact=b"data2",
            project_root=tmp_path
        )

        # Filter by type
        results = model_repo.list_models(
            model_type="THRESHOLD",
            project_root=tmp_path
        )

        assert len(results) == 1, "Should return only matching type"
        assert results[0]["model_type"] == "THRESHOLD", "Result must match type filter"

    def test_delete_model_returns_bool(self, model_repo, tmp_path):
        """Contract: delete_model must return bool indicating success."""
        # Save a model
        model_id = model_repo.save_model(
            model_metadata={"genre": "fantasy", "model_type": "THRESHOLD"},
            model_artifact=b"data",
            project_root=tmp_path
        )

        # Delete existing model
        result = model_repo.delete_model(
            model_id=model_id,
            project_root=tmp_path
        )
        assert result is True, "delete_model must return True when successful"

        # Try deleting non-existent model
        result = model_repo.delete_model(
            model_id="nonexistent",
            project_root=tmp_path
        )
        assert result is False, "delete_model must return False when ID not found"

    def test_get_latest_model_returns_newest(self, model_repo, tmp_path):
        """Contract: get_latest_model must return the newest matching model."""
        import time

        # Save models with small time gaps
        model_repo.save_model(
            model_metadata={"genre": "fantasy", "model_type": "THRESHOLD", "version": "1.0"},
            model_artifact=b"old",
            project_root=tmp_path
        )

        time.sleep(0.01)  # Small delay to ensure different timestamps

        model_repo.save_model(
            model_metadata={"genre": "fantasy", "model_type": "THRESHOLD", "version": "2.0"},
            model_artifact=b"new",
            project_root=tmp_path
        )

        # Get latest
        result = model_repo.get_latest_model(
            genre="fantasy",
            model_type="THRESHOLD",
            project_root=tmp_path
        )

        assert result is not None, "Should find matching model"
        metadata, artifact = result
        assert metadata["version"] == "2.0", "Should return newest model"
        assert artifact == b"new", "Should return newest artifact"

    def test_get_latest_model_returns_none_when_no_match(self, model_repo, tmp_path):
        """Contract: get_latest_model must return None when no matching model exists."""
        result = model_repo.get_latest_model(
            genre="nonexistent",
            model_type="THRESHOLD",
            project_root=tmp_path
        )

        assert result is None, "Should return None when no matching model"

    def test_empty_repository_list_returns_empty_list(self, model_repo, tmp_path):
        """Contract: list_models on empty repository must return empty list."""
        results = model_repo.list_models(project_root=tmp_path)

        assert isinstance(results, list), "Must return list even when empty"
        assert len(results) == 0, "Should return empty list for empty repository"


@pytest.mark.spec("SPEC-QUALITY-140")
class TestModelRepositorySpecCompliance:
    """Verify compliance with SPEC-QUALITY-140 requirements."""

    def test_model_repository_contract_coverage(self):
        """SPEC-QUALITY-140: Verify all required methods are defined in Protocol."""
        from noveler.domain.protocols.model_repository_protocol import IModelRepository

        required_methods = [
            "save_model",
            "load_model",
            "list_models",
            "delete_model",
            "get_latest_model"
        ]

        for method_name in required_methods:
            assert hasattr(IModelRepository, method_name), \
                f"IModelRepository must define {method_name} method"

    def test_in_memory_implementation_is_valid_protocol(self):
        """Verify that InMemoryModelRepository satisfies IModelRepository Protocol."""
        repo = InMemoryModelRepository()

        required_methods = [
            "save_model",
            "load_model",
            "list_models",
            "delete_model",
            "get_latest_model"
        ]

        for method_name in required_methods:
            assert hasattr(repo, method_name), \
                f"Implementation must have {method_name} method"
            assert callable(getattr(repo, method_name)), \
                f"{method_name} must be callable"
