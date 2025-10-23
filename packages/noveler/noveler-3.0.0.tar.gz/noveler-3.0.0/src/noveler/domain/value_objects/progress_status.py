#!/usr/bin/env python3
"""進捗ステータス値オブジェクト

進捗状況を表現するドメイン値オブジェクト
"""

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from noveler.domain.value_objects.time_estimation import TimeEstimation


class ProgressStatus(Enum):
    """進捗ステータス"""

    NOT_STARTED = "未開始"
    IN_PROGRESS = "進行中"
    COMPLETED = "完了"
    NEEDS_REVIEW = "要確認"
    BLOCKED = "阻害"

    def emoji(self) -> str:
        """ステータスに対応する絵文字"""
        emoji_map = {
            ProgressStatus.NOT_STARTED: "⚪",
            ProgressStatus.IN_PROGRESS: "🟡",
            ProgressStatus.COMPLETED: "✅",
            ProgressStatus.NEEDS_REVIEW: "⚠️",
            ProgressStatus.BLOCKED: "🚫",
        }
        return emoji_map.get(self, "❓")

    def can_transition_to(self, target_status: "ProgressStatus") -> bool:
        """状態遷移の妥当性チェック"""
        allowed_transitions = {
            ProgressStatus.NOT_STARTED: [ProgressStatus.IN_PROGRESS, ProgressStatus.BLOCKED],
            ProgressStatus.IN_PROGRESS: [ProgressStatus.COMPLETED, ProgressStatus.NEEDS_REVIEW, ProgressStatus.BLOCKED],
            ProgressStatus.COMPLETED: [ProgressStatus.NEEDS_REVIEW],
            ProgressStatus.NEEDS_REVIEW: [ProgressStatus.IN_PROGRESS, ProgressStatus.COMPLETED],
            ProgressStatus.BLOCKED: [ProgressStatus.IN_PROGRESS, ProgressStatus.NOT_STARTED],
        }
        return target_status in allowed_transitions.get(self, [])


@dataclass(frozen=True)
class NextAction:
    """次のアクション値オブジェクト"""

    title: str
    command: str
    time_estimation: "TimeEstimation"
    priority: str = "medium"

    def __post_init__(self) -> None:
        """値の検証"""
        if not self.title.strip():
            msg = "アクションタイトルは必須です"
            raise ValueError(msg)
        if not self.command.strip():
            msg = "実行コマンドは必須です"
            raise ValueError(msg)
        if self.priority not in ["high", "medium", "low"]:
            msg = "優先度は high, medium, low のいずれかである必要があります"
            raise ValueError(msg)

    def display_text(self) -> str:
        """表示用テキスト"""
        return f"{self.title} (所要時間: {self.time_estimation.display_text()})"

    @property
    def description(self) -> str:
        """アクション説明のエイリアス(互換性維持)"""
        return self.title

    @property
    def estimated_time(self) -> "TimeEstimation":
        """所要時間オブジェクトのエイリアス(互換性維持)"""
        return self.time_estimation
