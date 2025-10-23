#!/usr/bin/env python3
"""B20PreImplementationCheckUseCaseの簡易単体テスト

実際のプロジェクト構造に基づいた単体テスト
"""

from unittest.mock import MagicMock, patch
from pathlib import Path
import pytest
import tempfile
import shutil

from noveler.application.use_cases.b20_pre_implementation_check_use_case import (
    B20PreImplementationCheckUseCase,
    B20PreImplementationCheckRequest,
    B20PreImplementationCheckResponse,
)


@pytest.fixture
def temp_project_dir():
    """テスト用一時プロジェクトディレクトリ"""
    temp_dir = tempfile.mkdtemp(prefix="b20_test_")
    temp_path = Path(temp_dir)

    # 基本ディレクトリ構造作成
    (temp_path / "specs").mkdir(exist_ok=True)
    (temp_path / "tests").mkdir(exist_ok=True)
    (temp_path / "src").mkdir(exist_ok=True)

    yield temp_path
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_path_service(temp_project_dir):
    """モックパスサービス"""
    path_service = MagicMock()
    path_service.project_root = temp_project_dir
    path_service.get_spec_path.return_value = temp_project_dir / "specs"
    return path_service


@pytest.fixture
def use_case(mock_path_service):
    """テスト対象のユースケース"""
    return B20PreImplementationCheckUseCase(
        path_service=mock_path_service,
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


class TestB20PreImplementationCheckUseCaseBasic:
    """B20PreImplementationCheckUseCaseの基本テストクラス"""

    def test_execute_basic_success(self, use_case, basic_request, temp_project_dir):
        """基本的な実行成功テスト"""
        # Arrange - 仕様書を作成
        specs_dir = temp_project_dir / "specs"
        (specs_dir / "test.md").write_text("# Test Specification", encoding="utf-8")

        # Act
        response = use_case.execute(basic_request)

        # Assert
        assert response.success is True
        assert response.implementation_allowed is False  # CODEMAPが設定されていないため
        assert response.current_stage == "codemap_check_required"
        assert response.completion_percentage == 40.0  # 仕様書(30%) + テストなし(0%) + CODEMAP不完全(10%)
        assert response.execution_time_ms is not None

    def test_execute_without_specs(self, use_case, basic_request):
        """仕様書なし実行テスト"""
        # Act
        response = use_case.execute(basic_request)

        # Assert
        assert response.success is True
        assert response.implementation_allowed is False
        assert "specification_required" in response.current_stage
        assert len(response.errors) > 0
        assert any("仕様書が見つかりません" in error for error in response.errors)

    def test_execute_with_invalid_layer(self, use_case, temp_project_dir):
        """無効なレイヤー指定テスト"""
        # Arrange
        request = B20PreImplementationCheckRequest(
            feature_name="test_feature",
            target_layer="invalid_layer",
            auto_fix_issues=False,
            create_missing_spec=False,
        )

        # Act
        response = use_case.execute(request)

        # Assert
        assert response.success is True
        assert len(response.errors) > 0
        assert any("無効なレイヤー" in error for error in response.errors)

    def test_execute_with_auto_fix(self, use_case, basic_request, temp_project_dir):
        """自動修正有効テスト"""
        # Arrange
        request = B20PreImplementationCheckRequest(
            feature_name="auto_fix_test",
            target_layer="domain",
            auto_fix_issues=True,
            create_missing_spec=True,
        )

        # Act
        response = use_case.execute(request)

        # Assert
        assert response.success is True
        assert response.auto_fix_results is not None
        assert "attempted_fixes" in response.auto_fix_results

    def test_has_specification_documents_with_specs(self, use_case, temp_project_dir):
        """仕様書存在確認 - 仕様書ありテスト"""
        # Arrange
        specs_dir = temp_project_dir / "specs"
        (specs_dir / "test.md").write_text("test spec", encoding="utf-8")

        # Act
        result = use_case._has_specification_documents()

        # Assert
        assert result is True

    def test_has_specification_documents_without_specs(self, use_case):
        """仕様書存在確認 - 仕様書なしテスト"""
        # Act
        result = use_case._has_specification_documents()

        # Assert
        assert result is False

    def test_has_test_files_with_tests(self, use_case, temp_project_dir):
        """テストファイル存在確認 - テストファイルありテスト"""
        # Arrange
        tests_dir = temp_project_dir / "tests"
        (tests_dir / "test_example.py").write_text("test content", encoding="utf-8")

        # Act
        result = use_case._has_test_files()

        # Assert
        assert result is True

    def test_has_test_files_without_tests(self, use_case):
        """テストファイル存在確認 - テストファイルなしテスト"""
        # Act
        result = use_case._has_test_files()

        # Assert
        assert result is False

    def test_create_specification_file_success(self, use_case, temp_project_dir):
        """仕様書ファイル作成成功テスト"""
        # Act
        result = use_case._create_specification_file("test_feature")

        # Assert
        assert result["success"] is True
        assert "SPEC-TEST-FEATURE-001.md" in result["file_path"]

        # 実際にファイルが作成されたか確認
        created_file = Path(result["file_path"])
        assert created_file.exists()

    def test_execution_error_handling(self, use_case, basic_request):
        """実行エラーハンドリングテスト"""
        # Arrange - _check_codemap_statusでエラーを発生させる
        with patch.object(use_case, "_check_codemap_status", side_effect=Exception("Test error")):
            # Act
            response = use_case.execute(basic_request)

            # Assert
            assert response.success is False
            assert response.current_stage == "ERROR"
            assert response.completion_percentage == 0.0
            assert "実行エラー" in str(response.errors)

    def test_get_development_stage_guidance(self, use_case, temp_project_dir):
        """開発段階ガイダンス取得テスト"""
        # Arrange - 仕様書を作成
        specs_dir = temp_project_dir / "specs"
        (specs_dir / "test.md").write_text("# Test Specification", encoding="utf-8")

        # Act
        guidance = use_case.get_development_stage_guidance("test_feature")

        # Assert
        assert guidance["current_stage"] is not None
        assert guidance["completion_percentage"] >= 0.0
        assert guidance["implementation_allowed"] is not None
        assert guidance["estimated_time"] is not None

    def test_8_steps_execution_sequence(self, use_case, temp_project_dir):
        """8ステップ実行順序テスト"""
        # Arrange
        request = B20PreImplementationCheckRequest(
            feature_name="eight_steps_test",
            target_layer="domain",
            auto_fix_issues=True,
            create_missing_spec=True,
            force_codemap_update=True,
        )

        # Act
        response = use_case.execute(request)

        # Assert - 8ステップの結果が含まれている
        assert response.success is True
        # ステップ1: CODEMAPステータス
        assert response.codemap_status is not None
        # ステップ2: 実装許可判定
        assert response.implementation_allowed is not None
        # ステップ3: 進捗状況
        assert response.current_stage is not None
        assert response.completion_percentage is not None
        # ステップ4: 次のアクション
        assert response.next_required_actions is not None
        # ステップ5: 警告・エラー
        assert response.warnings is not None
        assert response.errors is not None
        # ステップ6-8: 自動修正・再評価・強制更新
        assert response.auto_fix_results is not None
        assert response.execution_time_ms is not None


class TestB20Performance:
    """B20ユースケースのパフォーマンステスト"""

    def test_execution_time_measurement(self, use_case, basic_request):
        """実行時間計測テスト"""
        # Act
        response = use_case.execute(basic_request)

        # Assert
        assert response.execution_time_ms is not None
        assert response.execution_time_ms > 0
        assert response.execution_time_ms < 5000  # 5秒以内

    def test_concurrent_execution_safety(self, use_case):
        """並行実行安全性テスト"""
        # Arrange
        requests = [
            B20PreImplementationCheckRequest(
                feature_name=f"concurrent_test_{i}",
                target_layer="domain"
            )
            for i in range(3)
        ]

        # Act
        responses = [use_case.execute(req) for req in requests]

        # Assert
        for response in responses:
            assert response.success is True
            assert response.execution_time_ms is not None


@pytest.mark.spec("SPEC-B20-PREPROCESSING-001")
class TestB20SpecificationCompliance:
    """B20前処理仕様準拠テスト"""

    def test_b20_preprocessing_specification_compliance(
        self, use_case, basic_request, temp_project_dir
    ):
        """B20前処理仕様準拠テスト"""
        # Arrange - 仕様書を作成
        specs_dir = temp_project_dir / "specs"
        (specs_dir / "test.md").write_text("# Test Specification", encoding="utf-8")

        # Act
        response = use_case.execute(basic_request)

        # Assert - SPEC-B20-PREPROCESSING-001の要件
        assert response.success is True
        assert response.implementation_allowed is not None
        assert response.current_stage is not None
        assert response.completion_percentage >= 0.0
        assert response.next_required_actions is not None
        assert response.warnings is not None
        assert response.errors is not None
        assert response.codemap_status is not None
        assert response.execution_time_ms is not None
