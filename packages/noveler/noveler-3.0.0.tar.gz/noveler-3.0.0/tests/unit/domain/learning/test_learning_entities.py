#!/usr/bin/env python3
"""学習機能付き品質チェックドメイン - エンティティのユニットテスト

TDD原則に従い、ビジネスロジックのテストを実装


仕様書: SPEC-UNIT-TEST
"""

from datetime import timedelta

import pytest

from noveler.domain.learning.entities import (
    LearningQualityEvaluator,
    ModelStatus,
    QualityLearningModel,
)
from noveler.domain.learning.value_objects import (
    LearningDataQuality,
    QualityEvaluationResult,
    QualityMetric,
)
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class TestQualityLearningModel:
    """QualityLearningModelのテストクラス"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行"""
        self.model = QualityLearningModel(
            model_id="test_model_1",
            project_id="test_project",
            target_metrics=[QualityMetric.READABILITY, QualityMetric.SENTENCE_VARIETY],
        )

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-INITIAL_STATE")
    def test_initial_state(self) -> None:
        """初期状態の確認"""
        assert self.model.model_id == "test_model_1"
        assert self.model.project_id == "test_project"
        assert self.model.status == ModelStatus.UNTRAINED
        assert self.model.accuracy is None
        assert self.model.training_data_count == 0
        assert self.model.last_training is None
        assert self.model.new_episodes_since_training == []

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-START_TRAINING_WITH_")
    def test_start_training_with_valid_data(self) -> None:
        """有効なデータで学習開始"""
        # Given
        training_data = [
            {
                "episode_id": f"ep_{i}",
                "readability": 80.0 + i,
                "sentence_variety": 75.0 + i,
            }
            for i in range(5)
        ]

        # When
        self.model.start_training(training_data)

        # Then
        assert self.model.status == ModelStatus.TRAINING
        assert self.model.training_data_count == 5

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-START_TRAINING_WITH_")
    def test_start_training_with_insufficient_data(self) -> None:
        """データ不足での学習開始エラー"""
        # Given
        training_data = [{"episode_id": "ep_1", "readability": 80.0, "sentence_variety": 75.0}]

        # When & Then
        with pytest.raises(ValueError) as exc_info:
            self.model.start_training(training_data)
        assert "学習データが不足しています" in str(exc_info.value)

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-START_TRAINING_FROM_")
    def test_start_training_from_invalid_status(self) -> None:
        """無効なステータスからの学習開始エラー"""
        # Given
        self.model.status = ModelStatus.TRAINING

        # When & Then
        with pytest.raises(ValueError) as exc_info:
            self.model.start_training([])
        assert "学習可能な状態ではありません" in str(exc_info.value)

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-VALIDATE_TRAINING_DA")
    def test_validate_training_data_missing_fields(self) -> None:
        """必須フィールド不足の検証"""
        # Given
        invalid_data = [
            {"readability": 80.0, "sentence_variety": 75.0}  # episode_id missing
            for _ in range(5)
        ]

        # When & Then
        with pytest.raises(ValueError) as exc_info:
            self.model.start_training(invalid_data)
        assert "必須フィールドが不足" in str(exc_info.value)

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-VALIDATE_TRAINING_DA")
    def test_validate_training_data_missing_metrics(self) -> None:
        """メトリックフィールド不足の検証"""
        # Given
        invalid_data = [
            {"episode_id": f"ep_{i}", "readability": 80.0}  # sentence_variety missing
            for i in range(5)
        ]

        # When & Then
        with pytest.raises(ValueError) as exc_info:
            self.model.start_training(invalid_data)
        assert "対象メトリックデータが不足" in str(exc_info.value)

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-VALIDATE_TRAINING_DA")
    def test_validate_training_data_out_of_range(self) -> None:
        """範囲外の値の検証"""
        # Given
        invalid_data = [
            {
                "episode_id": f"ep_{i}",
                "readability": 150.0,  # Out of range
                "sentence_variety": 75.0,
            }
            for i in range(5)
        ]

        # When & Then
        with pytest.raises(ValueError) as exc_info:
            self.model.start_training(invalid_data)
        assert "メトリック値が範囲外" in str(exc_info.value)

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-COMPLETE_TRAINING_SU")
    def test_complete_training_success(self) -> None:
        """学習完了の成功"""
        # Given
        self.model.status = ModelStatus.TRAINING
        accuracy = 0.85

        # When
        self.model.complete_training(accuracy)

        # Then
        assert self.model.status == ModelStatus.TRAINED
        assert self.model.accuracy == 0.85
        assert self.model.last_training is not None

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-COMPLETE_TRAINING_IN")
    def test_complete_training_invalid_status(self) -> None:
        """無効なステータスでの学習完了エラー"""
        # When & Then
        with pytest.raises(ValueError) as exc_info:
            self.model.complete_training(0.85)
        assert "学習中状態ではありません" in str(exc_info.value)

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-FAIL_TRAINING")
    def test_fail_training(self) -> None:
        """学習失敗の処理"""
        # Given
        self.model.status = ModelStatus.TRAINING

        # When
        self.model.fail_training("データ形式エラー")

        # Then
        assert self.model.status == ModelStatus.FAILED
        assert self.model.accuracy is None

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-IS_READY_FOR_PREDICT")
    def test_is_ready_for_prediction_trained(self) -> None:
        """予測準備完了チェック(学習済み)"""
        # Given
        self.model._set_trained_state(accuracy=0.85)

        # When & Then
        assert self.model.is_ready_for_prediction() is True

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-IS_READY_FOR_PREDICT")
    def test_is_ready_for_prediction_low_accuracy(self) -> None:
        """予測準備完了チェック(精度不足)"""
        # Given
        self.model._set_trained_state(accuracy=0.5)

        # When & Then
        assert self.model.is_ready_for_prediction() is False

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-IS_READY_FOR_PREDICT")
    def test_is_ready_for_prediction_untrained(self) -> None:
        """予測準備完了チェック(未学習)"""
        # When & Then
        assert self.model.is_ready_for_prediction() is False

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-PREDICT_QUALITY_SUCC")
    def test_predict_quality_success(self) -> None:
        """品質予測の成功"""
        # Given
        self.model._set_trained_state(accuracy=0.85)
        episode_features = {"avg_sentence_length": 40, "sentence_variety_score": 0.8}

        # When
        predictions = self.model.predict_quality(episode_features)

        # Then
        assert "readability" in predictions
        assert "sentence_variety" in predictions
        assert "confidence" in predictions
        assert predictions["confidence"] == 0.85
        assert 0 <= predictions["readability"] <= 100
        assert 0 <= predictions["sentence_variety"] <= 100

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-PREDICT_QUALITY_NOT_")
    def test_predict_quality_not_ready(self) -> None:
        """準備未完了での予測エラー"""
        # When & Then
        with pytest.raises(ValueError) as exc_info:
            self.model.predict_quality({})
        assert "モデルが予測可能状態ではありません" in str(exc_info.value)

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-ADD_NEW_EPISODES")
    def test_add_new_episodes(self) -> None:
        """新エピソードデータ追加"""
        # Given
        new_episodes = [{"episode_id": "ep_new_1"}, {"episode_id": "ep_new_2"}]

        # When
        self.model.add_new_episodes(new_episodes)

        # Then
        assert len(self.model.new_episodes_since_training) == 2

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-SHOULD_RETRAIN_BY_DA")
    def test_should_retrain_by_data_count(self) -> None:
        """データ蓄積による再学習判定"""
        # Given
        self.model._set_trained_state()
        new_episodes = [{"episode_id": f"ep_{i}"} for i in range(10)]
        self.model.add_new_episodes(new_episodes)

        # When & Then
        assert self.model.should_retrain() is True

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-SHOULD_RETRAIN_BY_TI")
    def test_should_retrain_by_time(self) -> None:
        """時間経過による再学習判定"""
        # Given
        old_training_time = project_now().datetime - timedelta(days=31)
        self.model._set_trained_state(last_training=old_training_time)

        # When & Then
        assert self.model.should_retrain() is True

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-SHOULD_RETRAIN_NOT_N")
    def test_should_retrain_not_needed(self) -> None:
        """再学習不要の判定"""
        # Given
        self.model._set_trained_state()

        # When & Then
        assert self.model.should_retrain() is False

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-GET_RETRAIN_REASON_D")
    def test_get_retrain_reason_data_accumulation(self) -> None:
        """再学習理由取得(データ蓄積)"""
        # Given
        self.model._set_trained_state()
        new_episodes = [{"episode_id": f"ep_{i}"} for i in range(10)]
        self.model.add_new_episodes(new_episodes)

        # When
        reason = self.model.get_retrain_reason()

        # Then
        assert "新しいエピソードデータが蓄積されました" in reason

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-GET_RETRAIN_REASON_T")
    def test_get_retrain_reason_time_elapsed(self) -> None:
        """再学習理由取得(時間経過)"""
        # Given
        old_training_time = project_now().datetime - timedelta(days=31)
        self.model._set_trained_state(last_training=old_training_time)

        # When
        reason = self.model.get_retrain_reason()

        # Then
        assert "前回学習から時間が経過しています" in reason

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-GET_RETRAIN_REASON_N")
    def test_get_retrain_reason_not_needed(self) -> None:
        """再学習理由取得(不要)"""
        # Given
        self.model._set_trained_state()

        # When
        reason = self.model.get_retrain_reason()

        # Then
        assert "再学習は不要です" in reason


class TestLearningQualityEvaluator:
    """LearningQualityEvaluatorのテストクラス"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行"""
        self.evaluator = LearningQualityEvaluator(evaluator_id="test_evaluator", project_id="test_project")

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-INITIAL_STATE")
    def test_initial_state(self) -> None:
        """初期状態の確認"""
        assert self.evaluator.evaluator_id == "test_evaluator"
        assert self.evaluator.project_id == "test_project"
        assert self.evaluator.learning_models == {}
        assert self.evaluator.author_style_profile is None
        assert self.evaluator.learned_patterns == {}
        assert self.evaluator.quality_criteria_adjustments == {}

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-LEARN_FROM_HISTORICA")
    def test_learn_from_historical_data_success(self) -> None:
        """過去データからの学習成功"""
        # Given
        historical_data = [
            {
                "episode_id": f"ep_{i}",
                "quality_scores": {
                    "readability": 80.0 + i,
                    "dialogue_ratio": 0.3 + i * 0.05,
                    "avg_sentence_length": 35.0 + i,
                },
            }
            for i in range(5)
        ]

        # When
        self.evaluator.learn_from_historical_data(historical_data)

        # Then
        assert self.evaluator.is_trained() is True
        assert len(self.evaluator.learning_models) > 0
        assert self.evaluator.author_style_profile is not None
        assert self.evaluator.author_style_profile.confidence_score > 0

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-LEARN_FROM_HISTORICA")
    def test_learn_from_historical_data_insufficient(self) -> None:
        """データ不足での学習エラー"""
        # Given
        historical_data = [{"episode_id": "ep_1", "quality_scores": {"readability": 80.0}}]

        # When & Then
        with pytest.raises(ValueError) as exc_info:
            self.evaluator.learn_from_historical_data(historical_data)
        assert "学習に十分なデータがありません" in str(exc_info.value)

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-IS_TRAINED_TRUE")
    def test_is_trained_true(self) -> None:
        """学習済み状態チェック(True)"""
        # Given
        self.evaluator._set_trained_state()

        # When & Then
        assert self.evaluator.is_trained() is True

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-IS_TRAINED_FALSE")
    def test_is_trained_false(self) -> None:
        """学習済み状態チェック(False)"""
        # When & Then
        assert self.evaluator.is_trained() is False

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-GET_LEARNING_DATA_QU")
    def test_get_learning_data_quality_excellent(self) -> None:
        """学習データ品質評価(最高)"""
        # Given
        self.evaluator._set_trained_state()
        for model in self.evaluator.learning_models.values():
            model.accuracy = 0.95

        # When
        quality = self.evaluator.get_learning_data_quality()

        # Then
        assert quality == LearningDataQuality.EXCELLENT

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-GET_LEARNING_DATA_QU")
    def test_get_learning_data_quality_insufficient(self) -> None:
        """学習データ品質評価(不足)"""
        # When
        quality = self.evaluator.get_learning_data_quality()

        # Then
        assert quality == LearningDataQuality.INSUFFICIENT

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-EVALUATE_WITH_STANDA")
    def test_evaluate_with_standard_criteria(self) -> None:
        """標準基準での評価"""
        # Given
        episode_text = "これはテストエピソードです。"

        # When
        result = self.evaluator.evaluate_with_standard_criteria(episode_text)

        # Then
        assert isinstance(result, QualityEvaluationResult)
        assert result.total_score > 0
        assert result.confidence_level == 0.8
        assert not result.has_personalized_adjustments()

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-EVALUATE_WITH_LEARNE")
    def test_evaluate_with_learned_criteria(self) -> None:
        """学習済み基準での評価"""
        # Given
        self.evaluator._set_trained_state()
        self.evaluator.quality_criteria_adjustments = {"readability_adjustment": 0.1}
        episode_text = "これはテストエピソードです。"

        # When
        result = self.evaluator.evaluate_with_learned_criteria(episode_text)

        # Then
        assert isinstance(result, QualityEvaluationResult)
        assert result.total_score > 0
        assert result.confidence_level == 0.85
        assert result.has_personalized_adjustments()

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-EVALUATE_WITH_LEARNE")
    def test_evaluate_with_learned_criteria_untrained(self) -> None:
        """未学習状態での学習済み基準評価"""
        # Given
        episode_text = "これはテストエピソードです。"

        # When
        result = self.evaluator.evaluate_with_learned_criteria(episode_text)

        # Then
        # 未学習の場合は標準基準で評価される
        assert result.confidence_level == 0.8
        assert not result.has_personalized_adjustments()

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-LEARN_AUTHOR_PATTERN")
    def test_learn_author_patterns(self) -> None:
        """作者パターン学習"""
        # Given
        patterns = [
            {"pattern_type": "short_sentences", "frequency": 0.7, "effectiveness": 0.85},
            {"pattern_type": "dialogue_heavy", "frequency": 0.6, "effectiveness": 0.75},
        ]

        # When
        self.evaluator.learn_author_patterns(patterns)

        # Then
        assert "short_sentences" in self.evaluator.learned_patterns
        assert self.evaluator.learned_patterns["short_sentences"]["effectiveness"] == 0.85
        assert "sentence_length_preference" in self.evaluator.quality_criteria_adjustments

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-GET_ADJUSTED_QUALITY")
    def test_get_adjusted_quality_criteria(self) -> None:
        """調整済み品質基準取得"""
        # Given
        self.evaluator.quality_criteria_adjustments = {"readability_weight": 1.2, "dialogue_ratio_weight": 1.1}

        # When
        criteria = self.evaluator.get_adjusted_quality_criteria()

        # Then
        assert criteria["readability_weight"] == 1.2
        assert criteria["dialogue_ratio_weight"] == 1.1
        assert "sentence_length_preference" in criteria

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-ANALYZE_QUALITY_FEED")
    def test_analyze_quality_feedback_correlation_success(self) -> None:
        """品質・読者反応相関分析成功"""
        # Given
        correlation_data = [
            {"readability": 80.0 + i, "reader_rating": 4.0 + i * 0.2, "dialogue_ratio": 0.3 + i * 0.05}
            for i in range(5)
        ]

        # When
        result = self.evaluator.analyze_quality_feedback_correlation(correlation_data)

        # Then
        assert "readability_vs_rating" in result
        assert "correlation" in result["readability_vs_rating"]
        assert "optimal_dialogue_ratio" in result

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-ANALYZE_QUALITY_FEED")
    def test_analyze_quality_feedback_correlation_insufficient_data(self) -> None:
        """データ不足での相関分析"""
        # Given
        correlation_data = [{"readability": 80.0, "reader_rating": 4.0, "dialogue_ratio": 0.3}]

        # When
        result = self.evaluator.analyze_quality_feedback_correlation(correlation_data)

        # Then
        assert "error" in result
        assert "分析に十分なデータがありません" in result["error"]

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-APPLY_CORRELATION_IN")
    def test_apply_correlation_insights(self) -> None:
        """相関分析洞察の適用"""
        # Given
        correlations = {
            "readability_vs_rating": {"correlation": 0.7, "significance": 0.02},
            "optimal_dialogue_ratio": 0.35,
        }

        # When
        self.evaluator.apply_correlation_insights(correlations)

        # Then
        assert self.evaluator.quality_criteria_adjustments["readability_weight"] == 1.2
        assert self.evaluator.quality_criteria_adjustments["optimal_dialogue_ratio"] == 0.35

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-CALCULATE_CORRELATIO")
    def test_calculate_correlation_empty_data(self) -> None:
        """空データでの相関計算"""
        # When
        correlation = self.evaluator._calculate_correlation([], [])

        # Then
        assert correlation == 0.0

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-CALCULATE_CORRELATIO")
    def test_calculate_correlation_different_lengths(self) -> None:
        """異なる長さのデータでの相関計算"""
        # When
        correlation = self.evaluator._calculate_correlation([1, 2], [1, 2, 3])

        # Then
        assert correlation == 0.0

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-FILTER_HIGH_RATED_EP")
    def test_filter_high_rated_episodes(self) -> None:
        """高評価エピソードのフィルタリング"""
        # Given
        historical_data = [
            {"episode_id": "ep_1", "reader_feedback": {"rating": 4.5}},
            {"episode_id": "ep_2", "reader_feedback": {"rating": 3.5}},
            {"episode_id": "ep_3", "reader_feedback": {"rating": 4.2}},
        ]

        # When
        high_rated = self.evaluator._filter_high_rated_episodes(historical_data)

        # Then
        assert len(high_rated) == 2
        assert all(ep["reader_feedback"]["rating"] >= 4.0 for ep in high_rated)

    @pytest.mark.spec("SPEC-LEARNING_ENTITIES-GENERATE_AUTHOR_STYL")
    def test_generate_author_style_profile_edge_cases(self) -> None:
        """作者文体プロファイル生成のエッジケース"""
        # Given
        historical_data = [
            {
                "episode_id": f"ep_{i}",
                "quality_scores": {},  # 空のスコア
            }
            for i in range(5)
        ]

        # When
        self.evaluator._generate_author_style_profile(historical_data)

        # Then
        assert self.evaluator.author_style_profile is not None
        # デフォルト値が使用される
        assert self.evaluator.author_style_profile.features["avg_sentence_length"] == 35.0
