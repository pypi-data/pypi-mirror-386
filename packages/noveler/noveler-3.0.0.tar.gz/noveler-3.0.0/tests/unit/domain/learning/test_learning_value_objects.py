#!/usr/bin/env python3
"""学習機能付き品質チェックドメイン - 値オブジェクトのユニットテスト

TDD原則に従い、値オブジェクトの不変性とビジネスルールをテスト


仕様書: SPEC-UNIT-TEST
"""

import pytest

from noveler.domain.learning.value_objects import (
    CorrelationInsight,
    LearningDataQuality,
    QualityEvaluationResult,
    QualityMetric,
    WritingStyleProfile,
)
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class TestQualityMetric:
    """QualityMetric列挙型のテスト"""

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-ALL_METRICS_DEFINED")
    def test_all_metrics_defined(self) -> None:
        """全てのメトリックが定義されていることを確認"""
        expected_metrics = [
            "readability",
            "dialogue_ratio",
            "sentence_variety",
            "narrative_depth",
            "emotional_intensity",
        ]

        actual_metrics = [metric.value for metric in QualityMetric]

        assert set(expected_metrics) == set(actual_metrics)

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-METRIC_VALUES")
    def test_metric_values(self) -> None:
        """メトリック値の確認"""
        assert QualityMetric.READABILITY.value == "readability"
        assert QualityMetric.DIALOGUE_RATIO.value == "dialogue_ratio"
        assert QualityMetric.SENTENCE_VARIETY.value == "sentence_variety"
        assert QualityMetric.NARRATIVE_DEPTH.value == "narrative_depth"
        assert QualityMetric.EMOTIONAL_INTENSITY.value == "emotional_intensity"


class TestLearningDataQuality:
    """LearningDataQuality列挙型のテスト"""

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-ALL_QUALITY_LEVELS_D")
    def test_all_quality_levels_defined(self) -> None:
        """全ての品質レベルが定義されていることを確認"""
        expected_levels = ["insufficient", "low", "medium", "high", "excellent"]

        actual_levels = [level.value for level in LearningDataQuality]

        assert set(expected_levels) == set(actual_levels)

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-QUALITY_LEVEL_VALUES")
    def test_quality_level_values(self) -> None:
        """品質レベル値の確認"""
        assert LearningDataQuality.INSUFFICIENT.value == "insufficient"
        assert LearningDataQuality.LOW.value == "low"
        assert LearningDataQuality.MEDIUM.value == "medium"
        assert LearningDataQuality.HIGH.value == "high"
        assert LearningDataQuality.EXCELLENT.value == "excellent"


class TestWritingStyleProfile:
    """WritingStyleProfile値オブジェクトのテスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行"""
        self.valid_features = {
            "avg_sentence_length": 35.0,
            "dialogue_ratio": 0.4,
            "emotional_words_ratio": 0.15,
            "comma_frequency": 0.3,
        }
        self.timestamp = project_now().datetime

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-CREATE_VALID_PROFILE")
    def test_create_valid_profile(self) -> None:
        """有効なプロファイルの作成"""
        # When
        profile = WritingStyleProfile(
            profile_id="test_profile",
            features=self.valid_features,
            confidence_score=0.85,
            sample_count=20,
            last_updated=self.timestamp,
        )

        # Then
        assert profile.profile_id == "test_profile"
        assert profile.features == self.valid_features
        assert profile.confidence_score == 0.85
        assert profile.sample_count == 20
        assert profile.last_updated == self.timestamp

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-IMMUTABILITY")
    def test_immutability(self) -> None:
        """不変性の確認"""
        # Given
        profile = WritingStyleProfile(
            profile_id="test_profile",
            features=self.valid_features,
            confidence_score=0.85,
            sample_count=20,
            last_updated=self.timestamp,
        )

        # When & Then
        with pytest.raises(AttributeError, match=".*"):
            profile.profile_id = "new_id"

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-VALIDATE_RATIO_FEATU")
    def test_validate_ratio_feature_valid(self) -> None:
        """比率特徴量の有効範囲検証(正常)"""
        # Given
        features = {
            "dialogue_ratio": 0.5,
            "emotional_words_ratio": 0.2,
        }

        # When & Then (例外が発生しない)
        WritingStyleProfile(
            profile_id="test",
            features=features,
            confidence_score=0.8,
            sample_count=10,
            last_updated=self.timestamp,
        )

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-VALIDATE_RATIO_FEATU")
    def test_validate_ratio_feature_invalid(self) -> None:
        """比率特徴量の有効範囲検証(異常)"""
        # Given
        features = {"dialogue_ratio": 1.5}  # 範囲外

        # When & Then
        with pytest.raises(ValueError) as exc_info:
            WritingStyleProfile(
                profile_id="test",
                features=features,
                confidence_score=0.8,
                sample_count=10,
                last_updated=self.timestamp,
            )

        assert "特徴量が有効範囲外: dialogue_ratio=1.5" in str(exc_info.value)

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-VALIDATE_SENTENCE_LE")
    def test_validate_sentence_length_valid(self) -> None:
        """文長特徴量の有効範囲検証(正常)"""
        # Given
        features = {"avg_sentence_length": 50.0}

        # When & Then (例外が発生しない)
        WritingStyleProfile(
            profile_id="test",
            features=features,
            confidence_score=0.8,
            sample_count=10,
            last_updated=self.timestamp,
        )

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-VALIDATE_SENTENCE_LE")
    def test_validate_sentence_length_invalid(self) -> None:
        """文長特徴量の有効範囲検証(異常)"""
        # Given
        features = {"avg_sentence_length": 250.0}  # 範囲外

        # When & Then
        with pytest.raises(ValueError) as exc_info:
            WritingStyleProfile(
                profile_id="test",
                features=features,
                confidence_score=0.8,
                sample_count=10,
                last_updated=self.timestamp,
            )

        assert "特徴量が有効範囲外: avg_sentence_length=250.0" in str(exc_info.value)

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-VALIDATE_CONFIDENCE_")
    def test_validate_confidence_valid(self) -> None:
        """信頼度の有効範囲検証(正常)"""
        # When & Then (例外が発生しない)
        WritingStyleProfile(
            profile_id="test",
            features=self.valid_features,
            confidence_score=1.0,
            sample_count=10,
            last_updated=self.timestamp,
        )

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-VALIDATE_CONFIDENCE_")
    def test_validate_confidence_invalid(self) -> None:
        """信頼度の有効範囲検証(異常)"""
        # When & Then
        with pytest.raises(ValueError) as exc_info:
            WritingStyleProfile(
                profile_id="test",
                features=self.valid_features,
                confidence_score=1.5,  # 範囲外
                sample_count=10,
                last_updated=self.timestamp,
            )

        assert "信頼度が有効範囲外: 1.5" in str(exc_info.value)

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-GET_FEATURE_EXISTING")
    def test_get_feature_existing(self) -> None:
        """存在する特徴量の取得"""
        # Given
        profile = WritingStyleProfile(
            profile_id="test",
            features=self.valid_features,
            confidence_score=0.8,
            sample_count=10,
            last_updated=self.timestamp,
        )

        # When
        value = profile.get_feature("dialogue_ratio")

        # Then
        assert value == 0.4

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-GET_FEATURE_NON_EXIS")
    def test_get_feature_non_existing(self) -> None:
        """存在しない特徴量の取得"""
        # Given
        profile = WritingStyleProfile(
            profile_id="test",
            features=self.valid_features,
            confidence_score=0.8,
            sample_count=10,
            last_updated=self.timestamp,
        )

        # When
        value = profile.get_feature("unknown_feature")

        # Then
        assert value == 0.0

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-IS_RELIABLE_TRUE")
    def test_is_reliable_true(self) -> None:
        """信頼度十分チェック(True)"""
        # Given
        profile = WritingStyleProfile(
            profile_id="test",
            features=self.valid_features,
            confidence_score=0.85,
            sample_count=15,
            last_updated=self.timestamp,
        )

        # When & Then
        assert profile.is_reliable() is True

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-IS_RELIABLE_LOW_CONF")
    def test_is_reliable_low_confidence(self) -> None:
        """信頼度十分チェック(信頼度不足)"""
        # Given
        profile = WritingStyleProfile(
            profile_id="test",
            features=self.valid_features,
            confidence_score=0.7,  # 閾値未満
            sample_count=15,
            last_updated=self.timestamp,
        )

        # When & Then
        assert profile.is_reliable() is False

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-IS_RELIABLE_LOW_SAMP")
    def test_is_reliable_low_sample_count(self) -> None:
        """信頼度十分チェック(サンプル数不足)"""
        # Given
        profile = WritingStyleProfile(
            profile_id="test",
            features=self.valid_features,
            confidence_score=0.85,
            sample_count=5,  # 閾値未満
            last_updated=self.timestamp,
        )

        # When & Then
        assert profile.is_reliable() is False

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-CALCULATE_SIMILARITY")
    def test_calculate_similarity_identical(self) -> None:
        """類似度計算(同一プロファイル)"""
        # Given
        profile1 = WritingStyleProfile(
            profile_id="test1",
            features=self.valid_features,
            confidence_score=0.8,
            sample_count=10,
            last_updated=self.timestamp,
        )

        profile2 = WritingStyleProfile(
            profile_id="test2",
            features=self.valid_features,
            confidence_score=0.8,
            sample_count=10,
            last_updated=self.timestamp,
        )

        # When
        similarity = profile1.calculate_similarity(profile2)

        # Then
        assert similarity == pytest.approx(1.0, abs=0.001)

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-CALCULATE_SIMILARITY")
    def test_calculate_similarity_different(self) -> None:
        """類似度計算(異なるプロファイル)"""
        # Given
        profile1 = WritingStyleProfile(
            profile_id="test1",
            features={"dialogue_ratio": 0.2, "emotional_words_ratio": 0.1},
            confidence_score=0.8,
            sample_count=10,
            last_updated=self.timestamp,
        )

        profile2 = WritingStyleProfile(
            profile_id="test2",
            features={"dialogue_ratio": 0.8, "emotional_words_ratio": 0.9},
            confidence_score=0.8,
            sample_count=10,
            last_updated=self.timestamp,
        )

        # When
        similarity = profile1.calculate_similarity(profile2)

        # Then
        assert 0 <= similarity <= 1

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-CALCULATE_SIMILARITY")
    def test_calculate_similarity_no_common_features(self) -> None:
        """類似度計算(共通特徴量なし)"""
        # Given
        profile1 = WritingStyleProfile(
            profile_id="test1",
            features={"dialogue_ratio": 0.4},
            confidence_score=0.8,
            sample_count=10,
            last_updated=self.timestamp,
        )

        profile2 = WritingStyleProfile(
            profile_id="test2",
            features={"emotional_words_ratio": 0.2},
            confidence_score=0.8,
            sample_count=10,
            last_updated=self.timestamp,
        )

        # When
        similarity = profile1.calculate_similarity(profile2)

        # Then
        assert similarity == 0.0

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-CALCULATE_SIMILARITY")
    def test_calculate_similarity_zero_magnitude(self) -> None:
        """類似度計算(ゼロベクトル)"""
        # Given
        profile1 = WritingStyleProfile(
            profile_id="test1",
            features={"dialogue_ratio": 0.0},
            confidence_score=0.8,
            sample_count=10,
            last_updated=self.timestamp,
        )

        profile2 = WritingStyleProfile(
            profile_id="test2",
            features={"dialogue_ratio": 0.5},
            confidence_score=0.8,
            sample_count=10,
            last_updated=self.timestamp,
        )

        # When
        similarity = profile1.calculate_similarity(profile2)

        # Then
        assert similarity == 0.0

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-GET_FEATURE_IMPORTAN")
    def test_get_feature_importance_weights(self) -> None:
        """特徴量重要度ウェイト取得"""
        # Given
        profile = WritingStyleProfile(
            profile_id="test",
            features=self.valid_features,
            confidence_score=0.8,
            sample_count=10,
            last_updated=self.timestamp,
        )

        # When
        weights = profile.get_feature_importance_weights()

        # Then
        assert "avg_sentence_length" in weights
        assert "dialogue_ratio" in weights
        # 信頼度による調整確認
        assert weights["avg_sentence_length"] == pytest.approx(0.2 * 0.8)


class TestQualityEvaluationResult:
    """QualityEvaluationResult値オブジェクトのテスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行"""
        self.metric_scores = {
            QualityMetric.READABILITY: 85.0,
            QualityMetric.DIALOGUE_RATIO: 80.0,
            QualityMetric.NARRATIVE_DEPTH: 82.0,
        }
        self.timestamp = project_now().datetime

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-CREATE_EVALUATION_RE")
    def test_create_evaluation_result(self) -> None:
        """評価結果の作成"""
        # When
        result = QualityEvaluationResult(
            total_score=82.33,
            metric_scores=self.metric_scores,
            confidence_level=0.85,
            personalized_adjustments={"readability_weight": 1.1},
            evaluation_timestamp=self.timestamp,
        )

        # Then
        assert result.total_score == 82.33
        assert result.metric_scores == self.metric_scores
        assert result.confidence_level == 0.85
        assert result.personalized_adjustments == {"readability_weight": 1.1}
        assert result.evaluation_timestamp == self.timestamp

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-IMMUTABILITY")
    def test_immutability(self) -> None:
        """不変性の確認"""
        # Given
        result = QualityEvaluationResult(
            total_score=82.33,
            metric_scores=self.metric_scores,
            confidence_level=0.85,
            personalized_adjustments={},
            evaluation_timestamp=self.timestamp,
        )

        # When & Then
        with pytest.raises(AttributeError, match=".*"):
            result.total_score = 90.0

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-HAS_PERSONALIZED_ADJ")
    def test_has_personalized_adjustments_true(self) -> None:
        """個人化調整有無チェック(あり)"""
        # Given
        result = QualityEvaluationResult(
            total_score=82.33,
            metric_scores=self.metric_scores,
            confidence_level=0.85,
            personalized_adjustments={"readability_weight": 1.1},
            evaluation_timestamp=self.timestamp,
        )

        # When & Then
        assert result.has_personalized_adjustments() is True

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-HAS_PERSONALIZED_ADJ")
    def test_has_personalized_adjustments_false(self) -> None:
        """個人化調整有無チェック(なし)"""
        # Given
        result = QualityEvaluationResult(
            total_score=82.33,
            metric_scores=self.metric_scores,
            confidence_level=0.85,
            personalized_adjustments={},
            evaluation_timestamp=self.timestamp,
        )

        # When & Then
        assert result.has_personalized_adjustments() is False

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-GET_METRIC_SCORE_EXI")
    def test_get_metric_score_existing(self) -> None:
        """メトリック別スコア取得(存在)"""
        # Given
        result = QualityEvaluationResult(
            total_score=82.33,
            metric_scores=self.metric_scores,
            confidence_level=0.85,
            personalized_adjustments={},
            evaluation_timestamp=self.timestamp,
        )

        # When
        score = result.get_metric_score(QualityMetric.READABILITY)

        # Then
        assert score == 85.0

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-GET_METRIC_SCORE_NON")
    def test_get_metric_score_non_existing(self) -> None:
        """メトリック別スコア取得(非存在)"""
        # Given
        result = QualityEvaluationResult(
            total_score=82.33,
            metric_scores=self.metric_scores,
            confidence_level=0.85,
            personalized_adjustments={},
            evaluation_timestamp=self.timestamp,
        )

        # When
        score = result.get_metric_score(QualityMetric.SENTENCE_VARIETY)

        # Then
        assert score == 0.0

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-IS_HIGH_QUALITY_TRUE")
    def test_is_high_quality_true(self) -> None:
        """高品質判定(True)"""
        # Given
        result = QualityEvaluationResult(
            total_score=85.0,
            metric_scores=self.metric_scores,
            confidence_level=0.8,
            personalized_adjustments={},
            evaluation_timestamp=self.timestamp,
        )

        # When & Then
        assert result.is_high_quality() is True

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-IS_HIGH_QUALITY_LOW_")
    def test_is_high_quality_low_score(self) -> None:
        """高品質判定(スコア不足)"""
        # Given
        result = QualityEvaluationResult(
            total_score=75.0,  # 閾値未満
            metric_scores=self.metric_scores,
            confidence_level=0.8,
            personalized_adjustments={},
            evaluation_timestamp=self.timestamp,
        )

        # When & Then
        assert result.is_high_quality() is False

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-IS_HIGH_QUALITY_LOW_")
    def test_is_high_quality_low_confidence(self) -> None:
        """高品質判定(信頼度不足)"""
        # Given
        result = QualityEvaluationResult(
            total_score=85.0,
            metric_scores=self.metric_scores,
            confidence_level=0.6,  # 閾値未満
            personalized_adjustments={},
            evaluation_timestamp=self.timestamp,
        )

        # When & Then
        assert result.is_high_quality() is False


class TestCorrelationInsight:
    """CorrelationInsight値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-CREATE_CORRELATION_I")
    def test_create_correlation_insight(self) -> None:
        """相関分析洞察の作成"""
        # When
        insight = CorrelationInsight(
            metric_pair=("readability", "reader_rating"),
            correlation_coefficient=0.75,
            significance_level=0.01,
            sample_size=50,
            actionable_insight="可読性の向上が読者評価向上につながる",
        )

        # Then
        assert insight.metric_pair == ("readability", "reader_rating")
        assert insight.correlation_coefficient == 0.75
        assert insight.significance_level == 0.01
        assert insight.sample_size == 50
        assert insight.actionable_insight == "可読性の向上が読者評価向上につながる"

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-IMMUTABILITY")
    def test_immutability(self) -> None:
        """不変性の確認"""
        # Given
        insight = CorrelationInsight(
            metric_pair=("readability", "reader_rating"),
            correlation_coefficient=0.75,
            significance_level=0.01,
            sample_size=50,
            actionable_insight="可読性の向上が読者評価向上につながる",
        )

        # When & Then
        with pytest.raises(AttributeError, match=".*"):
            insight.correlation_coefficient = 0.8

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-IS_SIGNIFICANT_TRUE")
    def test_is_significant_true(self) -> None:
        """統計的有意性チェック(有意)"""
        # Given
        insight = CorrelationInsight(
            metric_pair=("readability", "reader_rating"),
            correlation_coefficient=0.5,
            significance_level=0.01,  # < 0.05
            sample_size=50,
            actionable_insight="相関あり",
        )

        # When & Then
        assert insight.is_significant() is True

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-IS_SIGNIFICANT_HIGH_")
    def test_is_significant_high_p_value(self) -> None:
        """統計的有意性チェック(p値が高い)"""
        # Given
        insight = CorrelationInsight(
            metric_pair=("readability", "reader_rating"),
            correlation_coefficient=0.5,
            significance_level=0.1,  # > 0.05
            sample_size=50,
            actionable_insight="相関あり",
        )

        # When & Then
        assert insight.is_significant() is False

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-IS_SIGNIFICANT_LOW_C")
    def test_is_significant_low_correlation(self) -> None:
        """統計的有意性チェック(相関係数が低い)"""
        # Given
        insight = CorrelationInsight(
            metric_pair=("readability", "reader_rating"),
            correlation_coefficient=0.2,  # < 0.3
            significance_level=0.01,
            sample_size=50,
            actionable_insight="弱い相関",
        )

        # When & Then
        assert insight.is_significant() is False

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-GET_STRENGTH_DESCRIP")
    def test_get_strength_description_very_strong(self) -> None:
        """相関の強さ説明(非常に強い)"""
        # Given
        insight = CorrelationInsight(
            metric_pair=("readability", "reader_rating"),
            correlation_coefficient=0.85,
            significance_level=0.01,
            sample_size=50,
            actionable_insight="強い相関",
        )

        # When
        description = insight.get_strength_description()

        # Then
        assert description == "非常に強い"

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-GET_STRENGTH_DESCRIP")
    def test_get_strength_description_strong(self) -> None:
        """相関の強さ説明(強い)"""
        # Given
        insight = CorrelationInsight(
            metric_pair=("readability", "reader_rating"),
            correlation_coefficient=0.65,
            significance_level=0.01,
            sample_size=50,
            actionable_insight="相関あり",
        )

        # When
        description = insight.get_strength_description()

        # Then
        assert description == "強い"

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-GET_STRENGTH_DESCRIP")
    def test_get_strength_description_moderate(self) -> None:
        """相関の強さ説明(中程度)"""
        # Given
        insight = CorrelationInsight(
            metric_pair=("readability", "reader_rating"),
            correlation_coefficient=0.45,
            significance_level=0.01,
            sample_size=50,
            actionable_insight="相関あり",
        )

        # When
        description = insight.get_strength_description()

        # Then
        assert description == "中程度"

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-GET_STRENGTH_DESCRIP")
    def test_get_strength_description_weak(self) -> None:
        """相関の強さ説明(弱い)"""
        # Given
        insight = CorrelationInsight(
            metric_pair=("readability", "reader_rating"),
            correlation_coefficient=0.25,
            significance_level=0.01,
            sample_size=50,
            actionable_insight="弱い相関",
        )

        # When
        description = insight.get_strength_description()

        # Then
        assert description == "弱い"

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-GET_STRENGTH_DESCRIP")
    def test_get_strength_description_very_weak(self) -> None:
        """相関の強さ説明(非常に弱い)"""
        # Given
        insight = CorrelationInsight(
            metric_pair=("readability", "reader_rating"),
            correlation_coefficient=0.1,
            significance_level=0.01,
            sample_size=50,
            actionable_insight="ほぼ相関なし",
        )

        # When
        description = insight.get_strength_description()

        # Then
        assert description == "非常に弱い"

    @pytest.mark.spec("SPEC-LEARNING_VALUE_OBJECTS-GET_STRENGTH_DESCRIP")
    def test_get_strength_description_negative_correlation(self) -> None:
        """相関の強さ説明(負の相関)"""
        # Given
        insight = CorrelationInsight(
            metric_pair=("readability", "reader_rating"),
            correlation_coefficient=-0.75,  # 負の値
            significance_level=0.01,
            sample_size=50,
            actionable_insight="負の相関",
        )

        # When
        description = insight.get_strength_description()

        # Then
        assert description == "強い"  # 絶対値で判定される
