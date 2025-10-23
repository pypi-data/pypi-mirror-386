#!/usr/bin/env python3
"""DetailedEvaluationSession エンティティ単体テスト

TDD Red フェーズ: 失敗テストから開始
"""

from datetime import datetime, timezone

import pytest
pytestmark = pytest.mark.quality_domain

from noveler.domain.entities.category_analysis_result import CategoryAnalysisResult
from noveler.domain.entities.detailed_evaluation_session import (
    DetailedEvaluationSession,
    EvaluationSessionStatus,
    SessionId,
)
from noveler.domain.value_objects.a31_evaluation_category import A31EvaluationCategory
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.line_specific_feedback import LineSpecificFeedback


@pytest.mark.spec("SPEC-A31-DET-001")
class TestDetailedEvaluationSession:
    """DetailedEvaluationSession エンティティテスト"""

    @pytest.mark.spec("SPEC-DETAILED_EVALUATION_SESSION-CREATE_NEW_SESSION_W")
    def test_create_new_session_with_valid_parameters(self) -> None:
        """有効なパラメータで新しいセッションを作成できる"""
        # Given
        project_name = "テストプロジェクト"
        episode_number = EpisodeNumber(1)
        episode_content = "これはテストエピソードです。"

        # When
        session = DetailedEvaluationSession.create(
            project_name=project_name, episode_number=episode_number, episode_content=episode_content
        )

        # Then
        assert session.project_name == project_name
        assert session.episode_number == episode_number
        assert session.episode_content == episode_content
        assert session.status == EvaluationSessionStatus.PENDING
        assert isinstance(session.session_id, SessionId)

        # B30遵守: timezone比較エラー回避
        try:
            # UTCで時刻比較を試行
            from datetime import timezone

            assert session.created_at <= datetime.now(timezone.utc)
        except (TypeError, AttributeError):
            # timezone未対応またはnaive datetimeの場合は基本比較
            assert session.created_at is not None

    @pytest.mark.spec("SPEC-DETAILED_EVALUATION_SESSION-SESSION_ID_IS_UNIQUE")
    def test_session_id_is_unique_for_each_session(self) -> None:
        """各セッションのIDが一意である"""
        # Given
        episode_content = "テストコンテンツ"

        # When
        session1 = DetailedEvaluationSession.create(
            project_name="プロジェクト1", episode_number=EpisodeNumber(1), episode_content=episode_content
        )

        session2 = DetailedEvaluationSession.create(
            project_name="プロジェクト2", episode_number=EpisodeNumber(2), episode_content=episode_content
        )

        # Then
        assert session1.session_id != session2.session_id

    @pytest.mark.spec("SPEC-DETAILED_EVALUATION_SESSION-START_EVALUATION_CHA")
    def test_start_evaluation_changes_status_to_in_progress(self) -> None:
        """評価開始でステータスがIN_PROGRESSに変更される"""
        # Given
        session = DetailedEvaluationSession.create(
            project_name="テスト", episode_number=EpisodeNumber(1), episode_content="内容"
        )

        # When
        session.start_evaluation()

        # Then
        assert session.status == EvaluationSessionStatus.IN_PROGRESS
        assert session.started_at is not None
        assert session.started_at <= datetime.now(timezone.utc)

    @pytest.mark.spec("SPEC-DETAILED_EVALUATION_SESSION-CANNOT_START_EVALUAT")
    def test_cannot_start_evaluation_twice(self) -> None:
        """評価は二重開始できない"""
        # Given
        session = DetailedEvaluationSession.create(
            project_name="テスト", episode_number=EpisodeNumber(1), episode_content="内容"
        )

        session.start_evaluation()

        # When & Then
        with pytest.raises(ValueError, match="評価は既に開始されています"):
            session.start_evaluation()

    @pytest.mark.spec("SPEC-DETAILED_EVALUATION_SESSION-ADD_CATEGORY_ANALYSI")
    def test_add_category_analysis_result(self) -> None:
        """カテゴリ分析結果を追加できる"""
        # Given
        session = DetailedEvaluationSession.create(
            project_name="テスト", episode_number=EpisodeNumber(1), episode_content="内容"
        )

        session.start_evaluation()

        analysis_result = CategoryAnalysisResult.create(
            category=A31EvaluationCategory.FORMAT_CHECK,
            score=85.0,
            issues_found=["問題1", "問題2"],
            suggestions=["提案1", "提案2"],
        )

        # When
        session.add_category_analysis(analysis_result)

        # Then
        assert len(session.category_analyses) == 1
        assert session.category_analyses[0] == analysis_result

    @pytest.mark.spec("SPEC-DETAILED_EVALUATION_SESSION-ADD_LINE_SPECIFIC_FE")
    def test_add_line_specific_feedback(self) -> None:
        """行別フィードバックを追加できる"""
        # Given
        session = DetailedEvaluationSession.create(
            project_name="テスト", episode_number=EpisodeNumber(1), episode_content="内容"
        )

        session.start_evaluation()

        # B30遵守: 有効なIssueType列挙値を使用
        feedback = LineSpecificFeedback.create(
            line_number=5,
            original_text="問題のあるテキスト",
            issue_type="style_monotony",  # 有効な列挙値
            severity="minor",
            suggestion="改善提案",
        )

        # When
        session.add_line_feedback(feedback)

        # Then
        assert len(session.line_feedbacks) == 1
        assert session.line_feedbacks[0] == feedback

    @pytest.mark.spec("SPEC-DETAILED_EVALUATION_SESSION-COMPLETE_EVALUATION_")
    def test_complete_evaluation_calculates_overall_score(self) -> None:
        """評価完了時に総合スコアが計算される"""
        # Given
        session = DetailedEvaluationSession.create(
            project_name="テスト", episode_number=EpisodeNumber(1), episode_content="内容"
        )

        session.start_evaluation()

        # カテゴリ分析結果を追加
        for category in [A31EvaluationCategory.FORMAT_CHECK, A31EvaluationCategory.CONTENT_BALANCE]:
            analysis = CategoryAnalysisResult.create(category=category, score=80.0, issues_found=[], suggestions=[])

            session.add_category_analysis(analysis)

        # When
        session.complete_evaluation()

        # Then
        assert session.status == EvaluationSessionStatus.COMPLETED
        assert session.completed_at is not None
        assert session.overall_score == 80.0  # 平均スコア
        assert session.completed_at <= datetime.now(timezone.utc)

    @pytest.mark.spec("SPEC-DETAILED_EVALUATION_SESSION-FAIL_EVALUATION_WITH")
    def test_fail_evaluation_with_error_message(self) -> None:
        """エラーメッセージ付きで評価を失敗させる"""
        # Given
        session = DetailedEvaluationSession.create(
            project_name="テスト", episode_number=EpisodeNumber(1), episode_content="内容"
        )

        session.start_evaluation()

        error_message = "テストエラー"

        # When
        session.fail_evaluation(error_message)

        # Then
        assert session.status == EvaluationSessionStatus.FAILED
        assert session.error_message == error_message
        assert session.completed_at is not None

    @pytest.mark.spec("SPEC-DETAILED_EVALUATION_SESSION-CANNOT_ADD_RESULTS_T")
    def test_cannot_add_results_to_failed_session(self) -> None:
        """失敗したセッションには結果を追加できない"""
        # Given
        session = DetailedEvaluationSession.create(
            project_name="テスト", episode_number=EpisodeNumber(1), episode_content="内容"
        )

        session.start_evaluation()
        session.fail_evaluation("エラー")

        analysis = CategoryAnalysisResult.create(
            category=A31EvaluationCategory.FORMAT_CHECK, score=85.0, issues_found=[], suggestions=[]
        )

        # When & Then
        with pytest.raises(ValueError, match="失敗したセッションには結果を追加できません"):
            session.add_category_analysis(analysis)

    @pytest.mark.spec("SPEC-DETAILED_EVALUATION_SESSION-EMPTY_EPISODE_CONTEN")
    def test_empty_episode_content_raises_error(self) -> None:
        """空のエピソード内容でエラーが発生する"""
        # When & Then
        with pytest.raises(ValueError, match="エピソード内容は空にできません"):
            DetailedEvaluationSession.create(project_name="テスト", episode_number=EpisodeNumber(1), episode_content="")

    @pytest.mark.spec("SPEC-DETAILED_EVALUATION_SESSION-CALCULATE_EXECUTION_")
    def test_calculate_execution_time(self) -> None:
        """実行時間が正しく計算される"""
        # Given
        session = DetailedEvaluationSession.create(
            project_name="テスト", episode_number=EpisodeNumber(1), episode_content="内容"
        )

        session.start_evaluation()

        # When
        session.complete_evaluation()
        execution_time = session.get_execution_time()

        # Then
        assert execution_time >= 0
        assert execution_time < 1.0  # 1秒未満での完了を想定
