"""Domain.value_objects.completion_status
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

from __future__ import annotations

"""完成ステータス関連の値オブジェクト

エピソード完成処理で使用するステータスとフェーズ。
"""


from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from noveler.domain.value_objects.quality_score import QualityScore


class WritingPhase(Enum):
    """執筆フェーズ"""

    DRAFT = "draft"
    REVIEW = "review"
    FINAL_CHECK = "final_check"
    PUBLISHED = "published"

    def get_next_phase(self) -> WritingPhase:
        """次のフェーズを取得

        Returns:
            次のフェーズ
        """
        phase_order = [WritingPhase.DRAFT, WritingPhase.REVIEW, WritingPhase.FINAL_CHECK, WritingPhase.PUBLISHED]

        current_index = phase_order.index(self)
        if current_index < len(phase_order) - 1:
            return phase_order[current_index + 1]
        return self  # 最終フェーズの場合は変わらない

    def is_publishable(self) -> bool:
        """公開可能かどうか

        Returns:
            公開可能な場合True
        """
        return self == WritingPhase.PUBLISHED

    def to_japanese(self) -> str:
        """日本語表記を取得

        Returns:
            日本語表記
        """
        japanese_names = {
            WritingPhase.DRAFT: "下書き",
            WritingPhase.REVIEW: "推敲",
            WritingPhase.FINAL_CHECK: "最終チェック",
            WritingPhase.PUBLISHED: "公開済み",
        }
        return japanese_names.get(self, self.value)


class CompletionStatusType(str, Enum):
    """完成ステータスタイプ"""

    INITIALIZED = "initialized"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class QualityCheckResult:
    """品質チェック結果"""

    score: QualityScore
    passed: bool
    issues: list[str]

    @classmethod
    def from_score(cls, score: QualityScore, threshold: float) -> QualityCheckResult:
        """スコアから品質チェック結果を作成

        Args:
            score: 品質スコア
            threshold: 合格基準(デフォルト70点)

        Returns:
            品質チェック結果
        """
        passed = score.value >= threshold
        issues = []

        if not passed:
            if score.value < 50:
                issues.append("品質が著しく低い状態です")
            elif score.value < 70:
                issues.append("品質の改善が必要です")

        return cls(score=score, passed=passed, issues=issues)

    def is_excellent(self) -> bool:
        """優秀な品質かどうか

        Returns:
            90点以上の場合True
        """
        return self.score.value >= 90

    def get_summary_message(self) -> str:
        """サマリーメッセージを取得

        Returns:
            品質チェックのサマリー
        """
        if self.is_excellent():
            return f"優秀な品質です({self.score.value}点)"
        if self.passed:
            return f"品質基準を満たしています({self.score.value}点)"
        issue_count = len(self.issues)
        return f"改善が必要です({self.score.value}点、{issue_count}件の問題)"
