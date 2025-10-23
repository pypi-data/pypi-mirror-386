#!/usr/bin/env python3
"""ReaderBehavior値オブジェクトのユニットテスト

SPEC-ANALYSIS-001に基づくTDD実装
"""

import pytest

from noveler.domain.value_objects.reader_behavior import ReaderBehavior
from noveler.domain.value_objects.reader_segment import ReaderSegment

pytestmark = pytest.mark.vo_smoke



class TestReaderBehavior:
    """ReaderBehavior値オブジェクトのテストクラス"""

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_create_valid_reader_behavior(self) -> None:
        """正常なReaderBehaviorの作成テスト"""
        # Given: 正常な読者行動データ
        reader_segment = ReaderSegment.NEW
        engagement_score = 0.8
        retention_rate = 0.9
        dropout_probability = 0.1

        # When: ReaderBehaviorを作成
        behavior = ReaderBehavior(
            reader_segment=reader_segment,
            engagement_score=engagement_score,
            retention_rate=retention_rate,
            dropout_probability=dropout_probability,
        )

        # Then: 正しく作成される
        assert behavior.reader_segment == reader_segment
        assert behavior.engagement_score == engagement_score
        assert behavior.retention_rate == retention_rate
        assert behavior.dropout_probability == dropout_probability

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_is_high_risk_true_case(self) -> None:
        """高リスク判定テスト(True)"""
        # Given: 高離脱確率のReaderBehavior
        behavior = ReaderBehavior(
            reader_segment=ReaderSegment.AT_RISK,
            engagement_score=0.3,
            retention_rate=0.4,
            dropout_probability=0.8,  # 80%の離脱確率
        )

        # When: 高リスク判定
        result = behavior.is_high_risk()

        # Then: Trueが返される
        assert result is True

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_is_high_risk_false_case(self) -> None:
        """高リスク判定テスト(False)"""
        # Given: 低離脱確率のReaderBehavior
        behavior = ReaderBehavior(
            reader_segment=ReaderSegment.NEW,
            engagement_score=0.8,
            retention_rate=0.9,
            dropout_probability=0.1,  # 10%の離脱確率
        )

        # When: 高リスク判定
        result = behavior.is_high_risk()

        # Then: Falseが返される
        assert result is False

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_is_high_risk_boundary_case(self) -> None:
        """高リスク判定テスト(境界値)"""
        # Given: 境界値(50%)のReaderBehavior
        behavior = ReaderBehavior(
            reader_segment=ReaderSegment.REGULAR,
            engagement_score=0.5,
            retention_rate=0.5,
            dropout_probability=0.5,  # 50%の離脱確率
        )

        # When: 高リスク判定
        result = behavior.is_high_risk()

        # Then: Falseが返される(50%は高リスクではない)
        assert result is False

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_calculate_lifetime_value_high_engagement(self) -> None:
        """生涯価値計算テスト(高エンゲージメント)"""
        # Given: 高エンゲージメント・高継続率のReaderBehavior
        behavior = ReaderBehavior(
            reader_segment=ReaderSegment.REGULAR, engagement_score=0.9, retention_rate=0.8, dropout_probability=0.2
        )

        # When: 生涯価値を計算
        result = behavior.calculate_lifetime_value()

        # Then: 高い生涯価値が返される
        # engagement_score * retention_rate * (1 - dropout_probability)
        # = 0.9 * 0.8 * 0.8 = 0.576
        assert abs(result - 0.576) < 1e-10

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_calculate_lifetime_value_low_engagement(self) -> None:
        """生涯価値計算テスト(低エンゲージメント)"""
        # Given: 低エンゲージメント・低継続率のReaderBehavior
        behavior = ReaderBehavior(
            reader_segment=ReaderSegment.AT_RISK, engagement_score=0.2, retention_rate=0.3, dropout_probability=0.8
        )

        # When: 生涯価値を計算
        result = behavior.calculate_lifetime_value()

        # Then: 低い生涯価値が返される
        # engagement_score * retention_rate * (1 - dropout_probability)
        # = 0.2 * 0.3 * 0.2 = 0.012
        assert abs(result - 0.012) < 1e-10

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_reader_behavior_immutability(self) -> None:
        """ReaderBehaviorの不変性テスト"""
        # Given: ReaderBehavior
        behavior = ReaderBehavior(
            reader_segment=ReaderSegment.NEW, engagement_score=0.8, retention_rate=0.9, dropout_probability=0.1
        )

        # When/Then: 属性変更を試行するとエラーが発生
        with pytest.raises(AttributeError, match=".*"):
            behavior.engagement_score = 0.5

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_reader_behavior_equality(self) -> None:
        """ReaderBehaviorの等価性テスト"""
        # Given: 同じ値を持つ2つのReaderBehavior
        behavior1 = ReaderBehavior(
            reader_segment=ReaderSegment.NEW, engagement_score=0.8, retention_rate=0.9, dropout_probability=0.1
        )

        behavior2 = ReaderBehavior(
            reader_segment=ReaderSegment.NEW, engagement_score=0.8, retention_rate=0.9, dropout_probability=0.1
        )

        # When/Then: 等価である
        assert behavior1 == behavior2
        assert hash(behavior1) == hash(behavior2)

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_reader_behavior_inequality(self) -> None:
        """ReaderBehaviorの非等価性テスト"""
        # Given: 異なる値を持つ2つのReaderBehavior
        behavior1 = ReaderBehavior(
            reader_segment=ReaderSegment.NEW, engagement_score=0.8, retention_rate=0.9, dropout_probability=0.1
        )

        behavior2 = ReaderBehavior(
            reader_segment=ReaderSegment.REGULAR, engagement_score=0.6, retention_rate=0.7, dropout_probability=0.3
        )

        # When/Then: 等価でない
        assert behavior1 != behavior2
        assert hash(behavior1) != hash(behavior2)

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_score_validation_ranges(self) -> None:
        """スコア範囲検証テスト"""
        # Given: 範囲外の値を持つReaderBehavior
        # When/Then: 作成時にエラーが発生する
        with pytest.raises(ValueError, match=".*"):
            ReaderBehavior(
                reader_segment=ReaderSegment.NEW,
                engagement_score=1.5,  # 範囲外(0.0-1.0)
                retention_rate=0.9,
                dropout_probability=0.1,
            )

        with pytest.raises(ValueError, match=".*"):
            ReaderBehavior(
                reader_segment=ReaderSegment.NEW,
                engagement_score=0.8,
                retention_rate=-0.1,  # 範囲外(0.0-1.0)
                dropout_probability=0.1,
            )

        with pytest.raises(ValueError, match=".*"):
            ReaderBehavior(
                reader_segment=ReaderSegment.NEW,
                engagement_score=0.8,
                retention_rate=0.9,
                dropout_probability=2.0,  # 範囲外(0.0-1.0
            )
