"""
細かな伏線追加機能のテスト

TDD原則に従った単体テスト
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from noveler.application.use_cases.foreshadowing_design_use_case import (
    ForeshadowingDesignRequest,
    ForeshadowingDesignStatus,
    ForeshadowingDesignUseCase,
)
from noveler.presentation.shared.shared_utilities import get_common_path_service


class TestDetailedForeshadowingUseCase:
    """細かな伏線追加機能のテスト"""

    def setup_method(self) -> None:
        """テストセットアップ"""
        self.mock_project_repo = Mock()
        self.mock_plot_repo = Mock()
        self.mock_foreshadowing_repo = Mock()
        self.mock_foreshadowing_extractor = Mock()

        self.use_case = ForeshadowingDesignUseCase(
            project_repository=self.mock_project_repo,
            plot_repository=self.mock_plot_repo,
            foreshadowing_repository=self.mock_foreshadowing_repo,
            foreshadowing_extractor=self.mock_foreshadowing_extractor,
        )

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_add(self) -> None:
        """章別プロットから細かな伏線を追加する場合のテスト"""
        # Arrange
        project_name = "テスト小説"
        project_root = Path("/test/project")

        self.mock_project_repo.exists.return_value = True
        self.mock_project_repo.get_project_root.return_value = project_root

        # 既存の主要伏線が存在(全体構成から生成済み)
        path_service = get_common_path_service()
        existing_foreshadowing_file = project_root / str(path_service.get_management_dir()) / "伏線管理.yaml"
        self.mock_foreshadowing_repo.get_foreshadowing_file_path.return_value = existing_foreshadowing_file
        self.mock_foreshadowing_repo.exists.return_value = True

        # 章別プロットが存在
        chapter_plot_file = project_root / str(path_service.get_plots_dir()) / "chapter01.yaml"
        self.mock_plot_repo.get_chapter_plot_files.return_value = [chapter_plot_file]

        # 細かな伏線を抽出(章固有の要素)
        detailed_foreshadowing = [
            Mock(id=Mock(value="F003"), title="主人公とヒロインの出会い", importance=3),
            Mock(id=Mock(value="F004"), title="敵キャラクターの正体のほのめかし", importance=2),
        ]
        self.mock_foreshadowing_extractor.extract_detailed_foreshadowing_from_chapter.return_value = (
            detailed_foreshadowing
        )

        # 既存伏線の読み込みをモック
        existing_foreshadowing = [
            Mock(id=Mock(value="F001"), title="既存の主要伏線1", importance=5),
            Mock(id=Mock(value="F002"), title="既存の主要伏線2", importance=5),
        ]
        self.mock_foreshadowing_repo.load_all.return_value = existing_foreshadowing

        # 保存処理をモック
        self.mock_foreshadowing_repo.save_all.return_value = True

        # リクエストを作成(source="chapter_plot"で細かな伏線を指定)
        request = ForeshadowingDesignRequest(
            project_name=project_name,
            source="chapter_plot",  # 章別プロットから細かな伏線を抽出
            auto_extract=True,
            interactive=False,
            merge_existing=True,
            detailed_mode=True,  # 細かな伏線モード
        )

        # Act
        response = self.use_case.execute(request)

        # Assert
        assert response.status == ForeshadowingDesignStatus.SUCCESS
        assert response.created_count == 2
        assert "細かな伏線" in response.message or "詳細伏線" in response.message
        assert response.foreshadowing_file == existing_foreshadowing_file

        # 章別プロットから細かな伏線を抽出することを確認
        self.mock_foreshadowing_extractor.extract_detailed_foreshadowing_from_chapter.assert_called_once()
        self.mock_foreshadowing_repo.save_all.assert_called_once()

    @pytest.mark.spec("SPEC-PLOT-001")
    @pytest.mark.spec("SPEC-PLOT-001")
    def test_all(self) -> None:
        """全体構成から主要伏線を抽出する場合のテスト(既存機能の確認)"""
        # Arrange
        project_name = "テスト小説"
        project_root = Path("/test/project")

        self.mock_project_repo.exists.return_value = True
        self.mock_project_repo.get_project_root.return_value = project_root

        # 全体構成が存在
        path_service = get_common_path_service()
        master_plot_file = project_root / str(path_service.get_plots_dir()) / "全体構成.yaml"
        self.mock_plot_repo.get_master_plot_file.return_value = master_plot_file
        self.mock_plot_repo.master_plot_exists.return_value = True

        # マスタープロットデータを用意
        master_plot_data = {"title": "テスト小説", "chapters": []}
        self.mock_plot_repo.load_master_plot.return_value = master_plot_data

        # 主要伏線を抽出(物語の核心)
        foreshadowing1 = Mock(id=Mock(value="F001"), title="主人公の正体", importance=5)
        foreshadowing1.to_summary.return_value = "F001: 主人公の正体"

        foreshadowing2 = Mock(id=Mock(value="F002"), title="世界の秘密", importance=5)
        foreshadowing2.to_summary.return_value = "F002: 世界の秘密"

        major_foreshadowing = [foreshadowing1, foreshadowing2]
        self.mock_foreshadowing_extractor.extract_from_master_plot.return_value = major_foreshadowing

        # 保存処理をモック
        self.mock_foreshadowing_repo.save_all.return_value = True

        request = ForeshadowingDesignRequest(
            project_name=project_name,
            source="master_plot",  # 全体構成から主要伏線を抽出
            auto_extract=True,
            merge_existing=False,  # 既存ファイルとのマージを無効化
            detailed_mode=False,  # 主要伏線モード
        )

        # Act
        response = self.use_case.execute(request)

        # Assert
        assert response.status == ForeshadowingDesignStatus.SUCCESS
        assert response.created_count == 2
        assert "主要伏線" in response.message or "伏線" in response.message

        # 全体構成から主要伏線を抽出することを確認
        self.mock_foreshadowing_extractor.extract_from_master_plot.assert_called_once()

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_add_fileerror(self) -> None:
        """主要伏線ファイルが存在しない状態で細かな伏線を追加しようとした場合"""
        # Arrange
        project_name = "テスト小説"
        project_root = Path("/test/project")

        self.mock_project_repo.exists.return_value = True
        self.mock_project_repo.get_project_root.return_value = project_root
        self.mock_foreshadowing_repo.exists.return_value = False  # 伏線ファイルが存在しない

        request = ForeshadowingDesignRequest(project_name=project_name, source="chapter_plot", detailed_mode=True)

        # Act
        response = self.use_case.execute(request)

        # Assert
        assert response.status == ForeshadowingDesignStatus.FORESHADOWING_FILE_NOT_FOUND
        assert "主要伏線" in response.message
        assert "先に" in response.message
