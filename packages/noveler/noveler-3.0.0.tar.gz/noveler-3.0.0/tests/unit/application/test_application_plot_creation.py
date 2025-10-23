#!/usr/bin/env python3
"""プロット作成アプリケーション層テスト

PlotCreationOrchestratorのテスト


仕様書: SPEC-UNIT-TEST
"""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# スクリプトのルートディレクトリをパスに追加
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from noveler.application.use_cases.plot_creation_orchestrator import (
    PlotCreationOrchestrator,
    PlotCreationRequest,
    PlotCreationResponse,
)
from noveler.domain.value_objects.workflow_stage_type import WorkflowStageType


class TestPlotCreationRequest(unittest.TestCase):
    """プロット作成リクエストのテスト"""

    @pytest.mark.spec("SPEC-APPLICATION_PLOT_CREATION-CREATE_REQUEST")
    def test_create_request(self) -> None:
        """プロット作成リクエストを作成できる"""
        request = PlotCreationRequest(
            stage_type=WorkflowStageType.MASTER_PLOT,
            project_root=Path("/test"),
            parameters={"key": "value"},
        )

        assert request.stage_type == WorkflowStageType.MASTER_PLOT
        assert request.project_root == Path("/test")
        assert request.parameters == {"key": "value"}
        assert request.auto_confirm

    @pytest.mark.spec("SPEC-APPLICATION_PLOT_CREATION-DISABLE_AUTO_VERIFIC")
    def test_disable_auto_verification(self) -> None:
        """自動確認を無効にできる"""
        request = PlotCreationRequest(
            stage_type=WorkflowStageType.CHAPTER_PLOT,
            project_root=Path("/test"),
            parameters={},
            auto_confirm=False,
        )

        assert not request.auto_confirm


class TestPlotCreationResponse(unittest.TestCase):
    """プロット作成レスポンスのテスト"""

    @pytest.mark.spec("SPEC-APPLICATION_PLOT_CREATION-CREATE_SUCCESS_RESPO")
    def test_create_success_response(self) -> None:
        """成功レスポンスを作成できる"""
        response = PlotCreationResponse(
            success=True,
            created_files=[Path("/test/file.yaml")],
        )

        assert response.success
        assert response.created_files == [Path("/test/file.yaml")]
        assert response.error_message == ""
        assert response.conflict_files == []
        assert response.messages == []

    @pytest.mark.spec("SPEC-APPLICATION_PLOT_CREATION-CREATE_FAILURE_RESPO")
    def test_create_failure_response(self) -> None:
        """失敗レスポンスを作成できる"""
        response = PlotCreationResponse(
            success=False,
            created_files=[],
            error_message="エラーが発生しました",
        )

        assert not response.success
        assert response.created_files == []
        assert response.error_message == "エラーが発生しました"
        assert response.messages == []


class TestPlotCreationOrchestrator(unittest.TestCase):
    """プロット作成オーケストレーターのテスト"""

    def setUp(self) -> None:
        """テスト前準備"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.templates_dir = self.temp_dir / "templates"
        self.project_root = self.temp_dir / "project"

        # ディレクトリを作成
        self.templates_dir.mkdir(parents=True)
        self.project_root.mkdir(parents=True)

        self.orchestrator = PlotCreationOrchestrator(self.templates_dir)

    def tearDown(self) -> None:
        """テスト後クリーンアップ"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @patch("noveler.application.use_cases.plot_creation_orchestrator.PlotCreationService")
    @patch("noveler.application.use_cases.plot_creation_orchestrator.FileSystemProjectFileRepository")
    @patch("noveler.application.use_cases.plot_creation_orchestrator.YamlTemplateRepository")
    def test_execute_plot_creation(
        self, _mock_template_repo: object, _mock_file_repo: object, mock_service: object
    ) -> None:
        """プロット作成を実行できる"""
        # モックの設定
        mock_domain_result = Mock()
        mock_domain_result.success = True
        mock_domain_result.created_files = [Path("/test/output.yaml")]
        mock_domain_result.error_message = ""
        mock_domain_result.conflict_files = []
        mock_domain_result.messages = []

        mock_service_instance = Mock()
        mock_service_instance.execute_plot_creation.return_value = mock_domain_result
        mock_service.return_value = mock_service_instance

        # リクエスト作成
        request = PlotCreationRequest(
            stage_type=WorkflowStageType.MASTER_PLOT,
            project_root=self.project_root,
            parameters={"test": "data"},
        )

        # 実行
        response = self.orchestrator.execute_plot_creation(request)

        # 検証
        assert response.success
        assert response.created_files == [Path("/test/output.yaml")]
        assert response.error_message == ""
        assert response.messages == []

        # ドメインサービスが正しく呼ばれたか確認
        mock_service_instance.execute_plot_creation.assert_called_once()
        call_args = mock_service_instance.execute_plot_creation.call_args
        assert call_args[0][0].stage_type == WorkflowStageType.MASTER_PLOT
        assert call_args[0][0].parameters == {"test": "data"}

    @patch("noveler.application.use_cases.plot_creation_orchestrator.PlotCreationService")
    @patch("noveler.application.use_cases.plot_creation_orchestrator.FileSystemProjectFileRepository")
    @patch("noveler.application.use_cases.plot_creation_orchestrator.YamlTemplateRepository")
    def test_handles_domain_service_errors_properly(
        self, _mock_template_repo: object, _mock_file_repo: object, mock_service: object
    ) -> None:
        """ドメインサービスエラーを適切に処理する"""
        # モックの設定
        mock_domain_result = Mock()
        mock_domain_result.success = False
        mock_domain_result.created_files = []
        mock_domain_result.error_message = "ドメインエラー"
        mock_domain_result.conflict_files = []
        mock_domain_result.messages = []

        mock_service_instance = Mock()
        mock_service_instance.execute_plot_creation.return_value = mock_domain_result
        mock_service.return_value = mock_service_instance

        # リクエスト作成
        request = PlotCreationRequest(
            stage_type=WorkflowStageType.MASTER_PLOT,
            project_root=self.project_root,
            parameters={},
        )

        # 実行
        response = self.orchestrator.execute_plot_creation(request)

        # 検証
        assert not response.success
        assert response.created_files == []
        assert response.error_message == "ドメインエラー"
        assert response.messages == []

    @patch("noveler.application.use_cases.plot_creation_orchestrator.PlotCreationService")
    def test_handles_exceptions_on_error(self, mock_service: object) -> None:
        """例外発生時のエラーハンドリング"""
        # モックでエラーを発生させる
        mock_service.side_effect = RuntimeError("予期しないエラー")

        # リクエスト作成
        request = PlotCreationRequest(
            stage_type=WorkflowStageType.MASTER_PLOT,
            project_root=self.project_root,
            parameters={},
        )

        # 実行
        response = self.orchestrator.execute_plot_creation(request)

        # 検証
        assert not response.success
        assert response.created_files == []
        assert response.error_message.startswith("アプリケーション層エラー:")

    @patch("noveler.application.use_cases.plot_creation_orchestrator.PlotCreationService")
    @patch("noveler.application.use_cases.plot_creation_orchestrator.FileSystemProjectFileRepository")
    @patch("noveler.application.use_cases.plot_creation_orchestrator.YamlTemplateRepository")
    def test_all_structure_creation_convenience_method(
        self, _mock_template_repo: object, _mock_file_repo: object, mock_service: object
    ) -> None:
        """全体構成作成の便利メソッド"""
        # モックの設定
        mock_domain_result = Mock()
        mock_domain_result.success = True
        mock_domain_result.created_files = [Path("/test/master.yaml")]
        mock_domain_result.error_message = ""
        mock_domain_result.conflict_files = []

        mock_service_instance = Mock()
        mock_service_instance.execute_plot_creation.return_value = mock_domain_result
        mock_service.return_value = mock_service_instance

        # 実行 - B30品質作業指示書遵守: 必須引数追加
        response = self.orchestrator.create_master_plot(self.project_root, auto_confirm=True)

        # 検証
        assert response.success

        # ドメインサービスが正しいパラメータで呼ばれたか確認
        call_args = mock_service_instance.execute_plot_creation.call_args
        task = call_args[0][0]
        assert task.stage_type == WorkflowStageType.MASTER_PLOT
        assert task.parameters == {}

    @patch("noveler.application.use_cases.plot_creation_orchestrator.PlotCreationService")
    @patch("noveler.application.use_cases.plot_creation_orchestrator.FileSystemProjectFileRepository")
    @patch("noveler.application.use_cases.plot_creation_orchestrator.YamlTemplateRepository")
    def test_chapter_plot_creation_convenience_method(
        self, _mock_template_repo: object, _mock_file_repo: object, mock_service: object
    ) -> None:
        """章別プロット作成の便利メソッド"""
        # モックの設定
        mock_domain_result = Mock()
        mock_domain_result.success = True
        mock_domain_result.created_files = [Path("/test/chapter_1.yaml")]
        mock_domain_result.error_message = ""
        mock_domain_result.conflict_files = []

        mock_service_instance = Mock()
        mock_service_instance.execute_plot_creation.return_value = mock_domain_result
        mock_service.return_value = mock_service_instance

        # 実行
        response = self.orchestrator.create_chapter_plot(self.project_root, chapter=1)

        # 検証
        assert response.success

        # ドメインサービスが正しいパラメータで呼ばれたか確認
        call_args = mock_service_instance.execute_plot_creation.call_args
        task = call_args[0][0]
        assert task.stage_type == WorkflowStageType.CHAPTER_PLOT
        # B30品質作業指示書遵守: 実装と一致する期待値修正
        assert task.parameters == {"chapter_number": 1}

    @patch("noveler.application.use_cases.plot_creation_orchestrator.PlotCreationService")
    @patch("noveler.application.use_cases.plot_creation_orchestrator.FileSystemProjectFileRepository")
    @patch("noveler.application.use_cases.plot_creation_orchestrator.YamlTemplateRepository")
    def test_episode_count_plot_creation_convenience_method(
        self, _mock_template_repo: object, _mock_file_repo: object, mock_service: object
    ) -> None:
        """話数別プロット作成の便利メソッド"""
        # モックの設定
        mock_domain_result = Mock()
        mock_domain_result.success = True
        mock_domain_result.created_files = [Path("/test/episode_1.yaml")]
        mock_domain_result.error_message = ""
        mock_domain_result.conflict_files = []

        mock_service_instance = Mock()
        mock_service_instance.execute_plot_creation.return_value = mock_domain_result
        mock_service.return_value = mock_service_instance

        # 実行
        response = self.orchestrator.create_episode_plot(self.project_root, episode=1, chapter=1)

        # 検証
        assert response.success

        # ドメインサービスが正しいパラメータで呼ばれたか確認
        call_args = mock_service_instance.execute_plot_creation.call_args
        task = call_args[0][0]
        assert task.stage_type == WorkflowStageType.EPISODE_PLOT
        assert task.parameters == {"episode": 1, "chapter": 1}


if __name__ == "__main__":
    unittest.main()
