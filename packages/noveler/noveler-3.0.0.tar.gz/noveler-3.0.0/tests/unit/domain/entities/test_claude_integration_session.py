"""Claude連携セッションのテスト

SPEC-CLAUDE-001に基づくTDD実装
"""

from unittest.mock import Mock

import pytest

from noveler.domain.entities.claude_integration_session import (
    ClaudeIntegrationSession,
    ErrorCollection,
    SuggestionMetadata,
)
from noveler.domain.entities.file_quality_check_session import FileQualityCheckSession
from noveler.domain.value_objects.claude_session_id import ClaudeSessionId
from noveler.domain.value_objects.error_export_format import ErrorExportFormat, ExportFormatType
from noveler.domain.value_objects.file_path import FilePath


@pytest.mark.spec("SPEC-CLAUDE-001")
class TestClaudeIntegrationSession:
    """Claude連携セッションのテスト"""

    @pytest.mark.spec("SPEC-CLAUDE_INTEGRATION_SESSION-SESSION_ID_AUTO_GENE")
    def test_session_id_auto_generated_on_init(self) -> None:
        """セッションID未指定時の自動生成をテスト"""
        # Act
        session = ClaudeIntegrationSession()

        # Assert
        assert isinstance(session.session_id, ClaudeSessionId)
        assert session.session_id.value

    @pytest.mark.spec("SPEC-CLAUDE_INTEGRATION_SESSION-INITIALIZED_WITH_SPE")
    def test_initialized_with_specified_session_id(self) -> None:
        """指定セッションIDでの初期化をテスト"""
        # Arrange
        session_id = ClaudeSessionId.generate()

        # Act
        session = ClaudeIntegrationSession(session_id=session_id)

        # Assert
        assert session.session_id == session_id

    @pytest.mark.spec("SPEC-CLAUDE_INTEGRATION_SESSION-INITIAL_STATE_INACTI")
    def test_initial_state_inactive_with_empty_error_collection(self) -> None:
        """初期状態の確認"""
        # Act
        session = ClaudeIntegrationSession()

        # Assert
        assert not session.integration_status.is_active
        assert session.error_collection.total_errors == 0
        assert session.export_timestamp is None

    @pytest.mark.spec("SPEC-CLAUDE_INTEGRATION_SESSION-ERROR_STATS_UPDATED_")
    def test_error_stats_updated_when_quality_check_session_added(self) -> None:
        """エラー統計更新のテスト"""
        # Arrange
        session = ClaudeIntegrationSession()
        quality_session = self._create_mock_quality_session_with_errors(
            [{"code": "E999", "message": "構文エラー"}, {"code": "ANN001", "message": "型注釈なし"}]
        )

        # Act
        session.add_quality_sessions([quality_session])

        # Assert
        assert session.error_collection.total_errors == 2
        assert session.error_collection.syntax_errors == 1
        assert session.error_collection.type_errors == 1
        assert session.suggestion_metadata.estimated_fix_time_minutes == 7  # 5分+2分

    @pytest.mark.spec("SPEC-CLAUDE_INTEGRATION_SESSION-EXECUTE_JSON_FORMAT_")
    def test_execute_json_format_export(self) -> None:
        """JSON形式エクスポートのテスト"""
        # Arrange
        session = ClaudeIntegrationSession()
        quality_session = self._create_mock_quality_session_with_errors(
            [{"code": "E999", "message": "構文エラー", "line_number": 10}]
        )
        session.add_quality_sessions([quality_session])
        format_config = ErrorExportFormat.json_format()

        # Act
        result = session.export_for_claude(format_config)

        # Assert
        assert "session_id" in result
        assert "timestamp" in result
        assert "errors" in result
        assert "summary" in result
        assert len(result["errors"]) == 1
        assert result["errors"][0]["error_type"] == "syntax"
        assert result["errors"][0]["priority"] == "high"
        assert result["summary"]["total"] == 1

    @pytest.mark.spec("SPEC-CLAUDE_INTEGRATION_SESSION-STATE_UPDATED_ON_EXP")
    def test_state_updated_on_export_success(self) -> None:
        """エクスポート成功時の状態更新テスト"""
        # Arrange
        session = ClaudeIntegrationSession()
        format_config = ErrorExportFormat.json_format()

        # Act
        session.export_for_claude(format_config)

        # Assert
        assert session.integration_status.success_count == 1
        assert session.integration_status.error_count == 0
        assert session.export_timestamp is not None
        assert session.suggestion_metadata.format_used == format_config

    @pytest.mark.spec("SPEC-CLAUDE_INTEGRATION_SESSION-ERROR_STATE_UPDATED_")
    def test_error_state_updated_on_export_failure(self) -> None:
        """エクスポート失敗時の状態更新テスト"""
        # Arrange
        session = ClaudeIntegrationSession()
        # 意図的にエラーを発生させるためのモック設定
        session._create_export_data = Mock(side_effect=Exception("テストエラー"))
        format_config = ErrorExportFormat.json_format()

        # Act & Assert
        with pytest.raises(Exception, match="テストエラー"):
            session.export_for_claude(format_config)

        assert session.integration_status.error_count == 1
        assert session.integration_status.last_error_message == "テストエラー"

    @pytest.mark.spec("SPEC-CLAUDE_INTEGRATION_SESSION-HIGH_PRIORITY_ERROR_")
    def test_high_priority_error_filtering(self) -> None:
        """高優先度エラーのフィルタリングテスト"""
        # Arrange
        session = ClaudeIntegrationSession()
        quality_session = self._create_mock_quality_session_with_errors(
            [
                {"code": "E999", "message": "構文エラー"},  # high
                {"code": "ANN001", "message": "型注釈なし"},  # medium
                {"code": "W503", "message": "スタイル警告"},  # low
            ]
        )
        session.add_quality_sessions([quality_session])

        # Act
        high_priority_sessions = session.error_collection.get_high_priority_sessions()

        # Assert
        assert len(high_priority_sessions) == 1

    @pytest.mark.spec("SPEC-CLAUDE_INTEGRATION_SESSION-EXPORT_WITH_PRIORITY")
    def test_export_with_priority_filter_applied(self) -> None:
        """優先度フィルタ適用エクスポートのテスト"""
        # Arrange
        session = ClaudeIntegrationSession()
        quality_session = self._create_mock_quality_session_with_errors(
            [
                {"code": "E999", "message": "構文エラー"},  # high
                {"code": "ANN001", "message": "型注釈なし"},  # medium
            ]
        )
        session.add_quality_sessions([quality_session])

        format_config = ErrorExportFormat(
            format_type=ExportFormatType.JSON, structure_version="1.0", priority_filter="high"
        )

        # Act
        result = session.export_for_claude(format_config)

        # Assert
        assert len(result["errors"]) == 1  # 高優先度のみ
        assert result["errors"][0]["priority"] == "high"

    @pytest.mark.spec("SPEC-CLAUDE_INTEGRATION_SESSION-APPLY_FILE_ERROR_LIM")
    def test_apply_file_error_limit(self) -> None:
        """ファイル別エラー数制限のテスト"""
        # Arrange
        session = ClaudeIntegrationSession()
        errors = [{"code": f"E{i:03d}", "message": f"エラー{i}"} for i in range(15)]
        quality_session = self._create_mock_quality_session_with_errors(errors)
        session.add_quality_sessions([quality_session])

        format_config = ErrorExportFormat(
            format_type=ExportFormatType.JSON, structure_version="1.0", max_errors_per_file=5
        )

        # Act
        result = session.export_for_claude(format_config)

        # Assert
        assert len(result["errors"]) == 5  # 制限が適用される

    @pytest.mark.spec("SPEC-CLAUDE_INTEGRATION_SESSION-INTEGRATION_ACTIVATI")
    def test_integration_activation_and_deactivation(self) -> None:
        """連携状態の変更テスト"""
        # Arrange
        session = ClaudeIntegrationSession()

        # Act & Assert - アクティベーション
        session.activate_integration()
        assert session.integration_status.is_active

        # Act & Assert - 非アクティベーション
        session.deactivate_integration()
        assert not session.integration_status.is_active

    @pytest.mark.spec("SPEC-CLAUDE_INTEGRATION_SESSION-UNNAMED")
    def test_unnamed(self) -> None:
        """エクスポート概要取得のテスト"""
        # Arrange
        session = ClaudeIntegrationSession()
        quality_session = self._create_mock_quality_session_with_errors([{"code": "E999", "message": "構文エラー"}])
        session.add_quality_sessions([quality_session])
        session.activate_integration()

        # Act
        summary = session.get_export_summary()

        # Assert
        assert "session_id" in summary
        assert summary["is_active"] is True
        assert summary["total_errors"] == 1
        assert summary["has_high_priority"] is True
        assert "estimated_fix_time" in summary

    @pytest.mark.spec("SPEC-CLAUDE_INTEGRATION_SESSION-GENERATE_CORRECTION_")
    def test_generate_correction_suggestions(self) -> None:
        """修正提案生成のテスト"""
        # Arrange
        session = ClaudeIntegrationSession()

        # Act & Assert - 構文エラー
        suggestion = session._generate_suggestion({"code": "E999"})
        assert "構文エラー" in suggestion

        # Act & Assert - 型注釈エラー
        suggestion = session._generate_suggestion({"code": "ANN001"})
        assert "型注釈" in suggestion

        # Act & Assert - 未知のエラー
        suggestion = session._generate_suggestion({"code": "UNKNOWN"})
        assert "UNKNOWN" in suggestion

    @pytest.mark.spec("SPEC-CLAUDE_INTEGRATION_SESSION-EXCEPTION_ON_INVALID")
    def test_exception_on_invalid_value_initialization(self) -> None:
        """不正な値での初期化時の例外テスト"""
        # Act & Assert
        with pytest.raises(TypeError, match=".*"):
            session = ClaudeIntegrationSession()
            session.session_id = "不正な値"  # type: ignore
            session._validate_entity()

    def _create_mock_quality_session_with_errors(self, errors: list[dict]) -> FileQualityCheckSession:
        """エラーを持つモック品質チェックセッション作成

        Args:
            errors: エラー情報のリスト

        Returns:
            モック品質チェックセッション
        """
        mock_session = Mock(spec=FileQualityCheckSession)
        mock_session.file_path = FilePath("test_file.py")
        mock_session.has_errors.return_value = len(errors) > 0
        mock_session.get_error_details.return_value = errors
        return mock_session


@pytest.mark.spec("SPEC-CLAUDE-001")
class TestErrorCollection:
    """エラーコレクションのテスト"""

    @pytest.mark.spec("SPEC-CLAUDE_INTEGRATION_SESSION-INITIAL_STATE_EMPTY_")
    def test_initial_state_empty_collection(self) -> None:
        """初期状態の確認"""
        # Act
        collection = ErrorCollection()

        # Assert
        assert collection.total_errors == 0
        assert collection.syntax_errors == 0
        assert collection.type_errors == 0
        assert collection.style_errors == 0
        assert not collection.has_errors()

    @pytest.mark.spec("SPEC-CLAUDE_INTEGRATION_SESSION-STATS_UPDATED_WHEN_Q")
    def test_stats_updated_when_quality_session_added(self) -> None:
        """品質セッション追加での統計更新テスト"""
        # Arrange
        collection = ErrorCollection()
        mock_session = Mock(spec=FileQualityCheckSession)
        mock_session.has_errors.return_value = True
        mock_session.get_error_details.return_value = [
            {"code": "E999", "message": "構文エラー"},
            {"code": "ANN001", "message": "型注釈エラー"},
        ]

        # Act
        collection.add_quality_session(mock_session)

        # Assert
        assert collection.total_errors == 2
        assert collection.syntax_errors == 1
        assert collection.type_errors == 1
        assert collection.has_errors()

    @pytest.mark.spec("SPEC-CLAUDE_INTEGRATION_SESSION-DUPLICATE_IS_DONE")
    def test_duplicate_is_done(self) -> None:
        """重複セッション追加の防止テスト"""
        # Arrange
        collection = ErrorCollection()
        mock_session = Mock(spec=FileQualityCheckSession)
        mock_session.has_errors.return_value = True
        mock_session.get_error_details.return_value = [{"code": "E999"}]

        # Act
        collection.add_quality_session(mock_session)
        collection.add_quality_session(mock_session)  # 重複追加

        # Assert
        assert len(collection.quality_sessions) == 1
        assert collection.total_errors == 1

    @pytest.mark.spec("SPEC-CLAUDE_INTEGRATION_SESSION-IS_DONE")
    def test_is_done(self) -> None:
        """品質セッション削除での統計更新テスト"""
        # Arrange
        collection = ErrorCollection()
        mock_session = Mock(spec=FileQualityCheckSession)
        mock_session.has_errors.return_value = True
        mock_session.get_error_details.return_value = [{"code": "E999"}]

        collection.add_quality_session(mock_session)

        # Act
        collection.remove_quality_session(mock_session)

        # Assert
        assert collection.total_errors == 0
        assert not collection.has_errors()


@pytest.mark.spec("SPEC-CLAUDE-001")
class TestSuggestionMetadata:
    """修正提案メタデータのテスト"""

    @pytest.mark.spec("SPEC-CLAUDE_INTEGRATION_SESSION-UNNAMED")
    def test_unnamed(self) -> None:
        """修正時間計算のテスト"""
        # Arrange
        metadata = SuggestionMetadata()
        collection = ErrorCollection()
        collection.syntax_errors = 2  # 2 * 5分 = 10分
        collection.type_errors = 3  # 3 * 2分 = 6分
        collection.style_errors = 1  # 1 * 1分 = 1分
        collection.total_errors = 6

        # Act
        metadata.calculate_fix_time(collection)

        # Assert
        assert metadata.estimated_fix_time_minutes == 17  # 10+6+1
        assert metadata.suggestion_count == 6
