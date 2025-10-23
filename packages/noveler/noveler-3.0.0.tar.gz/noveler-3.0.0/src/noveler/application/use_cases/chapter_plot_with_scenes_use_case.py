"""章別プロット作成 + 細かな伏線・シーン抽出ユースケース (互換レイヤー)"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from noveler.application.use_cases.foreshadowing_design_use_case import (
    ForeshadowingDesignRequest,
    ForeshadowingDesignStatus,
    ForeshadowingDesignUseCase,
)
from noveler.application.use_cases.plot_creation_orchestrator import PlotCreationRequest
from noveler.application.use_cases.scene_extraction_use_case import (
    SceneExtractionRequest,
    SceneExtractionStatus,
    SceneExtractionUseCase,
)
from noveler.domain.value_objects.workflow_stage_type import WorkflowStageType
from noveler.presentation.shared.shared_utilities import get_common_path_service

if TYPE_CHECKING:
    from noveler.application.use_cases.plot_creation_orchestrator import PlotCreationOrchestrator
    from noveler.domain.repositories.foreshadowing_repository import ForeshadowingRepository
    from noveler.domain.repositories.plot_repository import PlotRepository
    from noveler.domain.repositories.project_repository import ProjectRepository
    from noveler.domain.repositories.scene_repository import SceneRepository
    from noveler.domain.services.foreshadowing_extractor import ForeshadowingExtractor
    from noveler.domain.services.scene_extractor import SceneExtractor


@dataclass
class ChapterPlotDependencies:
    project_repository: "ProjectRepository"
    plot_repository: "PlotRepository"
    foreshadowing_repository: "ForeshadowingRepository"
    scene_repository: "SceneRepository"
    plot_orchestrator: "PlotCreationOrchestrator"
    scene_extractor: "SceneExtractor"
    foreshadowing_extractor: "ForeshadowingExtractor"


class ChapterPlotWithScenesStatus(Enum):
    SUCCESS = "success"
    PLOT_CREATION_FAILED = "plot_creation_failed"
    FORESHADOWING_EXTRACTION_FAILED = "foreshadowing_extraction_failed"
    SCENE_EXTRACTION_FAILED = "scene_extraction_failed"
    PARTIAL_SUCCESS = "partial_success"
    ERROR = "error"


@dataclass
class ChapterPlotWithScenesRequest:
    project_name: str
    chapter: int
    auto_foreshadowing: bool = True
    auto_scenes: bool = True
    merge_existing: bool = True


@dataclass
class ChapterPlotWithScenesResponse:
    status: ChapterPlotWithScenesStatus
    message: str
    plot_created: bool = False
    foreshadowing_extracted: bool = False
    scenes_extracted: bool = False
    plot_file: Path | None = None
    foreshadowing_file: Path | None = None
    scene_file: Path | None = None
    extracted_foreshadowing_count: int = 0
    extracted_scene_count: int = 0


class ChapterPlotWithScenesUseCase:
    """章別プロット作成と重要シーン抽出の統合ユースケース (旧API互換)"""

    def __init__(self, dependencies: ChapterPlotDependencies) -> None:
        self._deps = dependencies

    def execute(self, request: ChapterPlotWithScenesRequest) -> ChapterPlotWithScenesResponse:
        try:
            if not self._deps.project_repository.exists(request.project_name):
                return ChapterPlotWithScenesResponse(
                    status=ChapterPlotWithScenesStatus.ERROR,
                    message=f"プロジェクト '{request.project_name}' が見つかりません",
                )

            project_root = self._deps.project_repository.get_project_root(request.project_name)
            path_service = get_common_path_service(project_root)

            plot_response = self._create_chapter_plot(request, project_root)
            if not plot_response.success:
                msg = plot_response.error_message or "章別プロット作成に失敗しました"
                return ChapterPlotWithScenesResponse(
                    status=ChapterPlotWithScenesStatus.PLOT_CREATION_FAILED,
                    message=f"章別プロット作成に失敗しました: {msg}",
                )

            plot_file = self._resolve_plot_file(plot_response, path_service, request.chapter)

            fo_result = self._handle_foreshadowing(request, project_root)
            if isinstance(fo_result, ChapterPlotWithScenesResponse):
                fo_result.plot_created = True
                fo_result.plot_file = plot_file
                return fo_result

            scene_result = self._handle_scene_extraction(request, project_root)
            if isinstance(scene_result, ChapterPlotWithScenesResponse):
                scene_result.plot_created = True
                scene_result.plot_file = plot_file
                scene_result.foreshadowing_extracted = fo_result["extracted"]
                scene_result.foreshadowing_file = fo_result["file"]
                scene_result.extracted_foreshadowing_count = fo_result["count"]
                return scene_result

            message = (
                f"chapter{request.chapter:02d}のプロットを作成しました。"
                f"{fo_result['count']}個の細かな伏線を追加しました。"
                f"{scene_result['count']}個の細かなシーンを追加しました。"
            )

            return ChapterPlotWithScenesResponse(
                status=ChapterPlotWithScenesStatus.SUCCESS,
                message=message,
                plot_created=True,
                foreshadowing_extracted=fo_result["extracted"],
                scenes_extracted=scene_result["extracted"],
                plot_file=plot_file,
                foreshadowing_file=fo_result["file"],
                scene_file=scene_result["file"],
                extracted_foreshadowing_count=fo_result["count"],
                extracted_scene_count=scene_result["count"],
            )

        except Exception as exc:
            return ChapterPlotWithScenesResponse(
                status=ChapterPlotWithScenesStatus.ERROR,
                message=f"予期しないエラーが発生しました: {exc}",
            )

    # ------------------------------------------------------------------
    # プロット作成
    # ------------------------------------------------------------------
    def _create_chapter_plot(self, request: ChapterPlotWithScenesRequest, project_root: Path):
        plot_request = PlotCreationRequest(
            stage_type=WorkflowStageType.CHAPTER_PLOT,
            project_root=project_root,
            parameters={"chapter": request.chapter},
            auto_confirm=True,
        )
        return self._deps.plot_orchestrator.execute_plot_creation(plot_request)

    def _resolve_plot_file(self, plot_response, path_service, chapter: int) -> Path | None:
        if getattr(plot_response, "created_files", None):
            first = plot_response.created_files[0]
            try:
                return Path(first)
            except TypeError:
                pass
        plots_dir = path_service.get_plots_dir() if hasattr(path_service, "get_plots_dir") else Path("plots")
        primary = Path(plots_dir) / f"ch{chapter:02d}.yaml"
        if primary.exists():
            return primary
        legacy = Path(plots_dir) / f"第{chapter}章.yaml"
        return legacy if legacy.exists() else primary

    # ------------------------------------------------------------------
    # 伏線処理
    # ------------------------------------------------------------------
    def _handle_foreshadowing(self, request: ChapterPlotWithScenesRequest, project_root: Path):
        if not request.auto_foreshadowing:
            return {"extracted": False, "count": 0, "file": None}

        fo_use_case = ForeshadowingDesignUseCase(
            project_repository=self._deps.project_repository,
            foreshadowing_repository=self._deps.foreshadowing_repository,
            plot_repository=self._deps.plot_repository,
            foreshadowing_extractor=self._deps.foreshadowing_extractor,
        )

        fo_request = ForeshadowingDesignRequest(
            project_name=request.project_name,
            source="chapter_plot",
            auto_extract=True,
            merge_existing=request.merge_existing,
            detailed_mode=True,
        )

        fo_response = fo_use_case.execute(fo_request)
        if fo_response.status != ForeshadowingDesignStatus.SUCCESS:
            message = (
                "章別プロットは作成されましたが、細かな伏線抽出に失敗しました"
                if not getattr(fo_response, "message", None)
                else f"章別プロットは作成されましたが、細かな伏線抽出に失敗しました: {fo_response.message}"
            )
            return ChapterPlotWithScenesResponse(
                status=ChapterPlotWithScenesStatus.PARTIAL_SUCCESS,
                message=message,
                foreshadowing_file=fo_response.foreshadowing_file,
                extracted_foreshadowing_count=fo_response.created_count,
            )

        return {
            "extracted": True,
            "count": fo_response.created_count,
            "file": fo_response.foreshadowing_file,
        }

    # ------------------------------------------------------------------
    # シーン処理
    # ------------------------------------------------------------------
    def _handle_scene_extraction(self, request: ChapterPlotWithScenesRequest, project_root: Path):
        if not request.auto_scenes:
            return {"extracted": False, "count": 0, "file": None}

        scene_use_case = SceneExtractionUseCase(
            plot_repository=self._deps.plot_repository,
            foreshadowing_repository=self._deps.foreshadowing_repository,
            scene_repository=self._deps.scene_repository,
            scene_extractor=self._deps.scene_extractor,
            project_repository=self._deps.project_repository,
        )

        scene_request = SceneExtractionRequest(
            project_name=request.project_name,
            use_master_plot=False,
            use_foreshadowing=True,
            use_chapter_plots=True,
            merge_existing=request.merge_existing,
            detailed_mode=True,
        )

        scene_response = scene_use_case.execute(scene_request)
        if scene_response.status != SceneExtractionStatus.SUCCESS:
            message = (
                "章別プロットは作成されましたが、細かな伏線抽出に失敗しました"
                if not getattr(scene_response, "message", None)
                else f"章別プロットは作成されましたが、細かな伏線抽出に失敗しました: {scene_response.message}"
            )
            status = ChapterPlotWithScenesStatus.PARTIAL_SUCCESS
            if scene_response.status == SceneExtractionStatus.ERROR:
                status = ChapterPlotWithScenesStatus.ERROR
            return ChapterPlotWithScenesResponse(
                status=status,
                message=message,
                scenes_extracted=False,
                scene_file=scene_response.scene_file,
                extracted_scene_count=scene_response.extracted_count,
            )

        return {
            "extracted": scene_response.extracted_count > 0,
            "count": scene_response.extracted_count,
            "file": scene_response.scene_file,
        }
