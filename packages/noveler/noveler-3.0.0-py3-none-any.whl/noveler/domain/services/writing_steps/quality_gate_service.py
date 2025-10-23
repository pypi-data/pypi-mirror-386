"""Domain.services.writing_steps.quality_gate_service
Where: Domain service module implementing a specific writing workflow step.
What: Provides helper routines and data structures for this writing step.
Why: Allows stepwise writing orchestrators to reuse consistent step logic.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""STEP 13: QualityGateService

A38執筆プロンプトガイドのSTEP 13に対応するマイクロサービス。
既存のQualityCheckUseCaseを15ステップ体系に適応し、品質ゲート機能を提供。
"""

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from noveler.domain.interfaces.quality_check_interface import (
    IAdaptiveQualityEvaluationUseCase,
    IQualityCheckUseCase,
    QualityCheckRequestInterface,
    QualityCheckResponseInterface,
    QualityViolationInterface,
)
from noveler.domain.protocols.unit_of_work_protocol import IUnitOfWorkProtocol
from noveler.domain.services.writing_steps.base_writing_step import BaseWritingStep, WritingStepResponse

if TYPE_CHECKING:
    from noveler.domain.interfaces.logger_service_protocol import ILoggerService


@dataclass
class QualityGatePolicy:
    """品質ゲートポリシー"""

    # 基本設定
    min_quality_score: float = 70.0
    strict_mode: bool = False
    auto_fix_enabled: bool = True

    # カテゴリ別重要度
    critical_categories: list[str] = field(default_factory=lambda: [
        "structure", "consistency", "readability"
    ])
    warning_categories: list[str] = field(default_factory=lambda: [
        "style", "grammar", "format"
    ])

    # 適応的評価設定
    adaptive_evaluation: bool = False
    adaptive_confidence_threshold: float = 0.8


@dataclass
class QualityGateResult:
    """品質ゲート結果"""

    gate_passed: bool
    overall_score: float
    category_scores: dict[str, float] = field(default_factory=dict)

    # 違反情報
    critical_violations: list[QualityViolationInterface] = field(default_factory=list)
    warning_violations: list[QualityViolationInterface] = field(default_factory=list)

    # 自動修正情報
    auto_fixes_applied: int = 0
    fixed_content: str | None = None

    # 適応的評価結果
    adaptive_enabled: bool = False
    confidence_level: float = 0.0


@dataclass
class QualityGateResponse(WritingStepResponse):
    """品質ゲートサービス結果"""

    # 基底クラスのフィールド継承
    # success, execution_time_ms, error_message

    # 品質ゲート固有結果
    quality_result: QualityGateResult | None = None
    project_id: str = ""
    episode_id: str = ""

    # パフォーマンス情報
    quality_check_time_ms: float = 0.0
    adaptive_evaluation_time_ms: float = 0.0
    auto_fix_time_ms: float = 0.0

    # 詳細情報
    checks_performed: int = 0
    violations_found: int = 0


class QualityGateService(BaseWritingStep):
    """STEP 13: 品質ゲートマイクロサービス

    QualityCheckUseCaseを15ステップ体系に適応し、品質保証機能を提供。
    適応的品質評価、自動修正、品質ゲートポリシーを統合管理。
    """

    def __init__(
        self,
        logger_service: ILoggerService = None,
        unit_of_work: IUnitOfWorkProtocol | None = None,
        quality_policy: QualityGatePolicy | None = None,
        quality_check_use_case: IQualityCheckUseCase | None = None,
        adaptive_quality_use_case: IAdaptiveQualityEvaluationUseCase | None = None,
        **kwargs: Any
    ) -> None:
        """品質ゲートサービス初期化

        Args:
            logger_service: ロガーサービス
            unit_of_work: Unit of Work
            quality_policy: 品質ゲートポリシー
            **kwargs: BaseWritingStepの引数
        """
        super().__init__(step_number=13, step_name="quality_gate", **kwargs)

        self._logger_service = logger_service
        self._unit_of_work = unit_of_work

        # 品質ゲートポリシー設定
        self.quality_policy = quality_policy or QualityGatePolicy()

        # 品質チェックユースケース設定
        self._quality_check_use_case = quality_check_use_case or self._create_default_quality_use_case(
            logger_service,
            unit_of_work,
            kwargs,
        )
        if self._quality_check_use_case is None:
            raise RuntimeError("QualityGateService requires a quality_check_use_case implementation.")

        # 適応的品質評価ユースケース設定
        if adaptive_quality_use_case is not None:
            self._adaptive_quality_use_case = adaptive_quality_use_case
        elif self.quality_policy.adaptive_evaluation:
            self._adaptive_quality_use_case = self._create_default_adaptive_use_case(kwargs)
        else:
            self._adaptive_quality_use_case = None

    def _create_default_quality_use_case(
        self,
        logger_service: "ILoggerService | None",
        unit_of_work: IUnitOfWorkProtocol | None,
        kwargs: dict[str, Any],
    ) -> IQualityCheckUseCase | None:
        """アプリケーション層実装がある場合のみ既定の品質チェックUCを生成する。"""
        try:
            from noveler.application.use_cases.quality_check_use_case import QualityCheckUseCase  # noqa: PLC0415
        except Exception:
            return None

        try:
            return QualityCheckUseCase(logger_service=logger_service, unit_of_work=unit_of_work)
        except Exception:
            return None

    def _create_default_adaptive_use_case(self, kwargs: dict[str, Any]) -> IAdaptiveQualityEvaluationUseCase | None:
        """アプリケーション層実装がある場合のみ既定の適応評価UCを生成する。"""
        try:
            from noveler.application.use_cases.adaptive_quality_evaluation import AdaptiveQualityEvaluationUseCase  # noqa: PLC0415
        except Exception:
            return None

        try:
            return AdaptiveQualityEvaluationUseCase(
                model_repository=self._create_model_repository(),
                path_service=kwargs.get("path_service"),
            )
        except Exception:
            return None

    async def execute(
        self,
        episode_number: int,
        previous_results: dict[int, Any] | None = None
    ) -> QualityGateResponse:
        """品質ゲート実行

        Args:
            episode_number: エピソード番号
            previous_results: 前ステップの結果（原稿コンテンツが含まれる）

        Returns:
            QualityGateResponse: 品質ゲート結果
        """
        start_time = time.time()

        try:
            if self._logger_service:
                self._logger_service.info(f"STEP 13 品質ゲート開始: エピソード={episode_number}")

            # 1. 品質チェック対象取得
            project_id, episode_id = self._extract_target_info(episode_number, previous_results)

            # 2. 基本品質チェック実行
            quality_start = time.time()
            quality_response = await self._execute_quality_check(project_id, episode_id)
            quality_time = (time.time() - quality_start) * 1000

            # 3. 適応的品質評価（有効な場合）
            adaptive_time = 0.0
            if self.quality_policy.adaptive_evaluation and self._adaptive_quality_use_case:
                adaptive_start = time.time()
                quality_response = await self._apply_adaptive_evaluation(
                    project_id, episode_number, quality_response
                )
                adaptive_time = (time.time() - adaptive_start) * 1000

            # 4. 品質ゲート判定
            quality_result = self._evaluate_quality_gate(quality_response)

            # 5. 自動修正（有効で必要な場合）
            auto_fix_time = 0.0
            if (self.quality_policy.auto_fix_enabled and
                not quality_result.gate_passed and
                quality_response.auto_fix_applied):
                auto_fix_start = time.time()
                await self._apply_additional_fixes(quality_result, quality_response)
                auto_fix_time = (time.time() - auto_fix_start) * 1000

            # 6. 成功応答作成
            execution_time = (time.time() - start_time) * 1000

            return QualityGateResponse(
                success=True,
                step_number=13,
                step_name="quality_gate",
                execution_time_ms=execution_time,

                # 品質ゲート固有フィールド
                quality_result=quality_result,
                project_id=project_id,
                episode_id=episode_id,

                # パフォーマンス情報
                quality_check_time_ms=quality_time,
                adaptive_evaluation_time_ms=adaptive_time,
                auto_fix_time_ms=auto_fix_time,

                # 詳細情報
                checks_performed=len(quality_response.violations or []),
                violations_found=len([v for v in (quality_response.violations or []) if v])
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_message = f"STEP 13 品質ゲートエラー: {e}"

            if self._logger_service:
                self._logger_service.error(error_message)

            return QualityGateResponse(
                success=False,
                step_number=13,
                step_name="quality_gate",
                execution_time_ms=execution_time,
                error_message=error_message
            )

    def _extract_target_info(
        self,
        episode_number: int,
        previous_results: dict[int, Any] | None
    ) -> tuple[str, str]:
        """品質チェック対象情報抽出

        Args:
            episode_number: エピソード番号
            previous_results: 前ステップ結果

        Returns:
            tuple[str, str]: (プロジェクトID, エピソードID)
        """
        # デフォルト値
        project_id = "default_project"
        episode_id = f"episode_{episode_number:03d}"

        # 前ステップから情報抽出
        if previous_results:
            # STEP 0からプロジェクト情報取得
            if 0 in previous_results:
                scope_result = previous_results[0]
                if isinstance(scope_result, dict):
                    project_id = scope_result.get("project_id", project_id)

            # STEP 10から原稿情報取得
            if 10 in previous_results:
                manuscript_result = previous_results[10]
                if isinstance(manuscript_result, dict):
                    episode_id = manuscript_result.get("episode_id", episode_id)

        return project_id, episode_id

    async def _execute_quality_check(
        self,
        project_id: str,
        episode_id: str
    ) -> QualityCheckResponseInterface:
        """基本品質チェック実行

        Args:
            project_id: プロジェクトID
            episode_id: エピソードID

        Returns:
            QualityCheckResponseInterface: 品質チェック結果
        """
        # チェックオプション設定
        check_options = {
            "auto_fix": self.quality_policy.auto_fix_enabled,
            "strict_mode": self.quality_policy.strict_mode,
            "categories": self.quality_policy.critical_categories + self.quality_policy.warning_categories
        }

        # QualityCheckUseCaseで品質チェック実行
        request = QualityCheckRequestInterface(
            episode_id=episode_id,
            project_id=project_id,
            check_options=check_options,
            auto_fix=self.quality_policy.auto_fix_enabled,
            threshold_score=self.quality_policy.min_quality_score,
        )

        return await self._quality_check_use_case.execute(request)

    async def _apply_adaptive_evaluation(
        self,
        project_id: str,
        episode_number: int,
        quality_response: QualityCheckResponseInterface
    ) -> QualityCheckResponseInterface:
        """適応的品質評価の適用"""
        if not self._adaptive_quality_use_case:
            return quality_response

        evaluation = await self._adaptive_quality_use_case.evaluate(
            content=quality_response.fixed_content or "",
            episode_number=episode_number,
            threshold=self.quality_policy.adaptive_confidence_threshold,
        )

        if evaluation.get("adaptive_enabled", False):
            quality_response.total_score = self._calculate_adaptive_score(
                evaluation.get("adjusted_scores", {}),
                quality_response.total_score or 0.0,
            )

        return quality_response

    def _evaluate_quality_gate(self, quality_response: QualityCheckResponseInterface) -> QualityGateResult:
        """品質ゲート判定

        Args:
            quality_response: 品質チェック結果

        Returns:
            QualityGateResult: 品質ゲート結果
        """
        overall_score = quality_response.total_score or 0.0
        violations = quality_response.violations or []

        # 重要度別違反分類
        critical_violations = []
        warning_violations = []

        for violation in violations:
            if hasattr(violation, "rule_id") and any(
                cat in violation.rule_id for cat in self.quality_policy.critical_categories
            ):
                critical_violations.append(violation)
            else:
                warning_violations.append(violation)

        # ゲート判定
        gate_passed = (
            overall_score >= self.quality_policy.min_quality_score and
            len(critical_violations) == 0
        )

        # ストリクトモードでは警告も考慮
        if self.quality_policy.strict_mode:
            gate_passed = gate_passed and len(warning_violations) == 0

        return QualityGateResult(
            gate_passed=gate_passed,
            overall_score=overall_score,
            critical_violations=critical_violations,
            warning_violations=warning_violations,
            auto_fixes_applied=1 if quality_response.auto_fix_applied else 0,
            fixed_content=quality_response.fixed_content
        )

    async def _apply_additional_fixes(
        self,
        quality_result: QualityGateResult,
        quality_response: QualityCheckResponseInterface
    ) -> None:
        """追加自動修正適用

        Args:
            quality_result: 品質ゲート結果
            quality_response: 品質チェック結果
        """
        # 追加修正ロジック（将来実装）
        # 現在はログ出力のみ
        if self._logger_service:
            self._logger_service.info(
                f"追加自動修正検討: 重要違反={len(quality_result.critical_violations)}件, "
                f"警告違反={len(quality_result.warning_violations)}件"
            )

    def _convert_quality_response_to_dict(self, quality_response: QualityCheckResponseInterface) -> dict[str, Any]:
        """品質チェック結果を辞書形式に変換

        Args:
            quality_response: 品質チェック結果

        Returns:
            Dict[str, Any]: 辞書形式の品質チェック結果
        """
        checks = {}

        if quality_response.violations:
            for violation in quality_response.violations:
                if hasattr(violation, "rule_id"):
                    checks[violation.rule_id] = {
                        "score": 100.0 if not violation else 50.0,  # 簡略化スコア
                        "message": getattr(violation, "message", ""),
                        "severity": getattr(violation, "severity", "warning")
                    }

        if quality_response.total_score:
            checks["overall"] = {"score": quality_response.total_score}

        return checks

    def _calculate_adaptive_score(
        self,
        adjusted_scores: dict[str, Any],
        base_score: float
    ) -> float:
        """適応的スコア計算

        Args:
            adjusted_scores: 適応的評価による調整スコア
            base_score: 基本スコア

        Returns:
            float: 適応的調整後スコア
        """
        if not adjusted_scores:
            return base_score

        # 調整スコアの平均を計算
        score_values = []
        for score_data in adjusted_scores.values():
            if isinstance(score_data, dict) and "score" in score_data:
                score_values.append(float(score_data["score"]))
            elif isinstance(score_data, int | float):
                score_values.append(float(score_data))

        if score_values:
            return sum(score_values) / len(score_values)

        return base_score

    def _create_model_repository(self) -> Any | None:
        """学習モデルリポジトリ作成

        Returns:
            Optional[ModelRepository]: モデルリポジトリ（利用可能な場合）
        """
        # 簡易的なModelRepositoryプロトコル実装
        class SimpleModelRepository:
            def has_trained_model(self, project_id: str) -> bool:
                # 実装では実際のモデル存在確認
                return False  # 現在は常にFalse

        return SimpleModelRepository()
