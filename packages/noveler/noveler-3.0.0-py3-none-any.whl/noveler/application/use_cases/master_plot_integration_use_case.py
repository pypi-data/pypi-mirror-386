"""
全体構成と伏線・重要シーン統合ユースケース

DDD原則に基づくアプリケーション層の実装
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from noveler.application.use_cases.foreshadowing_design_use_case import (
    ForeshadowingDesignRequest,
    ForeshadowingDesignStatus,
    ForeshadowingDesignUseCase,
)
from noveler.application.use_cases.plot_creation_orchestrator import (
    PlotCreationOrchestrator,
    PlotCreationRequest,
)
from noveler.domain.value_objects.domain_message import DomainMessage
from noveler.application.use_cases.scene_extraction_use_case import (
    SceneExtractionRequest,
    SceneExtractionStatus,
    SceneExtractionUseCase,
)
from noveler.domain.repositories.foreshadowing_repository import ForeshadowingRepository
from noveler.domain.repositories.plot_repository import PlotRepository
from noveler.domain.repositories.project_repository import ProjectRepository
from noveler.domain.repositories.scene_repository import SceneRepository
from noveler.domain.services.foreshadowing_extractor import ForeshadowingExtractor
from noveler.domain.services.scene_extractor import SceneExtractor
from noveler.domain.value_objects.workflow_stage_type import WorkflowStageType

# DDD準拠: Infrastructure層実装ではなくDomain層インターフェースを使用
# 具体的な実装は依存性注入で解決される


@dataclass
class IntegrationRepositoryCollection:
    """統合機能のリポジトリ群

    DDD準拠: Infrastructure層実装ではなくDomain層インターフェースを使用
    """

    project_repository: ProjectRepository
    plot_repository: PlotRepository
    # DDD準拠: 具体的実装ではなくDomain層インターフェースを使用
    foreshadowing_repository: ForeshadowingRepository
    scene_repository: SceneRepository


@dataclass
class IntegrationServiceCollection:
    """統合機能のサービス群"""

    plot_orchestrator: PlotCreationOrchestrator
    scene_extractor: SceneExtractor
    foreshadowing_extractor: ForeshadowingExtractor


class MasterPlotIntegrationStatus(Enum):
    """全体構成統合のステータス"""

    SUCCESS = "success"
    MASTER_PLOT_FAILED = "master_plot_failed"
    FORESHADOWING_FAILED = "foreshadowing_failed"
    SCENE_EXTRACTION_FAILED = "scene_extraction_failed"
    PARTIAL_SUCCESS = "partial_success"
    ERROR = "error"


@dataclass
class MasterPlotIntegrationRequest:
    """全体構成統合のリクエスト"""

    project_name: str
    auto_foreshadowing: bool = True  # 主要伏線を自動設計するか
    auto_scenes: bool = True  # 主要シーンを自動抽出するか
    merge_existing: bool = True  # 既存データとマージするか


@dataclass
class MasterPlotIntegrationResponse:
    """全体構成統合のレスポンス"""

    status: MasterPlotIntegrationStatus
    message: str
    master_plot_created: bool = False
    foreshadowing_created: bool = False
    scenes_extracted: bool = False
    master_plot_file: Path | None = None
    foreshadowing_file: Path | None = None
    scene_file: Path | None = None
    foreshadowing_count: int = 0
    scene_count: int = 0


class MasterPlotIntegrationUseCase:
    """全体構成と伏線・重要シーン統合ユースケース"""

    def __init__(self, repositories: IntegrationRepositoryCollection, services: IntegrationServiceCollection) -> None:
        """初期化

        Args:
            repositories: 統合機能のリポジトリ群
            services: 統合機能のサービス群
        """
        # リポジトリ
        self.project_repository = repositories.project_repository
        self.plot_repository = repositories.plot_repository
        self.foreshadowing_repository = repositories.foreshadowing_repository
        self.scene_repository = repositories.scene_repository
        # サービス
        self.plot_orchestrator = services.plot_orchestrator
        self.scene_extractor = services.scene_extractor
        self.foreshadowing_extractor = services.foreshadowing_extractor

    def execute(self, request: MasterPlotIntegrationRequest) -> MasterPlotIntegrationResponse:
        """全体構成と伏線・重要シーン統合を実行(リファクタリング済み:複雑度13→5に削減)

        Args:
            request: リクエスト

        Returns:
            MasterPlotIntegrationResponse: レスポンス
        """
        try:
            # プロジェクト存在確認
            project_root = self._validate_project(request)
            if isinstance(project_root, MasterPlotIntegrationResponse):
                return project_root

            # 統合処理の実行
            return self._execute_integration_steps(request, project_root)

        except Exception as e:
            return MasterPlotIntegrationResponse(
                status=MasterPlotIntegrationStatus.ERROR, message=f"予期しないエラーが発生しました: {e}"
            )

    def _validate_project(self, request: MasterPlotIntegrationRequest) -> Path | MasterPlotIntegrationResponse:
        """プロジェクトの存在確認"""
        if not self.project_repository.exists(request.project_name):
            return MasterPlotIntegrationResponse(
                status=MasterPlotIntegrationStatus.ERROR,
                message=f"プロジェクト '{request.project_name}' が見つかりません",
            )

        return self.project_repository.get_project_root(request.project_name)

    def _execute_integration_steps(
        self, request: MasterPlotIntegrationRequest, project_root: Path
    ) -> MasterPlotIntegrationResponse:
        """統合処理の各ステップを実行"""
        # 初期化
        context = self._initialize_integration_context()

        # ステップ1: 全体構成作成
        master_plot_result = self._create_master_plot(project_root)
        if isinstance(master_plot_result, MasterPlotIntegrationResponse):
            return master_plot_result
        context["master_plot_file"] = master_plot_result

        # ステップ2: 伏線設計(オプション)
        if request.auto_foreshadowing:
            foreshadowing_result = self._design_foreshadowing(request, context)
            if isinstance(foreshadowing_result, MasterPlotIntegrationResponse):
                return foreshadowing_result
            context.update(foreshadowing_result)

        # ステップ3: シーン抽出(オプション)
        if request.auto_scenes:
            scene_result = self._extract_scenes(request, context)
            if isinstance(scene_result, MasterPlotIntegrationResponse):
                return scene_result
            context.update(scene_result)

        # 成功レスポンス構築
        return self._build_success_response(context)

    def _initialize_integration_context(self) -> dict[str, Any]:
        """統合処理のコンテキストを初期化"""
        return {
            "foreshadowing_created": False,
            "scenes_extracted": False,
            "master_plot_file": None,
            "foreshadowing_file": None,
            "scene_file": None,
            "foreshadowing_count": 0,
            "scene_count": 0,
        }

    def _create_master_plot(self, project_root: Path) -> Path | MasterPlotIntegrationResponse:
        """全体構成を作成"""
        plot_request = PlotCreationRequest(
            stage_type=WorkflowStageType.MASTER_PLOT, project_root=project_root, parameters={}, auto_confirm=True
        )

        plot_response = self.plot_orchestrator.execute_plot_creation(plot_request)

        if not plot_response.success:
            extra = self._format_domain_messages(plot_response.messages)
            message = f"全体構成作成に失敗しました: {plot_response.error_message}"
            if extra:
                message = f"{message}\n{extra}"
            return MasterPlotIntegrationResponse(
                status=MasterPlotIntegrationStatus.MASTER_PLOT_FAILED,
                message=message,
                master_plot_created=False,
                foreshadowing_created=False,
                scenes_extracted=False,
            )

        # 作成されたファイルから全体構成ファイルを特定
        master_plot_file = None
        for file_path in plot_response.created_files:
            if "全体構成" in str(file_path):
                master_plot_file = file_path
                break
        if not master_plot_file and plot_response.created_files:
            master_plot_file = plot_response.created_files[0]

        return master_plot_file

    def _format_domain_messages(self, messages: list[DomainMessage]) -> str:
        """Convert domain messages into a human-readable bullet list."""

        if not messages:
            return ""

        lines: list[str] = []
        for msg in messages:
            line = f"- [{msg.level.upper()}] {msg.message}"
            if msg.suggestion:
                line = f"{line} (hint: {msg.suggestion})"
            if msg.details:
                line = f"{line} | details: {dict(msg.details)}"
            lines.append(line)
        return "\n".join(lines)

    def _design_foreshadowing(
        self, request: MasterPlotIntegrationRequest, context: dict[str, Any]
    ) -> dict[str, Any] | MasterPlotIntegrationResponse:
        """伏線設計を実行"""
        foreshadowing_use_case = ForeshadowingDesignUseCase(
            project_repository=self.project_repository,
            plot_repository=self.plot_repository,
            foreshadowing_repository=self.foreshadowing_repository,
            foreshadowing_extractor=self.foreshadowing_extractor,
        )

        foreshadowing_request = ForeshadowingDesignRequest(
            project_name=request.project_name,
            source="master_plot",
            auto_extract=True,
            interactive=False,
            merge_existing=request.merge_existing,
        )

        foreshadowing_response = foreshadowing_use_case.execute(foreshadowing_request)

        if foreshadowing_response.status != ForeshadowingDesignStatus.SUCCESS:
            return MasterPlotIntegrationResponse(
                status=MasterPlotIntegrationStatus.PARTIAL_SUCCESS,
                message=f"全体構成は作成されましたが、伏線設計に失敗しました: {foreshadowing_response.message}",
                master_plot_created=True,
                foreshadowing_created=False,
                scenes_extracted=False,
                master_plot_file=context["master_plot_file"],
            )

        return {
            "foreshadowing_created": True,
            "foreshadowing_file": foreshadowing_response.foreshadowing_file,
            "foreshadowing_count": foreshadowing_response.created_count,
        }

    def _extract_scenes(
        self, request: MasterPlotIntegrationRequest, context: dict[str, Any]
    ) -> dict[str, Any] | MasterPlotIntegrationResponse:
        """シーン抽出を実行"""
        scene_use_case = SceneExtractionUseCase(
            project_repository=self.project_repository,
            plot_repository=self.plot_repository,
            foreshadowing_repository=self.foreshadowing_repository,
            scene_repository=self.scene_repository,
            scene_extractor=self.scene_extractor,
        )

        scene_request = SceneExtractionRequest(
            project_name=request.project_name,
            use_master_plot=True,
            use_foreshadowing=context["foreshadowing_created"],
            merge_existing=request.merge_existing,
            auto_categorize=True,
        )

        scene_response = scene_use_case.execute(scene_request)

        if scene_response.status != SceneExtractionStatus.SUCCESS:
            return MasterPlotIntegrationResponse(
                status=MasterPlotIntegrationStatus.PARTIAL_SUCCESS,
                message=f"全体構成・伏線は作成されましたが、シーン抽出に失敗しました: {scene_response.message}",
                master_plot_created=True,
                foreshadowing_created=context["foreshadowing_created"],
                scenes_extracted=False,
                master_plot_file=context["master_plot_file"],
                foreshadowing_file=context.get("foreshadowing_file"),
                foreshadowing_count=context["foreshadowing_count"],
            )

        return {
            "scenes_extracted": True,
            "scene_file": scene_response.scene_file,
            "scene_count": scene_response.extracted_count,
        }

    def _build_success_response(self, context: dict[str, Any]) -> MasterPlotIntegrationResponse:
        """成功レスポンスを構築"""
        message_parts = ["全体構成を作成しました"]
        if context["foreshadowing_created"]:
            message_parts.append(f"{context['foreshadowing_count']}個の主要伏線を設計しました")
        if context["scenes_extracted"]:
            message_parts.append(f"{context['scene_count']}個の主要シーンを抽出しました")

        return MasterPlotIntegrationResponse(
            status=MasterPlotIntegrationStatus.SUCCESS,
            message="。".join(message_parts),
            master_plot_created=True,
            foreshadowing_created=context["foreshadowing_created"],
            scenes_extracted=context["scenes_extracted"],
            master_plot_file=context["master_plot_file"],
            foreshadowing_file=context.get("foreshadowing_file"),
            scene_file=context.get("scene_file"),
            foreshadowing_count=context["foreshadowing_count"],
            scene_count=context["scene_count"],
        )
