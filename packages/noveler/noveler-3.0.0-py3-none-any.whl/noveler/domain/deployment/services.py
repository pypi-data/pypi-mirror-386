"""Domain.deployment.services
Where: Domain services implementing deployment behaviour.
What: Encapsulates deployment orchestration logic and helper routines.
Why: Centralises deployment logic for reuse by upper layers.
"""

from __future__ import annotations

"""デプロイメントドメインのサービス

複数のエンティティにまたがるビジネスロジック
"""


import getpass
from typing import TYPE_CHECKING

from noveler.domain.deployment.entities import (
    Deployment,
    DeploymentMode,
    DeploymentTarget,
    ScriptVersion,
)
from noveler.domain.deployment.value_objects import DeploymentResult, ProjectPath
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

if TYPE_CHECKING:
    from noveler.domain.deployment.value_objects import CommitHash
    from noveler.domain.repositories.git_repository import GitRepository


# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class DeploymentService:
    """デプロイメントビジネスロジックサービス"""

    def __init__(self, git_repo: GitRepository, project_repo: str) -> None:
        self.git_repo = git_repo
        self.project_repo = project_repo

    def check_uncommitted_changes(self) -> tuple[bool, list[str]]:
        """未コミット変更をチェック"""
        has_changes = self.git_repo.has_uncommitted_changes()
        files = self.git_repo.get_uncommitted_files() if has_changes else []
        return has_changes, files

    def find_deployable_projects(self) -> list[DeploymentTarget]:
        """デプロイ可能なプロジェクトを検索"""
        return self.project_repo.find_all_projects()

    def validate_deployment_readiness(self, deployment: Deployment) -> tuple[bool, list[str]]:
        """デプロイメント準備状態を検証"""
        issues: list[str] = []

        # 未コミット変更のチェック(本番モードの場合のみ)
        if deployment.mode == DeploymentMode.PRODUCTION:
            has_changes, files = self.check_uncommitted_changes()
            if has_changes:
                issues.append(f"Uncommitted changes detected: {', '.join(files[:3])}")
                if len(files) > 3:
                    issues.append(f"... and {len(files) - 3} more files")

        # プロジェクトの存在確認
        if not self.project_repo.project_exists(deployment.target.project_path):
            issues.append("Project directory does not exist")

        # デプロイメント自体の検証
        deployment_warnings = deployment.validate()
        issues.extend(deployment_warnings)

        return len(issues) == 0, issues

    def determine_deployment_mode(self, force_development: bool = False) -> DeploymentMode:
        """デプロイメントモードを決定"""
        if force_development:
            return DeploymentMode.DEVELOPMENT

        has_changes, _ = self.check_uncommitted_changes()
        return DeploymentMode.DEVELOPMENT if has_changes else DeploymentMode.PRODUCTION

    def create_deployment(self, target: DeploymentTarget, mode: DeploymentMode) -> Deployment:
        """デプロイメントエンティティを作成"""
        if mode is None:
            mode = self.determine_deployment_mode()

        current_commit = self.git_repo.get_current_commit()
        current_time = project_now()
        timestamp = getattr(current_time, "datetime", current_time)

        return Deployment(
            target=target,
            mode=mode,
            source_commit=current_commit,
            timestamp=timestamp,
        )


class VersionControlService:
    """バージョン管理サービス"""

    def __init__(self, git_repo: GitRepository) -> None:
        self.git_repo = git_repo

    def get_current_commit(self) -> CommitHash:
        """現在のコミットハッシュを取得"""
        return self.git_repo.get_current_commit()

    def get_current_branch(self) -> str:
        """現在のブランチ名を取得"""
        return self.git_repo.get_current_branch()

    def create_version_info(self, deployment: Deployment) -> ScriptVersion:
        """デプロイメントからバージョン情報を作成"""
        return ScriptVersion(
            commit_hash=deployment.source_commit,
            timestamp=deployment.timestamp,
            deployed_by=getpass.getuser(),
            branch=self.get_current_branch(),
            mode=deployment.mode,
            deployment_id=deployment.id,
        )

    def is_production_ready(self) -> bool:
        """本番デプロイ可能な状態かチェック"""
        return not self.git_repo.has_uncommitted_changes()


class BackupService:
    """バックアップサービス"""

    def should_create_backup(self, target_path: ProjectPath) -> bool:
        """バックアップを作成すべきかチェック"""
        scripts_path = target_path.path / ".novel-scripts"
        return scripts_path.exists()

    def generate_backup_name(self, timestamp) -> str:
        """バックアップディレクトリ名を生成"""
        return f".noveler.backup.{timestamp.strftime('%Y%m%d_%H%M%S')}"

    def calculate_backup_size(self, backup_path: ProjectPath) -> int:
        """バックアップサイズを計算(バイト)"""
        filesystem_path = backup_path.path
        total_size = 0
        for file_path in filesystem_path.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size


class AutoDeploymentService:
    """自動デプロイメントサービス"""

    def __init__(self, git_synchronizer, create_backup: bool = False) -> None:
        self.git_synchronizer = git_synchronizer
        self.create_backup = create_backup

    def check_for_updates(self, project_path: str) -> bool:
        """プロジェクトに更新があるかチェック"""
        try:
            latest_commit = self.git_synchronizer.get_latest_commit()
            deployed_commit = self.git_synchronizer.get_deployed_commit(project_path)

            if deployed_commit is None:
                return True  # 初回デプロイ

            return latest_commit.value != deployed_commit.value
        except Exception:
            return False

    def auto_update(self, target: DeploymentTarget) -> DeploymentResult:
        """自動デプロイメント更新"""

        backup_path = None
        start_time = project_now()
        started_at = getattr(start_time, "datetime", start_time)
        try:
            # バックアップ作成
            if self.create_backup:
                backup_path = self.git_synchronizer.create_backup(target.project_path)

            # 最新バージョンに同期
            success = self.git_synchronizer.sync_to_latest(target.project_path)

            completed_at_value = project_now()
            completed_at = getattr(completed_at_value, "datetime", completed_at_value)

            if success:
                return DeploymentResult(
                    success=True,
                    message=f"Successfully updated {target.project_name}",
                    deployed_files_count=1,
                    backup_created=self.create_backup,
                    backup_path=str(backup_path) if backup_path else None,
                    started_at=started_at,
                    completed_at=completed_at,
                )

            return DeploymentResult(
                success=False,
                message=f"Failed to sync {target.project_name}",
                error_message=f"Failed to sync {target.project_name}",
                started_at=started_at,
                completed_at=completed_at,
            )

        except Exception as e:
            failed_at_value = project_now()
            failed_at = getattr(failed_at_value, "datetime", failed_at_value)
            return DeploymentResult(
                success=False,
                message=f"Auto-update failed: {e!s}",
                error_message=str(e),
                backup_created=False,
                started_at=started_at,
                completed_at=failed_at,
            )
