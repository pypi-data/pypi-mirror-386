#!/usr/bin/env python3
"""ファイル品質チェックセッション エンティティ

SPEC-CLAUDE-002に基づく実装
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from noveler.domain.value_objects.file_path import FilePath


class CheckType(Enum):
    """チェックタイプ"""

    SYNTAX = "syntax"
    TYPE_CHECK = "type_check"
    LINT = "lint"
    FORMAT = "format"
    QUALITY = "quality"
    SECURITY = "security"


class CheckStatus(Enum):
    """チェック状態"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class CheckResult:
    """チェック結果"""

    check_type: CheckType
    status: CheckStatus
    message: str
    details: dict[str, Any] | None = None
    execution_time_ms: int = 0
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class FileQualityCheckSession:
    """ファイル品質チェックセッション"""

    file_path: FilePath
    session_id: str
    check_results: list[CheckResult] = field(default_factory=list)
    status: CheckStatus = CheckStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    # テストでのback compatibility用属性
    results: list[Any] = field(default_factory=list)  # テストコードとの互換性用

    def add_check_result(self, result: CheckResult) -> None:
        """チェック結果を追加"""
        self.check_results.append(result)
        self.updated_at = datetime.now(timezone.utc)

        # 全体ステータス更新
        if result.status == CheckStatus.FAILED:
            self.status = CheckStatus.FAILED
        elif all(r.status == CheckStatus.COMPLETED for r in self.check_results):
            self.status = CheckStatus.COMPLETED

    def get_results_by_type(self, check_type: CheckType) -> list[CheckResult]:
        """チェックタイプ別結果取得"""
        return [r for r in self.check_results if r.check_type == check_type]

    def has_failures(self) -> bool:
        """失敗があるかチェック"""
        return any(r.status == CheckStatus.FAILED for r in self.check_results)

    def get_total_execution_time(self) -> int:
        """総実行時間取得（ミリ秒）"""
        return sum(r.execution_time_ms for r in self.check_results)

    def is_completed(self) -> bool:
        """完了状態かチェック"""
        return self.status in [CheckStatus.COMPLETED, CheckStatus.FAILED]

    # テスト互換性メソッド
    def has_errors(self) -> bool:
        """エラーがあるかチェック（テスト互換性）"""
        if self.has_failures():
            return True

        return any(getattr(result, "is_valid", True) is False for result in self.results)

    def get_error_details(self) -> list[dict[str, Any]]:
        """エラー詳細取得（テスト互換性）"""
        errors: list[Any] = []
        for result in self.check_results:
            if result.status == CheckStatus.FAILED:
                errors.append(
                    {
                        "code": result.details.get("code", "UNKNOWN") if result.details else "UNKNOWN",
                        "message": result.message,
                        "line_number": result.details.get("line_number") if result.details else None,
                    }
                )

        # results属性からもエラーを取得（back compatibility）
        for legacy_result in self.results:
            if getattr(legacy_result, "is_valid", True) is False:
                errors.append(
                    {
                        "code": getattr(legacy_result, "error_code", "UNKNOWN"),
                        "message": getattr(legacy_result, "message", ""),
                        "line_number": getattr(legacy_result, "line_number", None),
                    }
                )

        return errors
