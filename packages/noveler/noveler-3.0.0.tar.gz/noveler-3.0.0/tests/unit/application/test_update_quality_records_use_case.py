#!/usr/bin/env python3
"""品質記録更新ユースケースのテスト
TDD原則:アプリケーション層の使用事例をテスト


仕様書: SPEC-UNIT-TEST
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from noveler.application.use_cases.update_quality_records_use_case import (
    UpdateQualityRecordsRequest,
    UpdateQualityRecordsResponse,
    UpdateQualityRecordsUseCase,
)
from noveler.domain.entities.quality_record import QualityRecord
from noveler.domain.exceptions import RecordTransactionError
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.value_objects.quality_check_result import (
    AutoFix,
    CategoryScores,
    QualityCheckResult,
    QualityError,
    QualityScore,
)

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class TestUpdateQualityRecordsRequest:
    """更新リクエストの値オブジェクトテスト"""

    @pytest.mark.spec("SPEC-UPDATE_QUALITY_RECORDS_USE_CASE-VALID_REQUEST_CREATI")
    def test_valid_request_creation(self) -> None:
        """有効なリクエスト作成"""
        result = QualityCheckResult(
            episode_number=1,
            timestamp=project_now().datetime,
            checker_version="test_v1.0",
            category_scores=CategoryScores(
                basic_style=QualityScore.from_float(85.0),
                composition=QualityScore.from_float(80.0),
                character_consistency=QualityScore.from_float(88.0),
                readability=QualityScore.from_float(82.0),
            ),
            errors=[],
            warnings=[],
            auto_fixes=[],
        )

        request = UpdateQualityRecordsRequest(
            project_name="test_project", project_path=Path("/test/project"), quality_result=result
        )

        assert request.project_name == "test_project"
        assert request.project_path == Path("/test/project")
        assert request.quality_result.episode_number == 1

    @pytest.mark.spec("SPEC-UPDATE_QUALITY_RECORDS_USE_CASE-REQUEST_VALIDATION_E")
    def test_request_validation_empty_project_name(self) -> None:
        """空のプロジェクト名は無効"""
        result = QualityCheckResult(
            episode_number=1,
            timestamp=project_now().datetime,
            checker_version="test_v1.0",
            category_scores=CategoryScores(
                basic_style=QualityScore.from_float(80.0),
                composition=QualityScore.from_float(80.0),
                character_consistency=QualityScore.from_float(80.0),
                readability=QualityScore.from_float(80.0),
            ),
            errors=[],
            warnings=[],
            auto_fixes=[],
        )

        with pytest.raises(ValueError, match="Project name cannot be empty"):
            UpdateQualityRecordsRequest(project_name="", project_path=Path("/test"), quality_result=result)


class TestUpdateQualityRecordsUseCase:
    """品質記録更新ユースケースのテスト"""

    def setup_method(self) -> None:
        """テストセットアップ"""
        self.quality_repo = Mock()
        self.episode_repo = Mock()

        self.use_case = UpdateQualityRecordsUseCase(
            quality_record_repository=self.quality_repo, episode_management_repository=self.episode_repo
        )

    def create_sample_request(self) -> UpdateQualityRecordsRequest:
        """テスト用リクエスト作成"""
        result = QualityCheckResult(
            episode_number=1,
            timestamp=project_now().datetime,
            checker_version="test_v1.0",
            category_scores=CategoryScores(
                basic_style=QualityScore.from_float(90.0),
                composition=QualityScore.from_float(85.0),
                character_consistency=QualityScore.from_float(88.0),
                readability=QualityScore.from_float(82.0),
            ),
            errors=[QualityError(type="punctuation", message="記号エラー", line_number=10)],
            warnings=[],
            auto_fixes=[AutoFix(type="punctuation_fix", description="記号修正", count=1)],
        )

        return UpdateQualityRecordsRequest(
            project_name="test_project", project_path=Path("/test/project"), quality_result=result
        )

    @pytest.mark.spec("SPEC-UPDATE_QUALITY_RECORDS_USE_CASE-SUCCESSFUL_UPDATE_NE")
    def test_successful_update_new_record(self) -> None:
        """新規記録作成の成功パス"""
        # Arrange
        request = self.create_sample_request()

        # 新規プロジェクト(記録未存在)
        self.quality_repo.find_by_project.return_value = None

        # モックの設定
        self.quality_repo.save.return_value = None

        # Act
        response = self.use_case.execute(request)

        # Assert
        assert response.success is True
        assert response.error_message is None
        assert "品質記録.yaml" in response.updated_files

        # リポジトリメソッドの呼び出し確認
        self.quality_repo.find_by_project.assert_called_once_with("test_project")
        self.quality_repo.save.assert_called_once()

        # リポジトリメソッドが正しく呼び出されたことを確認
        saved_record = self.quality_repo.save.call_args[0][0]
        assert isinstance(saved_record, QualityRecord)

    @pytest.mark.spec("SPEC-UPDATE_QUALITY_RECORDS_USE_CASE-SUCCESSFUL_UPDATE_EX")
    def test_successful_update_existing_record(self) -> None:
        """既存記録更新の成功パス"""
        # Arrange
        request = self.create_sample_request()

        # 既存記録を返す
        existing_record = QualityRecord("test_project", [])
        self.quality_repo.find_by_project.return_value = existing_record

        # モックの設定
        self.quality_repo.save.return_value = None

        # Act
        response = self.use_case.execute(request)

        # Assert
        assert response.success is True
        assert existing_record.entry_count == 1  # 記録が追加された

        # 既存記録に結果が追加されていることを確認
        latest_entry = existing_record.get_latest_for_episode(1)
        assert latest_entry is not None
        assert latest_entry.quality_result.episode_number == 1

    @pytest.mark.spec("SPEC-UPDATE_QUALITY_RECORDS_USE_CASE-DUPLICATE_RECORD_HAN")
    def test_duplicate_record_handling(self) -> None:
        """重複記録の適切な処理"""
        # Arrange
        request = self.create_sample_request()

        # 重複エラーを発生させる既存記録
        existing_record = QualityRecord("test_project", [])
        # 同じエピソード・同じ時刻の記録を先に追加
        existing_record.add_quality_check_result(request.quality_result)

        self.quality_repo.find_by_project.return_value = existing_record

        # Act
        response = self.use_case.execute(request)

        # Assert
        assert response.success is False
        assert "Duplicate quality check" in response.error_message
        assert response.updated_files == []

    @pytest.mark.spec("SPEC-UPDATE_QUALITY_RECORDS_USE_CASE-TRANSACTION_FAILURE_")
    def test_transaction_failure_rollback(self) -> None:
        """トランザクション失敗時のロールバック"""
        # Arrange
        request = self.create_sample_request()
        self.quality_repo.find_by_project.return_value = None

        # 保存時にエラーを発生させる
        self.quality_repo.save.side_effect = RecordTransactionError("save", "Save failed")

        # Act
        response = self.use_case.execute(request)

        # Assert
        assert response.success is False
        assert "Save failed" in response.error_message

        # リポジトリメソッドの呼び出し確認
        self.quality_repo.save.assert_called_once()

    @pytest.mark.spec("SPEC-UPDATE_QUALITY_RECORDS_USE_CASE-PARTIAL_FAILURE_HAND")
    def test_partial_failure_handling(self) -> None:
        """部分失敗の処理"""
        # Arrange
        request = self.create_sample_request()
        self.quality_repo.find_by_project.return_value = None

        # エピソード管理更新でエラー
        self.episode_repo.update.side_effect = Exception("Episode update failed")

        # Act
        response = self.use_case.execute(request)

        # Assert
        assert response.success is False
        assert "Episode update failed" in response.error_message

    @pytest.mark.spec("SPEC-UPDATE_QUALITY_RECORDS_USE_CASE-REPOSITORY_DEPENDENC")
    def test_repository_dependency_injection(self) -> None:
        """依存性注入の確認"""
        # Arrange & Act
        use_case = UpdateQualityRecordsUseCase(
            quality_record_repository=self.quality_repo, episode_management_repository=self.episode_repo
        )

        # Assert
        assert use_case._quality_record_repository == self.quality_repo
        assert use_case._episode_management_repository == self.episode_repo

    @pytest.mark.spec("SPEC-UPDATE_QUALITY_RECORDS_USE_CASE-DOMAIN_EVENTS_PROCES")
    def test_domain_events_processing(self) -> None:
        """ドメインイベント処理の確認"""
        # Arrange
        request = self.create_sample_request()

        existing_record = QualityRecord("test_project", [])
        self.quality_repo.find_by_project.return_value = existing_record

        # モックの設定
        self.quality_repo.save.return_value = None

        # Act
        response = self.use_case.execute(request)

        # Assert
        assert response.success is True

        # ドメインイベントが発生し、クリアされていることを確認
        domain_events = existing_record.get_domain_events()
        assert len(domain_events) == 0  # イベントはクリアされている

    @pytest.mark.spec("SPEC-UPDATE_QUALITY_RECORDS_USE_CASE-ERROR_MESSAGE_FORMAT")
    def test_error_message_formatting(self) -> None:
        """エラーメッセージの適切なフォーマット"""
        # Arrange
        request = self.create_sample_request()
        self.quality_repo.find_by_project.side_effect = Exception("Database connection error")

        # Act
        response = self.use_case.execute(request)

        # Assert
        assert response.success is False
        assert "Database connection error" in response.error_message
        assert response.updated_files == []

    @pytest.mark.spec("SPEC-UPDATE_QUALITY_RECORDS_USE_CASE-RESPONSE_UPDATED_FIL")
    def test_response_updated_files_tracking(self) -> None:
        """更新ファイルの追跡"""
        # Arrange
        request = self.create_sample_request()
        self.quality_repo.find_by_project.return_value = None

        # モックの設定
        self.quality_repo.save.return_value = None

        # Act
        response = self.use_case.execute(request)

        # Assert
        assert response.success is True
        assert len(response.updated_files) == 3  # 品質記録、話数管理、改訂履歴
        assert "品質記録.yaml" in response.updated_files
        assert "話数管理.yaml" in response.updated_files
        assert "改訂履歴.yaml" in response.updated_files


class TestUpdateQualityRecordsResponse:
    """レスポンスの値オブジェクトテスト"""

    @pytest.mark.spec("SPEC-UPDATE_QUALITY_RECORDS_USE_CASE-SUCCESS_RESPONSE")
    def test_success_response(self) -> None:
        """成功レスポンス"""
        response = UpdateQualityRecordsResponse.success(updated_files=["品質記録.yaml", "話数管理.yaml"])

        assert response.success is True
        assert response.error_message is None
        assert len(response.updated_files) == 2

    @pytest.mark.spec("SPEC-UPDATE_QUALITY_RECORDS_USE_CASE-FAILURE_RESPONSE")
    def test_failure_response(self) -> None:
        """失敗レスポンス"""
        response = UpdateQualityRecordsResponse.failure(error_message="Update failed")

        assert response.success is False
        assert response.error_message == "Update failed"
        assert response.updated_files == []
