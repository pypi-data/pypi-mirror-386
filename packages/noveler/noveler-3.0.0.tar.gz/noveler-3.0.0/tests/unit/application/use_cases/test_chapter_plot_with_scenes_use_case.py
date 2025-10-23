"""
章別プロット作成と重要シーン抽出の統合ユースケースのテスト

TDD原則に従った単体テスト


仕様書: SPEC-APPLICATION-USE-CASES
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from noveler.application.use_cases.chapter_plot_with_scenes_use_case import (
    ChapterPlotWithScenesRequest,
    ChapterPlotWithScenesStatus,
    ChapterPlotWithScenesUseCase,
)
from noveler.application.use_cases.foreshadowing_design_use_case import (
    ForeshadowingDesignResponse,
    ForeshadowingDesignStatus,
)
from noveler.application.use_cases.plot_creation_orchestrator import PlotCreationResponse
from noveler.application.use_cases.scene_extraction_use_case import (
    SceneExtractionResponse,
    SceneExtractionStatus,
)
from noveler.presentation.shared.shared_utilities import get_common_path_service


class TestChapterPlotWithScenesUseCase:
    """章別プロット作成と重要シーン抽出の統合ユースケースのテスト"""

    def setup_method(self) -> None:
        """テストセットアップ"""
        self.mock_project_repo = Mock()
        self.mock_plot_repo = Mock()
        self.mock_foreshadowing_repo = Mock()
        self.mock_scene_repo = Mock()
        self.mock_plot_orchestrator = Mock()
        self.mock_scene_extractor = Mock()
        self.mock_foreshadowing_extractor = Mock()

        from noveler.application.use_cases.chapter_plot_with_scenes_use_case import ChapterPlotDependencies

        dependencies = ChapterPlotDependencies(
            project_repository=self.mock_project_repo,
            plot_repository=self.mock_plot_repo,
            foreshadowing_repository=self.mock_foreshadowing_repo,
            scene_repository=self.mock_scene_repo,
            plot_orchestrator=self.mock_plot_orchestrator,
            scene_extractor=self.mock_scene_extractor,
            foreshadowing_extractor=self.mock_foreshadowing_extractor,
        )

        self.use_case = ChapterPlotWithScenesUseCase(dependencies)

    @pytest.mark.spec("SPEC-CHAPTER_PLOT_WITH_SCENES_USE_CASE-CREATION")
    def test_creation(self) -> None:
        """プロット作成とシーン抽出の両方が成功する場合"""
        # Arrange
        project_name = "テスト小説"
        chapter = 1
        project_root = Path("/test/project")

        self.mock_project_repo.exists.return_value = True
        self.mock_project_repo.get_project_root.return_value = project_root

        # プロット作成の成功レスポンス
        path_service = get_common_path_service(project_root)
        path_service = get_common_path_service()
        plot_file = path_service.get_plots_dir() / "chapter01.yaml"
        self.mock_plot_orchestrator.execute_plot_creation.return_value = PlotCreationResponse(
            success=True, created_files=[plot_file], error_message=""
        )

        # 伏線抽出の成功レスポンス
        # from noveler.application.use_cases.foreshadowing_design_use_case import (  # Moved to top-level
        # ForeshadowingDesignResponse,
        # ForeshadowingDesignStatus,
        # )
        foreshadowing_file = path_service.get_management_dir() / "伏線管理.yaml"
        mock_foreshadowing_response = ForeshadowingDesignResponse(
            status=ForeshadowingDesignStatus.SUCCESS,
            message="伏線を抽出しました",
            created_count=3,
            existing_count=0,
            foreshadowing_file=foreshadowing_file,
        )

        # シーン抽出の成功レスポンス
        scene_file = path_service.get_management_dir() / "重要シーン.yaml"
        mock_scene_response = SceneExtractionResponse(
            status=SceneExtractionStatus.SUCCESS,
            message="重要シーンを抽出しました",
            extracted_count=5,
            existing_count=0,
            scene_file=scene_file,
        )

        # ForeshadowingDesignUseCaseとSceneExtractionUseCaseのモック
        with (
            patch(
                "noveler.application.use_cases.chapter_plot_with_scenes_use_case.ForeshadowingDesignUseCase"
            ) as MockForeshadowingUseCase,
            patch(
                "noveler.application.use_cases.chapter_plot_with_scenes_use_case.SceneExtractionUseCase"
            ) as MockSceneUseCase,
        ):
            mock_foreshadowing_use_case = MockForeshadowingUseCase.return_value
            mock_foreshadowing_use_case.execute.return_value = mock_foreshadowing_response

            mock_scene_use_case = MockSceneUseCase.return_value
            mock_scene_use_case.execute.return_value = mock_scene_response

            request = ChapterPlotWithScenesRequest(
                project_name=project_name,
                chapter=chapter,
                auto_foreshadowing=True,  # 明示的に設定
                auto_scenes=True,
                merge_existing=True,
            )

            # Act
            response = self.use_case.execute(request)

            # Assert
            assert response.status == ChapterPlotWithScenesStatus.SUCCESS
            assert response.plot_created is True
            assert response.foreshadowing_extracted is True
            assert response.scenes_extracted is True
            assert response.plot_file == plot_file
            assert response.foreshadowing_file == foreshadowing_file
            assert response.scene_file == scene_file
            assert response.extracted_foreshadowing_count == 3
            assert response.extracted_scene_count == 5
            assert "chapter01のプロットを作成しました" in response.message
            assert "3個の細かな伏線を追加しました" in response.message
            assert "5個の細かなシーンを追加しました" in response.message

    @pytest.mark.spec("SPEC-CHAPTER_PLOT_WITH_SCENES_USE_CASE-UNNAMED")
    def test_unnamed(self) -> None:
        """プロジェクトが存在しない場合のテスト"""
        # Arrange
        self.mock_project_repo.exists.return_value = False

        request = ChapterPlotWithScenesRequest(project_name="存在しないプロジェクト", chapter=1)

        # Act
        response = self.use_case.execute(request)

        # Assert
        assert response.status == ChapterPlotWithScenesStatus.ERROR
        assert "が見つかりません" in response.message
        assert response.plot_created is False
        assert response.scenes_extracted is False

    @pytest.mark.spec("SPEC-CHAPTER_PLOT_WITH_SCENES_USE_CASE-CREATION_DONE")
    def test_creation_done(self) -> None:
        """プロット作成に失敗した場合のテスト"""
        # Arrange
        project_root = Path("/test/project")
        self.mock_project_repo.exists.return_value = True
        self.mock_project_repo.get_project_root.return_value = project_root

        # プロット作成の失敗レスポンス
        self.mock_plot_orchestrator.execute_plot_creation.return_value = PlotCreationResponse(
            success=False, created_files=[], error_message="テンプレートが見つかりません"
        )

        request = ChapterPlotWithScenesRequest(project_name="テスト小説", chapter=1, auto_scenes=True)

        # Act
        response = self.use_case.execute(request)

        # Assert
        assert response.status == ChapterPlotWithScenesStatus.PLOT_CREATION_FAILED
        assert "章別プロット作成に失敗しました" in response.message
        assert response.plot_created is False
        assert response.scenes_extracted is False

    @pytest.mark.spec("SPEC-CHAPTER_PLOT_WITH_SCENES_USE_CASE-PLOT_SUCCESS_SCENE_E")
    def test_plot_success_scene_extraction_failure(self) -> None:
        """プロット作成は成功したがシーン抽出に失敗した場合"""
        # Arrange
        project_root = Path("/test/project")
        self.mock_project_repo.exists.return_value = True
        self.mock_project_repo.get_project_root.return_value = project_root

        # プロット作成の成功レスポンス
        path_service = get_common_path_service(project_root)
        path_service = get_common_path_service()
        plot_file = path_service.get_plots_dir() / "chapter01.yaml"
        self.mock_plot_orchestrator.execute_plot_creation.return_value = PlotCreationResponse(
            success=True, created_files=[plot_file], error_message=""
        )

        # シーン抽出の失敗レスポンス
        mock_scene_response = SceneExtractionResponse(
            status=SceneExtractionStatus.MASTER_PLOT_NOT_FOUND, message="全体構成.yamlが見つかりません"
        )

        with patch(
            "noveler.application.use_cases.chapter_plot_with_scenes_use_case.SceneExtractionUseCase"
        ) as MockSceneUseCase:
            mock_scene_use_case = MockSceneUseCase.return_value
            mock_scene_use_case.execute.return_value = mock_scene_response

            request = ChapterPlotWithScenesRequest(project_name="テスト小説", chapter=1, auto_scenes=True)

            # Act
            response = self.use_case.execute(request)

            # Assert
            assert response.status == ChapterPlotWithScenesStatus.PARTIAL_SUCCESS
            assert "章別プロットは作成されましたが、細かな伏線抽出に失敗しました" in response.message
            assert response.plot_created is True
            assert response.scenes_extracted is False
            assert response.plot_file == plot_file

    @pytest.mark.spec("SPEC-CHAPTER_PLOT_WITH_SCENES_USE_CASE-UNEXPECTED_EXCEPTION")
    def test_unexpected_exception_handling(self) -> None:
        """予期しない例外が発生した場合"""
        # Arrange
        self.mock_project_repo.exists.side_effect = Exception("データベースエラー")

        request = ChapterPlotWithScenesRequest(project_name="テスト小説", chapter=1)

        # Act
        response = self.use_case.execute(request)

        # Assert
        assert response.status == ChapterPlotWithScenesStatus.ERROR
        assert "予期しないエラーが発生しました" in response.message
        assert response.plot_created is False
        assert response.scenes_extracted is False
