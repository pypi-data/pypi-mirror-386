"""デプロイメントドメインサービスのテスト

TDD準拠テスト:
    - DeploymentService
- VersionControlService
- BackupService
- AutoDeploymentService


仕様書: SPEC-UNIT-TEST
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

from noveler.domain.deployment.entities import (
    Deployment,
    DeploymentMode,
    DeploymentTarget,
)
from noveler.domain.deployment.services import (
    AutoDeploymentService,
    BackupService,
    DeploymentService,
    VersionControlService,
)
from noveler.domain.deployment.value_objects import (
    CommitHash,
    DeploymentResult,
    ProjectPath,
)


class TestDeploymentService:
    """DeploymentServiceのテストクラス"""

    @pytest.fixture
    def mock_git_repo(self) -> Mock:
        """GitRepositoryのモック"""
        mock = Mock()
        mock.has_uncommitted_changes.return_value = False
        mock.get_uncommitted_files.return_value = []
        mock.get_current_commit.return_value = CommitHash("abc123def456")
        return mock

    @pytest.fixture
    def mock_project_repo(self) -> Mock:
        """ProjectRepositoryのモック"""
        mock = Mock()
        mock.find_all_projects.return_value = []
        mock.project_exists.return_value = True
        return mock

    @pytest.fixture
    def deployment_service(self, mock_git_repo: Mock, mock_project_repo: Mock) -> DeploymentService:
        """DeploymentServiceのインスタンス"""
        return DeploymentService(mock_git_repo, mock_project_repo)

    @pytest.fixture
    def sample_target(self) -> DeploymentTarget:
        """サンプルデプロイメント対象"""
        return DeploymentTarget(project_path=ProjectPath("/path/to/project"), project_name="test-project")

    @pytest.mark.spec("SPEC-DEPLOYMENT_SERVICES-CHECK_UNCOMMITTED_CH")
    def test_check_uncommitted_changes_no_changes(
        self, deployment_service: DeploymentService, mock_git_repo: Mock
    ) -> None:
        """未コミット変更がない場合のテスト"""
        mock_git_repo.has_uncommitted_changes.return_value = False

        has_changes, files = deployment_service.check_uncommitted_changes()

        assert has_changes is False
        assert files == []
        mock_git_repo.has_uncommitted_changes.assert_called_once()
        mock_git_repo.get_uncommitted_files.assert_not_called()

    @pytest.mark.spec("SPEC-DEPLOYMENT_SERVICES-CHECK_UNCOMMITTED_CH")
    def test_check_uncommitted_changes_with_changes(
        self, deployment_service: DeploymentService, mock_git_repo: Mock
    ) -> None:
        """未コミット変更がある場合のテスト"""
        mock_git_repo.has_uncommitted_changes.return_value = True
        mock_git_repo.get_uncommitted_files.return_value = ["file1.py", "file2.py"]

        has_changes, files = deployment_service.check_uncommitted_changes()

        assert has_changes is True
        assert files == ["file1.py", "file2.py"]
        mock_git_repo.has_uncommitted_changes.assert_called_once()
        mock_git_repo.get_uncommitted_files.assert_called_once()

    @pytest.mark.spec("SPEC-DEPLOYMENT_SERVICES-FIND_DEPLOYABLE_PROJ")
    def test_find_deployable_projects(self, deployment_service: DeploymentService, mock_project_repo: Mock) -> None:
        """デプロイ可能プロジェクトの検索テスト"""
        expected_projects = [
            DeploymentTarget(ProjectPath("/project1"), "Project 1"),
            DeploymentTarget(ProjectPath("/project2"), "Project 2"),
        ]
        mock_project_repo.find_all_projects.return_value = expected_projects

        projects = deployment_service.find_deployable_projects()

        assert projects == expected_projects
        mock_project_repo.find_all_projects.assert_called_once()

    @pytest.mark.spec("SPEC-DEPLOYMENT_SERVICES-VALIDATE_DEPLOYMENT_")
    def test_validate_deployment_readiness_production_with_uncommitted_changes(
        self, deployment_service: DeploymentService, mock_git_repo: Mock, sample_target: DeploymentTarget
    ) -> None:
        """本番モードで未コミット変更がある場合の検証テスト"""
        mock_git_repo.has_uncommitted_changes.return_value = True
        mock_git_repo.get_uncommitted_files.return_value = ["file1.py", "file2.py", "file3.py", "file4.py"]

        deployment = Deployment(
            target=sample_target, mode=DeploymentMode.PRODUCTION, source_commit=CommitHash("abc123def456")
        )

        is_ready, issues = deployment_service.validate_deployment_readiness(deployment)

        assert is_ready is False
        assert len(issues) >= 1
        assert "Uncommitted changes detected" in issues[0]
        assert "file1.py, file2.py, file3.py" in issues[0]
        assert "... and 1 more files" in issues[1]

    @pytest.mark.spec("SPEC-DEPLOYMENT_SERVICES-VALIDATE_DEPLOYMENT_")
    def test_validate_deployment_readiness_development_mode(
        self, deployment_service: DeploymentService, mock_git_repo: Mock, sample_target: DeploymentTarget
    ) -> None:
        """開発モードの場合の検証テスト(未コミット変更は許可)"""
        mock_git_repo.has_uncommitted_changes.return_value = True

        deployment = Deployment(
            target=sample_target, mode=DeploymentMode.DEVELOPMENT, source_commit=CommitHash("abc123def456")
        )

        is_ready, issues = deployment_service.validate_deployment_readiness(deployment)

        # 開発モードでは未コミット変更があっても警告のみ
        uncommitted_issues = [issue for issue in issues if "Uncommitted changes" in issue]
        assert len(uncommitted_issues) == 0

    @pytest.mark.spec("SPEC-DEPLOYMENT_SERVICES-VALIDATE_DEPLOYMENT_")
    def test_validate_deployment_readiness_project_not_exists(
        self, deployment_service: DeploymentService, mock_project_repo: Mock, sample_target: DeploymentTarget
    ) -> None:
        """プロジェクトが存在しない場合の検証テスト"""
        mock_project_repo.project_exists.return_value = False

        deployment = Deployment(
            target=sample_target, mode=DeploymentMode.PRODUCTION, source_commit=CommitHash("abc123def456")
        )

        is_ready, issues = deployment_service.validate_deployment_readiness(deployment)

        assert is_ready is False
        assert any("Project directory does not exist" in issue for issue in issues)

    @pytest.mark.spec("SPEC-DEPLOYMENT_SERVICES-DETERMINE_DEPLOYMENT")
    def test_determine_deployment_mode_force_development(self, deployment_service: DeploymentService) -> None:
        """開発モード強制指定のテスト"""
        mode = deployment_service.determine_deployment_mode(force_development=True)
        assert mode == DeploymentMode.DEVELOPMENT

    @pytest.mark.spec("SPEC-DEPLOYMENT_SERVICES-DETERMINE_DEPLOYMENT")
    def test_determine_deployment_mode_with_uncommitted_changes(
        self, deployment_service: DeploymentService, mock_git_repo: Mock
    ) -> None:
        """未コミット変更がある場合のモード決定テスト"""
        mock_git_repo.has_uncommitted_changes.return_value = True

        mode = deployment_service.determine_deployment_mode()

        assert mode == DeploymentMode.DEVELOPMENT

    @pytest.mark.spec("SPEC-DEPLOYMENT_SERVICES-DETERMINE_DEPLOYMENT")
    def test_determine_deployment_mode_production_ready(
        self, deployment_service: DeploymentService, mock_git_repo: Mock
    ) -> None:
        """本番準備完了状態のモード決定テスト"""
        mock_git_repo.has_uncommitted_changes.return_value = False

        mode = deployment_service.determine_deployment_mode()

        assert mode == DeploymentMode.PRODUCTION

    @patch("noveler.domain.deployment.services.project_now")
    def test_create_deployment_with_auto_mode(
        self,
        mock_project_now: Mock,
        deployment_service: DeploymentService,
        mock_git_repo: Mock,
        sample_target: DeploymentTarget,
    ) -> None:
        """自動モード決定でのデプロイメント作成テスト"""
        # B30品質作業指示書遵守: 適切なMock使用
        # B30品質作業指示書遵守: 適切なdatetime Mock修正
        mock_project_now.return_value = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_git_repo.has_uncommitted_changes.return_value = False
        expected_commit = CommitHash("abc123def456")
        mock_git_repo.get_current_commit.return_value = expected_commit

        deployment = deployment_service.create_deployment(sample_target, mode=None)

        assert deployment.target == sample_target
        assert deployment.mode == DeploymentMode.PRODUCTION
        assert deployment.source_commit == expected_commit
        assert deployment.timestamp == datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    @pytest.mark.spec("SPEC-DEPLOYMENT_SERVICES-CREATE_DEPLOYMENT_WI")
    def test_create_deployment_with_specified_mode(
        self, deployment_service: DeploymentService, sample_target: DeploymentTarget
    ) -> None:
        """指定モードでのデプロイメント作成テスト"""
        deployment = deployment_service.create_deployment(sample_target, mode=DeploymentMode.DEVELOPMENT)

        assert deployment.mode == DeploymentMode.DEVELOPMENT


class TestVersionControlService:
    """VersionControlServiceのテストクラス"""

    @pytest.fixture
    def mock_git_repo(self) -> Mock:
        """GitRepositoryのモック"""
        mock = Mock()
        mock.get_current_commit.return_value = CommitHash("abc123def456")
        mock.get_current_branch.return_value = "main"
        mock.has_uncommitted_changes.return_value = False
        return mock

    @pytest.fixture
    def version_service(self, mock_git_repo: Mock) -> VersionControlService:
        """VersionControlServiceのインスタンス"""
        return VersionControlService(mock_git_repo)

    @pytest.mark.spec("SPEC-DEPLOYMENT_SERVICES-GET_CURRENT_COMMIT")
    def test_get_current_commit(self, version_service: VersionControlService, mock_git_repo: Mock) -> None:
        """現在のコミットハッシュ取得テスト"""
        expected_commit = CommitHash("abc123def456")
        mock_git_repo.get_current_commit.return_value = expected_commit

        commit = version_service.get_current_commit()

        assert commit == expected_commit
        mock_git_repo.get_current_commit.assert_called_once()

    @pytest.mark.spec("SPEC-DEPLOYMENT_SERVICES-GET_CURRENT_BRANCH")
    def test_get_current_branch(self, version_service: VersionControlService, mock_git_repo: Mock) -> None:
        """現在のブランチ名取得テスト"""
        expected_branch = "feature/new-feature"
        mock_git_repo.get_current_branch.return_value = expected_branch

        branch = version_service.get_current_branch()

        assert branch == expected_branch
        mock_git_repo.get_current_branch.assert_called_once()

    @patch("noveler.domain.deployment.services.getpass")
    def test_create_version_info(
        self, mock_getpass: Mock, version_service: VersionControlService, mock_git_repo: Mock
    ) -> None:
        """バージョン情報作成テスト"""
        mock_getpass.getuser.return_value = "test-user"
        mock_git_repo.get_current_branch.return_value = "main"

        deployment = Deployment(
            target=DeploymentTarget(ProjectPath("/test"), "test"),
            mode=DeploymentMode.PRODUCTION,
            source_commit=CommitHash("abc123def456"),
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            id="deployment-123",
        )

        version_info = version_service.create_version_info(deployment)

        assert version_info.commit_hash == deployment.source_commit
        assert version_info.timestamp == deployment.timestamp
        assert version_info.deployed_by == "test-user"
        assert version_info.branch == "main"
        assert version_info.mode == DeploymentMode.PRODUCTION
        assert version_info.deployment_id == "deployment-123"

    @pytest.mark.spec("SPEC-DEPLOYMENT_SERVICES-IS_PRODUCTION_READY_")
    def test_is_production_ready_true(self, version_service: VersionControlService, mock_git_repo: Mock) -> None:
        """本番準備完了状態のテスト"""
        mock_git_repo.has_uncommitted_changes.return_value = False

        is_ready = version_service.is_production_ready()

        assert is_ready is True
        mock_git_repo.has_uncommitted_changes.assert_called_once()

    @pytest.mark.spec("SPEC-DEPLOYMENT_SERVICES-IS_PRODUCTION_READY_")
    def test_is_production_ready_false(self, version_service: VersionControlService, mock_git_repo: Mock) -> None:
        """本番準備未完了状態のテスト"""
        mock_git_repo.has_uncommitted_changes.return_value = True

        is_ready = version_service.is_production_ready()

        assert is_ready is False


class TestBackupService:
    """BackupServiceのテストクラス"""

    @pytest.fixture
    def backup_service(self) -> BackupService:
        """BackupServiceのインスタンス"""
        return BackupService()

    @pytest.mark.spec("SPEC-DEPLOYMENT_SERVICES-SHOULD_CREATE_BACKUP")
    def test_should_create_backup_exists(self, backup_service: BackupService) -> None:
        """バックアップ作成判定テスト(.novel-scriptsが存在)"""
        # Mock the path property since ProjectPath is frozen
        target_path = ProjectPath("/path/to/project")

        # Mock the path division and existence check
        mock_project_path = Mock()
        mock_scripts_path = Mock()
        mock_scripts_path.exists.return_value = True
        mock_project_path.__truediv__ = Mock(return_value=mock_scripts_path)

        # Mock ProjectPath.path to return our mocked path
        with patch.object(ProjectPath, "path", new_callable=lambda: property(lambda self: mock_project_path)):
            should_backup = backup_service.should_create_backup(target_path)

        assert should_backup is True

    @pytest.mark.spec("SPEC-DEPLOYMENT_SERVICES-SHOULD_CREATE_BACKUP")
    def test_should_create_backup_not_exists(self, backup_service: BackupService) -> None:
        """バックアップ作成判定テスト(.novel-scriptsが存在しない)"""
        target_path = ProjectPath("/path/to/project")

        # Mock the path division and existence check
        mock_project_path = Mock()
        mock_scripts_path = Mock()
        mock_scripts_path.exists.return_value = False
        mock_project_path.__truediv__ = Mock(return_value=mock_scripts_path)

        # Mock ProjectPath.path to return our mocked path
        with patch.object(ProjectPath, "path", new_callable=lambda: property(lambda self: mock_project_path)):
            should_backup = backup_service.should_create_backup(target_path)

        assert should_backup is False

    @pytest.mark.spec("SPEC-DEPLOYMENT_SERVICES-GENERATE_BACKUP_NAME")
    def test_generate_backup_name(self, backup_service: BackupService) -> None:
        """バックアップ名生成テスト"""
        timestamp = datetime(2024, 1, 15, 14, 30, 45, tzinfo=timezone.utc)

        backup_name = backup_service.generate_backup_name(timestamp)

        assert backup_name == ".noveler.backup.20240115_143045"

    @pytest.mark.spec("SPEC-DEPLOYMENT_SERVICES-CALCULATE_BACKUP_SIZ")
    def test_calculate_backup_size(self, backup_service: BackupService) -> None:
        """バックアップサイズ計算テスト"""
        backup_path = ProjectPath("/path/to/backup")

        # Mock filesystem_path since ProjectPath is frozen
        mock_filesystem_path = Mock()

        # File 1: 100 bytes
        mock_file1 = Mock()
        mock_file1.is_file.return_value = True
        mock_file1.stat.return_value.st_size = 100

        # File 2: 200 bytes
        mock_file2 = Mock()
        mock_file2.is_file.return_value = True
        mock_file2.stat.return_value.st_size = 200

        # Directory (ignored in calculation)
        mock_dir = Mock()
        mock_dir.is_file.return_value = False

        mock_filesystem_path.rglob.return_value = [mock_file1, mock_file2, mock_dir]

        # Mock ProjectPath.path to return our mocked filesystem path
        with patch.object(ProjectPath, "path", new_callable=lambda: property(lambda self: mock_filesystem_path)):
            total_size = backup_service.calculate_backup_size(backup_path)

        assert total_size == 300


class TestAutoDeploymentService:
    """AutoDeploymentServiceのテストクラス"""

    @pytest.fixture
    def mock_git_synchronizer(self) -> Mock:
        """Git同期処理のモック"""
        return Mock()

    @pytest.fixture
    def auto_deployment_service(self, mock_git_synchronizer: Mock) -> AutoDeploymentService:
        """AutoDeploymentServiceのインスタンス"""
        return AutoDeploymentService(mock_git_synchronizer, create_backup=True)

    @pytest.fixture
    def sample_target(self) -> DeploymentTarget:
        """サンプルデプロイメント対象"""
        return DeploymentTarget(project_path=ProjectPath("/path/to/project"), project_name="test-project")

    @pytest.mark.spec("SPEC-DEPLOYMENT_SERVICES-CHECK_FOR_UPDATES_IN")
    def test_check_for_updates_initial_deploy(
        self, auto_deployment_service: AutoDeploymentService, mock_git_synchronizer: Mock
    ) -> None:
        """初回デプロイ時の更新チェックテスト"""
        project_path = ProjectPath("/path/to/project")
        mock_git_synchronizer.get_latest_commit.return_value = CommitHash("abc123")
        mock_git_synchronizer.get_deployed_commit.return_value = None

        has_updates = auto_deployment_service.check_for_updates(project_path)

        assert has_updates is True

    @pytest.mark.spec("SPEC-DEPLOYMENT_SERVICES-CHECK_FOR_UPDATES_HA")
    def test_check_for_updates_has_new_commits(
        self, auto_deployment_service: AutoDeploymentService, mock_git_synchronizer: Mock
    ) -> None:
        """新しいコミットがある場合の更新チェックテスト"""
        project_path = ProjectPath("/path/to/project")
        mock_git_synchronizer.get_latest_commit.return_value = CommitHash("def456")
        mock_git_synchronizer.get_deployed_commit.return_value = CommitHash("abc123")

        has_updates = auto_deployment_service.check_for_updates(project_path)

        assert has_updates is True

    @pytest.mark.spec("SPEC-DEPLOYMENT_SERVICES-CHECK_FOR_UPDATES_NO")
    def test_check_for_updates_no_new_commits(
        self, auto_deployment_service: AutoDeploymentService, mock_git_synchronizer: Mock
    ) -> None:
        """新しいコミットがない場合の更新チェックテスト"""
        project_path = ProjectPath("/path/to/project")
        same_commit = CommitHash("abc123")
        mock_git_synchronizer.get_latest_commit.return_value = same_commit
        mock_git_synchronizer.get_deployed_commit.return_value = same_commit

        has_updates = auto_deployment_service.check_for_updates(project_path)

        assert has_updates is False

    @pytest.mark.spec("SPEC-DEPLOYMENT_SERVICES-CHECK_FOR_UPDATES_EX")
    def test_check_for_updates_exception_handling(
        self, auto_deployment_service: AutoDeploymentService, mock_git_synchronizer: Mock
    ) -> None:
        """例外発生時の更新チェックテスト"""
        project_path = ProjectPath("/path/to/project")
        mock_git_synchronizer.get_latest_commit.side_effect = Exception("Git error")

        has_updates = auto_deployment_service.check_for_updates(project_path)

        assert has_updates is False

    @pytest.mark.spec("SPEC-DEPLOYMENT_SERVICES-AUTO_UPDATE_SUCCESS_")
    def test_auto_update_success_with_backup(
        self,
        auto_deployment_service: AutoDeploymentService,
        mock_git_synchronizer: Mock,
        sample_target: DeploymentTarget,
    ) -> None:
        """バックアップ付き自動更新成功テスト"""
        mock_git_synchronizer.sync_to_latest.return_value = True

        result = auto_deployment_service.auto_update(sample_target)

        assert isinstance(result, DeploymentResult)
        assert result.success is True
        assert "Successfully updated test-project" in result.message
        mock_git_synchronizer.create_backup.assert_called_once_with(sample_target.project_path)
        mock_git_synchronizer.sync_to_latest.assert_called_once_with(sample_target.project_path)

    @pytest.mark.spec("SPEC-DEPLOYMENT_SERVICES-AUTO_UPDATE_SUCCESS_")
    def test_auto_update_success_without_backup(
        self, mock_git_synchronizer: Mock, sample_target: DeploymentTarget
    ) -> None:
        """バックアップなし自動更新成功テスト"""
        auto_deployment_service = AutoDeploymentService(mock_git_synchronizer, create_backup=False)
        mock_git_synchronizer.sync_to_latest.return_value = True

        result = auto_deployment_service.auto_update(sample_target)

        assert result.success is True
        mock_git_synchronizer.create_backup.assert_not_called()

    @pytest.mark.spec("SPEC-DEPLOYMENT_SERVICES-AUTO_UPDATE_SYNC_FAI")
    def test_auto_update_sync_failure(
        self,
        auto_deployment_service: AutoDeploymentService,
        mock_git_synchronizer: Mock,
        sample_target: DeploymentTarget,
    ) -> None:
        """同期失敗時の自動更新テスト"""
        mock_git_synchronizer.sync_to_latest.return_value = False

        result = auto_deployment_service.auto_update(sample_target)

        assert result.success is False
        assert "Failed to sync test-project" in result.message

    @pytest.mark.spec("SPEC-DEPLOYMENT_SERVICES-AUTO_UPDATE_EXCEPTIO")
    def test_auto_update_exception_handling(
        self,
        auto_deployment_service: AutoDeploymentService,
        mock_git_synchronizer: Mock,
        sample_target: DeploymentTarget,
    ) -> None:
        """例外発生時の自動更新テスト"""
        mock_git_synchronizer.create_backup.side_effect = Exception("Backup failed")

        result = auto_deployment_service.auto_update(sample_target)

        assert result.success is False
        assert "Auto-update failed" in result.message
        assert result.error_message == "Backup failed"
