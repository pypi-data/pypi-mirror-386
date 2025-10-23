"""品質チェックコマンドユースケースのユニットテスト

TDD原則に基づき、実装前にテストを作成。
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from noveler.application.use_cases.quality_check_command_use_case import (
    QualityCheckCommandRequest,
    QualityCheckCommandUseCase,
    QualityCheckTarget,
)
from noveler.domain.value_objects.completion_status import QualityCheckResult
from noveler.domain.value_objects.quality_score import QualityScore


@pytest.mark.spec("SPEC-QUALITY-014")
class TestQualityCheckCommandUseCase:
    """品質チェックコマンドユースケースのテスト"""

    @pytest.fixture
    def mock_episode_repository(self):
        """モックエピソードリポジトリ"""
        return Mock()

    @pytest.fixture
    def mock_quality_check_repository(self):
        """モック品質チェックリポジトリ"""
        return Mock()

    @pytest.fixture
    def mock_quality_record_repository(self):
        """モック品質記録リポジトリ"""
        return Mock()

    @pytest.fixture
    def use_case(
        self,
        mock_episode_repository: object,
        mock_quality_check_repository: object,
        mock_quality_record_repository: object,
    ):
        """ユースケースインスタンス"""
        return QualityCheckCommandUseCase(
            episode_repository=mock_episode_repository,
            quality_check_repository=mock_quality_check_repository,
            quality_record_repository=mock_quality_record_repository,
        )

    @pytest.mark.spec("SPEC-QUALITY_CHECK_COMMAND_USE_CASE-UNNAMED")
    def test_unnamed(
        self, use_case: object, mock_episode_repository: object, mock_quality_check_repository: object
    ) -> None:
        """単一エピソードの品質チェックが実行されることを確認"""
        # Given
        request = QualityCheckCommandRequest(
            project_name="テストプロジェクト",
            target=QualityCheckTarget.SINGLE,
            episode_number=1,
            auto_fix=False,
            verbose=True,
        )

        # エピソード情報をモック
        episode_info = {
            "number": 1,
            "title": "第1話",
            "content": "テスト内容",
            "file_path": Path("40_原稿/第001話_タイトル.md"),
        }
        mock_episode_repository.get_episode_info.return_value = episode_info

        # 品質チェック結果をモック
        quality_result = QualityCheckResult(score=QualityScore(85), passed=True, issues=[])
        mock_quality_check_repository.check_quality.return_value = quality_result

        # When
        response = use_case.execute(request)

        # Then
        assert response.success is True
        assert response.checked_count == 1
        assert response.passed_count == 1
        assert len(response.results) == 1
        assert response.results[0]["score"] == 85

    @pytest.mark.spec("SPEC-QUALITY_CHECK_COMMAND_USE_CASE-BULK_QUALITY_CHECK")
    def test_bulk_quality_check(
        self, use_case: object, mock_episode_repository: object, mock_quality_check_repository: object
    ) -> None:
        """全話一括チェックが実行されることを確認"""
        # Given
        request = QualityCheckCommandRequest(
            project_name="テストプロジェクト", target=QualityCheckTarget.BULK, auto_fix=False
        )

        # 複数エピソードをモック
        episodes = [
            {"number": 1, "title": "第1話", "content": "内容1"},
            {"number": 2, "title": "第2話", "content": "内容2"},
            {"number": 3, "title": "第3話", "content": "内容3"},
        ]
        mock_episode_repository.get_all_episodes.return_value = episodes

        # 品質チェック結果をモック(異なるスコア)
        quality_results = [
            QualityCheckResult(score=QualityScore(90), passed=True, issues=[]),
            QualityCheckResult(score=QualityScore(65), passed=False, issues=["文章が冗長"]),
            QualityCheckResult(score=QualityScore(80), passed=True, issues=[]),
        ]
        mock_quality_check_repository.check_quality.side_effect = quality_results

        # When
        response = use_case.execute(request)

        # Then
        assert response.success is True
        assert response.checked_count == 3
        assert response.passed_count == 2  # 90点と80点
        assert len(response.results) == 3

    @pytest.mark.spec("SPEC-QUALITY_CHECK_COMMAND_USE_CASE-UNNAMED")
    def test_basic_functionality(
        self, use_case: object, mock_episode_repository: object, mock_quality_check_repository: object
    ) -> None:
        """範囲指定チェックが実行されることを確認"""
        # Given
        request = QualityCheckCommandRequest(
            project_name="テストプロジェクト",
            target=QualityCheckTarget.RANGE,
            start_episode=5,
            end_episode=7,
            auto_fix=False,
        )

        # 範囲内のエピソードをモック
        episodes = [
            {"number": 5, "title": "第5話", "content": "内容5"},
            {"number": 6, "title": "第6話", "content": "内容6"},
            {"number": 7, "title": "第7話", "content": "内容7"},
        ]
        mock_episode_repository.get_episodes_in_range.return_value = episodes

        quality_result = QualityCheckResult(score=QualityScore(85), passed=True, issues=[])
        mock_quality_check_repository.check_quality.return_value = quality_result

        # When
        response = use_case.execute(request)

        # Then
        assert response.success is True
        assert response.checked_count == 3
        assert mock_episode_repository.get_episodes_in_range.called_with("テストプロジェクト", 5, 7)

    @pytest.mark.spec("SPEC-QUALITY_CHECK_COMMAND_USE_CASE-FROM")
    def test_from(self, use_case: object, mock_episode_repository: object) -> None:
        """エピソードが見つからない場合のエラー処理を確認"""
        # Given
        request = QualityCheckCommandRequest(
            project_name="テストプロジェクト", target=QualityCheckTarget.SINGLE, episode_number=999
        )

        mock_episode_repository.get_episode_info.return_value = None

        # When
        response = use_case.execute(request)

        # Then
        assert response.success is False
        assert response.error_message == "エピソードが見つかりません"
        assert response.checked_count == 0

    @pytest.mark.spec("SPEC-QUALITY_CHECK_COMMAND_USE_CASE-AUTO")
    def test_auto(
        self, use_case: object, mock_episode_repository: object, mock_quality_check_repository: object
    ) -> None:
        """自動修正モードが動作することを確認"""
        # Given
        request = QualityCheckCommandRequest(
            project_name="テストプロジェクト", target=QualityCheckTarget.SINGLE, episode_number=1, auto_fix=True
        )

        episode_info = {
            "number": 1,
            "title": "第1話",
            "content": "修正前の内容",
            "file_path": Path("40_原稿/第001話_タイトル.md"),
        }
        mock_episode_repository.get_episode_info.return_value = episode_info

        # 修正可能な問題を含む結果
        quality_result = QualityCheckResult(
            score=QualityScore(70), passed=False, issues=["句読点の誤り", "スペースの問題"]
        )

        mock_quality_check_repository.check_quality.return_value = quality_result

        # 自動修正後の結果
        fixed_result = QualityCheckResult(score=QualityScore(85), passed=True, issues=[])
        mock_quality_check_repository.auto_fix_content.return_value = ("修正後の内容", fixed_result)

        # When
        response = use_case.execute(request)

        # Then
        assert response.success is True
        assert response.results[0]["auto_fixed"] is True
        assert response.results[0]["score"] == 85
        mock_episode_repository.update_content.assert_called_once()

    @pytest.mark.spec("SPEC-QUALITY_CHECK_COMMAND_USE_CASE-RECORD")
    def test_record(
        self,
        use_case: object,
        mock_episode_repository: object,
        mock_quality_check_repository: object,
        mock_quality_record_repository: object,
    ) -> None:
        """品質チェック結果が記録されることを確認"""
        # Given
        request = QualityCheckCommandRequest(
            project_name="テストプロジェクト", target=QualityCheckTarget.SINGLE, episode_number=1, save_records=True
        )

        episode_info = {"number": 1, "title": "第1話", "content": "テスト内容"}
        mock_episode_repository.get_episode_info.return_value = episode_info

        quality_result = QualityCheckResult(score=QualityScore(85), passed=True, issues=[])
        mock_quality_check_repository.check_quality.return_value = quality_result

        # When
        response = use_case.execute(request)

        # Then
        assert response.success is True
        mock_quality_record_repository.save_check_result.assert_called_once()
        saved_record = mock_quality_record_repository.save_check_result.call_args[0][0]
        assert saved_record["episode_number"] == 1
        assert saved_record["score"] == 85


@pytest.mark.spec("SPEC-QUALITY-014")
class TestQualityCheckCommandRequest:
    """品質チェックコマンドリクエストのテスト"""

    @pytest.mark.spec("SPEC-QUALITY_CHECK_COMMAND_USE_CASE-UNNAMED")
    def test_edge_cases(self) -> None:
        """リクエストが正しく作成されることを確認"""
        # When
        request = QualityCheckCommandRequest(
            project_name="テストプロジェクト",
            target=QualityCheckTarget.SINGLE,
            episode_number=1,
            auto_fix=True,
            verbose=True,
            adaptive=True,
        )

        # Then
        assert request.project_name == "テストプロジェクト"
        assert request.target == QualityCheckTarget.SINGLE
        assert request.episode_number == 1
        assert request.auto_fix is True
        assert request.verbose is True
        assert request.adaptive is True

    @pytest.mark.spec("SPEC-QUALITY_CHECK_COMMAND_USE_CASE-UNNAMED")
    def test_error_handling(self) -> None:
        """デフォルト値が正しく設定されることを確認"""
        # When
        request = QualityCheckCommandRequest(project_name="テストプロジェクト", target=QualityCheckTarget.SINGLE)

        # Then
        assert request.auto_fix is False
        assert request.verbose is False
        assert request.adaptive is False
        assert request.save_records is True


@pytest.mark.spec("SPEC-QUALITY-014")
class TestQualityCheckTarget:
    """品質チェック対象のテスト"""

    @pytest.mark.spec("SPEC-QUALITY_CHECK_COMMAND_USE_CASE-UNNAMED")
    def test_validation(self) -> None:
        """各チェック対象が定義されていることを確認"""
        assert QualityCheckTarget.SINGLE == "single"
        assert QualityCheckTarget.BULK == "bulk"
        assert QualityCheckTarget.RANGE == "range"
        assert QualityCheckTarget.LATEST == "latest"
