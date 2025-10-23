#!/usr/bin/env python3
"""Integrated quality check use case.

Provides the integrated quality evaluation workflow and exposes it to application clients.
"""

from __future__ import annotations



import uuid
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from noveler.domain.interfaces.quality_checker import IQualityChecker


from noveler.application.checkers.foreshadowing_checker import ForeshadowingChecker
from noveler.domain.entities.quality_check_session import (
    CheckType,
    QualityCheckResult,
    QualityCheckSession,
    QualityIssue,
    QualityScore,
    Severity,
)
from noveler.domain.services.foreshadowing_validation_service import ForeshadowingValidationService
from noveler.domain.services.quality_evaluation_service import QualityEvaluationService
from noveler.domain.value_objects.file_content import FileContent
from noveler.infrastructure.di.unified_repository_factory import UnifiedRepositoryFactory


class _CheckerInput(dict):
    """Checker payload that exposes both dict and attribute-style access."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.__dict__ = self


@dataclass(frozen=True)
class QualityCheckRequest:
    """Input parameters for the integrated quality check.

    Attributes:
        project_id: Identifier of the project under evaluation.
        filepath: Path to the manuscript file to inspect.
        check_types: Optional subset of check types to execute.
        auto_fix: Whether auto-fix routines should run after evaluation.
        verbose: Controls verbosity for downstream adapters.
        config: Optional configuration overrides supplied by the caller.
    """

    project_id: str
    filepath: Path
    check_types: list[CheckType] | None = None
    auto_fix: bool = False
    verbose: bool = True
    config: dict[str, Any] | None = None


@dataclass
class QualityCheckResponse:
    """Structured response returned by the integrated quality check workflow.

    Attributes:
        success: True when the workflow completed successfully.
        session_id: Identifier of the persisted quality check session.
        total_score: Aggregated quality score across all checks.
        grade: Letter grade assigned by the scoring rules.
        check_results: Serialized results for each executed checker.
        issues: Formatted issues aggregated from all checkers.
        suggestions: Improvement suggestions that can be surfaced to users.
        auto_fixed_content: Content string after optional auto-fix routines.
        error_message: Description of the failure when success is False.
    """

    success: bool
    session_id: str | None = None
    total_score: float | None = None
    grade: str | None = None
    check_results: list[dict[str, Any]] | None = None
    issues: list[dict[str, Any]] | None = None
    suggestions: list[str] | None = None
    auto_fixed_content: str | None = None
    error_message: str | None = None


class IntegratedQualityCheckUseCase:
    """Coordinate the integrated quality check workflow for manuscripts.

    The use case orchestrates quality services, executes registered checkers, aggregates
    results, and applies optional auto-fix strategies.
    """

    def __init__(
        self,
        quality_evaluation_service: QualityEvaluationService | None = None,
        checker_registry: dict[CheckType, IQualityChecker] | None = None,
        foreshadowing_validation_service: ForeshadowingValidationService | None = None,
        repository_factory: UnifiedRepositoryFactory = None,
    ) -> None:
        """Initialize the integrated quality check use case.

        Args:
            quality_evaluation_service: Service used for score aggregation and grading.
            checker_registry: Optional registry that maps check types to checkers.
            foreshadowing_validation_service: Service that validates foreshadowing constructs.
            repository_factory: Factory used to obtain infrastructure repositories when needed.
        """
        if quality_evaluation_service is None:
            quality_evaluation_service = QualityEvaluationService()

        # DDD準拠：統合ファクトリー経由でリポジトリ作成
        if foreshadowing_validation_service is None:
            self._repository_factory = repository_factory or self._create_default_factory()

            if self._repository_factory:
                foreshadowing_repository = self._repository_factory.create_yaml_foreshadowing_repository()
            else:
                # DDD準拠: Application→Infrastructure違反を遅延初期化で回避（緊急時対応）
                # フォールバック：遅延初期化パターン
                try:
                    from noveler.infrastructure.repositories.yaml_foreshadowing_repository import (
                        YamlForeshadowingRepository,
                    )

                    foreshadowing_repository = YamlForeshadowingRepository()
                except ImportError:
                    foreshadowing_repository = None

            foreshadowing_validation_service = ForeshadowingValidationService(foreshadowing_repository)

        self.quality_evaluation_service = quality_evaluation_service
        self.foreshadowing_validation_service = foreshadowing_validation_service
        self.checker_registry = checker_registry or self._create_default_checker_registry()
        self._sessions: dict[str, QualityCheckSession] = {}

    def _create_default_factory(self) -> UnifiedRepositoryFactory:
        """Create the default repository factory used for backward compatibility."""
        try:
            # DDD準拠: Application→Infrastructure違反を遅延初期化で回避
            from noveler.infrastructure.di.unified_repository_factory import UnifiedRepositoryFactory

            return UnifiedRepositoryFactory()
        except ImportError:
            # フォールバック：緊急時対応
            return None

    def _create_default_checker_registry(self) -> dict[CheckType, IQualityChecker]:
        """Build the default registry of quality checkers."""
        # モックチェッカーを作成(実際のチェッカーの代替)
        mock_checker = type(
            "MockChecker",
            (),
            {
                "execute": lambda _self, _data: {
                    "score": 85.0,
                    "issues": [
                        {
                            "type": "punctuation",
                            "message": "連続句読点が見つかりました",
                            "severity": "warning",
                            "auto_fixable": True,
                            "suggestion": "連続句読点を修正",
                        },
                        {
                            "type": "space",
                            "message": "連続スペースが見つかりました",
                            "severity": "info",
                            "auto_fixable": True,
                            "suggestion": "連続スペースを修正",
                        },
                    ],
                    "metadata": {},
                    "execution_time": 0.1,
                }
            },
        )()

        return {
            CheckType.BASIC_STYLE: mock_checker,
            CheckType.COMPOSITION: mock_checker,
            CheckType.READABILITY: mock_checker,
            CheckType.FORESHADOWING: self._create_foreshadowing_checker(),
            # v2.0 執筆品質強化チェッカー (SPEC-QUALITY-023 v2.0)
            CheckType.EMOTION_DEPTH: self._create_emotion_expression_checker(),
            CheckType.ANTAGONIST_PERSONALITY: self._create_antagonist_personality_checker(),
            CheckType.TENSION_BALANCE: self._create_tension_relief_balance_checker(),
        }

    def _create_foreshadowing_checker(self) -> ForeshadowingChecker:
        """Create the foreshadowing checker backed by the validation service."""
        return ForeshadowingChecker(self.foreshadowing_validation_service)

    def _create_emotion_expression_checker(self) -> Any:
        """Create the emotion expression depth checker."""
        from noveler.domain.services.emotion_expression_checker import EmotionExpressionChecker

        return EmotionExpressionChecker()

    def _create_antagonist_personality_checker(self) -> Any:
        """Create the antagonist personality checker."""
        from noveler.domain.services.antagonist_personality_checker import AntagonistPersonalityChecker

        return AntagonistPersonalityChecker()

    def _create_tension_relief_balance_checker(self) -> Any:
        """Create the tension and relief balance checker."""
        from noveler.domain.services.tension_relief_balance_checker import TensionReliefBalanceChecker

        return TensionReliefBalanceChecker()

    def execute(self, request: QualityCheckRequest) -> QualityCheckResponse:
        """Alias for `check_quality` to maintain backward compatibility."""
        return self.check_quality(request)

    def check_quality(self, request: QualityCheckRequest) -> QualityCheckResponse:
        """Run the integrated quality evaluation workflow.

        The workflow reads the target file, creates a quality session, executes registered
        checkers, aggregates results, optionally applies auto fixes, and finally builds
        a response object.

        Args:
            request: Parameters describing the quality check to perform.

        Returns:
            QualityCheckResponse: Result produced by the quality evaluation.
        """
        try:
            # 1. ファイル内容の読み込み
            if not request.filepath.exists():
                return QualityCheckResponse(
                    success=False,
                    error_message=f"ファイルが見つかりません: {request.filepath}",
                )

            content = request.filepath.read_text(encoding="utf-8")
            file_content = FileContent(
                filepath=str(request.filepath),
                content=content,
                encoding="utf-8",
            )

            # 2. 品質チェックセッションの作成
            session_id = str(uuid.uuid4())
            session = QualityCheckSession(
                session_id=session_id,
                project_id=request.project_id,
                target_content=file_content,
                config=request.config,
            )

            self._sessions[session_id] = session

            # 3. 各種チェッカーの実行
            check_types = request.check_types or list(CheckType)
            for check_type in check_types:
                if check_type in self.checker_registry:
                    result = self._execute_checker(
                        check_type,
                        file_content,
                        request.config,
                    )

                    session.add_check_result(result)

            # 4. 結果の集約と評価
            total_score = session.calculate_total_score()
            grade = session.determine_grade()

            # 5. 自動修正(オプション)
            auto_fixed_content = None
            if request.auto_fix:
                auto_fixed_content = self._apply_auto_fixes(
                    file_content.content,
                    session.get_all_issues(),
                )

            # 6. セッション完了
            session.complete()

            # 7. レスポンスの生成
            session.export_summary()

            return QualityCheckResponse(
                success=True,
                session_id=session_id,
                total_score=total_score.value,
                grade=grade.value,
                check_results=[result.to_dict() for result in session.check_results],
                issues=self._format_issues(session.get_all_issues()),
                suggestions=session.get_improvement_suggestions(),
                auto_fixed_content=auto_fixed_content,
            )

        except Exception as e:
            return QualityCheckResponse(
                success=False,
                error_message=f"品質チェックエラー: {e!s}",
            )

    def get_session_summary(self, session_id: str) -> dict[str, Any] | None:
        """Return the exported summary for a given session.

        Args:
            session_id: Identifier obtained from a previous quality check execution.

        Returns:
            dict[str, Any] | None: Summary dictionary when the session exists, otherwise None.
        """
        session = self._sessions.get(session_id)
        if session:
            return session.export_summary()
        return None

    def _execute_checker(
        self,
        check_type: CheckType,
        file_content: FileContent,
        config: dict[str, Any] | None = None,
    ) -> QualityCheckResult:
        """Execute a single checker and convert the result into domain objects.

        Args:
            check_type: Type of checker to execute.
            file_content: File content being analysed.
            config: Optional configuration dictionary passed to the checker.

        Returns:
            QualityCheckResult: Normalised result that fits the domain model.
        """
        checker = self.checker_registry[check_type]

        # チェッカー実行(インフラ層のアダプター経由)
        try:
            # v2.0新チェッカー（IQualityCheckerインターフェイス）の場合
            if check_type in [CheckType.EMOTION_DEPTH, CheckType.ANTAGONIST_PERSONALITY, CheckType.TENSION_BALANCE]:
                result = checker.check_text(file_content.content)

                # IQualityCheckerの結果形式から変換
                if result.get("success", False):
                    # recommendationsを適切な形式に変換
                    issues = [
                        {
                            "type": "improvement",
                            "message": rec,
                            "severity": "info",
                            "auto_fixable": False,
                        }
                        for rec in result.get("recommendations", [])
                    ]

                    return QualityCheckResult(
                        check_type=check_type,
                        score=QualityScore(result.get("score", 0.0)),
                        issues=[
                            QualityIssue(
                                type=issue_data["type"],
                                message=issue_data["message"],
                                severity=Severity(issue_data.get("severity", "info")),
                                line_number=issue_data.get("line_number"),
                                position=issue_data.get("position"),
                                suggestion=issue_data.get("suggestion"),
                                auto_fixable=issue_data.get("auto_fixable", False),
                            )
                            for issue_data in issues
                        ],
                        metadata=result.get("analysis", {}),
                        execution_time=0.1,  # デフォルト値
                        suggestions=result.get("recommendations", []),
                    )
                # エラー時の処理
                return QualityCheckResult(
                    check_type=check_type,
                    score=QualityScore(0.0),
                    issues=[
                        QualityIssue(
                            type="checker_error",
                            message=result.get("error", "チェッカーエラー"),
                            severity=Severity.ERROR,
                        )
                    ],
                    suggestions=[],
                )
            # 従来のチェッカーの場合
            payload = _CheckerInput(
                content=file_content.content,
                filepath=file_content.filepath,
                config=config or {},
            )
            result = checker.execute(payload)

            # 結果をドメインオブジェクトに変換
            issues: list[QualityIssue] = [
                QualityIssue(
                    type=issue_data["type"],
                    message=issue_data["message"],
                    severity=Severity(issue_data.get("severity", "info")),
                    line_number=issue_data.get("line_number"),
                    position=issue_data.get("position"),
                    suggestion=issue_data.get("suggestion"),
                    auto_fixable=issue_data.get("auto_fixable", False),
                )
                for issue_data in result.get("issues", [])
            ]

            return QualityCheckResult(
                check_type=check_type,
                score=QualityScore(result.get("score", 0.0)),
                issues=issues,
                metadata=result.get("metadata", {}),
                execution_time=result.get("execution_time", 0.0),
                suggestions=result.get("suggestions", []),
            )

        except Exception as e:
            # エラー時は低スコアの結果を返す
            return QualityCheckResult(
                check_type=check_type,
                score=QualityScore(0.0),
                issues=[
                    QualityIssue(
                        type="checker_error",
                        message=f"チェッカーエラー: {e!s}",
                        severity=Severity.ERROR,
                    )
                ],
                suggestions=[],
            )

    def _apply_auto_fixes(self, content: str, issues: list[QualityIssue]) -> str:
        """Apply simple auto-fix routines to the provided content.

        Args:
            content: Original manuscript content.
            issues: Issues flagged by the checkers.

        Returns:
            str: Content string after basic auto fixes have been applied.
        """
        fixed_content = dedent(content)

        # 自動修正可能な問題を処理
        for issue in issues:
            if issue.auto_fixable and issue.suggestion:
                # 簡易的な置換処理(実際はもっと高度な処理が必要)
                if issue.type == "punctuation":
                    fixed_content = fixed_content.replace("。。", "。")
                elif issue.type == "space":
                    suggestion = issue.suggestion
                    if "→" in suggestion:
                        before, after = suggestion.split("→", 1)
                    else:
                        before, after = "  ", " "
                    fixed_content = fixed_content.replace(before, after)
                # 他の自動修正ロジック...

        while "  " in fixed_content:
            fixed_content = fixed_content.replace("  ", " ")

        return fixed_content

    def _format_issues(self, issues: list[QualityIssue]) -> list[dict[str, Any]]:
        """Format domain issues into serialisable dictionaries.

        Args:
            issues: Issues returned by the checkers.

        Returns:
            list[dict[str, Any]]: Issues formatted for presentation layers.
        """
        return [
            {
                "type": issue.type,
                "message": issue.message,
                "severity": issue.severity.value,
                "line_number": issue.line_number,
                "position": issue.position,
                "suggestion": issue.suggestion,
                "auto_fixable": issue.auto_fixable,
            }
            for issue in issues
        ]

    def bulk_check(
        self, project_id: str, file_patterns: list[str], config: dict[str, Any] | None = None
    ) -> list[QualityCheckResponse]:
        """Run quality checks for multiple files that match the given patterns.

        Args:
            project_id: Project identifier shared by all evaluations.
            file_patterns: Glob patterns that resolve to target files.
            config: Optional configuration overrides applied to each request.

        Returns:
            list[QualityCheckResponse]: Responses produced for every matching file.
        """
        results: list[Any] = []

        for pattern in file_patterns:
            for filepath in Path().glob(pattern):
                if filepath.is_file():
                    request = QualityCheckRequest(
                        project_id=project_id,
                        filepath=filepath,
                        config=config,
                    )

                    response = self.check_quality(request)
                    results.append(response)

        return results
