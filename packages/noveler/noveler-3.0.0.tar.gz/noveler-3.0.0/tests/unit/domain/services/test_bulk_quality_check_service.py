#!/usr/bin/env python3
"""BulkQualityCheckServiceのユニットテスト

ドメインサービスのビジネスロジックをテスト
"""

from typing import Any
from unittest.mock import Mock

import pytest

from noveler.domain.services.bulk_quality_check_service import (
    BulkQualityCheckRequest,
    BulkQualityCheckService,
)
from noveler.domain.value_objects.quality_check_result import QualityCheckResult


class TestBulkQualityCheckService:
    """BulkQualityCheckServiceのテスト"""

    @pytest.fixture
    def mock_episode_repository(self):
        """モックエピソードリポジトリの作成"""
        return Mock()

    @pytest.fixture
    def mock_quality_repository(self):
        """モック品質リポジトリの作成"""
        return Mock()

    @pytest.fixture
    def mock_quality_checker(self):
        """モック品質チェッカーの作成"""
        return Mock()

    @pytest.fixture
    def service(self, mock_episode_repository: object, mock_quality_repository: object, mock_quality_checker: object):
        """テスト用サービスインスタンス"""
        return BulkQualityCheckService(mock_episode_repository, mock_quality_repository, mock_quality_checker)

    @pytest.fixture
    def sample_episodes(self):
        """サンプルエピソード"""
        episodes = []
        for i in range(1, 4):
            episode = Mock()
            episode.episode_number = i
            episode.title = f"第{i}話"
            episodes.append(episode)
        return episodes

    @pytest.fixture
    def sample_quality_results(self):
        """サンプル品質チェック結果"""
        results = []
        scores = [85.0, 90.0, 75.0]
        for score in scores:
            result = Mock(spec=QualityCheckResult)
            result.overall_score = Mock()
            result.overall_score.to_float.return_value = score
            result.category_scores = Mock()
            result.category_scores.to_dict.return_value = {
                "basic_style": score,
                "structure": score,
                "engagement": score,
            }
            results.append(result)
        return results

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_execute_bulk_check_success(
        self,
        service: BulkQualityCheckService,
        mock_episode_repository: Mock,
        mock_quality_checker: Mock,
        sample_episodes: list[Any],
        sample_quality_results: list[Mock],
    ) -> None:
        """全話品質チェックの成功テスト"""
        # Given
        request = BulkQualityCheckRequest(project_name="テストプロジェクト", parallel=False)
        mock_episode_repository.find_by_project.return_value = sample_episodes
        mock_quality_checker.check_episode.side_effect = sample_quality_results

        # When
        result = service.execute_bulk_check(request)

        # Then
        assert result.success is True
        assert result.project_name == "テストプロジェクト"
        assert result.total_episodes == 3
        assert result.checked_episodes == 3
        assert result.average_quality_score == 83.33333333333333  # (85 + 90 + 75) / 3
        assert result.quality_trend == "stable"
        assert result.errors == []
        assert result.execution_time > 0

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_execute_bulk_check_with_episode_range(
        self,
        service: BulkQualityCheckService,
        mock_episode_repository: Mock,
        mock_quality_checker: Mock,
        sample_episodes: list[Any],
        sample_quality_results: list[Mock],
    ) -> None:
        """エピソード範囲指定での品質チェック"""
        # Given
        request = BulkQualityCheckRequest(project_name="テストプロジェクト", episode_range=(2, 3), parallel=False)
        mock_episode_repository.find_by_project.return_value = sample_episodes
        mock_quality_checker.check_episode.side_effect = sample_quality_results[1:]  # 2話と3話分

        # When
        result = service.execute_bulk_check(request)

        # Then
        assert result.success is True
        assert result.total_episodes == 2  # フィルタリング後
        assert result.checked_episodes == 2
        mock_quality_checker.check_episode.assert_called()

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_execute_bulk_check_no_episodes(
        self, service: BulkQualityCheckService, mock_episode_repository: Mock
    ) -> None:
        """エピソードが見つからない場合"""
        # Given
        request = BulkQualityCheckRequest(project_name="空プロジェクト")
        mock_episode_repository.find_by_project.return_value = []

        # When
        result = service.execute_bulk_check(request)

        # Then
        assert result.success is False
        assert result.total_episodes == 0
        assert result.checked_episodes == 0
        assert "No episodes found" in result.errors[0]

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_execute_bulk_check_exception(
        self, service: BulkQualityCheckService, mock_episode_repository: Mock
    ) -> None:
        """例外発生時の処理"""
        # Given
        request = BulkQualityCheckRequest(project_name="エラープロジェクト")
        mock_episode_repository.find_by_project.side_effect = Exception("リポジトリエラー")

        # When
        result = service.execute_bulk_check(request)

        # Then
        assert result.success is False
        assert result.total_episodes == 0
        assert result.average_quality_score == 0.0
        assert "リポジトリエラー" in result.errors[0]

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_execute_parallel_check(
        self,
        service: BulkQualityCheckService,
        mock_quality_checker: Mock,
        sample_episodes: list[Any],
        sample_quality_results: list[Mock],
    ) -> None:
        """並列実行のテスト"""
        # Given
        mock_quality_checker.check_episode.side_effect = sample_quality_results

        # When
        results = service._execute_parallel_check(sample_episodes)

        # Then
        assert len(results) == 3
        assert mock_quality_checker.check_episode.call_count == 3

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_execute_sequential_check(
        self,
        service: BulkQualityCheckService,
        mock_quality_checker: Mock,
        sample_episodes: list[Any],
        sample_quality_results: list[Mock],
    ) -> None:
        """逐次実行のテスト"""
        # Given
        mock_quality_checker.check_episode.side_effect = sample_quality_results

        # When
        results = service._execute_sequential_check(sample_episodes)

        # Then
        assert len(results) == 3
        assert mock_quality_checker.check_episode.call_count == 3
        # 逐次実行なので順番通りに呼ばれる
        for i, episode in enumerate(sample_episodes):
            assert mock_quality_checker.check_episode.call_args_list[i][0][0] == episode

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_generate_improvement_suggestions_low_score(self, service: object, sample_quality_results: object) -> None:
        """低スコア時の改善提案生成"""
        # Given
        # 平均スコアを70に調整
        for result in sample_quality_results:
            result.overall_score.to_float.return_value = 70.0
            result.category_scores.to_dict.return_value = {"basic_style": 70.0, "structure": 70.0, "engagement": 70.0}

        # When
        suggestions = service._generate_improvement_suggestions(sample_quality_results)

        # Then
        assert len(suggestions) >= 1
        assert "全体的な品質向上が必要です" in suggestions
        assert "文体の統一性を確認してください" in suggestions

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_generate_improvement_suggestions_high_score(self, service: object) -> None:
        """高スコア時の改善提案生成"""
        # Given
        results = []
        for _ in range(3):
            result = Mock(spec=QualityCheckResult)
            result.overall_score = Mock()
            result.overall_score.to_float.return_value = 95.0
            result.category_scores = Mock()
            result.category_scores.to_dict.return_value = {"basic_style": 95.0, "structure": 95.0, "engagement": 95.0}
            results.append(result)

        # When
        suggestions = service._generate_improvement_suggestions(results)

        # Then
        # 高スコアでも何らかの提案は出る(現在の実装)
        assert len(suggestions) == 0  # 90以上なので提案なし

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_bulk_request_creation(self) -> None:
        """BulkQualityCheckRequestの作成テスト"""
        # Given/When
        request = BulkQualityCheckRequest(
            project_name="テスト", episode_range=(1, 10), parallel=True, include_archived=True, force_recheck=True
        )

        # Then
        assert request.project_name == "テスト"
        assert request.episode_range == (1, 10)
        assert request.parallel is True
        assert request.include_archived is True
        assert request.force_recheck is True

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_bulk_request_defaults(self) -> None:
        """BulkQualityCheckRequestのデフォルト値テスト"""
        # Given/When
        request = BulkQualityCheckRequest(project_name="テスト")

        # Then
        assert request.project_name == "テスト"
        assert request.episode_range is None
        assert request.parallel is False
        assert request.include_archived is False
        assert request.force_recheck is False

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_problematic_episodes_identification(
        self, service, mock_episode_repository, mock_quality_checker, sample_episodes
    ) -> None:
        """問題のあるエピソードの特定"""
        # Given
        request = BulkQualityCheckRequest(project_name="テストプロジェクト")
        mock_episode_repository.find_by_project.return_value = sample_episodes

        # 低スコアの結果を設定
        low_score_results = []
        scores = [65.0, 90.0, 60.0]  # 1話と3話が低スコア
        for score in scores:
            result = Mock(spec=QualityCheckResult)
            result.overall_score = Mock()
            result.overall_score.to_float.return_value = score
            result.category_scores = Mock()
            result.category_scores.to_dict.return_value = {
                "basic_style": score,
                "structure": score,
                "engagement": score,
            }
            low_score_results.append(result)

        mock_quality_checker.check_episode.side_effect = low_score_results

        # When
        result = service.execute_bulk_check(request)

        # Then
        assert result.success is True
        assert 1 in result.problematic_episodes  # 第1話
        assert 3 in result.problematic_episodes  # 第3話
        assert 2 not in result.problematic_episodes  # 第2話は問題なし

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_empty_results_handling(self, service: object) -> None:
        """空の結果リストの処理"""
        # Given
        empty_results = []

        # When
        suggestions = service._generate_improvement_suggestions(empty_results)

        # Then
        assert isinstance(suggestions, list)
        # 空の結果でも処理はエラーにならない
