#!/usr/bin/env python3
"""詳細評価システム統合テスト

A31詳細評価システム全体の統合動作をテスト。
手動Claude Code分析レベルの品質評価機能を検証。


仕様書: SPEC-INTEGRATION
"""

import tempfile
from unittest.mock import Mock

import pytest

from noveler.application.use_cases.a31_detailed_evaluation_use_case import (
    A31DetailedEvaluationRequest,
    A31DetailedEvaluationUseCase,
)
from noveler.domain.services.detailed_analysis_engine import DetailedAnalysisEngine
from noveler.domain.value_objects.a31_evaluation_category import A31EvaluationCategory
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.infrastructure.repositories.yaml_detailed_evaluation_repository import YamlDetailedEvaluationRepository


@pytest.mark.integration
class TestDetailedEvaluationIntegration:
    """詳細評価システム統合テスト"""

    def setup_method(self) -> None:
        """テストセットアップ"""
        self.temp_dir = tempfile.mkdtemp()

        # 実際のリポジトリとエンジンを使用
        self.detailed_repository = YamlDetailedEvaluationRepository(self.temp_dir)
        self.analysis_engine = DetailedAnalysisEngine()

        # 他のリポジトリはモック
        self.mock_episode_repository = Mock()
        self.mock_project_repository = Mock()
        self.mock_a31_checklist_repository = Mock()

        # ユースケース作成
        self.use_case = A31DetailedEvaluationUseCase(
            episode_repository=self.mock_episode_repository,
            project_repository=self.mock_project_repository,
            a31_checklist_repository=self.mock_a31_checklist_repository,
            detailed_evaluation_repository=self.detailed_repository,
            analysis_engine=self.analysis_engine,
        )

        # テスト用エピソード内容
        self.test_episode_content = """# 第001話 詳細評価テスト

「おはようございます」と彼女は笑顔で言った。だった。だった。

俺の心は温かくなった。朝の光が教室に差し込んでいる。

「今日はいい天気ですね」

「そうですね。気持ちのいい朝です」

彼女の声には安らぎがあった。それは俺にとって何よりも大切なものだった。

窓の外では桜の花びらが舞っていた。春の訪れを感じさせる美しい光景だった。

「一緒に外に出ませんか？」と彼女は提案した。

俺は頷いた。このような穏やかな時間を彼女と過ごせることに感謝していた。"""

    def teardown_method(self) -> None:
        """テスト後クリーンアップ"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.spec("SPEC-DETAILED_EVALUATION_INTEGRATION-END_TO_END_DETAILED_")
    def test_end_to_end_detailed_evaluation_flow(self) -> None:
        """エンドツーエンド詳細評価フローのテスト"""
        # Given
        project_name = "統合テストプロジェクト"
        episode_number = 1

        # モックの設定
        self.mock_episode_repository.get_episode_content.return_value = self.test_episode_content
        self.mock_a31_checklist_repository.get_all_checklist_items.return_value = []
        self.mock_project_repository.get_project_config.return_value = {"quality_threshold": 80.0}

        request = A31DetailedEvaluationRequest(
            project_name=project_name,
            episode_number=episode_number,
            target_categories=[A31EvaluationCategory.STYLE_CONSISTENCY, A31EvaluationCategory.CONTENT_BALANCE],
            include_line_feedback=True,
            include_improvement_suggestions=True,
            output_format="comprehensive",
            save_results=True,
        )

        # When
        response = self.use_case.execute(request)

        # Then
        assert response.success is True
        assert response.project_name == project_name
        assert response.episode_number == episode_number
        assert response.overall_score > 0
        assert response.confidence_score > 0
        assert len(response.category_scores) == 2

        # 文体一貫性で「だった」の問題が検出されること
        style_score = response.category_scores.get("style_consistency", 0)
        assert style_score < 100  # 「だった」の反復により減点されるはず

    @pytest.mark.spec("SPEC-DETAILED_EVALUATION_INTEGRATION-YAML_PERSISTENCE_INT")
    def test_yaml_persistence_integration(self) -> None:
        """YAML永続化統合テスト"""
        # Given
        project_name = "永続化テストプロジェクト"
        episode_number = 1

        # モックの設定
        self.mock_episode_repository.get_episode_content.return_value = self.test_episode_content
        self.mock_a31_checklist_repository.get_all_checklist_items.return_value = []

        request = A31DetailedEvaluationRequest(
            project_name=project_name, episode_number=episode_number, save_results=True
        )

        # When - 評価実行
        response = self.use_case.execute(request)

        # Then - 評価完了確認
        assert response.success is True

        # 保存されたセッションを直接確認
        saved_session = self.detailed_repository.get_evaluation_session(project_name, EpisodeNumber(episode_number))

        assert saved_session is not None
        assert saved_session.project_name == project_name
        assert saved_session.episode_number.value == episode_number

        # 保存された分析結果を確認
        saved_analysis = self.detailed_repository.get_analysis_result(response.session_id)
        assert saved_analysis is not None
        assert saved_analysis.overall_score == response.overall_score

    @pytest.mark.spec("SPEC-DETAILED_EVALUATION_INTEGRATION-MULTIPLE_CATEGORY_AN")
    def test_multiple_category_analysis_integration(self) -> None:
        """複数カテゴリ分析統合テスト"""
        # Given
        project_name = "複数カテゴリテストプロジェクト"
        episode_number = 1

        # 全ての基本カテゴリをテスト対象とする
        all_core_categories = A31EvaluationCategory.get_all_core_categories()

        # モックの設定
        self.mock_episode_repository.get_episode_content.return_value = self.test_episode_content
        self.mock_a31_checklist_repository.get_all_checklist_items.return_value = []

        request = A31DetailedEvaluationRequest(
            project_name=project_name,
            episode_number=episode_number,
            target_categories=all_core_categories,
            save_results=False,
        )  # 保存は無効にしてパフォーマンス重視

        # When
        response = self.use_case.execute(request)

        # Then
        assert response.success is True
        assert len(response.category_scores) == len(all_core_categories)

        # 各カテゴリのスコアが有効範囲内であることを確認
        for category_name, score in response.category_scores.items():
            assert 0 <= score <= 100, f"カテゴリ {category_name} のスコアが無効: {score}"

        # 総合スコアが各カテゴリスコアの平均になっていることを確認
        expected_overall = sum(response.category_scores.values()) / len(response.category_scores)
        assert abs(response.overall_score - expected_overall) < 0.1

    @pytest.mark.spec("SPEC-DETAILED_EVALUATION_INTEGRATION-ERROR_HANDLING_INTEG")
    def test_error_handling_integration(self) -> None:
        """エラーハンドリング統合テスト"""
        # Given - 存在しないエピソード
        project_name = "エラーテストプロジェクト"
        episode_number = 999

        # エピソード取得でエラーを発生させる
        self.mock_episode_repository.get_episode_content.side_effect = FileNotFoundError("エピソードが見つかりません")

        request = A31DetailedEvaluationRequest(project_name=project_name, episode_number=episode_number)

        # When
        response = self.use_case.execute(request)

        # Then
        assert response.success is False
        assert "エピソード 999 が見つかりません" in response.error_message
        assert response.overall_score == 0.0
        assert response.total_issues_found == 0

    @pytest.mark.spec("SPEC-DETAILED_EVALUATION_INTEGRATION-YAML_OUTPUT_FORMAT_I")
    def test_yaml_output_format_integration(self) -> None:
        """YAML出力形式統合テスト"""
        # Given
        project_name = "YAML出力テストプロジェクト"
        episode_number = 1

        # モックの設定
        self.mock_episode_repository.get_episode_content.return_value = self.test_episode_content
        self.mock_a31_checklist_repository.get_all_checklist_items.return_value = []

        request = A31DetailedEvaluationRequest(
            project_name=project_name, episode_number=episode_number, output_format="yaml", save_results=False
        )

        # When
        response = self.use_case.execute(request)

        # Then
        assert response.success is True
        assert response.yaml_output is not None

        # YAML出力の内容確認
        yaml_content = response.yaml_output
        assert "evaluation_summary:" in yaml_content
        assert "overall_score:" in yaml_content
        assert "category_results:" in yaml_content
        assert "line_feedback:" in yaml_content

        # 日本語が正しく含まれていることを確認
        assert "総合スコア" not in yaml_content  # 英語キーのはず
        assert str(response.overall_score) in yaml_content

    @pytest.mark.spec("SPEC-DETAILED_EVALUATION_INTEGRATION-PERFORMANCE_BENCHMAR")
    def test_performance_benchmark_integration(self) -> None:
        """パフォーマンスベンチマーク統合テスト"""
        # Given
        project_name = "パフォーマンステストプロジェクト"
        episode_number = 1

        # 長めのエピソード内容でテスト
        long_episode_content = self.test_episode_content * 10  # 10倍の長さ

        # モックの設定
        self.mock_episode_repository.get_episode_content.return_value = long_episode_content
        self.mock_a31_checklist_repository.get_all_checklist_items.return_value = []

        request = A31DetailedEvaluationRequest(
            project_name=project_name,
            episode_number=episode_number,
            target_categories=A31EvaluationCategory.get_all_core_categories(),
            save_results=False,
        )

        # When - 実行時間測定
        import time

        start_time = time.time()

        response = self.use_case.execute(request)

        end_time = time.time()
        execution_time = end_time - start_time

        # Then
        assert response.success is True
        assert execution_time < 10.0  # 10秒以内で完了
        assert response.execution_time_seconds > 0
        assert abs(response.execution_time_seconds - execution_time) < 1.0  # 実行時間の記録が正確
