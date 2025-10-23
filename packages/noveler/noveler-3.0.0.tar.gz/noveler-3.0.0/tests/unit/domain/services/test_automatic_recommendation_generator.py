#!/usr/bin/env python3
"""自動提案生成サービステスト

SPEC: SPEC-NIH-PREVENTION-CODEMAP-001 Phase2 P2
"""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from noveler.domain.entities.similarity_analyzer import SimilarityAnalyzer
from noveler.domain.services.automatic_recommendation_generator import (
    AutomaticRecommendationGenerator,
    AutomationRecommendation,
    RecommendationAction,
    RecommendationCategory,
    RecommendationPriority,
)
from noveler.domain.services.machine_learning_based_similarity_service import (
    MachineLearningBasedSimilarityService,
    MLSimilarityFeatures,
    MLSimilarityResult,
)
from noveler.domain.value_objects.function_signature import FunctionSignature
from noveler.infrastructure.adapters.nlp_analysis_adapter import NLPAnalysisAdapter
from noveler.infrastructure.adapters.similarity_calculation_adapter import BasicSimilarityCalculationAdapter
from noveler.domain.interfaces.logger_interface import NullLogger


@pytest.mark.spec("SPEC-NIH-PREVENTION-CODEMAP-001")
class TestAutomaticRecommendationGenerator:
    """自動提案生成サービステスト"""

    def setup_method(self):
        """テストセットアップ"""

        # テスト用関数シグネチャ
        self.target_function = FunctionSignature(
            name="process_user_registration",
            module_path="noveler.domain.user_service",
            file_path=Path("/test/project/scripts/domain/user_service.py"),
            line_number=10,
            parameters=["user_data", "validation_rules"],
            return_type="RegistrationResult",
            docstring="ユーザー登録処理を実行する",
            ddd_layer="domain",
        )

        self.similar_function_high = FunctionSignature(
            name="handle_user_registration",
            module_path="noveler.application.user_handler",
            file_path=Path("/test/project/scripts/application/user_handler.py"),
            line_number=15,
            parameters=["user_info", "rules"],
            return_type="UserResult",
            docstring="ユーザー登録処理を管理する",
            ddd_layer="application",
        )

        self.similar_function_medium = FunctionSignature(
            name="validate_user_data",
            module_path="noveler.domain.validation_service",
            file_path=Path("/test/project/scripts/domain/validation_service.py"),
            line_number=20,
            parameters=["data", "constraints"],
            return_type="ValidationResult",
            docstring="ユーザーデータを検証する",
            ddd_layer="domain",
        )

        # モックコンポーネント作成
        similarity_calculator = BasicSimilarityCalculationAdapter()
        similarity_analyzer = SimilarityAnalyzer(similarity_calculator)
        nlp_analyzer = NLPAnalysisAdapter()

        self.ml_similarity_service = MachineLearningBasedSimilarityService(
            similarity_analyzer=similarity_analyzer, nlp_analyzer=nlp_analyzer, project_root=Path("/test/project")
        )

        # 自動提案生成サービス初期化
        self.recommendation_generator = AutomaticRecommendationGenerator(
            ml_similarity_service=self.ml_similarity_service,
            project_root=Path("/test/project"),
            enable_advanced_analysis=True,
        )

    @pytest.mark.spec("SPEC-AUTOMATIC_RECOMMENDATION_GENERATOR-RECOMMENDATION_GENER")
    def test_recommendation_generator_initialization(self):
        """提案生成サービス初期化テスト"""

        assert self.recommendation_generator.ml_similarity_service == self.ml_similarity_service
        assert self.recommendation_generator.project_root == Path("/test/project")
        assert self.recommendation_generator.enable_advanced_analysis

        # しきい値設定確認
        thresholds = self.recommendation_generator.recommendation_thresholds
        assert "direct_reuse_similarity" in thresholds
        assert "extend_similarity" in thresholds
        assert "merge_similarity" in thresholds
        assert "min_confidence_score" in thresholds

        # パターンキーワード設定確認
        patterns = self.recommendation_generator.pattern_keywords
        assert "data_processing" in patterns
        assert "validation" in patterns
        assert "authentication" in patterns

    @pytest.mark.spec("SPEC-AUTOMATIC_RECOMMENDATION_GENERATOR-DIRECT_REUSE_RECOMME")
    def test_direct_reuse_recommendation_generation(self):
        """直接再利用提案生成テスト"""

        # 高類似度MLテスト結果作成
        high_sim_features = MLSimilarityFeatures(
            syntactic_score=0.9,
            semantic_score=0.95,
            functional_score=0.88,
            architectural_score=0.8,
            nlp_similarity_score=0.92,
            intent_similarity_score=0.9,
            structural_complexity_score=0.85,
            confidence_score=0.9,
        )

        ml_result = MLSimilarityResult(
            source_function=self.target_function,
            target_function=self.similar_function_high,
            ml_features=high_sim_features,
            overall_ml_similarity=0.9,
            confidence_level="high",
            recommended_action="reuse",
            reasoning="非常に高い類似度",
            feature_importance_ranking=[("semantic", 0.95), ("nlp_similarity", 0.92)],
        )

        # 直接再利用提案生成実行
        recommendations = self.recommendation_generator.generate_direct_reuse_recommendations(
            self.target_function, [ml_result]
        )

        # 結果検証
        assert len(recommendations) == 1

        rec = recommendations[0]
        assert rec.category == RecommendationCategory.DIRECT_REUSE
        assert rec.priority == RecommendationPriority.HIGH
        assert rec.confidence_score == 0.9
        assert rec.target_function == self.target_function
        assert len(rec.similar_functions) == 1
        assert rec.similar_functions[0][0] == self.similar_function_high
        assert rec.similar_functions[0][1] == 0.9

        # 推奨アクション確認
        assert len(rec.recommended_actions) == 1
        action = rec.recommended_actions[0]
        assert action.action_type == "reuse"
        assert self.similar_function_high in action.target_functions
        assert action.estimated_effort_hours == 0.5
        assert action.risk_level == "low"
        assert len(action.implementation_steps) > 0
        assert len(action.expected_benefits) > 0

    @pytest.mark.spec("SPEC-AUTOMATIC_RECOMMENDATION_GENERATOR-EXTENSION_RECOMMENDA")
    def test_extension_recommendation_generation(self):
        """拡張提案生成テスト"""

        # 中程度類似度MLテスト結果作成
        medium_sim_features = MLSimilarityFeatures(
            syntactic_score=0.6,
            semantic_score=0.7,
            functional_score=0.65,
            architectural_score=0.8,
            nlp_similarity_score=0.68,
            intent_similarity_score=0.6,
            structural_complexity_score=0.7,
            confidence_score=0.7,
        )

        ml_result = MLSimilarityResult(
            source_function=self.target_function,
            target_function=self.similar_function_medium,
            ml_features=medium_sim_features,
            overall_ml_similarity=0.68,
            confidence_level="medium",
            recommended_action="extend",
            reasoning="中程度の類似度",
            feature_importance_ranking=[("architectural", 0.8), ("semantic", 0.7)],
        )

        # 拡張提案生成実行
        recommendations = self.recommendation_generator.generate_extension_recommendations(
            self.target_function, [ml_result]
        )

        # 結果検証
        assert len(recommendations) == 1

        rec = recommendations[0]
        assert rec.category == RecommendationCategory.EXTEND_EXISTING
        assert rec.priority == RecommendationPriority.MEDIUM
        assert rec.confidence_score == 0.68 * 0.8  # 拡張の不確実性考慮
        assert rec.target_function == self.target_function
        assert len(rec.similar_functions) == 1

        # 推奨アクション確認
        assert len(rec.recommended_actions) == 1
        action = rec.recommended_actions[0]
        assert action.action_type == "extend"
        assert self.similar_function_medium in action.target_functions
        assert action.estimated_effort_hours == 2.0
        assert action.risk_level == "medium"
        assert "拡張" in action.description

    @pytest.mark.spec("SPEC-AUTOMATIC_RECOMMENDATION_GENERATOR-ARCHITECTURAL_IMPROV")
    def test_architectural_improvement_recommendation_generation(self):
        """アーキテクチャ改善提案生成テスト"""

        # 同一レイヤーの類似機能を複数作成
        same_layer_function_1 = FunctionSignature(
            name="validate_user_input",
            module_path="noveler.domain.input_validator",
            file_path=Path("/test/project/scripts/domain/input_validator.py"),
            line_number=25,
            parameters=["input_data"],
            return_type="ValidationResult",
            docstring="ユーザー入力を検証",
            ddd_layer="domain",
        )

        same_layer_function_2 = FunctionSignature(
            name="process_user_profile",
            module_path="noveler.domain.profile_service",
            file_path=Path("/test/project/scripts/domain/profile_service.py"),
            line_number=30,
            parameters=["profile_data"],
            return_type="ProfileResult",
            docstring="ユーザープロファイル処理",
            ddd_layer="domain",
        )

        # 高類似度MLテスト結果作成
        ml_results = []
        for func in [same_layer_function_1, same_layer_function_2]:
            features = MLSimilarityFeatures(
                syntactic_score=0.75,
                semantic_score=0.8,
                functional_score=0.77,
                architectural_score=0.9,  # 同一レイヤーで高スコア
                nlp_similarity_score=0.78,
                intent_similarity_score=0.75,
                structural_complexity_score=0.8,
                confidence_score=0.8,
            )

            ml_result = MLSimilarityResult(
                source_function=self.target_function,
                target_function=func,
                ml_features=features,
                overall_ml_similarity=0.78,
                confidence_level="high",
                recommended_action="extend",
                reasoning="同一レイヤー高類似度",
                feature_importance_ranking=[("architectural", 0.9), ("semantic", 0.8)],
            )

            ml_results.append(ml_result)

        # アーキテクチャ改善提案生成実行
        recommendations = self.recommendation_generator.generate_architectural_improvement_recommendations(
            self.target_function, ml_results
        )

        # 結果検証
        assert len(recommendations) == 1

        rec = recommendations[0]
        assert rec.category == RecommendationCategory.ARCHITECTURAL_IMPROVEMENT
        assert rec.priority == RecommendationPriority.HIGH
        assert rec.confidence_score == 0.75
        assert len(rec.similar_functions) == 2

        # 推奨アクション確認
        assert len(rec.recommended_actions) == 1
        action = rec.recommended_actions[0]
        assert action.action_type == "merge"
        assert len(action.target_functions) == 2
        assert action.estimated_effort_hours == 8.0
        assert action.risk_level == "high"
        assert "統合" in action.description
        assert rec.implementation_complexity == "complex"

    @pytest.mark.spec("SPEC-AUTOMATIC_RECOMMENDATION_GENERATOR-FUNCTION_PATTERN_ANA")
    def test_function_pattern_analysis(self):
        """機能パターン分析テスト"""

        # テスト用ML結果作成
        ml_results = []
        test_functions = [
            ("process_validation_data", "validation"),
            ("calculate_user_score", "calculation"),
            ("authenticate_user_access", "authentication"),
        ]

        for name, _expected_pattern in test_functions:
            func = FunctionSignature(
                name=name,
                module_path=f"noveler.domain.{name}_service",
                file_path=Path(f"/test/{name}.py"),
                line_number=10,
                parameters=["data"],
                return_type="Result",
                ddd_layer="domain",
            )

            features = MLSimilarityFeatures(
                syntactic_score=0.6,
                semantic_score=0.7,
                functional_score=0.6,
                architectural_score=0.7,
                nlp_similarity_score=0.65,
                intent_similarity_score=0.6,
                structural_complexity_score=0.6,
                confidence_score=0.6,
            )

            ml_result = MLSimilarityResult(
                source_function=self.target_function,
                target_function=func,
                ml_features=features,
                overall_ml_similarity=0.65,
                confidence_level="medium",
                recommended_action="extend",
                reasoning="中程度類似度",
                feature_importance_ranking=[],
            )

            ml_results.append(ml_result)

        # パターン分析実行
        patterns = self.recommendation_generator._analyze_function_patterns(self.target_function, ml_results)

        # パターン分析結果検証
        assert "detected_patterns" in patterns
        assert "common_keywords" in patterns
        assert "layer_distribution" in patterns
        assert "parameter_patterns" in patterns
        assert "return_type_patterns" in patterns

        # レイヤー分布確認
        assert patterns["layer_distribution"]["domain"] == 3

        # パラメータパターン確認
        assert len(patterns["parameter_patterns"]) == 3
        assert all(count == 1 for count in patterns["parameter_patterns"])

    @pytest.mark.spec("SPEC-AUTOMATIC_RECOMMENDATION_GENERATOR-RECOMMENDATION_STRAT")
    def test_recommendation_strategies_determination(self):
        """提案戦略決定テスト"""

        # 様々な類似度のMLテスト結果作成
        ml_results = []

        # 高類似度結果
        high_sim_result = self._create_ml_result(self.similar_function_high, 0.9, "reuse")

        ml_results.append(high_sim_result)

        # 中程度類似度結果
        medium_sim_result = self._create_ml_result(self.similar_function_medium, 0.68, "extend")

        ml_results.append(medium_sim_result)

        # 同一レイヤー統合候補
        same_layer_func = FunctionSignature(
            name="another_domain_function",
            module_path="noveler.domain.another_service",
            file_path=Path("/test/another.py"),
            line_number=20,
            ddd_layer="domain",
        )

        same_layer_result = self._create_ml_result(same_layer_func, 0.76, "extend")

        ml_results.append(same_layer_result)

        # パターン情報作成
        patterns = {
            "detected_patterns": ["data_processing"],
            "common_keywords": {"process", "data"},
            "layer_distribution": {"domain": 2, "application": 1},
            "parameter_patterns": [2, 2, 1],
            "return_type_patterns": ["Result", "Result", "ValidationResult"],
        }

        # 戦略決定実行
        strategies = self.recommendation_generator._determine_recommendation_strategies(
            self.target_function, ml_results, patterns
        )

        # 戦略結果確認
        assert "direct_reuse" in strategies
        assert "extend_existing" in strategies
        assert "architectural_improvement" in strategies
        assert "extract_common" in strategies

    @pytest.mark.spec("SPEC-AUTOMATIC_RECOMMENDATION_GENERATOR-EXTRACT_COMMON")
    def test_extract_common_strategy_generation(self):
        """extract_common 戦略の生成テスト"""

        ml_results = [
            self._create_ml_result(self.similar_function_high, 0.68, "extend"),
            self._create_ml_result(self.similar_function_medium, 0.66, "extend"),
        ]

        recommendation = self.recommendation_generator._generate_specific_recommendation(
            self.target_function, ml_results, "extract_common"
        )

        assert recommendation is not None
        assert recommendation.category == RecommendationCategory.EXTRACT_COMMON
        assert recommendation.recommended_actions[0].action_type == "extract_common"
        assert len(recommendation.similar_functions) >= 1

    @pytest.mark.spec("SPEC-AUTOMATIC_RECOMMENDATION_GENERATOR-FALLBACK_STRATEGY")
    def test_fallback_recommendation_generation(self):
        """フォールバック提案が最低1件生成されることを確認"""

        with patch.object(
            self.recommendation_generator.ml_similarity_service,
            "batch_analyze_ml_similarities",
            return_value=[],
        ) as _:
            with patch.object(
                self.recommendation_generator.ml_similarity_service,
                "analyze_ml_based_similarity",
                return_value=self._create_ml_result(self.similar_function_high, 0.58, "extend"),
            ):
                recommendations = self.recommendation_generator.generate_comprehensive_recommendations(
                    self.target_function,
                    [self.similar_function_high],
                    max_recommendations=1,
                )

        assert len(recommendations) == 1
        assert recommendations[0].category == RecommendationCategory.EXTEND_EXISTING

    @pytest.mark.spec("SPEC-AUTOMATIC_RECOMMENDATION_GENERATOR-NULL_LOGGER")
    def test_null_logger_fallback_when_logger_not_supplied(self):
        """ロガー未指定時にNullLoggerが利用されることを確認"""

        generator = AutomaticRecommendationGenerator(
            ml_similarity_service=self.ml_similarity_service,
            project_root=Path("/test/project"),
            enable_advanced_analysis=False,
        )

        assert isinstance(generator._logger, NullLogger)

        # ロガーがNullLoggerでも例外が発生しないことを簡易確認
        with patch.object(generator.ml_similarity_service, "batch_analyze_ml_similarities", return_value=[]):
            recommendations = generator.generate_comprehensive_recommendations(
                self.target_function,
                [self.similar_function_high],
                max_recommendations=1,
            )
        assert isinstance(recommendations, list)

    @pytest.mark.spec("SPEC-AUTOMATIC_RECOMMENDATION_GENERATOR-COMPREHENSIVE_RECOMM")
    def test_comprehensive_recommendations_generation(self):
        """包括的提案生成テスト"""

        candidate_functions = [self.similar_function_high, self.similar_function_medium]

        # 包括的提案生成実行
        with patch.object(
            self.recommendation_generator.ml_similarity_service, "batch_analyze_ml_similarities"
        ) as mock_batch_analyze:
            # モック結果設定
            mock_batch_analyze.return_value = [
                self._create_ml_result(self.similar_function_high, 0.9, "reuse"),
                self._create_ml_result(self.similar_function_medium, 0.68, "extend"),
            ]

            recommendations = self.recommendation_generator.generate_comprehensive_recommendations(
                self.target_function, candidate_functions, max_recommendations=3
            )

        # 結果検証
        assert len(recommendations) <= 3
        assert len(recommendations) > 0

        # 各提案の基本構造確認
        for rec in recommendations:
            assert isinstance(rec, AutomationRecommendation)
            assert rec.target_function == self.target_function
            assert rec.confidence_score >= 0.5  # 最小信頼度しきい値
            assert len(rec.recommended_actions) > 0
            assert rec.generated_timestamp is not None

            # 推奨アクション詳細確認
            for action in rec.recommended_actions:
                assert isinstance(action, RecommendationAction)
                assert len(action.implementation_steps) > 0
                assert len(action.expected_benefits) > 0
                assert action.estimated_effort_hours > 0
                assert action.risk_level in ["low", "medium", "high"]

    @pytest.mark.spec("SPEC-AUTOMATIC_RECOMMENDATION_GENERATOR-RECOMMENDATIONS_OPTI")
    def test_recommendations_optimization(self):
        """提案最適化テスト"""

        # 異なる優先度・信頼度の提案作成
        recommendations = []

        # 高優先度・高信頼度
        high_rec = AutomationRecommendation(
            recommendation_id="high_rec",
            category=RecommendationCategory.DIRECT_REUSE,
            priority=RecommendationPriority.HIGH,
            title="高優先度提案",
            description="高信頼度の提案",
            confidence_score=0.9,
            target_function=self.target_function,
            similar_functions=[],
            ml_analysis_results=[],
            recommended_actions=[
                RecommendationAction(
                    action_type="reuse",
                    target_functions=[],
                    description="テスト",
                    implementation_steps=["step1"],
                    expected_benefits=["benefit1"],
                    estimated_effort_hours=1.0,
                    risk_level="low",
                )
            ],
            alternative_approaches=[],
            generated_timestamp=datetime.now(timezone.utc),
            reasoning="テスト用",
            implementation_complexity="simple",
        )

        recommendations.append(high_rec)

        # 低優先度・低信頼度
        low_rec = AutomationRecommendation(
            recommendation_id="low_rec",
            category=RecommendationCategory.EXTEND_EXISTING,
            priority=RecommendationPriority.LOW,
            title="低優先度提案",
            description="低信頼度の提案",
            confidence_score=0.4,  # しきい値以下
            target_function=self.target_function,
            similar_functions=[],
            ml_analysis_results=[],
            recommended_actions=[
                RecommendationAction(
                    action_type="extend",
                    target_functions=[],
                    description="テスト",
                    implementation_steps=["step1"],
                    expected_benefits=["benefit1"],
                    estimated_effort_hours=5.0,
                    risk_level="high",
                )
            ],
            alternative_approaches=[],
            generated_timestamp=datetime.now(timezone.utc),
            reasoning="テスト用",
            implementation_complexity="complex",
        )

        recommendations.append(low_rec)

        # 最適化実行
        optimized = self.recommendation_generator._optimize_recommendations(recommendations)

        # 最適化結果確認
        assert len(optimized) == 1  # 信頼度しきい値により1つフィルタリング
        assert optimized[0] == high_rec  # 高優先度・高信頼度が残る

    @pytest.mark.spec("SPEC-AUTOMATIC_RECOMMENDATION_GENERATOR-IMPLEMENTATION_GUIDE")
    def test_implementation_guide_generation(self):
        """実装ガイド生成テスト"""

        # テスト用提案作成
        recommendation = AutomationRecommendation(
            recommendation_id="test_rec",
            category=RecommendationCategory.DIRECT_REUSE,
            priority=RecommendationPriority.HIGH,
            title="テスト提案",
            description="テスト用の提案",
            confidence_score=0.8,
            target_function=self.target_function,
            similar_functions=[],
            ml_analysis_results=[],
            recommended_actions=[
                RecommendationAction(
                    action_type="reuse",
                    target_functions=[],
                    description="直接再利用",
                    implementation_steps=["step1", "step2", "step3"],
                    expected_benefits=["benefit1", "benefit2"],
                    estimated_effort_hours=2.0,
                    risk_level="medium",
                )
            ],
            alternative_approaches=["alternative1"],
            generated_timestamp=datetime.now(timezone.utc),
            reasoning="テスト用推論",
            implementation_complexity="medium",
        )

        # 実装ガイド生成実行
        guide = self.recommendation_generator.generate_implementation_guide(recommendation)

        # ガイド構造確認
        assert "recommendation_summary" in guide
        assert "implementation_plan" in guide
        assert "risk_assessment" in guide
        assert "success_metrics" in guide
        assert "testing_strategy" in guide

        # サマリー情報確認
        summary = guide["recommendation_summary"]
        assert summary["title"] == "テスト提案"
        assert summary["category"] == "direct_reuse"
        assert summary["confidence"] == "0.80"
        assert summary["estimated_effort"] == "2.0時間"

        # 実装プラン確認
        assert len(guide["implementation_plan"]) == 1
        plan = guide["implementation_plan"][0]
        assert plan["action_type"] == "reuse"
        assert len(plan["steps"]) == 3
        assert plan["estimated_hours"] == 2.0
        assert plan["risk_level"] == "medium"

        # その他セクション確認
        assert len(guide["success_metrics"]) > 0
        assert len(guide["testing_strategy"]) > 0

    @pytest.mark.spec("SPEC-AUTOMATIC_RECOMMENDATION_GENERATOR-HELPER_METHODS")
    def test_helper_methods(self):
        """ヘルパーメソッドテスト"""

        # テスト用提案作成
        recommendation = AutomationRecommendation(
            recommendation_id="helper_test",
            category=RecommendationCategory.EXTEND_EXISTING,
            priority=RecommendationPriority.MEDIUM,
            title="ヘルパーテスト",
            description="ヘルパーメソッドのテスト",
            confidence_score=0.85,
            target_function=self.target_function,
            similar_functions=[],
            ml_analysis_results=[],
            recommended_actions=[
                RecommendationAction(
                    action_type="extend",
                    target_functions=[],
                    description="拡張1",
                    implementation_steps=["step1"],
                    expected_benefits=["benefit1"],
                    estimated_effort_hours=1.5,
                    risk_level="low",
                ),
                RecommendationAction(
                    action_type="merge",
                    target_functions=[],
                    description="統合2",
                    implementation_steps=["step1"],
                    expected_benefits=["benefit1"],
                    estimated_effort_hours=3.0,
                    risk_level="high",
                ),
            ],
            alternative_approaches=[],
            generated_timestamp=datetime.now(timezone.utc),
            reasoning="ヘルパーテスト用",
            implementation_complexity="medium",
        )

        # ヘルパーメソッドテスト
        assert recommendation.is_high_confidence(threshold=0.8)
        assert not recommendation.is_high_confidence(threshold=0.9)

        assert recommendation.get_effort_estimate() == 4.5  # 1.5 + 3.0

        primary_action = recommendation.get_primary_action()
        assert primary_action is not None
        assert primary_action.estimated_effort_hours == 1.5  # より少ない工数のアクション

    def _create_ml_result(
        self, target_function: FunctionSignature, similarity: float, action: str
    ) -> MLSimilarityResult:
        """テスト用ML結果作成ヘルパー"""

        features = MLSimilarityFeatures(
            syntactic_score=similarity * 0.8,
            semantic_score=similarity * 0.9,
            functional_score=similarity * 0.7,
            architectural_score=similarity * 0.8,
            nlp_similarity_score=similarity * 0.85,
            intent_similarity_score=similarity * 0.75,
            structural_complexity_score=similarity * 0.8,
            confidence_score=similarity,
        )

        confidence_level = "high" if similarity >= 0.8 else "medium" if similarity >= 0.6 else "low"

        return MLSimilarityResult(
            source_function=self.target_function,
            target_function=target_function,
            ml_features=features,
            overall_ml_similarity=similarity,
            confidence_level=confidence_level,
            recommended_action=action,
            reasoning=f"テスト用結果 (類似度: {similarity})",
            feature_importance_ranking=[("semantic", similarity * 0.9), ("nlp_similarity", similarity * 0.85)],
        )
