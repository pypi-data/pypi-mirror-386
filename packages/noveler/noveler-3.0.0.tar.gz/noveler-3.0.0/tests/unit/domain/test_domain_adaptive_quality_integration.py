#!/usr/bin/env python3
"""適応的品質評価統合のドメインテスト(TDD RED段階)

DDDアーキテクチャ:
    - Domain Layer: AdaptiveQualityEvaluator, QualityAdaptationPolicy
- Application Layer: AdaptiveQualityEvaluationUseCase
- Infrastructure Layer: LearningModelRepository


仕様書: SPEC-INTEGRATION
"""

import contextlib
import sys
from pathlib import Path

import pytest

from noveler.application.use_cases.adaptive_quality_evaluation import AdaptiveQualityEvaluationUseCase
from noveler.domain.learning.entities import LearningQualityEvaluator
from noveler.domain.quality.entities import AdaptiveQualityEvaluator, QualityAdaptationPolicy
from noveler.domain.quality.services import QualityAdaptationService
from noveler.domain.quality.value_objects import AdaptationStrength, EvaluationContext, QualityScore
from noveler.infrastructure.persistence.learning_model_repository import LearningModelRepository

# パス設定
sys.path.append(str(Path(__file__).resolve().parent.parent))

# ドメインエンティティのインポート(実装前なので失敗する)
with contextlib.suppress(ImportError):
    pass


class TestAdaptiveQualityEvaluator:
    """AdaptiveQualityEvaluatorエンティティテスト(TDD RED段階)"""

    @pytest.mark.spec("SPEC-DOMAIN_ADAPTIVE_QUALITY_INTEGRATION-EVALUATOR_CREATION_W")
    def test_evaluator_creation_with_learning_model(self) -> None:
        """学習モデル付き評価器の作成"""
        # RED: まだ実装されていないため失敗する

        evaluator = AdaptiveQualityEvaluator(
            evaluator_id="adaptive_001",
            project_id="zerodaybodyparty",
            learning_model_path="/path/to/model.pkl",
            is_trained=True,
        )

        assert evaluator.evaluator_id == "adaptive_001"
        assert evaluator.project_id == "zerodaybodyparty"
        assert evaluator.has_learning_model() is True
        assert evaluator.is_ready_for_adaptive_evaluation() is True

    @pytest.mark.spec("SPEC-DOMAIN_ADAPTIVE_QUALITY_INTEGRATION-STANDARD_TO_ADAPTIVE")
    def test_standard_to_adaptive_evaluation_transition(self) -> None:
        """標準評価から適応的評価への移行"""

        evaluator = AdaptiveQualityEvaluator(
            evaluator_id="adaptive_002",
            project_id="zerodaybodyparty",
            learning_model_path="/path/to/model.pkl",
            is_trained=True,
        )

        # 標準評価結果
        standard_scores = {
            "dialogue_ratio": QualityScore(65.0),
            "narrative_depth": QualityScore(72.0),
            "readability": QualityScore(78.0),
        }

        # 評価コンテキスト
        context = EvaluationContext(
            episode_number=15,
            chapter_number=3,
            genre="body_swap_fantasy",
            viewpoint_type="single_introspective",
        )

        # 適応的評価の実行
        adaptive_scores = evaluator.evaluate_adaptively(standard_scores, context)

        # ビジネスルール:適応的評価は標準評価と異なる結果を返すべき
        assert adaptive_scores != standard_scores
        assert adaptive_scores["dialogue_ratio"].value != standard_scores["dialogue_ratio"].value
        assert adaptive_scores.get("adaptation_confidence") is not None
        assert adaptive_scores.get("learning_source") == "project_specific_model"

    @pytest.mark.spec("SPEC-DOMAIN_ADAPTIVE_QUALITY_INTEGRATION-ADAPTATION_POLICY_AP")
    def test_adaptation_policy_application(self) -> None:
        """適応ポリシーの適用"""

        evaluator = AdaptiveQualityEvaluator(
            evaluator_id="adaptive_003",
            project_id="zerodaybodyparty",
            learning_model_path="/path/to/model.pkl",
            is_trained=True,
        )

        # 適応ポリシーの定義
        policy = QualityAdaptationPolicy(
            policy_id="body_swap_policy",
            adaptations={
                "dialogue_ratio": AdaptationStrength.MODERATE,  # 会話比率は中程度調整
                "character_consistency": AdaptationStrength.STRONG,  # キャラ一貫性は強く調整
                "viewpoint_clarity": AdaptationStrength.STRONG,  # 視点明確性は強く調整
            },
            confidence_threshold=0.7,
        )

        evaluator.apply_adaptation_policy(policy)

        assert evaluator.current_policy == policy
        assert evaluator.has_adaptation_policy() is True
        assert evaluator.get_adaptation_strength("dialogue_ratio") == AdaptationStrength.MODERATE


class TestQualityAdaptationService:
    """QualityAdaptationServiceドメインサービステスト"""

    @pytest.mark.spec("SPEC-DOMAIN_ADAPTIVE_QUALITY_INTEGRATION-PROJECT_SPECIFIC_ADA")
    def test_project_specific_adaptation_generation(self) -> None:
        """プロジェクト固有適応の生成"""

        service = QualityAdaptationService()

        # 学習済み評価器(モック)
        learned_evaluator = LearningQualityEvaluator(
            evaluator_id="learned_001",
            project_id="zerodaybodyparty",
        )

        learned_evaluator._set_trained_state()  # テスト用の学習済み状態設定

        # プロジェクト固有適応の生成
        adaptation_policy = service.generate_project_adaptation(
            learned_evaluator=learned_evaluator,
            episode_count=34,
            genre="body_swap_fantasy",
        )

        assert adaptation_policy is not None
        assert adaptation_policy.policy_id.startswith("zerodaybodyparty_")
        assert len(adaptation_policy.adaptations) > 0
        assert adaptation_policy.confidence_threshold > 0.5

    @pytest.mark.spec("SPEC-DOMAIN_ADAPTIVE_QUALITY_INTEGRATION-ADAPTATION_STRENGTH_")
    def test_adaptation_strength_calculation(self) -> None:
        """適応強度の計算"""

        service = QualityAdaptationService()

        # 学習データからの適応強度計算
        learning_data = {
            "dialogue_ratio_variance": 0.25,  # 高い分散 = 強い適応
            "reader_satisfaction_correlation": 0.8,  # 高い相関 = 強い適応
            "episode_count": 34,  # 十分なデータ
        }

        strength = service.calculate_adaptation_strength(
            metric="dialogue_ratio",
            learning_data=learning_data,
        )

        assert strength in [AdaptationStrength.WEAK, AdaptationStrength.MODERATE, AdaptationStrength.STRONG]
        # 高い分散と相関なので強い適応が期待される
        assert strength == AdaptationStrength.STRONG


class TestAdaptiveQualityEvaluationUseCase:
    """AdaptiveQualityEvaluationUseCaseアプリケーション層テスト"""

    @pytest.mark.spec("SPEC-DOMAIN_ADAPTIVE_QUALITY_INTEGRATION-INTEGRATED_ADAPTIVE_")
    def test_integrated_adaptive_evaluation_workflow(self) -> None:
        """統合適応的評価ワークフロー"""

        # リポジトリ(モック)
        class MockLearningModelRepository:
            def has_trained_model(self, project_id: object):
                return project_id == "zerodaybodyparty"

        model_repository = MockLearningModelRepository()

        # ユースケース
        use_case = AdaptiveQualityEvaluationUseCase(
            model_repository=model_repository,
        )

        # 標準品質チェック結果
        standard_results = {
            "episode_number": 15,
            "checks": {
                "basic_style": {"score": 85, "errors": []},
                "composition": {"score": 72, "warnings": ["dialogue_ratio_low"]},
                "readability": {"score": 78},
            },
        }

        # 適応的評価の実行
        adaptive_results = use_case.evaluate_adaptively(
            project_id="zerodaybodyparty",
            standard_results=standard_results,
            episode_file_path="/path/to/episode15.md",
        )

        # ビジネスルール検証
        assert adaptive_results["adaptive_enabled"] is True
        assert "adaptation_summary" in adaptive_results
        assert "adjusted_scores" in adaptive_results
        assert adaptive_results["confidence_level"] > 0.5

    @pytest.mark.spec("SPEC-DOMAIN_ADAPTIVE_QUALITY_INTEGRATION-FALLBACK_TO_STANDARD")
    def test_fallback_to_standard_when_model_unavailable(self) -> None:
        """学習モデル利用不可時の標準評価フォールバック"""

        use_case = AdaptiveQualityEvaluationUseCase(
            model_repository=None,  # モデルリポジトリなし
        )

        standard_results = {
            "episode_number": 1,
            "checks": {"basic_style": {"score": 80}},
        }

        # 適応的評価を試行するが、モデルがないため標準評価にフォールバック
        adaptive_results = use_case.evaluate_adaptively(
            project_id="new_project",
            standard_results=standard_results,
            episode_file_path="/path/to/episode1.md",
        )

        assert adaptive_results["adaptive_enabled"] is False
        assert adaptive_results["fallback_reason"] == "no_learning_model"
        assert adaptive_results["adjusted_scores"] == standard_results["checks"]


class TestLearningModelRepository:
    """LearningModelRepositoryインフラ層テスト"""

    @pytest.mark.spec("SPEC-DOMAIN_ADAPTIVE_QUALITY_INTEGRATION-MODEL_LOADING_AND_PR")
    def test_model_loading_and_prediction(self) -> None:
        """モデルの読み込みと予測"""

        repository = LearningModelRepository()

        # 学習済みモデルの存在確認
        model_exists = repository.has_trained_model("zerodaybodyparty")

        if model_exists:
            # モデルの読み込み
            model = repository.load_model("zerodaybodyparty")
            assert model is not None

            # 特徴量の準備
            features = {
                "total_characters": 3500,
                "dialogue_ratio": 0.35,
                "exclamation_count": 12,
                "question_count": 8,
            }

            # 予測の実行
            prediction = repository.predict_quality(model, features)

            assert prediction is not None
            assert isinstance(prediction, int | float)
            assert 0 <= prediction <= 5  # エンゲージメントスコア範囲

    @pytest.mark.spec("SPEC-DOMAIN_ADAPTIVE_QUALITY_INTEGRATION-MODEL_METADATA_RETRI")
    def test_model_metadata_retrieval(self) -> None:
        """モデルメタデータの取得"""

        repository = LearningModelRepository()

        metadata = repository.get_model_metadata("zerodaybodyparty")

        if metadata:
            assert "version" in metadata
            assert "training_date" in metadata
            assert "feature_importance" in metadata
            assert "model_performance" in metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
