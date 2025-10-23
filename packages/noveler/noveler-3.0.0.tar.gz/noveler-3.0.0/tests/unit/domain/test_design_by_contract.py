#!/usr/bin/env python3
"""Design by Contract テスト

バリデーションとビジネスルールの動作確認


仕様書: SPEC-UNIT-TEST
"""

import pytest

from noveler.domain.exceptions import DomainException
from noveler.domain.value_objects.quality_score import QualityScore
from noveler.domain.writing.value_objects.episode_number import EpisodeNumber
from noveler.domain.writing.value_objects.word_count import WordCount


class TestDesignByContract:
    """Design by Contract機能のテストスイート"""

    @pytest.mark.spec("SPEC-DESIGN_BY_CONTRACT-WORD_COUNT_PRECONDIT")
    def test_word_count_precondition_violation(self) -> None:
        """WordCountの事前条件違反テスト"""
        # 負の値は事前条件違反
        with pytest.raises(DomainException, match=".*"):
            WordCount(-1)

        # 上限超過も事前条件違反
        with pytest.raises(DomainException, match=".*"):
            WordCount(2000000)

    @pytest.mark.spec("SPEC-DESIGN_BY_CONTRACT-WORD_COUNT_ADDITION_")
    def test_word_count_addition_postcondition(self) -> None:
        """WordCountの加算後条件テスト"""
        wc1 = WordCount(1000)
        wc2 = WordCount(500)
        result = wc1 + wc2

        # 事後条件: 結果の値は期待値と一致
        assert result.value == 1500

        # 事後条件: 結果は有効範囲内
        assert 0 <= result.value <= 1000000

    @pytest.mark.spec("SPEC-DESIGN_BY_CONTRACT-WORD_COUNT_SUBTRACTI")
    def test_word_count_subtraction_precondition(self) -> None:
        """WordCountの減算事前条件テスト"""
        wc1 = WordCount(500)
        wc2 = WordCount(1000)

        # 事前条件違反: 減算結果が負になる
        with pytest.raises(DomainException, match=".*"):
            wc1 - wc2

    @pytest.mark.spec("SPEC-DESIGN_BY_CONTRACT-QUALITY_SCORE_PRECON")
    def test_quality_score_precondition_violation(self) -> None:
        """QualityScoreの事前条件違反テスト"""
        # 負の値は事前条件違反
        with pytest.raises(DomainException, match=".*"):
            QualityScore(-1)

        # 上限超過も事前条件違反
        with pytest.raises(DomainException, match=".*"):
            QualityScore(101)

    @pytest.mark.spec("SPEC-DESIGN_BY_CONTRACT-QUALITY_SCORE_GRADE_")
    def test_quality_score_grade_postcondition(self) -> None:
        """QualityScoreのグレード後条件テスト"""
        score = QualityScore(85)
        grade = score.get_grade()

        # 事後条件: グレードは有効な値のみ
        assert grade in ["S", "A", "B", "C", "D"]
        assert grade == "A"

    @pytest.mark.spec("SPEC-DESIGN_BY_CONTRACT-QUALITY_SCORE_IS_PAS")
    def test_quality_score_is_passing_precondition(self) -> None:
        """QualityScoreのis_passing事前条件テスト"""
        score = QualityScore(75)

        # 有効な閾値では動作
        assert score.is_passing(70)

        # 無効な閾値では事前条件違反
        with pytest.raises(DomainException, match=".*"):
            score.is_passing(-1)

        with pytest.raises(DomainException, match=".*"):
            score.is_passing(101)

    @pytest.mark.spec("SPEC-DESIGN_BY_CONTRACT-EPISODE_NUMBER_PRECO")
    def test_episode_number_precondition_violation(self) -> None:
        """EpisodeNumberの事前条件違反テスト"""
        # 0以下は事前条件違反
        with pytest.raises(DomainException, match=".*"):
            EpisodeNumber(0)

        # 上限超過も事前条件違反
        with pytest.raises(DomainException, match=".*"):
            EpisodeNumber(10000)

    @pytest.mark.spec("SPEC-DESIGN_BY_CONTRACT-EPISODE_NUMBER_NEXT_")
    def test_episode_number_next_precondition(self) -> None:
        """EpisodeNumberのnext事前条件テスト"""
        # 上限値では次の値を生成できない
        max_episode = EpisodeNumber(9999)

        with pytest.raises(DomainException, match=".*"):
            max_episode.next()

    @pytest.mark.spec("SPEC-DESIGN_BY_CONTRACT-EPISODE_NUMBER_NEXT_")
    def test_episode_number_next_postcondition(self) -> None:
        """EpisodeNumberのnext後条件テスト"""
        episode = EpisodeNumber(5)
        next_episode = episode.next()

        # 事後条件: 次の値は現在値+1
        assert next_episode.value == 6

        # 事後条件: 結果は有効範囲内
        assert 1 <= next_episode.value <= 9999

    @pytest.mark.spec("SPEC-DESIGN_BY_CONTRACT-EPISODE_NUMBER_PREVI")
    def test_episode_number_previous_postcondition(self) -> None:
        """EpisodeNumberのprevious後条件テスト"""
        episode = EpisodeNumber(5)
        prev_episode = episode.previous()

        # 事後条件: 前の値は現在値-1
        assert prev_episode is not None
        assert prev_episode.value == 4

        # 事後条件: 結果は有効範囲内
        assert 1 <= prev_episode.value <= 9999

    @pytest.mark.spec("SPEC-DESIGN_BY_CONTRACT-EPISODE_NUMBER_PREVI")
    def test_episode_number_previous_at_minimum(self) -> None:
        """EpisodeNumberの最小値でのprevious後条件テスト"""
        episode = EpisodeNumber(1)
        prev_episode = episode.previous()

        # 事後条件: 最小値では前の値はNone
        assert prev_episode is None

    @pytest.mark.spec("SPEC-DESIGN_BY_CONTRACT-CONTRACT_ERROR_VS_DO")
    def test_contract_error_vs_domain_exception(self) -> None:
        """DomainExceptionのバリデーションテスト"""
        # DomainExceptionは実行時にバリデーションで発生
        with pytest.raises(DomainException, match=".*"):
            WordCount(-1)

        # DomainExceptionは__post_init__内で発生
        # バリデーション違反時の適切なエラーハンドリング

    @pytest.mark.spec("SPEC-DESIGN_BY_CONTRACT-MULTIPLE_PRECONDITIO")
    def test_multiple_preconditions(self) -> None:
        """複数の事前条件の動作確認"""
        # WordCountは型チェックと範囲チェックの両方を持つ
        with pytest.raises(DomainException, match=".*"):
            WordCount(-1)  # 範囲チェック失敗

        # QualityScoreも同様
        with pytest.raises(DomainException, match=".*"):
            QualityScore(101)  # 範囲チェック失敗

    @pytest.mark.spec("SPEC-DESIGN_BY_CONTRACT-POSTCONDITION_VERIFI")
    def test_postcondition_verification(self) -> None:
        """事後条件の検証テスト"""
        # 加算の事後条件: 結果が期待値と一致
        wc1 = WordCount(100)
        wc2 = WordCount(50)
        result = wc1 + wc2

        # 事後条件により自動的に検証される
        assert result.value == 150

        # 次の話数の事後条件: 値が+1になる
        episode = EpisodeNumber(10)
        next_episode = episode.next()
        assert next_episode.value == 11
