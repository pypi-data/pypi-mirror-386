#!/usr/bin/env python3
"""B20統合NIH症候群防止システムテスト

SPEC: SPEC-NIH-PREVENTION-CODEMAP-001 Phase2
"""

import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from noveler.domain.entities.similarity_analyzer import SimilarityAnalyzer
from noveler.domain.services.b20_integrated_nih_prevention_service import (
    B20ComplianceLevel,
    B20IntegratedCheckResult,
    B20IntegratedNIHPreventionService,
    ImplementationJustification,
    ImplementationPermissionStatus,
)
from noveler.domain.services.machine_learning_based_similarity_service import MachineLearningBasedSimilarityService
from noveler.domain.services.similar_function_detection_service import SimilarFunctionDetectionService
from noveler.domain.value_objects.function_signature import FunctionSignature
from noveler.infrastructure.adapters.nlp_analysis_adapter import NLPAnalysisAdapter
from noveler.infrastructure.adapters.similarity_calculation_adapter import BasicSimilarityCalculationAdapter


@pytest.mark.spec("SPEC-NIH-PREVENTION-CODEMAP-001")
class TestB20IntegratedNIHPrevention:
    """B20統合NIH症候群防止システムテスト"""

    def setup_method(self):
        """テストセットアップ"""

        # テスト用関数シグネチャ
        self.new_user_function = FunctionSignature(
            name="process_new_user_data",
            module_path="noveler.domain.new_user_service",
            file_path=Path("/test/project/scripts/domain/new_user_service.py"),
            line_number=10,
            parameters=["user_id", "user_data"],
            return_type="ProcessedUser",
            docstring="新しいユーザーデータ処理機能",
            ddd_layer="domain",
        )

        self.unique_feature_function = FunctionSignature(
            name="calculate_unique_metric",
            module_path="noveler.domain.analytics_service",
            file_path=Path("/test/project/scripts/domain/analytics_service.py"),
            line_number=15,
            parameters=["data_points", "algorithm_type"],
            return_type="MetricResult",
            docstring="独自のメトリクス計算機能",
            ddd_layer="domain",
        )

        # モックコンポーネントのセットアップ
        similarity_calculator = BasicSimilarityCalculationAdapter()
        similarity_analyzer = SimilarityAnalyzer(similarity_calculator)
        nlp_analyzer = NLPAnalysisAdapter()

        mock_function_repo = Mock()
        mock_similarity_repo = Mock()

        # モックロガーの追加
        mock_logger = Mock()

        self.ml_similarity_service = MachineLearningBasedSimilarityService(
            similarity_analyzer=similarity_analyzer,
            nlp_analyzer=nlp_analyzer,
            logger=mock_logger,
            project_root=Path("/test/project")
        )

        self.detection_service = SimilarFunctionDetectionService(
            similarity_analyzer=similarity_analyzer,
            function_index_repo=mock_function_repo,
            similarity_index_repo=mock_similarity_repo,
            project_root=Path("/test/project"),
        )

        # B20統合サービス初期化
        self.b20_service = B20IntegratedNIHPreventionService(
            ml_similarity_service=self.ml_similarity_service,
            detection_service=self.detection_service,
            logger=mock_logger,
            project_root=Path("/test/project"),
            strict_mode=True,
        )

        # テスト用実装正当化
        self.valid_justification = ImplementationJustification(
            developer_name="test_developer",
            implementation_reason="新機能が既存機能では対応できない要件を満たすため",
            uniqueness_explanation="既存の処理方式では対応できない特殊なアルゴリズムを使用し、パフォーマンス要件を満たす独自の実装が必要です。",
            alternative_analysis_summary="既存の3つの類似機能を検討したが、いずれも性能要件やAPI仕様を満たせないことを確認しました。",
            expected_benefits=["パフォーマンス向上", "新しいユースケース対応"],
            risk_assessment="実装リスクは低く、テストカバレッジも十分に確保予定です。",
            maintenance_commitment="長期的なメンテナンス責任を負います",
            submission_timestamp=datetime.now(timezone.utc),
        )

    @pytest.mark.asyncio
    async def test_b20_integrated_check_approved(self):
        """B20統合チェック承認ケーステスト"""

        # ユニークな機能での実行
        result = await self.b20_service.execute_b20_integrated_check(
            self.unique_feature_function, self.valid_justification
        )

        # 承認結果の検証
        assert isinstance(result, B20IntegratedCheckResult)
        assert result.target_function == self.unique_feature_function
        assert result.is_approved() or result.permission_status == ImplementationPermissionStatus.CONDITIONAL_APPROVAL

        # B20準拠性の確認
        assert result.compliance_level in [B20ComplianceLevel.FULL_COMPLIANCE, B20ComplianceLevel.PARTIAL_COMPLIANCE]

        # 実装必要性スコアの妥当性
        assert 0.0 <= result.implementation_necessity_score <= 1.0

        # レビューコメントが生成されていることを確認
        assert len(result.reviewer_comments) > 0

    @pytest.mark.asyncio
    async def test_b20_integrated_check_rejected_high_similarity(self):
        """高類似度による拒否ケーステスト"""

        # 高類似度になりそうな関数で実行
        with patch.object(
            self.ml_similarity_service,
            "batch_analyze_ml_similarities",
            return_value=self._create_high_similarity_ml_results(),
        ):
            result = await self.b20_service.execute_b20_integrated_check(self.new_user_function)

        # 拒否結果の検証
        assert result.permission_status == ImplementationPermissionStatus.REJECTED
        assert len(result.violation_reasons) > 0
        assert any("高類似度機能存在" in reason for reason in result.violation_reasons)

        # 類似機能情報が含まれていることを確認
        assert len(result.ml_similarity_results) > 0
        assert len(result.top_similar_functions) > 0

    @pytest.mark.asyncio
    async def test_b20_integrated_check_needs_review(self):
        """レビュー必要ケーステスト"""

        # 中程度の類似度結果をモック
        with patch.object(
            self.ml_similarity_service,
            "batch_analyze_ml_similarities",
            return_value=self._create_medium_similarity_ml_results(),
        ):
            # 正当化なしで実行
            result = await self.b20_service.execute_b20_integrated_check(self.new_user_function, justification=None)

        # レビュー必要結果の検証
        assert (
            result.requires_manual_review()
            or result.permission_status == ImplementationPermissionStatus.CONDITIONAL_APPROVAL
        )

        # 条件付き承認の場合、承認条件が設定されていることを確認
        if result.permission_status == ImplementationPermissionStatus.CONDITIONAL_APPROVAL:
            assert len(result.approval_conditions) > 0

    @pytest.mark.asyncio
    async def test_b20_compliance_evaluation(self):
        """B20準拠性評価テスト"""

        # 完全準拠ケース
        result_full = await self.b20_service.execute_b20_integrated_check(
            self.unique_feature_function, self.valid_justification
        )

        # 完全準拠または部分準拠であることを確認
        assert result_full.compliance_level in [
            B20ComplianceLevel.FULL_COMPLIANCE,
            B20ComplianceLevel.PARTIAL_COMPLIANCE,
        ]

        # 非準拠ケース（正当化なし）
        result_non = await self.b20_service.execute_b20_integrated_check(self.new_user_function, justification=None)

        # 準拠レベルが低いことを確認
        assert result_non.compliance_level in [B20ComplianceLevel.PARTIAL_COMPLIANCE, B20ComplianceLevel.NON_COMPLIANCE]

    @pytest.mark.asyncio
    async def test_batch_b20_check(self):
        """バッチB20チェックテスト"""

        target_functions = [
            self.new_user_function,
            self.unique_feature_function,
            FunctionSignature(
                name="another_test_function",
                module_path="noveler.test.module",
                file_path=Path("/test/project/scripts/test/module.py"),
                line_number=20,
                parameters=["param1"],
                return_type="TestResult",
                docstring="テスト用関数",
                ddd_layer="domain",
            ),
        ]

        # バッチチェック実行
        results = await self.b20_service.batch_b20_check(target_functions, max_concurrent=2)

        # 結果検証
        assert len(results) == len(target_functions)

        for result in results:
            assert isinstance(result, B20IntegratedCheckResult)
            assert result.target_function in target_functions
            assert result.permission_status in [
                ImplementationPermissionStatus.APPROVED,
                ImplementationPermissionStatus.REJECTED,
                ImplementationPermissionStatus.NEEDS_REVIEW,
                ImplementationPermissionStatus.CONDITIONAL_APPROVAL,
            ]

    @pytest.mark.spec("SPEC-B20_INTEGRATED_NIH_PREVENTION-APPROVAL_STATISTICS")
    def test_approval_statistics(self):
        """承認統計テスト"""

        # 初期状態
        initial_stats = self.b20_service.get_approval_statistics()
        assert initial_stats["total_checks"] == 0
        assert initial_stats["approval_rate"] == 0.0

        # テスト結果を手動で履歴に追加
        test_result = B20IntegratedCheckResult(
            target_function=self.unique_feature_function,
            permission_status=ImplementationPermissionStatus.APPROVED,
            compliance_level=B20ComplianceLevel.FULL_COMPLIANCE,
            ml_similarity_results=[],
            top_similar_functions=[],
            implementation_necessity_score=0.8,
            justification=self.valid_justification,
            violation_reasons=[],
            approval_conditions=[],
            reviewer_comments=["承認"],
            review_timestamp=datetime.now(timezone.utc),
        )

        self.b20_service._record_approval_history(test_result)

        # 統計更新確認
        updated_stats = self.b20_service.get_approval_statistics()
        assert updated_stats["total_checks"] == 1
        assert updated_stats["approval_rate"] == 1.0
        assert updated_stats["approved_count"] == 1

    @pytest.mark.spec("SPEC-B20_INTEGRATED_NIH_PREVENTION-FORCE_APPROVE_IMPLEM")
    def test_force_approve_implementation(self):
        """強制承認テスト"""

        # 強制承認実行
        force_result = self.b20_service.force_approve_implementation(
            self.new_user_function, approver="admin_user", override_reason="緊急リリース対応"
        )

        # 強制承認結果の検証
        assert force_result.is_approved()
        assert force_result.compliance_level == B20ComplianceLevel.EXEMPTED
        assert force_result.implementation_necessity_score == 1.0
        assert any("強制承認" in condition for condition in force_result.approval_conditions)
        assert any("管理者による強制承認" in comment for comment in force_result.reviewer_comments)

        # 履歴に記録されていることを確認
        stats = self.b20_service.get_approval_statistics()
        assert stats["total_checks"] > 0

    @pytest.mark.spec("SPEC-B20_INTEGRATED_NIH_PREVENTION-IMPLEMENTATION_JUSTI")
    def test_implementation_justification_validation(self):
        """実装正当化バリデーションテスト"""

        # 有効な正当化
        assert self.valid_justification.is_sufficiently_detailed()

        # 不十分な正当化
        insufficient_justification = ImplementationJustification(
            developer_name="test",
            implementation_reason="短い理由",
            uniqueness_explanation="短い説明",
            alternative_analysis_summary="短い",
            expected_benefits=["メリット1"],
            risk_assessment="短い",
            maintenance_commitment="維持",
            submission_timestamp=datetime.now(timezone.utc),
        )

        assert not insufficient_justification.is_sufficiently_detailed()

    @pytest.mark.spec("SPEC-B20_INTEGRATED_NIH_PREVENTION-RESULT_HELPER_METHOD")
    def test_result_helper_methods(self):
        """結果ヘルパーメソッドテスト"""

        # 承認結果
        approved_result = B20IntegratedCheckResult(
            target_function=self.unique_feature_function,
            permission_status=ImplementationPermissionStatus.APPROVED,
            compliance_level=B20ComplianceLevel.FULL_COMPLIANCE,
            ml_similarity_results=[],
            top_similar_functions=[],
            implementation_necessity_score=0.9,
            justification=None,
            violation_reasons=[],
            approval_conditions=[],
            reviewer_comments=[],
            review_timestamp=datetime.now(timezone.utc),
        )

        assert approved_result.is_approved()
        assert not approved_result.requires_manual_review()

        # 拒否結果
        rejected_result = B20IntegratedCheckResult(
            target_function=self.new_user_function,
            permission_status=ImplementationPermissionStatus.REJECTED,
            compliance_level=B20ComplianceLevel.NON_COMPLIANCE,
            ml_similarity_results=[],
            top_similar_functions=[],
            implementation_necessity_score=0.2,
            justification=None,
            violation_reasons=["類似機能存在", "正当化不足"],
            approval_conditions=[],
            reviewer_comments=[],
            review_timestamp=datetime.now(timezone.utc),
        )

        assert not rejected_result.is_approved()
        rejection_summary = rejected_result.get_rejection_summary()
        assert "類似機能存在" in rejection_summary
        assert "正当化不足" in rejection_summary

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """エラーハンドリングテスト"""

        # 不正な関数シグネチャでのテスト
        invalid_function = FunctionSignature(name="", module_path="", file_path=Path("/invalid"), line_number=0)

        # エラーが発生してもシステムが停止しないことを確認
        result = await self.b20_service.execute_b20_integrated_check(invalid_function)

        assert isinstance(result, B20IntegratedCheckResult)
        assert result.permission_status in [
            ImplementationPermissionStatus.NEEDS_REVIEW,
            ImplementationPermissionStatus.REJECTED,
        ]
        assert len(result.violation_reasons) > 0 or len(result.reviewer_comments) > 0

    @pytest.mark.asyncio
    async def test_performance_with_concurrent_checks(self):
        """並行チェック性能テスト"""

        # 多数の関数を生成
        large_function_list = []
        for i in range(20):  # テスト用に数を調整
            func = FunctionSignature(
                name=f"test_function_{i}",
                module_path=f"noveler.test.module_{i}",
                file_path=Path(f"/test/project/scripts/test/module_{i}.py"),
                line_number=10 + i,
                parameters=[f"param_{j}" for j in range(i % 3 + 1)],
                return_type=f"Result{i}",
                docstring=f"テスト関数{i}",
                ddd_layer="domain",
            )

            large_function_list.append(func)

        # 並行実行時間測定
        start_time = time.perf_counter()

        results = await self.b20_service.batch_b20_check(large_function_list, max_concurrent=5)

        end_time = time.perf_counter()
        execution_time = end_time - start_time

        # パフォーマンス検証
        assert execution_time < 30.0  # 30秒以内（要調整）
        assert len(results) == len(large_function_list)

        # 全結果が有効であることを確認
        for result in results:
            assert isinstance(result, B20IntegratedCheckResult)
            assert result.target_function in large_function_list

    def _create_high_similarity_ml_results(self):
        """高類似度MLテスト結果作成"""

        from noveler.domain.services.machine_learning_based_similarity_service import (
            MLSimilarityFeatures,
            MLSimilarityResult,
        )

        high_sim_features = MLSimilarityFeatures(
            syntactic_score=0.9,
            semantic_score=0.95,
            functional_score=0.9,
            architectural_score=0.8,
            nlp_similarity_score=0.92,
            intent_similarity_score=0.88,
            structural_complexity_score=0.85,
            confidence_score=0.9,
        )

        similar_function = FunctionSignature(
            name="existing_user_processor",
            module_path="noveler.domain.user_service",
            file_path=Path("/project/scripts/domain/user_service.py"),
            line_number=20,
            parameters=["user_data"],
            return_type="ProcessedUser",
            docstring="既存のユーザー処理機能",
            ddd_layer="domain",
        )

        return [
            MLSimilarityResult(
                source_function=self.new_user_function,
                target_function=similar_function,
                ml_features=high_sim_features,
                overall_ml_similarity=0.91,
                confidence_level="high",
                recommended_action="reuse",
                reasoning="非常に高い類似度",
                feature_importance_ranking=[("semantic", 0.95), ("nlp_similarity", 0.92)],
            )
        ]

    def _create_medium_similarity_ml_results(self):
        """中程度類似度MLテスト結果作成"""

        from noveler.domain.services.machine_learning_based_similarity_service import (
            MLSimilarityFeatures,
            MLSimilarityResult,
        )

        medium_sim_features = MLSimilarityFeatures(
            syntactic_score=0.6,
            semantic_score=0.7,
            functional_score=0.5,
            architectural_score=0.8,
            nlp_similarity_score=0.65,
            intent_similarity_score=0.6,
            structural_complexity_score=0.7,
            confidence_score=0.6,
        )

        similar_function = FunctionSignature(
            name="related_function",
            module_path="noveler.domain.related_service",
            file_path=Path("/project/scripts/domain/related_service.py"),
            line_number=30,
            parameters=["data"],
            return_type="Result",
            docstring="関連機能",
            ddd_layer="domain",
        )

        return [
            MLSimilarityResult(
                source_function=self.new_user_function,
                target_function=similar_function,
                ml_features=medium_sim_features,
                overall_ml_similarity=0.65,
                confidence_level="medium",
                recommended_action="extend",
                reasoning="中程度の類似度",
                feature_importance_ranking=[("architectural", 0.8), ("semantic", 0.7)],
            )
        ]


@pytest.mark.spec("SPEC-NIH-PREVENTION-CODEMAP-001")
class TestB20IntegratedEndToEnd:
    """B20統合システムエンドツーエンドテスト"""

    @pytest.mark.asyncio
    async def test_complete_b20_workflow(self):
        """完全B20ワークフローテスト"""

        # システム準備
        similarity_calculator = BasicSimilarityCalculationAdapter()
        similarity_analyzer = SimilarityAnalyzer(similarity_calculator)
        nlp_analyzer = NLPAnalysisAdapter()

        mock_function_repo = Mock()
        mock_similarity_repo = Mock()

        # モックロガーの追加
        mock_logger = Mock()

        ml_service = MachineLearningBasedSimilarityService(
            similarity_analyzer=similarity_analyzer,
            nlp_analyzer=nlp_analyzer,
            logger=mock_logger,
            project_root=Path("/test/project")
        )

        detection_service = SimilarFunctionDetectionService(
            similarity_analyzer=similarity_analyzer,
            function_index_repo=mock_function_repo,
            similarity_index_repo=mock_similarity_repo,
            project_root=Path("/test/project"),
        )

        b20_service = B20IntegratedNIHPreventionService(
            ml_similarity_service=ml_service,
            detection_service=detection_service,
            logger=mock_logger,
            project_root=Path("/test/project"),
            strict_mode=True,
        )

        # テストシナリオ: 新しいセキュリティ機能の実装申請
        new_security_function = FunctionSignature(
            name="validate_security_token",
            module_path="noveler.infrastructure.security_service",
            file_path=Path("/test/project/scripts/infrastructure/security_service.py"),
            line_number=25,
            parameters=["token", "context"],
            return_type="ValidationResult",
            docstring="セキュリティトークンの検証機能",
            ddd_layer="infrastructure",
        )

        justification = ImplementationJustification(
            developer_name="security_team",
            implementation_reason="新しいセキュリティ要件に対応するため、既存の認証機能では不十分で独自実装が必要です",
            uniqueness_explanation="従来のトークン検証では対応できない新しいセキュリティ標準（OAuth 2.1）への準拠が必要で、アルゴリズムと検証ロジックが根本的に異なります",
            alternative_analysis_summary="既存の5つの認証関連機能を検証したが、いずれも新しいセキュリティ標準の要件を満たせないことを確認しました",
            expected_benefits=["セキュリティ強化", "新標準準拠", "将来的な拡張性確保"],
            risk_assessment="セキュリティチームによる十分なレビューを実施し、テスト環境での検証も完了済みです",
            maintenance_commitment="セキュリティチームが長期的な保守責任を負います",
            submission_timestamp=datetime.now(timezone.utc),
        )

        # エンドツーエンドワークフロー実行
        result = await b20_service.execute_b20_integrated_check(new_security_function, justification)

        # エンドツーエンドの検証
        assert isinstance(result, B20IntegratedCheckResult)
        assert result.target_function == new_security_function
        assert result.justification == justification

        # B20プロセス統合の確認
        assert result.permission_status in [
            ImplementationPermissionStatus.APPROVED,
            ImplementationPermissionStatus.CONDITIONAL_APPROVAL,
            ImplementationPermissionStatus.NEEDS_REVIEW,
        ]

        # 機械学習分析が実行されていることを確認
        assert isinstance(result.ml_similarity_results, list)
        assert isinstance(result.top_similar_functions, list)
        assert 0.0 <= result.implementation_necessity_score <= 1.0

        # B20準拠性評価が実行されていることを確認
        assert result.compliance_level in [
            B20ComplianceLevel.FULL_COMPLIANCE,
            B20ComplianceLevel.PARTIAL_COMPLIANCE,
            B20ComplianceLevel.NON_COMPLIANCE,
        ]

        # レビューコメントが生成されていることを確認
        assert len(result.reviewer_comments) > 0

        # 統計が更新されていることを確認
        stats = b20_service.get_approval_statistics()
        assert stats["total_checks"] > 0

        print(
            f"E2Eテスト完了: 許可ステータス={result.permission_status.value}, B20準拠={result.compliance_level.value}"
        )
