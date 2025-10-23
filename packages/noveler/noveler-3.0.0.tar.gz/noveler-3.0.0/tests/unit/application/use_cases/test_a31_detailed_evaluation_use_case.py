#!/usr/bin/env python3
"""A31DetailedEvaluationUseCase アプリケーション層単体テスト

TDD Red フェーズ: A31詳細評価ユースケースの失敗テスト
手動Claude Code分析レベルの評価機能をテスト
"""

from unittest.mock import Mock

import pytest

from noveler.application.use_cases.a31_detailed_evaluation_use_case import (
    A31DetailedEvaluationRequest,
    A31DetailedEvaluationUseCase,
)
from noveler.domain.entities.category_analysis_result import CategoryAnalysisResult
from noveler.domain.services.detailed_analysis_engine import (
    DetailedAnalysisEngine,
    DetailedAnalysisResult,
)
from noveler.domain.value_objects.a31_evaluation_category import A31EvaluationCategory


@pytest.mark.spec("SPEC-A31-DET-001")
class TestA31DetailedEvaluationUseCase:
    """A31DetailedEvaluationUseCase アプリケーション層テスト"""

    def setup_method(self) -> None:
        """テストセットアップ"""
        # モックリポジトリ作成
        self.mock_episode_repository = Mock()
        self.mock_project_repository = Mock()
        self.mock_a31_checklist_repository = Mock()
        self.mock_detailed_evaluation_repository = Mock()
        self.mock_analysis_engine = Mock(spec=DetailedAnalysisEngine)

        # ユースケースインスタンス作成
        self.use_case = A31DetailedEvaluationUseCase(
            episode_repository=self.mock_episode_repository,
            project_repository=self.mock_project_repository,
            a31_checklist_repository=self.mock_a31_checklist_repository,
            detailed_evaluation_repository=self.mock_detailed_evaluation_repository,
            analysis_engine=self.mock_analysis_engine,
        )

        # テストデータ
        self.test_project_name = "テストプロジェクト"
        self.test_episode_number = 1
        self.test_episode_content = """# 第001話 テスト

「こんにちは」と彼女は言った。だった。だった。

俺は驚いた。彼女の笑顔が美しかった。"""

    @pytest.mark.spec("SPEC-A31_DETAILED_EVALUATION_USE_CASE-EXECUTE_DETAILED_EVA")
    def test_execute_detailed_evaluation_successfully(self) -> None:
        """詳細評価が正常に実行される"""
        # Given
        request = A31DetailedEvaluationRequest(
            project_name=self.test_project_name,
            episode_number=self.test_episode_number,
            target_categories=[A31EvaluationCategory.STYLE_CONSISTENCY],
            include_line_feedback=True,
            include_improvement_suggestions=True,
            output_format="comprehensive",
            save_results=True,
        )

        # エピソード内容取得のモック設定
        self.mock_episode_repository.get_episode_content.return_value = self.test_episode_content

        # チェックリスト項目のモック設定
        mock_checklist_item = Mock()
        mock_checklist_item.category = A31EvaluationCategory.STYLE_CONSISTENCY
        self.mock_a31_checklist_repository.get_all_checklist_items.return_value = [mock_checklist_item]

        # 分析結果のモック設定
        mock_category_result = CategoryAnalysisResult.create(
            category=A31EvaluationCategory.STYLE_CONSISTENCY,
            score=75.0,
            issues_found=["文末単調性問題"],
            suggestions=["文末バリエーションを増やす"],
        )

        mock_analysis_result = Mock(spec=DetailedAnalysisResult)
        mock_analysis_result.overall_score = 78.5
        mock_analysis_result.category_results = [mock_category_result]
        mock_analysis_result.line_feedbacks = []
        mock_analysis_result.confidence_score = 0.85

        self.mock_analysis_engine.analyze_episode_detailed.return_value = mock_analysis_result

        # When
        response = self.use_case.execute(request)

        # Then
        assert response.success is True
        assert response.project_name == self.test_project_name
        assert response.episode_number == self.test_episode_number
        assert response.overall_score == 78.5
        assert response.confidence_score == 0.85
        assert len(response.category_scores) == 1
        assert "style_consistency" in response.category_scores

        # リポジトリメソッドが呼ばれたことを確認
        self.mock_episode_repository.get_episode_content.assert_called_once_with(
            self.test_project_name, self.test_episode_number
        )

        self.mock_detailed_evaluation_repository.save_evaluation_session.assert_called_once()
        self.mock_detailed_evaluation_repository.save_analysis_result.assert_called_once()

    @pytest.mark.spec("SPEC-A31_DETAILED_EVALUATION_USE_CASE-EXECUTE_WITH_SPECIFI")
    def test_execute_with_specific_target_categories(self) -> None:
        """特定カテゴリ指定での実行"""
        # Given
        target_categories = [A31EvaluationCategory.FORMAT_CHECK, A31EvaluationCategory.CONTENT_BALANCE]

        request = A31DetailedEvaluationRequest(
            project_name=self.test_project_name,
            episode_number=self.test_episode_number,
            target_categories=target_categories,
            output_format="summary",
        )

        # エピソード内容取得のモック設定
        self.mock_episode_repository.get_episode_content.return_value = self.test_episode_content

        # 対象カテゴリのチェックリスト項目のみ返す
        mock_items = []
        for category in target_categories:
            mock_item = Mock()
            mock_item.category = category
            mock_items.append(mock_item)

        self.mock_a31_checklist_repository.get_all_checklist_items.return_value = mock_items

        # 分析結果のモック設定
        mock_category_results = [
            CategoryAnalysisResult.create(
                category=A31EvaluationCategory.FORMAT_CHECK, score=82.0, issues_found=[], suggestions=[]
            ),
            CategoryAnalysisResult.create(
                category=A31EvaluationCategory.CONTENT_BALANCE,
                score=77.5,
                issues_found=["バランス問題"],
                suggestions=["改善提案"],
            ),
        ]

        mock_analysis_result = Mock(spec=DetailedAnalysisResult)
        mock_analysis_result.overall_score = 79.75
        mock_analysis_result.category_results = mock_category_results
        mock_analysis_result.line_feedbacks = []
        mock_analysis_result.confidence_score = 0.88

        self.mock_analysis_engine.analyze_episode_detailed.return_value = mock_analysis_result

        # When
        response = self.use_case.execute(request)

        # Then
        assert response.success is True
        assert len(response.category_scores) == 2
        assert "format_check" in response.category_scores
        assert "content_balance" in response.category_scores
        assert response.category_scores["format_check"] == 82.0
        assert response.category_scores["content_balance"] == 77.5

    @pytest.mark.spec("SPEC-A31_DETAILED_EVALUATION_USE_CASE-EXECUTE_WITH_YAML_OU")
    def test_execute_with_yaml_output_format(self) -> None:
        """YAML出力形式での実行"""
        # Given
        request = A31DetailedEvaluationRequest(
            project_name=self.test_project_name, episode_number=self.test_episode_number, output_format="yaml"
        )

        # 基本モック設定
        self.mock_episode_repository.get_episode_content.return_value = self.test_episode_content
        self.mock_a31_checklist_repository.get_all_checklist_items.return_value = []

        mock_analysis_result = Mock(spec=DetailedAnalysisResult)
        mock_analysis_result.overall_score = 85.0
        mock_analysis_result.category_results = []
        mock_analysis_result.line_feedbacks = []
        mock_analysis_result.confidence_score = 0.90

        self.mock_analysis_engine.analyze_episode_detailed.return_value = mock_analysis_result

        # When
        response = self.use_case.execute(request)

        # Then
        assert response.success is True
        assert response.yaml_output is not None
        assert "evaluation_summary" in response.yaml_output
        assert "overall_score: 85.0" in response.yaml_output

    @pytest.mark.spec("SPEC-A31_DETAILED_EVALUATION_USE_CASE-EXECUTE_LEGACY_A31_C")
    def test_execute_legacy_a31_compatible_format(self) -> None:
        """既存A31システム互換フォーマットでの実行"""
        # Given
        request = A31DetailedEvaluationRequest(
            project_name=self.test_project_name, episode_number=self.test_episode_number
        )

        # 基本モック設定
        self.mock_episode_repository.get_episode_content.return_value = self.test_episode_content
        self.mock_a31_checklist_repository.get_all_checklist_items.return_value = []

        mock_category_result = CategoryAnalysisResult.create(
            category=A31EvaluationCategory.QUALITY_THRESHOLD, score=88.0, issues_found=[], suggestions=[]
        )

        mock_analysis_result = Mock(spec=DetailedAnalysisResult)
        mock_analysis_result.overall_score = 88.0
        mock_analysis_result.category_results = [mock_category_result]
        mock_analysis_result.line_feedbacks = []
        mock_analysis_result.confidence_score = 0.92

        self.mock_analysis_engine.analyze_episode_detailed.return_value = mock_analysis_result

        # When
        legacy_response = self.use_case.execute_legacy_a31_compatible(request)

        # Then
        assert legacy_response["success"] is True
        assert legacy_response["project_name"] == self.test_project_name
        assert legacy_response["episode_number"] == self.test_episode_number
        assert "evaluation_batch" in legacy_response
        assert legacy_response["overall_score"] == 88.0
        assert legacy_response["pass_rate"] >= 0.0

    @pytest.mark.spec("SPEC-A31_DETAILED_EVALUATION_USE_CASE-HANDLE_EPISODE_NOT_F")
    def test_handle_episode_not_found_error(self) -> None:
        """エピソード未発見エラーの処理"""
        # Given
        request = A31DetailedEvaluationRequest(
            project_name=self.test_project_name,
            episode_number=999,  # 存在しないエピソード
        )

        # エピソード取得でFileNotFoundError発生
        self.mock_episode_repository.get_episode_content.side_effect = FileNotFoundError("エピソードが見つかりません")

        # When
        response = self.use_case.execute(request)

        # Then
        assert response.success is False
        assert "エピソード 999 が見つかりません" in response.error_message
        assert response.overall_score == 0.0
        assert response.total_issues_found == 0

    @pytest.mark.spec("SPEC-A31_DETAILED_EVALUATION_USE_CASE-HANDLE_ANALYSIS_ENGI")
    def test_handle_analysis_engine_error(self) -> None:
        """分析エンジンエラーの処理"""
        # Given
        request = A31DetailedEvaluationRequest(
            project_name=self.test_project_name, episode_number=self.test_episode_number
        )

        # 基本モック設定
        self.mock_episode_repository.get_episode_content.return_value = self.test_episode_content
        self.mock_a31_checklist_repository.get_all_checklist_items.return_value = []

        # 分析エンジンでエラー発生
        self.mock_analysis_engine.analyze_episode_detailed.side_effect = Exception("分析エンジンエラー")

        # When
        response = self.use_case.execute(request)

        # Then
        assert response.success is False
        assert "詳細評価実行中にエラーが発生しました" in response.error_message
        assert "分析エンジンエラー" in response.error_message

    @pytest.mark.spec("SPEC-A31_DETAILED_EVALUATION_USE_CASE-PREPARE_ANALYSIS_CON")
    def test_prepare_analysis_context_with_previous_episode(self) -> None:
        """前話内容を含む分析コンテキストの準備"""
        # Given
        request = A31DetailedEvaluationRequest(
            project_name=self.test_project_name,
            episode_number=2,  # 2話目なので前話あり
        )

        # 現在話と前話の内容設定
        self.mock_episode_repository.get_episode_content.side_effect = [
            "第002話の内容",  # 現在話
            "第001話の内容",  # 前話（episode_number - 1）
        ]

        self.mock_a31_checklist_repository.get_all_checklist_items.return_value = []

        # プロジェクト設定のモック
        self.mock_project_repository.get_project_config.return_value = {"quality_threshold": 85.0}

        mock_analysis_result = Mock(spec=DetailedAnalysisResult)
        mock_analysis_result.overall_score = 80.0
        mock_analysis_result.category_results = []
        mock_analysis_result.line_feedbacks = []
        mock_analysis_result.confidence_score = 0.8

        self.mock_analysis_engine.analyze_episode_detailed.return_value = mock_analysis_result

        # When
        response = self.use_case.execute(request)

        # Then
        assert response.success is True

        # 分析エンジンが適切なコンテキストで呼ばれたことを確認
        self.mock_analysis_engine.analyze_episode_detailed.assert_called_once()
        call_args = self.mock_analysis_engine.analyze_episode_detailed.call_args
        context = call_args[1]["context"]  # keyword arguments

        assert context.project_name == self.test_project_name
        assert context.episode_number == 2
        assert context.quality_threshold == 85.0
        assert context.previous_episode_content == "第001話の内容"

    @pytest.mark.spec("SPEC-A31_DETAILED_EVALUATION_USE_CASE-SAVE_RESULTS_DISABLE")
    def test_save_results_disabled(self) -> None:
        """結果保存無効時の動作"""
        # Given
        request = A31DetailedEvaluationRequest(
            project_name=self.test_project_name,
            episode_number=self.test_episode_number,
            save_results=False,  # 保存無効
        )

        # 基本モック設定
        self.mock_episode_repository.get_episode_content.return_value = self.test_episode_content
        self.mock_a31_checklist_repository.get_all_checklist_items.return_value = []

        mock_analysis_result = Mock(spec=DetailedAnalysisResult)
        mock_analysis_result.overall_score = 85.0
        mock_analysis_result.category_results = []
        mock_analysis_result.line_feedbacks = []
        mock_analysis_result.confidence_score = 0.90

        self.mock_analysis_engine.analyze_episode_detailed.return_value = mock_analysis_result

        # When
        response = self.use_case.execute(request)

        # Then
        assert response.success is True

        # 保存メソッドが呼ばれていないことを確認
        self.mock_detailed_evaluation_repository.save_evaluation_session.assert_not_called()
        self.mock_detailed_evaluation_repository.save_analysis_result.assert_not_called()

    @pytest.mark.spec("SPEC-A31_DETAILED_EVALUATION_USE_CASE-CALCULATE_EXECUTION_")
    def test_calculate_execution_time_accurately(self) -> None:
        """実行時間が正確に計算される"""
        # Given
        request = A31DetailedEvaluationRequest(
            project_name=self.test_project_name, episode_number=self.test_episode_number
        )

        # 実行時間をシミュレートするため、少し処理を遅延させる
        import time

        def slow_analysis(*args, **kwargs):
            time.sleep(0.1)  # 100ms遅延
            mock_result = Mock(spec=DetailedAnalysisResult)
            mock_result.overall_score = 85.0
            mock_result.category_results = []
            mock_result.line_feedbacks = []
            mock_result.confidence_score = 0.90
            return mock_result

        # 基本モック設定
        self.mock_episode_repository.get_episode_content.return_value = self.test_episode_content
        self.mock_a31_checklist_repository.get_all_checklist_items.return_value = []
        self.mock_analysis_engine.analyze_episode_detailed.side_effect = slow_analysis

        # When
        response = self.use_case.execute(request)

        # Then
        assert response.success is True
        assert response.execution_time_seconds >= 0.1  # 最低100ms
        assert response.execution_time_seconds < 1.0  # 1秒未満
