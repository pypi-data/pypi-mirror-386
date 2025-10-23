"""離脱率分析ユースケースのユニットテスト

TDD原則に基づき、実装前にテストを作成。
"""

from datetime import date, datetime, timezone
from unittest.mock import Mock

import pytest

from noveler.application.use_cases.analyze_dropout_rate_use_case import (
    AnalyzeDropoutRateUseCase,
    DropoutAnalysisRequest,
    DropoutAnalysisResponse,
)
from noveler.domain.value_objects.dropout_metrics import AccessData, EpisodeAccess


@pytest.mark.spec("SPEC-QUALITY-014")
class TestAnalyzeDropoutRateUseCase:
    """離脱率分析ユースケースのテスト"""

    @pytest.fixture
    def mock_access_data_repository(self):
        """モックアクセスデータリポジトリ"""
        return Mock()

    @pytest.fixture
    def mock_analysis_result_repository(self):
        """モック分析結果リポジトリ"""
        return Mock()

    @pytest.fixture
    def use_case(self, mock_access_data_repository: object, mock_analysis_result_repository: object):
        """ユースケースインスタンス"""
        return AnalyzeDropoutRateUseCase(
            access_data_repository=mock_access_data_repository,
            analysis_result_repository=mock_analysis_result_repository,
        )

    @pytest.mark.spec("SPEC-ANALYZE_DROPOUT_RATE_USE_CASE-INTEGRATION_WITH_ACC")
    def test_integration_with_access_data_repository(
        self, use_case: object, mock_access_data_repository: object
    ) -> None:
        """離脱率分析が正常に実行されることを確認"""
        # Given
        request = DropoutAnalysisRequest(
            project_name="テストプロジェクト", ncode="n1234kr", target_date=datetime.now(timezone.utc).date()
        )

        # アクセスデータをモック
        access_data = AccessData(
            [
                EpisodeAccess(1, 1000, datetime.now(timezone.utc).date()),
                EpisodeAccess(2, 800, datetime.now(timezone.utc).date()),
                EpisodeAccess(3, 600, datetime.now(timezone.utc).date()),
            ]
        )

        mock_access_data_repository.get_access_data.return_value = access_data

        # When
        response = use_case.execute(request)

        # Then
        assert response is not None
        assert response.success is True
        assert response.average_dropout_rate == pytest.approx(22.5, 0.1)
        assert len(response.episode_dropouts) == 2
        assert response.episode_dropouts[0]["episode_number"] == 2
        assert response.episode_dropouts[0]["dropout_rate"] == pytest.approx(20.0, 0.1)

    @pytest.mark.spec("SPEC-ANALYZE_DROPOUT_RATE_USE_CASE-EMPTY_DATA_PROCESS")
    def test_empty_data_process(self, use_case: object, mock_access_data_repository: object) -> None:
        """空のアクセスデータでも正常に処理されることを確認"""
        # Given
        request = DropoutAnalysisRequest(project_name="テストプロジェクト", ncode="n1234kr")

        # 空のアクセスデータ
        access_data = AccessData([])
        mock_access_data_repository.get_access_data.return_value = access_data

        # When
        response = use_case.execute(request)

        # Then
        assert response.success is True
        assert response.average_dropout_rate == 0.0
        assert len(response.episode_dropouts) == 0
        assert len(response.critical_episodes) == 0

    @pytest.mark.spec("SPEC-ANALYZE_DROPOUT_RATE_USE_CASE-UNNAMED")
    def test_unnamed(
        self, use_case: object, mock_access_data_repository: object, mock_analysis_result_repository: object
    ) -> None:
        """分析結果が正しく保存されることを確認"""
        # Given
        request = DropoutAnalysisRequest(project_name="テストプロジェクト", ncode="n1234kr", save_result=True)

        access_data = AccessData(
            [
                EpisodeAccess(1, 1000, datetime.now(timezone.utc).date()),
                EpisodeAccess(2, 800, datetime.now(timezone.utc).date()),
            ]
        )
        mock_access_data_repository.get_access_data.return_value = access_data

        # When
        response = use_case.execute(request)

        # Then
        assert response.success is True
        mock_analysis_result_repository.save.assert_called_once()

        # 保存されたデータを検証
        saved_result = mock_analysis_result_repository.save.call_args[0][0]
        assert saved_result.project_name == "テストプロジェクト"
        assert saved_result.ncode == "n1234kr"
        assert saved_result.average_dropout_rate == pytest.approx(20.0, 0.1)

    @pytest.mark.spec("SPEC-ANALYZE_DROPOUT_RATE_USE_CASE-RECOMMENDATION_GENER")
    def test_recommendation_generation(self, use_case: object, mock_access_data_repository: object) -> None:
        """改善提案が正しく生成されることを確認"""
        # Given
        request = DropoutAnalysisRequest(
            project_name="テストプロジェクト", ncode="n1234kr", generate_recommendations=True
        )

        # 高い離脱率を含むデータ
        access_data = AccessData(
            [
                EpisodeAccess(1, 1000, datetime.now(timezone.utc).date()),
                EpisodeAccess(2, 650, datetime.now(timezone.utc).date()),  # 35% dropout
                EpisodeAccess(3, 500, datetime.now(timezone.utc).date()),  # 23% dropout
            ]
        )

        mock_access_data_repository.get_access_data.return_value = access_data

        # When
        response = use_case.execute(request)

        # Then
        assert response.success is True
        assert len(response.recommendations) > 0
        assert any("離脱率" in rec for rec in response.recommendations)
        assert response.recommendations[-1].startswith("KASASAGI")


@pytest.mark.spec("SPEC-QUALITY-014")
class TestDropoutAnalysisRequest:
    """離脱率分析リクエストのテスト"""

    @pytest.mark.spec("SPEC-ANALYZE_DROPOUT_RATE_USE_CASE-REQUEST_CREATION")
    def test_request_creation(self) -> None:
        """リクエストが正しく作成されることを確認"""
        # When
        request = DropoutAnalysisRequest(
            project_name="テストプロジェクト",
            ncode="n1234kr",
            target_date=date(2024, 1, 1),
            critical_threshold=30.0,
            save_result=True,
            generate_recommendations=True,
        )

        # Then
        assert request.project_name == "テストプロジェクト"
        assert request.ncode == "n1234kr"
        assert request.target_date == date(2024, 1, 1)
        assert request.critical_threshold == 30.0
        assert request.save_result is True
        assert request.generate_recommendations is True

    @pytest.mark.spec("SPEC-ANALYZE_DROPOUT_RATE_USE_CASE-DEFAULT_VALUES")
    def test_default_values(self) -> None:
        """デフォルト値が正しく設定されることを確認"""
        # When
        request = DropoutAnalysisRequest(project_name="テストプロジェクト", ncode="n1234kr")

        # Then
        assert request.target_date is None
        assert request.critical_threshold == 20.0
        assert request.save_result is False
        assert request.generate_recommendations is False


@pytest.mark.spec("SPEC-QUALITY-014")
class TestDropoutAnalysisResponse:
    """離脱率分析レスポンスのテスト"""

    @pytest.mark.spec("SPEC-ANALYZE_DROPOUT_RATE_USE_CASE-SUCCESS_RESPONSE_CRE")
    def test_success_response_creation(self) -> None:
        """成功レスポンスが正しく作成されることを確認"""
        # When
        response = DropoutAnalysisResponse(
            success=True,
            average_dropout_rate=25.5,
            episode_dropouts=[
                {"episode_number": 2, "dropout_rate": 20.0, "page_views": 800},
                {"episode_number": 3, "dropout_rate": 31.0, "page_views": 552},
            ],
            critical_episodes=[{"episode_number": 3, "dropout_rate": 31.0, "priority": "high"}],
            recommendations=["第3話の離脱率が高いため、内容の見直しを推奨"],
            analysis_id="test-id-123",
        )

        # Then
        assert response.success is True
        assert response.average_dropout_rate == 25.5
        assert len(response.episode_dropouts) == 2
        assert len(response.critical_episodes) == 1
        assert len(response.recommendations) == 1
        assert response.analysis_id == "test-id-123"
        assert response.error_message is None

    @pytest.mark.spec("SPEC-ANALYZE_DROPOUT_RATE_USE_CASE-ERROR_RESPONSE_CREAT")
    def test_error_response_creation(self) -> None:
        """エラーレスポンスが正しく作成されることを確認"""
        # When
        response = DropoutAnalysisResponse(success=False, error_message="データ取得に失敗しました")

        # Then
        assert response.success is False
        assert response.error_message == "データ取得に失敗しました"
        assert response.average_dropout_rate == 0.0
        assert len(response.episode_dropouts) == 0
