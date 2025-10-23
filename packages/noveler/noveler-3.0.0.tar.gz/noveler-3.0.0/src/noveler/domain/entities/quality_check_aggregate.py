#!/usr/bin/env python3

"""Domain.entities.quality_check_aggregate
Where: Domain aggregate for quality check results.
What: Aggregates quality scores and violations across checks.
Why: Enables reporting and follow-up actions based on quality data.
"""

from __future__ import annotations

"""品質チェックアグリゲート(DDD実装)

品質チェックシステムの中核となるアグリゲート。
ビジネスルールとドメイン知識を凝集させた実装。
"""


import re
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

from noveler.domain.exceptions import DomainException
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.value_objects.quality_threshold import QualityThreshold

if TYPE_CHECKING:
    from datetime import datetime

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class InvalidQualityRuleError(DomainException):
    """無効な品質ルールエラー"""


class QualityCheckNotStartedError(DomainException):
    """品質チェック未開始エラー"""


class DuplicateRuleError(DomainException):
    """重複ルールエラー"""


class RuleCategory(str, Enum):
    """ルールカテゴリ"""

    BASIC_STYLE = "basic_style"
    COMPOSITION = "composition"
    CHARACTER_CONSISTENCY = "character_consistency"
    READABILITY = "readability"
    EXPRESSION = "expression"


class Severity(str, Enum):
    """重要度"""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class CheckStatus(str, Enum):
    """チェック状態"""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class QualityRule:
    """品質ルール(値オブジェクト)

    品質チェックの個別ルールを表現する不変オブジェクト。
    """

    rule_id: str
    name: str
    category: RuleCategory
    severity: Severity
    description: str = ""
    pattern: str | None = None
    message_template: str = "{line}行目: {message}"
    enabled: bool = True
    penalty_score: float = 5.0

    def __post_init__(self) -> None:
        """バリデーション"""
        if not self.rule_id:
            msg = "ルールIDは必須です"
            raise InvalidQualityRuleError(msg)
        if not self.name:
            msg = "ルール名は必須です"
            raise InvalidQualityRuleError(msg)
        if self.penalty_score < 0:
            msg = "減点スコアは0以上である必要があります"
            raise InvalidQualityRuleError(msg)

    def disable(self) -> QualityRule:
        """ルールを無効化"""
        return QualityRule(
            rule_id=self.rule_id,
            name=self.name,
            category=self.category,
            severity=self.severity,
            description=self.description,
            pattern=self.pattern,
            message_template=self.message_template,
            enabled=False,
            penalty_score=self.penalty_score,
        )

    def enable(self) -> QualityRule:
        """ルールを有効化"""
        return QualityRule(
            rule_id=self.rule_id,
            name=self.name,
            category=self.category,
            severity=self.severity,
            description=self.description,
            pattern=self.pattern,
            message_template=self.message_template,
            enabled=True,
            penalty_score=self.penalty_score,
        )


@dataclass
class QualityViolation:
    """品質違反"""

    rule_id: str
    line_number: int
    column_number: int
    severity: Severity
    message: str
    context: str = ""
    suggestion: str = ""


@dataclass
class QualityCheckConfiguration:
    """品質チェック設定"""

    min_quality_score: QualityThreshold = field(
        default_factory=lambda: QualityThreshold(
            name="最小品質スコア",
            value=70.0,
            min_value=0.0,
            max_value=100.0,
        )
    )

    enabled_categories: list[RuleCategory] = field(default_factory=list)
    severity_weights: dict[Severity, float] = field(
        default_factory=lambda: {Severity.ERROR: 1.0, Severity.WARNING: 0.5, Severity.INFO: 0.1}
    )


@dataclass
class QualityCheckResult:
    """品質チェック結果"""

    check_id: str
    episode_id: str
    violations: list[QualityViolation]
    total_score: float
    executed_at: datetime
    threshold: QualityThreshold = field(
        default_factory=lambda: QualityThreshold(
            name="合格閾値",
            value=70.0,
            min_value=0.0,
            max_value=100.0,
        )
    )

    @property
    def total_violations(self) -> int:
        """総違反数"""
        return len(self.violations)

    @property
    def error_count(self) -> int:
        """エラー数"""
        return sum(1 for v in self.violations if v.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        """警告数"""
        return sum(1 for v in self.violations if v.severity == Severity.WARNING)

    @property
    def is_passed(self) -> bool:
        """合格判定"""
        return self.total_score >= self.threshold.value

    @property
    def violation_summary(self) -> dict[str, int]:
        """違反サマリー"""
        return {
            "error": self.error_count,
            "warning": self.warning_count,
            "info": sum(1 for v in self.violations if v.severity == Severity.INFO),
        }

    @property
    def category_summary(self) -> dict[RuleCategory, int]:
        """カテゴリ別サマリー"""
        summary = {}
        # 仮実装:実際にはルールとの関連を保持する必要がある
        for category in RuleCategory:
            summary[category] = 0
        return summary

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "check_id": self.check_id,
            "episode_id": self.episode_id,
            "total_score": self.total_score,
            "violations": [
                {
                    "rule_id": v.rule_id,
                    "line_number": v.line_number,
                    "column_number": v.column_number,
                    "severity": v.severity.value,
                    "message": v.message,
                    "context": v.context,
                }
                for v in self.violations
            ],
            "executed_at": self.executed_at.isoformat(),
            "is_passed": self.is_passed,
            "summary": self.violation_summary,
        }


class QualityCheckAggregate:
    """品質チェックアグリゲート

    品質チェックのビジネスロジックを集約したルートエンティティ。
    複数の品質ルールを組み合わせて、テキストの品質を総合的に評価する。
    """

    def __init__(self, check_id: str, episode_id: str, configuration: QualityCheckConfiguration | None = None) -> None:
        self.check_id = check_id
        self.episode_id = episode_id
        self.configuration = configuration or QualityCheckConfiguration()
        self.status = CheckStatus.NOT_STARTED
        self.rules: list[QualityRule] = []
        self._rule_ids: set[str] = set()
        self.started_at: datetime | None = None
        self.completed_at: datetime | None = None
        self.execution_count = 0
        self._last_result: QualityCheckResult | None = None

    def add_rule(self, rule: QualityRule) -> None:
        """ルールを追加

        ビジネスルール:
        - 同じIDのルールは追加できない
        - 設定で有効になっているカテゴリのルールのみ追加可能
        """
        if rule.rule_id in self._rule_ids:
            msg = f"ルールID {rule.rule_id} は既に存在します"
            raise DuplicateRuleError(msg)

        # カテゴリが有効な場合のみ追加
        if self.configuration.enabled_categories and rule.category not in self.configuration.enabled_categories:
            msg = f"カテゴリ {rule.category.value} は無効です"
            raise InvalidQualityRuleError(msg)

        self.rules.append(rule)
        self._rule_ids.add(rule.rule_id)

    def execute_check(self, content: str) -> QualityCheckResult:
        """品質チェックを実行

        ビジネスルール:
        - ルールが1つ以上設定されている必要がある
        - 有効なルールのみ実行される
        - 違反に基づいてスコアが計算される
        """
        if not self.rules:
            msg = "ルールが設定されていません"
            raise InvalidQualityRuleError(msg)

        self.status = CheckStatus.IN_PROGRESS
        self.started_at = project_now().datetime
        self.execution_count += 1

        try:
            violations: Any = self._detect_violations(content)
            total_score = self._calculate_score(violations)

            result = QualityCheckResult(
                check_id=self.check_id,
                episode_id=self.episode_id,
                violations=violations,
                total_score=total_score,
                executed_at=project_now().datetime,
                threshold=self.configuration.min_quality_score,
            )

            self.status = CheckStatus.COMPLETED
            self.completed_at = project_now().datetime
            self._last_result = result

            return result

        except Exception:
            self.status = CheckStatus.FAILED
            raise

    def _detect_violations(self, content: str) -> list[QualityViolation]:
        """違反を検出"""
        violations: list[Any] = []
        lines = content.split("\n")

        for rule in self.rules:
            if not rule.enabled:
                continue

            if rule.pattern:
                try:
                    pattern = re.compile(rule.pattern)

                    for line_num, line in enumerate(lines, 1):
                        matches = pattern.finditer(line)
                        for match in matches:
                            violation = QualityViolation(
                                rule_id=rule.rule_id,
                                line_number=line_num,
                                column_number=match.start(),
                                severity=rule.severity,
                                message=rule.message_template.format(
                                    line=line_num,
                                    message=rule.description or rule.name,
                                ),
                                context=line[max(0, match.start() - 10) : match.end() + 10],
                            )

                            violations.append(violation)
                except re.error:
                    # 正規表現パターンが無効な場合はスキップ
                    continue
            else:
                # パターンがない場合は、カスタム検証ロジックなどを将来実装可能
                pass

        return violations

    def _calculate_score(self, violations: list[QualityViolation]) -> float:
        """品質スコアを計算

        ビジネスルール:
        - 基本スコアは100点
        - 違反ごとに減点
        - 重要度に応じて減点幅が変わる
        """
        score = 100.0

        # ルールIDから減点スコアを取得するマップを作成
        rule_penalty_map = {rule.rule_id: rule.penalty_score for rule in self.rules}

        for violation in violations:
            penalty = rule_penalty_map.get(violation.rule_id, 5.0)
            weight = self.configuration.severity_weights.get(violation.severity, 1.0)
            score -= penalty * weight

        return max(0.0, score)
