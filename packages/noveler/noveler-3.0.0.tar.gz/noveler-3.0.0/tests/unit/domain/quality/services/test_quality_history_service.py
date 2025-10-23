"""
SPEC-QUALITY-002: 品質履歴管理システムのテスト

品質チェック履歴の記録、トレンド分析、学習データ蓄積機能のテスト。
"""

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest
pytestmark = pytest.mark.quality_domain


from noveler.domain.repositories.quality_history_repository import QualityHistoryRepository
from noveler.domain.services.quality_history_service import QualityHistoryService
from noveler.domain.services.quality_history_value_objects import (
    AnalysisPeriod,
    ImprovementPattern,
    QualityHistory,
    QualityRecord,
    QualityTrendAnalysis,
    ImprovementRate,
    TrendDirection,
)
from noveler.domain.services.quality_trend_analyzer import QualityTrendAnalyzer
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.quality_score import QualityScore


@pytest.mark.spec("SPEC-QUALITY-002")
class TestQualityHistoryService:
    """品質履歴管理サービスのテスト"""

    @pytest.fixture
    def mock_repository(self) -> Mock:
        """モックリポジトリ"""
        return Mock()

    @pytest.fixture
    def mock_analyzer(self) -> Mock:
        """モック分析器"""
        return Mock(spec=QualityTrendAnalyzer)

    @pytest.fixture
    def service(self, mock_repository: Mock, mock_analyzer: Mock) -> QualityHistoryService:
        """テスト対象サービス"""
        return QualityHistoryService(mock_repository, mock_analyzer)

    @pytest.fixture
    def sample_quality_record(self) -> QualityRecord:
        """サンプル品質記録"""
        return QualityRecord(
            check_id="check_001",
            timestamp=datetime.now(timezone.utc),
            overall_score=QualityScore(85),
            category_scores={"structure": QualityScore(80), "style": QualityScore(90), "readability": QualityScore(85)},
            improvement_suggestions=["より具体的な描写を追加", "文章のリズムを改善"],
            checker_version="1.2.0",
            metadata={"check_duration": 1.5, "auto_fixed": False},
        )

    @pytest.fixture
    def sample_quality_history(self, sample_quality_record: QualityRecord) -> QualityHistory:
        """サンプル品質履歴"""
        records = [sample_quality_record]
        for i in range(1, 5):
            record = QualityRecord(
                check_id=f"check_{i:03d}",
                timestamp=datetime.now(timezone.utc) - timedelta(days=i),
                overall_score=QualityScore(80 + i),
                category_scores={
                    "structure": QualityScore(75 + i),
                    "style": QualityScore(85 + i),
                    "readability": QualityScore(80 + i),
                },
                improvement_suggestions=[f"改善提案{i}"],
                checker_version="1.2.0",
                metadata={},
            )

            records.append(record)

        return QualityHistory(
            episode_number=EpisodeNumber(1),
            history_records=records,
            analysis_summary=None,
            created_at=datetime.now(timezone.utc) - timedelta(days=7),
        )

    @pytest.mark.spec("SPEC-QUALITY_HISTORY_SERVICE-RECORD_QUALITY_CHECK")
    def test_record_quality_check_success(
        self,
        service: QualityHistoryService,
        mock_repository: Mock,
        mock_analyzer: Mock,
        sample_quality_record: QualityRecord,
        sample_quality_history: QualityHistory,
    ) -> None:
        """品質チェック結果記録成功テスト"""
        # Given
        episode_number = EpisodeNumber(1)
        mock_repository.find_by_episode.return_value = sample_quality_history
        mock_analyzer.calculate_improvement_rate.return_value = 7.5
        mock_analyzer.identify_weak_areas.return_value = ["style"]

        # When
        service.record_quality_check(episode_number, sample_quality_record)

        # Then
        mock_repository.find_by_episode.assert_called_once_with(episode_number)
        mock_repository.save_history.assert_called_once()

    @pytest.mark.spec("SPEC-QUALITY_HISTORY_SERVICE-ANALYZE_IMPROVEMENT_")
    def test_analyze_improvement_trend_success(
        self, service: QualityHistoryService, sample_quality_history: QualityHistory
    ) -> None:
        """改善トレンド分析成功テスト"""
        # Given
        period = AnalysisPeriod.LAST_30_DAYS

        service._repository.find_by_episode.return_value = sample_quality_history

        # When
        result = service.analyze_improvement_trend(sample_quality_history.episode_number, period)

        # Then
        assert isinstance(result, QualityTrendAnalysis)
        assert isinstance(result.trend_direction, TrendDirection)

    @pytest.mark.spec("SPEC-QUALITY_HISTORY_SERVICE-EXTRACT_LEARNING_PAT")
    def test_extract_learning_patterns_success(
        self, service: QualityHistoryService, sample_quality_history: QualityHistory
    ) -> None:
        """学習パターン抽出成功テスト"""
        # Given
        min_occurrences = 3

        # When
        patterns = service.extract_learning_patterns(sample_quality_history, min_occurrences)

        # Then
        assert isinstance(patterns, list)
        assert all(isinstance(pattern, ImprovementPattern) for pattern in patterns)

    @pytest.mark.spec("SPEC-QUALITY_HISTORY_SERVICE-GENERATE_PERSONALIZE")
    def test_generate_personalized_guidance_success(
        self, service: QualityHistoryService, sample_quality_history: QualityHistory
    ) -> None:
        """個人化指導生成成功テスト"""
        # Given
        writer_level = "intermediate"

        service._analyzer.identify_weak_areas.return_value = ["style", "structure"]

        # When
        guidance = service.generate_personalized_guidance(sample_quality_history, writer_level)

        # Then
        assert guidance["level"] == writer_level
        assert isinstance(guidance.get("improvement_patterns"), list)
        assert "recommended_actions" in guidance

    @pytest.mark.spec("SPEC-QUALITY_HISTORY_SERVICE-GET_QUALITY_HISTORY_")
    def test_get_quality_history_by_episode(
        self, service: QualityHistoryService, mock_repository: Mock, sample_quality_history: QualityHistory
    ) -> None:
        """エピソード別品質履歴取得テスト"""
        # Given
        episode_number = EpisodeNumber(1)
        mock_repository.find_by_episode.return_value = sample_quality_history

        # When
        history = service.get_quality_history(episode_number)

        # Then
        assert history is sample_quality_history

    @pytest.mark.spec("SPEC-QUALITY_HISTORY_SERVICE-CALCULATE_IMPROVEMEN")
    def test_calculate_improvement_rate(
        self, service: QualityHistoryService, sample_quality_history: QualityHistory
    ) -> None:
        """改善率計算テスト"""
        # When
        rate = service.calculate_improvement_rate(sample_quality_history)

        # Then
        assert isinstance(rate, ImprovementRate)
        assert rate.total_improvement >= 0

    @pytest.mark.spec("SPEC-QUALITY_HISTORY_SERVICE-EMPTY_HISTORY_HANDLI")
    def test_empty_history_handling(self, service: QualityHistoryService, mock_repository: Mock) -> None:
        """空の履歴の処理テスト"""
        # Given
        episode_number = EpisodeNumber(999)
        mock_repository.find_by_episode.return_value = None

        service._repository.find_by_episode.return_value = None

        # When
        result = service.analyze_improvement_trend(episode_number, AnalysisPeriod.LAST_7_DAYS)

        # Then
        assert result is None


@pytest.mark.spec("SPEC-QUALITY-002")
class TestQualityTrendAnalyzer:
    """品質トレンド分析器のテスト"""

    @pytest.fixture
    def analyzer(self) -> QualityTrendAnalyzer:
        """テスト対象分析器"""
        return QualityTrendAnalyzer()

    @pytest.mark.spec("SPEC-QUALITY_HISTORY_SERVICE-CALCULATE_IMPROVEMEN")
    def test_calculate_improvement_rate_success(self, analyzer: QualityTrendAnalyzer) -> None:
        """改善率計算成功テスト"""
        # Given
        records = [
            QualityRecord(
                check_id="1",
                timestamp=datetime.now(timezone.utc) - timedelta(days=5),
                overall_score=QualityScore(70),
                category_scores={},
                improvement_suggestions=[],
                checker_version="1.0",
                metadata={},
            ),
            QualityRecord(
                check_id="2",
                timestamp=datetime.now(timezone.utc),
                overall_score=QualityScore(85),
                category_scores={},
                improvement_suggestions=[],
                checker_version="1.0",
                metadata={},
            ),
        ]

        # When
        rate = analyzer.calculate_improvement_rate(records)

        # Then
        assert pytest.approx(rate, rel=1e-2) == 21.428571428571427

    @pytest.mark.spec("SPEC-QUALITY_HISTORY_SERVICE-IDENTIFY_WEAK_AREAS_")
    def test_identify_weak_areas_success(self, analyzer: QualityTrendAnalyzer) -> None:
        """弱点領域特定成功テスト"""
        # Given
        records = [
            QualityRecord(
                check_id="1",
                timestamp=datetime.now(timezone.utc),
                overall_score=QualityScore(80),
                category_scores={
                    "structure": QualityScore(90),
                    "style": QualityScore(60),  # 弱点
                    "readability": QualityScore(85),
                },
                improvement_suggestions=[],
                checker_version="1.0",
                metadata={},
            )
        ]

        # When
        weak_areas = analyzer.identify_weak_areas(records)

        # Then
        assert "style" in weak_areas

    @pytest.mark.spec("SPEC-QUALITY_HISTORY_SERVICE-PREDICT_QUALITY_TRAJ")
    def test_predict_quality_trajectory_success(self, analyzer: QualityTrendAnalyzer) -> None:
        """品質軌道予測成功テスト"""
        # Given
        historical_data = [
            QualityRecord(
                check_id=str(i),
                timestamp=datetime.now(timezone.utc) - timedelta(days=3 - i),
                overall_score=QualityScore(70 + i * 5),
                category_scores={},
                improvement_suggestions=[],
                checker_version="1.0",
                metadata={},
            )
            for i in range(3)
        ]
        prediction_days = 30

        # When
        prediction = analyzer.predict_quality_trajectory(historical_data, prediction_days)

        # Then
        assert prediction is not None
        assert 0.0 <= prediction.confidence_level <= 1.0


@pytest.mark.spec("SPEC-QUALITY-002")
class TestQualityHistoryValueObjects:
    """品質履歴値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-QUALITY_HISTORY_SERVICE-QUALITY_HISTORY_IMMU")
    def test_quality_history_immutability(self) -> None:
        """QualityHistoryの不変性テスト"""
        history = QualityHistory(
            episode_number=EpisodeNumber(1),
            history_records=[],
            analysis_summary=None,
            created_at=datetime.now(timezone.utc),
        )

        with pytest.raises(FrozenInstanceError):
            history.history_records = []

    @pytest.mark.spec("SPEC-QUALITY_HISTORY_SERVICE-QUALITY_RECORD_VALID")
    def test_quality_record_validation(self) -> None:
        """QualityRecordのバリデーションテスト"""
        with pytest.raises(ValueError):
            QualityRecord(
                check_id="",  # 空文字は無効
                timestamp=datetime.now(timezone.utc),
                overall_score=QualityScore(90),
                category_scores={},
                improvement_suggestions=[],
                checker_version="",
                metadata={},
            )

    @pytest.mark.spec("SPEC-QUALITY_HISTORY_SERVICE-IMPROVEMENT_PATTERN_")
    def test_improvement_pattern_effectiveness_calculation(self) -> None:
        """ImprovementPatternの効果性計算テスト"""
        pattern = ImprovementPattern(
            pattern_id="pattern_001",
            problem_type="文体の一貫性",
            successful_solutions=["敬語の統一", "文末表現の統一"],
            effectiveness_score=0.85,
            usage_frequency=12,
        )

        assert pattern.effectiveness_score == 0.85
        assert pattern.usage_frequency == 12

            # 効果性計算メソッドが正しく動作することを期待


@pytest.mark.spec("SPEC-QUALITY-002")
class TestQualityHistoryRepository:
    """品質履歴リポジトリインターフェースのテスト"""

    @pytest.mark.spec("SPEC-QUALITY_HISTORY_SERVICE-REPOSITORY_INTERFACE")
    def test_repository_interface_definition(self) -> None:
        """リポジトリインターフェースの定義テスト"""
        # 抽象クラスなので直接インスタンス化はできないことを確認
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            QualityHistoryRepository()

        # インターフェースが正しく定義されていることを確認
        assert hasattr(QualityHistoryRepository, "find_by_episode")
        assert hasattr(QualityHistoryRepository, "find_by_period")
        assert hasattr(QualityHistoryRepository, "save_record")
        assert hasattr(QualityHistoryRepository, "get_trend_statistics")
