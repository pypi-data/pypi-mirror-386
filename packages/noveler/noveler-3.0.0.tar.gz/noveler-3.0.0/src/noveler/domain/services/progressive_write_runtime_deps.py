# File: src/noveler/domain/services/progressive_write_runtime_deps.py
# Purpose: Manage optional runtime dependencies for ProgressiveWriteManager with safe fallbacks.
# Context: Bridges domain services to infrastructure/presentation modules while avoiding hard imports.

"""Dependency bundle helpers for :mod:`progressive_write_manager`."""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from pathlib import Path

from noveler.domain.value_objects.path_configuration import get_default_manuscript_dir
from typing import Any, Callable

from noveler.domain.interfaces.logger_interface import ILogger, NullLogger
from noveler.domain.interfaces.progressive_write_llm_executor import ProgressiveWriteLLMExecutor


def _load_optional_module(module_path: str) -> Any | None:
    """Return the imported module or ``None`` if import fails."""

    try:
        return importlib.import_module(module_path)
    except Exception:
        return None


def _load_optional_attr(module_path: str, attribute: str) -> Any | None:
    """Return attribute from module when available, otherwise ``None``."""

    module = _load_optional_module(module_path)
    if module is None:
        return None
    return getattr(module, attribute, None)


def _noop_performance_monitor(_: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        return func

    return decorator


class NullProgressDisplay:
    """Fallback implementation used when real UI components are unavailable."""

    def __init__(self, *_: Any, **__: Any) -> None:
        self._steps: dict[Any, str] = {}

    def start_step(self, step_id: Any) -> None:  # pragma: no cover - trivial
        self._steps[step_id] = "in_progress"

    def complete_step(self, step_id: Any, success: bool = True) -> None:  # pragma: no cover - trivial
        self._steps[step_id] = "success" if success else "failed"

    def fail_step(self, step_id: Any, message: str | None = None) -> None:  # pragma: no cover - trivial
        self._steps[step_id] = message or "failed"


class NullFeedbackSystem:
    """No-op feedback system used outside interactive environments."""

    def __init__(self, *_: Any, **__: Any) -> None:  # pragma: no cover - trivial
        self._messages: list[tuple[str, str]] = []

    def show_error(self, title: str, message: str, **__: Any) -> None:  # pragma: no cover - trivial
        self._messages.append((title, message))

    def request_confirmation(self, _title: str, _message: str, **__: Any) -> bool:  # pragma: no cover - trivial
        return False


class NullLLMIOLogger:
    """Lightweight logger stub for offline execution paths."""

    def __init__(self, *_: Any, **__: Any) -> None:  # pragma: no cover - trivial
        self.records: list[dict[str, Any]] = []

    def save_stage_io(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - trivial
        self.records.append({"args": args, "kwargs": kwargs})


class NullArtifactStore:
    """In-memory artifact store used when the real implementation is unavailable."""

    def __init__(self) -> None:  # pragma: no cover - trivial
        self._artifacts: dict[str, dict[str, Any]] = {}
        self._counter = 0

    def store(self, *, content: str, **metadata: Any) -> str:
        self._counter += 1
        artifact_id = f"null_artifact_{self._counter}"
        self._artifacts[artifact_id] = {"content": content, **metadata}
        return artifact_id

    def list_artifacts(self) -> list[dict[str, Any]]:  # pragma: no cover - trivial
        return [
            {"artifact_id": key, **value}
            for key, value in self._artifacts.items()
        ]

    def get_metadata(self, artifact_id: str) -> Any:  # pragma: no cover - trivial
        return self._artifacts.get(artifact_id)

    def fetch(self, artifact_id: str) -> str | None:  # pragma: no cover - trivial
        entry = self._artifacts.get(artifact_id)
        if not entry:
            return None
        return entry.get("content")


class NullPathService:
    """Minimal path service used when infrastructure factory is unavailable."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root)

    # The following helpers mirror the methods used by ProgressiveWriteManager.
    def get_episode_plot_path(self, episode_number: int) -> Path:
        yaml_dir = self.project_root / "20_プロット" / "話別プロット"
        yaml_candidate = yaml_dir / f"第{episode_number:03d}話_プロット.yaml"
        if yaml_candidate.exists():
            return yaml_candidate
        md_dir = self.project_root / "20_プロット"
        md_candidate = md_dir / f"第{episode_number:03d}話_プロット.md"
        if md_candidate.exists():
            return md_candidate
        return md_candidate

    def get_plots_dir(self) -> Path:
        candidate = self.project_root / "plots"
        if candidate.exists():
            return candidate
        return self.project_root / "20_プロット"

    def get_episode_plots_dir(self) -> Path:
        return self.project_root / "20_プロット" / "話別プロット"

    def get_manuscript_path(self, episode_number: int) -> Path:
        md_dir = self.get_manuscript_dir()
        return md_dir / f"第{episode_number:03d}話_原稿.md"

    def get_manuscript_dir(self) -> Path:
        return get_default_manuscript_dir(self.project_root)


PathServiceFactory = Callable[[Path], Any]
ArtifactStoreFactory = Callable[..., Any]
ProgressDisplayFactory = Callable[[int, int], Any]
FeedbackSystemFactory = Callable[[int], Any]
LoggerFactory = Callable[[], ILogger]
IOLoggerFactory = Callable[[Path], Any]
ConfigurationManagerFactory = Callable[[], Any]
LLMExecutorFactory = Callable[[], ProgressiveWriteLLMExecutor | None]


@dataclass
class ProgressiveWriteRuntimeDeps:
    """Runtime dependency bundle for :class:`ProgressiveWriteManager`."""

    llm_executor: ProgressiveWriteLLMExecutor | None = None
    llm_executor_factory: LLMExecutorFactory | None = None
    path_service_factory: PathServiceFactory | None = None
    artifact_store_factory: ArtifactStoreFactory | None = None
    progress_display_factory: ProgressDisplayFactory | None = None
    feedback_system_factory: FeedbackSystemFactory | None = None
    logger_factory: LoggerFactory = field(default=lambda: NullLogger())
    performance_monitor: Callable[[str], Callable[..., Any]] = field(default=_noop_performance_monitor)
    async_optimizer: Any | None = None
    io_logger_factory: IOLoggerFactory | None = None
    configuration_manager_factory: ConfigurationManagerFactory | None = None

    def ensure_logger(self, override: ILogger | None = None) -> ILogger:
        if override is not None:
            return override
        if self.logger_factory is None:
            return NullLogger()
        return self.logger_factory()

    def ensure_llm_executor(self) -> ProgressiveWriteLLMExecutor | None:
        if self.llm_executor is not None:
            return self.llm_executor
        if self.llm_executor_factory is not None:
            self.llm_executor = self.llm_executor_factory()
            return self.llm_executor
        return None

    def create_path_service(self, project_root: Path) -> Any:
        if self.path_service_factory is None:
            return NullPathService(project_root)
        try:
            return self.path_service_factory(project_root)
        except Exception:
            return NullPathService(project_root)

    def create_artifact_store(self, storage_dir: Path, **options: Any) -> Any:
        if self.artifact_store_factory is None:
            return NullArtifactStore()
        return self.artifact_store_factory(storage_dir=storage_dir, **options)

    def create_progress_display(self, episode_number: int, *, total_steps: int) -> Any:
        if self.progress_display_factory is None:
            return NullProgressDisplay(episode_number, total_steps=total_steps)
        return self.progress_display_factory(episode_number, total_steps)

    def create_feedback_system(self, episode_number: int) -> Any:
        if self.feedback_system_factory is None:
            return NullFeedbackSystem(episode_number)
        return self.feedback_system_factory(episode_number)

    def create_io_logger(self, project_root: Path) -> Any:
        if self.io_logger_factory is None:
            return NullLLMIOLogger(project_root)
        return self.io_logger_factory(project_root)

    def get_configuration_manager(self) -> Any | None:
        if self.configuration_manager_factory is None:
            return None
        try:
            return self.configuration_manager_factory()
        except Exception:
            return None

    @classmethod
    def with_defaults(cls) -> "ProgressiveWriteRuntimeDeps":
        """Create dependency bundle using the existing production wiring."""

        llm_executor_factory: LLMExecutorFactory | None = None
        create_progressive_write_llm_executor = _load_optional_attr(
            "noveler.infrastructure.factories.progressive_write_llm_executor_factory",
            "create_progressive_write_llm_executor",
        )
        if callable(create_progressive_write_llm_executor):

            def build_llm_executor() -> ProgressiveWriteLLMExecutor | None:
                return create_progressive_write_llm_executor()

            llm_executor_factory = build_llm_executor

        path_service_factory: PathServiceFactory | None = None
        create_path_service = _load_optional_attr(
            "noveler.infrastructure.factories.path_service_factory",
            "create_path_service",
        )
        create_mcp_aware_path_service = _load_optional_attr(
            "noveler.infrastructure.factories.path_service_factory",
            "create_mcp_aware_path_service",
        )
        if callable(create_path_service):

            def build_path_service(project_root: Path) -> Any:
                service = None
                if callable(create_mcp_aware_path_service):
                    try:
                        service = create_mcp_aware_path_service()
                    except TypeError:  # pragma: no cover - signature guard
                        service = create_mcp_aware_path_service(project_root)
                    except Exception:
                        service = None
                if service is None:
                    service = create_path_service(project_root)
                return service

            path_service_factory = build_path_service

        artifact_store_factory: ArtifactStoreFactory | None = None
        create_artifact_store = _load_optional_attr(
            "noveler.domain.services.artifact_store_service",
            "create_artifact_store",
        )
        if callable(create_artifact_store):

            def build_artifact_store(*, storage_dir: Path, **options: Any) -> Any:
                return create_artifact_store(storage_dir=storage_dir, **options)

            artifact_store_factory = build_artifact_store

        progress_display_factory: ProgressDisplayFactory | None = None
        ProgressDisplaySystem = _load_optional_attr(
            "noveler.presentation.ui.progress_display",
            "ProgressDisplaySystem",
        )
        if callable(ProgressDisplaySystem):

            def build_progress_display(episode_number: int, total_steps: int) -> Any:
                try:
                    return ProgressDisplaySystem(episode_number, total_steps=total_steps)
                except Exception:
                    return NullProgressDisplay(episode_number, total_steps=total_steps)

            progress_display_factory = build_progress_display

        feedback_system_factory: FeedbackSystemFactory | None = None
        InteractiveFeedbackSystem = _load_optional_attr(
            "noveler.presentation.ui.feedback_system",
            "InteractiveFeedbackSystem",
        )
        if callable(InteractiveFeedbackSystem):

            def build_feedback_system(episode_number: int) -> Any:
                try:
                    return InteractiveFeedbackSystem(episode_number)
                except Exception:
                    return NullFeedbackSystem(episode_number)

            feedback_system_factory = build_feedback_system

        io_logger_factory: IOLoggerFactory | None = None
        LLMIOLogger = _load_optional_attr(
            "noveler.infrastructure.llm.llm_io_logger",
            "LLMIOLogger",
        )
        if callable(LLMIOLogger):

            def build_io_logger(project_root: Path) -> Any:
                try:
                    return LLMIOLogger(project_root)
                except Exception:
                    return NullLLMIOLogger(project_root)

            io_logger_factory = build_io_logger

        configuration_manager_factory: ConfigurationManagerFactory | None = None
        get_configuration_manager = _load_optional_attr(
            "noveler.infrastructure.factories.configuration_service_factory",
            "get_configuration_manager",
        )
        if callable(get_configuration_manager):
            configuration_manager_factory = get_configuration_manager

        performance_monitor = _noop_performance_monitor
        async_optimizer: Any | None = None
        try:
            perf_module = importlib.import_module(
                "noveler.infrastructure.performance.comprehensive_performance_optimizer"
            )
            performance_monitor = getattr(
                perf_module,
                "performance_monitor",
                performance_monitor,
            )
            optimizer = getattr(perf_module, "performance_optimizer", None)
            if optimizer is not None:
                async_optimizer = getattr(optimizer, "async_optimizer", async_optimizer)
                performance_monitor = getattr(
                    optimizer,
                    "performance_monitor",
                    performance_monitor,
                )
        except Exception:  # pragma: no cover - optional dependency
            performance_monitor = _noop_performance_monitor
            async_optimizer = None

        return cls(
            llm_executor_factory=llm_executor_factory,
            path_service_factory=path_service_factory,
            artifact_store_factory=artifact_store_factory,
            progress_display_factory=progress_display_factory,
            feedback_system_factory=feedback_system_factory,
            logger_factory=lambda: NullLogger(),
            performance_monitor=performance_monitor,
            async_optimizer=async_optimizer,
            io_logger_factory=io_logger_factory,
            configuration_manager_factory=configuration_manager_factory,
        )
