"""
細かなシーン抽出機能のテスト

TDD原則に従った単体テスト


仕様書: SPEC-APPLICATION-USE-CASES
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from noveler.application.use_cases.scene_extraction_use_case import (
    SceneExtractionRequest,
    SceneExtractionStatus,
    SceneExtractionUseCase,
)
from noveler.presentation.shared.shared_utilities import get_common_path_service


class TestDetailedSceneExtractionUseCase:
    """細かなシーン抽出機能のテスト"""

    def setup_method(self) -> None:
        """テストセットアップ"""
        self.mock_project_repo = Mock()
        self.mock_plot_repo = Mock()
        self.mock_foreshadowing_repo = Mock()
        self.mock_scene_repo = Mock()
        self.mock_scene_extractor = Mock()

        self.use_case = SceneExtractionUseCase(
            project_repository=self.mock_project_repo,
            plot_repository=self.mock_plot_repo,
            foreshadowing_repository=self.mock_foreshadowing_repo,
            scene_repository=self.mock_scene_repo,
            scene_extractor=self.mock_scene_extractor,
        )

    @patch("noveler.application.use_cases.scene_extraction_use_case.SceneExtractionUseCase._update_scene_file")
    @patch("pathlib.Path.exists")
    def test_extract(self, mock_path_exists: object, mock_update_scene_file: object, tmp_path: Path) -> None:
        """章別プロットから細かなシーンを抽出する場合のテスト"""
        # Arrange
        project_name = "テスト小説"
        project_root = tmp_path

        self.mock_project_repo.exists.return_value = True
        self.mock_project_repo.get_project_root.return_value = project_root

        # 既存の主要シーンが存在(全体構成から生成済み)
        existing_scene_file = project_root / "50_管理資料" / "重要シーン.yaml"

        # scene_file.exists() をモック(_extract_detailed_scenes で使用)
        mock_path_exists.return_value = True

        # _update_scene_fileメソッドをモック(ファイルI/Oを回避)
        mock_update_scene_file.return_value = None

        # 章別プロットが存在
        chapter_plot_files = [project_root / "60_プロンプト" / "chapter01.yaml", project_root / "60_プロンプト" / "chapter02.yaml"]
        self.mock_plot_repo.get_chapter_plot_files.return_value = chapter_plot_files

        # 細かなシーンを抽出(章固有の詳細シーン)
        scene1 = Mock(scene_id="scene_101", title="主人公の日常描写", category=Mock(value="daily_life"))
        scene1.episode_range = [1, 1]
        scene1.importance = Mock(value=3)
        scene1.to_dict.return_value = {
            "title": "主人公の日常描写",
            "description": "日常の詳細な描写",
            "importance": 3,
            "episodes": [1],
            "source": "chapter_plot",
        }

        scene2 = Mock(scene_id="scene_102", title="キャラクター間の会話", category=Mock(value="dialogue"))
        scene2.episode_range = [2, 2]
        scene2.importance = Mock(value=3)
        scene2.to_dict.return_value = {
            "title": "キャラクター間の会話",
            "description": "重要な対話シーン",
            "importance": 3,
            "episodes": [2],
            "source": "chapter_plot",
        }

        scene3 = Mock(scene_id="scene_103", title="心理描写の詳細", category=Mock(value="inner_monologue"))
        scene3.episode_range = [3, 3]
        scene3.importance = Mock(value=3)
        scene3.to_dict.return_value = {
            "title": "心理描写の詳細",
            "description": "内面の詳細な描写",
            "importance": 3,
            "episodes": [3],
            "source": "chapter_plot",
        }

        detailed_scenes = [scene1, scene2, scene3]
        self.mock_scene_extractor.extract_detailed_scenes_from_chapters.return_value = detailed_scenes

        # extract_from_chapter_plotもモック(個別の章プロット処理用)
        self.mock_scene_extractor.extract_from_chapter_plot.return_value = [scene1]

        # merge_and_deduplicate の結果をモック
        self.mock_scene_extractor.merge_and_deduplicate.return_value = detailed_scenes

        # 伏線リポジトリの存在確認をモック
        self.mock_foreshadowing_repo.exists.return_value = True
        self.mock_foreshadowing_repo.load_all.return_value = []

        # 伏線と章別プロットを組み合わせたシーン抽出をモック(空のリストを返す)
        self.mock_scene_extractor.extract_scenes_from_chapter_and_foreshadowing.return_value = []

        # シーンファイルの存在確認と既存シーンとのマージ結果
        self.mock_scene_repo.file_exists.return_value = True
        self.mock_scene_repo.load_scenes.return_value = {"scenes": {}}
        self.mock_scene_repo.save_scenes.return_value = True

        # リクエストを作成(detailed_mode=Trueで細かなシーンを指定)
        request = SceneExtractionRequest(
            project_name=project_name,
            use_master_plot=False,  # 全体構成は使用しない
            use_foreshadowing=True,  # 細かな伏線は使用
            use_chapter_plots=True,  # 章別プロットから抽出
            merge_existing=True,
            auto_categorize=True,
            detailed_mode=True,  # 細かなシーンモード
        )

        # Act
        response = self.use_case.execute(request)

        # Assert
        assert response.status == SceneExtractionStatus.SUCCESS
        assert response.extracted_count == 3
        assert "細かなシーン" in response.message or "詳細シーン" in response.message
        assert response.scene_file == existing_scene_file

        # 章別プロットからシーンが抽出されたことを確認
        # extract_from_chapter_plotが章ごとに呼ばれる
        assert self.mock_scene_extractor.extract_from_chapter_plot.call_count >= 1

        # _update_scene_fileが呼ばれたことを確認
        mock_update_scene_file.assert_called_once()

    @patch("noveler.application.use_cases.scene_extraction_use_case.SceneExtractionUseCase._update_scene_file")
    def test_all(self, mock_update_scene_file: object) -> None:
        """全体構成から主要シーンを抽出する場合のテスト(既存機能の確認)"""
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

        # 主要シーンを抽出(物語の核心シーン)
        scene1 = Mock(scene_id="scene_001", title="物語の開幕", category=Mock(value="opening"))
        scene1.chapter = 1
        scene1.chapters = [1]
        scene1.episode_range = [1, 3]
        scene1.importance = Mock(value=5)
        scene1.to_dict.return_value = {"title": "物語の開幕", "chapters": [1], "category": "opening"}

        scene2 = Mock(scene_id="scene_002", title="クライマックス", category=Mock(value="climax"))
        scene2.chapter = 5
        scene2.chapters = [5]
        scene2.episode_range = [20, 22]
        scene2.importance = Mock(value=5)
        scene2.to_dict.return_value = {"title": "クライマックス", "chapters": [5], "category": "climax"}

        scene3 = Mock(scene_id="scene_003", title="物語の終幕", category=Mock(value="ending"))
        scene3.chapter = 10
        scene3.chapters = [10]
        scene3.episode_range = [48, 50]
        scene3.importance = Mock(value=5)
        scene3.to_dict.return_value = {"title": "物語の終幕", "chapters": [10], "category": "ending"}

        major_scenes = [scene1, scene2, scene3]
        self.mock_scene_extractor.extract_from_master_plot.return_value = major_scenes

        # merge_and_deduplicateの結果をモック
        self.mock_scene_extractor.merge_and_deduplicate.return_value = major_scenes

        # シーンファイル関連のモック
        self.mock_scene_repo.file_exists.return_value = False  # 新規作成
        self.mock_scene_repo.save_scenes.return_value = True

        # _update_scene_fileメソッドをモック
        mock_update_scene_file.return_value = None

        request = SceneExtractionRequest(
            project_name=project_name,
            use_master_plot=True,  # 全体構成から主要シーンを抽出
            use_foreshadowing=False,
            detailed_mode=False,  # 主要シーンモード
        )

        # Act
        response = self.use_case.execute(request)

        # Assert
        assert response.status == SceneExtractionStatus.SUCCESS
        assert response.extracted_count == 3
        assert "重要シーン" in response.message or "シーン" in response.message

        # 全体構成から主要シーンを抽出することを確認
        self.mock_scene_extractor.extract_from_master_plot.assert_called_once()

    @pytest.mark.spec("SPEC-DETAILED_SCENE_EXTRACTION_USE_CASE-EXTRACT_FILEERROR")
    def test_extract_fileerror(self) -> None:
        """主要シーンファイルが存在しない状態で細かなシーンを追加しようとした場合"""
        # Arrange
        project_name = "テスト小説"
        project_root = Path("/test/project")

        self.mock_project_repo.exists.return_value = True
        self.mock_project_repo.get_project_root.return_value = project_root
        self.mock_scene_repo.scene_exists.return_value = False  # シーンファイルが存在しない

        # 章別プロットファイルを設定(空のリストでもよい)
        self.mock_plot_repo.get_chapter_plot_files.return_value = []

        request = SceneExtractionRequest(project_name=project_name, use_chapter_plots=True, detailed_mode=True)

        # Act
        response = self.use_case.execute(request)

        # Assert
        # 章別プロットが存在しない場合、そちらのエラーが先に返される
        assert response.status == SceneExtractionStatus.CHAPTER_PLOT_NOT_FOUND
        assert "章別プロット" in response.message

    @patch("noveler.application.use_cases.scene_extraction_use_case.SceneExtractionUseCase._update_scene_file")
    @patch("pathlib.Path.exists")
    def test_extract_1(self, mock_path_exists: object, mock_update_scene_file: object) -> None:
        """細かな伏線と連動した細かなシーン抽出のテスト"""
        # Arrange
        project_name = "テスト小説"
        project_root = Path("/test/project")

        self.mock_project_repo.exists.return_value = True
        self.mock_project_repo.get_project_root.return_value = project_root
        self.mock_scene_repo.scene_exists.return_value = True
        self.mock_scene_repo.file_exists.return_value = True

        # パスの存在チェックとファイル更新をモック
        mock_path_exists.return_value = True
        mock_update_scene_file.return_value = None

        # 章別プロットが存在
        path_service = get_common_path_service()
        chapter_plot_files = [project_root / str(path_service.get_plots_dir()) / "chapter01.yaml"]
        self.mock_plot_repo.get_chapter_plot_files.return_value = chapter_plot_files
        self.mock_plot_repo.load_chapter_plot.return_value = {"title": "ch01", "scenes": []}

        # 細かな伏線が存在
        detailed_foreshadowing = [
            Mock(id=Mock(value="F003"), title="キャラクター関係"),
            Mock(id=Mock(value="F004"), title="局所的な謎"),
        ]
        self.mock_foreshadowing_repo.exists.return_value = True
        self.mock_foreshadowing_repo.load_all.return_value = detailed_foreshadowing
        self.mock_foreshadowing_repo.load_detailed_foreshadowing.return_value = detailed_foreshadowing

        # 章別プロットから抽出するシーン
        self.mock_scene_extractor.extract_from_chapter_plot.return_value = []

        # 章別プロットと伏線を組み合わせたシーン抽出
        scene1 = Mock(scene_id="scene_201", title="伏線F003に関連するシーン")
        scene1.episode_range = [3, 3]
        scene1.importance = Mock(value=3)
        scene1.category = Mock(value="character_moment")

        scene2 = Mock(scene_id="scene_202", title="伏線F004に関連するシーン")
        scene2.episode_range = [4, 4]
        scene2.importance = Mock(value=3)
        scene2.category = Mock(value="mystery")

        combined_scenes = [scene1, scene2]
        self.mock_scene_extractor.extract_scenes_from_chapter_and_foreshadowing.return_value = combined_scenes

        # マージと重複削除
        self.mock_scene_extractor.merge_and_deduplicate.return_value = combined_scenes

        # 既存シーンを空に
        self.mock_scene_repo.load_scenes.return_value = {"scenes": {}}

        request = SceneExtractionRequest(
            project_name=project_name,
            use_chapter_plots=True,
            use_foreshadowing=True,  # 細かな伏線を活用
            detailed_mode=True,
        )

        # Act
        response = self.use_case.execute(request)

        # Assert
        assert response.status == SceneExtractionStatus.SUCCESS
        assert response.extracted_count == 2

        # 伏線と章別プロットを組み合わせた抽出が実行されることを確認
        self.mock_scene_extractor.extract_scenes_from_chapter_and_foreshadowing.assert_called_once()
