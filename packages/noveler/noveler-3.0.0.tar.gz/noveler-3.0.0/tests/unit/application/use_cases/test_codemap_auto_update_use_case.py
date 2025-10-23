#!/usr/bin/env python3
"""CODEMAP自動更新ユースケースの単体テスト

仕様書: SPEC-CODEMAP-AUTO-UPDATE-001
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

from noveler.application.use_cases.codemap_auto_update_use_case import (
    CodeMapAutoUpdateRequest,
    CodeMapAutoUpdateUseCase,
)
from noveler.domain.entities.codemap_entity import CodeMapEntity, CodeMapMetadata
from noveler.domain.services.codemap_synchronization_service import CodeMapSynchronizationService
from noveler.domain.value_objects.commit_information import CommitInformation


class TestCodeMapAutoUpdateUseCase:
    """CODEMAP自動更新ユースケースのテストクラス"""

    @pytest.fixture
    def mock_codemap_repository(self):
        """CODEMAPリポジトリのモック"""
        return Mock()

    @pytest.fixture
    def mock_git_adapter(self):
        """Git情報アダプターのモック"""
        return Mock()

    @pytest.fixture
    def mock_sync_service(self):
        """CODEMAP同期サービスのモック"""
        return CodeMapSynchronizationService()

    @pytest.fixture
    def use_case(self, mock_codemap_repository, mock_git_adapter, mock_sync_service):
        """テスト対象のユースケース"""
        return CodeMapAutoUpdateUseCase(mock_codemap_repository, mock_git_adapter, mock_sync_service)

    @pytest.fixture
    def sample_commit_info(self):
        """サンプルコミット情報"""
        return CommitInformation.from_git_log(
            commit_hash="abcd1234567890abcdef1234567890abcdef1234",
            commit_date=datetime.now(timezone.utc),
            author_name="Test Author",
            author_email="test@example.com",
            commit_message="feat: implement new feature",
            changed_files=["noveler/domain/entities/test_entity.py", "README.md"],
            branch_name="master",
        )

    @pytest.fixture
    def sample_codemap(self):
        """サンプルCODEMAPエンティティ"""
        metadata = CodeMapMetadata(
            name="Test Project",
            architecture="DDD + Clean Architecture",
            version="1.0.0",
            last_updated=datetime.now(timezone.utc),
            commit="old1234",
        )

        return CodeMapEntity(
            metadata=metadata,
            architecture_layers=[],
            circular_import_issues=[],
            b20_compliance=None,
            quality_prevention=None,
        )

    @pytest.mark.spec("SPEC-CODEMAP_AUTO_UPDATE_USE_CASE-EXECUTE_SUCCESSFUL_U")
    def test_execute_successful_update(
        self, use_case, mock_codemap_repository, mock_git_adapter, sample_commit_info, sample_codemap
    ):
        """正常な更新プロセスのテスト"""
        # Arrange
        mock_git_adapter.is_git_repository.return_value = True
        mock_codemap_repository.load_codemap.return_value = sample_codemap
        mock_git_adapter.get_latest_commit_info.return_value = sample_commit_info
        mock_codemap_repository.create_backup.return_value = "backup_123"
        mock_codemap_repository.save_codemap.return_value = True

        request = CodeMapAutoUpdateRequest(force_update=False, create_backup=True, validate_result=True)

        # Act
        response = use_case.execute(request)

        # Assert
        assert response.success is True
        assert response.updated is True
        assert response.backup_id == "backup_123"
        assert response.commit_hash == sample_commit_info.short_hash
        assert response.execution_time_ms > 0

        # モックの呼び出し確認
        mock_git_adapter.is_git_repository.assert_called_once()
        mock_codemap_repository.load_codemap.assert_called_once()
        mock_git_adapter.get_latest_commit_info.assert_called_once()
        mock_codemap_repository.create_backup.assert_called_once()
        mock_codemap_repository.save_codemap.assert_called_once()

    @pytest.mark.spec("SPEC-CODEMAP_AUTO_UPDATE_USE_CASE-EXECUTE_NOT_GIT_REPO")
    def test_execute_not_git_repository(self, use_case, mock_git_adapter):
        """Gitリポジトリでない場合のテスト"""
        # Arrange
        mock_git_adapter.is_git_repository.return_value = False
        request = CodeMapAutoUpdateRequest()

        # Act
        response = use_case.execute(request)

        # Assert
        assert response.success is False
        assert response.error_message == "Not a Git repository"
        assert response.updated is False

    @pytest.mark.spec("SPEC-CODEMAP_AUTO_UPDATE_USE_CASE-EXECUTE_CODEMAP_LOAD")
    def test_execute_codemap_load_failed(self, use_case, mock_codemap_repository, mock_git_adapter):
        """CODEMAP読み込み失敗のテスト"""
        # Arrange
        mock_git_adapter.is_git_repository.return_value = True
        mock_codemap_repository.load_codemap.return_value = None
        request = CodeMapAutoUpdateRequest()

        # Act
        response = use_case.execute(request)

        # Assert
        assert response.success is False
        assert response.error_message == "Failed to load current CODEMAP"
        assert response.updated is False

    @pytest.mark.spec("SPEC-CODEMAP_AUTO_UPDATE_USE_CASE-EXECUTE_COMMIT_INFO_")
    def test_execute_commit_info_failed(self, use_case, mock_codemap_repository, mock_git_adapter, sample_codemap):
        """コミット情報取得失敗のテスト"""
        # Arrange
        mock_git_adapter.is_git_repository.return_value = True
        mock_codemap_repository.load_codemap.return_value = sample_codemap
        mock_git_adapter.get_latest_commit_info.return_value = None
        request = CodeMapAutoUpdateRequest()

        # Act
        response = use_case.execute(request)

        # Assert
        assert response.success is False
        assert response.error_message == "Failed to get commit information"

    @pytest.mark.spec("SPEC-CODEMAP_AUTO_UPDATE_USE_CASE-EXECUTE_NO_UPDATE_NE")
    def test_execute_no_update_needed(
        self, use_case, mock_codemap_repository, mock_git_adapter, sample_commit_info, sample_codemap
    ):
        """更新不要の場合のテスト"""
        # Arrange
        sample_codemap.metadata.commit = sample_commit_info.short_hash  # 既に同じコミットで更新済み
        mock_git_adapter.is_git_repository.return_value = True
        mock_codemap_repository.load_codemap.return_value = sample_codemap
        mock_git_adapter.get_latest_commit_info.return_value = sample_commit_info

        request = CodeMapAutoUpdateRequest(force_update=False)

        # Act
        response = use_case.execute(request)

        # Assert
        assert response.success is True
        assert response.updated is False
        assert response.changes_summary == "No update needed"

    @pytest.mark.spec("SPEC-CODEMAP_AUTO_UPDATE_USE_CASE-EXECUTE_FORCE_UPDATE")
    def test_execute_force_update(
        self, use_case, mock_codemap_repository, mock_git_adapter, sample_commit_info, sample_codemap
    ):
        """強制更新のテスト"""
        # Arrange
        sample_codemap.metadata.commit = sample_commit_info.short_hash  # 既に同じコミット
        mock_git_adapter.is_git_repository.return_value = True
        mock_codemap_repository.load_codemap.return_value = sample_codemap
        mock_git_adapter.get_latest_commit_info.return_value = sample_commit_info
        mock_codemap_repository.create_backup.return_value = "backup_force"
        mock_codemap_repository.save_codemap.return_value = True

        request = CodeMapAutoUpdateRequest(force_update=True)

        # Act
        response = use_case.execute(request)

        # Assert
        assert response.success is True
        assert response.updated is True
        assert response.backup_id == "backup_force"

    @pytest.mark.spec("SPEC-CODEMAP_AUTO_UPDATE_USE_CASE-EXECUTE_BACKUP_CREAT")
    def test_execute_backup_creation_failed(
        self, use_case, mock_codemap_repository, mock_git_adapter, sample_commit_info, sample_codemap
    ):
        """バックアップ作成失敗のテスト"""
        # Arrange
        mock_git_adapter.is_git_repository.return_value = True
        mock_codemap_repository.load_codemap.return_value = sample_codemap
        mock_git_adapter.get_latest_commit_info.return_value = sample_commit_info
        mock_codemap_repository.create_backup.return_value = None  # バックアップ失敗

        request = CodeMapAutoUpdateRequest(create_backup=True)

        # Act
        response = use_case.execute(request)

        # Assert
        assert response.success is False
        assert response.error_message == "Failed to create backup"

    @pytest.mark.spec("SPEC-CODEMAP_AUTO_UPDATE_USE_CASE-EXECUTE_SYNCHRONIZAT")
    def test_execute_synchronization_failed(
        self, use_case, mock_codemap_repository, mock_git_adapter, mock_sync_service, sample_commit_info, sample_codemap
    ):
        """同期処理失敗のテスト"""
        # Arrange
        mock_git_adapter.is_git_repository.return_value = True
        mock_codemap_repository.load_codemap.return_value = sample_codemap
        mock_git_adapter.get_latest_commit_info.return_value = sample_commit_info
        mock_codemap_repository.create_backup.return_value = "backup_123"

        # 同期処理で例外発生
        with patch.object(mock_sync_service, "synchronize_with_commit", side_effect=Exception("Sync error")):
            request = CodeMapAutoUpdateRequest()

            # Act
            response = use_case.execute(request)

            # Assert
            assert response.success is False
            assert "Synchronization failed: Sync error" in response.error_message
            assert response.backup_id == "backup_123"

    @pytest.mark.spec("SPEC-CODEMAP_AUTO_UPDATE_USE_CASE-EXECUTE_VALIDATION_F")
    def test_execute_validation_failed(
        self, use_case, mock_codemap_repository, mock_git_adapter, mock_sync_service, sample_commit_info, sample_codemap
    ):
        """検証失敗時のロールバックテスト"""
        # Arrange
        mock_git_adapter.is_git_repository.return_value = True
        mock_codemap_repository.load_codemap.return_value = sample_codemap
        mock_git_adapter.get_latest_commit_info.return_value = sample_commit_info
        mock_codemap_repository.create_backup.return_value = "backup_123"
        mock_codemap_repository.restore_from_backup.return_value = True

        # 検証エラーを発生させる
        with patch.object(
            mock_sync_service,
            "validate_synchronization_result",
            return_value=["Validation error 1", "Validation error 2"],
        ):
            request = CodeMapAutoUpdateRequest(validate_result=True)

            # Act
            response = use_case.execute(request)

            # Assert
            assert response.success is False
            assert "Validation failed, restored from backup" in response.error_message
            assert response.validation_errors == ["Validation error 1", "Validation error 2"]
            mock_codemap_repository.restore_from_backup.assert_called_once_with("backup_123")

    @pytest.mark.spec("SPEC-CODEMAP_AUTO_UPDATE_USE_CASE-EXECUTE_SAVE_FAILED")
    def test_execute_save_failed(
        self, use_case, mock_codemap_repository, mock_git_adapter, sample_commit_info, sample_codemap
    ):
        """保存失敗時のロールバックテスト"""
        # Arrange
        mock_git_adapter.is_git_repository.return_value = True
        mock_codemap_repository.load_codemap.return_value = sample_codemap
        mock_git_adapter.get_latest_commit_info.return_value = sample_commit_info
        mock_codemap_repository.create_backup.return_value = "backup_save"
        mock_codemap_repository.save_codemap.return_value = False  # 保存失敗
        mock_codemap_repository.restore_from_backup.return_value = True

        request = CodeMapAutoUpdateRequest()

        # Act
        response = use_case.execute(request)

        # Assert
        assert response.success is False
        assert "Failed to save updated CODEMAP, restored from backup" in response.error_message
        mock_codemap_repository.restore_from_backup.assert_called_once_with("backup_save")

    @pytest.mark.spec("SPEC-CODEMAP_AUTO_UPDATE_USE_CASE-GET_UPDATE_STATUS_SU")
    def test_get_update_status_success(
        self, use_case, mock_codemap_repository, mock_git_adapter, sample_commit_info, sample_codemap
    ):
        """システム状態取得成功のテスト"""
        # Arrange
        sample_codemap.metadata.commit = "old1234"
        mock_codemap_repository.load_codemap.return_value = sample_codemap
        mock_git_adapter.get_latest_commit_info.return_value = sample_commit_info
        mock_git_adapter.is_git_repository.return_value = True

        # Act
        status = use_case.get_update_status()

        # Assert
        assert status["codemap_available"] is True
        assert status["git_repository"] is True
        assert status["current_commit"] == "old1234"
        assert status["latest_commit"] == sample_commit_info.short_hash
        assert status["needs_update"] is True
        assert "completion_rate" in status

    @pytest.mark.spec("SPEC-CODEMAP_AUTO_UPDATE_USE_CASE-GET_UPDATE_STATUS_ER")
    def test_get_update_status_error(self, use_case, mock_codemap_repository):
        """システム状態取得エラーのテスト"""
        # Arrange
        mock_codemap_repository.load_codemap.side_effect = Exception("Load error")

        # Act
        status = use_case.get_update_status()

        # Assert
        assert "error" in status
        assert status["error"] == "Load error"
        assert status["codemap_available"] is False
        assert status["git_repository"] is False

    @pytest.mark.spec("SPEC-CODEMAP_AUTO_UPDATE_USE_CASE-NEEDS_UPDATE_SAME_CO")
    def test_needs_update_same_commit(self, use_case, sample_codemap, sample_commit_info):
        """同じコミットの場合は更新不要のテスト"""
        # Arrange
        sample_codemap.metadata.commit = sample_commit_info.short_hash

        # Act
        needs_update = use_case._needs_update(sample_codemap, sample_commit_info)

        # Assert
        assert needs_update is False

    @pytest.mark.spec("SPEC-CODEMAP_AUTO_UPDATE_USE_CASE-NEEDS_UPDATE_IMPLEME")
    def test_needs_update_implementation_commit(self, use_case, sample_codemap):
        """実装コミットの場合は更新必要のテスト"""
        # Arrange
        sample_codemap.metadata.commit = "different1234"

        # 実装関連のコミット情報を作成
        impl_commit_info = CommitInformation.from_git_log(
            commit_hash="impl1234567890abcdef1234567890abcdef1234",
            commit_date=datetime.now(timezone.utc),
            author_name="Developer",
            author_email="dev@example.com",
            commit_message="feat: implement new domain entity",
            changed_files=["noveler/domain/entities/new_entity.py", "noveler/domain/services/entity_service.py"],
            branch_name="master",
        )

        # Act
        needs_update = use_case._needs_update(sample_codemap, impl_commit_info)

        # Assert
        assert needs_update is True

    @pytest.mark.spec("SPEC-CODEMAP_AUTO_UPDATE_USE_CASE-NEEDS_UPDATE_CODEMAP")
    def test_needs_update_codemap_related_docs(self, use_case, sample_codemap):
        """CODEMAP関連ドキュメント更新の場合のテスト"""
        # Arrange
        sample_codemap.metadata.commit = "different1234"

        # ドキュメント更新のコミット情報を作成
        docs_commit_info = CommitInformation.from_git_log(
            commit_hash="docs1234567890abcdef1234567890abcdef1234",
            commit_date=datetime.now(timezone.utc),
            author_name="Documentation Team",
            author_email="docs@example.com",
            commit_message="docs: update CODEMAP structure documentation",
            changed_files=["CODEMAP.yaml", "docs/architecture.md", "README.md"],
            branch_name="master",
        )

        # Act
        needs_update = use_case._needs_update(sample_codemap, docs_commit_info)

        # Assert
        assert needs_update is True

    @pytest.mark.spec("SPEC-CODEMAP_AUTO_UPDATE_USE_CASE-CREATE_CHANGES_SUMMA")
    def test_create_changes_summary(self, use_case):
        """変更サマリ作成のテスト"""
        # Arrange
        impact = {"issues_resolved": 2, "completion_rate_change": 5.5}

        # 変更サマリ用のコミット情報を作成
        summary_commit_info = CommitInformation.from_git_log(
            commit_hash="summary1234567890abcdef1234567890abcdef1234",
            commit_date=datetime.now(timezone.utc),
            author_name="Developer",
            author_email="dev@example.com",
            commit_message="refactor: improve architecture layers",
            changed_files=["noveler/domain/entities/entity.py", "noveler/infrastructure/adapters/adapter.py"],
            branch_name="master",
        )

        # Act
        summary = use_case._create_changes_summary(impact, summary_commit_info)

        # Assert
        expected = f"Updated from commit {summary_commit_info.short_hash}; 2 issues resolved; completion rate improved by 5.5%; affected files: scripts/domain/entities/entity.py, scripts/infrastructure/adapters/adapter.py"
        assert summary == expected

    @pytest.mark.parametrize(
        ("force_update", "create_backup", "validate_result"),
        [
            (True, True, True),
            (False, False, False),
            (True, False, True),
            (False, True, False),
        ],
    )
    @pytest.mark.spec("SPEC-CODEMAP_AUTO_UPDATE_USE_CASE-REQUEST_PARAMETER_CO")
    def test_request_parameter_combinations(
        self,
        use_case,
        mock_codemap_repository,
        mock_git_adapter,
        sample_commit_info,
        sample_codemap,
        force_update,
        create_backup,
        validate_result,
    ):
        """リクエストパラメータの組み合わせテスト"""
        # Arrange
        mock_git_adapter.is_git_repository.return_value = True
        mock_codemap_repository.load_codemap.return_value = sample_codemap
        mock_git_adapter.get_latest_commit_info.return_value = sample_commit_info

        if create_backup:
            mock_codemap_repository.create_backup.return_value = "backup_param"

        mock_codemap_repository.save_codemap.return_value = True

        request = CodeMapAutoUpdateRequest(
            force_update=force_update, create_backup=create_backup, validate_result=validate_result
        )

        # Act
        response = use_case.execute(request)

        # Assert
        assert response.success is True

        if create_backup:
            mock_codemap_repository.create_backup.assert_called_once()
            assert response.backup_id == "backup_param"
        else:
            mock_codemap_repository.create_backup.assert_not_called()
            assert response.backup_id is None
