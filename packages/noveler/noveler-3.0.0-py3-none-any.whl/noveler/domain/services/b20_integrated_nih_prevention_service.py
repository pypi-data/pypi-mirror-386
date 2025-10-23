#!/usr/bin/env python3
"""B20統合NIH症候群防止サービス - Phase2

SPEC: SPEC-NIH-PREVENTION-CODEMAP-001 Phase2
責務: B20開発プロセスと統合した実装前強制チェック・許可システム
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from noveler.domain.services.machine_learning_based_similarity_service import (
    MachineLearningBasedSimilarityService,
    MLSimilarityResult,
)
from noveler.domain.services.similar_function_detection_service import SimilarFunctionDetectionService
from noveler.domain.value_objects.function_signature import FunctionSignature
from noveler.domain.value_objects.project_time import project_now

if TYPE_CHECKING:
    from noveler.domain.interfaces.logger_interface import ILogger
else:
    from noveler.domain.interfaces.logger_interface import NullLogger


class ImplementationPermissionStatus(Enum):
    """実装許可ステータス"""

    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"
    CONDITIONAL_APPROVAL = "conditional_approval"


class B20ComplianceLevel(Enum):
    """B20準拠レベル"""

    FULL_COMPLIANCE = "full_compliance"
    PARTIAL_COMPLIANCE = "partial_compliance"
    NON_COMPLIANCE = "non_compliance"
    EXEMPTED = "exempted"


@dataclass
class B20CheckRequirement:
    """B20チェック要件"""

    similarity_analysis_required: bool = True
    existing_function_survey_required: bool = True
    design_review_required: bool = True
    implementation_justification_required: bool = True
    min_similar_function_check_count: int = 5
    similarity_threshold_for_rejection: float = 0.9
    similarity_threshold_for_review: float = 0.7


@dataclass
class ImplementationJustification:
    """実装正当性証明"""

    developer_name: str
    implementation_reason: str
    uniqueness_explanation: str
    alternative_analysis_summary: str
    expected_benefits: list[str]
    risk_assessment: str
    maintenance_commitment: str
    submission_timestamp: datetime

    def is_sufficiently_detailed(self) -> bool:
        """十分詳細な正当化かチェック"""
        return (
            len(self.implementation_reason) >= 20
            and len(self.uniqueness_explanation) >= 40
            and len(self.alternative_analysis_summary) >= 30
            and len(self.expected_benefits) >= 1
            and len(self.risk_assessment) >= 25
        )


@dataclass
class B20IntegratedCheckResult:
    """B20統合チェック結果"""

    target_function: FunctionSignature
    permission_status: ImplementationPermissionStatus
    compliance_level: B20ComplianceLevel
    ml_similarity_results: list[MLSimilarityResult]
    top_similar_functions: list[tuple[FunctionSignature, float]]
    implementation_necessity_score: float
    justification: ImplementationJustification | None
    violation_reasons: list[str]
    approval_conditions: list[str]
    reviewer_comments: list[str]
    review_timestamp: datetime

    def is_approved(self) -> bool:
        """実装承認済みか判定"""
        return self.permission_status == ImplementationPermissionStatus.APPROVED

    def requires_manual_review(self) -> bool:
        """手動レビュー必要か判定"""
        return self.permission_status == ImplementationPermissionStatus.NEEDS_REVIEW

    def get_rejection_summary(self) -> str:
        """拒否理由サマリー生成"""
        if not self.violation_reasons:
            return "拒否理由なし"

        return " | ".join(self.violation_reasons)

    def get_approval_conditions_summary(self) -> str:
        """承認条件サマリー生成"""
        if not self.approval_conditions:
            return "条件なし"

        return " | ".join(self.approval_conditions)


class B20IntegratedNIHPreventionService:
    """B20統合NIH症候群防止サービス"""

    def __init__(
        self,
        ml_similarity_service: MachineLearningBasedSimilarityService,
        detection_service: SimilarFunctionDetectionService,
        project_root: Path,
        logger: "ILogger | None" = None,
        strict_mode: bool = True,
    ) -> None:
        """初期化

        Args:
            ml_similarity_service: 機械学習ベース類似度サービス
            detection_service: 類似関数検出サービス
            project_root: プロジェクトルートパス
            logger: ロガーインターフェース（DI注入）
            strict_mode: 厳格モード有効化
        """
        self.ml_similarity_service = ml_similarity_service
        self.detection_service = detection_service
        self.project_root = project_root
        self._logger = logger if logger is not None else NullLogger()
        self.strict_mode = strict_mode

        # B20チェック要件設定
        self.check_requirements = B20CheckRequirement()
        if strict_mode:
            self.check_requirements.min_similar_function_check_count = 10
            self.check_requirements.similarity_threshold_for_rejection = 0.85
            self.check_requirements.similarity_threshold_for_review = 0.65

        # 承認履歴（実際の実装では永続化が必要）
        self.approval_history: dict[str, B20IntegratedCheckResult] = {}

        self._logger.info("B20IntegratedNIHPreventionService初期化完了 (strict_mode: %s)", strict_mode=strict_mode)

    async def execute_b20_integrated_check(
        self,
        target_function: FunctionSignature,
        justification: ImplementationJustification | None = None,
        bypass_similarity_check: bool = False,
    ) -> B20IntegratedCheckResult:
        """B20統合チェック実行"""

        self._logger.info("B20統合チェック開始: %s", target_function_name=target_function.name)

        try:
            # Phase 1: 類似機能検出
            ml_results = []
            top_similar_functions = []

            if not bypass_similarity_check:
                ml_results = await self._execute_ml_similarity_analysis(target_function)
                top_similar_functions = self._extract_top_similar_functions(ml_results)

            # Phase 2: 実装必要性評価
            necessity_score = self._calculate_implementation_necessity(ml_results, target_function)

            # Phase 3: B20準拠性評価
            compliance_level = self._evaluate_b20_compliance(target_function, ml_results, justification)

            # Phase 4: 許可判定
            permission_status, violation_reasons, approval_conditions = self._determine_permission_status(
                target_function, ml_results, necessity_score, justification, compliance_level
            )

            # Phase 5: レビューコメント生成
            reviewer_comments = self._generate_reviewer_comments(
                target_function, ml_results, necessity_score, permission_status
            )

            # 結果構築
            result = B20IntegratedCheckResult(
                target_function=target_function,
                permission_status=permission_status,
                compliance_level=compliance_level,
                ml_similarity_results=ml_results,
                top_similar_functions=top_similar_functions,
                implementation_necessity_score=necessity_score,
                justification=justification,
                violation_reasons=violation_reasons,
                approval_conditions=approval_conditions,
                reviewer_comments=reviewer_comments,
                review_timestamp=project_now().datetime,
            )

            # 承認履歴記録
            self._record_approval_history(result)

            self._logger.info("B20統合チェック完了: %s -> %s", target_function_name=target_function.name, permission_status=permission_status.value)

            return result

        except Exception as e:
            self._logger.exception("B20統合チェックエラー: %s: %s", target_function_name=target_function.name, error=str(e))
            return self._create_error_result(target_function, str(e))

    async def batch_b20_check(
        self, target_functions: list[FunctionSignature], max_concurrent: int = 3
    ) -> list[B20IntegratedCheckResult]:
        """バッチB20チェック実行"""

        self._logger.info("バッチB20チェック開始: %s件", function_count=len(target_functions))

        # 並行実行制御
        semaphore = asyncio.Semaphore(max_concurrent)

        async def check_with_semaphore(func: FunctionSignature) -> B20IntegratedCheckResult:
            async with semaphore:
                return await self.execute_b20_integrated_check(func)

        # 並行実行
        tasks = [check_with_semaphore(func) for func in target_functions]
        results: Any = await asyncio.gather(*tasks, return_exceptions=True)

        # エラー処理
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self._logger.error("バッチチェックエラー (%s): %s", target_function_name=target_functions[i].name, error=str(result))
                error_result = self._create_error_result(target_functions[i], str(result))
                valid_results.append(error_result)
            else:
                valid_results.append(result)

        self._logger.info("バッチB20チェック完了: %s件", result_count=len(valid_results))
        return valid_results

    def get_approval_statistics(self) -> dict[str, Any]:
        """承認統計取得"""

        if not self.approval_history:
            return {"total_checks": 0, "approval_rate": 0.0, "rejection_rate": 0.0, "review_required_rate": 0.0}

        total = len(self.approval_history)
        approved = sum(
            1
            for result in self.approval_history.values()
            if result.permission_status == ImplementationPermissionStatus.APPROVED
        )

        rejected = sum(
            1
            for result in self.approval_history.values()
            if result.permission_status == ImplementationPermissionStatus.REJECTED
        )

        review_needed = sum(
            1
            for result in self.approval_history.values()
            if result.permission_status == ImplementationPermissionStatus.NEEDS_REVIEW
        )

        return {
            "total_checks": total,
            "approval_rate": approved / total if total > 0 else 0.0,
            "rejection_rate": rejected / total if total > 0 else 0.0,
            "review_required_rate": review_needed / total if total > 0 else 0.0,
            "approved_count": approved,
            "rejected_count": rejected,
            "review_needed_count": review_needed,
            "b20_compliance_rate": self._calculate_b20_compliance_rate(),
        }

    def force_approve_implementation(
        self, target_function: FunctionSignature, approver: str, override_reason: str
    ) -> B20IntegratedCheckResult:
        """実装強制承認（緊急時・管理者権限）"""

        self._logger.warning("実装強制承認: %s by %s", target_function_name=target_function.name, approver=approver)

        # 強制承認結果作成
        force_approval_result = B20IntegratedCheckResult(
            target_function=target_function,
            permission_status=ImplementationPermissionStatus.APPROVED,
            compliance_level=B20ComplianceLevel.EXEMPTED,
            ml_similarity_results=[],
            top_similar_functions=[],
            implementation_necessity_score=1.0,
            justification=None,
            violation_reasons=[],
            approval_conditions=[f"強制承認 (承認者: {approver})"],
            reviewer_comments=[f"管理者による強制承認: {override_reason}"],
            review_timestamp=project_now().datetime,
        )

        # 履歴記録
        self._record_approval_history(force_approval_result)

        return force_approval_result

    async def _execute_ml_similarity_analysis(self, target_function: FunctionSignature) -> list[MLSimilarityResult]:
        """機械学習類似度分析実行"""

        # 候補関数の取得（実際の実装では関数インデックスから取得）
        # ここでは簡略化してモックデータ使用
        mock_candidates = self._get_mock_candidate_functions()

        if not mock_candidates:
            self._logger.warning("候補関数が見つからないため、類似度分析をスキップ")
            return []

        # バッチ機械学習類似度分析
        results: Any = self.ml_similarity_service.batch_analyze_ml_similarities(
            target_function, mock_candidates, max_results=self.check_requirements.min_similar_function_check_count
        )

        return results

    def _get_mock_candidate_functions(self) -> list[FunctionSignature]:
        """モック候補関数取得（テスト用）"""
        return [
            FunctionSignature(
                name="existing_user_processor",
                module_path="noveler.domain.user_service",
                file_path=Path("/project/scripts/domain/user_service.py"),  # TODO: IPathServiceを使用するように修正
                line_number=20,
                parameters=["user_data"],
                return_type="ProcessedUser",
                docstring="既存のユーザー処理機能",
                ddd_layer="domain",
            ),
            FunctionSignature(
                name="handle_customer_data",
                module_path="noveler.application.customer_service",
                file_path=Path("/project/scripts/application/customer_service.py"),  # TODO: IPathServiceを使用するように修正
                line_number=30,
                parameters=["customer_info"],
                return_type="CustomerResult",
                docstring="顧客データ処理機能",
                ddd_layer="application",
            ),
        ]

    def _extract_top_similar_functions(
        self, ml_results: list[MLSimilarityResult]
    ) -> list[tuple[FunctionSignature, float]]:
        """上位類似関数抽出"""

        similar_functions = []
        for result in ml_results:
            similar_functions.append((result.target_function, result.overall_ml_similarity))

        # 類似度順にソート
        similar_functions.sort(key=lambda x: x[1], reverse=True)

        return similar_functions[:5]  # 上位5件

    def _calculate_implementation_necessity(
        self, ml_results: list[MLSimilarityResult], target_function: FunctionSignature
    ) -> float:
        """実装必要性計算"""

        if not ml_results:
            return 1.0  # 類似機能なしの場合は実装必要

        # 最高類似度の取得
        max_similarity = max(result.overall_ml_similarity for result in ml_results)

        # 実装必要性スコア = 1 - 最高類似度
        necessity_score = 1.0 - max_similarity

        # 同一レイヤーでの類似機能がある場合はペナルティ
        same_layer_penalty = 0.0
        for result in ml_results:
            if result.target_function.ddd_layer == target_function.ddd_layer and result.overall_ml_similarity > 0.6:
                same_layer_penalty += 0.1

        necessity_score = max(0.0, necessity_score - same_layer_penalty)

        return min(1.0, necessity_score)

    def _evaluate_b20_compliance(
        self,
        target_function: FunctionSignature,
        ml_results: list[MLSimilarityResult],
        justification: ImplementationJustification | None,
    ) -> B20ComplianceLevel:
        """B20準拠性評価"""

        compliance_score = 0
        max_score = 4

        # 1. 類似度分析実施確認
        if ml_results:
            compliance_score += 1

        # 2. 十分な候補数チェック（基準を緩和）
        if len(ml_results) >= max(1, self.check_requirements.min_similar_function_check_count // 2):
            compliance_score += 1

        # 3. 実装正当化提出確認
        if justification is not None:
            compliance_score += 1

        # 4. 正当化の詳細度確認
        if justification and justification.is_sufficiently_detailed():
            compliance_score += 1

        # 準拠レベル判定（基準を緩和）
        if compliance_score >= max_score * 0.75:
            return B20ComplianceLevel.FULL_COMPLIANCE
        if compliance_score >= max_score * 0.5:
            return B20ComplianceLevel.PARTIAL_COMPLIANCE
        return B20ComplianceLevel.NON_COMPLIANCE

    def _determine_permission_status(
        self,
        target_function: FunctionSignature,
        ml_results: list[MLSimilarityResult],
        necessity_score: float,
        justification: ImplementationJustification | None,
        compliance_level: B20ComplianceLevel,
    ) -> tuple[ImplementationPermissionStatus, list[str], list[str]]:
        """許可ステータス判定"""

        approval_conditions = []
        critical_violations = []

        # 高類似度による重大違反判定
        for result in ml_results:
            if result.overall_ml_similarity >= self.check_requirements.similarity_threshold_for_rejection:
                critical_violations.append(
                    f"高類似度機能存在: {result.target_function.name} (類似度: {result.overall_ml_similarity:.2f})"
                )

        # 実装必要性の重大不足チェック
        if necessity_score < 0.1:
            critical_violations.append(f"実装必要性不足: {necessity_score:.2f}")

        # 重大違反がある場合は拒否
        if critical_violations:
            return ImplementationPermissionStatus.REJECTED, critical_violations, []

        # 中程度の問題をチェック
        moderate_issues = []

        # B20準拠性チェック
        if compliance_level == B20ComplianceLevel.NON_COMPLIANCE:
            moderate_issues.append("B20開発プロセス非準拠")

        # 実装必要性チェック（中程度）
        if necessity_score < 0.3:
            moderate_issues.append(f"実装必要性不足: {necessity_score:.2f}")

        # 正当化不足チェック
        if justification is None and any(
            result.overall_ml_similarity >= self.check_requirements.similarity_threshold_for_review
            for result in ml_results
        ):
            moderate_issues.append("類似機能存在時の実装正当化未提出")

        # 正当化があっても十分でない場合
        if justification and not justification.is_sufficiently_detailed() and any(
            result.overall_ml_similarity >= self.check_requirements.similarity_threshold_for_review
            for result in ml_results
        ):
            moderate_issues.append("実装正当化の詳細度不足")

        # 中程度の問題への対応判定
        if moderate_issues:
            # 正当化が十分な場合は条件付き承認
            if justification and justification.is_sufficiently_detailed():
                return ImplementationPermissionStatus.CONDITIONAL_APPROVAL, [], moderate_issues
            # そうでなければ手動レビュー必要
            return ImplementationPermissionStatus.NEEDS_REVIEW, moderate_issues, []

        # 条件付き承認チェック
        for result in ml_results:
            if result.overall_ml_similarity >= self.check_requirements.similarity_threshold_for_review:
                approval_conditions.append(f"類似機能との差分明確化必要: {result.target_function.name}")

        if compliance_level == B20ComplianceLevel.PARTIAL_COMPLIANCE:
            approval_conditions.append("B20プロセス完全準拠の確認が必要")

        if approval_conditions:
            return ImplementationPermissionStatus.CONDITIONAL_APPROVAL, [], approval_conditions

        return ImplementationPermissionStatus.APPROVED, [], []

    def _generate_reviewer_comments(
        self,
        target_function: FunctionSignature,
        ml_results: list[MLSimilarityResult],
        necessity_score: float,
        permission_status: ImplementationPermissionStatus,
    ) -> list[str]:
        """レビューコメント生成"""

        comments = []

        # 類似度分析結果コメント
        if ml_results:
            top_similarity = max(result.overall_ml_similarity for result in ml_results)
            comments.append(f"最高類似度: {top_similarity:.2f}")

            if top_similarity > 0.8:
                comments.append("高類似度機能が存在します。再利用を強く推奨")
            elif top_similarity > 0.6:
                comments.append("中程度の類似機能が存在します。拡張での対応も検討してください")

        # 実装必要性コメント
        comments.append(f"実装必要性スコア: {necessity_score:.2f}")

        if necessity_score < 0.5:
            comments.append("実装必要性が低いため、既存機能の活用を検討してください")

        # ステータス別コメント
        if permission_status == ImplementationPermissionStatus.APPROVED:
            comments.append("実装が承認されました")
        elif permission_status == ImplementationPermissionStatus.REJECTED:
            comments.append("実装が拒否されました。代替案を検討してください")
        elif permission_status == ImplementationPermissionStatus.CONDITIONAL_APPROVAL:
            comments.append("条件付き承認です。指定条件を満たしてから実装してください")

        return comments

    def _calculate_b20_compliance_rate(self) -> float:
        """B20準拠率計算"""

        if not self.approval_history:
            return 1.0

        compliant_count = sum(
            1
            for result in self.approval_history.values()
            if result.compliance_level in [B20ComplianceLevel.FULL_COMPLIANCE, B20ComplianceLevel.PARTIAL_COMPLIANCE]
        )

        return compliant_count / len(self.approval_history)

    def _record_approval_history(self, result: B20IntegratedCheckResult) -> None:
        """承認履歴記録"""

        function_key = f"{result.target_function.module_path}:{result.target_function.name}"
        self.approval_history[function_key] = result

        self._logger.debug("承認履歴記録: %s -> %s", function_key=function_key, permission_status=result.permission_status.value)

    def _create_error_result(self, target_function: FunctionSignature, error_message: str) -> B20IntegratedCheckResult:
        """エラー時のデフォルト結果作成"""

        return B20IntegratedCheckResult(
            target_function=target_function,
            permission_status=ImplementationPermissionStatus.NEEDS_REVIEW,
            compliance_level=B20ComplianceLevel.NON_COMPLIANCE,
            ml_similarity_results=[],
            top_similar_functions=[],
            implementation_necessity_score=0.0,
            justification=None,
            violation_reasons=[f"システムエラー: {error_message}"],
            approval_conditions=[],
            reviewer_comments=[f"エラー発生のため手動レビューが必要: {error_message}"],
            review_timestamp=project_now().datetime,
        )
