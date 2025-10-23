"""Domain.entities.backup_session
Where: Domain entity modelling a backup session.
What: Records backup configuration, executions, and statuses.
Why: Supports unified backup management with consistent data.
"""

from __future__ import annotations

"""バックアップセッション集約ルート

B20準拠実装 - AggregateRootパターン（___python-ddd-main参照）
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from noveler.domain.value_objects.project_time import project_now
from noveler.noveler.domain.entities.aggregate_root import AggregateRoot
from noveler.noveler.domain.events.backup_events import BackupSessionCompleted, BackupSessionStarted
from noveler.noveler.domain.value_objects.session_id import SessionId

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(kw_only=True)
class BackupSession(AggregateRoot[SessionId]):
    """バックアップセッション集約ルート

    B20準拠 AggregateRootパターン:
    - 不変性保持（dataclass(frozen=True)は使わず、明示的な変更メソッド）
    - ドメインイベント発行
    - ビジネスルールチェック
    """

    session_id: str
    operation_type: str  # 'analyze' | 'migrate' | 'cleanup' | 'create'
    started_at: datetime
    completed_at: datetime | None = None
    dry_run: bool = True

    # 操作結果
    operations_performed: list[str] = field(default_factory=list)
    errors_encountered: list[str] = field(default_factory=list)

    # メタデータ
    total_files_processed: int = 0
    total_size_processed_mb: float = 0.0

    def __post_init__(self) -> None:
        """初期化後処理 - ドメインイベント発行"""
        super().__post_init__()

        # セッション開始イベント
        self.register_event(
            BackupSessionStarted(
                session_id=self.session_id,
                operation_type=self.operation_type,
                started_at=self.started_at,
                dry_run=self.dry_run,
            )
        )

    def add_operation(self, operation_description: str) -> None:
        """操作記録追加 - ビジネスルール適用"""
        if self.completed_at is not None:
            msg = "完了済みセッションに操作を追加できません"
            raise ValueError(msg)

        self.operations_performed.append(operation_description)

    def add_error(self, error_description: str) -> None:
        """エラー記録追加"""
        self.errors_encountered.append(error_description)

    def update_progress(self, files_processed: int, size_mb: float) -> None:
        """進捗更新"""
        self.total_files_processed += files_processed
        self.total_size_processed_mb += size_mb

    def complete_session(self) -> None:
        """セッション完了 - ドメインイベント発行"""
        if self.completed_at is not None:
            msg = "セッションは既に完了しています"
            raise ValueError(msg)

        self.completed_at = project_now().datetime

        # セッション完了イベント
        self.register_event(
            BackupSessionCompleted(
                session_id=self.session_id,
                completed_at=self.completed_at,
                operations_count=len(self.operations_performed),
                errors_count=len(self.errors_encountered),
                success=len(self.errors_encountered) == 0,
            )
        )

    def is_completed(self) -> bool:
        """完了状態チェック - Functional Core（純粋関数）"""
        return self.completed_at is not None

    def is_successful(self) -> bool:
        """成功状態チェック - Functional Core（純粋関数）"""
        return self.is_completed() and len(self.errors_encountered) == 0

    def get_duration_seconds(self) -> float | None:
        """実行時間取得 - Functional Core（純粋関数）"""
        if not self.is_completed():
            return None

        duration = self.completed_at - self.started_at
        return duration.total_seconds()

    def get_summary(self) -> dict:
        """セッション概要取得 - Functional Core（純粋関数）"""
        return {
            "session_id": self.session_id,
            "operation_type": self.operation_type,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "dry_run": self.dry_run,
            "operations_count": len(self.operations_performed),
            "errors_count": len(self.errors_encountered),
            "total_files_processed": self.total_files_processed,
            "total_size_mb": round(self.total_size_processed_mb, 2),
            "duration_seconds": self.get_duration_seconds(),
            "successful": self.is_successful(),
        }
