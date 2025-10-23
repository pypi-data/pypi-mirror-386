#!/usr/bin/env python3
"""YamlDetailedEvaluationRepository インフラ層単体テスト

TDD Red フェーズ: YAML詳細評価リポジトリの失敗テスト
詳細評価セッションと分析結果のYAML永続化機能をテスト
"""

import tempfile
from pathlib import Path

import pytest

from noveler.domain.entities.category_analysis_result import CategoryAnalysisResult
from noveler.domain.entities.detailed_evaluation_session import DetailedEvaluationSession, EvaluationSessionStatus
from noveler.domain.services.detailed_analysis_engine import DetailedAnalysisResult
from noveler.domain.value_objects.a31_evaluation_category import A31EvaluationCategory
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.improvement_suggestion import ImprovementSuggestion
from noveler.domain.value_objects.line_specific_feedback import IssueSeverity, IssueType, LineSpecificFeedback
from noveler.infrastructure.repositories.yaml_detailed_evaluation_repository import (
    YamlDetailedEvaluationRepository,
)


@pytest.mark.spec("SPEC-A31-DET-001")
class TestYamlDetailedEvaluationRepository:
    """YamlDetailedEvaluationRepository インフラ層テスト"""

    def setup_method(self) -> None:
        """テストセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.repository = YamlDetailedEvaluationRepository(self.temp_dir)

        # テスト用エリアルデータ
        self.test_project_name = "テストプロジェクト"
        self.test_episode_number = EpisodeNumber(1)
        self.test_episode_content = """# 第001話 テストエピソード

「こんにちは」と彼女は言った。

俺は驚いた。だった。だった。

彼女の笑顔が美しかった。"""

    def teardown_method(self) -> None:
        """テストクリーンアップ"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_and_load_evaluation_session_successfully(self) -> None:
        """評価セッションの保存と読み込みが正常に動作する"""
        # Given
        session = DetailedEvaluationSession.create(
            project_name=self.test_project_name,
            episode_number=self.test_episode_number,
            episode_content=self.test_episode_content,
        )

        session.start_evaluation()

        # カテゴリ分析結果を追加
        category_result = CategoryAnalysisResult.create(
            category=A31EvaluationCategory.STYLE_CONSISTENCY,
            score=75.0,
            issues_found=["文末単調性問題"],
            suggestions=["文末バリエーションを増やす"],
        )

        session.add_category_analysis(category_result)

        # When - 保存
        self.repository.save_evaluation_session(session)

        # Then - 読み込み確認
        loaded_session = self.repository.get_evaluation_session(self.test_project_name, self.test_episode_number)

        assert loaded_session is not None
        assert loaded_session.project_name == self.test_project_name
        assert loaded_session.episode_number == self.test_episode_number
        assert loaded_session.episode_content == self.test_episode_content
        assert loaded_session.status == EvaluationSessionStatus.IN_PROGRESS
        assert len(loaded_session.category_analyses) == 1
        assert loaded_session.category_analyses[0].category == A31EvaluationCategory.STYLE_CONSISTENCY

    def test_save_and_load_analysis_result_with_line_feedbacks(self) -> None:
        """行別フィードバック付き分析結果の保存と読み込み"""
        # Given
        session_id = "test-session-123"

        # カテゴリ分析結果作成
        category_result = CategoryAnalysisResult.create(
            category=A31EvaluationCategory.CONTENT_BALANCE,
            score=82.5,
            issues_found=["会話バランス問題"],
            suggestions=["地の文を追加"],
        )

        # 行別フィードバック作成
        improvement_suggestion = ImprovementSuggestion.create(
            content="この箇所に状況説明を追加してください",
            suggestion_type="content_enhancement",
            confidence=0.9,
            fix_example="「こんにちは」と彼女は笑顔で言った。朝の光が彼女の髪を照らしている。",
        )

        line_feedback = LineSpecificFeedback.create(
            line_number=3,
            original_text="「こんにちは」と彼女は言った。",
            issue_type=IssueType.CONTENT_BALANCE.value,
            severity=IssueSeverity.MINOR.value,
            suggestion=improvement_suggestion.content,
            confidence=0.9,
            context_lines=["# 第001話 テストエピソード", "", "「こんにちは」と彼女は言った。", "", "俺は驚いた。"],
        )

        # 分析結果作成
        analysis_result = DetailedAnalysisResult(
            session_id=session_id,
            overall_score=78.2,
            category_results=[category_result],
            line_feedbacks=[line_feedback],
            confidence_score=0.85,
            analysis_summary={"total_issues": 1, "total_suggestions": 1, "analysis_depth": "comprehensive"},
        )

        # When - 保存
        self.repository.save_analysis_result(analysis_result)

        # Then - 読み込み確認
        loaded_result = self.repository.get_analysis_result(session_id)

        assert loaded_result is not None
        assert loaded_result.session_id == session_id
        assert loaded_result.overall_score == 78.2
        assert loaded_result.confidence_score == 0.85
        assert len(loaded_result.category_results) == 1
        assert len(loaded_result.line_feedbacks) == 1

        # カテゴリ結果詳細確認
        loaded_category = loaded_result.category_results[0]
        assert loaded_category.category == A31EvaluationCategory.CONTENT_BALANCE
        assert loaded_category.score == 82.5

        # 行フィードバック詳細確認
        loaded_feedback = loaded_result.line_feedbacks[0]
        assert loaded_feedback.line_number == 3
        assert loaded_feedback.issue_type == IssueType.CONTENT_BALANCE
        assert loaded_feedback.severity == IssueSeverity.MINOR

    def test_list_evaluation_sessions_returns_sorted_episodes(self) -> None:
        """評価セッション一覧がエピソード番号順でソートされて返される"""
        # Given - 複数のエピソードセッションを作成
        episodes = [3, 1, 5, 2]
        sessions = []

        for ep_num in episodes:
            session = DetailedEvaluationSession.create(
                project_name=self.test_project_name,
                episode_number=EpisodeNumber(ep_num),
                episode_content=f"エピソード{ep_num}の内容",
            )

            sessions.append(session)
            self.repository.save_evaluation_session(session)

        # When
        loaded_sessions = self.repository.list_evaluation_sessions(self.test_project_name)

        # Then
        assert len(loaded_sessions) == 4
        episode_numbers = [session.episode_number.value for session in loaded_sessions]
        assert episode_numbers == [1, 2, 3, 5]  # ソートされている

    def test_delete_evaluation_session_removes_files(self) -> None:
        """評価セッション削除でファイルが削除される"""
        # Given
        session = DetailedEvaluationSession.create(
            project_name=self.test_project_name,
            episode_number=self.test_episode_number,
            episode_content=self.test_episode_content,
        )

        self.repository.save_evaluation_session(session)

        # 存在確認
        assert self.repository.exists_evaluation_session(self.test_project_name, self.test_episode_number) is True

        # When
        result = self.repository.delete_evaluation_session(self.test_project_name, self.test_episode_number)

        # Then
        assert result is True
        assert self.repository.exists_evaluation_session(self.test_project_name, self.test_episode_number) is False

        # 読み込み不可確認
        loaded_session = self.repository.get_evaluation_session(self.test_project_name, self.test_episode_number)

        assert loaded_session is None

    def test_sanitize_filename_handles_unsafe_characters(self) -> None:
        """ファイル名の危険文字がサニタイズされる"""
        # Given
        unsafe_project_name = 'プロジェクト<>:"/\\|?*'

        # When
        safe_filename = self.repository._sanitize_filename(unsafe_project_name)

        # Then
        assert safe_filename == "プロジェクト_________"
        assert not any(char in safe_filename for char in '<>:"/\\|?*')

    def test_handle_nonexistent_files_gracefully(self) -> None:
        """存在しないファイルの操作が適切に処理される"""
        # Given - 存在しないセッション
        nonexistent_episode = EpisodeNumber(999)

        # When & Then - 存在しないセッションの取得
        session = self.repository.get_evaluation_session(self.test_project_name, nonexistent_episode)

        assert session is None

        # When & Then - 存在しないセッションの削除
        result = self.repository.delete_evaluation_session(self.test_project_name, nonexistent_episode)

        assert result is False

        # When & Then - 存在しない分析結果の取得
        analysis_result = self.repository.get_analysis_result("nonexistent-session")
        assert analysis_result is None

    def test_yaml_serialization_preserves_unicode_content(self) -> None:
        """YAML シリアライゼーションでUnicode内容が保持される"""
        # Given - 日本語を含むセッション
        japanese_content = """# 第001話 桜咲く季節

「お疲れさまでした」と彼女は深々と頭を下げた。

私の心は温かくなった。これこそが求めていた瞬間だった。"""

        session = DetailedEvaluationSession.create(
            project_name="日本語プロジェクト", episode_number=EpisodeNumber(1), episode_content=japanese_content
        )

        # When
        self.repository.save_evaluation_session(session)
        loaded_session = self.repository.get_evaluation_session("日本語プロジェクト", EpisodeNumber(1))

        # Then
        assert loaded_session is not None
        assert loaded_session.episode_content == japanese_content
        assert loaded_session.project_name == "日本語プロジェクト"

    def test_repository_directory_creation(self) -> None:
        """リポジトリの必要ディレクトリが自動作成される"""
        # Given - 新しい一時ディレクトリ
        new_temp_dir = Path(tempfile.mkdtemp()) / "new_repo_location"

        # When - 新しいリポジトリ作成
        YamlDetailedEvaluationRepository(str(new_temp_dir))

        # Then - ディレクトリが存在することを確認
        assert (new_temp_dir / "sessions").exists()
        assert (new_temp_dir / "results").exists()

        # クリーンアップ
        import shutil

        shutil.rmtree(new_temp_dir.parent, ignore_errors=True)

    def test_concurrent_access_safety(self) -> None:
        """同時アクセス時の安全性確認"""
        # Given
        session1 = DetailedEvaluationSession.create(
            project_name=self.test_project_name, episode_number=EpisodeNumber(1), episode_content="セッション1"
        )

        session2 = DetailedEvaluationSession.create(
            project_name=self.test_project_name, episode_number=EpisodeNumber(2), episode_content="セッション2"
        )

        # When - 同時保存
        self.repository.save_evaluation_session(session1)
        self.repository.save_evaluation_session(session2)

        # Then - 両方とも正常に保存・読み込み可能
        loaded1 = self.repository.get_evaluation_session(self.test_project_name, EpisodeNumber(1))

        loaded2 = self.repository.get_evaluation_session(self.test_project_name, EpisodeNumber(2))

        assert loaded1 is not None
        assert loaded2 is not None
        assert loaded1.episode_content == "セッション1"
        assert loaded2.episode_content == "セッション2"
