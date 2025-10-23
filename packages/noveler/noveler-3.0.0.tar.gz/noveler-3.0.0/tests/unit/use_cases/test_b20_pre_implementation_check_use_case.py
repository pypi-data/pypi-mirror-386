#!/usr/bin/env python3
"""B20PreImplementationCheckUseCaseの単体テスト

8ステップの事前チェック処理を完全にテストする包括的テストスイート
"""

from unittest.mock import MagicMock, patch
from pathlib import Path
from types import SimpleNamespace
import pytest

from noveler.application.use_cases.b20_pre_implementation_check_use_case import (
    B20PreImplementationCheckUseCase,
    B20PreImplementationCheckRequest,
    B20PreImplementationCheckResponse,
)
from noveler.domain.interfaces.logger_service import ILoggerService
from noveler.domain.protocols.unit_of_work_protocol import IUnitOfWorkProtocol
from noveler.domain.interfaces.console_service_protocol import IConsoleService


@pytest.fixture
def mock_logger_service():
    """モックロガーサービス"""
    logger = MagicMock(spec=ILoggerService)
    logger.info = MagicMock()
    logger.error = MagicMock()
    logger.warning = MagicMock()
    logger.exception = MagicMock()
    return logger


@pytest.fixture
def mock_unit_of_work():
    """モックユニットオブワーク"""
    return MagicMock(spec=IUnitOfWorkProtocol)


@pytest.fixture
def mock_console_service():
    """モックコンソールサービス"""
    return MagicMock(spec=IConsoleService)


@pytest.fixture
def mock_path_service(tmp_path):
    """モックパスサービス"""
    path_service = MagicMock()
    path_service.project_root = tmp_path
    path_service.get_management_dir.return_value = tmp_path / "management"
    path_service.get_spec_path.return_value = tmp_path / "specs"
    return path_service


@pytest.fixture
def mock_check_service():
    """モックチェックサービス"""
    service = MagicMock()
    service.execute_pre_implementation_check.return_value = SimpleNamespace(
        is_implementation_allowed=True,
    )
    return service


@pytest.fixture
def mock_codemap_update_use_case():
    """モックCODEMAPアップデートユースケース"""
    mock_use_case = MagicMock()
    mock_use_case.return_value = {"status": "available"}
    return mock_use_case


@pytest.fixture
def use_case(
    mock_logger_service,
    mock_unit_of_work,
    mock_console_service,
    mock_path_service,
    mock_check_service,
    mock_codemap_update_use_case,
):
    """テスト対象のユースケース"""
    return B20PreImplementationCheckUseCase(
        logger_service=mock_logger_service,
        unit_of_work=mock_unit_of_work,
        console_service=mock_console_service,
        path_service=mock_path_service,
        check_service=mock_check_service,
        codemap_update_use_case=mock_codemap_update_use_case,
    )


@pytest.fixture
def basic_request():
    """基本的なリクエスト"""
    return B20PreImplementationCheckRequest(
        feature_name="test_feature",
        target_layer="domain",
        auto_fix_issues=False,
        create_missing_spec=False,
        force_codemap_update=False,
    )


class TestB20PreImplementationCheckUseCase:
    """B20PreImplementationCheckUseCaseのテストクラス"""

    def test_step1_codemap_status_check_success(
        self, use_case, basic_request, mock_codemap_update_use_case
    ):
        """ステップ1: CODEMAPステータスチェック成功テスト"""
        # Arrange
        mock_codemap_update_use_case.return_value = {"status": "available"}

        with patch.object(use_case, "_has_specification_documents", return_value=True):
            # Act
            response = use_case.execute(basic_request)

            # Assert
            assert response.success is True
            assert response.codemap_status["status"] == "available"

    def test_step1_codemap_status_check_failure(
        self, use_case, basic_request
    ):
        """ステップ1: CODEMAPステータスチェック失敗テスト"""
        # Arrange
        use_case.codemap_update_use_case = None

        with patch.object(use_case, "_has_specification_documents", return_value=True):
            # Act
            response = use_case.execute(basic_request)

            # Assert
            assert response.codemap_status["status"] == "unavailable"
            assert "codemap_update_use_case not configured" in response.codemap_status["reason"]

    def test_step2_implementation_permission_allowed(
        self, use_case, basic_request, mock_codemap_update_use_case
    ):
        """ステップ2: 実装許可判定 - 許可テスト"""
        # Arrange
        mock_codemap_update_use_case.return_value = {"status": "available"}

        with patch.object(use_case, "_has_specification_documents", return_value=True):
            # Act
            response = use_case.execute(basic_request)

            # Assert
            assert response.implementation_allowed is True

    def test_step2_implementation_permission_denied_no_spec(
        self, use_case, basic_request
    ):
        """ステップ2: 実装許可判定 - 仕様書なしで拒否テスト"""
        # Arrange
        with patch.object(use_case, "_has_specification_documents", return_value=False):
            # Act
            response = use_case.execute(basic_request)

            # Assert
            assert response.implementation_allowed is False
            assert "仕様書が見つかりません" in str(response.errors)

    def test_step3_progress_status_calculation_with_spec(
        self, use_case, basic_request, mock_codemap_update_use_case
    ):
        """ステップ3: 進捗状況計算 - 仕様書ありテスト"""
        # Arrange
        mock_codemap_update_use_case.return_value = {"status": "available"}

        with patch.object(use_case, "_has_specification_documents", return_value=True), \
             patch.object(use_case, "_has_test_files", return_value=True):
            # Act
            response = use_case.execute(basic_request)

            # Assert
            assert response.current_stage == "implementation_allowed"
            assert response.completion_percentage == 100.0  # 30 + 20 + 50

    def test_step3_progress_status_calculation_no_spec(
        self, use_case, basic_request
    ):
        """ステップ3: 進捗状況計算 - 仕様書なしテスト"""
        # Arrange
        with patch.object(use_case, "_has_specification_documents", return_value=False):
            # Act
            response = use_case.execute(basic_request)

            # Assert
            assert response.current_stage == "specification_required"
            assert response.completion_percentage == 10.0

    def test_step4_next_actions_identification_success(
        self, use_case, basic_request, mock_codemap_update_use_case
    ):
        """ステップ4: 次のアクション特定 - 成功時テスト"""
        # Arrange
        mock_codemap_update_use_case.return_value = {"status": "available"}

        with patch.object(use_case, "_has_specification_documents", return_value=True):
            # Act
            response = use_case.execute(basic_request)

            # Assert
            assert "実装開始可能" in response.next_required_actions

    def test_step4_next_actions_identification_codemap_unavailable(
        self, use_case, basic_request
    ):
        """ステップ4: 次のアクション特定 - CODEMAP利用不可テスト"""
        # Arrange
        use_case.codemap_update_use_case = None

        with patch.object(use_case, "_has_specification_documents", return_value=True):
            # Act
            response = use_case.execute(basic_request)

            # Assert
            assert "CODEMAP.yamlの更新が必要" in response.next_required_actions

    def test_step5_warnings_and_errors_collection(
        self, use_case, basic_request
    ):
        """ステップ5: 警告・エラー収集テスト"""
        # Arrange
        request = B20PreImplementationCheckRequest(
            feature_name="test_feature",
            target_layer="invalid_layer",  # 無効なレイヤー
            auto_fix_issues=False,
            create_missing_spec=False,
            force_codemap_update=False,
        )

        with patch.object(use_case, "_has_specification_documents", return_value=False):
            # Act
            response = use_case.execute(request)

            # Assert
            assert len(response.errors) >= 2  # 仕様書エラー + 無効レイヤーエラー
            assert any("仕様書が見つかりません" in error for error in response.errors)
            assert any("無効なレイヤー" in error for error in response.errors)

    def test_step6_auto_fix_execution_with_spec_creation(
        self, use_case, mock_path_service
    ):
        """ステップ6: 自動修正実行 - 仕様書作成テスト"""
        # Arrange
        request = B20PreImplementationCheckRequest(
            feature_name="test_feature",
            target_layer="domain",
            auto_fix_issues=True,
            create_missing_spec=True,
            force_codemap_update=False,
        )

        specs_dir = mock_path_service.project_root / "specs"
        specs_dir.mkdir(parents=True, exist_ok=True)
        mock_path_service.get_management_dir.return_value = specs_dir
        mock_path_service.get_spec_path.return_value = specs_dir

        with patch.object(use_case, "_has_specification_documents", return_value=False):
            # Act
            response = use_case.execute(request)

            # Assert
            assert response.auto_fix_results is not None
            assert response.auto_fix_results.get("attempted_fixes", 0) > 0

    def test_step7_state_reevaluation_after_auto_fix(
        self, use_case, mock_path_service
    ):
        """ステップ7: 自動修正後の状態再評価テスト"""
        # Arrange
        request = B20PreImplementationCheckRequest(
            feature_name="test_feature",
            target_layer="domain",
            auto_fix_issues=True,
            create_missing_spec=True,
            force_codemap_update=False,
        )

        specs_dir = mock_path_service.project_root / "specs"
        specs_dir.mkdir(parents=True, exist_ok=True)
        mock_path_service.get_management_dir.return_value = specs_dir
        mock_path_service.get_spec_path.return_value = specs_dir

        # 最初は仕様書なし、修正後は仕様書あり
        spec_calls = [False, False, False, True, True, True]
        with patch.object(use_case, "_has_specification_documents", side_effect=spec_calls):
            # Act
            response = use_case.execute(request)

            # Assert - 自動修正により状態が改善されているはず
            assert response.auto_fix_results is not None
            assert response.auto_fix_results.get("successful_fixes", 0) > 0

    def test_step8_codemap_force_update(
        self, use_case, mock_codemap_update_use_case
    ):
        """ステップ8: CODEMAP強制アップデートテスト"""
        # Arrange
        request = B20PreImplementationCheckRequest(
            feature_name="test_feature",
            target_layer="domain",
            auto_fix_issues=False,
            create_missing_spec=False,
            force_codemap_update=True,
        )

        with patch.object(use_case, "_has_specification_documents", return_value=True):
            # Act
            use_case.execute(request)

            # Assert - CODEMAP更新が呼び出されることを確認
            assert mock_codemap_update_use_case.call_count >= 2

    def test_execution_error_handling(
        self, use_case, basic_request, mock_logger_service
    ):
        """実行エラーハンドリングテスト"""
        # Arrange
        with patch.object(use_case, "_check_codemap_status", side_effect=Exception("Test error")):
            # Act
            response = use_case.execute(basic_request)

            # Assert
            assert response.success is False
            assert response.current_stage == "ERROR"
            assert response.completion_percentage == 0.0
            assert "実行エラー" in str(response.errors)
            mock_logger_service.exception.assert_called_once()

    def test_has_specification_documents_with_specs(
        self, use_case, mock_path_service
    ):
        """仕様書存在確認 - 仕様書ありテスト"""
        # Arrange
        specs_dir = mock_path_service.project_root / "specs"
        specs_dir.mkdir(parents=True, exist_ok=True)
        (specs_dir / "test.md").write_text("test spec")
        mock_path_service.get_management_dir.return_value = specs_dir
        mock_path_service.get_spec_path.return_value = specs_dir

        # Act
        result = use_case._has_specification_documents()

        # Assert
        assert result is True

    def test_has_specification_documents_without_specs(
        self, use_case, mock_path_service
    ):
        """仕様書存在確認 - 仕様書なしテスト"""
        # Arrange
        specs_dir = mock_path_service.project_root / "empty_specs"
        specs_dir.mkdir(parents=True, exist_ok=True)
        mock_path_service.get_management_dir.return_value = specs_dir
        mock_path_service.get_spec_path.return_value = specs_dir

        # Act
        result = use_case._has_specification_documents()

        # Assert
        assert result is False

    def test_has_test_files_with_tests(
        self, use_case, mock_path_service
    ):
        """テストファイル存在確認 - テストファイルありテスト"""
        # Arrange
        project_root = mock_path_service.project_root
        tests_dir = project_root / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)
        (tests_dir / "test_example.py").write_text("test content")
        mock_path_service.project_root = project_root

        # Act
        result = use_case._has_test_files()

        # Assert
        assert result is True

    def test_has_test_files_without_tests(
        self, use_case, mock_path_service
    ):
        """テストファイル存在確認 - テストファイルなしテスト"""
        # Arrange
        project_root = mock_path_service.project_root / "project_no_tests"
        project_root.mkdir(parents=True, exist_ok=True)
        mock_path_service.project_root = project_root

        # Act
        result = use_case._has_test_files()

        # Assert
        assert result is False

    def test_create_specification_file_success(
        self, use_case, mock_path_service
    ):
        """仕様書ファイル作成成功テスト"""
        # Arrange
        specs_dir = mock_path_service.project_root / "specs"
        specs_dir.mkdir(parents=True, exist_ok=True)
        mock_path_service.get_management_dir.return_value = specs_dir
        mock_path_service.get_spec_path.return_value = specs_dir

        # Act
        result = use_case._create_specification_file("test_feature")

        # Assert
        assert result["success"] is True
        assert "SPEC-TEST-FEATURE-001.md" in result["file_path"]

    def test_create_specification_file_no_path_service(
        self, mock_logger_service,
        mock_unit_of_work,
        mock_console_service,
        mock_check_service,
        mock_codemap_update_use_case,
    ):
        """仕様書ファイル作成 - PathServiceなしテスト"""
        # Arrange
        use_case = B20PreImplementationCheckUseCase(
            logger_service=mock_logger_service,
            unit_of_work=mock_unit_of_work,
            console_service=mock_console_service,
            path_service=None,  # PathServiceなし
            check_service=mock_check_service,
            codemap_update_use_case=mock_codemap_update_use_case,
        )

        # Act
        result = use_case._create_specification_file("test_feature")

        # Assert
        assert result["success"] is False
        assert "PathServiceが利用できません" in result["error"]

    def test_get_development_stage_guidance(
        self, use_case, mock_codemap_update_use_case
    ):
        """開発段階ガイダンス取得テスト"""
        # Arrange
        mock_codemap_update_use_case.return_value = {"status": "available"}

        with patch.object(use_case, "_has_specification_documents", return_value=True), \
             patch.object(use_case, "_has_test_files", return_value=True):
            # Act
            guidance = use_case.get_development_stage_guidance("test_feature")

            # Assert
            assert guidance["current_stage"] == "implementation_allowed"
            assert guidance["completion_percentage"] == 100.0
            assert guidance["implementation_allowed"] is True
            assert "30分" in guidance["estimated_time"]

    def test_get_development_stage_guidance_error(
        self, use_case
    ):
        """開発段階ガイダンス取得エラーテスト"""
        # Arrange
        with patch.object(use_case, "execute", side_effect=Exception("Test error")):
            # Act
            guidance = use_case.get_development_stage_guidance("test_feature")

            # Assert
            assert guidance["current_stage"] == "analysis_error"
            assert guidance["completion_percentage"] == 0.0
            assert guidance["implementation_allowed"] is False
            assert "不明" in guidance["estimated_time"]

    def test_step_sequence_integration(
        self, use_case, mock_codemap_update_use_case, mock_path_service
    ):
        """8ステップ統合テスト - 全ステップの連携確認"""
        # Arrange
        request = B20PreImplementationCheckRequest(
            feature_name="integration_test",
            target_layer="domain",
            auto_fix_issues=True,
            create_missing_spec=True,
            force_codemap_update=True,
        )

        specs_dir = mock_path_service.project_root / "specs"
        specs_dir.mkdir(parents=True, exist_ok=True)
        mock_path_service.get_management_dir.return_value = specs_dir
        mock_path_service.get_spec_path.return_value = specs_dir
        mock_codemap_update_use_case.return_value = {"status": "available"}

        # 最初は仕様書なし、修正後は仕様書あり
        spec_calls = [False, False, False, True, True, True]
        with patch.object(use_case, "_has_specification_documents", side_effect=spec_calls), \
             patch.object(use_case, "_has_test_files", return_value=True):

            # Act
            response = use_case.execute(request)

            # Assert - 全ステップが正常に実行されていることを確認
            assert response.success is True
            assert response.auto_fix_results is not None
            assert response.auto_fix_results.get("attempted_fixes", 0) > 0
            assert response.implementation_allowed is True
            assert response.current_stage == "implementation_allowed"
            assert response.completion_percentage == 100.0


class TestB20PerformanceAndReliability:
    """B20ユースケースのパフォーマンスと信頼性テスト"""

    def test_execution_time_measurement(
        self, use_case, basic_request, mock_codemap_update_use_case
    ):
        """実行時間計測テスト"""
        # Arrange
        mock_codemap_update_use_case.return_value = {"status": "available"}

        with patch.object(use_case, "_has_specification_documents", return_value=True):
            # Act
            response = use_case.execute(basic_request)

            # Assert
            assert response.execution_time_ms is not None
            assert response.execution_time_ms > 0

    def test_concurrent_execution_safety(
        self, use_case, mock_codemap_update_use_case
    ):
        """並行実行安全性テスト"""
        # Arrange
        request1 = B20PreImplementationCheckRequest(
            feature_name="concurrent_test_1",
            target_layer="domain",
            auto_fix_issues=False,
            create_missing_spec=False,
        )
        request2 = B20PreImplementationCheckRequest(
            feature_name="concurrent_test_2",
            target_layer="application",
            auto_fix_issues=False,
            create_missing_spec=False,
        )

        mock_codemap_update_use_case.return_value = {"status": "available"}

        with patch.object(use_case, "_has_specification_documents", return_value=True):
            # Act
            response1 = use_case.execute(request1)
            response2 = use_case.execute(request2)

            # Assert
            assert response1.success is True
            assert response2.success is True
            assert response1.execution_time_ms is not None
            assert response2.execution_time_ms is not None

    def test_large_feature_name_handling(
        self, use_case, mock_codemap_update_use_case
    ):
        """大きな機能名の処理テスト"""
        # Arrange
        large_feature_name = "very_long_feature_name_" * 100
        request = B20PreImplementationCheckRequest(
            feature_name=large_feature_name,
            target_layer="domain",
            auto_fix_issues=False,
            create_missing_spec=False,
        )

        mock_codemap_update_use_case.return_value = {"status": "available"}

        with patch.object(use_case, "_has_specification_documents", return_value=True):
            # Act
            response = use_case.execute(request)

            # Assert
            assert response.success is True
            assert response.feature_name == large_feature_name

    @pytest.mark.spec("SPEC-B20-PREPROCESSING-001")
    def test_b20_preprocessing_specification_compliance(
        self, use_case, basic_request, mock_codemap_update_use_case
    ):
        """B20前処理仕様準拠テスト"""
        # Arrange
        mock_codemap_update_use_case.return_value = {"status": "available"}

        with patch.object(use_case, "_has_specification_documents", return_value=True), \
             patch.object(use_case, "_has_test_files", return_value=True):

            # Act
            response = use_case.execute(basic_request)

            # Assert - SPEC-B20-PREPROCESSING-001の要件
            assert response.success is True
            assert response.implementation_allowed is True
            assert response.current_stage is not None
            assert response.completion_percentage >= 0.0
            assert response.next_required_actions is not None
            assert response.warnings is not None
            assert response.errors is not None
            assert response.codemap_status is not None
            assert response.execution_time_ms is not None
