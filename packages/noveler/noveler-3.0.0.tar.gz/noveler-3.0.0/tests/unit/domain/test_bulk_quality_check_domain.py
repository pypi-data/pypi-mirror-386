"""全話品質チェック機能のテストケース

仕様書: scripts/specs/bulk_quality_check.spec.md
"""

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from noveler.domain.entities.bulk_quality_check import QualityHistory
from noveler.domain.services.bulk_quality_check_service import BulkQualityCheckService
from noveler.domain.value_objects.quality_check_result import (
    CategoryScores,
    QualityCheckResult,
    QualityError,
    QualityScore,
)


@dataclass
class BulkQualityCheckRequest:
    """全話品質チェック要求"""

    project_name: str
    episode_range: tuple[int, int] | None = None
    parallel: bool = False
    include_archived: bool = False
    force_recheck: bool = False


@dataclass
class BulkQualityCheckResult:
    """全話品質チェック結果"""

    project_name: str
    total_episodes: int
    checked_episodes: int
    average_quality_score: float
    quality_trend: str
    problematic_episodes: list[int]
    improvement_suggestions: list[str]
    execution_time: float
    success: bool
    errors: list[str]


class TestBulkQualityCheckService:
    """全話品質チェックサービスのテストケース"""

    def setup_method(self) -> None:
        """テストセットアップ"""
        self.mock_episode_repository = Mock()
        self.mock_quality_repository = Mock()
        self.mock_quality_checker = Mock()
        self.service = BulkQualityCheckService(
            episode_repository=self.mock_episode_repository,
            quality_repository=self.mock_quality_repository,
            quality_checker=self.mock_quality_checker,
        )

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_all_episodesquality_check(self) -> None:
        """仕様3.1: 全話品質チェック実行の正常系"""
        # Arrange
        request = BulkQualityCheckRequest(project_name="test_project", episode_range=None, parallel=False)

        # モックの設定
        self.mock_episode_repository.find_by_project.return_value = [
            Mock(episode_number=1, title="第1話"),
            Mock(episode_number=2, title="第2話"),
            Mock(episode_number=3, title="第3話"),
        ]

        # 既存のQualityCheckResultに合わせたモック
        category_scores = CategoryScores(
            basic_style=QualityScore.from_float(80.0),
            composition=QualityScore.from_float(90.0),
            character_consistency=QualityScore.from_float(85.0),
            readability=QualityScore.from_float(85.0),
        )

        self.mock_quality_checker.check_episode.return_value = QualityCheckResult(
            episode_number=1,
            timestamp=datetime.now(timezone.utc),
            checker_version="1.0.0",
            category_scores=category_scores,
            errors=[],
            warnings=[],
            auto_fixes=[],
            word_count=1000,
        )

        # Act
        result = self.service.execute_bulk_check(request)

        # Assert
        assert result.success is True
        assert result.project_name == "test_project"
        assert result.total_episodes == 3
        assert result.checked_episodes == 3
        assert result.average_quality_score == 85.0
        assert len(result.problematic_episodes) == 0
        assert len(result.improvement_suggestions) > 0

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_all_episodesquality_check_1(self) -> None:
        """仕様5: プロジェクトが存在しない場合のエラーハンドリング"""
        # Arrange
        request = BulkQualityCheckRequest(project_name="nonexistent_project")
        self.mock_episode_repository.find_by_project.return_value = []

        # Act
        result = self.service.execute_bulk_check(request)

        # Assert
        assert result.success is False
        assert result.total_episodes == 0
        assert result.checked_episodes == 0
        assert len(result.errors) == 1
        assert "nonexistent_project" in result.errors[0]

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_all_episodesquality_check_2(self) -> None:
        """仕様5: エピソードが存在しない場合のエラーハンドリング"""
        # Arrange
        request = BulkQualityCheckRequest(project_name="empty_project")
        self.mock_episode_repository.find_by_project.return_value = []

        # Act
        result = self.service.execute_bulk_check(request)

        # Assert
        assert result.success is False
        assert result.total_episodes == 0
        assert result.checked_episodes == 0
        assert len(result.errors) == 1
        assert "empty_project" in result.errors[0]

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_all_episodesquality_check_3(self) -> None:
        """仕様3.1: 範囲指定での品質チェック"""
        # Arrange
        request = BulkQualityCheckRequest(project_name="test_project", episode_range=(1, 2))

        episodes = [
            Mock(episode_number=1, title="第1話"),
            Mock(episode_number=2, title="第2話"),
            Mock(episode_number=3, title="第3話"),
        ]
        self.mock_episode_repository.find_by_project.return_value = episodes

        # 範囲指定テスト用の品質チェック結果
        category_scores = CategoryScores(
            basic_style=QualityScore.from_float(85.0),
            composition=QualityScore.from_float(80.0),
            character_consistency=QualityScore.from_float(85.0),
            readability=QualityScore.from_float(85.0),
        )

        self.mock_quality_checker.check_episode.return_value = QualityCheckResult(
            episode_number=1,
            timestamp=datetime.now(timezone.utc),
            checker_version="1.0.0",
            category_scores=category_scores,
            errors=[],
            warnings=[],
            auto_fixes=[],
            word_count=1000,
        )

        # Act
        result = self.service.execute_bulk_check(request)

        # Assert
        assert result.success is True
        assert result.total_episodes == 2  # 範囲内のエピソード数
        assert result.checked_episodes == 2  # 範囲指定で2話のみチェック

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_all_episodesquality_check_quality(self) -> None:
        """仕様3.1: 問題のある話を特定"""
        # Arrange
        request = BulkQualityCheckRequest(project_name="test_project")

        self.mock_episode_repository.find_by_project.return_value = [
            Mock(episode_number=1, title="第1話"),
            Mock(episode_number=2, title="第2話"),
        ]

        # 第1話は高品質、第2話は低品質に設定
        def mock_check_episode(episode):
            if episode.episode_number == 1:
                # from noveler.domain.value_objects.quality_check_result import (  # Moved to top-level
                # CategoryScores,
                # QualityCheckResult,
                # QualityScore,
                # )
                return QualityCheckResult(
                    episode_number=episode.episode_number,
                    timestamp=datetime.now(timezone.utc),
                    checker_version="1.0.0",
                    category_scores=CategoryScores(
                        basic_style=QualityScore.from_float(90.0),
                        composition=QualityScore.from_float(90.0),
                        character_consistency=QualityScore.from_float(90.0),
                        readability=QualityScore.from_float(90.0),
                    ),
                    errors=[],
                    warnings=[],
                    auto_fixes=[],
                    word_count=1000,
                )

            # from noveler.domain.value_objects.quality_check_result import (  # Moved to top-level
            # CategoryScores,
            # QualityCheckResult,
            # QualityError,
            # QualityScore,
            # )
            return QualityCheckResult(
                episode_number=episode.episode_number,
                timestamp=datetime.now(timezone.utc),
                checker_version="1.0.0",
                category_scores=CategoryScores(
                    basic_style=QualityScore.from_float(60.0),
                    composition=QualityScore.from_float(60.0),
                    character_consistency=QualityScore.from_float(60.0),
                    readability=QualityScore.from_float(60.0),
                ),
                errors=[
                    QualityError(
                        type="style_inconsistency",
                        message="文体が不安定",
                        severity="error",
                        suggestion="文体を統一してください",
                    )
                ],
                warnings=[],
                auto_fixes=[],
                word_count=1000,
            )

        self.mock_quality_checker.check_episode.side_effect = mock_check_episode

        # Act
        result = self.service.execute_bulk_check(request)

        # Assert
        assert result.success is True
        assert result.average_quality_score == 75.0  # (90 + 60) / 2
        assert 2 in result.problematic_episodes  # 第2話が問題として特定される
        assert len(result.improvement_suggestions) > 0

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_all_episodesquality_check_execution(self) -> None:
        """仕様6: 並列実行機能"""
        # Arrange
        request = BulkQualityCheckRequest(project_name="test_project", parallel=True)

        self.mock_episode_repository.find_by_project.return_value = [
            Mock(episode_number=i, title=f"第{i}話") for i in range(1, 11)
        ]

        # from noveler.domain.value_objects.quality_check_result import (  # Moved to top-level
        # CategoryScores,
        # QualityCheckResult,
        # QualityScore,
        # )
        self.mock_quality_checker.check_episode.return_value = QualityCheckResult(
            episode_number=1,
            timestamp=datetime.now(timezone.utc),
            checker_version="1.0.0",
            category_scores=CategoryScores(
                basic_style=QualityScore.from_float(85.0),
                composition=QualityScore.from_float(85.0),
                character_consistency=QualityScore.from_float(85.0),
                readability=QualityScore.from_float(85.0),
            ),
            errors=[],
            warnings=[],
            auto_fixes=[],
            word_count=1000,
        )

        # Act
        result = self.service.execute_bulk_check(request)

        # Assert
        assert result.success is True
        assert result.total_episodes == 10
        assert result.checked_episodes == 10
        # 並列実行フラグが設定されていることを確認
        assert request.parallel is True
        # モックされたチェッカーが10回呼ばれたことを確認
        assert self.mock_quality_checker.check_episode.call_count == 10

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_all_episodesquality_check_check(self) -> None:
        """仕様8: 強制再チェック機能"""
        # Arrange
        request = BulkQualityCheckRequest(project_name="test_project", force_recheck=True)

        self.mock_episode_repository.find_by_project.return_value = [Mock(episode_number=1, title="第1話")]

        # 既存の品質記録があることを設定
        self.mock_quality_repository.has_record.return_value = True

        # from noveler.domain.value_objects.quality_check_result import (  # Moved to top-level
        # CategoryScores,
        # QualityCheckResult,
        # QualityScore,
        # )
        self.mock_quality_checker.check_episode.return_value = QualityCheckResult(
            episode_number=1,
            timestamp=datetime.now(timezone.utc),
            checker_version="1.0.0",
            category_scores=CategoryScores(
                basic_style=QualityScore.from_float(85.0),
                composition=QualityScore.from_float(85.0),
                character_consistency=QualityScore.from_float(85.0),
                readability=QualityScore.from_float(85.0),
            ),
            errors=[],
            warnings=[],
            auto_fixes=[],
            word_count=1000,
        )

        # Act
        result = self.service.execute_bulk_check(request)

        # Assert
        assert result.success is True
        # 強制再チェックなので、既存記録があってもチェックが実行される
        self.mock_quality_checker.check_episode.assert_called_once()

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_all_episodesquality_check_4(self) -> None:
        """仕様6: パフォーマンス要件(10話あたり1秒以内)"""
        # Arrange
        request = BulkQualityCheckRequest(project_name="test_project")

        # 10話のエピソードを作成
        episodes = [Mock(episode_number=i, title=f"第{i}話") for i in range(1, 11)]
        self.mock_episode_repository.find_by_project.return_value = episodes

        # from noveler.domain.value_objects.quality_check_result import (  # Moved to top-level
        # CategoryScores,
        # QualityCheckResult,
        # QualityScore,
        # )
        self.mock_quality_checker.check_episode.return_value = QualityCheckResult(
            episode_number=1,
            timestamp=datetime.now(timezone.utc),
            checker_version="1.0.0",
            category_scores=CategoryScores(
                basic_style=QualityScore.from_float(85.0),
                composition=QualityScore.from_float(85.0),
                character_consistency=QualityScore.from_float(85.0),
                readability=QualityScore.from_float(85.0),
            ),
            errors=[],
            warnings=[],
            auto_fixes=[],
            word_count=1000,
        )

        # Act

        start_time = time.time()
        result = self.service.execute_bulk_check(request)
        elapsed_time = time.time() - start_time

        # Assert
        assert result.success is True
        assert elapsed_time < 1.0  # 10話あたり1秒以内
        assert result.execution_time < 1.0


class TestQualityHistory:
    """品質記録履歴のテストケース"""

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_quality_record(self) -> None:
        """仕様3.2: 品質記録管理の正常系"""
        # Arrange
        history = QualityHistory(project_name="test_project")
        # from noveler.domain.value_objects.quality_check_result import (  # Moved to top-level
        # CategoryScores,
        # QualityCheckResult,
        # QualityScore,
        # )
        quality_result = QualityCheckResult(
            episode_number=1,
            timestamp=datetime.now(timezone.utc),
            checker_version="1.0.0",
            category_scores=CategoryScores(
                basic_style=QualityScore.from_float(80.0),
                composition=QualityScore.from_float(90.0),
                character_consistency=QualityScore.from_float(85.0),
                readability=QualityScore.from_float(85.0),
            ),
            errors=[],
            warnings=[],
            auto_fixes=[],
            word_count=1000,
        )

        # Act
        history.add_record(episode_number=1, quality_result=quality_result)

        # Assert
        assert len(history.records) == 1
        record = history.records[0]
        assert record.episode_number == 1
        assert record.quality_score == 85.0
        assert record.category_scores == {
            "basic_style": 80.0,
            "composition": 90.0,
            "character_consistency": 85.0,
            "readability": 85.0,
        }

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_quality(self) -> None:
        """仕様3.2: 品質トレンドの計算"""
        # Arrange
        history = QualityHistory(project_name="test_project")

        # 品質が向上するトレンドを作成
        scores = [70.0, 75.0, 80.0, 85.0, 90.0]
        # from noveler.domain.value_objects.quality_check_result import (  # Moved to top-level
        # CategoryScores,
        # QualityCheckResult,
        # QualityScore,
        # )
        for i, score in enumerate(scores, 1):
            quality_result = QualityCheckResult(
                episode_number=i,
                timestamp=datetime.now(timezone.utc),
                checker_version="1.0.0",
                category_scores=CategoryScores(
                    basic_style=QualityScore.from_float(score),
                    composition=QualityScore.from_float(score),
                    character_consistency=QualityScore.from_float(score),
                    readability=QualityScore.from_float(score),
                ),
                errors=[],
                warnings=[],
                auto_fixes=[],
                word_count=1000,
            )

            history.add_record(episode_number=i, quality_result=quality_result)

        # Act
        trend = history.calculate_trend()

        # Assert
        assert trend.direction == "improving"  # 向上トレンド
        assert trend.slope > 0  # 正の傾き
        assert trend.confidence > 0.8  # 高い信頼度

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_unnamed(self) -> None:
        """仕様3.3: 問題のある話の特定"""
        # Arrange
        history = QualityHistory(project_name="test_project")

        # 品質にばらつきがあるデータを作成
        test_data = [
            (1, 90.0),  # 高品質
            (2, 60.0),  # 低品質
            (3, 85.0),  # 高品質
            (4, 55.0),  # 低品質
            (5, 88.0),  # 高品質
        ]

        # from noveler.domain.value_objects.quality_check_result import (  # Moved to top-level
        # CategoryScores,
        # QualityCheckResult,
        # QualityScore,
        # )
        for episode_num, score in test_data:
            quality_result = QualityCheckResult(
                episode_number=episode_num,
                timestamp=datetime.now(timezone.utc),
                checker_version="1.0.0",
                category_scores=CategoryScores(
                    basic_style=QualityScore.from_float(score),
                    composition=QualityScore.from_float(score),
                    character_consistency=QualityScore.from_float(score),
                    readability=QualityScore.from_float(score),
                ),
                errors=[],
                warnings=[],
                auto_fixes=[],
                word_count=1000,
            )

            history.add_record(episode_number=episode_num, quality_result=quality_result)

        # Act
        problematic_episodes = history.find_problematic_episodes(threshold=70.0)

        # Assert
        assert 2 in problematic_episodes  # 第2話(60.0)
        assert 4 in problematic_episodes  # 第4話(55.0)
        assert 1 not in problematic_episodes  # 第1話(90.0)は問題なし
        assert 3 not in problematic_episodes  # 第3話(85.0)は問題なし
        assert 5 not in problematic_episodes  # 第5話(88.0)は問題なし
