#!/usr/bin/env python3
"""Plot creation orchestrator use case.

Coordinates the application-layer workflow for creating plots and managing external integrations.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from noveler.domain.entities.plot_creation_task import PlotCreationTask
from noveler.domain.services.plot_creation_service import PlotCreationService
from noveler.domain.services.plot_merge_service import PlotMergeService
from noveler.domain.value_objects.domain_message import DomainMessage
from noveler.domain.value_objects.merge_strategy import MergeStrategy
from noveler.domain.value_objects.workflow_stage_type import WorkflowStageType

# Backwards compatibility: expose infrastructure classes for legacy patches/tests
try:
    from noveler.infrastructure.persistence.file_system_project_file_repository import (
        FileSystemProjectFileRepository,
    )
except Exception:  # pragma: no cover - test environments may not have full infrastructure
    FileSystemProjectFileRepository = None  # type: ignore

try:
    from noveler.infrastructure.persistence.yaml_template_repository import YamlTemplateRepository
except Exception:  # pragma: no cover
    YamlTemplateRepository = None  # type: ignore

# DDD準拠: Infrastructure層への直接依存を排除（遅延初期化で対応）
# from noveler.infrastructure.persistence.file_system_project_file_repository import FileSystemProjectFileRepository


@dataclass(frozen=True)
class PlotCreationRequest:
    """Request payload for orchestrating plot creation.

    Attributes:
        stage_type: Workflow stage indicating which plot to create.
        project_root: Root directory of the target project.
        parameters: Arbitrary parameters forwarded to the domain task.
        auto_confirm: Whether to skip confirmation prompts.
        merge_strategy: Strategy controlling how plots are merged.
    """

    stage_type: WorkflowStageType
    project_root: Path
    parameters: dict[str, Any]
    auto_confirm: bool = True
    merge_strategy: MergeStrategy = MergeStrategy.MERGE


@dataclass(frozen=True)
class PlotCreationResponse:
    """Response payload returned after plot creation.

    Attributes:
        success: Indicates whether the operation completed successfully.
        created_files: List of plot files generated during the workflow.
        error_message: Error text when the workflow fails.
        conflict_files: Files that require manual resolution.
    """

    success: bool
    created_files: list[Path]
    error_message: str = ""
    conflict_files: list[Path] = field(default_factory=list)
    messages: list[DomainMessage] = field(default_factory=list)


class PlotCreationOrchestrator:
    """Coordinate plot creation workflows using domain services."""

    def __init__(self, templates_dir: str | Path) -> None:
        """Initialise the orchestrator with a templates directory.

        Args:
            templates_dir: Directory containing plot templates used by the domain service.
        """
        self.templates_dir = Path(templates_dir)

    def execute_plot_creation(self, request: PlotCreationRequest) -> PlotCreationResponse:
        """Execute the plot creation workflow for the given request.

        Args:
            request: Plot creation request payload.

        Returns:
            PlotCreationResponse: Resulting response translated from the domain service.
        """
        try:
            # DDD準拠: Infrastructure層への直接依存を排除（遅延初期化で対応）
            # リポジトリの初期化（遅延初期化パターン）
            from noveler.infrastructure.persistence.file_system_project_file_repository import (
                FileSystemProjectFileRepository,
            )
            from noveler.infrastructure.persistence.yaml_template_repository import YamlTemplateRepository

            project_file_repo = FileSystemProjectFileRepository(request.project_root)
            template_repo = YamlTemplateRepository(self.templates_dir)

            # ドメインサービスの初期化
            plot_merge_service = PlotMergeService()
            plot_service = PlotCreationService(project_file_repo, template_repo, plot_merge_service)

            # ドメインタスクの作成
            task = PlotCreationTask(
                stage_type=request.stage_type,
                project_root=str(request.project_root),
                parameters=request.parameters,
                merge_strategy=request.merge_strategy,
            )

            # ドメインサービスで実行
            domain_result = plot_service.execute_plot_creation(task, request.auto_confirm)

            # レスポンスに変換
            return PlotCreationResponse(
                success=domain_result.success,
                created_files=domain_result.created_files,
                error_message=domain_result.error_message,
                conflict_files=domain_result.conflict_files,
                messages=getattr(domain_result, "messages", []),
            )

        except Exception as e:
            return PlotCreationResponse(
                success=False,
                created_files=[],
                error_message=f"アプリケーション層エラー: {e!s}",
                messages=[
                    DomainMessage(
                        level="error",
                        message="PlotCreationOrchestratorで予期しない例外が発生しました",
                        details={"error": str(e)},
                    )
                ],
            )

    def create_master_plot(self, project_root: Path, auto_confirm: bool) -> PlotCreationResponse:
        """Create the master plot (overall structure) for a project.

        Args:
            project_root: Root directory of the project.
            auto_confirm: Whether to bypass confirmation prompts.

        Returns:
            PlotCreationResponse: Response describing the master plot creation.
        """
        request = PlotCreationRequest(
            stage_type=WorkflowStageType.MASTER_PLOT,
            project_root=project_root,
            parameters={},
            auto_confirm=auto_confirm,
        )

        return self.execute_plot_creation(request)

    def create_chapter_plot(self, project_root: Path, chapter: int, auto_confirm: bool = False) -> PlotCreationResponse:
        """Create a chapter-level plot for the specified project.

        Args:
            project_root: Root directory of the project.
            chapter: Chapter number to generate.
            auto_confirm: Whether to bypass confirmation prompts.

        Returns:
            PlotCreationResponse: Response describing the chapter plot creation.
        """
        request = PlotCreationRequest(
            stage_type=WorkflowStageType.CHAPTER_PLOT,
            project_root=project_root,
            parameters={"chapter_number": chapter},  # chapter を chapter_number に変更
            auto_confirm=auto_confirm,
        )

        return self.execute_plot_creation(request)

    def create_episode_plot(
        self, project_root: Path, episode: int, chapter: int | None = None, auto_confirm: bool = False
    ) -> PlotCreationResponse:
        """Create an episode-level plot for the specified project.

        Args:
            project_root: Root directory of the project.
            episode: Episode number to generate.
            chapter: Optional chapter number for contextual linkage.
            auto_confirm: Whether to bypass confirmation prompts.

        Returns:
            PlotCreationResponse: Response describing the episode plot creation.
        """
        parameters = {"episode": episode}
        if chapter is not None:
            parameters["chapter"] = chapter

        request = PlotCreationRequest(
            stage_type=WorkflowStageType.EPISODE_PLOT,
            project_root=project_root,
            parameters=parameters,
            auto_confirm=auto_confirm,
        )

        return self.execute_plot_creation(request)
