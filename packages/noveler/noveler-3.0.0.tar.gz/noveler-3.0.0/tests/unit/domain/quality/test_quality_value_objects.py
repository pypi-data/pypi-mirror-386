"""品質管理ドメインの値オブジェクトのテスト

TDD準拠テスト:
    - ErrorSeverity (Enum)
- RuleCategory (Enum)
- LineNumber
- ErrorContext
- QualityScore
- AdaptationStrength (Enum)
- EvaluationContext


仕様書: SPEC-UNIT-TEST
"""

import pytest

from noveler.domain.exceptions import DomainException
from noveler.domain.quality.value_objects import (
    AdaptationStrength,
    ErrorContext,
    ErrorSeverity,
    EvaluationContext,
    LineNumber,
    QualityScore,
    RuleCategory,
)


class TestErrorSeverity:
    """ErrorSeverity(Enum)のテストクラス"""

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-ERROR_SEVERITY_VALUE")
    def test_error_severity_values(self) -> None:
        """エラー重要度値テスト"""
        assert ErrorSeverity.ERROR.value == "error"
        assert ErrorSeverity.WARNING.value == "warning"
        assert ErrorSeverity.INFO.value == "info"

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-ERROR_SEVERITY_ENUM_")
    def test_error_severity_enum_count(self) -> None:
        """エラー重要度数テスト"""
        assert len(ErrorSeverity) == 3

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-ERROR_SEVERITY_MEMBE")
    def test_error_severity_membership(self) -> None:
        """エラー重要度メンバーシップテスト"""
        assert ErrorSeverity.ERROR in ErrorSeverity
        assert ErrorSeverity.WARNING in ErrorSeverity
        assert ErrorSeverity.INFO in ErrorSeverity


class TestRuleCategory:
    """RuleCategory(Enum)のテストクラス"""

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-RULE_CATEGORY_VALUES")
    def test_rule_category_values(self) -> None:
        """ルールカテゴリー値テスト"""
        assert RuleCategory.BASIC_STYLE.value == "基本文体"
        assert RuleCategory.COMPOSITION.value == "構成"
        assert RuleCategory.PROPER_NOUN.value == "固有名詞"
        assert RuleCategory.READABILITY.value == "読みやすさ"
        assert RuleCategory.CONSISTENCY.value == "一貫性"

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-RULE_CATEGORY_ENUM_C")
    def test_rule_category_enum_count(self) -> None:
        """ルールカテゴリー数テスト"""
        assert len(RuleCategory) == 5

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-RULE_CATEGORY_MEMBER")
    def test_rule_category_membership(self) -> None:
        """ルールカテゴリーメンバーシップテスト"""
        assert RuleCategory.BASIC_STYLE in RuleCategory
        assert RuleCategory.COMPOSITION in RuleCategory
        assert RuleCategory.PROPER_NOUN in RuleCategory
        assert RuleCategory.READABILITY in RuleCategory
        assert RuleCategory.CONSISTENCY in RuleCategory


class TestLineNumber:
    """LineNumber値オブジェクトのテストクラス"""

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-LINE_NUMBER_CREATION")
    def test_line_number_creation_valid(self) -> None:
        """有効な行番号での作成テスト"""
        line_num = LineNumber(1)
        assert line_num.value == 1

        line_num = LineNumber(100)
        assert line_num.value == 100

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-LINE_NUMBER_CREATION")
    def test_line_number_creation_zero_error(self) -> None:
        """0行番号エラーテスト"""
        with pytest.raises(DomainException, match="行番号は1以上である必要があります"):
            LineNumber(0)

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-LINE_NUMBER_CREATION")
    def test_line_number_creation_negative_error(self) -> None:
        """負の行番号エラーテスト"""
        with pytest.raises(DomainException, match="行番号は1以上である必要があります"):
            LineNumber(-1)

        with pytest.raises(DomainException, match="行番号は1以上である必要があります"):
            LineNumber(-100)

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-LINE_NUMBER_FORMAT")
    def test_line_number_format(self) -> None:
        """行番号フォーマットテスト"""
        line_num = LineNumber(5)
        assert line_num.format() == "5行目"

        line_num = LineNumber(123)
        assert line_num.format() == "123行目"

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-LINE_NUMBER_STR")
    def test_line_number_str(self) -> None:
        """行番号文字列表現テスト"""
        line_num = LineNumber(10)
        assert str(line_num) == "10行目"

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-LINE_NUMBER_IS_FROZE")
    def test_line_number_is_frozen(self) -> None:
        """行番号オブジェクトの不変性テスト"""
        line_num = LineNumber(1)
        with pytest.raises(AttributeError, match=".*"):
            line_num.value = 2  # type: ignore


class TestErrorContext:
    """ErrorContext値オブジェクトのテストクラス"""

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-ERROR_CONTEXT_CREATI")
    def test_error_context_creation_valid(self) -> None:
        """有効なエラーコンテキスト作成テスト"""
        context = ErrorContext("テストテキスト")
        assert context.text == "テストテキスト"
        assert context.start_pos is None
        assert context.end_pos is None

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-ERROR_CONTEXT_CREATI")
    def test_error_context_creation_with_positions(self) -> None:
        """位置情報付きエラーコンテキスト作成テスト"""
        context = ErrorContext("テストテキスト", 2, 4)
        assert context.text == "テストテキスト"
        assert context.start_pos == 2
        assert context.end_pos == 4

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-ERROR_CONTEXT_CREATI")
    def test_error_context_creation_empty_text_error(self) -> None:
        """空テキストエラーテスト"""
        with pytest.raises(DomainException, match="コンテキストテキストは必須です"):
            ErrorContext("")

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-ERROR_CONTEXT_GET_HI")
    def test_error_context_get_highlighted_text_no_positions(self) -> None:
        """位置情報なしハイライトテキスト取得テスト"""
        context = ErrorContext("テストテキスト")
        assert context.get_highlighted_text() == "テストテキスト"

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-ERROR_CONTEXT_GET_HI")
    def test_error_context_get_highlighted_text_with_positions(self) -> None:
        """位置情報ありハイライトテキスト取得テスト"""
        context = ErrorContext("これはテストです", 2, 5)
        assert context.get_highlighted_text() == "これ【はテス】トです"

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-ERROR_CONTEXT_GET_HI")
    def test_error_context_get_highlighted_text_beginning(self) -> None:
        """開始位置からのハイライトテキスト取得テスト"""
        context = ErrorContext("テストテキスト", 0, 3)
        assert context.get_highlighted_text() == "【テスト】テキスト"

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-ERROR_CONTEXT_GET_HI")
    def test_error_context_get_highlighted_text_end(self) -> None:
        """終了位置までのハイライトテキスト取得テスト"""
        context = ErrorContext("テストテキスト", 3, 6)
        assert context.get_highlighted_text() == "テスト【テキス】ト"

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-ERROR_CONTEXT_GET_HI")
    def test_error_context_get_highlighted_text_whole_text(self) -> None:
        """全体ハイライトテキスト取得テスト"""
        context = ErrorContext("テスト", 0, 3)
        assert context.get_highlighted_text() == "【テスト】"

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-ERROR_CONTEXT_IS_FRO")
    def test_error_context_is_frozen(self) -> None:
        """エラーコンテキストオブジェクトの不変性テスト"""
        context = ErrorContext("テスト")
        with pytest.raises(AttributeError, match=".*"):
            context.text = "変更後"  # type: ignore


class TestQualityScore:
    """QualityScore値オブジェクトのテストクラス"""

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-QUALITY_SCORE_CREATI")
    def test_quality_score_creation_valid(self) -> None:
        """有効な品質スコア作成テスト"""
        score = QualityScore(85.5)
        assert score.value == 85.5

        score = QualityScore(0.0)
        assert score.value == 0.0

        score = QualityScore(100.0)
        assert score.value == 100.0

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-QUALITY_SCORE_CREATI")
    def test_quality_score_creation_below_min_error(self) -> None:
        """最小値未満エラーテスト"""
        with pytest.raises(DomainException, match="品質スコアは0から100の範囲である必要があります"):
            QualityScore(-0.1)

        with pytest.raises(DomainException, match="品質スコアは0から100の範囲である必要があります"):
            QualityScore(-50.0)

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-QUALITY_SCORE_CREATI")
    def test_quality_score_creation_above_max_error(self) -> None:
        """最大値超過エラーテスト"""
        with pytest.raises(DomainException, match="品質スコアは0から100の範囲である必要があります"):
            QualityScore(100.1)

        with pytest.raises(DomainException, match="品質スコアは0から100の範囲である必要があります"):
            QualityScore(150.0)

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-QUALITY_SCORE_FORMAT")
    def test_quality_score_format(self) -> None:
        """品質スコアフォーマットテスト"""
        score = QualityScore(75.0)
        assert score.format() == "75.0点"

        score = QualityScore(90.5)
        assert score.format() == "90.5点"

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-QUALITY_SCORE_STR")
    def test_quality_score_str(self) -> None:
        """品質スコア文字列表現テスト"""
        score = QualityScore(80.0)
        assert str(score) == "80.0点"

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-QUALITY_SCORE_COMPAR")
    def test_quality_score_comparison_lt(self) -> None:
        """品質スコア比較(未満)テスト"""
        score1 = QualityScore(70.0)
        score2 = QualityScore(80.0)

        assert score1 < score2
        assert not (score2 < score1)
        assert not (score1 < score1)

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-QUALITY_SCORE_COMPAR")
    def test_quality_score_comparison_le(self) -> None:
        """品質スコア比較(以下)テスト"""
        score1 = QualityScore(70.0)
        score2 = QualityScore(80.0)
        score3 = QualityScore(70.0)

        assert score1 <= score2
        assert score1 <= score3
        assert not (score2 <= score1)

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-QUALITY_SCORE_COMPAR")
    def test_quality_score_comparison_gt(self) -> None:
        """品質スコア比較(超過)テスト"""
        score1 = QualityScore(80.0)
        score2 = QualityScore(70.0)

        assert score1 > score2
        assert not (score2 > score1)
        assert not (score1 > score1)

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-QUALITY_SCORE_COMPAR")
    def test_quality_score_comparison_ge(self) -> None:
        """品質スコア比較(以上)テスト"""
        score1 = QualityScore(80.0)
        score2 = QualityScore(70.0)
        score3 = QualityScore(80.0)

        assert score1 >= score2
        assert score1 >= score3
        assert not (score2 >= score1)

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-QUALITY_SCORE_COMPAR")
    def test_quality_score_comparison_with_non_score(self) -> None:
        """非QualityScoreとの比較テスト"""
        score = QualityScore(80)

        # TypeErrorが発生することを確認
        with pytest.raises(TypeError):
            score < 90
        with pytest.raises(TypeError):
            score <= "80"
        with pytest.raises(TypeError):
            score > 70.0
        with pytest.raises(TypeError):
            score >= None

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-QUALITY_SCORE_GET_GR")
    def test_quality_score_get_grade(self) -> None:
        """品質スコアグレード取得テスト"""
        assert QualityScore(95.0).get_grade() == "A"
        assert QualityScore(90.0).get_grade() == "A"
        assert QualityScore(85.0).get_grade() == "B"
        assert QualityScore(80.0).get_grade() == "B"
        assert QualityScore(75.0).get_grade() == "C"
        assert QualityScore(70.0).get_grade() == "C"
        assert QualityScore(65.0).get_grade() == "D"
        assert QualityScore(60.0).get_grade() == "D"
        assert QualityScore(55.0).get_grade() == "F"
        assert QualityScore(0.0).get_grade() == "F"

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-QUALITY_SCORE_IS_ACC")
    def test_quality_score_is_acceptable_default_threshold(self) -> None:
        """品質スコア許容性(デフォルト閾値)テスト"""
        assert QualityScore(80.0).is_acceptable() is True
        assert QualityScore(70.0).is_acceptable() is True
        assert QualityScore(69.9).is_acceptable() is False
        assert QualityScore(50.0).is_acceptable() is False

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-QUALITY_SCORE_IS_ACC")
    def test_quality_score_is_acceptable_custom_threshold(self) -> None:
        """品質スコア許容性(カスタム閾値)テスト"""
        assert QualityScore(90.0).is_acceptable(85.0) is True
        assert QualityScore(85.0).is_acceptable(85.0) is True
        assert QualityScore(84.9).is_acceptable(85.0) is False

        assert QualityScore(60.0).is_acceptable(50.0) is True
        assert QualityScore(50.0).is_acceptable(50.0) is True
        assert QualityScore(49.9).is_acceptable(50.0) is False

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-QUALITY_SCORE_CONSTA")
    def test_quality_score_constants(self) -> None:
        """品質スコア定数テスト"""
        assert QualityScore.MIN_SCORE == 0.0
        assert QualityScore.MAX_SCORE == 100.0

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-QUALITY_SCORE_IS_FRO")
    def test_quality_score_is_frozen(self) -> None:
        """品質スコアオブジェクトの不変性テスト"""
        score = QualityScore(80.0)
        with pytest.raises(AttributeError, match=".*"):
            score.value = 90.0  # type: ignore


class TestAdaptationStrength:
    """AdaptationStrength(Enum)のテストクラス"""

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-ADAPTATION_STRENGTH_")
    def test_adaptation_strength_values(self) -> None:
        """適応強度値テスト"""
        assert AdaptationStrength.WEAK.value == "weak"
        assert AdaptationStrength.MODERATE.value == "moderate"
        assert AdaptationStrength.STRONG.value == "strong"

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-ADAPTATION_STRENGTH_")
    def test_adaptation_strength_enum_count(self) -> None:
        """適応強度数テスト"""
        assert len(AdaptationStrength) == 3

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-ADAPTATION_STRENGTH_")
    def test_adaptation_strength_membership(self) -> None:
        """適応強度メンバーシップテスト"""
        assert AdaptationStrength.WEAK in AdaptationStrength
        assert AdaptationStrength.MODERATE in AdaptationStrength
        assert AdaptationStrength.STRONG in AdaptationStrength


class TestEvaluationContext:
    """EvaluationContext値オブジェクトのテストクラス"""

    @pytest.fixture
    def valid_context(self) -> EvaluationContext:
        """有効な評価コンテキスト"""
        return EvaluationContext(episode_number=5, chapter_number=2, genre="fantasy", viewpoint_type="first_person")

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-EVALUATION_CONTEXT_C")
    def test_evaluation_context_creation_valid(self, valid_context: EvaluationContext) -> None:
        """有効な評価コンテキスト作成テスト"""
        assert valid_context.episode_number == 5
        assert valid_context.chapter_number == 2
        assert valid_context.genre == "fantasy"
        assert valid_context.viewpoint_type == "first_person"

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-EVALUATION_CONTEXT_E")
    def test_evaluation_context_episode_number_zero_error(self) -> None:
        """エピソード番号0エラーテスト"""
        with pytest.raises(DomainException, match="エピソード番号は1以上である必要があります"):
            EvaluationContext(episode_number=0, chapter_number=1, genre="fantasy", viewpoint_type="first_person")

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-EVALUATION_CONTEXT_E")
    def test_evaluation_context_episode_number_negative_error(self) -> None:
        """エピソード番号負数エラーテスト"""
        with pytest.raises(DomainException, match="エピソード番号は1以上である必要があります"):
            EvaluationContext(episode_number=-1, chapter_number=1, genre="fantasy", viewpoint_type="first_person")

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-EVALUATION_CONTEXT_C")
    def test_evaluation_context_chapter_number_zero_error(self) -> None:
        """章番号0エラーテスト"""
        with pytest.raises(DomainException, match="章番号は1以上である必要があります"):
            EvaluationContext(episode_number=1, chapter_number=0, genre="fantasy", viewpoint_type="first_person")

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-EVALUATION_CONTEXT_C")
    def test_evaluation_context_chapter_number_negative_error(self) -> None:
        """章番号負数エラーテスト"""
        with pytest.raises(DomainException, match="章番号は1以上である必要があります"):
            EvaluationContext(episode_number=1, chapter_number=-1, genre="fantasy", viewpoint_type="first_person")

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-EVALUATION_CONTEXT_E")
    def test_evaluation_context_empty_genre_error(self) -> None:
        """空ジャンルエラーテスト"""
        with pytest.raises(DomainException, match="ジャンルは必須です"):
            EvaluationContext(episode_number=1, chapter_number=1, genre="", viewpoint_type="first_person")

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-EVALUATION_CONTEXT_E")
    def test_evaluation_context_empty_viewpoint_type_error(self) -> None:
        """空視点タイプエラーテスト"""
        with pytest.raises(DomainException, match="視点タイプは必須です"):
            EvaluationContext(episode_number=1, chapter_number=1, genre="fantasy", viewpoint_type="")

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-EVALUATION_CONTEXT_I")
    def test_evaluation_context_is_complex_viewpoint_true(self) -> None:
        """複雑な視点判定(True)テスト"""
        context_multiple = EvaluationContext(
            episode_number=1, chapter_number=1, genre="fantasy", viewpoint_type="multiple_perspective"
        )

        assert context_multiple.is_complex_viewpoint() is True

        context_complex = EvaluationContext(
            episode_number=1, chapter_number=1, genre="fantasy", viewpoint_type="complex_narrative"
        )

        assert context_complex.is_complex_viewpoint() is True

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-EVALUATION_CONTEXT_I")
    def test_evaluation_context_is_complex_viewpoint_false(self) -> None:
        """複雑な視点判定(False)テスト"""
        context = EvaluationContext(episode_number=1, chapter_number=1, genre="fantasy", viewpoint_type="first_person")
        assert context.is_complex_viewpoint() is False

        context_simple = EvaluationContext(
            episode_number=1, chapter_number=1, genre="fantasy", viewpoint_type="third_person"
        )

        assert context_simple.is_complex_viewpoint() is False

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-EVALUATION_CONTEXT_I")
    def test_evaluation_context_is_introspective_type_true(self) -> None:
        """内省的タイプ判定(True)テスト"""
        context = EvaluationContext(
            episode_number=1, chapter_number=1, genre="literary", viewpoint_type="introspective_first_person"
        )

        assert context.is_introspective_type() is True

        context_deep = EvaluationContext(
            episode_number=1, chapter_number=1, genre="literary", viewpoint_type="deep_introspective"
        )

        assert context_deep.is_introspective_type() is True

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-EVALUATION_CONTEXT_I")
    def test_evaluation_context_is_introspective_type_false(self) -> None:
        """内省的タイプ判定(False)テスト"""
        context = EvaluationContext(episode_number=1, chapter_number=1, genre="fantasy", viewpoint_type="first_person")
        assert context.is_introspective_type() is False

        context_action = EvaluationContext(
            episode_number=1, chapter_number=1, genre="action", viewpoint_type="third_person_limited"
        )

        assert context_action.is_introspective_type() is False

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-EVALUATION_CONTEXT_B")
    def test_evaluation_context_boundary_values(self) -> None:
        """評価コンテキスト境界値テスト"""
        # 最小値(1)
        context_min = EvaluationContext(episode_number=1, chapter_number=1, genre="g", viewpoint_type="v")
        assert context_min.episode_number == 1
        assert context_min.chapter_number == 1

        # 大きな値
        context_large = EvaluationContext(
            episode_number=9999, chapter_number=999, genre="fantasy", viewpoint_type="first_person"
        )

        assert context_large.episode_number == 9999
        assert context_large.chapter_number == 999

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-EVALUATION_CONTEXT_I")
    def test_evaluation_context_is_frozen(self) -> None:
        """評価コンテキストオブジェクトの不変性テスト"""
        context = EvaluationContext(episode_number=1, chapter_number=1, genre="fantasy", viewpoint_type="first_person")

        with pytest.raises(AttributeError, match=".*"):
            context.episode_number = 2  # type: ignore

        with pytest.raises(AttributeError, match=".*"):
            context.genre = "romance"  # type: ignore

    @pytest.mark.spec("SPEC-QUALITY_VALUE_OBJECTS-EVALUATION_CONTEXT_C")
    def test_evaluation_context_complex_combinations(self) -> None:
        """評価コンテキスト複雑な組み合わせテスト"""
        test_cases = [
            ("multiple_complex_introspective", True, True),
            ("complex_introspective", True, True),
            ("multiple_first_person", True, False),
            ("simple_introspective", False, True),
            ("first_person", False, False),
        ]

        for viewpoint_type, expected_complex, expected_introspective in test_cases:
            context = EvaluationContext(
                episode_number=1, chapter_number=1, genre="fantasy", viewpoint_type=viewpoint_type
            )

            assert context.is_complex_viewpoint() == expected_complex
            assert context.is_introspective_type() == expected_introspective
