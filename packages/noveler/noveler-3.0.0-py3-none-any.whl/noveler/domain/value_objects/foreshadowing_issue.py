"""Domain.value_objects.foreshadowing_issue
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""
伏線検知結果の値オブジェクト
SPEC-FORESHADOWING-001準拠のドメインモデル
"""


from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


class ForeshadowingIssueType(Enum):
    """伏線問題のタイプ"""

    MISSING_PLANTING = "missing_planting"  # 仕込み漏れ
    MISSING_RESOLUTION = "missing_resolution"  # 回収漏れ
    STATUS_MISMATCH = "status_mismatch"  # ステータス不整合


class ForeshadowingSeverity(Enum):
    """伏線問題の重要度"""

    CRITICAL = "critical"  # 回収漏れ(必ず修正)
    HIGH = "high"  # 重要度4-5の仕込み漏れ
    MEDIUM = "medium"  # 重要度1-3の仕込み漏れ
    LOW = "low"  # 軽微な問題


@dataclass(frozen=True)
class ForeshadowingIssue:
    """伏線問題の値オブジェクト"""

    foreshadowing_id: str
    issue_type: ForeshadowingIssueType
    severity: ForeshadowingSeverity
    episode_number: int
    message: str
    expected_content: str = ""
    suggestion: str = ""

    def __post_init__(self) -> None:
        if not self.foreshadowing_id:
            msg = "伏線IDは必須です"
            raise ValueError(msg)
        if not self.foreshadowing_id.startswith("F"):
            msg = "伏線IDは'F'で始まる必要があります"
            raise ValueError(msg)
        if self.episode_number < 1:
            msg = "エピソード番号は1以上である必要があります"
            raise ValueError(msg)
        if not self.message:
            msg = "メッセージは必須です"
            raise ValueError(msg)

    def is_critical(self) -> bool:
        """クリティカルな問題かどうか"""
        return self.severity == ForeshadowingSeverity.CRITICAL

    def is_planting_issue(self) -> bool:
        """仕込み関連の問題かどうか"""
        return self.issue_type == ForeshadowingIssueType.MISSING_PLANTING

    def is_resolution_issue(self) -> bool:
        """回収関連の問題かどうか"""
        return self.issue_type == ForeshadowingIssueType.MISSING_RESOLUTION

    def format_for_display(self) -> str:
        """表示用フォーマット"""
        severity_icon = {
            ForeshadowingSeverity.CRITICAL: "🚨",
            ForeshadowingSeverity.HIGH: "⚠️",
            ForeshadowingSeverity.MEDIUM: "💡",
            ForeshadowingSeverity.LOW: "ℹ️",
        }

        type_icon = {
            ForeshadowingIssueType.MISSING_PLANTING: "🔍",
            ForeshadowingIssueType.MISSING_RESOLUTION: "🎯",
            ForeshadowingIssueType.STATUS_MISMATCH: "🔄",
        }

        return f"{severity_icon[self.severity]} {type_icon[self.issue_type]} {self.foreshadowing_id}: {self.message}"


@dataclass(frozen=True)
class ForeshadowingDetectionResult:
    """伏線検知結果の値オブジェクト"""

    episode_number: int
    issues: list[ForeshadowingIssue]
    total_foreshadowing_checked: int
    detection_timestamp: datetime

    def __post_init__(self) -> None:
        if self.episode_number < 1:
            msg = "エピソード番号は1以上である必要があります"
            raise ValueError(msg)
        if self.total_foreshadowing_checked < 0:
            msg = "チェック対象数は0以上である必要があります"
            raise ValueError(msg)

    def has_issues(self) -> bool:
        """問題が存在するかどうか"""
        return len(self.issues) > 0

    def has_critical_issues(self) -> bool:
        """クリティカルな問題が存在するかどうか"""
        return any(issue.is_critical() for issue in self.issues)

    def get_issues_by_severity(self, severity: ForeshadowingSeverity) -> list[ForeshadowingIssue]:
        """重要度別の問題取得"""
        return [issue for issue in self.issues if issue.severity == severity]

    def get_planting_issues(self) -> list[ForeshadowingIssue]:
        """仕込み関連の問題取得"""
        return [issue for issue in self.issues if issue.is_planting_issue()]

    def get_resolution_issues(self) -> list[ForeshadowingIssue]:
        """回収関連の問題取得"""
        return [issue for issue in self.issues if issue.is_resolution_issue()]

    def format_summary(self) -> str:
        """サマリー表示用フォーマット"""
        if not self.has_issues():
            return f"✅ エピソード{self.episode_number}: 伏線チェック問題なし ({self.total_foreshadowing_checked}件チェック済み)"

        critical_count = len(self.get_issues_by_severity(ForeshadowingSeverity.CRITICAL))
        high_count = len(self.get_issues_by_severity(ForeshadowingSeverity.HIGH))
        medium_count = len(self.get_issues_by_severity(ForeshadowingSeverity.MEDIUM))

        summary_parts = []
        if critical_count > 0:
            summary_parts.append(f"🚨 クリティカル: {critical_count}件")
        if high_count > 0:
            summary_parts.append(f"⚠️ 高: {high_count}件")
        if medium_count > 0:
            summary_parts.append(f"💡 中: {medium_count}件")

        return f"❌ エピソード{self.episode_number}: {', '.join(summary_parts)}"


@dataclass(frozen=True)
class ForeshadowingValidationConfig:
    """伏線検証設定の値オブジェクト"""

    enable_planting_check: bool = True
    enable_resolution_check: bool = True
    enable_interactive_confirmation: bool = True
    auto_update_status: bool = False
    min_importance_for_high_severity: int = 4

    def __post_init__(self) -> None:
        if self.min_importance_for_high_severity < 1 or self.min_importance_for_high_severity > 5:
            msg = "最小重要度は1-5の範囲である必要があります"
            raise ValueError(msg)
