#!/usr/bin/env python3

"""Domain.entities.quality_check_session
Where: Domain entity tracking quality check sessions.
What: Stores session configuration, progress, and outcomes.
Why: Supports auditing and reruns of quality checks.
"""

from __future__ import annotations

"""品質チェックセッションエンティティ(DDD実装)

品質チェックのドメインモデル。
レガシーの品質チェッカーをDDDアーキテクチャで再実装。
"""


from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, ClassVar

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

if TYPE_CHECKING:
    from datetime import datetime

# ファイルコンテンツの型エイリアス
FileContent = str | bytes | dict[str, Any]

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class CheckType(Enum):
    """チェックタイプ"""

    BASIC_STYLE = "basic_style"
    COMPOSITION = "composition"
    CHARACTER_CONSISTENCY = "character_consistency"
    READABILITY = "readability"
    INVALID_KANJI = "invalid_kanji"
    FORESHADOWING = "foreshadowing"

    # v2.0 執筆品質強化チェックタイプ (SPEC-QUALITY-023 v2.0)
    EMOTION_DEPTH = "emotion_depth"          # 感情表現深度チェック
    ANTAGONIST_PERSONALITY = "antagonist"    # 対立キャラクター個性化チェック
    TENSION_BALANCE = "tension_balance"      # 緊張緩和バランスチェック


class Severity(Enum):
    """問題の重要度"""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class QualityGrade(Enum):
    """品質グレード"""

    S = "S"  # 90以上
    A = "A"  # 80以上
    B = "B"  # 70以上
    C = "C"  # 60以上
    D = "D"  # 60未満

    @property
    def display_name(self) -> str:
        """表示名を取得"""
        names = {
            "S": "S級(秀逸)",
            "A": "A級(優良)",
            "B": "B級(標準)",
            "C": "C級(要改善)",
            "D": "D級(要大幅改善)",
        }
        return names[self.value]

    def __gt__(self, other: QualityGrade) -> bool:
        """グレードの比較(大きい)"""
        if not isinstance(other, QualityGrade):
            return NotImplemented
        order = ["D", "C", "B", "A", "S"]
        return order.index(self.value) > order.index(other.value)

    def __lt__(self, other: QualityGrade) -> bool:
        """グレードの比較(小さい)"""
        if not isinstance(other, QualityGrade):
            return NotImplemented
        order = ["D", "C", "B", "A", "S"]
        return order.index(self.value) < order.index(other.value)


@dataclass(frozen=True)
class QualityScore:
    """品質スコア値オブジェクト(0-100)"""

    value: float

    def __post_init__(self) -> None:
        """バリデーション"""
        if not 0 <= self.value <= 100:
            msg = "スコアは0-100の範囲内である必要があります"
            raise ValueError(msg)

    def __hash__(self) -> int:
        """ハッシュ値を生成"""
        return hash(self.value)

    def to_grade(self) -> QualityGrade:
        """スコアからグレードを判定"""
        if self.value >= 90:
            return QualityGrade.S
        if self.value >= 80:
            return QualityGrade.A
        if self.value >= 70:
            return QualityGrade.B
        if self.value >= 60:
            return QualityGrade.C
        return QualityGrade.D

    def __lt__(self, other: QualityScore) -> bool:
        if not isinstance(other, QualityScore):
            return NotImplemented
        return self.value < other.value

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, QualityScore):
            return NotImplemented
        return self.value > other.value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, QualityScore):
            return NotImplemented
        return self.value == other.value


@dataclass(frozen=True)
class QualityIssue:
    """品質問題値オブジェクト"""

    type: str
    message: str
    severity: Severity
    line_number: int | None = None
    position: int | None = None
    suggestion: str | None = None
    auto_fixable: bool = False


@dataclass(frozen=True)
class QualityCheckResult:
    """個別チェック結果値オブジェクト"""

    check_type: CheckType
    score: QualityScore
    issues: list[QualityIssue]
    metadata: dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    suggestions: list[str] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        """エラー数を取得"""
        return sum(1 for issue in self.issues if issue.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        """警告数を取得"""
        return sum(1 for issue in self.issues if issue.severity == Severity.WARNING)

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "check_type": self.check_type.value,
            "score": self.score.value,
            "issues": [
                {
                    "type": issue.type,
                    "message": issue.message,
                    "severity": issue.severity.value,
                    "line_number": issue.line_number,
                    "position": issue.position,
                    "suggestion": issue.suggestion,
                    "auto_fixable": issue.auto_fixable,
                }
                for issue in self.issues
            ],
            "metadata": self.metadata,
            "execution_time": self.execution_time,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "suggestions": self.suggestions,
        }


class QualityCheckSession:
    """品質チェックセッション(ルートアグリゲート)

    品質チェックの実行単位を表現。
    複数のチェック結果を集約して総合評価を行う。
    """

    # チェッカーの重み設定
    CHECKER_WEIGHTS: ClassVar[dict[CheckType, float]] = {
        CheckType.BASIC_STYLE: 0.25,
        CheckType.COMPOSITION: 0.25,
        CheckType.CHARACTER_CONSISTENCY: 0.20,
        CheckType.READABILITY: 0.20,
        CheckType.INVALID_KANJI: 0.10,
    }

    def __init__(
        self, session_id: str, project_id: str, target_content: str | None = None, config: dict[str, Any] | None = None
    ) -> None:
        """初期化

        Args:
            session_id: セッションID
            project_id: プロジェクトID
            target_content: チェック対象コンテンツ
            config: 設定
        """
        self.session_id = session_id
        self.project_id = project_id
        self.target_content = target_content
        self.config = config or {}
        self.created_at = project_now().datetime
        self.completed_at: datetime | None = None
        self.status = "pending"  # pending, in_progress, completed, failed
        self.check_results: list[QualityCheckResult] = []
        self._total_score_cache: QualityScore | None = None
        self._grade_cache: QualityGrade | None = None

    def add_check_result(self, result: QualityCheckResult) -> None:
        """チェック結果を追加

        Args:
            result: チェック結果

        Raises:
            ValueError: 完了したセッションに追加しようとした場合
        """
        if self.status == "completed":
            msg = "完了したセッションには結果を追加できません"
            raise ValueError(msg)

        # 同じタイプの結果は上書き
        self.check_results = [r for r in self.check_results if r.check_type != result.check_type]
        self.check_results.append(result)

        # キャッシュをクリア
        self._total_score_cache = None
        self._grade_cache = None

        # ステータス更新
        if self.status == "pending":
            self.status = "in_progress"

    def has_check_type(self, check_type: CheckType) -> bool:
        """指定したチェックタイプの結果が存在するか"""
        return any(r.check_type == check_type for r in self.check_results)

    def get_check_result(self, check_type: CheckType) -> QualityCheckResult | None:
        """指定したチェックタイプの結果を取得"""
        for result in self.check_results:
            if result.check_type == check_type:
                return result
        return None

    def calculate_total_score(self) -> QualityScore:
        """総合スコアを計算

        Returns:
            総合スコア(重み付け平均)
        """
        if self._total_score_cache is not None:
            return self._total_score_cache

        if not self.check_results:
            return QualityScore(0.0)

        # 重み付け平均を計算
        total_weight = 0.0
        weighted_sum = 0.0

        for result in self.check_results:
            weight = self.CHECKER_WEIGHTS.get(result.check_type, 0.0)
            weighted_sum += result.score.value * weight
            total_weight += weight

        if total_weight == 0:
            # 重みが設定されていないチェックのみの場合は単純平均
            avg_score = sum(r.score.value for r in self.check_results) / len(self.check_results)
            self._total_score_cache = QualityScore(avg_score)
        else:
            self._total_score_cache = QualityScore(weighted_sum / total_weight)

        return self._total_score_cache

    def determine_grade(self) -> QualityGrade:
        """品質グレードを判定

        Returns:
            品質グレード
        """
        if self._grade_cache is not None:
            return self._grade_cache

        total_score = self.calculate_total_score()
        self._grade_cache = total_score.to_grade()
        return self._grade_cache

    def get_all_issues(self) -> list[QualityIssue]:
        """全ての問題を取得

        Returns:
            全チェック結果の問題リスト
        """
        issues = []
        for result in self.check_results:
            issues.extend(result.issues)
        return issues

    def get_issues_by_severity(self, severity: str) -> list[QualityIssue]:
        """重要度別に問題を取得

        Args:
            severity: 重要度

        Returns:
            指定した重要度の問題リスト
        """
        return [issue for issue in self.get_all_issues() if issue.severity == severity]

    def complete(self) -> None:
        """セッションを完了"""
        self.status = "completed"
        self.completed_at = project_now().datetime

    def fail(self, error_message: str) -> None:
        """セッションを失敗として記録"""
        self.status = "failed"
        self.completed_at = project_now().datetime
        self.config["error_message"] = error_message

    def export_summary(self) -> dict[str, Any]:
        """サマリーをエクスポート

        Returns:
            セッションのサマリー情報
        """
        total_score = self.calculate_total_score()
        grade = self.determine_grade()
        all_issues = self.get_all_issues()

        return {
            "session_id": self.session_id,
            "project_id": self.project_id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "target_file": self.target_content.filepath,
            "total_score": total_score.value,
            "grade": grade.value,
            "grade_display": grade.display_name,
            "check_results": [result.to_dict() for result in self.check_results],
            "total_issues": len(all_issues),
            "error_count": len(self.get_issues_by_severity(Severity.ERROR)),
            "warning_count": len(self.get_issues_by_severity(Severity.WARNING)),
            "info_count": len(self.get_issues_by_severity(Severity.INFO)),
        }

    def get_improvement_suggestions(self) -> list[str]:
        """改善提案を生成

        Returns:
            改善提案のリスト
        """
        suggestions = []

        # スコアが低いチェック項目を特定
        low_score_results = [r for r in self.check_results if r.score.value < 70]

        for result in sorted(low_score_results, key=lambda r: r.score.value):
            check_name = self._get_check_display_name(result.check_type)
            suggestions.append(f"{check_name}のスコアが{result.score.value}点と低めです")

        # 自動修正可能な問題を提案
        auto_fixable_issues = [issue for issue in self.get_all_issues() if issue.auto_fixable]
        if auto_fixable_issues:
            suggestions.append(
                f"{len(auto_fixable_issues)}件の問題は自動修正が可能です。"
                "品質チェックツールの自動修正機能を使用することをお勧めします。"
            )

        return suggestions

    def _get_check_display_name(self, check_type: CheckType) -> str:
        """チェックタイプの表示名を取得"""
        names = {
            CheckType.BASIC_STYLE: "基礎文章作法",
            CheckType.COMPOSITION: "文章構成",
            CheckType.CHARACTER_CONSISTENCY: "キャラクター一貫性",
            CheckType.READABILITY: "読みやすさ",
            CheckType.INVALID_KANJI: "無効漢字",
        }
        return names.get(check_type, check_type.value)
