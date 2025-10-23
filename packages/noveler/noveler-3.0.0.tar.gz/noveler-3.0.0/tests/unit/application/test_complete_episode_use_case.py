#!/usr/bin/env python3
"""執筆完了ユースケースのテスト

TDD原則:アプリケーション層のテスト
"""

from datetime import datetime, timezone
import tempfile
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from noveler.application.use_cases.complete_episode_use_case import (
    CompleteEpisodeDependencies,
    CompleteEpisodeRequest,
    CompleteEpisodeResponse,
    CompleteEpisodeUseCase,
)
from noveler.domain.repositories.episode_completion_repository import (
    CompletionTransactionManager,
)
from noveler.domain.value_objects.project_time import ProjectDateTime, ProjectTimezone


class TestCompleteEpisodeRequest:
    """完了リクエストのテスト"""

    @pytest.mark.spec("SPEC-EPISODE-013")
    @pytest.mark.spec("SPEC-EPISODE-012")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_valid_request(self) -> None:
        """有効なリクエスト作成"""
        request = CompleteEpisodeRequest(
            project_name="テストプロジェクト",
            project_path=Path("/test/project"),
            episode_number=1,
            quality_score=Decimal("85.5"),
            plot_data={"title": "テストエピソード"},
        )

        assert request.project_name == "テストプロジェクト"
        assert request.episode_number == 1
        assert request.quality_score == Decimal("85.5")

    @pytest.mark.spec("SPEC-EPISODE-013")
    @pytest.mark.spec("SPEC-EPISODE-012")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_request_validation(self) -> None:
        """リクエストバリデーション"""
        # プロジェクト名が空
        with pytest.raises(ValueError, match="Project name cannot be empty"):
            CompleteEpisodeRequest(
                project_name="", project_path=Path("/test"), episode_number=1, quality_score=Decimal("80")
            )

        # エピソード番号が負
        with pytest.raises(ValueError, match="Episode number must be positive"):
            CompleteEpisodeRequest(
                project_name="test", project_path=Path("/test"), episode_number=-1, quality_score=Decimal("80")
            )


class TestCompleteEpisodeUseCase:
    """執筆完了ユースケースのテスト"""

    def setup_method(self) -> None:
        """テストセットアップ"""
        self.episode_repo = Mock()
        self.foreshadowing_repo = Mock()
        self.growth_repo = Mock()
        self.scene_repo = Mock()
        self.history_repo = Mock()
        self.chapter_plot_repo = Mock()
        self.transaction_manager = Mock(spec=CompletionTransactionManager)

        # from noveler.application.use_cases.complete_episode_use_case import CompleteEpisodeDependencies  # Moved to top-level

        dependencies = CompleteEpisodeDependencies(
            episode_management_repository=self.episode_repo,
            foreshadowing_repository=self.foreshadowing_repo,
            character_growth_repository=self.growth_repo,
            important_scene_repository=self.scene_repo,
            revision_history_repository=self.history_repo,
            chapter_plot_repository=self.chapter_plot_repo,
            transaction_manager=self.transaction_manager,
        )

        self.use_case = CompleteEpisodeUseCase(dependencies)

    def create_sample_request(self) -> CompleteEpisodeRequest:
        """サンプルリクエスト作成"""
        plot_data = {
            "title": "テストエピソード",
            "character_growth": [
                {"character": "主人公", "type": "realization", "description": "真実に気づく", "importance": "high"}
            ],
            "important_scenes": [
                {
                    "scene_id": "climax",
                    "type": "turning_point",
                    "description": "クライマックス",
                    "emotion_level": "high",
                }
            ],
            "foreshadowing": {"planted": ["F001"], "resolved": ["F002"]},
        }

        return CompleteEpisodeRequest(
            project_name="テストプロジェクト",
            project_path=Path(tempfile.gettempdir()) / "noveler_test_project",
            episode_number=5,
            quality_score=Decimal("88.5"),
            plot_data=plot_data,
        )

    @pytest.mark.spec("SPEC-EPISODE-013")
    @pytest.mark.spec("SPEC-EPISODE-012")
    @pytest.mark.spec("SPEC-EPISODE-005")
    @patch("noveler.application.use_cases.complete_episode_use_case.Path")
    @patch("noveler.domain.value_objects.project_time.project_now")
    def test_successful_completion(self, mock_project_now: object, mock_path: object) -> None:
        """正常な執筆完了処理"""
        # Arrange
        mock_project_now.return_value = ProjectDateTime(
            datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc), ProjectTimezone.jst()
        )
        mock_path.return_value.read_text.return_value = "テスト原稿" * 1000

        # テスト用ディレクトリを先に作成
        temp_dir = Path(tempfile.mkdtemp())

        sample_request = self.create_sample_request()
        request = CompleteEpisodeRequest(
            project_name=sample_request.project_name,
            project_path=temp_dir,  # temp_dirを使用
            episode_number=sample_request.episode_number,
            quality_score=sample_request.quality_score,
            plot_data=sample_request.plot_data,
        )

        # トランザクション設定
        mock_transaction = Mock()
        mock_transaction.__enter__ = Mock(return_value=mock_transaction)
        mock_transaction.__exit__ = Mock(return_value=False)
        self.transaction_manager.begin_transaction.return_value = mock_transaction

        manuscript_file = temp_dir / "episode005.txt"
        manuscript_file.write_text("あ" * 5000, encoding="utf-8")

        mock_path_service = Mock()
        mock_path_service.get_manuscript_path.return_value = manuscript_file
        self.use_case.get_path_service = Mock(return_value=mock_path_service)
        assert isinstance(self.use_case.get_path_service, Mock)
        self.use_case._service_locator.get_path_service = Mock(return_value=mock_path_service)

        # Act
        response = self.use_case.execute(request)

        # Assert
        assert response.success is True
        assert response.error_message is None
        assert len(response.updated_files) > 0
        assert response.summary is not None

        # リポジトリ呼び出し確認
        self.transaction_manager.begin_transaction.assert_called_once()
        mock_transaction.commit.assert_called_once()

        # 章別プロット更新が呼ばれていることを確認
        mock_transaction.update_chapter_plot.assert_called_once()
        chapter_call = mock_transaction.update_chapter_plot.call_args
        assert chapter_call[0][0] == "chapter01"  # エピソード5はchapter01
        assert chapter_call[0][1] == 5
        assert "status" in chapter_call[0][2]
        assert chapter_call[0][2]["status"] == "執筆済み"

    @pytest.mark.spec("SPEC-EPISODE-013")
    @pytest.mark.spec("SPEC-EPISODE-012")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_transaction_rollback_on_error(self) -> None:
        """エラー時のトランザクションロールバック"""
        # Arrange
        request = self.create_sample_request()

        mock_transaction = Mock()
        mock_transaction.__enter__ = Mock(return_value=mock_transaction)
        mock_transaction.__exit__ = Mock(return_value=False)
        self.transaction_manager.begin_transaction.return_value = mock_transaction

        # エラーを発生させる
        mock_transaction.update_episode_status.side_effect = Exception("Update failed")

        # Act
        response = self.use_case.execute(request)

        # Assert
        assert response.success is False
        assert "Update failed" in response.error_message
        mock_transaction.rollback.assert_called_once()

    @pytest.mark.spec("SPEC-EPISODE-013")
    @pytest.mark.spec("SPEC-EPISODE-012")
    @pytest.mark.spec("SPEC-EPISODE-005")
    @patch("pathlib.Path.glob")
    @patch("pathlib.Path.read_text")
    def test_word_count_calculation(self, mock_read_text: object, mock_glob: object) -> None:
        """文字数計算のテスト"""
        # Arrange
        # 原稿ファイルのモック
        mock_file = Mock()
        mock_file.read_text.return_value = "あ" * 5000
        mock_glob.return_value = [mock_file]
        mock_read_text.return_value = "あ" * 5000  # 5000文字

        request = self.create_sample_request()

        mock_transaction = Mock()
        mock_transaction.__enter__ = Mock(return_value=mock_transaction)
        mock_transaction.__exit__ = Mock(return_value=False)
        self.transaction_manager.begin_transaction.return_value = mock_transaction

        # path serviceのモック設定（word count計算に必要）
        mock_manuscript_file = Mock()
        mock_manuscript_file.read_text.return_value = "あ" * 5000

        mock_path_service = Mock()
        mock_path_service.get_manuscript_path.return_value = mock_manuscript_file
        self.use_case.get_path_service = Mock(return_value=mock_path_service)

        # Act
        response = self.use_case.execute(request)

        # Assert
        assert response.success is True
        # 文字数が更新されていることを確認
        mock_transaction.update_episode_status.assert_called()
        call_args = mock_transaction.update_episode_status.call_args
        # metadataの中にword_countがある
        assert call_args[1]["metadata"]["word_count"] == 5000

    @pytest.mark.spec("SPEC-EPISODE-013")
    @pytest.mark.spec("SPEC-EPISODE-012")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_plot_data_extraction(self) -> None:
        """プロットデータからの情報抽出"""
        # Arrange
        request = self.create_sample_request()

        mock_transaction = Mock()
        mock_transaction.__enter__ = Mock(return_value=mock_transaction)
        mock_transaction.__exit__ = Mock(return_value=False)
        self.transaction_manager.begin_transaction.return_value = mock_transaction

        # Act
        response = self.use_case.execute(request)

        # Assert
        assert response.success is True

        # キャラクター成長が追加されている
        mock_transaction.add_character_growth.assert_called()
        growth_call = mock_transaction.add_character_growth.call_args
        assert growth_call[0][0] == "主人公"

        # 重要シーンが追加されている
        mock_transaction.add_important_scene.assert_called()
        scene_call = mock_transaction.add_important_scene.call_args
        assert scene_call[0][0] == 5  # episode_number

        # 伏線が更新されている
        mock_transaction.plant_foreshadowing.assert_called_with("F001", 5)
        mock_transaction.resolve_foreshadowing.assert_called_with("F002", 5)

    @pytest.mark.spec("SPEC-EPISODE-013")
    @pytest.mark.spec("SPEC-EPISODE-012")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_response_summary_generation(self) -> None:
        """レスポンスサマリーの生成"""
        # Arrange
        request = self.create_sample_request()

        mock_transaction = Mock()
        mock_transaction.__enter__ = Mock(return_value=mock_transaction)
        mock_transaction.__exit__ = Mock(return_value=False)
        self.transaction_manager.begin_transaction.return_value = mock_transaction

        # Act
        response = self.use_case.execute(request)

        # Assert
        assert response.success is True
        assert response.summary is not None

        summary = response.summary
        assert summary["episode_number"] == 5
        assert summary["quality_score"] == 88.5
        assert "character_growth_count" in summary
        assert "important_scenes_count" in summary
        assert "foreshadowing_planted" in summary
        assert "foreshadowing_resolved" in summary

    @pytest.mark.spec("SPEC-EPISODE-013")
    @pytest.mark.spec("SPEC-EPISODE-012")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_low_quality_warning(self) -> None:
        """低品質警告のテスト"""
        # Arrange
        request = CompleteEpisodeRequest(
            project_name="テスト", project_path=Path("/test"), episode_number=1, quality_score=Decimal("70")
        )  # 低品質

        mock_transaction = Mock()
        mock_transaction.__enter__ = Mock(return_value=mock_transaction)
        mock_transaction.__exit__ = Mock(return_value=False)
        self.transaction_manager.begin_transaction.return_value = mock_transaction

        # Act
        response = self.use_case.execute(request)

        # Assert
        assert response.success is True
        assert len(response.warnings) > 0
        assert any("quality" in w.lower() for w in response.warnings)


class TestCompleteEpisodeResponse:
    """レスポンスのテスト"""

    @pytest.mark.spec("SPEC-EPISODE-013")
    @pytest.mark.spec("SPEC-EPISODE-012")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_success_response(self) -> None:
        """成功レスポンス"""
        response = CompleteEpisodeResponse.success(
            updated_files=["話数管理.yaml", "伏線管理.yaml"], summary={"episode_number": 1}
        )

        assert response.success is True
        assert response.error_message is None
        assert len(response.updated_files) == 2
        assert response.summary["episode_number"] == 1

    @pytest.mark.spec("SPEC-EPISODE-013")
    @pytest.mark.spec("SPEC-EPISODE-012")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_failure_response(self) -> None:
        """失敗レスポンス"""
        response = CompleteEpisodeResponse.failure("Error occurred")

        assert response.success is False
        assert response.error_message == "Error occurred"
        assert response.updated_files == []
        assert response.summary == {}
