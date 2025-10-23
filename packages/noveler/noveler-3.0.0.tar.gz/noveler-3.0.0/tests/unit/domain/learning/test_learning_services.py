"""学習機能付き品質チェックドメインサービスのテスト

TDD準拠テスト:
    - StyleLearningService
- AdaptiveQualityService
- CorrelationAnalysisService


仕様書: SPEC-UNIT-TEST
"""

import statistics

import pytest

from noveler.domain.initialization.value_objects import Genre
from noveler.domain.learning.services import (
    AdaptiveQualityService,
    CorrelationAnalysisService,
    StyleLearningService,
)
from noveler.domain.learning.value_objects import (
    QualityMetric,
    WritingStyleProfile,
)
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class TestStyleLearningService:
    """StyleLearningServiceのテストクラス"""

    @pytest.fixture
    def style_service(self) -> StyleLearningService:
        """文体学習サービスのインスタンス"""
        return StyleLearningService()

    @pytest.fixture
    def sample_episode_text(self) -> str:
        """サンプルエピソードテキスト"""
        return """彼は朝早く起きた。そして準備をした。
        「おはよう」と彼女は言った。「今日も頑張ろう」
        美しい朝の光が窓から差し込んでいた。風が心地よく吹いている。
        彼は嬉しい気持ちになった!"""

    @pytest.fixture
    def fantasy_episode_text(self) -> str:
        """ファンタジーエピソードテキスト"""
        return """魔法使いは杖を振り上げた。ドラゴンが空を舞っている。
        「魔王を倒すのだ!」騎士が声を上げた。
        魔術師が呪文を唱え始めた。冒険が始まろうとしていた。"""

    @pytest.fixture
    def sample_episodes_data(self) -> list[dict]:
        """サンプルエピソードデータ"""
        return [
            {"text": "短い文です。簡潔に書きました。読みやすいです。", "rating": 4.5},
            {
                "text": "これは長い文章で、複数の要素を含んでおり、読者にとって理解が困難になる可能性があります。",
                "rating": 2.5,
            },
            {"text": "中程度の長さです。適切なバランスを保っています。", "rating": 4.0},
            {"text": "もう一つの短文。効果的です。", "rating": 4.2},
        ]

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-EXTRACT_STYLE_FEATUR")
    def test_extract_style_features_basic(self, style_service: StyleLearningService, sample_episode_text: str) -> None:
        """基本的な文体特徴抽出テスト"""
        features = style_service.extract_style_features(sample_episode_text)

        # 基本的な特徴量が抽出される
        assert "avg_sentence_length" in features
        assert "sentence_count" in features
        assert "dialogue_ratio" in features
        assert "question_count" in features
        assert "emotional_expression_count" in features
        assert "paragraph_count" in features
        assert "descriptive_ratio" in features

        # 値の妥当性チェック
        assert features["sentence_count"] > 0
        assert features["avg_sentence_length"] > 0
        assert 0 <= features["dialogue_ratio"] <= 1
        assert features["question_count"] >= 0

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-EXTRACT_STYLE_FEATUR")
    def test_extract_style_features_dialogue_ratio(self, style_service: StyleLearningService) -> None:
        """会話比率計算テスト"""
        text_with_dialogue = "彼は言った。「こんにちは」彼女は答えた。「元気ですか?」普通の文。"
        features = style_service.extract_style_features(text_with_dialogue)

        # 「こんにちは」+「元気ですか?」の文字数比率
        dialogue_chars = len("こんにちは") + len("元気ですか?")
        total_chars = len(text_with_dialogue)
        expected_ratio = dialogue_chars / total_chars

        assert abs(features["dialogue_ratio"] - expected_ratio) < 0.01

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-EXTRACT_STYLE_FEATUR")
    def test_extract_style_features_empty_text(self, style_service: StyleLearningService) -> None:
        """空テキストでの特徴抽出テスト"""
        features = style_service.extract_style_features("")

        assert features["avg_sentence_length"] == 0.0
        assert features["sentence_count"] == 0
        assert features["dialogue_ratio"] == 0.0

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-SPLIT_SENTENCES")
    def test_split_sentences(self, style_service: StyleLearningService) -> None:
        """文分割テスト"""
        text = "これは最初の文です。これは二番目の文です!これは疑問文ですか?"
        sentences = style_service._split_sentences(text)

        assert len(sentences) == 3
        assert "これは最初の文です" in sentences
        assert "これは二番目の文です" in sentences
        assert "これは疑問文ですか" in sentences

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-CALCULATE_AVG_SENTEN")
    def test_calculate_avg_sentence_length(self, style_service: StyleLearningService) -> None:
        """平均文長計算テスト"""
        sentences = ["短い", "これは中程度の長さの文", "非常に長い文章で複数の要素を含んでいる"]
        avg_length = style_service._calculate_avg_sentence_length(sentences)

        expected_avg = statistics.mean(len(s) for s in sentences)
        assert avg_length == expected_avg

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-CALCULATE_AVG_SENTEN")
    def test_calculate_avg_sentence_length_empty(self, style_service: StyleLearningService) -> None:
        """空リストでの平均文長計算テスト"""
        avg_length = style_service._calculate_avg_sentence_length([])
        assert avg_length == 0.0

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-CALCULATE_DESCRIPTIV")
    def test_calculate_descriptive_ratio(self, style_service: StyleLearningService) -> None:
        """描写比率計算テスト"""
        descriptive_text = "美しい朝だった。静かな風が吹いている。光がきらめいている。"
        ratio = style_service._calculate_descriptive_ratio(descriptive_text)

        # 描写表現が含まれているため比率が0より大きい
        assert ratio > 0.0
        assert ratio <= 1.0

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-LEARN_WRITING_PATTER")
    def test_learn_writing_patterns_insufficient_data(self, style_service: StyleLearningService) -> None:
        """データ不足時の学習パターンテスト"""
        insufficient_episodes = [{"text": "短いテスト", "rating": 3.0}]

        result = style_service.learn_writing_patterns(insufficient_episodes)

        assert "error" in result
        assert "学習に十分なエピソードがありません" in result["error"]

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-LEARN_WRITING_PATTER")
    def test_learn_writing_patterns_sufficient_data(
        self, style_service: StyleLearningService, sample_episodes_data: list[dict]
    ) -> None:
        """十分なデータでの学習パターンテスト"""
        result = style_service.learn_writing_patterns(sample_episodes_data)

        assert "error" not in result
        assert "sentence_length_preference" in result
        assert "optimal_sentence_length" in result
        assert "effectiveness_score" in result

        # 短文が高評価のため「short」が選択される
        assert result["sentence_length_preference"] == "short"
        assert 0 <= result["effectiveness_score"] <= 1.0

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-LEARN_WRITING_PATTER")
    def test_learn_writing_patterns_long_preference(self, style_service: StyleLearningService) -> None:
        """長文好み学習テスト"""
        long_preference_episodes = [
            {"text": "非常に長い文章で、複数の節を含み、詳細な描写を行っています。", "rating": 5.0},
            {"text": "短い文。", "rating": 2.0},
            {"text": "中程度の長さの文章です。", "rating": 3.0},
        ]

        result = style_service.learn_writing_patterns(long_preference_episodes)

        assert result["sentence_length_preference"] == "long"

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-LEARN_GENRE_SPECIFIC")
    def test_learn_genre_specific_style_insufficient_data(self, style_service: StyleLearningService) -> None:
        """ジャンル学習データ不足テスト"""
        insufficient_data = [{"text": "テスト", "rating": 3.0}]

        with pytest.raises(ValueError, match="ジャンル学習に十分なデータがありません"):
            style_service.learn_genre_specific_style(insufficient_data, Genre.FANTASY)

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-LEARN_GENRE_SPECIFIC")
    def test_learn_genre_specific_style_fantasy(
        self, style_service: StyleLearningService, fantasy_episode_text: str
    ) -> None:
        """ファンタジージャンル学習テスト"""
        fantasy_episodes = [
            {"text": fantasy_episode_text, "rating": 4.0},
            {"text": "魔法が使えるようになった。ドラゴンと戦った。", "rating": 4.5},
        ]

        profile = style_service.learn_genre_specific_style(fantasy_episodes, Genre.FANTASY)

        assert isinstance(profile, WritingStyleProfile)
        assert profile.genre == Genre.FANTASY or "fantasy" in profile.profile_id
        assert "fantasy_elements_density" in profile.features
        assert profile.confidence_score > 0.5
        assert profile.sample_count == len(fantasy_episodes)

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-LEARN_GENRE_SPECIFIC")
    def test_learn_genre_specific_style_science_fiction(self, style_service: StyleLearningService) -> None:
        """SF ジャンル学習テスト"""
        sf_episodes = [
            {"text": "ロボットが未来の技術を使った。AIが進歩している。", "rating": 4.0},
            {"text": "宇宙を旅し、科学的な発見をした。", "rating": 4.2},
        ]

        profile = style_service.learn_genre_specific_style(sf_episodes, Genre.SCIENCE_FICTION)

        assert "sf_elements_density" in profile.features
        assert profile.features["sf_elements_density"] > 0

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-LEARN_GENRE_SPECIFIC")
    def test_learn_genre_specific_style_other_genre(self, style_service: StyleLearningService) -> None:
        """その他ジャンル学習テスト"""
        romance_episodes = [
            {"text": "彼と彼女は愛し合っていた。ロマンチックな夜だった。", "rating": 4.0},
            {"text": "愛について考えた。心が温かくなった。", "rating": 4.3},
        ]

        profile = style_service.learn_genre_specific_style(romance_episodes, Genre.ROMANCE)

        # ジャンル固有要素は追加されないが、基本特徴は含まれる
        assert "avg_sentence_length" in profile.features
        assert "dialogue_ratio" in profile.features
        assert "fantasy_elements_density" not in profile.features
        assert "sf_elements_density" not in profile.features


class TestAdaptiveQualityService:
    """AdaptiveQualityServiceのテストクラス"""

    @pytest.fixture
    def adaptive_service(self) -> AdaptiveQualityService:
        """適応的品質サービスのインスタンス"""
        return AdaptiveQualityService()

    @pytest.fixture
    def standard_criteria(self) -> dict[str, float]:
        """標準品質基準"""
        return {
            "sentence_length_tolerance": 1.0,
            "dialogue_ratio_weight": 1.0,
            "descriptive_depth_weight": 1.0,
            "readability_target": 80.0,
        }

    @pytest.fixture
    def short_sentence_profile(self) -> WritingStyleProfile:
        """短文好み作家プロファイル"""
        return WritingStyleProfile(
            profile_id="short_writer",
            features={
                "avg_sentence_length": 20.0,
                "dialogue_ratio": 0.3,
            },
            confidence_score=0.8,
            sample_count=15,
            last_updated=project_now().datetime,
        )

    @pytest.fixture
    def dialogue_heavy_profile(self) -> WritingStyleProfile:
        """会話多用作家プロファイル"""
        return WritingStyleProfile(
            profile_id="dialogue_writer",
            features={
                "avg_sentence_length": 35.0,
                "dialogue_ratio": 0.6,
            },
            confidence_score=0.9,
            sample_count=20,
            last_updated=project_now().datetime,
        )

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-ADJUST_CRITERIA_FOR_")
    def test_adjust_criteria_for_author_short_sentences(
        self,
        adaptive_service: AdaptiveQualityService,
        standard_criteria: dict[str, float],
        short_sentence_profile: WritingStyleProfile,
    ) -> None:
        """短文好み作家の基準調整テスト"""
        adjusted = adaptive_service.adjust_criteria_for_author(standard_criteria, short_sentence_profile)

        # 短文好みなので tolerance が上がる
        assert adjusted["sentence_length_tolerance"] > standard_criteria["sentence_length_tolerance"]
        assert adjusted["sentence_length_tolerance"] == 1.3

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-ADJUST_CRITERIA_FOR_")
    def test_adjust_criteria_for_author_dialogue_heavy(
        self,
        adaptive_service: AdaptiveQualityService,
        standard_criteria: dict[str, float],
        dialogue_heavy_profile: WritingStyleProfile,
    ) -> None:
        """会話多用作家の基準調整テスト"""
        adjusted = adaptive_service.adjust_criteria_for_author(standard_criteria, dialogue_heavy_profile)

        # 会話多用なので dialogue_ratio_weight が上がる
        assert adjusted["dialogue_ratio_weight"] > standard_criteria["dialogue_ratio_weight"]
        assert adjusted["dialogue_ratio_weight"] == 1.2

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-ADJUST_CRITERIA_FOR_")
    def test_adjust_criteria_for_author_low_dialogue(
        self, adaptive_service: AdaptiveQualityService, standard_criteria: dict[str, float]
    ) -> None:
        """会話少なめ作家の基準調整テスト"""
        low_dialogue_profile = WritingStyleProfile(
            profile_id="descriptive_writer",
            features={
                "avg_sentence_length": 40.0,
                "dialogue_ratio": 0.1,
            },
            confidence_score=0.7,
            sample_count=12,
            last_updated=project_now().datetime,
        )

        adjusted = adaptive_service.adjust_criteria_for_author(standard_criteria, low_dialogue_profile)

        # 会話少なめなので dialogue_ratio_weight が下がり、descriptive_depth_weight が上がる
        assert adjusted["dialogue_ratio_weight"] < standard_criteria["dialogue_ratio_weight"]
        assert adjusted["descriptive_depth_weight"] > standard_criteria["descriptive_depth_weight"]

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-ADJUST_CRITERIA_CONF")
    def test_adjust_criteria_confidence_adjustment(
        self, adaptive_service: AdaptiveQualityService, standard_criteria: dict[str, float]
    ) -> None:
        """信頼度による調整強度テスト"""
        low_confidence_profile = WritingStyleProfile(
            profile_id="uncertain_writer",
            features={"avg_sentence_length": 20.0},
            confidence_score=0.3,  # 低信頼度
            sample_count=5,
            last_updated=project_now().datetime,
        )

        adjusted = adaptive_service.adjust_criteria_for_author(standard_criteria, low_confidence_profile)

        # 低信頼度なので調整が控えめになる
        tolerance_diff = adjusted["sentence_length_tolerance"] - standard_criteria["sentence_length_tolerance"]
        # 信頼度0.3倍されるので、調整幅が小さい
        assert abs(tolerance_diff) < 0.2

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-UPDATE_CRITERIA_FROM")
    def test_update_criteria_from_feedback_high_rating(self, adaptive_service: AdaptiveQualityService) -> None:
        """高評価フィードバックからの基準更新テスト"""
        episode_data = {
            "quality_scores": {"readability": 85, "dialogue_ratio": 90, "narrative_depth": 75},
            "reader_feedback": {"rating": 4.5, "comments": ["読みやすい", "面白い"]},
        }

        updated_weights = adaptive_service.update_criteria_from_feedback(episode_data)

        # 高スコア項目の重みが上がる
        assert updated_weights.get("readability_weight") == 1.1
        assert updated_weights.get("dialogue_ratio_weight") == 1.1
        # 低スコア項目は重み変更なし
        assert "narrative_depth_weight" not in updated_weights

        # ポジティブコメントによる信頼度向上
        assert updated_weights.get("confidence_increase") > 0

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-UPDATE_CRITERIA_FROM")
    def test_update_criteria_from_feedback_low_rating(self, adaptive_service: AdaptiveQualityService) -> None:
        """低評価フィードバックからの基準更新テスト"""
        episode_data = {
            "quality_scores": {"readability": 50, "dialogue_ratio": 40, "narrative_depth": 80},
            "reader_feedback": {"rating": 2.0, "comments": ["わかりにくい"]},
        }

        updated_weights = adaptive_service.update_criteria_from_feedback(episode_data)

        # 低スコア項目の重みが上がる
        assert updated_weights.get("readability_weight") == 1.2
        assert updated_weights.get("dialogue_ratio_weight") == 1.2
        # 高スコア項目は重み変更なし
        assert "narrative_depth_weight" not in updated_weights

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-OPTIMIZE_QUALITY_STA")
    def test_optimize_quality_standards_insufficient_data(
        self, adaptive_service: AdaptiveQualityService, standard_criteria: dict[str, float]
    ) -> None:
        """データ不足時の品質基準最適化テスト"""
        insufficient_data = [{"reader_rating": 3.0}] * 3

        optimized = adaptive_service.optimize_quality_standards(insufficient_data, standard_criteria)

        # データ不足時は現在基準をそのまま返す
        assert optimized == standard_criteria

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-OPTIMIZE_QUALITY_STA")
    def test_optimize_quality_standards_sufficient_data(
        self, adaptive_service: AdaptiveQualityService, standard_criteria: dict[str, float]
    ) -> None:
        """十分なデータでの品質基準最適化テスト"""
        historical_data = [
            {"reader_rating": 4.0, "quality_scores": {"readability": 85, "dialogue_ratio": 80}},
            {"reader_rating": 4.5, "quality_scores": {"readability": 90, "dialogue_ratio": 75}},
            {"reader_rating": 4.2, "quality_scores": {"readability": 88, "dialogue_ratio": 85}},
            {"reader_rating": 3.0, "quality_scores": {"readability": 60, "dialogue_ratio": 70}},
            {"reader_rating": 4.8, "quality_scores": {"readability": 95, "dialogue_ratio": 90}},
        ]

        criteria_with_targets = standard_criteria.copy()
        criteria_with_targets.update({"readability_target": 75.0, "dialogue_ratio_target": 70.0})

        optimized = adaptive_service.optimize_quality_standards(historical_data, criteria_with_targets)

        # 高評価エピソードの平均スコアを反映して基準が調整される
        assert "readability_target" in optimized
        assert "dialogue_ratio_target" in optimized
        # 最適化されて値が変わっている
        assert optimized["readability_target"] != criteria_with_targets["readability_target"]

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-FILTER_HIGH_PERFORMA")
    def test_filter_high_performance_episodes(self, adaptive_service: AdaptiveQualityService) -> None:
        """高パフォーマンスエピソードフィルタリングテスト"""
        historical_data = [
            {"reader_rating": 4.5},
            {"reader_rating": 3.0},
            {"reader_rating": 4.0},
            {"reader_rating": 2.5},
            {"reader_rating": 4.8},
        ]

        high_performance = adaptive_service._filter_high_performance_episodes(historical_data)

        # 4.0以上のエピソードのみフィルタリング
        assert len(high_performance) == 3
        ratings = [ep["reader_rating"] for ep in high_performance]
        assert all(rating >= 4.0 for rating in ratings)


class TestCorrelationAnalysisService:
    """CorrelationAnalysisServiceのテストクラス"""

    @pytest.fixture
    def correlation_service(self) -> CorrelationAnalysisService:
        """相関分析サービスのインスタンス"""
        return CorrelationAnalysisService()

    @pytest.fixture
    def quality_data_sample(self) -> list[dict]:
        """品質データサンプル"""
        return [
            {"readability": 80, "dialogue_ratio": 70, "narrative_depth": 85},
            {"readability": 85, "dialogue_ratio": 75, "narrative_depth": 80},
            {"readability": 90, "dialogue_ratio": 80, "narrative_depth": 90},
            {"readability": 75, "dialogue_ratio": 65, "narrative_depth": 75},
            {"readability": 95, "dialogue_ratio": 85, "narrative_depth": 95},
            {"readability": 70, "dialogue_ratio": 60, "narrative_depth": 70},
        ]

    @pytest.fixture
    def reader_data_sample(self) -> list[dict]:
        """読者データサンプル(品質データと対応)"""
        return [
            {"rating": 4.0},
            {"rating": 4.2},
            {"rating": 4.8},
            {"rating": 3.5},
            {"rating": 5.0},
            {"rating": 3.0},
        ]

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-ANALYZE_QUALITY_READ")
    def test_analyze_quality_reader_correlation_insufficient_data(
        self, correlation_service: CorrelationAnalysisService
    ) -> None:
        """データ不足時の相関分析テスト"""
        insufficient_quality = [{"readability": 80}, {"readability": 85}]
        insufficient_reader = [{"rating": 4.0}, {"rating": 4.2}]

        correlations = correlation_service.analyze_quality_reader_correlation(insufficient_quality, insufficient_reader)

        assert correlations == []

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-ANALYZE_QUALITY_READ")
    def test_analyze_quality_reader_correlation_mismatched_data(
        self, correlation_service: CorrelationAnalysisService, quality_data_sample: list[dict]
    ) -> None:
        """データ長不一致時の相関分析テスト"""
        mismatched_reader = [{"rating": 4.0}, {"rating": 4.2}]  # 長さが異なる

        correlations = correlation_service.analyze_quality_reader_correlation(quality_data_sample, mismatched_reader)

        assert correlations == []

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-ANALYZE_QUALITY_READ")
    def test_analyze_quality_reader_correlation_sufficient_data(
        self,
        correlation_service: CorrelationAnalysisService,
        quality_data_sample: list[dict],
        reader_data_sample: list[dict],
    ) -> None:
        """十分なデータでの相関分析テスト"""
        correlations = correlation_service.analyze_quality_reader_correlation(quality_data_sample, reader_data_sample)

        assert len(correlations) > 0

        # 各相関結果の構造チェック
        for corr in correlations:
            assert "metric" in corr
            assert "correlation" in corr
            assert "significance" in corr
            assert "sample_size" in corr
            assert "actionable_insight" in corr

            # 相関係数は -1 から 1 の範囲
            assert -1.0 <= corr["correlation"] <= 1.0
            assert corr["sample_size"] == len(quality_data_sample)

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-CALCULATE_CORRELATIO")
    def test_calculate_correlation_perfect_positive(self, correlation_service: CorrelationAnalysisService) -> None:
        """完全正の相関計算テスト"""
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]  # x の2倍

        correlation = correlation_service._calculate_correlation(x, y)

        # 完全正の相関なので1.0に近い
        assert abs(correlation - 1.0) < 0.01

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-CALCULATE_CORRELATIO")
    def test_calculate_correlation_perfect_negative(self, correlation_service: CorrelationAnalysisService) -> None:
        """完全負の相関計算テスト"""
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [5.0, 4.0, 3.0, 2.0, 1.0]  # x の逆順

        correlation = correlation_service._calculate_correlation(x, y)

        # 完全負の相関なので-1.0に近い
        assert abs(correlation - (-1.0)) < 0.01

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-CALCULATE_CORRELATIO")
    def test_calculate_correlation_no_correlation(self, correlation_service: CorrelationAnalysisService) -> None:
        """無相関データの相関計算テスト"""
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [3.0, 1.0, 4.0, 2.0, 5.0]  # ランダム的

        correlation = correlation_service._calculate_correlation(x, y)

        # 相関は低い
        assert abs(correlation) < 0.8

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-CALCULATE_CORRELATIO")
    def test_calculate_correlation_insufficient_data(self, correlation_service: CorrelationAnalysisService) -> None:
        """データ不足時の相関計算テスト"""
        x = [1.0]
        y = [2.0]

        correlation = correlation_service._calculate_correlation(x, y)

        assert correlation == 0.0

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-CALCULATE_CORRELATIO")
    def test_calculate_correlation_zero_variance(self, correlation_service: CorrelationAnalysisService) -> None:
        """分散ゼロデータの相関計算テスト"""
        x = [5.0, 5.0, 5.0, 5.0]  # 全て同じ値
        y = [1.0, 2.0, 3.0, 4.0]

        correlation = correlation_service._calculate_correlation(x, y)

        assert correlation == 0.0

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-CALCULATE_SIGNIFICAN")
    def test_calculate_significance_high_correlation_large_sample(
        self, correlation_service: CorrelationAnalysisService
    ) -> None:
        """高相関・大サンプルでの有意性計算テスト"""
        significance = correlation_service._calculate_significance(0.8, 20)

        # 高相関・大サンプルなので有意性が高い(p値が小さい)
        assert significance <= 0.05

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-CALCULATE_SIGNIFICAN")
    def test_calculate_significance_low_correlation_small_sample(
        self, correlation_service: CorrelationAnalysisService
    ) -> None:
        """低相関・小サンプルでの有意性計算テスト"""
        significance = correlation_service._calculate_significance(0.2, 5)

        # 低相関・小サンプルなので有意性が低い(p値が大きい)
        assert significance > 0.1

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-GENERATE_INSIGHT_STR")
    def test_generate_insight_strong_positive_significant(
        self, correlation_service: CorrelationAnalysisService
    ) -> None:
        """強い正の相関・有意な場合の洞察生成テスト"""
        insight = correlation_service._generate_insight(QualityMetric.READABILITY, 0.7, 0.01)

        assert "強く寄与" in insight
        assert "重点的に改善" in insight

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-GENERATE_INSIGHT_MOD")
    def test_generate_insight_moderate_positive_significant(
        self, correlation_service: CorrelationAnalysisService
    ) -> None:
        """中程度正の相関・有意な場合の洞察生成テスト"""
        insight = correlation_service._generate_insight(QualityMetric.DIALOGUE_RATIO, 0.4, 0.03)

        assert "寄与" in insight
        assert "改善を検討" in insight

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-GENERATE_INSIGHT_NEG")
    def test_generate_insight_negative_correlation(self, correlation_service: CorrelationAnalysisService) -> None:
        """負の相関の場合の洞察生成テスト"""
        insight = correlation_service._generate_insight(QualityMetric.SENTENCE_VARIETY, -0.4, 0.05)

        assert "過度な重視" in insight
        assert "バランスを見直し" in insight

    @pytest.mark.spec("SPEC-LEARNING_SERVICES-GENERATE_INSIGHT_NOT")
    def test_generate_insight_not_significant(self, correlation_service: CorrelationAnalysisService) -> None:
        """有意でない場合の洞察生成テスト"""
        insight = correlation_service._generate_insight(
            QualityMetric.NARRATIVE_DEPTH,
            0.3,
            0.15,  # 有意でない
        )

        assert "有意な関係は見つかりませんでした" in insight
