"""エピソード完成セッションのユニットテスト

TDD原則に基づき、実装前にテストを作成。
"""

import pytest

from noveler.domain.entities.episode_completion_session import (
    CompletionResult,
    CompletionStatus,
    EpisodeCompletionSession,
    QualityCheckResult,
)
from noveler.domain.value_objects.completion_status import WritingPhase
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.value_objects.quality_score import QualityScore

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


@pytest.mark.spec("SPEC-QUALITY-014")
class TestEpisodeCompletionSession:
    """エピソード完成セッションのテスト"""

    @pytest.mark.spec("SPEC-EPISODE_COMPLETION_SESSION-UNNAMED")
    def test_unnamed(self) -> None:
        """完成セッションを作成できることを確認"""
        # Given
        episode_number = EpisodeNumber(1)
        project_name = "テストプロジェクト"

        # When
        session = EpisodeCompletionSession(
            episode_number=episode_number, project_name=project_name, current_phase=WritingPhase.DRAFT
        )

        # Then
        assert session.episode_number == episode_number
        assert session.project_name == project_name
        assert session.current_phase == WritingPhase.DRAFT
        assert session.get_status() == CompletionStatus.INITIALIZED

    @pytest.mark.spec("SPEC-EPISODE_COMPLETION_SESSION-UNNAMED")
    def test_basic_functionality(self) -> None:
        """執筆フェーズが正しく進行することを確認"""
        # Given
        session = EpisodeCompletionSession(
            episode_number=EpisodeNumber(1), project_name="テストプロジェクト", current_phase=WritingPhase.DRAFT
        )

        # When
        new_phase = session.advance_phase()

        # Then
        assert new_phase == WritingPhase.REVIEW
        assert session.current_phase == WritingPhase.REVIEW

    @pytest.mark.spec("SPEC-EPISODE_COMPLETION_SESSION-UNNAMED")
    def test_edge_cases(self) -> None:
        """エピソード完成処理が正しく実行されることを確認"""
        # Given
        session = EpisodeCompletionSession(
            episode_number=EpisodeNumber(1), project_name="テストプロジェクト", current_phase=WritingPhase.DRAFT
        )

        quality_result = QualityCheckResult(score=QualityScore(90), passed=True, issues=[])

        # When
        result = session.complete_episode(quality_result=quality_result, auto_advance_phase=True)

        # Then
        assert result.success is True
        assert result.new_phase == WritingPhase.REVIEW
        assert result.quality_score.value == 90
        assert session.get_status() == CompletionStatus.COMPLETED

    @pytest.mark.spec("SPEC-EPISODE_COMPLETION_SESSION-UNNAMED")
    def test_error_handling(self) -> None:
        """品質が低い場合の完成処理を確認"""
        # Given
        session = EpisodeCompletionSession(
            episode_number=EpisodeNumber(1), project_name="テストプロジェクト", current_phase=WritingPhase.DRAFT
        )

        quality_result = QualityCheckResult(
            score=QualityScore(60), passed=False, issues=["文章が冗長です", "誤字があります"]
        )

        # When
        result = session.complete_episode(quality_result=quality_result, auto_advance_phase=False)

        # Then
        assert result.success is True
        assert result.new_phase == WritingPhase.DRAFT  # フェーズは進まない
        assert result.quality_score.value == 60
        assert "品質スコアが低い" in result.message

    @pytest.mark.spec("SPEC-EPISODE_COMPLETION_SESSION-CHECK")
    def test_check(self) -> None:
        """品質チェックをスキップした場合の処理を確認"""
        # Given
        session = EpisodeCompletionSession(
            episode_number=EpisodeNumber(1), project_name="テストプロジェクト", current_phase=WritingPhase.REVIEW
        )

        # When
        result = session.complete_episode(quality_result=None, auto_advance_phase=True)

        # Then
        assert result.success is True
        assert result.new_phase == WritingPhase.FINAL_CHECK
        assert result.quality_score is None

    @pytest.mark.spec("SPEC-EPISODE_COMPLETION_SESSION-UNNAMED")
    def test_validation(self) -> None:
        """公開可能状態での完成処理を確認"""
        # Given
        session = EpisodeCompletionSession(
            episode_number=EpisodeNumber(1), project_name="テストプロジェクト", current_phase=WritingPhase.FINAL_CHECK
        )

        quality_result = QualityCheckResult(score=QualityScore(95), passed=True, issues=[])

        # When
        result = session.complete_episode(quality_result=quality_result, auto_advance_phase=True)

        # Then
        assert result.success is True
        assert result.new_phase == WritingPhase.PUBLISHED
        assert session.current_phase == WritingPhase.PUBLISHED
        assert session.is_publishable() is True

    @pytest.mark.spec("SPEC-EPISODE_COMPLETION_SESSION-UNNAMED")
    def test_integration(self) -> None:
        """既に公開済みの場合はフェーズが進まないことを確認"""
        # Given
        session = EpisodeCompletionSession(
            episode_number=EpisodeNumber(1), project_name="テストプロジェクト", current_phase=WritingPhase.PUBLISHED
        )

        # When
        result = session.complete_episode(quality_result=None, auto_advance_phase=True)

        # Then
        assert result.success is True
        assert result.new_phase == WritingPhase.PUBLISHED
        assert "既に公開済み" in result.message


@pytest.mark.spec("SPEC-QUALITY-014")
class TestCompletionResult:
    """完成結果のテスト"""

    @pytest.mark.spec("SPEC-EPISODE_COMPLETION_SESSION-UNNAMED")
    def test_performance(self) -> None:
        """成功結果が正しく作成されることを確認"""
        # When
        result = CompletionResult(
            success=True,
            new_phase=WritingPhase.REVIEW,
            quality_score=QualityScore(85),
            message="下書きが完了しました。",
            completed_at=project_now().datetime,
        )

        # Then
        assert result.success is True
        assert result.new_phase == WritingPhase.REVIEW
        assert result.quality_score.value == 85
        assert result.message == "下書きが完了しました。"
        assert result.completed_at is not None
        assert result.error is None

    @pytest.mark.spec("SPEC-EPISODE_COMPLETION_SESSION-UNNAMED")
    def test_configuration(self) -> None:
        """エラー結果が正しく作成されることを確認"""
        # When
        result = CompletionResult(success=False, error="エピソードが見つかりません")

        # Then
        assert result.success is False
        assert result.error == "エピソードが見つかりません"
        assert result.new_phase is None
        assert result.quality_score is None
