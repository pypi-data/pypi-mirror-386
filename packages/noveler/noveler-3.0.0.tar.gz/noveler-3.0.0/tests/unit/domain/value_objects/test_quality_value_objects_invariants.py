"""品質管理ドメインの値オブジェクトの不変条件テスト
TDD: RED Phase - 失敗するテストから開始


仕様書: SPEC-DOMAIN-VALUE-OBJECTS
"""

import pytest

from noveler.domain.exceptions import DomainException
from noveler.domain.quality.value_objects import (
    ErrorContext,
    EvaluationContext,
    LineNumber,
    QualityScore,
)


class TestLineNumberInvariants:
    """LineNumber値オブジェクトの不変条件テスト"""

    def test_valid_line_number_creation(self) -> None:
        """有効な行番号でLineNumberを作成できる"""
        line = LineNumber(10)
        assert line.value == 10
        assert str(line) == "10行目"

    def test_line_number_minimum_is_one(self) -> None:
        """行番号1は有効(最小値)"""
        line = LineNumber(1)
        assert line.value == 1

    def test_zero_line_number_raises_error(self) -> None:
        """行番号0はエラーになる"""
        with pytest.raises(DomainException, match="行番号は1以上である必要があります"):
            LineNumber(0)

    def test_negative_line_number_raises_error(self) -> None:
        """負の行番号はエラーになる"""
        with pytest.raises(DomainException, match="行番号は1以上である必要があります"):
            LineNumber(-5)

    def test_line_number_immutability(self) -> None:
        """LineNumberは不変である"""
        line = LineNumber(10)
        with pytest.raises(AttributeError, match=".*"):
            line.value = 20

    def test_large_line_number_is_valid(self) -> None:
        """大きな行番号も有効(実用的な上限なし)"""
        line = LineNumber(100000)
        assert line.value == 100000
        assert str(line) == "100000行目"

    def test_line_number_format_method(self) -> None:
        """format()メソッドのテスト"""
        line = LineNumber(42)
        assert line.format() == "42行目"


class TestQualityScoreInvariants:
    """QualityScore値オブジェクトの不変条件テスト"""

    def test_valid_quality_score_creation(self) -> None:
        """有効なスコアでQualityScoreを作成できる"""
        score = QualityScore(85.5)
        assert score.value == 85.5

    def test_quality_score_zero_is_valid(self) -> None:
        """スコア0は有効(最低値)"""
        score = QualityScore(0.0)
        assert score.value == 0.0

    def test_quality_score_hundred_is_valid(self) -> None:
        """スコア100は有効(最高値)"""
        score = QualityScore(100.0)
        assert score.value == 100.0

    def test_negative_quality_score_raises_error(self) -> None:
        """負のスコアはエラーになる"""
        with pytest.raises(DomainException, match="品質スコアは0から100の範囲である必要があります"):
            QualityScore(-1.0)

    def test_over_hundred_quality_score_raises_error(self) -> None:
        """100を超えるスコアはエラーになる"""
        with pytest.raises(DomainException, match="品質スコアは0から100の範囲である必要があります"):
            QualityScore(100.1)

    def test_quality_score_immutability(self) -> None:
        """QualityScoreは不変である"""
        score = QualityScore(75.0)
        with pytest.raises(AttributeError, match=".*"):
            score.value = 80.0

    def test_quality_score_get_grade(self) -> None:
        """グレード変換が正しく動作する"""
        test_cases = [
            (95.0, "A"),  # 90以上
            (85.0, "B"),  # 80-89
            (75.0, "C"),  # 70-79
            (65.0, "D"),  # 60-69
            (55.0, "F"),  # 60未満
            (90.0, "A"),  # 境界値
            (80.0, "B"),  # 境界値
            (70.0, "C"),  # 境界値
            (60.0, "D"),  # 境界値
        ]
        for value, expected_grade in test_cases:
            score = QualityScore(value)
            assert score.get_grade() == expected_grade

    def test_quality_score_is_acceptable(self) -> None:
        """許容可能判定が正しく動作する"""
        # デフォルト閾値(70.0)
        score_high = QualityScore(75.0)
        score_low = QualityScore(65.0)
        assert score_high.is_acceptable()
        assert not score_low.is_acceptable()

        # カスタム閾値
        assert score_low.is_acceptable(threshold=60.0)
        assert not score_low.is_acceptable(threshold=80.0)

    def test_quality_score_format_method(self) -> None:
        """format()メソッドのテスト"""
        score = QualityScore(85.5)
        assert score.format() == "85.5点"

    def test_quality_score_equality(self) -> None:
        """スコアの等価性"""
        score1 = QualityScore(85.5)
        score2 = QualityScore(85.5)
        score3 = QualityScore(90.0)

        assert score1 == score2
        assert score1 != score3

    def test_quality_score_comparison(self) -> None:
        """スコアの比較演算"""
        score1 = QualityScore(70.0)
        score2 = QualityScore(80.0)

        assert score1 < score2
        assert score2 > score1
        assert score1 <= score2
        assert score2 >= score1


class TestErrorContextInvariants:
    """ErrorContext値オブジェクトの不変条件テスト"""

    def test_valid_error_context_creation(self) -> None:
        """有効なエラーコンテキストを作成できる"""
        context = ErrorContext("エラーを含むテキスト", start_pos=5, end_pos=8)
        assert context.text == "エラーを含むテキスト"
        assert context.start_pos == 5
        assert context.end_pos == 8

    def test_error_context_without_position(self) -> None:
        """位置情報なしでもコンテキスト作成可能"""
        context = ErrorContext("エラーテキスト")
        assert context.text == "エラーテキスト"
        assert context.start_pos is None
        assert context.end_pos is None

    def test_empty_context_text_raises_error(self) -> None:
        """空のコンテキストテキストはエラーになる"""
        with pytest.raises(DomainException, match="コンテキストテキストは必須です"):
            ErrorContext("")

    def test_error_context_highlighted_text(self) -> None:
        """ハイライト表示が正しく動作する"""
        context = ErrorContext("これはエラーを含むテキストです", start_pos=3, end_pos=6)
        assert context.get_highlighted_text() == "これは【エラー】を含むテキストです"

        # 位置情報なしの場合
        context_no_pos = ErrorContext("エラーテキスト")
        assert context_no_pos.get_highlighted_text() == "エラーテキスト"

    def test_error_context_immutability(self) -> None:
        """ErrorContextは不変である"""
        context = ErrorContext("テキスト", start_pos=0, end_pos=3)
        with pytest.raises(AttributeError, match=".*"):
            context.text = "変更"
        with pytest.raises(AttributeError, match=".*"):
            context.start_pos = 10


class TestEvaluationContextInvariants:
    """EvaluationContext値オブジェクトの不変条件テスト"""

    def test_valid_evaluation_context_creation(self) -> None:
        """有効な評価コンテキストを作成できる"""
        context = EvaluationContext(
            episode_number=5,
            chapter_number=2,
            genre="ファンタジー",
            viewpoint_type="単一視点",
        )

        assert context.episode_number == 5
        assert context.chapter_number == 2
        assert context.genre == "ファンタジー"
        assert context.viewpoint_type == "単一視点"

    def test_invalid_episode_number_raises_error(self) -> None:
        """無効なエピソード番号はエラーになる"""
        with pytest.raises(DomainException, match="エピソード番号は1以上である必要があります"):
            EvaluationContext(
                episode_number=0,
                chapter_number=1,
                genre="ファンタジー",
                viewpoint_type="単一視点",
            )

    def test_invalid_chapter_number_raises_error(self) -> None:
        """無効な章番号はエラーになる"""
        with pytest.raises(DomainException, match="章番号は1以上である必要があります"):
            EvaluationContext(
                episode_number=1,
                chapter_number=0,
                genre="ファンタジー",
                viewpoint_type="単一視点",
            )

    def test_empty_genre_raises_error(self) -> None:
        """空のジャンルはエラーになる"""
        with pytest.raises(DomainException, match="ジャンルは必須です"):
            EvaluationContext(
                episode_number=1,
                chapter_number=1,
                genre="",
                viewpoint_type="単一視点",
            )

    def test_empty_viewpoint_type_raises_error(self) -> None:
        """空の視点タイプはエラーになる"""
        with pytest.raises(DomainException, match="視点タイプは必須です"):
            EvaluationContext(
                episode_number=1,
                chapter_number=1,
                genre="ファンタジー",
                viewpoint_type="",
            )

    def test_is_complex_viewpoint(self) -> None:
        """複雑な視点の判定が正しく動作する"""
        simple = EvaluationContext(1, 1, "ファンタジー", "単一視点")
        complex_multi = EvaluationContext(1, 1, "ファンタジー", "multiple_perspective")
        complex_type = EvaluationContext(1, 1, "ファンタジー", "complex_narrative")

        assert not simple.is_complex_viewpoint()
        assert complex_multi.is_complex_viewpoint()
        assert complex_type.is_complex_viewpoint()

    def test_is_introspective_type(self) -> None:
        """内省的タイプの判定が正しく動作する"""
        normal = EvaluationContext(1, 1, "ファンタジー", "交流型")
        introspective = EvaluationContext(1, 1, "ファンタジー", "introspective_monologue")

        assert not normal.is_introspective_type()
        assert introspective.is_introspective_type()

    def test_evaluation_context_immutability(self) -> None:
        """EvaluationContextは不変である"""
        context = EvaluationContext(1, 1, "ファンタジー", "単一視点")
        with pytest.raises(AttributeError, match=".*"):
            context.episode_number = 2
