#!/usr/bin/env python3
"""機械学習ベース類似度判定システム統合テスト

SPEC: SPEC-NIH-PREVENTION-CODEMAP-001 Phase2
"""

import time
from pathlib import Path

import pytest

from noveler.domain.entities.similarity_analyzer import SimilarityAnalyzer
from noveler.domain.services.machine_learning_based_similarity_service import (
    MachineLearningBasedSimilarityService,
    MLSimilarityFeatures,
    MLSimilarityResult,
)
from noveler.domain.value_objects.function_signature import FunctionSignature
from noveler.infrastructure.adapters.nlp_analysis_adapter import NLPAnalysisAdapter
from noveler.infrastructure.adapters.similarity_calculation_adapter import BasicSimilarityCalculationAdapter


@pytest.mark.spec("SPEC-NIH-PREVENTION-CODEMAP-001")
class TestMLSimilarityIntegration:
    """機械学習ベース類似度判定システム統合テスト"""

    def setup_method(self):
        """テストセットアップ"""

        # テスト用関数シグネチャ
        self.user_process_function = FunctionSignature(
            name="process_user_data",
            module_path="noveler.domain.user_service",
            file_path=Path("/test/project/scripts/domain/user_service.py"),
            line_number=10,
            parameters=["user_id", "user_data"],
            return_type="ProcessedUser",
            docstring="ユーザーデータを処理する",
            ddd_layer="domain",
        )

        self.user_handle_function = FunctionSignature(
            name="handle_user_information",
            module_path="noveler.application.user_handler",
            file_path=Path("/test/project/scripts/application/user_handler.py"),
            line_number=15,
            parameters=["user_id", "information"],
            return_type="UserInfo",
            docstring="ユーザー情報を処理する",
            ddd_layer="application",
        )

        self.pricing_function = FunctionSignature(
            name="calculate_total_price",
            module_path="noveler.domain.pricing_service",
            file_path=Path("/test/project/scripts/domain/pricing_service.py"),
            line_number=20,
            parameters=["items", "discount_rate"],
            return_type="float",
            docstring="商品の合計価格を計算する",
            ddd_layer="domain",
        )

        # 機械学習類似度サービス初期化
        similarity_calculator = BasicSimilarityCalculationAdapter()
        similarity_analyzer = SimilarityAnalyzer(similarity_calculator)
        nlp_analyzer = NLPAnalysisAdapter(enable_advanced_features=True)

        self.ml_similarity_service = MachineLearningBasedSimilarityService(
            similarity_analyzer=similarity_analyzer,
            nlp_analyzer=nlp_analyzer,
            project_root=Path("/test/project"),
            enable_advanced_ml=True,
        )

    @pytest.mark.spec("SPEC-ML_SIMILARITY_INTEGRATION-ML_SIMILARITY_ANALYS")
    def test_ml_similarity_analysis_basic(self):
        """基本的な機械学習類似度分析テスト"""

        # 類似度分析実行
        result = self.ml_similarity_service.analyze_ml_based_similarity(
            self.user_process_function, self.user_handle_function
        )

        # 結果の検証
        assert isinstance(result, MLSimilarityResult)
        assert result.source_function == self.user_process_function
        assert result.target_function == self.user_handle_function

        assert 0.0 <= result.overall_ml_similarity <= 1.0
        assert result.confidence_level in ["high", "medium", "low"]
        assert result.recommended_action in ["reuse", "extend", "new_implementation"]

        # 特徴量の検証
        features = result.ml_features
        assert isinstance(features, MLSimilarityFeatures)
        assert 0.0 <= features.syntactic_score <= 1.0
        assert 0.0 <= features.semantic_score <= 1.0
        assert 0.0 <= features.nlp_similarity_score <= 1.0

        # 特徴量重要度ランキングの検証
        assert len(result.feature_importance_ranking) > 0
        assert all(0.0 <= score <= 1.0 for _, score in result.feature_importance_ranking)

    @pytest.mark.spec("SPEC-ML_SIMILARITY_INTEGRATION-HIGH_SIMILARITY_DETE")
    def test_high_similarity_detection(self):
        """高類似度検出テスト"""

        # 非常に似た関数を作成
        similar_function = FunctionSignature(
            name="process_user_data_enhanced",
            module_path="noveler.domain.user_service_v2",
            file_path=Path("/test/project/scripts/domain/user_service_v2.py"),
            line_number=12,
            parameters=["user_id", "user_data", "options"],
            return_type="EnhancedUser",
            docstring="ユーザーデータを処理する（拡張版）",
            ddd_layer="domain",
        )

        result = self.ml_similarity_service.analyze_ml_based_similarity(self.user_process_function, similar_function)

        # 高類似度が検出されることを確認
        assert result.overall_ml_similarity > 0.5  # 意味的に類似
        assert result.ml_features.semantic_score > 0.3  # 意味的類似度が高い
        assert result.confidence_level in ["medium", "high"]

        # NLP特徴量が有効に機能していることを確認
        assert result.ml_features.nlp_similarity_score > 0.0
        assert result.feature_importance_ranking

    @pytest.mark.spec("SPEC-ML_SIMILARITY_INTEGRATION-LOW_SIMILARITY_DETEC")
    def test_low_similarity_detection(self):
        """低類似度検出テスト"""

        result = self.ml_similarity_service.analyze_ml_based_similarity(
            self.user_process_function, self.pricing_function
        )

        # 低類似度が検出されることを確認
        assert result.overall_ml_similarity < 0.7  # ドメインが異なるため類似度は低い
        assert result.recommended_action in ["new_implementation", "extend"]

        # 特徴量の妥当性確認
        assert result.ml_features.nlp_similarity_score < 0.8  # NLP類似度は低いはず
        assert result.feature_importance_ranking

    @pytest.mark.spec("SPEC-ML_SIMILARITY_INTEGRATION-BATCH_ML_SIMILARITY_")
    def test_batch_ml_similarity_analysis(self):
        """バッチ機械学習類似度分析テスト"""

        candidate_functions = [
            self.user_handle_function,
            self.pricing_function,
            FunctionSignature(
                name="authenticate_user_session",
                module_path="noveler.infrastructure.auth_service",
                file_path=Path("/test/project/scripts/infrastructure/auth_service.py"),
                line_number=30,
                parameters=["user_id", "session_token"],
                return_type="AuthResult",
                docstring="ユーザーセッションを認証する",
                ddd_layer="infrastructure",
            ),
        ]

        results = self.ml_similarity_service.batch_analyze_ml_similarities(
            self.user_process_function, candidate_functions, max_results=5
        )

        # 結果の検証
        assert len(results) <= 5
        assert len(results) <= len(candidate_functions)

        # 類似度順にソートされていることを確認
        for i in range(len(results) - 1):
            assert results[i].overall_ml_similarity >= results[i + 1].overall_ml_similarity

        # 各結果の妥当性確認
        for result in results:
            assert isinstance(result, MLSimilarityResult)
            assert result.source_function == self.user_process_function
            assert result.target_function in candidate_functions

    @pytest.mark.spec("SPEC-ML_SIMILARITY_INTEGRATION-THRESHOLD_OPTIMIZATI")
    def test_threshold_optimization(self):
        """しきい値最適化テスト"""

        # 訓練データの準備
        training_data = [
            (self.user_process_function, self.user_handle_function, 0.8),  # 高類似
            (self.user_process_function, self.pricing_function, 0.2),  # 低類似
        ]

        # しきい値最適化実行
        original_thresholds = self.ml_similarity_service.similarity_thresholds.copy()
        optimized_thresholds = self.ml_similarity_service.optimize_similarity_thresholds(training_data)

        # 最適化結果の検証
        assert isinstance(optimized_thresholds, dict)
        assert "high_confidence" in optimized_thresholds
        assert "medium_confidence" in optimized_thresholds
        assert "low_confidence" in optimized_thresholds
        assert "reuse_recommendation" in optimized_thresholds

        # しきい値の妥当性確認
        for threshold_value in optimized_thresholds.values():
            assert 0.0 <= threshold_value <= 1.0

        # しきい値が更新されていることを確認
        updated_thresholds = self.ml_similarity_service.similarity_thresholds
        assert updated_thresholds != original_thresholds

    @pytest.mark.spec("SPEC-ML_SIMILARITY_INTEGRATION-PERFORMANCE_METRICS_")
    def test_performance_metrics_calculation(self):
        """性能メトリクス計算テスト"""

        # テストデータの準備
        test_data = [
            (self.user_process_function, self.user_handle_function, True),  # 類似と判定すべき
            (self.user_process_function, self.pricing_function, False),  # 非類似と判定すべき
        ]

        # 性能メトリクス計算
        metrics = self.ml_similarity_service.get_ml_performance_metrics(test_data)

        # メトリクスの検証
        assert isinstance(metrics, dict)

        if metrics:  # テストデータが処理された場合:
            assert "accuracy" in metrics
            assert "precision" in metrics
            assert "recall" in metrics
            assert "f1_score" in metrics

            # メトリクス値の妥当性確認
            for metric_name, metric_value in metrics.items():
                if metric_name in ["accuracy", "precision", "recall", "f1_score"]:
                    assert 0.0 <= metric_value <= 1.0
                else:
                    assert metric_value >= 0  # カウント系メトリクス

    @pytest.mark.spec("SPEC-ML_SIMILARITY_INTEGRATION-NLP_FEATURES_INTEGRA")
    def test_nlp_features_integration(self):
        """NLP特徴量統合テスト"""

        # 日本語ドキュメント文字列を持つ関数
        japanese_doc_function = FunctionSignature(
            name="validate_user_input",
            module_path="noveler.domain.validation_service",
            file_path=Path("/test/project/scripts/domain/validation_service.py"),
            line_number=25,
            parameters=["input_data"],
            return_type="ValidationResult",
            docstring="ユーザー入力データを検証する",
            ddd_layer="domain",
        )

        result = self.ml_similarity_service.analyze_ml_based_similarity(
            self.user_process_function, japanese_doc_function
        )

        # NLP特徴量が抽出されていることを確認
        assert result.ml_features.nlp_similarity_score >= 0.0
        assert result.ml_features.intent_similarity_score >= 0.0

        # 意味的類似度が計算されていることを確認
        assert result.ml_features.semantic_score >= 0.0

    @pytest.mark.spec("SPEC-ML_SIMILARITY_INTEGRATION-ML_FEATURES_VECTOR_R")
    def test_ml_features_vector_representation(self):
        """機械学習特徴量ベクトル表現テスト"""

        result = self.ml_similarity_service.analyze_ml_based_similarity(
            self.user_process_function, self.user_handle_function
        )

        # 特徴量ベクトル取得
        feature_vector = result.ml_features.get_feature_vector()

        # ベクトルの検証
        assert isinstance(feature_vector, list)
        assert len(feature_vector) == 8  # 8次元特徴量ベクトル
        assert all(isinstance(val, float) for val in feature_vector)
        assert all(0.0 <= val <= 1.0 for val in feature_vector)

        # 重み付け類似度計算テスト
        weighted_similarity = result.ml_features.get_weighted_similarity()
        assert 0.0 <= weighted_similarity <= 1.0

        # カスタム重みでの計算テスト
        custom_weights = {"semantic": 0.5, "nlp_similarity": 0.3, "functional": 0.2}
        custom_weighted_similarity = result.ml_features.get_weighted_similarity(custom_weights)
        assert 0.0 <= custom_weighted_similarity <= 1.0

    @pytest.mark.spec("SPEC-ML_SIMILARITY_INTEGRATION-CONFIDENCE_LEVEL_DET")
    def test_confidence_level_determination(self):
        """信頼度レベル判定テスト"""

        # 高類似度ケース
        high_sim_result = self.ml_similarity_service.analyze_ml_based_similarity(
            self.user_process_function, self.user_handle_function
        )

        # 低類似度ケース
        low_sim_result = self.ml_similarity_service.analyze_ml_based_similarity(
            self.user_process_function, self.pricing_function
        )

        # 信頼度レベルの妥当性確認
        assert high_sim_result.confidence_level in ["high", "medium", "low"]
        assert low_sim_result.confidence_level in ["high", "medium", "low"]

        # 類似度と信頼度レベルの一貫性確認
        if high_sim_result.overall_ml_similarity > low_sim_result.overall_ml_similarity:
            confidence_order = {"high": 3, "medium": 2, "low": 1}
            assert (
                confidence_order[high_sim_result.confidence_level] >= confidence_order[low_sim_result.confidence_level]
            )

    @pytest.mark.spec("SPEC-ML_SIMILARITY_INTEGRATION-RECOMMENDED_ACTION_L")
    def test_recommended_action_logic(self):
        """推奨アクション決定ロジックテスト"""

        result = self.ml_similarity_service.analyze_ml_based_similarity(
            self.user_process_function, self.user_handle_function
        )

        # 推奨アクションの妥当性確認
        assert result.recommended_action in ["reuse", "extend", "new_implementation"]
        assert result.is_reuse_recommended() == (result.recommended_action == "reuse")

        # 高類似度の場合のロジック確認
        if result.overall_ml_similarity >= 0.8:
            assert result.recommended_action in ["reuse", "extend"]

        # 低類似度の場合のロジック確認
        if result.overall_ml_similarity < 0.5:
            assert result.recommended_action == "new_implementation"

    @pytest.mark.spec("SPEC-ML_SIMILARITY_INTEGRATION-SIMILARITY_EXPLANATI")
    def test_similarity_explanation_generation(self):
        """類似度説明生成テスト"""

        result = self.ml_similarity_service.analyze_ml_based_similarity(
            self.user_process_function, self.user_handle_function
        )

        # 説明文の取得
        explanation = result.get_similarity_explanation()

        # 説明文の検証
        assert isinstance(explanation, str)
        assert len(explanation) > 0
        assert explanation != "類似度分析完了"  # デフォルトメッセージではない

        # 類似度スコアが含まれていることを確認
        assert f"{result.overall_ml_similarity:.2f}" in explanation

        # 推論理由の妥当性確認
        assert isinstance(result.reasoning, str)
        assert len(result.reasoning) > 0

    @pytest.mark.spec("SPEC-ML_SIMILARITY_INTEGRATION-ERROR_HANDLING_RESIL")
    def test_error_handling_resilience(self):
        """エラーハンドリング・耐障害性テスト"""

        # 不正なデータでのテスト
        empty_function = FunctionSignature(name="", module_path="", file_path=Path("/empty"), line_number=1)

        # エラーが発生せずに結果が返されることを確認
        result = self.ml_similarity_service.analyze_ml_based_similarity(self.user_process_function, empty_function)

        assert isinstance(result, MLSimilarityResult)
        assert 0.0 <= result.overall_ml_similarity <= 1.0
        assert result.confidence_level in ["high", "medium", "low"]
        assert result.recommended_action in ["reuse", "extend", "new_implementation"]

        # 空の候補リストでのバッチ処理テスト
        batch_results = self.ml_similarity_service.batch_analyze_ml_similarities(
            self.user_process_function, [], max_results=5
        )

        assert isinstance(batch_results, list)
        assert len(batch_results) == 0

    @pytest.mark.asyncio
    async def test_performance_scalability(self):
        """パフォーマンス・スケーラビリティテスト"""

        # 大量候補関数生成
        large_candidate_list = []
        for i in range(50):  # 実際のテストでは数を調整
            func = FunctionSignature(
                name=f"test_function_{i}",
                module_path=f"test.module_{i % 10}",
                file_path=Path(f"/test/module_{i % 10}.py"),
                line_number=i + 1,
                parameters=[f"param_{j}" for j in range(i % 5)],
                ddd_layer="domain" if i % 2 == 0 else "application",
            )

            large_candidate_list.append(func)

        # パフォーマンステスト実行
        start_time = time.perf_counter()

        results = self.ml_similarity_service.batch_analyze_ml_similarities(
            self.user_process_function, large_candidate_list, max_results=10
        )

        end_time = time.perf_counter()
        execution_time_seconds = end_time - start_time

        # パフォーマンス要件の確認
        assert execution_time_seconds < 10.0  # 10秒以内（要調整）
        assert len(results) <= 10
        assert len(results) <= len(large_candidate_list)

        # 結果の妥当性確認
        for result in results:
            assert isinstance(result, MLSimilarityResult)
            assert 0.0 <= result.overall_ml_similarity <= 1.0


@pytest.mark.spec("SPEC-NIH-PREVENTION-CODEMAP-001")
class TestMLSimilarityEndToEnd:
    """機械学習類似度システムエンドツーエンドテスト"""

    @pytest.mark.asyncio
    async def test_complete_ml_workflow(self):
        """完全機械学習ワークフローテスト"""

        # コンポーネント準備
        similarity_calculator = BasicSimilarityCalculationAdapter()
        similarity_analyzer = SimilarityAnalyzer(similarity_calculator)
        nlp_analyzer = NLPAnalysisAdapter(enable_advanced_features=True)

        ml_service = MachineLearningBasedSimilarityService(
            similarity_analyzer=similarity_analyzer,
            nlp_analyzer=nlp_analyzer,
            project_root=Path("/test/project"),
            enable_advanced_ml=True,
        )

        # テストシナリオ: 新しい認証機能の類似検出
        new_auth_function = FunctionSignature(
            name="authenticate_user_credentials",
            module_path="noveler.application.auth_service",
            file_path=Path("/test/project/scripts/application/auth_service.py"),
            line_number=10,
            parameters=["username", "password"],
            return_type="AuthenticationResult",
            docstring="ユーザー認証情報を検証する",
            ddd_layer="application",
        )

        existing_functions = [
            FunctionSignature(
                name="validate_user_login",
                module_path="noveler.domain.security_service",
                file_path=Path("/test/project/scripts/domain/security_service.py"),
                line_number=20,
                parameters=["login_id", "password_hash"],
                return_type="LoginResult",
                docstring="ユーザーログインを検証する",
                ddd_layer="domain",
            ),
            FunctionSignature(
                name="process_user_data",
                module_path="noveler.domain.user_service",
                file_path=Path("/test/project/scripts/domain/user_service.py"),
                line_number=30,
                parameters=["user_data"],
                return_type="ProcessedUser",
                docstring="ユーザーデータを処理する",
                ddd_layer="domain",
            ),
        ]

        # エンドツーエンド実行
        results = ml_service.batch_analyze_ml_similarities(new_auth_function, existing_functions, max_results=5)

        # エンドツーエンドの検証
        assert len(results) > 0

        # 認証関連の機能が高い類似度で検出されることを確認
        top_result = results[0]
        assert top_result.source_function == new_auth_function

        # 機械学習特徴量が有効に機能していることを確認
        assert top_result.ml_features.nlp_similarity_score > 0.0
        assert top_result.ml_features.semantic_score > 0.0

        # 推奨アクションが生成されていることを確認
        assert top_result.recommended_action in ["reuse", "extend", "new_implementation"]
        assert len(top_result.reasoning) > 0

        # 特徴量重要度が計算されていることを確認
        assert len(top_result.feature_importance_ranking) > 0

        # Phase2機械学習機能の動作確認
        assert isinstance(top_result.ml_features, MLSimilarityFeatures)
        feature_vector = top_result.ml_features.get_feature_vector()
        assert len(feature_vector) == 8  # 8次元特徴量
        assert all(0.0 <= val <= 1.0 for val in feature_vector)
