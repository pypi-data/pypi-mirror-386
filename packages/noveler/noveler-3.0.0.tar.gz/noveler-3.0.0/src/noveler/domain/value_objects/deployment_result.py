"""デプロイメント結果値オブジェクト."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from noveler.domain.exceptions import ValidationError


class DeploymentStatus(Enum):
    """デプロイメントステータス."""

    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class DeploymentResult:
    """デプロイメント結果値オブジェクト."""

    deployment_id: str
    status: DeploymentStatus
    started_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None
    deployed_files: list[str] | None = None
    rollback_available: bool = False

    def __post_init__(self) -> None:
        """値オブジェクトの不変条件を検証."""
        if self.deployed_files is None:
            object.__setattr__(self, "deployed_files", [])

        self._validate_deployment_id()
        self._validate_timestamps()
        self._validate_error_conditions()

    def _validate_deployment_id(self) -> None:
        """デプロイメントIDの妥当性検証."""
        if not self.deployment_id or not self.deployment_id.strip():
            msg = "deployment_id"
            raise ValidationError(msg, "デプロイメントIDは必須です")

    def _validate_timestamps(self) -> None:
        """タイムスタンプの妥当性検証."""
        if self.completed_at and self.completed_at < self.started_at:
            msg = "completed_at"
            raise ValidationError(msg, "完了時刻は開始時刻より後である必要があります")

    def _validate_error_conditions(self) -> None:
        """エラー条件の妥当性検証."""
        if self.status == DeploymentStatus.FAILED and not self.error_message:
            msg = "error_message"
            raise ValidationError(msg, "失敗ステータスの場合はエラーメッセージが必要です")

    def is_completed(self) -> bool:
        """デプロイメントが完了しているかどうか."""
        return self.status in [DeploymentStatus.SUCCESS, DeploymentStatus.FAILED, DeploymentStatus.CANCELLED]

    def is_successful(self) -> bool:
        """デプロイメントが成功したかどうか."""
        return self.status == DeploymentStatus.SUCCESS

    def get_duration_seconds(self) -> int | None:
        """デプロイメント実行時間を秒単位で取得."""
        if not self.completed_at:
            return None
        return int((self.completed_at - self.started_at).total_seconds())

    def get_summary(self) -> str:
        """デプロイメント結果のサマリーを取得."""
        if self.status == DeploymentStatus.SUCCESS:
            file_count = len(self.deployed_files or [])
            return f"デプロイメント成功: {file_count}ファイルをデプロイ"
        if self.status == DeploymentStatus.FAILED:
            return f"デプロイメント失敗: {self.error_message}"
        if self.status == DeploymentStatus.PENDING:
            return "デプロイメント実行中"
        return "デプロイメントがキャンセルされました"
