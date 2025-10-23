#!/usr/bin/env python3

"""Application.use_cases.foreshadowing_design_use_case
Where: Application use case guiding foreshadowing design workflows.
What: Coordinates validation, impact analysis, and report generation for foreshadowing plans.
Why: Ensures foreshadowing decisions stay consistent and traceable across the project.
"""

from __future__ import annotations



from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable

from noveler.application.base.abstract_use_case import AbstractUseCase
from noveler.infrastructure.logging.unified_logger import get_logger

if TYPE_CHECKING:
    from noveler.domain.repositories.foreshadowing_repository import ForeshadowingRepository
    from noveler.domain.repositories.plot_repository import PlotRepository
    from noveler.domain.repositories.project_repository import ProjectRepository
    from noveler.domain.services.foreshadowing_extractor_service import ForeshadowingExtractorService

logger = get_logger(__name__)


class ForeshadowingDesignStatus(Enum):
    """Execution status values returned by the foreshadowing design workflow."""

    SUCCESS = "success"
    PROJECT_NOT_FOUND = "project_not_found"
    MASTER_PLOT_NOT_FOUND = "master_plot_not_found"
    CHAPTER_PLOT_NOT_FOUND = "chapter_plot_not_found"
    FORESHADOWING_FILE_NOT_FOUND = "foreshadowing_file_not_found"
    ERROR = "error"


@dataclass
class ForeshadowingDesignRequest:
    """Input parameters required to design foreshadowing.

    Attributes:
        project_name: Name of the project whose foreshadowing should be updated.
        source: Data source that drives extraction (master_plot, chapter_plot, manual).
        auto_extract: Whether automatic extraction should run before merging.
        interactive: Enables interactive prompts in legacy flows.
        merge_existing: Merge new foreshadowing with existing entries when True.
        detailed_mode: Enables chapter-level extraction for detailed foreshadowing.
        target_episodes: Specific episode numbers to include when supported.
        metadata: Arbitrary metadata forwarded to downstream services.
    """

    project_name: str
    source: str = "master_plot"  # master_plot / chapter_plot / manual
    auto_extract: bool = True
    interactive: bool = False
    merge_existing: bool = True
    detailed_mode: bool = False
    target_episodes: list[int] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ForeshadowingDesignResponse:
    """Result payload produced by the foreshadowing design workflow.

    Attributes:
        status: Final status enumeration.
        message: Human-readable outcome description.
        created_count: Number of new foreshadowing entries created.
        existing_count: Number of existing entries encountered.
        updated_count: Number of entries updated in place.
        foreshadowing_file: Path to the foreshadowing file when available.
        foreshadowing_summary: Summary string describing resulting foreshadowing.
        error_details: Optional raw error message for troubleshooting.
    """

    status: ForeshadowingDesignStatus
    message: str
    created_count: int = 0
    existing_count: int = 0
    updated_count: int = 0
    foreshadowing_file: Path | None = None
    foreshadowing_summary: str = ""
    error_details: str | None = None


class ForeshadowingDesignError(Exception):
    """Compatibility error that stores a status enumeration and message."""

    def __init__(self, status: ForeshadowingDesignStatus, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


class ForeshadowingDesignUseCase(AbstractUseCase[ForeshadowingDesignRequest, ForeshadowingDesignResponse]):
    """Coordinate repositories and services to maintain foreshadowing artifacts."""

    def __init__(
        self,
        project_repository: ProjectRepository,
        foreshadowing_repository: ForeshadowingRepository,
        plot_repository: PlotRepository,
        foreshadowing_extractor: ForeshadowingExtractorService,
        **kwargs: Any,
    ) -> None:
        """Initialise the use case with required repositories and services.

        Args:
            project_repository: Repository for resolving project metadata.
            foreshadowing_repository: Repository that persists foreshadowing entries.
            plot_repository: Repository used to read master and chapter plots.
            foreshadowing_extractor: Service that extracts foreshadowing from plots.
            **kwargs: Additional arguments forwarded to the base use case.
        """
        super().__init__(**kwargs)
        self.project_repository = project_repository
        self.foreshadowing_repository = foreshadowing_repository
        self.plot_repository = plot_repository
        self.foreshadowing_extractor = foreshadowing_extractor

    def execute(self, request: ForeshadowingDesignRequest) -> ForeshadowingDesignResponse:
        """Run the foreshadowing design workflow for the given project.

        Args:
            request: Parameters controlling extraction and merge behaviour.

        Returns:
            ForeshadowingDesignResponse: Result of the design operation.
        """
        logger.info("Starting foreshadowing design for project %s", request.project_name)

        if not self._project_exists(request.project_name):
            msg = f"プロジェクト '{request.project_name}' が見つかりません"
            return ForeshadowingDesignResponse(
                status=ForeshadowingDesignStatus.PROJECT_NOT_FOUND,
                message=msg,
            )

        try:
            from noveler.infrastructure.services.common_path_service import get_common_path_service

            path_service = get_common_path_service()
        except Exception:  # pragma: no cover - フォールバック
            from noveler.presentation.shared.shared_utilities import get_common_path_service as _get_common_path_service

            path_service = _get_common_path_service()

        project_root = self._resolve_project_root(request.project_name)
        foreshadowing_file = self._resolve_foreshadowing_file(project_root, path_service)

        try:
            if request.detailed_mode or request.source == "chapter_plot":
                return self._handle_detailed_mode(request, project_root, foreshadowing_file)

            if request.source == "manual":
                return self._handle_manual_mode(project_root, foreshadowing_file)

            return self._handle_master_mode(request, project_root, foreshadowing_file)

        except ForeshadowingDesignError as exc:
            logger.warning("Foreshadowing design warning: %s", exc)
            return ForeshadowingDesignResponse(
                status=exc.status,
                message=exc.message,
                foreshadowing_file=foreshadowing_file,
            )
        except Exception as exc:
            logger.exception("Foreshadowing design failed for project %s: %s", request.project_name, exc)
            return ForeshadowingDesignResponse(
                status=ForeshadowingDesignStatus.ERROR,
                message=f"伏線設計中にエラーが発生しました: {exc}",
                foreshadowing_file=foreshadowing_file,
                error_details=str(exc),
            )

    # ------------------------------------------------------------------
    # プライベートヘルパー
    # ------------------------------------------------------------------

    def _project_exists(self, project_name: str) -> bool:
        """Return whether the target project exists.

        Args:
            project_name: Name of the project to look up.

        Returns:
            bool: True when the project repository can resolve the project.
        """
        try:
            return bool(self.project_repository.exists(project_name))
        except TypeError:
            return bool(self.project_repository.exists())  # type: ignore[call-arg]

    def _resolve_project_root(self, project_name: str) -> Path:
        """Resolve the root directory for the given project.

        Args:
            project_name: Name of the project whose root should be resolved.

        Returns:
            Path: Detected project root or the current working directory as fallback.
        """
        if hasattr(self.project_repository, "get_project_root"):
            root = self.project_repository.get_project_root(project_name)
            if root:
                return Path(root)

        path_service = self.get_path_service()
        if path_service and hasattr(path_service, "get_project_root_by_name"):
            resolved = path_service.get_project_root_by_name(project_name)
            if resolved:
                return Path(resolved)

        return Path.cwd()

    def _resolve_foreshadowing_file(self, project_root: Path, path_service: Any) -> Path:
        """Calculate the foreshadowing file path using repositories and path services.

        Args:
            project_root: Root directory of the project.
            path_service: Shared path service used as a fallback.

        Returns:
            Path: Path to the foreshadowing YAML file.
        """
        try:
            file_path = self.foreshadowing_repository.get_foreshadowing_file_path(project_root)
            if isinstance(file_path, Path):
                return file_path
            if file_path:
                try:
                    return Path(file_path)
                except TypeError:
                    pass
        except TypeError:
            try:
                file_path = self.foreshadowing_repository.get_foreshadowing_file_path()
                if isinstance(file_path, Path):
                    return file_path
                if file_path:
                    try:
                        return Path(file_path)
                    except TypeError:
                        pass
            except AttributeError:
                pass
        except AttributeError:
            pass

        management_dir = path_service.get_management_dir() if hasattr(path_service, "get_management_dir") else "50_管理資料"
        return project_root / str(management_dir) / "伏線管理.yaml"

    # ---- モード別処理 ----

    def _handle_master_mode(
        self,
        request: ForeshadowingDesignRequest,
        project_root: Path,
        foreshadowing_file: Path,
    ) -> ForeshadowingDesignResponse:
        """Design foreshadowing using the master plot as the primary source.

        Args:
            request: Original request describing merge behaviour.
            project_root: Root directory of the project.
            foreshadowing_file: Destination file for foreshadowing entries.

        Returns:
            ForeshadowingDesignResponse: Response describing the outcome.
        """
        master_plot_data = self._load_master_plot(project_root)
        extracted = self.foreshadowing_extractor.extract_from_master_plot(master_plot_data)
        extracted = list(extracted or [])

        existing_items = self._load_existing(project_root) if request.merge_existing else []
        combined = self._merge_foreshadowings(existing_items, extracted, request.merge_existing)
        self._save_foreshadowings(combined, project_root)

        created_count = len(extracted)
        existing_count = len(existing_items)
        message = self._build_success_message(
            created_count,
            existing_count,
            detailed=False,
        )

        return ForeshadowingDesignResponse(
            status=ForeshadowingDesignStatus.SUCCESS,
            message=message,
            created_count=created_count,
            existing_count=existing_count,
            updated_count=existing_count,
            foreshadowing_file=foreshadowing_file,
            foreshadowing_summary=self._create_summary(combined),
        )

    def _handle_detailed_mode(
        self,
        request: ForeshadowingDesignRequest,
        project_root: Path,
        foreshadowing_file: Path,
    ) -> ForeshadowingDesignResponse:
        """Design foreshadowing at the chapter level for detailed mode.

        Args:
            request: Original request describing merge behaviour.
            project_root: Root directory of the project.
            foreshadowing_file: Destination file for foreshadowing entries.

        Returns:
            ForeshadowingDesignResponse: Response describing the outcome.

        Raises:
            ForeshadowingDesignError: When required files are missing.
        """
        if not self._foreshadowing_file_exists(project_root):
            raise ForeshadowingDesignError(
                ForeshadowingDesignStatus.FORESHADOWING_FILE_NOT_FOUND,
                "主要伏線がまだ生成されていません。先に 'novel foreshadowing design --source master_plot' を実行してください。",
            )

        chapter_files = self._get_chapter_plot_files(project_root)
        if not chapter_files:
            raise ForeshadowingDesignError(
                ForeshadowingDesignStatus.CHAPTER_PLOT_NOT_FOUND,
                "章別プロットが見つかりません。先に 'novel plot chapter' を実行してください。",
            )

        extracted = self.foreshadowing_extractor.extract_detailed_foreshadowing_from_chapter(project_root, chapter_files)
        extracted = list(extracted or [])

        existing_items = self._load_existing(project_root)
        if not request.merge_existing:
            existing_items = []

        combined = self._merge_foreshadowings(existing_items, extracted, merge_existing=True if request.merge_existing or existing_items else False)
        self._save_foreshadowings(combined, project_root)

        created_count = len(extracted)
        existing_count = len(existing_items)
        message = self._build_success_message(
            created_count,
            existing_count,
            detailed=True,
        )

        return ForeshadowingDesignResponse(
            status=ForeshadowingDesignStatus.SUCCESS,
            message=message,
            created_count=created_count,
            existing_count=existing_count,
            updated_count=existing_count,
            foreshadowing_file=foreshadowing_file,
            foreshadowing_summary=self._create_summary(combined),
        )

    def _handle_manual_mode(self, project_root: Path, foreshadowing_file: Path) -> ForeshadowingDesignResponse:
        """Create a manual foreshadowing template without automatic extraction.

        Args:
            project_root: Root directory of the project.
            foreshadowing_file: Destination file for the template.

        Returns:
            ForeshadowingDesignResponse: Response describing the manual template creation.
        """
        message = "手動伏線テンプレートを作成しました。伏線管理.yaml を編集してください。"
        return ForeshadowingDesignResponse(
            status=ForeshadowingDesignStatus.SUCCESS,
            message=message,
            created_count=0,
            existing_count=0,
            foreshadowing_file=foreshadowing_file,
            foreshadowing_summary="",
        )

    # ---- データアクセス補助 ----

    def _load_master_plot(self, project_root: Path) -> Any:
        """Load the master plot data and raise when it is missing.

        Args:
            project_root: Root directory of the project.

        Returns:
            Any: Master plot structure consumed by the extractor.

        Raises:
            ForeshadowingDesignError: If the master plot cannot be found.
        """
        try:
            if hasattr(self.plot_repository, "master_plot_exists") and not self.plot_repository.master_plot_exists(project_root):
                raise ForeshadowingDesignError(
                    ForeshadowingDesignStatus.MASTER_PLOT_NOT_FOUND,
                    "全体構成.yamlが見つかりません。先に 'novel plot master' を実行してください。",
                )
            return self.plot_repository.load_master_plot(project_root)
        except FileNotFoundError as exc:
            raise ForeshadowingDesignError(
                ForeshadowingDesignStatus.MASTER_PLOT_NOT_FOUND,
                "全体構成.yamlが見つかりません。先に 'novel plot master' を実行してください。",
            ) from exc

    def _foreshadowing_file_exists(self, project_root: Path) -> bool:
        """Return whether the foreshadowing file already exists at the project root.

        Args:
            project_root: Root directory of the project.

        Returns:
            bool: True when the repository reports an existing foreshadowing file.
        """
        try:
            return bool(self.foreshadowing_repository.exists(project_root))
        except TypeError:
            try:
                return bool(self.foreshadowing_repository.exists())  # type: ignore[call-arg]
            except Exception:
                return False

    def _load_existing(self, project_root: Path) -> list[Any]:
        """Load existing foreshadowing entries from the repository.

        Args:
            project_root: Root directory of the project.

        Returns:
            list[Any]: Existing foreshadowing entries, empty when missing.
        """
        if not self._foreshadowing_file_exists(project_root):
            return []

        try:
            items = self.foreshadowing_repository.load_all(project_root)
        except TypeError:
            items = self.foreshadowing_repository.load_all()  # type: ignore[call-arg]
        except Exception:
            return []
        return list(items or [])

    def _get_chapter_plot_files(self, project_root: Path) -> list[Path]:
        """Return chapter plot files used for detailed extraction.

        Args:
            project_root: Root directory of the project.

        Returns:
            list[Path]: Chapter plot file paths.
        """
        try:
            files = self.plot_repository.get_chapter_plot_files(project_root)
            return [Path(f) for f in files or []]
        except AttributeError:
            return []

    def _save_foreshadowings(self, foreshadowings: Iterable[Any], project_root: Path) -> None:
        """Persist foreshadowing entries via the repository.

        Args:
            foreshadowings: Iterable of foreshadowing structures to save.
            project_root: Root directory used for repository context.
        """
        try:
            self.foreshadowing_repository.save_all(list(foreshadowings), project_root=project_root)  # type: ignore[call-arg]
        except TypeError:
            self.foreshadowing_repository.save_all(list(foreshadowings))

    # ---- マージ・サマリー ----

    def _merge_foreshadowings(
        self,
        existing: list[Any],
        new: list[Any],
        merge_existing: bool,
    ) -> list[Any]:
        """Merge newly extracted foreshadowings with existing entries.

        Args:
            existing: Existing foreshadowing entries.
            new: Newly extracted foreshadowing entries.
            merge_existing: Whether existing entries should be preserved.

        Returns:
            list[Any]: Combined foreshadowing list with unique identifiers.
        """
        merged = list(existing) if merge_existing else []
        existing_ids = {self._extract_id(item) for item in merged}
        existing_ids.discard(None)

        next_number = self._next_id_number(existing_ids)

        for item in new:
            item_id = self._extract_id(item)
            if not item_id or item_id in existing_ids:
                item_id = self._format_id(next_number)
                next_number += 1
                self._assign_id(item, item_id)
            existing_ids.add(item_id)
            merged.append(item)

        return merged

    def _extract_id(self, item: Any) -> str | None:
        """Extract a foreshadowing identifier from heterogeneous structures.

        Args:
            item: Foreshadowing entry that may expose an id attribute or key.

        Returns:
            str | None: Identifier when present.
        """
        if hasattr(item, "id"):
            identifier = getattr(item.id, "value", getattr(item.id, "id", item.id))
            if isinstance(identifier, str):
                return identifier
        if isinstance(item, dict):
            identifier = item.get("id")
            if isinstance(identifier, dict):
                identifier = identifier.get("value") or identifier.get("id")
            if isinstance(identifier, str):
                return identifier
        return None

    def _assign_id(self, item: Any, identifier: str) -> None:
        """Assign an identifier to a foreshadowing entry.

        Args:
            item: Foreshadowing entry to update.
            identifier: Identifier string to assign.
        """
        if hasattr(item, "id") and hasattr(item.id, "value"):
            try:
                item.id.value = identifier
                return
            except Exception:
                pass
        if isinstance(item, dict):
            item["id"] = identifier
            return
        if hasattr(item, "id"):
            try:
                item.id = identifier
            except Exception:
                pass

    def _next_id_number(self, identifiers: set[str]) -> int:
        """Return the next numeric suffix for foreshadowing identifiers.

        Args:
            identifiers: Existing identifier strings.

        Returns:
            int: Next available numeric suffix.
        """
        max_number = 0
        for identifier in identifiers:
            if identifier and identifier.startswith("F"):
                try:
                    number = int(identifier[1:])
                    max_number = max(max_number, number)
                except ValueError:
                    continue
        return max_number + 1

    def _format_id(self, number: int) -> str:
        """Format a foreshadowing identifier from a numeric suffix.

        Args:
            number: Numeric component of the identifier.

        Returns:
            str: Formatted identifier string.
        """
        return f"F{number:03d}"

    def _create_summary(self, foreshadowings: Iterable[Any]) -> str:
        """Build a human-readable summary for the resulting foreshadowing list.

        Args:
            foreshadowings: Foreshadowing entries to summarise.

        Returns:
            str: Summary text suitable for logs and responses.
        """
        items = list(foreshadowings)
        if not items:
            return "伏線なし"

        summary_parts: list[str] = []
        for item in items:
            if hasattr(item, "to_summary"):
                try:
                    summary_parts.append(str(item.to_summary()))
                    continue
                except Exception:
                    pass

            identifier = self._extract_id(item) or "不明"
            title = getattr(item, "title", None)
            if not title and isinstance(item, dict):
                title = item.get("title") or item.get("name")
            if not title:
                title = "タイトルなし"
            summary_parts.append(f"{identifier}: {title}")

        return "\n".join(summary_parts)

    def _build_success_message(self, created: int, existing: int, *, detailed: bool) -> str:
        """Create a success message describing newly generated foreshadowing.

        Args:
            created: Number of newly created entries.
            existing: Number of existing entries encountered.
            detailed: Whether detailed mode was used.

        Returns:
            str: Formatted success message.
        """
        base = "細かな伏線を追加しました" if detailed else "主要伏線を設計しました"
        if existing:
            base += f"（既存: {existing}件, 新規: {created}件）"
        else:
            base += f"（新規: {created}件）"
        return base
