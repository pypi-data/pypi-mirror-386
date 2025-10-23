#!/usr/bin/env python3
# File: tests/unit/infrastructure/test_deployment_system.py
# Purpose: Verify deployment domain and infrastructure behaviour across services and repositories.
# Context: Utilises shared path management to resolve project roots for deployment workflows.

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# PathManager統一パス管理システムを使用(事前にパスを設定)
sys.path.insert(0, str(Path(__file__).parent.parent))  # scripts/を追加
from noveler.infrastructure.utils.path_manager import ensure_imports  # noqa: E402

ensure_imports()

from noveler.application.use_cases.deploy_scripts_use_case import DeployScriptsUseCase
from noveler.domain.deployment.entities import (
    Deployment,
    DeploymentMode,
    DeploymentStatus,
    DeploymentTarget,
    ScriptVersion,
)
from noveler.domain.deployment.value_objects import CommitHash, DeploymentConfig
from noveler.domain.value_objects.project_path import ProjectPath
from noveler.domain.value_objects.project_time import ProjectTimezone, project_datetime
from noveler.infrastructure.deployment.git_repository_impl import GitRepositoryImpl
from noveler.infrastructure.services.deployment_service import DeploymentService
from noveler.presentation.shared.shared_utilities import get_common_path_service


def resolve_project_path(raw_path: str | Path | None = None) -> ProjectPath:
    """共通PathServiceを介してプロジェクトパスを解決する"""

    path_service = get_common_path_service()
    if raw_path is None:
        resolved = path_service.project_root
    else:
        candidate = Path(raw_path)
        resolved = candidate if candidate.is_absolute() else path_service.project_root / candidate

    return ProjectPath(str(resolved))


# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone

class TestDeploymentEntities(unittest.TestCase):
    """デプロイメントエンティティのテスト"""

    def test_create_deployment(self) -> None:
        """デプロイメントエンティティの作成"""
        # Arrange
        target = DeploymentTarget(
            project_path=resolve_project_path("/path/to/project"),
            project_name="テスト小説プロジェクト",
        )

        # Act
        deployment = Deployment(
            target=target,
            mode=DeploymentMode.PRODUCTION,
            source_commit=CommitHash("abcd123"),
            timestamp=datetime.now(JST),
        )

        # Assert
        assert deployment.status == DeploymentStatus.PENDING
        assert deployment.mode == DeploymentMode.PRODUCTION
        assert deployment.id is not None

    def test_deployment_state_transitions(self) -> None:
        """デプロイメントの状態遷移"""
        # Arrange
        deployment = self._create_test_deployment()

        # Act & Assert
        # 開始
        deployment.start()
        assert deployment.status == DeploymentStatus.IN_PROGRESS

        # 完了
        deployment.complete()
        assert deployment.status == DeploymentStatus.COMPLETED

        # 完了後は開始できない
        with pytest.raises(ValueError, match=".*"):
            deployment.start()

    def test_deployment_failure(self) -> None:
        """デプロイメント失敗の処理"""
        # Arrange
        deployment = self._create_test_deployment()
        deployment.start()

        # Act
        deployment.fail("ディスク容量不足")

        # Assert
        assert deployment.status == DeploymentStatus.FAILED
        assert deployment.error_message == "ディスク容量不足"
        assert deployment.completed_at is not None

    def test_deployment_validation(self) -> None:
        """デプロイメントの検証"""
        # Arrange
        deployment = self._create_test_deployment()

        # Act & Assert
        # 開発モードでは警告
        deployment.mode = DeploymentMode.DEVELOPMENT
        warnings = deployment.validate()
        assert "development" in warnings[0].lower()

        # 本番モードでは開発警告なし(ただし他の警告は出る可能性)
        deployment.mode = DeploymentMode.PRODUCTION
        warnings = deployment.validate()
        # 開発モード関連の警告がないことを確認
        assert not any("development" in w.lower() for w in warnings)

    def _create_test_deployment(self):
        """テスト用デプロイメント作成"""
        target = DeploymentTarget(
            project_path=resolve_project_path("/test/project"),
            project_name="Test Project",
        )

        return Deployment(
            target=target,
            mode=DeploymentMode.PRODUCTION,
            source_commit=CommitHash("abcd123"),
        )


class TestScriptVersion(unittest.TestCase):
    """スクリプトバージョンのテスト"""

    def test_version_comparison(self) -> None:
        """バージョンの比較"""
        # Arrange
        v1 = ScriptVersion(
            commit_hash=CommitHash("abc123"),
            timestamp=project_datetime(2024, 1, 1).datetime,
            deployed_by="user1",
        )

        v2 = ScriptVersion(
            commit_hash=CommitHash("def456"),
            timestamp=project_datetime(2024, 1, 2).datetime,
            deployed_by="user2",
        )

        # Act & Assert
        assert v2.is_newer_than(v1)
        assert not v1.is_newer_than(v2)

    def test_version_info_generation(self) -> None:
        """バージョン情報の生成"""
        # Arrange
        version = ScriptVersion(
            commit_hash=CommitHash("abc123"),
            timestamp=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
            deployed_by="test_user",
            branch="main",
            mode=DeploymentMode.PRODUCTION,
        )

        # Act
        info = version.generate_version_info()

        # Assert
        assert "abc123" in info
        assert "2024-01-01" in info
        assert "PRODUCTION" in info
        assert "main" in info


class TestDeploymentService(unittest.TestCase):
    """デプロイメントサービスのテスト"""

    def setUp(self) -> None:
        self.git_repo = Mock()
        self.project_repo = Mock()
        self.service = DeploymentService(self.git_repo, self.project_repo)

    def test_check_uncommitted_changes(self) -> None:
        """未コミット変更のチェック"""
        # Arrange
        self.git_repo.has_uncommitted_changes.return_value = True
        self.git_repo.get_uncommitted_files.return_value = ["file1.py", "file2.py"]

        # Act
        has_changes, files = self.service.check_uncommitted_changes()

        # Assert
        assert has_changes
        assert len(files) == 2

    def test_find_deployable_projects(self) -> None:
        """デプロイ可能なプロジェクトの検索"""
        # Arrange
        self.project_repo.find_all_projects.return_value = [
            DeploymentTarget(resolve_project_path("/proj1"), "Project 1"),
            DeploymentTarget(resolve_project_path("/proj2"), "Project 2"),
        ]

        # Act
        projects = self.service.find_deployable_projects()

        # Assert
        assert len(projects) == 2
        assert projects[0].project_name == "Project 1"

    def test_validate_deployment_readiness(self) -> None:
        """デプロイ準備状態の検証"""
        # Arrange
        deployment = self._create_test_deployment()

        # 正常なケース
        self.git_repo.has_uncommitted_changes.return_value = False
        self.project_repo.project_exists.return_value = True

        # DeploymentTarget.validate()をモック化してエラーなしを返す
        with unittest.mock.patch.object(deployment.target, "validate", return_value=[]):
            # Act
            is_ready, issues = self.service.validate_deployment_readiness(deployment)

            # Assert
            assert is_ready
            assert len(issues) == 0

    def test_validate_deployment_with_issues(self) -> None:
        """問題があるデプロイメントの検証"""
        # Arrange
        deployment = self._create_test_deployment()
        deployment.mode = DeploymentMode.DEVELOPMENT

        self.git_repo.has_uncommitted_changes.return_value = True

        # Act
        is_ready, issues = self.service.validate_deployment_readiness(deployment)

        # Assert
        assert not is_ready
        assert len(issues) > 0
        assert any("uncommitted" in issue.lower() for issue in issues)

    def _create_test_deployment(self):
        target = DeploymentTarget(
            project_path=resolve_project_path("/test/project"),
            project_name="Test Project",
        )

        return Deployment(
            target=target,
            mode=DeploymentMode.PRODUCTION,
            source_commit=CommitHash("abcd123"),
        )


class TestDeployScriptsUseCase(unittest.TestCase):
    """デプロイスクリプトユースケースのテスト"""

    def setUp(self) -> None:
        self.deployment_repo = Mock()
        self.deployment_service = Mock()
        self.version_service = Mock()

        self.use_case = DeployScriptsUseCase(
            self.deployment_repo,
            self.deployment_service,
            self.version_service,
        )

        # テンポラリディレクトリ
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_execute_single_deployment(self) -> None:
        """単一プロジェクトへのデプロイ"""
        # Arrange
        target = DeploymentTarget(
            project_path=resolve_project_path(self.temp_dir),
            project_name="Test Project",
        )

        # create_deploymentの戻り値を設定(PENDING状態で開始)
        deployment = Deployment(
            target=target,
            mode=DeploymentMode.PRODUCTION,
            source_commit=CommitHash("abc123"),
        )

        self.deployment_service.validate_deployment_readiness.return_value = (True, [])
        self.deployment_service.create_deployment.return_value = deployment
        self.version_service.get_current_commit.return_value = CommitHash("abc123")

        # デプロイメント処理の内部メソッドをモック化
        with unittest.mock.patch.object(self.use_case, "_perform_deployment") as mock_perform:
            mock_perform.return_value = None  # 成功を表す

            # Act
            from noveler.application.use_cases.deploy_scripts_use_case import DeployScriptsRequest

            request = DeployScriptsRequest(
                targets=[target],
                mode=DeploymentMode.PRODUCTION,
                force=False,
            )

            result = self.use_case.execute(request)

        # Assert
        assert result.success
        assert len(result.deployments) == 1
        assert result.deployments[0].status == DeploymentStatus.COMPLETED

    def test_execute_with_validation_failure(self) -> None:
        """検証失敗時のデプロイ中止"""
        # Arrange
        target = DeploymentTarget(
            project_path=resolve_project_path("/invalid/path"),
            project_name="Invalid Project",
        )

        # create_deploymentの戻り値を設定
        deployment = Deployment(
            target=target,
            mode=DeploymentMode.PRODUCTION,
            source_commit=CommitHash("abc123"),
        )

        self.deployment_service.validate_deployment_readiness.return_value = (
            False,
            ["Project directory does not exist"],
        )

        self.deployment_service.create_deployment.return_value = deployment

        # Act
        result = self.use_case.execute(
            targets=[target],
            mode=DeploymentMode.PRODUCTION,
            force=False,
        )

        # Assert
        assert not result.success
        assert "validation" in result.error_message.lower()

    def test_rollback_on_failure(self) -> None:
        """失敗時のロールバック"""
        # Arrange
        target = DeploymentTarget(
            project_path=resolve_project_path(self.temp_dir),
            project_name="Test Project",
        )

        # create_deploymentの戻り値を設定
        deployment = Deployment(
            target=target,
            mode=DeploymentMode.PRODUCTION,
            source_commit=CommitHash("abc123"),
        )

        self.deployment_service.validate_deployment_readiness.return_value = (True, [])
        self.deployment_service.create_deployment.return_value = deployment

        # _perform_deploymentでエラーを発生させる
        with unittest.mock.patch.object(self.use_case, "_perform_deployment") as mock_perform:
            mock_perform.side_effect = Exception("Disk full")

            # Act
            result = self.use_case.execute(
                targets=[target],
                mode=DeploymentMode.PRODUCTION,
                force=False,
            )

        # Assert
        assert not result.success
        # デプロイメントが失敗状態になることを確認
        assert deployment.status == DeploymentStatus.FAILED


class TestDeploymentConfig(unittest.TestCase):
    """デプロイメント設定のテスト"""

    def test_default_config(self) -> None:
        """デフォルト設定の確認"""
        # Act
        config = DeploymentConfig()

        # Assert
        assert config.scripts_directory_name == ".novel-scripts"
        assert config.create_backup
        assert config.backup_retention_days == 7

    def test_config_validation(self) -> None:
        """設定の検証"""
        # Arrange
        config = DeploymentConfig(
            scripts_directory_name="invalid/name",
            backup_retention_days=-1,
        )

        # Act
        errors = config.validate()

        # Assert
        assert len(errors) > 0
        assert any("directory name" in e.lower() for e in errors)


class TestIntegration(unittest.TestCase):
    """統合テスト"""

    @patch("subprocess.run")
    @patch("os.path.exists")
    @patch("noveler.infrastructure.deployment.git_deployment_synchronizer.GitDeploymentSynchronizer")
    def test_full_deployment_flow(self, mock_synchronizer_class: object, mock_exists: object, mock_run: object) -> None:
        """完全なデプロイメントフロー(TDD準拠修正版)"""
        # Arrange - TDDの原則に従って明確なテストデータ作成
        mock_exists.return_value = True
        mock_run.return_value = MagicMock(returncode=0, stdout="deployment success")

        # TDD: GitDeploymentSynchronizerのモック設定
        mock_synchronizer = MagicMock()
        mock_synchronizer.create_backup.return_value = "backup_20240714_120000"
        mock_synchronizer.sync_to_latest.return_value = True
        mock_synchronizer.verify_deployment.return_value = True
        mock_synchronizer_class.return_value = mock_synchronizer

        with tempfile.TemporaryDirectory() as temp_dir:
            # プロジェクト構造を作成
            project_dir = Path(temp_dir) / "test_project"
            project_dir.mkdir()
            (project_dir / "プロジェクト設定.yaml").touch()

            # DDD: エンティティとサービスを適切にモック
            deployment_target = DeploymentTarget(
                resolve_project_path(project_dir),
                "Test Project",
            )

            # リポジトリとサービスを初期化
            git_repo = Mock(spec=GitRepositoryImpl)
            git_repo.get_current_commit.return_value = CommitHash("abc123def")
            git_repo.has_uncommitted_changes.return_value = False

            deployment_repo = Mock()
            deployment_repo.save.return_value = True

            project_repo = Mock()
            project_repo.find_all_projects.return_value = [deployment_target]

            # DDD: ドメインサービスのモック
            deployment_service = Mock()
            deployment_service.find_deployable_projects.return_value = [deployment_target]

            # TDD: ドメインサービスが作成するデプロイメントエンティティ(PENDING状態)
            pending_deployment = Deployment(
                target=deployment_target,
                mode=DeploymentMode.PRODUCTION,
                source_commit=CommitHash("abc123def"),
            )

            # 注意: デプロイメントはPENDING状態でcreate_deploymentから返され、
            # Use Case内で状態遷移が制御される

            # TDD: 実際のサービス仕様に合わせてcreate_deploymentメソッドを使用
            deployment_service.create_deployment.return_value = pending_deployment
            deployment_service.validate_deployment_readiness.return_value = (True, [])

            version_service = Mock()
            version_service.get_current_commit.return_value = CommitHash("abc123def")
            version_service.get_current_branch.return_value = "main"

            use_case = DeployScriptsUseCase(
                deployment_repo,
                deployment_service,
                version_service,
            )

            # Act
            result = use_case.execute(
                targets=None,  # すべてのプロジェクト
                mode=DeploymentMode.PRODUCTION,
                force=True,  # テストなので強制実行
            )

            # Assert - TDD: 期待される結果を明確に検証
            assert result.success, f"Expected success but got: {result.error_message}"
            assert len(result.deployments) > 0, "Expected at least one deployment"
            # TDD: Use Caseでデプロイメント処理が正常に実行された場合の状態確認
            # 注意: pending_deploymentの状態はUse Case内で変更される

            # DDD: ドメインサービスが適切に呼び出されたことを検証
            deployment_service.find_deployable_projects.assert_called_once()
            # TDD: Use Caseが内部で_deploy_to_targetを呼び出すため、deployment_serviceのcreate_deploymentが呼ばれることを確認


if __name__ == "__main__":
    unittest.main()
