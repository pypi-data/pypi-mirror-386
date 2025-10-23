# File: tests/unit/infrastructure/factories/test_ml_similarity_service_factory.py
# Purpose: Ensure ML similarity service factory wires default adapters and logger.
# Context: Validates infrastructure factory behaves as integration point for ML similarity service.

"""Tests for ml_similarity_service_factory helpers."""

from pathlib import Path

from noveler.infrastructure.factories.ml_similarity_service_factory import (
    create_ml_similarity_service,
    create_ml_similarity_service_with_overrides,
)


def test_create_ml_similarity_service_injects_defaults(tmp_path):
    service = create_ml_similarity_service(project_root=tmp_path, enable_advanced_ml=False)

    assert service.project_root == Path(tmp_path)
    assert hasattr(service, "similarity_analyzer")
    assert hasattr(service, "_logger")


def test_create_ml_similarity_service_with_overrides(tmp_path):
    service = create_ml_similarity_service_with_overrides(project_root=tmp_path)

    assert service.project_root == Path(tmp_path)
    assert hasattr(service, "similarity_analyzer")
