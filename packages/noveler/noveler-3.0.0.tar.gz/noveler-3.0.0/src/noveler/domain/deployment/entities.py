"""Domain.deployment.entities
Where: Domain entities modelling deployment artifacts and status.
What: Defines data structures used when orchestrating deployments.
Why: Provides reusable deployment entity models across the domain.
"""

from __future__ import annotations

from typing import Any

"""デプロイメントドメインのエンティティ

スクリプトのデプロイメントに関するビジネスロジックを含む
"""


import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

if TYPE_CHECKING:
    from datetime import datetime

    from noveler.domain.value_objects import CommitHash, ProjectPath


# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class DeploymentStatus(Enum):
    """デプロイメントステータス"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class DeploymentMode(Enum):
    """デプロイメントモード"""

    PRODUCTION = "production"  # コミット済みの安定版
    DEVELOPMENT = "development"  # 未コミットの開発版


@dataclass
class DeploymentTarget:
    """デプロイメント対象"""

    project_path: ProjectPath
    project_name: str

    def validate(self) -> list[str]:
        """デプロイメント対象の検証"""
        errors: list[Any] = []

        # ドメイン層でのファイルシステムアクセスは避ける
        # 実際の存在チェックはインフラ層で行う
        if not self.project_path.value:
            errors.append("Project path is required")

        if not self.project_name:
            errors.append("Project name is required")

        return errors


@dataclass
class Deployment:
    """デプロイメントエンティティ"""

    target: DeploymentTarget
    mode: DeploymentMode
    source_commit: CommitHash
    timestamp: datetime = field(default_factory=lambda: project_now().datetime)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: DeploymentStatus = DeploymentStatus.PENDING
    error_message: str | None = None
    completed_at: datetime | None = None

    def start(self) -> None:
        """デプロイメントを開始"""
        if self.status != DeploymentStatus.PENDING:
            msg = f"Cannot start deployment in {self.status} status"
            raise ValueError(msg)

        self.status = DeploymentStatus.IN_PROGRESS

    def complete(self) -> None:
        """デプロイメントを完了"""
        if self.status != DeploymentStatus.IN_PROGRESS:
            msg = f"Cannot complete deployment in {self.status} status"
            raise ValueError(msg)

        self.status = DeploymentStatus.COMPLETED
        self.completed_at = project_now().datetime

    def fail(self, error_message: str) -> None:
        """デプロイメントを失敗としてマーク"""
        if self.status not in [DeploymentStatus.PENDING, DeploymentStatus.IN_PROGRESS]:
            msg = f"Cannot fail deployment in {self.status} status"
            raise ValueError(msg)

        self.status = DeploymentStatus.FAILED
        self.error_message = error_message
        self.completed_at = project_now().datetime

    def validate(self) -> list[str]:
        """デプロイメントの検証"""
        warnings = []

        # 開発モードの警告
        if self.mode == DeploymentMode.DEVELOPMENT:
            warnings.append("Deploying in development mode - uncommitted changes will be included")

        # ターゲットの検証
        target_errors = self.target.validate()
        warnings.extend(target_errors)

        return warnings

    @property
    def duration(self) -> float | None:
        """デプロイメント時間(秒)"""
        if self.completed_at and self.timestamp:
            return (self.completed_at - self.timestamp).total_seconds()
        return None


@dataclass
class ScriptVersion:
    """デプロイされたスクリプトのバージョン情報"""

    commit_hash: CommitHash
    timestamp: datetime
    deployed_by: str
    branch: str | None = None
    mode: DeploymentMode = DeploymentMode.PRODUCTION
    deployment_id: str | None = None
    changes: list[str] | None = None
    version: str = "1.0.0"

    def is_newer_than(self, other: ScriptVersion) -> bool:
        """他のバージョンより新しいかチェック"""
        return self.timestamp > other.timestamp

    def generate_version_info(self) -> str:
        """バージョン情報文字列を生成"""
        lines = [
            f"Deployed: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Mode: {self.mode.value.upper()}",
            f"Git Commit: {self.commit_hash.short}",
        ]

        if self.branch:
            lines.append(f"Git Branch: {self.branch}")

        if self.deployed_by:
            lines.append(f"Deployed By: {self.deployed_by}")

        if self.deployment_id:
            lines.append(f"Deployment ID: {self.deployment_id}")

        if self.changes:
            lines.append("Changes:")
            lines.extend(f"- {change}" for change in self.changes)

        return "\n".join(lines)


@dataclass
class DeploymentHistory:
    """デプロイメント履歴"""

    project_path: ProjectPath
    deployments: list[Deployment] = field(default_factory=list)
    last_successful_deployment: Deployment | None = None

    # 互換性のためのエイリアス（旧実装は `_project_path` フィールドを公開していた）
    @property
    def _project_path(self) -> ProjectPath:  # pragma: no cover - 単純アクセサ
        return self.project_path

    @_project_path.setter
    def _project_path(self, value: ProjectPath) -> None:  # pragma: no cover - 単純アクセサ
        self.project_path = value

    def add_deployment(self, deployment: Deployment) -> None:
        """デプロイメントを履歴に追加"""
        self.deployments.append(deployment)
        # 最新のものが最初に来るようにソート
        self.deployments.sort(key=lambda d: d.timestamp, reverse=True)
        if deployment.status == DeploymentStatus.COMPLETED:
            self.last_successful_deployment = deployment

    def get_latest(self) -> Deployment | None:
        """最新のデプロイメントを取得"""
        return self.deployments[0] if self.deployments else None

    def get_successful_deployments(self) -> list[Deployment]:
        """成功したデプロイメントのみ取得"""
        return [d for d in self.deployments if d.status == DeploymentStatus.COMPLETED]

    def cleanup_old_deployments(self, keep_count: int) -> list[Deployment]:
        """古いデプロイメント履歴をクリーンアップ"""
        if len(self.deployments) <= keep_count:
            return []

        removed = self.deployments[keep_count:]
        self.deployments = self.deployments[:keep_count]
        return removed
