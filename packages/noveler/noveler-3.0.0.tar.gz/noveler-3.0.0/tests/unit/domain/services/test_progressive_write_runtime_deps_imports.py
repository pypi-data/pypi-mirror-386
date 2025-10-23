# File: tests/unit/domain/services/test_progressive_write_runtime_deps_imports.py
# Purpose: Verify that ProgressiveWriteRuntimeDeps loads optional dependencies lazily and falls back safely.
# Context: Guards PLC0415 refactor by asserting lazy import helpers handle missing infrastructure modules.

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from pytest import MonkeyPatch

from noveler.domain.services.progressive_write_runtime_deps import (
    NullFeedbackSystem,
    NullLLMIOLogger,
    NullPathService,
    NullProgressDisplay,
    ProgressiveWriteRuntimeDeps,
    _noop_performance_monitor,
)


def test_with_defaults_handles_missing_optional_modules(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    """Ensure lazy import helpers return safe defaults when optional modules are unavailable."""

    requested: list[tuple[str, str]] = []

    def fake_loader(module_path: str, attribute: str) -> None:
        requested.append((module_path, attribute))
        return None

    def fake_import(module_path: str) -> None:
        raise ImportError(f"{module_path} not available")

    monkeypatch.setattr(
        "noveler.domain.services.progressive_write_runtime_deps._load_optional_attr",
        fake_loader,
    )
    monkeypatch.setattr(
        "noveler.domain.services.progressive_write_runtime_deps.importlib.import_module",
        fake_import,
    )

    deps = ProgressiveWriteRuntimeDeps.with_defaults()

    assert deps.llm_executor_factory is None
    assert deps.ensure_llm_executor() is None

    path_service = deps.create_path_service(tmp_path)
    assert isinstance(path_service, NullPathService)

    artifact_store = deps.create_artifact_store(tmp_path)
    artifact_id = artifact_store.store(content="dummy")
    assert artifact_id.startswith("null_artifact_")

    progress_display = deps.create_progress_display(episode_number=1, total_steps=2)
    assert isinstance(progress_display, NullProgressDisplay)

    feedback_system = deps.create_feedback_system(episode_number=1)
    assert isinstance(feedback_system, NullFeedbackSystem)

    io_logger = deps.create_io_logger(tmp_path)
    assert isinstance(io_logger, NullLLMIOLogger)

    assert deps.get_configuration_manager() is None
    assert deps.performance_monitor is _noop_performance_monitor
    assert deps.async_optimizer is None

    expected_requests: Iterable[tuple[str, str]] = {
        (
            "noveler.infrastructure.factories.progressive_write_llm_executor_factory",
            "create_progressive_write_llm_executor",
        ),
        (
            "noveler.infrastructure.factories.path_service_factory",
            "create_path_service",
        ),
        (
            "noveler.infrastructure.factories.path_service_factory",
            "create_mcp_aware_path_service",
        ),
        ("noveler.domain.services.artifact_store_service", "create_artifact_store"),
        ("noveler.presentation.ui.progress_display", "ProgressDisplaySystem"),
        ("noveler.presentation.ui.feedback_system", "InteractiveFeedbackSystem"),
        ("noveler.infrastructure.llm.llm_io_logger", "LLMIOLogger"),
        (
            "noveler.infrastructure.factories.configuration_service_factory",
            "get_configuration_manager",
        ),
    }

    assert set(expected_requests).issubset(set(requested))
