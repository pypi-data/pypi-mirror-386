#!/usr/bin/env python3

"""Domain.entities.quality_record_enhancement
Where: Domain entity describing enhancements to quality records.
What: Tracks enrichment data and transformations applied to records.
Why: Supports richer quality reporting and insights.
"""

from __future__ import annotations

"""品質記録拡張エンティティ
品質記録活用システムのドメインモデル
"""


from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from noveler.domain.exceptions import BusinessRuleViolationError
from noveler.domain.value_objects.learning_metrics import LearningMetrics
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


@dataclass
class QualityCheckParameters:
    """品質チェックのパラメータ群"""

    episode_number: int
    category_scores: dict[str, float]
    errors: list[str]
    warnings: list[str]
    auto_fixes: list[str]


@dataclass
class QualityCheckContext:
    """品質チェックのコンテキスト情報"""

    learning_metrics: LearningMetrics
    writing_environment: str | None = None
    target_audience: str | None = None
    writing_goal: str | None = None


@dataclass
class QualityRecordEnhancement:
    """品質記録拡張エンティティ

    品質記録を活用した学習システムの中核エンティティ
    学習データの蓄積、トレンド分析、改善提案の管理を行う
    """

    project_name: str
    version: str = "1.0"
    last_updated: datetime = field(default_factory=datetime.now)
    entry_count: int = 0
    quality_checks: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """エンティティの不変条件を検証"""
        self._validate_project_name()
        self._validate_version()

    def _validate_project_name(self) -> None:
        """プロジェクト名の妥当性検証"""
        if not self.project_name or len(self.project_name.strip()) == 0:
            msg = "プロジェクト名は必須です"
            raise BusinessRuleViolationError("project_name_required", msg)

    def _validate_version(self) -> None:
        """バージョンの妥当性検証"""
        if not self.version or len(self.version.strip()) == 0:
            msg = "バージョンは必須です"
            raise BusinessRuleViolationError("version_required", msg)

    def add_quality_check_result(self, *args, **kwargs) -> None:
        """品質チェック結果を追加

        互換性維持のため、従来の `QualityCheckParameters` + `QualityCheckContext`
        形式と、テスト仕様で用いられるキーワード引数形式の両方を受け付ける。
        """

        parameters: QualityCheckParameters
        context: QualityCheckContext

        if args and isinstance(args[0], QualityCheckParameters):
            parameters = args[0]
            if len(args) > 1 and isinstance(args[1], QualityCheckContext):
                context = args[1]
            else:
                context = kwargs.get("context")
                if not isinstance(context, QualityCheckContext):
                    msg = "QualityCheckContext is required when using positional parameters"
                    raise BusinessRuleViolationError("context_required", msg)
        else:
            try:
                episode_number = kwargs["episode_number"]
                category_scores = kwargs["category_scores"]
                errors = kwargs.get("errors", [])
                warnings = kwargs.get("warnings", [])
                auto_fixes = kwargs.get("auto_fixes", [])
                learning_metrics = kwargs["learning_metrics"]
            except KeyError as exc:
                msg = f"Missing required argument: {exc.args[0]}"
                raise TypeError(msg) from exc

            if not isinstance(learning_metrics, LearningMetrics):
                msg = "learning_metrics must be a LearningMetrics instance"
                raise TypeError(msg)

            parameters = QualityCheckParameters(
                episode_number=episode_number,
                category_scores=dict(category_scores),
                errors=list(errors),
                warnings=list(warnings),
                auto_fixes=list(auto_fixes),
            )

            context = QualityCheckContext(
                learning_metrics=learning_metrics,
                writing_environment=kwargs.get("writing_environment"),
                target_audience=kwargs.get("target_audience"),
                writing_goal=kwargs.get("writing_goal"),
            )

        # ビジネスルール:エピソード番号は正の整数
        if parameters.episode_number <= 0:
            msg = "エピソード番号は1以上の正の整数である必要があります"
            raise BusinessRuleViolationError("episode_number_invalid", msg)

        recorded_at = project_now().datetime

        # 品質チェック結果を構築
        quality_check_entry = {
            "id": f"{self.project_name}_{parameters.episode_number}_{recorded_at.isoformat()}",
            "episode_number": parameters.episode_number,
            "timestamp": recorded_at.isoformat(),
            "recorded_at": recorded_at,
            "results": {
                "category_scores": parameters.category_scores,
                "errors": parameters.errors,
                "warnings": parameters.warnings,
                "auto_fixes": parameters.auto_fixes,
            },
            "learning_metrics": {
                "improvement_from_previous": context.learning_metrics.improvement_from_previous,
                "time_spent_writing": context.learning_metrics.time_spent_writing,
                "revision_count": context.learning_metrics.revision_count,
                "user_feedback": context.learning_metrics.user_feedback,
                "writing_context": context.learning_metrics.writing_context,
            },
            "context": {
                "writing_environment": context.writing_environment,
                "target_audience": context.target_audience,
                "writing_goal": context.writing_goal,
            },
        }

        self.quality_checks.append(quality_check_entry)
        self.entry_count = len(self.quality_checks)
        self.last_updated = recorded_at

    def get_improvement_trend(self, category: str) -> list[dict[str, Any]]:
        """指定カテゴリの改善トレンドを取得"""
        trend_data: list[dict[str, Any]] = []
        for check in self.quality_checks:
            category_scores = check["results"]["category_scores"]
            if category not in category_scores:
                continue

            trend_data.append(
                {
                    "episode_number": check["episode_number"],
                    "timestamp": check["timestamp"],
                    "score": category_scores[category],
                    "improvement": check["learning_metrics"]["improvement_from_previous"],
                }
            )

        return sorted(trend_data, key=lambda x: x["episode_number"])

    def calculate_average_improvement_rate(self) -> float:
        """平均改善率を計算"""
        if not self.quality_checks:
            return 0.0

        total_improvement = sum(check["learning_metrics"]["improvement_from_previous"] for check in self.quality_checks)

        return total_improvement / len(self.quality_checks)

    def get_latest_scores(self) -> dict[str, float]:
        """最新の品質スコアを取得"""
        if not self.quality_checks:
            return {}

        latest_check = max(
            self.quality_checks,
            key=lambda x: x.get("recorded_at") or datetime.fromisoformat(x["timestamp"]),
        )
        return dict(latest_check["results"]["category_scores"])

    def get_weakest_categories(self, limit: int = 3) -> list[str]:
        """最も弱いカテゴリを取得"""
        latest_scores = self.get_latest_scores()
        if not latest_scores:
            return []

        # スコアの低い順にソート
        sorted_categories = sorted(latest_scores.items(), key=lambda x: x[1])
        return [category for category, _ in sorted_categories[:limit]]

    def get_strongest_categories(self, limit: int = 3) -> list[str]:
        """最も強いカテゴリを取得"""
        latest_scores = self.get_latest_scores()
        if not latest_scores:
            return []

        # スコアの高い順にソート
        sorted_categories = sorted(latest_scores.items(), key=lambda x: x[1], reverse=True)
        return [category for category, _ in sorted_categories[:limit]]

    def has_sufficient_data_for_analysis(self, minimum_entries: int = 3) -> bool:
        """分析に十分なデータがあるかどうかを判定"""
        return len(self.quality_checks) >= minimum_entries

    def get_total_writing_time(self) -> int:
        """総執筆時間を取得"""
        return sum(check["learning_metrics"]["time_spent_writing"] for check in self.quality_checks)

    def get_total_revision_count(self) -> int:
        """総リビジョン数を取得"""
        return sum(check["learning_metrics"]["revision_count"] for check in self.quality_checks)

    def get_learning_summary(self) -> dict[str, Any]:
        """学習の要約を取得"""
        if not self.quality_checks:
            return {
                "total_entries": 0,
                "total_writing_time": 0,
                "total_revisions": 0,
                "average_improvement_rate": 0.0,
                "strongest_categories": [],
                "weakest_categories": [],
                "has_sufficient_data": False,
            }

        return {
            "total_entries": self.entry_count,
            "total_writing_time": self.get_total_writing_time(),
            "total_revisions": self.get_total_revision_count(),
            "average_improvement_rate": self.calculate_average_improvement_rate(),
            "strongest_categories": self.get_strongest_categories(),
            "weakest_categories": self.get_weakest_categories(),
            "has_sufficient_data": self.has_sufficient_data_for_analysis(),
            "latest_scores": self.get_latest_scores(),
        }

    def can_generate_trend_analysis(self) -> bool:
        """トレンド分析が可能かどうかを判定"""
        return self.has_sufficient_data_for_analysis()

    def can_generate_improvement_suggestions(self) -> bool:
        """改善提案が可能かどうかを判定"""
        return self.has_sufficient_data_for_analysis()

    def generate_improvement_suggestions_precondition_check(self) -> None:
        """改善提案生成の前提条件チェック"""
        if not self.can_generate_improvement_suggestions():
            msg = f"改善提案の生成には最低3回の品質チェックデータが必要です。現在のデータ数: {len(self.quality_checks)}"
            raise BusinessRuleViolationError("insufficient_quality_checks", msg)
