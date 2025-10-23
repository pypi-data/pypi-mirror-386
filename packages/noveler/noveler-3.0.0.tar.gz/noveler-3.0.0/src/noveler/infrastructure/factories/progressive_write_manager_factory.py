"""Factory helpers for constructing :class:`ProgressiveWriteManager` instances."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable

from noveler.domain.interfaces.logger_interface import ILogger
from noveler.domain.interfaces.progressive_write_llm_executor import ProgressiveWriteLLMExecutor
from noveler.domain.services.progressive_write_manager import ProgressiveWriteManager
from noveler.domain.services.progressive_write_runtime_deps import (
    ArtifactStoreFactory,
    ConfigurationManagerFactory,
    FeedbackSystemFactory,
    IOLoggerFactory,
    LLMExecutorFactory,
    LoggerFactory,
    PathServiceFactory,
    ProgressDisplayFactory,
    ProgressiveWriteRuntimeDeps,
)


@dataclass
class ProgressiveWriteRuntimeOverrides:
    """Selective overrides for :class:`ProgressiveWriteRuntimeDeps`."""

    llm_executor: ProgressiveWriteLLMExecutor | None = None
    llm_executor_factory: LLMExecutorFactory | None = None
    path_service_factory: PathServiceFactory | None = None
    artifact_store_factory: ArtifactStoreFactory | None = None
    progress_display_factory: ProgressDisplayFactory | None = None
    feedback_system_factory: FeedbackSystemFactory | None = None
    logger_factory: LoggerFactory | None = None
    performance_monitor: Callable[[str], Callable[..., Any]] | None = None
    async_optimizer: Any | None = None
    io_logger_factory: IOLoggerFactory | None = None
    configuration_manager_factory: ConfigurationManagerFactory | None = None

    def apply(self, base: ProgressiveWriteRuntimeDeps) -> ProgressiveWriteRuntimeDeps:
        data: dict[str, Any] = {}
        for field_name in (
            "llm_executor",
            "llm_executor_factory",
            "path_service_factory",
            "artifact_store_factory",
            "progress_display_factory",
            "feedback_system_factory",
            "logger_factory",
            "performance_monitor",
            "async_optimizer",
            "io_logger_factory",
            "configuration_manager_factory",
        ):
            value = getattr(self, field_name)
            if value is not None:
                data[field_name] = value

        if not data:
            return base
        return replace(base, **data)


def build_runtime_deps(overrides: ProgressiveWriteRuntimeOverrides | None = None) -> ProgressiveWriteRuntimeDeps:
    """Create runtime dependencies honoring optional overrides."""

    deps = ProgressiveWriteRuntimeDeps.with_defaults()
    if overrides is None:
        return deps
    return overrides.apply(deps)


def create_progressive_write_manager(
    project_root: str | Path,
    episode_number: int,
    *,
    overrides: ProgressiveWriteRuntimeOverrides | None = None,
    logger: ILogger | None = None,
    llm_executor: ProgressiveWriteLLMExecutor | None = None,
) -> ProgressiveWriteManager:
    """Factory function for constructing :class:`ProgressiveWriteManager` instances.

    Parameters
    ----------
    project_root:
        Base directory of the target project.
    episode_number:
        Episode identifier passed to the manager.
    overrides:
        Optional overrides to customise runtime dependencies per entry point.
    logger:
        Logger instance injected into the manager.
    llm_executor:
        Optional executor override. When provided it bypasses the facade factory
        contained in ``ProgressiveWriteRuntimeDeps``.
    """

    deps = build_runtime_deps(overrides)
    return ProgressiveWriteManager(
        project_root=project_root,
        episode_number=episode_number,
        llm_executor=llm_executor,
        logger=logger,
        deps=deps,
    )
