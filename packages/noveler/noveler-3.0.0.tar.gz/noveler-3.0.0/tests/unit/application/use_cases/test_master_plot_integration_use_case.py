"""
全体構成と伏線・重要シーン統合ユースケースのテスト

TDD原則に従った単体テスト


仕様書: SPEC-INTEGRATION
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from noveler.application.use_cases.foreshadowing_design_use_case import (
    ForeshadowingDesignResponse,
    ForeshadowingDesignStatus,
)
from noveler.application.use_cases.master_plot_integration_use_case import (
    MasterPlotIntegrationRequest,
    MasterPlotIntegrationStatus,
    MasterPlotIntegrationUseCase,
)
from noveler.application.use_cases.plot_creation_orchestrator import PlotCreationResponse
from noveler.domain.value_objects.domain_message import DomainMessage
from noveler.application.use_cases.scene_extraction_use_case import (
    SceneExtractionResponse,
    SceneExtractionStatus,
)
from noveler.presentation.shared.shared_utilities import get_common_path_service


class TestMasterPlotIntegrationUseCase:
    """全体構成と伏線・重要シーン統合ユースケースのテスト"""

    def setup_method(self) -> None:
        """テストセットアップ"""
        self.mock_project_repo = Mock()
        self.mock_plot_repo = Mock()
        self.mock_foreshadowing_repo = Mock()
        self.mock_scene_repo = Mock()
        self.mock_plot_orchestrator = Mock()
        self.mock_scene_extractor = Mock()
        self.mock_foreshadowing_extractor = Mock()

        from noveler.application.use_cases.master_plot_integration_use_case import (
            IntegrationRepositoryCollection,
            IntegrationServiceCollection,
        )

        repositories = IntegrationRepositoryCollection(
            project_repository=self.mock_project_repo,
            plot_repository=self.mock_plot_repo,
            foreshadowing_repository=self.mock_foreshadowing_repo,
            scene_repository=self.mock_scene_repo,
        )

        services = IntegrationServiceCollection(
            plot_orchestrator=self.mock_plot_orchestrator,
            scene_extractor=self.mock_scene_extractor,
            foreshadowing_extractor=self.mock_foreshadowing_extractor,
        )

        self.use_case = MasterPlotIntegrationUseCase(repositories, services)

    @pytest.mark.spec("SPEC-MASTER_PLOT_INTEGRATION_USE_CASE-ALL_ALL")
    def test_all_all(self) -> None:
        """全体構成作成、伏線設計、シーン抽出の全てが成功する場合"""
        # Arrange
        project_name = "テスト小説"
        project_root = Path("/test/project")

        self.mock_project_repo.exists.return_value = True
        self.mock_project_repo.get_project_root.return_value = project_root

        # 全体構成作成の成功レスポンス
        path_service = get_common_path_service()
        master_plot_file = project_root / str(path_service.get_plots_dir()) / "全体構成.yaml"
        self.mock_plot_orchestrator.execute_plot_creation.return_value = PlotCreationResponse(
            success=True, created_files=[master_plot_file], error_message=""
        )

        # 伏線設計の成功レスポンス
        foreshadowing_file = project_root / str(path_service.get_management_dir()) / "伏線管理.yaml"
        mock_foreshadowing_response = ForeshadowingDesignResponse(
            status=ForeshadowingDesignStatus.SUCCESS,
            message="主要伏線を設計しました",
            created_count=3,
            existing_count=0,
            foreshadowing_file=foreshadowing_file,
            foreshadowing_summary="F001: 主人公の正体\nF002: 世界の秘密\nF003: 最終ボスの謎",
        )

        # シーン抽出の成功レスポンス
        scene_file = project_root / str(path_service.get_management_dir()) / "重要シーン.yaml"
        mock_scene_response = SceneExtractionResponse(
            status=SceneExtractionStatus.SUCCESS,
            message="主要シーンを抽出しました",
            extracted_count=7,
            existing_count=0,
            scene_file=scene_file,
        )

        # ForeshadowingDesignUseCaseとSceneExtractionUseCaseのモック
        with (
            patch(
                "noveler.application.use_cases.master_plot_integration_use_case.ForeshadowingDesignUseCase"
            ) as MockForeshadowingUseCase,
            patch(
                "noveler.application.use_cases.master_plot_integration_use_case.SceneExtractionUseCase"
            ) as MockSceneUseCase,
        ):
            mock_foreshadowing_use_case = MockForeshadowingUseCase.return_value
            mock_foreshadowing_use_case.execute.return_value = mock_foreshadowing_response

            mock_scene_use_case = MockSceneUseCase.return_value
            mock_scene_use_case.execute.return_value = mock_scene_response

            request = MasterPlotIntegrationRequest(
                project_name=project_name, auto_foreshadowing=True, auto_scenes=True, merge_existing=True
            )

            # Act
            response = self.use_case.execute(request)

            # Assert
            assert response.status == MasterPlotIntegrationStatus.SUCCESS
            assert response.master_plot_created is True
            assert response.foreshadowing_created is True
            assert response.scenes_extracted is True
            assert response.master_plot_file == master_plot_file
            assert response.foreshadowing_file == foreshadowing_file
            assert response.scene_file == scene_file
            assert response.foreshadowing_count == 3
            assert response.scene_count == 7
            assert "全体構成を作成しました" in response.message
            assert "3個の主要伏線を設計しました" in response.message
            assert "7個の主要シーンを抽出しました" in response.message

    @pytest.mark.spec("SPEC-MASTER_PLOT_INTEGRATION_USE_CASE-UNNAMED")
    def test_unnamed(self) -> None:
        """プロジェクトが存在しない場合のテスト"""
        # Arrange
        self.mock_project_repo.exists.return_value = False

        request = MasterPlotIntegrationRequest(project_name="存在しないプロジェクト")

        # Act
        response = self.use_case.execute(request)

        # Assert
        assert response.status == MasterPlotIntegrationStatus.ERROR
        assert "が見つかりません" in response.message
        assert response.master_plot_created is False
        assert response.foreshadowing_created is False
        assert response.scenes_extracted is False

    @pytest.mark.spec("SPEC-MASTER_PLOT_INTEGRATION_USE_CASE-ALL_CREATION_DONE")
    def test_all_creation_done(self) -> None:
        """全体構成作成に失敗した場合のテスト"""
        # Arrange
        project_root = Path("/test/project")
        self.mock_project_repo.exists.return_value = True
        self.mock_project_repo.get_project_root.return_value = project_root

        # 全体構成作成の失敗レスポンス
        self.mock_plot_orchestrator.execute_plot_creation.return_value = PlotCreationResponse(
            success=False,
            created_files=[],
            error_message="テンプレートが見つかりません",
            messages=[DomainMessage(level="error", message="テンプレートの検証に失敗しました")],
        )

        request = MasterPlotIntegrationRequest(project_name="テスト小説", auto_foreshadowing=True, auto_scenes=True)

        # Act
        response = self.use_case.execute(request)

        # Assert
        assert response.status == MasterPlotIntegrationStatus.MASTER_PLOT_FAILED
        assert "全体構成作成に失敗しました" in response.message
        assert response.master_plot_created is False
        assert response.foreshadowing_created is False
        assert response.scenes_extracted is False
        assert "テンプレートの検証に失敗しました" in response.message

    @pytest.mark.spec("SPEC-MASTER_PLOT_INTEGRATION_USE_CASE-DONE")
    def test_done(self) -> None:
        """全体構成は成功したが伏線設計に失敗した場合"""
        # Arrange
        project_root = Path("/test/project")
        self.mock_project_repo.exists.return_value = True
        self.mock_project_repo.get_project_root.return_value = project_root

        # 全体構成作成の成功レスポンス
        path_service = get_common_path_service()
        master_plot_file = project_root / str(path_service.get_plots_dir()) / "全体構成.yaml"
        self.mock_plot_orchestrator.execute_plot_creation.return_value = PlotCreationResponse(
            success=True, created_files=[master_plot_file], error_message=""
        )

        # 伏線設計の失敗レスポンス
        mock_foreshadowing_response = ForeshadowingDesignResponse(
            status=ForeshadowingDesignStatus.MASTER_PLOT_NOT_FOUND, message="全体構成の読み込みに失敗しました"
        )

        with patch(
            "noveler.application.use_cases.master_plot_integration_use_case.ForeshadowingDesignUseCase"
        ) as MockForeshadowingUseCase:
            mock_foreshadowing_use_case = MockForeshadowingUseCase.return_value
            mock_foreshadowing_use_case.execute.return_value = mock_foreshadowing_response

            request = MasterPlotIntegrationRequest(
                project_name="テスト小説",
                auto_foreshadowing=True,
                auto_scenes=False,  # シーン抽出は無効
            )

            # Act
            response = self.use_case.execute(request)

            # Assert
            assert response.status == MasterPlotIntegrationStatus.PARTIAL_SUCCESS
            assert "全体構成は作成されましたが、伏線設計に失敗しました" in response.message
            assert response.master_plot_created is True
            assert response.foreshadowing_created is False
            assert response.scenes_extracted is False
            assert response.master_plot_file == master_plot_file

    @pytest.mark.spec("SPEC-MASTER_PLOT_INTEGRATION_USE_CASE-DONE")
    def test_done_1(self) -> None:
        """予期しない例外が発生した場合"""
        # Arrange
        self.mock_project_repo.exists.side_effect = Exception("データベースエラー")

        request = MasterPlotIntegrationRequest(project_name="テスト小説")

        # Act
        response = self.use_case.execute(request)

        # Assert
        assert response.status == MasterPlotIntegrationStatus.ERROR
        assert "予期しないエラーが発生しました" in response.message
        assert response.master_plot_created is False
        assert response.foreshadowing_created is False
        assert response.scenes_extracted is False
