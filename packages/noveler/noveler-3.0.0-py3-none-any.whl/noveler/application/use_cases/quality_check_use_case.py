#!/usr/bin/env python3

"""Application.use_cases.quality_check_use_case
Where: Application use case orchestrating the main quality check pipeline.
What: Coordinates content validation, violation reporting, and persistence.
Why: Ensures consistent quality enforcement across episodes and projects.
"""

from __future__ import annotations



import re
import uuid
from contextlib import nullcontext
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from noveler.application.base.abstract_use_case import AbstractUseCase

# B20準拠: FC/ISパターン - Functional Core導入
from noveler.domain.entities.quality_check_aggregate import (
    InvalidQualityRuleError,
    QualityCheckConfiguration,
    QualityCheckAggregate,
    QualityRule,
    QualityViolation,
)
from noveler.domain.value_objects.quality_threshold import QualityThreshold

if TYPE_CHECKING:
    from datetime import datetime

    from noveler.domain.interfaces.logger_service_protocol import ILoggerService
    from noveler.infrastructure.unit_of_work import IUnitOfWork


@dataclass(frozen=True)
class QualityCheckRequest:
    """Input payload for a quality check execution.

    Attributes:
        episode_id: Identifier of the episode that should be evaluated.
        project_id: Project identifier used when resolving repositories.
        check_options: Options that control which rules and features are enabled.
    """

    episode_id: str
    project_id: str
    check_options: dict[str, Any]

    def __post_init__(self) -> None:
        """Ensure optional flags such as `auto_fix` are always present."""
        if "auto_fix" not in self.check_options:
            object.__setattr__(self, "check_options", {**self.check_options, "auto_fix": False})


@dataclass
class QualityCheckResponse:
    """Result object returned after executing a quality check.

    Attributes:
        success: Indicates whether the use case completed without errors.
        check_id: Identifier assigned to the persisted quality check record.
        episode_id: Episode identifier associated with the evaluation.
        total_score: Aggregated score returned by the quality aggregate.
        violations: Domain violations detected during the evaluation.
        is_passed: Flag that signals whether the score passed the threshold.
        executed_at: Timestamp when the evaluation finished.
        auto_fix_applied: True when automatic fixes were applied.
        fixed_content: Modified content produced by the auto-fix routine.
        error_message: Details about a failure when `success` is False.
    """

    success: bool
    check_id: str | None = None
    episode_id: str | None = None
    total_score: float | None = None
    violations: list[QualityViolation] | None = None
    is_passed: bool | None = None
    executed_at: datetime | None = None
    auto_fix_applied: bool = False
    fixed_content: str | None = None
    error_message: str | None = None


class QualityCheckUseCase(AbstractUseCase[QualityCheckRequest, QualityCheckResponse]):
    """Application-level coordinator for running quality checks on episodes.

    The use case wires repositories, aggregates, and optional auto-fix behaviour
    using dependency injection primitives inspired by the B20 architecture guide.
    """

    def __init__(self,
        episode_repository=None,
        quality_check_repository=None,
        logger_service: ILoggerService = None,
        unit_of_work: IUnitOfWork = None,
        **kwargs) -> None:
        """Initialise the use case with optional infrastructure dependencies.

        Args:
            episode_repository: Repository used to load and persist episodes.
            quality_check_repository: Repository that stores quality check results.
            logger_service: Logger instance used for diagnostic logging.
            unit_of_work: Unit-of-work implementation that provides transactions.
            **kwargs: Additional parameters forwarded to the abstract base class.
        """
        super().__init__(**kwargs)
        # B20準拠: 標準DIサービス
        self._logger_service = logger_service
        self._unit_of_work = unit_of_work
        self.episode_repository = episode_repository
        self.quality_check_repository = quality_check_repository

    async def execute(self, request: QualityCheckRequest) -> QualityCheckResponse:
        """Execute the end-to-end quality evaluation within a transactional scope.

        The coroutine validates input, fetches rules, executes the aggregate, optionally
        applies auto fixes, persists the result, and returns a structured response.

        Args:
            request: Parameters describing the quality check to run.

        Returns:
            QualityCheckResponse: Response containing evaluation details and scores.
        """
        self._logger_service.info(f"品質チェック開始: エピソード={request.episode_id}")

        episode_repo = self._resolve_episode_repository()
        quality_repo = self._resolve_quality_repository()

        transaction_factory = getattr(self._unit_of_work, "transaction", None) if self._unit_of_work else None
        transaction_ctx = transaction_factory() if callable(transaction_factory) else nullcontext()

        try:
            with transaction_ctx:
                # 1. エピソードの存在確認
                episode = episode_repo.find_by_id(request.episode_id, request.project_id)
                if episode is None:
                    return QualityCheckResponse(
                        success=False, error_message=f"エピソードが見つかりません: {request.episode_id}"
                    )

                # 2. 品質ルールの取得・フィルタリング
                all_rules = quality_repo.get_default_rules()
                filtered_rules = self._filter_rules_by_options(all_rules, request.check_options)

                if not filtered_rules:
                    return QualityCheckResponse(success=False, error_message="品質ルールが設定されていません")

                # 3. 品質チェック実行準備
                check_id = str(uuid.uuid4())
                quality_threshold = self._extract_quality_threshold(quality_repo.get_quality_threshold())
                configuration = QualityCheckConfiguration(min_quality_score=quality_threshold)
                if request.check_options.get("categories"):
                    configuration.enabled_categories = list(request.check_options["categories"])

                aggregate = QualityCheckAggregate(
                    check_id=check_id,
                    episode_id=request.episode_id,
                    configuration=configuration,
                )

                for rule in filtered_rules:
                    try:
                        aggregate.add_rule(rule)
                    except InvalidQualityRuleError:
                        continue

                check_result = aggregate.execute_check(episode.content)
                violations = list(getattr(check_result, "violations", []))

                # 5. Imperative Shell: 自動修正（副作用）
                fixed_content = None
                auto_fix_applied = False
                if request.check_options.get("auto_fix", False):
                    fixed_content, auto_fix_applied = self._apply_auto_fixes(
                        episode.content, violations, [], filtered_rules
                    )

                if auto_fix_applied:
                    # 修正されたコンテンツでエピソードを更新
                    episode.update_content(fixed_content)
                    episode_repo.save(episode, request.project_id)

                # 6. Imperative Shell: 結果の永続化（副作用）
                quality_repo.save_result(check_result)

                # 7. Imperative Shell: レスポンス作成（副作用なし）
                return QualityCheckResponse(
                    success=True,
                    check_id=getattr(check_result, "check_id", check_id),
                    episode_id=getattr(check_result, "episode_id", request.episode_id),
                    total_score=getattr(check_result, "total_score", 0.0),
                    violations=violations,
                    is_passed=getattr(check_result, "is_passed", None),
                    executed_at=getattr(check_result, "executed_at", None),
                    auto_fix_applied=auto_fix_applied,
                    fixed_content=fixed_content,
                )

        except InvalidQualityRuleError as e:
            self._logger_service.error(f"品質ルールエラー: {e}")
            return QualityCheckResponse(success=False, error_message=f"品質ルールエラー: {e}")

        except Exception as e:
            self._logger_service.error(f"品質チェック実行エラー: {e}")
            return QualityCheckResponse(success=False, error_message=f"品質チェック実行エラー: {e}")

    def _resolve_episode_repository(self):
        """Return the episode repository resolved from dependencies.

        Returns:
            Any: Repository capable of loading and saving episodes.

        Raises:
            RuntimeError: If no repository can be resolved from DI or unit of work.
        """
        if self.episode_repository is not None:
            return self.episode_repository
        if self._unit_of_work and getattr(self._unit_of_work, "episode_repository", None) is not None:
            return self._unit_of_work.episode_repository
        msg = "EpisodeRepository が設定されていません"
        raise RuntimeError(msg)

    def _resolve_quality_repository(self):
        """Return the quality check repository resolved from dependencies.

        Returns:
            Any: Repository that manages quality check rules and results.

        Raises:
            RuntimeError: If no repository can be resolved from DI or unit of work.
        """
        if self.quality_check_repository is not None:
            return self.quality_check_repository
        if self._unit_of_work and getattr(self._unit_of_work, "quality_check_repository", None) is not None:
            return self._unit_of_work.quality_check_repository
        msg = "QualityCheckRepository が設定されていません"
        raise RuntimeError(msg)

    def _extract_quality_threshold(self, threshold_obj: Any) -> QualityThreshold:
        """Normalise threshold values provided by legacy or mock implementations.

        Args:
            threshold_obj: Object or primitive describing the desired threshold.

        Returns:
            QualityThreshold: Domain value object built from the provided data.
        """
        if isinstance(threshold_obj, QualityThreshold):
            return threshold_obj

        value = getattr(threshold_obj, "value", threshold_obj)
        name = getattr(threshold_obj, "name", "最小品質スコア")
        min_value = getattr(threshold_obj, "min_value", 0.0)
        max_value = getattr(threshold_obj, "max_value", 100.0)

        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            numeric_value = 0.0

        return QualityThreshold(
            name=name,
            value=numeric_value,
            min_value=self._safe_float(min_value, 0.0),
            max_value=self._safe_float(max_value, 100.0),
        )

    @staticmethod
    def _safe_float(value: Any, default: float) -> float:
        """Convert a value to float while falling back to a default."""
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _filter_rules_by_options(self, rules: list[QualityRule], options: dict[str, Any]) -> list[QualityRule]:
        """Filter quality rules based on the caller-provided options.

        Args:
            rules: Candidate rules retrieved from the repository.
            options: Request options that may limit categories or features.

        Returns:
            list[QualityRule]: Rules that remain enabled for the evaluation.
        """
        filtered_rules = []

        # カテゴリフィルタリング
        target_categories = options.get("categories", [])

        for rule in rules:
            if not rule.enabled:
                continue

            # カテゴリ指定がある場合はフィルタリング
            if target_categories and rule.category not in target_categories:
                continue

            filtered_rules.append(rule)

        return filtered_rules

    def _apply_auto_fixes(
        self,
        content: str,
        violations: list[QualityViolation],
        suggestions: list[str],
        rules: list[Any] | None = None,
    ) -> tuple[str, bool]:
        """Apply auto-fix suggestions generated by the aggregate or rules.

        Args:
            content: Original manuscript content.
            violations: Violations reported by the quality aggregate.
            suggestions: Textual suggestions that may imply quick fixes.
            rules: Optional rule definitions that provide regex-based replacements.

        Returns:
            tuple[str, bool]: Updated content and a flag indicating whether any fixes were applied.
        """
        fixed_content = content
        auto_fix_applied = False

        # B20準拠: FC/ISパターン - 自動修正提案を使用
        for suggestion in suggestions:
            if "鍵括弧の対応" in suggestion:
                # 簡単な修正例
                if content.count("「") > content.count("」"):
                    fixed_content += "」"
                    auto_fix_applied = True

        # 違反ベースの修正
        for violation in violations:
            if violation.rule_id == "length_check" and "文字数不足" in violation.message:
                # 文字数不足の場合は修正提案のみ（実際のコンテンツ修正は困難）
                continue
            if violation.rule_id == "sentence_structure":
                # 構造的修正
                lines = fixed_content.split("\n")
                fixed_lines = [line for line in lines if line.strip() or not auto_fix_applied]
                fixed_content = "\n".join(fixed_lines)
                auto_fix_applied = True

        if rules:
            for rule in rules:
                pattern = getattr(rule, "pattern", None)
                replacement = getattr(rule, "replacement", None)
                auto_fixable = getattr(rule, "auto_fixable", False)

                if not auto_fixable or not pattern or replacement is None:
                    continue

                new_content = fixed_content
                if pattern:
                    try:
                        new_content = re.sub(pattern, replacement, fixed_content)
                    except re.error:
                        new_content = fixed_content

                if new_content == fixed_content:
                    for candidate in (pattern, "...", "。。。"):
                        if candidate and candidate in fixed_content:
                            new_content = fixed_content.replace(candidate, replacement)
                            break

                if new_content != fixed_content:
                    fixed_content = new_content
                    auto_fix_applied = True

        return fixed_content, auto_fix_applied
