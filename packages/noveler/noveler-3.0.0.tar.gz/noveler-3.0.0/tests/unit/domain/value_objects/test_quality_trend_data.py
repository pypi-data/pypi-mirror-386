"""品質トレンドデータ値オブジェクトのテスト

TDD準拠テスト:
    - QualityTrendData


仕様書: SPEC-DOMAIN-VALUE-OBJECTS
"""

import pytest

from noveler.domain.exceptions import ValidationError
from noveler.domain.value_objects.quality_trend_data import QualityTrendData


class TestQualityTrendData:
    """QualityTrendData値オブジェクトのテストクラス"""

    @pytest.fixture
    def valid_improvement_trend(self) -> QualityTrendData:
        """有効な改善トレンドデータ"""
        return QualityTrendData(
            category="基本文体",
            trend_direction="improvement",
            confidence_level=0.85,
            slope=2.5,
            recent_scores=[70.0, 75.0, 80.0, 82.0, 85.0],
            analysis_period_days=30,
        )

    @pytest.fixture
    def valid_decline_trend(self) -> QualityTrendData:
        """有効な悪化トレンドデータ"""
        return QualityTrendData(
            category="構成",
            trend_direction="decline",
            confidence_level=0.92,
            slope=-1.8,
            recent_scores=[85.0, 82.0, 79.0, 76.0],
            analysis_period_days=21,
        )

    @pytest.fixture
    def valid_stable_trend(self) -> QualityTrendData:
        """有効な安定トレンドデータ"""
        return QualityTrendData(
            category="読みやすさ",
            trend_direction="stable",
            confidence_level=0.67,
            slope=0.1,
            recent_scores=[75.0, 74.5, 75.2, 75.1, 74.8, 75.3],
            analysis_period_days=45,
        )

    def test_quality_trend_data_creation_improvement(self, valid_improvement_trend: QualityTrendData) -> None:
        """改善トレンドデータ作成テスト"""
        assert valid_improvement_trend.category == "基本文体"
        assert valid_improvement_trend.trend_direction == "improvement"
        assert valid_improvement_trend.confidence_level == 0.85
        assert valid_improvement_trend.slope == 2.5
        assert valid_improvement_trend.recent_scores == [70.0, 75.0, 80.0, 82.0, 85.0]
        assert valid_improvement_trend.analysis_period_days == 30

    def test_quality_trend_data_creation_decline(self, valid_decline_trend: QualityTrendData) -> None:
        """悪化トレンドデータ作成テスト"""
        assert valid_decline_trend.category == "構成"
        assert valid_decline_trend.trend_direction == "decline"
        assert valid_decline_trend.confidence_level == 0.92
        assert valid_decline_trend.slope == -1.8
        assert valid_decline_trend.recent_scores == [85.0, 82.0, 79.0, 76.0]
        assert valid_decline_trend.analysis_period_days == 21

    def test_quality_trend_data_creation_stable(self, valid_stable_trend: QualityTrendData) -> None:
        """安定トレンドデータ作成テスト"""
        assert valid_stable_trend.category == "読みやすさ"
        assert valid_stable_trend.trend_direction == "stable"
        assert valid_stable_trend.confidence_level == 0.67
        assert valid_stable_trend.slope == 0.1
        assert valid_stable_trend.recent_scores == [75.0, 74.5, 75.2, 75.1, 74.8, 75.3]
        assert valid_stable_trend.analysis_period_days == 45

    def test_quality_trend_data_confidence_level_below_min_error(self) -> None:
        """信頼度最小値未満エラーテスト"""
        with pytest.raises(ValidationError, match="信頼度は0.0から1.0の範囲で指定してください"):
            QualityTrendData(
                category="テスト",
                trend_direction="stable",
                confidence_level=-0.1,
                slope=0.0,
                recent_scores=[70.0, 71.0, 72.0],
                analysis_period_days=7,
            )

    def test_quality_trend_data_confidence_level_above_max_error(self) -> None:
        """信頼度最大値超過エラーテスト"""
        with pytest.raises(ValidationError, match="信頼度は0.0から1.0の範囲で指定してください"):
            QualityTrendData(
                category="テスト",
                trend_direction="stable",
                confidence_level=1.1,
                slope=0.0,
                recent_scores=[70.0, 71.0, 72.0],
                analysis_period_days=7,
            )

    def test_quality_trend_data_confidence_level_boundary_values(self) -> None:
        """信頼度境界値テスト"""
        # 最小値(0.0)
        trend_min = QualityTrendData(
            category="テスト",
            trend_direction="stable",
            confidence_level=0.0,
            slope=0.0,
            recent_scores=[70.0, 71.0, 72.0],
            analysis_period_days=7,
        )

        assert trend_min.confidence_level == 0.0

        # 最大値(1.0)
        trend_max = QualityTrendData(
            category="テスト",
            trend_direction="stable",
            confidence_level=1.0,
            slope=0.0,
            recent_scores=[70.0, 71.0, 72.0],
            analysis_period_days=7,
        )

        assert trend_max.confidence_level == 1.0

    def test_quality_trend_data_invalid_trend_direction_error(self) -> None:
        """無効なトレンド方向エラーテスト"""
        with pytest.raises(
            ValidationError, match="トレンド方向は 'improvement', 'decline', 'stable' のいずれかを指定してください"
        ):
            QualityTrendData(
                category="テスト",
                trend_direction="invalid",
                confidence_level=0.8,
                slope=0.0,
                recent_scores=[70.0, 71.0, 72.0],
                analysis_period_days=7,
            )

    def test_quality_trend_data_valid_trend_directions(self) -> None:
        """有効なトレンド方向テスト"""
        valid_directions = ["improvement", "decline", "stable"]

        for direction in valid_directions:
            trend = QualityTrendData(
                category="テスト",
                trend_direction=direction,
                confidence_level=0.8,
                slope=0.0,
                recent_scores=[70.0, 71.0, 72.0],
                analysis_period_days=7,
            )

            assert trend.trend_direction == direction

    def test_quality_trend_data_insufficient_recent_scores_error(self) -> None:
        """不十分な最新スコア数エラーテスト"""
        # 2つのスコア
        with pytest.raises(ValidationError, match="最低3つのデータポイントが必要です"):
            QualityTrendData(
                category="テスト",
                trend_direction="stable",
                confidence_level=0.8,
                slope=0.0,
                recent_scores=[70.0, 71.0],
                analysis_period_days=7,
            )

        # 1つのスコア
        with pytest.raises(ValidationError, match="最低3つのデータポイントが必要です"):
            QualityTrendData(
                category="テスト",
                trend_direction="stable",
                confidence_level=0.8,
                slope=0.0,
                recent_scores=[70.0],
                analysis_period_days=7,
            )

        # 空のスコア
        with pytest.raises(ValidationError, match="最低3つのデータポイントが必要です"):
            QualityTrendData(
                category="テスト",
                trend_direction="stable",
                confidence_level=0.8,
                slope=0.0,
                recent_scores=[],
                analysis_period_days=7,
            )

    def test_quality_trend_data_invalid_score_range_error(self) -> None:
        """無効なスコア範囲エラーテスト"""
        # 負のスコア
        with pytest.raises(ValidationError, match="スコアは0.0から100.0の範囲で指定してください"):
            QualityTrendData(
                category="テスト",
                trend_direction="stable",
                confidence_level=0.8,
                slope=0.0,
                recent_scores=[70.0, -1.0, 72.0],
                analysis_period_days=7,
            )

        # 100を超えるスコア
        with pytest.raises(ValidationError, match="スコアは0.0から100.0の範囲で指定してください"):
            QualityTrendData(
                category="テスト",
                trend_direction="stable",
                confidence_level=0.8,
                slope=0.0,
                recent_scores=[70.0, 101.0, 72.0],
                analysis_period_days=7,
            )

    def test_quality_trend_data_score_boundary_values(self) -> None:
        """スコア境界値テスト"""
        # 最小値・最大値を含むスコア
        trend = QualityTrendData(
            category="テスト",
            trend_direction="stable",
            confidence_level=0.8,
            slope=0.0,
            recent_scores=[0.0, 50.0, 100.0],
            analysis_period_days=7,
        )

        assert trend.recent_scores == [0.0, 50.0, 100.0]

    def test_quality_trend_data_zero_or_negative_analysis_period_error(self) -> None:
        """0以下の分析期間エラーテスト"""
        # 0日
        with pytest.raises(ValidationError, match="分析期間は1日以上で指定してください"):
            QualityTrendData(
                category="テスト",
                trend_direction="stable",
                confidence_level=0.8,
                slope=0.0,
                recent_scores=[70.0, 71.0, 72.0],
                analysis_period_days=0,
            )

        # 負の日数
        with pytest.raises(ValidationError, match="分析期間は1日以上で指定してください"):
            QualityTrendData(
                category="テスト",
                trend_direction="stable",
                confidence_level=0.8,
                slope=0.0,
                recent_scores=[70.0, 71.0, 72.0],
                analysis_period_days=-5,
            )

    def test_quality_trend_data_is_improving(
        self,
        valid_improvement_trend: QualityTrendData,
        valid_decline_trend: QualityTrendData,
        valid_stable_trend: QualityTrendData,
    ) -> None:
        """改善トレンド判定テスト"""
        assert valid_improvement_trend.is_improving() is True
        assert valid_decline_trend.is_improving() is False
        assert valid_stable_trend.is_improving() is False

    def test_quality_trend_data_is_declining(
        self,
        valid_improvement_trend: QualityTrendData,
        valid_decline_trend: QualityTrendData,
        valid_stable_trend: QualityTrendData,
    ) -> None:
        """悪化トレンド判定テスト"""
        assert valid_improvement_trend.is_declining() is False
        assert valid_decline_trend.is_declining() is True
        assert valid_stable_trend.is_declining() is False

    def test_quality_trend_data_is_stable(
        self,
        valid_improvement_trend: QualityTrendData,
        valid_decline_trend: QualityTrendData,
        valid_stable_trend: QualityTrendData,
    ) -> None:
        """安定トレンド判定テスト"""
        assert valid_improvement_trend.is_stable() is False
        assert valid_decline_trend.is_stable() is False
        assert valid_stable_trend.is_stable() is True

    def test_quality_trend_data_is_reliable_default_threshold(
        self, valid_improvement_trend: QualityTrendData, valid_stable_trend: QualityTrendData
    ) -> None:
        """信頼性判定(デフォルト閾値)テスト"""
        # 信頼度0.85 >= 0.7(デフォルト)
        assert valid_improvement_trend.is_reliable() is True

        # 信頼度0.67 < 0.7(デフォルト)
        assert valid_stable_trend.is_reliable() is False

    def test_quality_trend_data_is_reliable_custom_threshold(
        self, valid_improvement_trend: QualityTrendData, valid_decline_trend: QualityTrendData
    ) -> None:
        """信頼性判定(カスタム閾値)テスト"""
        # 信頼度0.85 < 0.9(カスタム)
        assert valid_improvement_trend.is_reliable(0.9) is False

        # 信頼度0.92 >= 0.9(カスタム)
        assert valid_decline_trend.is_reliable(0.9) is True

        # 信頼度0.85 >= 0.5(カスタム)
        assert valid_improvement_trend.is_reliable(0.5) is True

    def test_quality_trend_data_get_latest_score(
        self, valid_improvement_trend: QualityTrendData, valid_decline_trend: QualityTrendData
    ) -> None:
        """最新スコア取得テスト"""
        # 改善トレンド:[70.0, 75.0, 80.0, 82.0, 85.0]
        assert valid_improvement_trend.get_latest_score() == 85.0

        # 悪化トレンド:[85.0, 82.0, 79.0, 76.0]
        assert valid_decline_trend.get_latest_score() == 76.0

    def test_quality_trend_data_get_score_range(
        self, valid_improvement_trend: QualityTrendData, valid_stable_trend: QualityTrendData
    ) -> None:
        """スコア範囲取得テスト"""
        # 改善トレンド:[70.0, 75.0, 80.0, 82.0, 85.0]
        assert valid_improvement_trend.get_score_range() == (70.0, 85.0)

        # 安定トレンド:[75.0, 74.5, 75.2, 75.1, 74.8, 75.3]
        assert valid_stable_trend.get_score_range() == (74.5, 75.3)

    def test_quality_trend_data_get_average_score(
        self, valid_improvement_trend: QualityTrendData, valid_decline_trend: QualityTrendData
    ) -> None:
        """平均スコア取得テスト"""
        # 改善トレンド:[70.0, 75.0, 80.0, 82.0, 85.0] = 392.0 / 5 = 78.4
        assert valid_improvement_trend.get_average_score() == 78.4

        # 悪化トレンド:[85.0, 82.0, 79.0, 76.0] = 322.0 / 4 = 80.5
        assert valid_decline_trend.get_average_score() == 80.5

    def test_quality_trend_data_get_trend_summary(self, valid_improvement_trend: QualityTrendData) -> None:
        """トレンド要約取得テスト"""
        summary = valid_improvement_trend.get_trend_summary()

        assert summary["category"] == "基本文体"
        assert summary["direction"] == "improvement"
        assert summary["confidence"] == 0.85
        assert summary["slope"] == 2.5
        assert summary["latest_score"] == 85.0
        assert summary["average_score"] == 78.4
        assert summary["score_range"] == (70.0, 85.0)
        assert summary["analysis_period"] == 30
        assert summary["is_reliable"] is True

    def test_quality_trend_data_get_trend_summary_all_fields(self, valid_stable_trend: QualityTrendData) -> None:
        """トレンド要約全フィールドテスト"""
        summary = valid_stable_trend.get_trend_summary()

        required_fields = [
            "category",
            "direction",
            "confidence",
            "slope",
            "latest_score",
            "average_score",
            "score_range",
            "analysis_period",
            "is_reliable",
        ]

        for field in required_fields:
            assert field in summary

    def test_quality_trend_data_is_frozen(self, valid_improvement_trend: QualityTrendData) -> None:
        """品質トレンドデータオブジェクトの不変性テスト"""
        with pytest.raises(AttributeError, match=".*"):
            valid_improvement_trend.category = "変更後"  # type: ignore

        with pytest.raises(AttributeError, match=".*"):
            valid_improvement_trend.confidence_level = 0.9  # type: ignore

    def test_quality_trend_data_extreme_values(self) -> None:
        """極端な値でのテスト"""
        # 非常に多くのスコア
        large_scores = [50.0 + i * 0.1 for i in range(1000)]  # 1000個のスコア

        trend = QualityTrendData(
            category="大量データテスト",
            trend_direction="improvement",
            confidence_level=0.99,
            slope=100.0,
            recent_scores=large_scores,
            analysis_period_days=365,
        )

        assert len(trend.recent_scores) == 1000
        assert trend.get_latest_score() == large_scores[-1]
        assert trend.get_score_range() == (min(large_scores), max(large_scores))

    def test_quality_trend_data_edge_case_scores(self) -> None:
        """エッジケーススコアテスト"""
        # 同じスコアが続く場合
        same_scores = [75.0, 75.0, 75.0, 75.0, 75.0]

        trend = QualityTrendData(
            category="同値スコア",
            trend_direction="stable",
            confidence_level=0.8,
            slope=0.0,
            recent_scores=same_scores,
            analysis_period_days=10,
        )

        assert trend.get_average_score() == 75.0
        assert trend.get_score_range() == (75.0, 75.0)
        assert trend.get_latest_score() == 75.0

    def test_quality_trend_data_negative_slope(self) -> None:
        """負の傾きテスト"""
        trend = QualityTrendData(
            category="負の傾き",
            trend_direction="decline",
            confidence_level=0.8,
            slope=-5.2,
            recent_scores=[80.0, 75.0, 70.0],
            analysis_period_days=14,
        )

        assert trend.slope == -5.2
        assert trend.is_declining() is True

    def test_quality_trend_data_zero_slope(self) -> None:
        """0の傾きテスト"""
        trend = QualityTrendData(
            category="ゼロ傾き",
            trend_direction="stable",
            confidence_level=0.8,
            slope=0.0,
            recent_scores=[75.0, 75.1, 74.9],
            analysis_period_days=7,
        )

        assert trend.slope == 0.0
        assert trend.is_stable() is True

    def test_quality_trend_data_decimal_scores(self) -> None:
        """小数点スコアテスト"""
        decimal_scores = [72.5, 73.2, 74.8, 75.1, 76.3]

        trend = QualityTrendData(
            category="小数点スコア",
            trend_direction="improvement",
            confidence_level=0.82,
            slope=1.2,
            recent_scores=decimal_scores,
            analysis_period_days=15,
        )

        assert trend.get_latest_score() == 76.3
        assert trend.get_average_score() == sum(decimal_scores) / len(decimal_scores)
