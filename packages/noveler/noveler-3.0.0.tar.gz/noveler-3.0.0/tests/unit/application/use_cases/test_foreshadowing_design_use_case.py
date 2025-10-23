"""
伏線設計ユースケースのテスト(TDD RED段階)
DDD + TDD実装チェックリストに従って作成
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from noveler.application.use_cases.foreshadowing_design_use_case import (
    ForeshadowingDesignRequest,
    ForeshadowingDesignStatus,
    ForeshadowingDesignUseCase,
)
from noveler.domain.services.foreshadowing_extractor import ForeshadowingExtractor
from noveler.domain.value_objects.foreshadowing import (
    Foreshadowing,
    ForeshadowingCategory,
    ForeshadowingId,
    ForeshadowingStatus,
    PlantingInfo,
    ResolutionInfo,
)
from noveler.presentation.shared.shared_utilities import get_common_path_service


class TestForeshadowingDesignUseCase:
    """伏線設計ユースケースのテスト"""

    def setup_method(self) -> None:
        """テストセットアップ"""
        self.mock_project_repo = Mock()
        self.mock_foreshadowing_repo = Mock()
        self.mock_plot_repo = Mock()
        self.mock_extractor = Mock(spec=ForeshadowingExtractor)

        self.use_case = ForeshadowingDesignUseCase(
            project_repository=self.mock_project_repo,
            foreshadowing_repository=self.mock_foreshadowing_repo,
            plot_repository=self.mock_plot_repo,
            foreshadowing_extractor=self.mock_extractor,
        )

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_all_from_extractsave(self) -> None:
        """全体構成.yamlから伏線を抽出し、伏線管理.yamlを作成する"""
        # Arrange
        project_name = "テスト小説"
        project_root = Path("/test/project")

        # プロジェクトが存在する
        self.mock_project_repo.exists.return_value = True
        self.mock_project_repo.get_project_root.return_value = project_root

        # 全体構成.yamlが存在する
        master_plot_data = {
            "metadata": {"title": "テスト小説", "total_chapters": 3},
            "story_structure": {
                "opening": {"description": "主人公が記憶を失った状態で目覚める"},
                "development": {"major_revelations": ["主人公の正体が明かされる", "黒幕の存在が示唆される"]},
                "climax": {"description": "すべての謎が明かされ、主人公が真実と向き合う"},
            },
            "themes": {"main": "アイデンティティの探求", "sub": ["記憶と自己", "真実の代償"]},
        }
        self.mock_plot_repo.load_master_plot.return_value = master_plot_data

        # 伏線抽出サービスが伏線を抽出する
        extracted_foreshadowings = [
            Foreshadowing(
                id=ForeshadowingId("F001"),
                title="失われた記憶",
                category=ForeshadowingCategory.MYSTERY,
                description="主人公の記憶喪失の真相",
                importance=5,
                planting=PlantingInfo(
                    episode="第001話",
                    chapter=1,
                    method="冒頭での描写",
                    content="主人公が何も思い出せない状態で目覚める",
                ),
                resolution=ResolutionInfo(
                    episode="第025話", chapter=3, method="衝撃的な真実の開示", impact="主人公の本当の正体が明かされる"
                ),
                status=ForeshadowingStatus.PLANNED,
            ),
            Foreshadowing(
                id=ForeshadowingId("F002"),
                title="黒幕の影",
                category=ForeshadowingCategory.MAIN,
                description="物語全体を操る黒幕の存在",
                importance=5,
                planting=PlantingInfo(
                    episode="第005話",
                    chapter=1,
                    method="不自然な出来事の連続",
                    content="偶然にしては出来すぎた事件が続く",
                ),
                resolution=ResolutionInfo(
                    episode="第030話",
                    chapter=3,
                    method="黒幕の正体判明",
                    impact="すべての事件の裏に一人の人物がいたことが判明",
                ),
                status=ForeshadowingStatus.PLANNED,
            ),
        ]
        self.mock_extractor.extract_from_master_plot.return_value = extracted_foreshadowings

        # 伏線管理.yamlが存在しない場合(新規作成)
        self.mock_foreshadowing_repo.exists.return_value = False

        # リクエスト作成
        request = ForeshadowingDesignRequest(
            project_name=project_name, source="master_plot", auto_extract=True, interactive=False
        )

        # Act
        response = self.use_case.execute(request)

        # Assert
        assert response.status == ForeshadowingDesignStatus.SUCCESS
        assert response.created_count == 2
        path_service = get_common_path_service()
        assert response.foreshadowing_file == project_root / str(path_service.get_management_dir()) / "伏線管理.yaml"
        assert "F001: 失われた記憶" in response.foreshadowing_summary
        assert "F002: 黒幕の影" in response.foreshadowing_summary

        # リポジトリのメソッドが適切に呼ばれたか確認
        self.mock_plot_repo.load_master_plot.assert_called_once_with(project_root)
        self.mock_extractor.extract_from_master_plot.assert_called_once_with(master_plot_data)
        # save_allメソッドが呼ばれたことを確認
        self.mock_foreshadowing_repo.save_all.assert_called_once()
        # 保存された伏線の数を確認
        saved_foreshadowings = self.mock_foreshadowing_repo.save_all.call_args[0][0]
        assert len(saved_foreshadowings) == 2

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_unnamed(self) -> None:
        """プロジェクトが存在しない場合はエラーを返す"""
        # Arrange
        self.mock_project_repo.exists.return_value = False

        request = ForeshadowingDesignRequest(
            project_name="存在しないプロジェクト", source="master_plot", auto_extract=True, interactive=False
        )

        # Act
        response = self.use_case.execute(request)

        # Assert
        assert response.status == ForeshadowingDesignStatus.PROJECT_NOT_FOUND
        assert response.created_count == 0
        assert "が見つかりません" in response.message

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_all(self) -> None:
        """全体構成.yamlが存在しない場合はエラーを返す"""
        # Arrange
        self.mock_project_repo.exists.return_value = True
        self.mock_project_repo.get_project_root.return_value = Path("/test/project")
        self.mock_plot_repo.load_master_plot.side_effect = FileNotFoundError()

        request = ForeshadowingDesignRequest(
            project_name="テスト小説", source="master_plot", auto_extract=True, interactive=False
        )

        # Act
        response = self.use_case.execute(request)

        # Assert
        assert response.status == ForeshadowingDesignStatus.MASTER_PLOT_NOT_FOUND
        assert response.created_count == 0
        assert "全体構成.yamlが見つかりません" in response.message

    @pytest.mark.spec("SPEC-PLOT-001")
    @pytest.mark.spec("SPEC-PLOT-001")
    def test_file_new(self) -> None:
        """既存の伏線管理.yamlがある場合は、新しい伏線を追加"""
        # Arrange
        project_root = Path("/test/project")
        self.mock_project_repo.exists.return_value = True
        self.mock_project_repo.get_project_root.return_value = project_root

        # 既存の伏線
        existing_foreshadowings = [
            Foreshadowing(
                id=ForeshadowingId("F001"),
                title="既存の伏線",
                category=ForeshadowingCategory.CHARACTER,
                description="既に設定済みの伏線",
                importance=3,
                planting=PlantingInfo(
                    episode="第002話", chapter=1, method="キャラクターの台詞", content="意味深な発言"
                ),
                resolution=ResolutionInfo(
                    episode="第020話", chapter=2, method="真相の告白", impact="キャラクターの本心が明らかに"
                ),
                status=ForeshadowingStatus.PLANTED,
            )
        ]
        self.mock_foreshadowing_repo.load_all.return_value = existing_foreshadowings

        # 新しく抽出される伏線
        new_foreshadowing = Foreshadowing(
            id=ForeshadowingId("F002"),
            title="新しい伏線",
            category=ForeshadowingCategory.WORLDBUILDING,
            description="全体構成から新たに発見された伏線",
            importance=4,
            planting=PlantingInfo(episode="第003話", chapter=1, method="世界観の描写", content="違和感のある設定"),
            resolution=ResolutionInfo(
                episode="第028話", chapter=3, method="世界の真実", impact="世界観の根幹が覆される"
            ),
            status=ForeshadowingStatus.PLANNED,
        )

        master_plot_data = {"dummy": "data"}
        self.mock_plot_repo.load_master_plot.return_value = master_plot_data
        self.mock_extractor.extract_from_master_plot.return_value = [new_foreshadowing]

        request = ForeshadowingDesignRequest(
            project_name="テスト小説", source="master_plot", auto_extract=True, interactive=False, merge_existing=True
        )

        # Act
        response = self.use_case.execute(request)

        # Assert
        assert response.status == ForeshadowingDesignStatus.SUCCESS
        assert response.created_count == 1  # 新規追加のみカウント
        assert response.existing_count == 1
        assert "既存: 1件, 新規: 1件" in response.message

        # 既存と新規の伏線が両方保存されることを確認
        saved_foreshadowings = self.mock_foreshadowing_repo.save_all.call_args[0][0]
        assert len(saved_foreshadowings) == 2
        assert any(f.id.value == "F001" for f in saved_foreshadowings)
        assert any(f.id.value == "F002" for f in saved_foreshadowings)
