#!/usr/bin/env python3
"""デプロイメントエンティティのテスト

TDD+DDD原則に基づく包括的なテストスイート


仕様書: SPEC-UNIT-TEST
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from noveler.domain.deployment.entities import (
    Deployment,
    DeploymentHistory,
    DeploymentMode,
    DeploymentStatus,
    DeploymentTarget,
    ScriptVersion,
)
from noveler.domain.deployment.value_objects import CommitHash, ProjectPath
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class TestDeploymentTarget:
    """DeploymentTargetのテスト"""

    @pytest.mark.spec("SPEC-DEPLOYMENT_ENTITIES-DEPLOYMENT_TARGET_CR")
    def test_deployment_target_creation(self) -> None:
        """デプロイメント対象の作成"""
        # Arrange
        project_path = ProjectPath("/test/project")
        project_name = "test-project"

        # Act
        target = DeploymentTarget(project_path=project_path, project_name=project_name)

        # Assert
        assert target.project_path == project_path
        assert target.project_name == project_name

    @pytest.mark.spec("SPEC-DEPLOYMENT_ENTITIES-DEPLOYMENT_TARGET_BA")
    def test_deployment_target_basic_properties(self) -> None:
        """デプロイメント対象の基本プロパティ"""
        # Arrange
        project_path = ProjectPath("/test/project")
        project_name = "test-project"

        # Act
        target = DeploymentTarget(project_path=project_path, project_name=project_name)

        # Assert
        assert target.project_path == project_path
        assert target.project_name == project_name
        assert str(target.project_path) == "/test/project"


class TestDeployment:
    """Deploymentエンティティのテスト"""

    def create_sample_deployment(self, status=DeploymentStatus.PENDING) -> Deployment:
        """サンプルデプロイメントを作成"""
        target = DeploymentTarget(project_path=ProjectPath("/test/project"), project_name="test-project")

        return Deployment(
            target=target,
            mode=DeploymentMode.PRODUCTION,
            source_commit=CommitHash("abc123def456"),
            status=status,
        )

    @pytest.mark.spec("SPEC-DEPLOYMENT_ENTITIES-DEPLOYMENT_CREATION_")
    def test_deployment_creation_with_defaults(self) -> None:
        """デフォルト値でのデプロイメント作成"""
        # Arrange
        target = DeploymentTarget(project_path=ProjectPath("/test/project"), project_name="test-project")

        # Act
        deployment = Deployment(target=target, mode=DeploymentMode.PRODUCTION, source_commit=CommitHash("abc123def456"))

        # Assert
        assert deployment.target == target
        assert deployment.mode == DeploymentMode.PRODUCTION
        assert deployment.source_commit.value == "abc123def456"
        assert deployment.status == DeploymentStatus.PENDING
        assert deployment.error_message is None
        assert deployment.completed_at is None
        assert isinstance(deployment.id, str)
        assert isinstance(deployment.timestamp, datetime)

    @pytest.mark.spec("SPEC-DEPLOYMENT_ENTITIES-DEPLOYMENT_START_SUC")
    def test_deployment_start_success(self) -> None:
        """デプロイメント開始成功"""
        # Arrange
        deployment = self.create_sample_deployment(DeploymentStatus.PENDING)

        # Act
        deployment.start()

        # Assert
        assert deployment.status == DeploymentStatus.IN_PROGRESS

    @pytest.mark.spec("SPEC-DEPLOYMENT_ENTITIES-DEPLOYMENT_START_INV")
    def test_deployment_start_invalid_status(self) -> None:
        """無効なステータスからのデプロイメント開始"""
        # Arrange
        deployment = self.create_sample_deployment(DeploymentStatus.COMPLETED)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            deployment.start()
        assert "Cannot start deployment in" in str(exc_info.value)

    @pytest.mark.spec("SPEC-DEPLOYMENT_ENTITIES-DEPLOYMENT_COMPLETE_")
    def test_deployment_complete_success(self) -> None:
        """デプロイメント完了成功"""
        # Arrange
        deployment = self.create_sample_deployment(DeploymentStatus.IN_PROGRESS)

        # Act
        deployment.complete()

        # Assert
        assert deployment.status == DeploymentStatus.COMPLETED
        assert deployment.completed_at is not None
        assert isinstance(deployment.completed_at, datetime)

    @pytest.mark.spec("SPEC-DEPLOYMENT_ENTITIES-DEPLOYMENT_COMPLETE_")
    def test_deployment_complete_invalid_status(self) -> None:
        """無効なステータスからのデプロイメント完了"""
        # Arrange
        deployment = self.create_sample_deployment(DeploymentStatus.PENDING)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            deployment.complete()
        assert "Cannot complete deployment in" in str(exc_info.value)

    @pytest.mark.spec("SPEC-DEPLOYMENT_ENTITIES-DEPLOYMENT_FAIL_FROM")
    def test_deployment_fail_from_pending(self) -> None:
        """PENDINGからのデプロイメント失敗"""
        # Arrange
        deployment = self.create_sample_deployment(DeploymentStatus.PENDING)
        error_message = "Template not found"

        # Act
        deployment.fail(error_message)

        # Assert
        assert deployment.status == DeploymentStatus.FAILED
        assert deployment.error_message == error_message
        assert deployment.completed_at is not None

    @pytest.mark.spec("SPEC-DEPLOYMENT_ENTITIES-DEPLOYMENT_FAIL_FROM")
    def test_deployment_fail_from_in_progress(self) -> None:
        """IN_PROGRESSからのデプロイメント失敗"""
        # Arrange
        deployment = self.create_sample_deployment(DeploymentStatus.IN_PROGRESS)
        error_message = "Network error"

        # Act
        deployment.fail(error_message)

        # Assert
        assert deployment.status == DeploymentStatus.FAILED
        assert deployment.error_message == error_message
        assert deployment.completed_at is not None

    @pytest.mark.spec("SPEC-DEPLOYMENT_ENTITIES-DEPLOYMENT_FAIL_INVA")
    def test_deployment_fail_invalid_status(self) -> None:
        """無効なステータスからのデプロイメント失敗"""
        # Arrange
        deployment = self.create_sample_deployment(DeploymentStatus.COMPLETED)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            deployment.fail("Error message")
        assert "Cannot fail deployment in" in str(exc_info.value)

    @pytest.mark.spec("SPEC-DEPLOYMENT_ENTITIES-DEPLOYMENT_VALIDATE_")
    def test_deployment_validate_production_mode(self) -> None:
        """本番モードのデプロイメント検証"""
        # Arrange
        deployment = self.create_sample_deployment()
        deployment.mode = DeploymentMode.PRODUCTION

        # Mock target validation
        with patch.object(deployment.target, "validate", return_value=[]):
            # Act
            warnings = deployment.validate()

            # Assert
            assert len(warnings) == 0

    @pytest.mark.spec("SPEC-DEPLOYMENT_ENTITIES-DEPLOYMENT_VALIDATE_")
    def test_deployment_validate_development_mode(self) -> None:
        """開発モードのデプロイメント検証"""
        # Arrange
        deployment = self.create_sample_deployment()
        deployment.mode = DeploymentMode.DEVELOPMENT

        # Mock target validation
        with patch.object(deployment.target, "validate", return_value=[]):
            # Act
            warnings = deployment.validate()

            # Assert
            assert len(warnings) == 1
            assert "development mode" in warnings[0]

    @pytest.mark.spec("SPEC-DEPLOYMENT_ENTITIES-DEPLOYMENT_VALIDATE_")
    def test_deployment_validate_with_target_errors(self) -> None:
        """ターゲットエラーがあるデプロイメント検証"""
        # Arrange
        deployment = self.create_sample_deployment()

        # Mock target validation with errors
        target_errors = ["Directory not found", "Permission denied"]
        with patch.object(deployment.target, "validate", return_value=target_errors):
            # Act
            warnings = deployment.validate()

            # Assert
            assert len(warnings) == 2
            assert "Directory not found" in warnings
            assert "Permission denied" in warnings

    @pytest.mark.spec("SPEC-DEPLOYMENT_ENTITIES-DEPLOYMENT_DURATION_")
    def test_deployment_duration_calculation(self) -> None:
        """デプロイメント時間計算"""
        # Arrange
        deployment = self.create_sample_deployment(DeploymentStatus.IN_PROGRESS)
        start_time = project_now().datetime
        deployment.timestamp = start_time

        # Act
        deployment.complete()

        # Assert
        duration = deployment.duration
        assert duration is not None
        assert duration > 0
        assert duration < 1.0  # 実行時間は1秒未満であるべき

    @pytest.mark.spec("SPEC-DEPLOYMENT_ENTITIES-DEPLOYMENT_DURATION_")
    def test_deployment_duration_not_completed(self) -> None:
        """未完了デプロイメントの時間計算"""
        # Arrange
        deployment = self.create_sample_deployment(DeploymentStatus.IN_PROGRESS)

        # Act
        duration = deployment.duration

        # Assert
        assert duration is None

    @pytest.mark.spec("SPEC-DEPLOYMENT_ENTITIES-DEPLOYMENT_WORKFLOW_")
    def test_deployment_workflow_cycle(self) -> None:
        """デプロイメントワークフローサイクル"""
        # Arrange
        deployment = self.create_sample_deployment(DeploymentStatus.PENDING)

        # Act & Assert: 開始
        deployment.start()
        assert deployment.status == DeploymentStatus.IN_PROGRESS

        # Act & Assert: 完了
        deployment.complete()
        assert deployment.status == DeploymentStatus.COMPLETED
        assert deployment.completed_at is not None

        # 完了後の時間計算
        duration = deployment.duration
        assert duration is not None
        assert duration >= 0


class TestScriptVersion:
    """ScriptVersionのテスト"""

    @pytest.mark.spec("SPEC-DEPLOYMENT_ENTITIES-SCRIPT_VERSION_CREAT")
    def test_script_version_creation(self) -> None:
        """スクリプトバージョンの作成"""
        # Arrange
        commit_hash = CommitHash("abc123def456")
        timestamp = project_now().datetime
        deployed_by = "test-user"

        # Act
        version = ScriptVersion(commit_hash=commit_hash, timestamp=timestamp, deployed_by=deployed_by)

        # Assert
        assert version.commit_hash == commit_hash
        assert version.timestamp == timestamp
        assert version.deployed_by == deployed_by
        assert version.branch is None
        assert version.mode == DeploymentMode.PRODUCTION
        assert version.deployment_id is None

    @pytest.mark.spec("SPEC-DEPLOYMENT_ENTITIES-SCRIPT_VERSION_IS_NE")
    def test_script_version_is_newer_than(self) -> None:
        """バージョンの新しさ比較"""
        # Arrange
        old_time = project_now().datetime - timedelta(hours=1)
        new_time = project_now().datetime

        old_version = ScriptVersion(commit_hash=CommitHash("abc123"), timestamp=old_time, deployed_by="user1")

        new_version = ScriptVersion(commit_hash=CommitHash("def456"), timestamp=new_time, deployed_by="user2")

        # Act & Assert
        assert new_version.is_newer_than(old_version)
        assert not old_version.is_newer_than(new_version)

    @pytest.mark.spec("SPEC-DEPLOYMENT_ENTITIES-SCRIPT_VERSION_GENER")
    def test_script_version_generate_version_info_minimal(self) -> None:
        """最小構成のバージョン情報生成"""
        # Arrange
        version = ScriptVersion(
            commit_hash=CommitHash("abc123def456"),
            timestamp=datetime(2024, 7, 16, 10, 30, 0, tzinfo=JST),
            deployed_by="test-user",
        )

        # Act
        info = version.generate_version_info()

        # Assert
        assert "Deployed: 2024-07-16 10:30:00" in info
        assert "Mode: PRODUCTION" in info
        assert "Git Commit: abc123d" in info  # short hash
        assert "Deployed By: test-user" in info
        assert "Git Branch:" not in info
        assert "Deployment ID:" not in info

    @pytest.mark.spec("SPEC-DEPLOYMENT_ENTITIES-SCRIPT_VERSION_GENER")
    def test_script_version_generate_version_info_full(self) -> None:
        """完全構成のバージョン情報生成"""
        # Arrange
        version = ScriptVersion(
            commit_hash=CommitHash("abc123def456"),
            timestamp=datetime(2024, 7, 16, 10, 30, 0, tzinfo=JST),
            deployed_by="test-user",
            branch="main",
            mode=DeploymentMode.DEVELOPMENT,
            deployment_id="deploy-123",
        )

        # Act
        info = version.generate_version_info()

        # Assert
        assert "Deployed: 2024-07-16 10:30:00" in info
        assert "Mode: DEVELOPMENT" in info
        assert "Git Commit: abc123d" in info
        assert "Deployed By: test-user" in info
        assert "Git Branch: main" in info
        assert "Deployment ID: deploy-123" in info


class TestDeploymentHistory:
    """DeploymentHistoryのテスト"""

    def create_sample_deployment_history(self) -> DeploymentHistory:
        """サンプルデプロイメント履歴を作成"""
        project_path = ProjectPath("/test/project")
        return DeploymentHistory(project_path=project_path)

    def create_sample_deployment_for_history(self, timestamp: datetime | None = None) -> Deployment:
        """履歴用のサンプルデプロイメントを作成"""
        if timestamp is None:
            timestamp = project_now().datetime

        target = DeploymentTarget(project_path=ProjectPath("/test/project"), project_name="test-project")

        return Deployment(
            target=target,
            mode=DeploymentMode.PRODUCTION,
            source_commit=CommitHash("abc123def456"),
            timestamp=timestamp,
        )

    @pytest.mark.spec("SPEC-DEPLOYMENT_ENTITIES-DEPLOYMENT_HISTORY_C")
    def test_deployment_history_creation(self) -> None:
        """デプロイメント履歴の作成"""
        # Arrange
        project_path = ProjectPath("/test/project")

        # Act
        history = DeploymentHistory(project_path=project_path)

        # Assert
        assert history.project_path == project_path
        assert len(history.deployments) == 0

    @pytest.mark.spec("SPEC-DEPLOYMENT_ENTITIES-DEPLOYMENT_HISTORY_A")
    def test_deployment_history_add_deployment(self) -> None:
        """デプロイメント履歴への追加"""
        # Arrange
        history = self.create_sample_deployment_history()
        deployment = self.create_sample_deployment_for_history()

        # Act
        history.add_deployment(deployment)

        # Assert
        assert len(history.deployments) == 1
        assert history.deployments[0] == deployment

    @pytest.mark.spec("SPEC-DEPLOYMENT_ENTITIES-DEPLOYMENT_HISTORY_S")
    def test_deployment_history_sorting(self) -> None:
        """デプロイメント履歴のソート"""
        # Arrange
        history = self.create_sample_deployment_history()

        # 時系列順に作成
        old_deployment = self.create_sample_deployment_for_history(project_now().datetime - timedelta(hours=2))
        new_deployment = self.create_sample_deployment_for_history(project_now().datetime - timedelta(hours=1))
        latest_deployment = self.create_sample_deployment_for_history(project_now().datetime)

        # Act: 順序を混ぜて追加
        history.add_deployment(new_deployment)
        history.add_deployment(latest_deployment)
        history.add_deployment(old_deployment)

        # Assert: 最新が最初に来る
        assert history.deployments[0] == latest_deployment
        assert history.deployments[1] == new_deployment
        assert history.deployments[2] == old_deployment

    @pytest.mark.spec("SPEC-DEPLOYMENT_ENTITIES-DEPLOYMENT_HISTORY_G")
    def test_deployment_history_get_latest(self) -> None:
        """最新デプロイメントの取得"""
        # Arrange
        history = self.create_sample_deployment_history()

        # Act & Assert: 空の履歴
        assert history.get_latest() is None

        # Arrange: デプロイメント追加
        deployment = self.create_sample_deployment_for_history()
        history.add_deployment(deployment)

        # Act & Assert: 最新を取得
        latest = history.get_latest()
        assert latest == deployment

    @pytest.mark.spec("SPEC-DEPLOYMENT_ENTITIES-DEPLOYMENT_HISTORY_G")
    def test_deployment_history_get_successful_deployments(self) -> None:
        """成功したデプロイメントの取得"""
        # Arrange
        history = self.create_sample_deployment_history()

        # 成功したデプロイメント
        successful1 = self.create_sample_deployment_for_history()
        successful1.status = DeploymentStatus.COMPLETED

        successful2 = self.create_sample_deployment_for_history()
        successful2.status = DeploymentStatus.COMPLETED

        # 失敗したデプロイメント
        failed = self.create_sample_deployment_for_history()
        failed.status = DeploymentStatus.FAILED

        # 進行中のデプロイメント
        in_progress = self.create_sample_deployment_for_history()
        in_progress.status = DeploymentStatus.IN_PROGRESS

        # Act
        history.add_deployment(successful1)
        history.add_deployment(failed)
        history.add_deployment(successful2)
        history.add_deployment(in_progress)

        successful_deployments = history.get_successful_deployments()

        # Assert
        assert len(successful_deployments) == 2
        assert successful1 in successful_deployments
        assert successful2 in successful_deployments
        assert failed not in successful_deployments
        assert in_progress not in successful_deployments

    @pytest.mark.spec("SPEC-DEPLOYMENT_ENTITIES-DEPLOYMENT_HISTORY_C")
    def test_deployment_history_cleanup_old_deployments(self) -> None:
        """古いデプロイメント履歴のクリーンアップ"""
        # Arrange
        history = self.create_sample_deployment_history()

        # 15個のデプロイメントを作成
        deployments = []
        for i in range(15):
            deployment = self.create_sample_deployment_for_history(project_now().datetime - timedelta(hours=i))
            deployments.append(deployment)
            history.add_deployment(deployment)

        # Act: 10個だけ保持
        removed = history.cleanup_old_deployments(keep_count=10)

        # Assert
        assert len(history.deployments) == 10
        assert len(removed) == 5

        # 最新の10個が残っているか確認
        for i in range(10):
            assert deployments[i] in history.deployments

    @pytest.mark.spec("SPEC-DEPLOYMENT_ENTITIES-DEPLOYMENT_HISTORY_C")
    def test_deployment_history_cleanup_no_excess(self) -> None:
        """クリーンアップ不要なデプロイメント履歴"""
        # Arrange
        history = self.create_sample_deployment_history()

        # 5個のデプロイメントを作成
        for _i in range(5):
            deployment = self.create_sample_deployment_for_history()
            history.add_deployment(deployment)

        # Act: 10個まで保持(5個しかないので変化なし)
        removed = history.cleanup_old_deployments(keep_count=10)

        # Assert
        assert len(history.deployments) == 5
        assert len(removed) == 0

    @pytest.mark.spec("SPEC-DEPLOYMENT_ENTITIES-DEPLOYMENT_HISTORY_C")
    def test_deployment_history_complex_scenario(self) -> None:
        """複雑なデプロイメント履歴シナリオ"""
        # Arrange
        history = self.create_sample_deployment_history()

        # 複数のデプロイメントを追加
        deployments = []
        for i in range(20):
            deployment = self.create_sample_deployment_for_history(project_now().datetime - timedelta(hours=i))

            # ステータスを設定
            if i % 4 == 0:
                deployment.status = DeploymentStatus.COMPLETED
            elif i % 4 == 1:
                deployment.status = DeploymentStatus.FAILED
            elif i % 4 == 2:
                deployment.status = DeploymentStatus.IN_PROGRESS
            else:
                deployment.status = DeploymentStatus.PENDING

            deployments.append(deployment)
            history.add_deployment(deployment)

        # Act & Assert: 成功したデプロイメント
        successful = history.get_successful_deployments()
        assert len(successful) == 5  # 20個中5個が成功

        # Act & Assert: 最新のデプロイメント
        latest = history.get_latest()
        assert latest == deployments[0]

        # Act & Assert: クリーンアップ
        removed = history.cleanup_old_deployments(keep_count=12)
        assert len(history.deployments) == 12
        assert len(removed) == 8

        # 最新の12個が残っているか確認
        for i in range(12):
            assert deployments[i] in history.deployments
