"""統合執筆セッションエンティティのテスト
仕様: specs/integrated_writing_workflow.spec.md
"""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from noveler.domain.entities.integrated_writing_session import (
    IntegratedWritingSession,
    WritingSessionStatus,
    WritingWorkflowType,
)
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.yaml_prompt_content import YamlPromptContent, YamlPromptMetadata


@pytest.mark.spec("SPEC-IWW-001")
class TestIntegratedWritingSession:
    """統合執筆セッションエンティティのテスト"""

    @pytest.fixture
    def valid_episode_number(self) -> EpisodeNumber:
        """有効なエピソード番号"""
        return EpisodeNumber(13)

    @pytest.fixture
    def valid_project_root(self, tmp_path: Path) -> Path:
        """有効なプロジェクトルート"""
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        return project_root

    @pytest.fixture
    def valid_yaml_metadata(self) -> YamlPromptMetadata:
        """有効なYAMLメタデータ"""
        return YamlPromptMetadata(
            title="段階的執筆プロンプト: 第013話_テスト.md",
            project="../test_project",
            episode_file="第013話_テスト.md",
            genre="fantasy",
            word_count="3500",
            viewpoint="三人称単元視点",
            viewpoint_character="主人公",
            detail_level="stepwise",
            methodology="A30準拠10段階構造化執筆プロセス",
            generated_at="2025-08-05 19:00:00",
        )

    @pytest.fixture
    def valid_yaml_content(self, valid_yaml_metadata: YamlPromptMetadata) -> YamlPromptContent:
        """有効なYAMLコンテンツ"""
        yaml_string = """metadata:
  title: 段階的執筆プロンプト: 第013話_テスト.md
  genre: fantasy
  word_count: '3500'"""

        return YamlPromptContent.create_from_yaml_string(
            yaml_content=yaml_string, metadata=valid_yaml_metadata, custom_requirements=["テスト要件1", "テスト要件2"]
        )

    @pytest.mark.spec("SPEC-INTEGRATED_WRITING_SESSION-CREATE_SESSION_WITH_")
    def test_create_session_with_valid_data(
        self, valid_episode_number: EpisodeNumber, valid_project_root: Path
    ) -> None:
        """有効なデータでセッション作成成功"""
        session = IntegratedWritingSession(
            session_id="test-session-001",
            episode_number=valid_episode_number,
            project_root=valid_project_root,
            workflow_type=WritingWorkflowType.INTEGRATED,
        )

        assert session.session_id == "test-session-001"
        assert session.episode_number == valid_episode_number
        assert session.project_root == valid_project_root
        assert session.workflow_type == WritingWorkflowType.INTEGRATED
        assert session.status == WritingSessionStatus.INITIALIZED
        assert isinstance(session.created_at, datetime)
        assert session.yaml_prompt_content is None
        assert session.error_message is None
        assert not session.fallback_executed

    @pytest.mark.spec("SPEC-INTEGRATED_WRITING_SESSION-CREATE_SESSION_WITH_")
    def test_create_session_with_invalid_session_id(
        self, valid_episode_number: EpisodeNumber, valid_project_root: Path
    ) -> None:
        """無効なセッションIDでエラー"""
        with pytest.raises(ValueError, match="session_idは必須です"):
            IntegratedWritingSession(
                session_id="",
                episode_number=valid_episode_number,
                project_root=valid_project_root,
                workflow_type=WritingWorkflowType.INTEGRATED,
            )

    @pytest.mark.spec("SPEC-INTEGRATED_WRITING_SESSION-CREATE_SESSION_WITH_")
    def test_create_session_with_invalid_episode_number(self, valid_project_root: Path) -> None:
        """無効なエピソード番号でエラー"""
        with pytest.raises(ValueError, match="episode_numberはEpisodeNumber型である必要があります"):
            IntegratedWritingSession(
                session_id="test-session-001",
                episode_number=13,  # type: ignore - テスト用の型エラー
                project_root=valid_project_root,
                workflow_type=WritingWorkflowType.INTEGRATED,
            )

    @pytest.mark.spec("SPEC-INTEGRATED_WRITING_SESSION-CREATE_SESSION_WITH_")
    def test_create_session_with_nonexistent_project_root(self, valid_episode_number: EpisodeNumber) -> None:
        """存在しないプロジェクトルートでエラー"""
        nonexistent_path = Path("/nonexistent/path")

        with pytest.raises(ValueError, match="プロジェクトルートが存在しません"):
            IntegratedWritingSession(
                session_id="test-session-001",
                episode_number=valid_episode_number,
                project_root=nonexistent_path,
                workflow_type=WritingWorkflowType.INTEGRATED,
            )

    @pytest.mark.spec("SPEC-INTEGRATED_WRITING_SESSION-PROMPT_GENERATION_WO")
    def test_prompt_generation_workflow(
        self, valid_episode_number: EpisodeNumber, valid_project_root: Path, valid_yaml_content: YamlPromptContent
    ) -> None:
        """プロンプト生成ワークフローのテスト"""
        session = IntegratedWritingSession(
            session_id="test-session-001",
            episode_number=valid_episode_number,
            project_root=valid_project_root,
            workflow_type=WritingWorkflowType.INTEGRATED,
        )

        # プロンプト生成開始
        session.start_prompt_generation()
        assert session.status == WritingSessionStatus.PROMPT_GENERATED

        # プロンプト生成完了
        output_path = valid_project_root / "test_prompt.yaml"
        session.complete_prompt_generation(valid_yaml_content, output_path)

        assert session.yaml_prompt_content == valid_yaml_content
        assert session.yaml_output_path == output_path

    @pytest.mark.spec("SPEC-INTEGRATED_WRITING_SESSION-COMPLETE_WORKFLOW")
    def test_complete_workflow(
        self, valid_episode_number: EpisodeNumber, valid_project_root: Path, valid_yaml_content: YamlPromptContent
    ) -> None:
        """完全ワークフローのテスト"""
        session = IntegratedWritingSession(
            session_id="test-session-001",
            episode_number=valid_episode_number,
            project_root=valid_project_root,
            workflow_type=WritingWorkflowType.INTEGRATED,
        )

        # 各段階を順次実行
        session.start_prompt_generation()

        output_path = valid_project_root / "test_prompt.yaml"
        session.complete_prompt_generation(valid_yaml_content, output_path)

        manuscript_path = valid_project_root / "manuscript.md"
        session.complete_manuscript_creation(manuscript_path)
        assert session.status == WritingSessionStatus.MANUSCRIPT_CREATED

        session.complete_editor_opening()
        assert session.status == WritingSessionStatus.EDITOR_OPENED

        session.complete_session()
        assert session.status == WritingSessionStatus.COMPLETED
        assert session.is_completed()

    @pytest.mark.spec("SPEC-INTEGRATED_WRITING_SESSION-ERROR_HANDLING_WITH_")
    def test_error_handling_with_fallback(self, valid_episode_number: EpisodeNumber, valid_project_root: Path) -> None:
        """エラーハンドリングとフォールバックのテスト"""
        session = IntegratedWritingSession(
            session_id="test-session-001",
            episode_number=valid_episode_number,
            project_root=valid_project_root,
            workflow_type=WritingWorkflowType.INTEGRATED,
        )

        error_msg = "YAML生成に失敗しました"
        session.fail_with_error(error_msg, enable_fallback=True)

        assert session.status == WritingSessionStatus.FAILED
        assert session.error_message == error_msg
        assert session.fallback_executed
        assert session.is_failed()
        assert session.should_fallback_to_traditional()

    @pytest.mark.spec("SPEC-INTEGRATED_WRITING_SESSION-CUSTOM_REQUIREMENTS_")
    def test_custom_requirements_management(
        self, valid_episode_number: EpisodeNumber, valid_project_root: Path
    ) -> None:
        """カスタム要件管理のテスト"""
        session = IntegratedWritingSession(
            session_id="test-session-001",
            episode_number=valid_episode_number,
            project_root=valid_project_root,
            workflow_type=WritingWorkflowType.INTEGRATED,
        )

        # 要件追加
        session.add_custom_requirement("古代システム分析")
        session.add_custom_requirement("危険性証明")

        assert len(session.custom_requirements) == 2
        assert "古代システム分析" in session.custom_requirements
        assert "危険性証明" in session.custom_requirements

        # 重複追加の防止
        session.add_custom_requirement("古代システム分析")
        assert len(session.custom_requirements) == 2

    @pytest.mark.spec("SPEC-INTEGRATED_WRITING_SESSION-SESSION_DURATION_CAL")
    def test_session_duration_calculation(self, valid_episode_number: EpisodeNumber, valid_project_root: Path) -> None:
        """セッション実行時間計算のテスト"""
        with patch("noveler.domain.entities.integrated_writing_session.datetime") as mock_datetime:
            # 開始時間をモック
            start_time = datetime(2025, 8, 5, 19, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = start_time
            mock_datetime.timezone = timezone

            session = IntegratedWritingSession(
                session_id="test-session-001",
                episode_number=valid_episode_number,
                project_root=valid_project_root,
                workflow_type=WritingWorkflowType.INTEGRATED,
            )

            # 終了時間をモック（3秒後）
            end_time = datetime(2025, 8, 5, 19, 0, 3, tzinfo=timezone.utc)
            mock_datetime.now.return_value = end_time

            # 何らかの状態変更を実行
            session.start_prompt_generation()

            duration = session.get_session_duration_seconds()
            assert duration == 3.0
