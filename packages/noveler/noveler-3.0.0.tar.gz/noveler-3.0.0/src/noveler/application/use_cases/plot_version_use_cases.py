#!/usr/bin/env python3

"""Application.use_cases.plot_version_use_cases
Where: Application use case module managing plot version operations.
What: Provides utilities to create, compare, and manage plot versions and history.
Why: Enables teams to track plot evolution without custom orchestration per caller.
"""

from __future__ import annotations



from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from noveler.application.base.abstract_use_case import AbstractUseCase
from noveler.infrastructure.logging.unified_logger import get_logger

if TYPE_CHECKING:
    from noveler.domain.repositories.episode_repository import EpisodeRepository
    from noveler.domain.repositories.plot_repository import PlotRepository
    from noveler.domain.repositories.quality_repository import QualityRepository

from noveler.domain.entities.plot_version_entities import (
    ManuscriptPlotLink,
    PlotChangeSet,
    PlotVersion,
)
from noveler.domain.value_objects.project_time import ProjectTimezone

logger = get_logger(__name__)
JST = ProjectTimezone.jst().timezone

try:
    from noveler.infrastructure.adapters.git_service import GitService  # type: ignore
except Exception:  # pragma: no cover - GitService はテスト環境では存在しない場合がある
    GitService = None  # type: ignore


class ManuscriptStatus(Enum):
    """Represents the current manuscript state."""

    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REVIEWED = "reviewed"
    PUBLISHED = "published"
    ARCHIVED = "archived"


@dataclass
class CheckManuscriptStatusRequest:
    """Input payload for checking manuscript status.

    Attributes:
        project_id: Identifier of the project containing the episode.
        episode_number: Episode number whose status should be checked.
        check_plot_version: Whether to include plot version consistency.
        detailed_analysis: Toggle to compute additional diagnostics.
        metadata: Arbitrary caller-supplied information.
    """

    project_id: str
    episode_number: int
    check_plot_version: bool = True
    detailed_analysis: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CheckManuscriptStatusResponse:
    """Result payload produced by the manuscript status check.

    Attributes:
        success: Indicates whether the check completed successfully.
        manuscript_status: Detected manuscript status enumeration.
        plot_version: Plot version associated with the episode.
        last_modified: ISO formatted timestamp of the latest change.
        word_count: Word count reported for the manuscript.
        quality_score: Optional quality score when available.
        issues: List of issues discovered during analysis.
        recommendations: Suggested follow-up actions.
        error_details: Raw error message when the check fails.
    """

    success: bool
    manuscript_status: ManuscriptStatus | None = None
    plot_version: str | None = None
    last_modified: str | None = None
    word_count: int = 0
    quality_score: float | None = None
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    error_details: str | None = None


class CheckManuscriptStatusUseCase(AbstractUseCase[CheckManuscriptStatusRequest, CheckManuscriptStatusResponse]):
    """Check manuscript status and ensure consistency with plot versions."""

    def __init__(
        self,
        episode_repository: EpisodeRepository,
        plot_repository: PlotRepository,
        quality_repository: QualityRepository | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialise the use case with required repositories.

        Args:
            episode_repository: Repository used to load episode data.
            plot_repository: Repository that provides plot information.
            quality_repository: Optional repository for quality metrics.
            **kwargs: Additional arguments forwarded to the base class.
        """
        super().__init__(**kwargs)
        self.episode_repository = episode_repository
        self.plot_repository = plot_repository
        self.quality_repository = quality_repository

        logger.debug("CheckManuscriptStatusUseCase initialized")

    async def execute(self, request: CheckManuscriptStatusRequest) -> CheckManuscriptStatusResponse:
        """Run the manuscript status check workflow.

        Args:
            request: Manuscript status check request payload.

        Returns:
            CheckManuscriptStatusResponse: Result of the status evaluation.
        """
        try:
            logger.info(f"Checking manuscript status for episode {request.episode_number}")

            # エピソード情報取得
            episode = await self.episode_repository.find_by_number(request.project_id, request.episode_number)

            if not episode:
                return CheckManuscriptStatusResponse(
                    success=False, error_details=f"Episode {request.episode_number} not found"
                )

            # 原稿状態判定
            manuscript_status = await self._determine_manuscript_status(episode)

            # プロットバージョン情報取得
            plot_version = None
            if request.check_plot_version:
                plot_data = await self.plot_repository.find_by_episode_number(
                    request.project_id, request.episode_number
                )
                if plot_data:
                    plot_version = getattr(plot_data, "version", "unknown")

            # 詳細分析
            issues = []
            recommendations = []
            quality_score = None

            if request.detailed_analysis:
                analysis_result = await self._perform_detailed_analysis(episode, request)
                issues = analysis_result.get("issues", [])
                recommendations = analysis_result.get("recommendations", [])
                quality_score = analysis_result.get("quality_score")

            # 基本情報取得
            word_count = await self._get_word_count(episode)
            last_modified = await self._get_last_modified(episode)

            logger.info(f"Manuscript status check completed for episode {request.episode_number}")

            return CheckManuscriptStatusResponse(
                success=True,
                manuscript_status=manuscript_status,
                plot_version=plot_version,
                last_modified=last_modified,
                word_count=word_count,
                quality_score=quality_score,
                issues=issues,
                recommendations=recommendations,
            )

        except Exception as e:
            logger.exception(f"Manuscript status check failed: {e}")
            return CheckManuscriptStatusResponse(success=False, error_details=str(e))


@dataclass
class CreatePlotVersionResponse:
    """Response payload produced when creating a plot version.

    Attributes:
        success: Indicates whether the version creation succeeded.
        version: Newly created plot version entity.
        error_message: Error detail when creation fails.
    """

    success: bool
    version: PlotVersion | None = None
    error_message: str = ""


class CreatePlotVersionUseCase:
    """Create new plot versions and optionally interact with Git."""

    def __init__(self, plot_version_repository, *, git_service_cls: Any | None = None) -> None:
        """Initialise the plot version use case with repositories and git service.

        Args:
            plot_version_repository: Repository that persists plot versions.
            git_service_cls: Optional git service class for tagging and diffs.
        """
        self._repository = plot_version_repository
        self._git_service_cls = git_service_cls or GitService

    def execute(
        self,
        version_number: str,
        author: str,
        major_changes: list[str],
        affected_chapters: list[int],
    ) -> CreatePlotVersionResponse:
        """Create a new plot version and optionally tag git history.

        Args:
            version_number: Version identifier to assign.
            author: Author credited for the version.
            major_changes: Summary of major modifications.
            affected_chapters: List of chapters impacted by the changes.

        Returns:
            CreatePlotVersionResponse: Response describing the outcome.
        """
        try:
            logger.info("Creating plot version %s", version_number)
            previous_version = None
            if hasattr(self._repository, "get_current"):
                previous_version = self._repository.get_current()

            new_version = PlotVersion(
                version_number=version_number,
                created_at=datetime.now(JST),
                author=author,
                major_changes=major_changes,
                affected_chapters=affected_chapters,
                previous_version=previous_version,
            )

            if self._git_service_cls is not None:
                try:
                    git_service = self._git_service_cls()
                    # タグの作成
                    git_service.create_tag(new_version.version_number)
                    if previous_version is not None:
                        diff_range = git_service.get_commit_range(
                            previous_version.version_number, new_version.version_number
                        )
                        new_version.git_commit_range = diff_range
                except Exception as git_error:  # pragma: no cover - ログのみ
                    logger.warning("Git integration failed: %s", git_error)

            if hasattr(self._repository, "save"):
                self._repository.save(new_version)

            return CreatePlotVersionResponse(success=True, version=new_version)

        except Exception as exc:  # pragma: no cover - 安全策
            logger.exception("CreatePlotVersionUseCase failed: %s", exc)
            return CreatePlotVersionResponse(success=False, error_message=str(exc))


@dataclass
class LinkManuscriptResponse:
    """Response payload for manuscript linking workflow.

    Attributes:
        success: Indicates whether linking completed successfully.
        link: Link entity describing the association.
        error_message: Error detail when linking fails.
    """

    success: bool
    link: ManuscriptPlotLink | None = None
    error_message: str = ""


class LinkManuscriptUseCase:
    """Link manuscripts with specific plot versions."""

    def __init__(self, plot_repository, link_repository, *, git_service_cls: Any | None = None) -> None:
        """Initialise the linking use case with repositories and optional git service.

        Args:
            plot_repository: Repository that exposes plot versions.
            link_repository: Repository used to persist manuscript links.
            git_service_cls: Optional git service for commit metadata.
        """
        self._plot_repository = plot_repository
        self._link_repository = link_repository
        self._git_service_cls = git_service_cls or GitService

    def execute(
        self,
        episode_number: str,
        plot_version_number: str | None = None,
    ) -> LinkManuscriptResponse:
        """Link a manuscript to a plot version.

        Args:
            episode_number: Episode identifier to link.
            plot_version_number: Optional explicit plot version.

        Returns:
            LinkManuscriptResponse: Response describing the link outcome.
        """
        try:
            if plot_version_number:
                plot_version = self._plot_repository.find_by_version(plot_version_number)
            else:
                plot_version = self._plot_repository.get_current()

            if not plot_version:
                msg = "Plot version not found"
                return LinkManuscriptResponse(success=False, error_message=msg)

            git_commit = "unknown"
            if self._git_service_cls is not None:
                try:
                    git_service = self._git_service_cls()
                    git_commit = git_service.get_current_commit()
                except Exception as git_error:  # pragma: no cover
                    logger.warning("Git commit retrieval failed: %s", git_error)

            link = ManuscriptPlotLink(
                episode_number=episode_number,
                plot_version=plot_version,
                implementation_date=datetime.now(JST),
                git_commit=git_commit,
            )

            if hasattr(self._link_repository, "save"):
                self._link_repository.save(link)

            return LinkManuscriptResponse(success=True, link=link)

        except Exception as exc:  # pragma: no cover
            logger.exception("LinkManuscriptUseCase failed: %s", exc)
            return LinkManuscriptResponse(success=False, error_message=str(exc))


@dataclass
class CompareVersionsResponse:
    """Response payload for plot version comparisons.

    Attributes:
        success: Indicates whether the comparison executed successfully.
        changeset: Summary of changes between versions.
        changed_files: Files reported as changed.
        diff_stats: Optional diff metadata.
        error_message: Error detail when comparison fails.
    """

    success: bool
    changeset: PlotChangeSet | None = None
    changed_files: list[str] = field(default_factory=list)
    diff_stats: dict[str, Any] | None = None
    error_message: str = ""


class CompareVersionsUseCase:
    """Compare two plot versions and gather diff information."""

    def __init__(self, plot_repository, *, git_service_cls: Any | None = None) -> None:
        """Initialise the comparison use case with repositories and git service.

        Args:
            plot_repository: Repository that provides plot versions.
            git_service_cls: Optional git service for diff operations.
        """
        self._plot_repository = plot_repository
        self._git_service_cls = git_service_cls or GitService

    def execute(self, from_version: str, to_version: str) -> CompareVersionsResponse:
        """Compare two plot versions and collect diff information.

        Args:
            from_version: Base version identifier.
            to_version: Target version identifier.

        Returns:
            CompareVersionsResponse: Response describing the comparison result.
        """
        try:
            base_version = self._plot_repository.find_by_version(from_version)
            target_version = self._plot_repository.find_by_version(to_version)

            if not base_version or not target_version:
                msg = "Specified plot versions not found"
                return CompareVersionsResponse(success=False, error_message=msg)

            diff_info: dict[str, Any] = {}
            changed_files: list[str] = []

            if self._git_service_cls is not None:
                try:
                    git_service = self._git_service_cls()
                    diff_info = git_service.get_diff(from_version, to_version) or {}
                    changed_files = list(diff_info.get("files", []))
                except Exception as git_error:  # pragma: no cover
                    logger.warning("Git diff retrieval failed: %s", git_error)

            changeset = PlotChangeSet(
                from_version=base_version,
                to_version=target_version,
                git_diff_files=changed_files,
            )

            return CompareVersionsResponse(
                success=True,
                changeset=changeset,
                changed_files=changed_files,
                diff_stats=diff_info or None,
            )

        except Exception as exc:  # pragma: no cover
            logger.exception("CompareVersionsUseCase failed: %s", exc)
            return CompareVersionsResponse(success=False, error_message=str(exc))


# 旧テスト互換: グローバル名前空間に公開
try:  # pragma: no cover - 既に存在する場合は上書きしない
    import builtins as _builtins

    for _legacy_name in (
        "CreatePlotVersionUseCase",
        "LinkManuscriptUseCase",
        "CompareVersionsUseCase",
    ):
        if not hasattr(_builtins, _legacy_name):
            setattr(_builtins, _legacy_name, globals()[_legacy_name])
except Exception:
    pass

__all__ = [
    "CheckManuscriptStatusRequest",
    "CheckManuscriptStatusResponse",
    "CheckManuscriptStatusUseCase",
    "CreatePlotVersionResponse",
    "CreatePlotVersionUseCase",
    "LinkManuscriptResponse",
    "LinkManuscriptUseCase",
    "CompareVersionsResponse",
    "CompareVersionsUseCase",
]
