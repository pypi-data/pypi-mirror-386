"""Claude連携状態

SPEC-CLAUDE-001に基づくClaude Code連携の状態を表現する値オブジェクト
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from noveler.domain.value_objects.project_time import project_now


@dataclass(frozen=True)
class IntegrationStatus:
    """Claude連携状態

    Claude Code連携システムの現在の状態を表現する値オブジェクト
    """

    is_active: bool
    last_export: datetime | None
    error_count: int
    success_count: int = 0
    last_error_message: str | None = None

    def __post_init__(self) -> None:
        """値の検証"""
        if self.error_count < 0:
            msg = "error_countは0以上である必要があります"
            raise ValueError(msg)

        if self.success_count < 0:
            msg = "success_countは0以上である必要があります"
            raise ValueError(msg)

        if self.last_export and self.last_export > project_now().datetime:
            msg = "last_exportは未来の時刻にできません"
            raise ValueError(msg)

        if self.last_error_message and len(self.last_error_message) > 500:
            msg = "last_error_messageは500文字以下である必要があります"
            raise ValueError(msg)

    @classmethod
    def initial(cls) -> "IntegrationStatus":
        """初期状態作成

        Returns:
            初期状態のIntegrationStatus
        """
        return cls(is_active=False, last_export=None, error_count=0, success_count=0)

    @classmethod
    def active(cls) -> "IntegrationStatus":
        """アクティブ状態作成

        Returns:
            アクティブ状態のIntegrationStatus
        """
        return cls(is_active=True, last_export=None, error_count=0, success_count=0)

    def with_successful_export(self, export_time: datetime | None = None) -> "IntegrationStatus":
        """成功したエクスポートで状態更新

        Args:
            export_time: エクスポート時刻(Noneの場合は現在時刻)

        Returns:
            更新されたIntegrationStatus
        """
        return IntegrationStatus(
            is_active=self.is_active,
            last_export=export_time or project_now().datetime,
            error_count=self.error_count,
            success_count=self.success_count + 1,
            last_error_message=None,  # 成功時はエラーメッセージをクリア
        )

    def with_failed_export(self, error_message: str) -> "IntegrationStatus":
        """失敗したエクスポートで状態更新

        Args:
            error_message: エラーメッセージ

        Returns:
            更新されたIntegrationStatus
        """
        return IntegrationStatus(
            is_active=self.is_active,
            last_export=self.last_export,
            error_count=self.error_count + 1,
            success_count=self.success_count,
            last_error_message=error_message[:500],  # 長さ制限
        )

    def activate(self) -> "IntegrationStatus":
        """連携をアクティベート

        Returns:
            アクティブ化されたIntegrationStatus
        """
        return IntegrationStatus(
            is_active=True,
            last_export=self.last_export,
            error_count=self.error_count,
            success_count=self.success_count,
            last_error_message=self.last_error_message,
        )

    def deactivate(self) -> "IntegrationStatus":
        """連携を非アクティベート

        Returns:
            非アクティブ化されたIntegrationStatus
        """
        return IntegrationStatus(
            is_active=False,
            last_export=self.last_export,
            error_count=self.error_count,
            success_count=self.success_count,
            last_error_message=self.last_error_message,
        )

    def get_success_rate(self) -> float:
        """成功率計算

        Returns:
            成功率(0.0-1.0)
        """
        total = self.success_count + self.error_count
        if total == 0:
            return 1.0  # 実行履歴がない場合は100%とする
        return self.success_count / total

    def has_recent_activity(self, hours: int = 24) -> bool:
        """最近のアクティビティ有無判定

        Args:
            hours: 判定時間(時間)

        Returns:
            指定時間内にアクティビティがあったかどうか
        """
        if not self.last_export:
            return False

        threshold = project_now().datetime - timedelta(hours=hours)
        return self.last_export > threshold

    def is_healthy(self) -> bool:
        """健全性判定

        Returns:
            連携システムが健全かどうか
        """
        # 成功率が80%以上で健全とみなす
        return self.get_success_rate() >= 0.8

    def __str__(self) -> str:
        """文字列表現"""
        status = "アクティブ" if self.is_active else "非アクティブ"
        return f"Claude連携: {status} (成功: {self.success_count}, エラー: {self.error_count})"
