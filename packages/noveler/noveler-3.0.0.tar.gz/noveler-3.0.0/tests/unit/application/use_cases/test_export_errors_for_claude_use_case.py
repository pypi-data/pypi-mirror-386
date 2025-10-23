#!/usr/bin/env python3
"""Claude向けエラー出力ユースケース テスト

SPEC-CLAUDE-002に基づくTDD実装
"""

from unittest.mock import AsyncMock, Mock

import pytest

from noveler.application.use_cases.export_errors_for_claude_use_case import ExportErrorsForClaudeUseCase
from noveler.domain.entities.claude_integration_session import ClaudeIntegrationSession
from noveler.domain.entities.file_quality_check_session import FileQualityCheckSession
from noveler.domain.value_objects.error_export_format import ErrorExportFormat, ExportFormatType
from noveler.domain.value_objects.file_path import FilePath
from noveler.infrastructure.adapters.claude_code_adapter import ClaudeCodeAdapter


class TestExportErrorsForClaudeUseCase:
    """Claude向けエラー出力ユースケース テストクラス

    SPEC-CLAUDE-002に基づくTDD実装
    """

    @pytest.mark.spec("SPEC-CLAUDE-002")
    def test_should_exist(self):
        """ユースケースクラスが存在することを確認"""
        # RED段階: まだ実装されていないので失敗
        assert ExportErrorsForClaudeUseCase

    @pytest.mark.spec("SPEC-CLAUDE-002")
    async def test_execute_export_with_no_errors(self):
        """エラーがない場合のエクスポート実行"""
        # Arrange
        mock_session_repo = Mock()
        mock_session_repo.find_recent_sessions = AsyncMock(return_value=[])

        mock_format_service = Mock()
        mock_adapter = Mock(spec=ClaudeCodeAdapter)

        use_case = ExportErrorsForClaudeUseCase(
            session_repository=mock_session_repo, format_service=mock_format_service, claude_adapter=mock_adapter
        )

        # Act
        result = await use_case.execute_export()

        # Assert
        assert isinstance(result, ClaudeIntegrationSession)
        assert result.error_collection.total_errors == 0

    @pytest.mark.spec("SPEC-CLAUDE-002")
    async def test_execute_export_with_syntax_errors(self):
        """構文エラーがある場合のエクスポート実行"""
        # Arrange
        error_session = self._create_error_session()

        mock_session_repo = Mock()
        mock_session_repo.find_recent_sessions = AsyncMock(return_value=[error_session])

        mock_format_service = Mock()
        mock_adapter = Mock(spec=ClaudeCodeAdapter)
        mock_adapter.export_errors_for_claude = Mock()

        use_case = ExportErrorsForClaudeUseCase(
            session_repository=mock_session_repo, format_service=mock_format_service, claude_adapter=mock_adapter
        )

        # Act
        result = await use_case.execute_export()

        # Assert
        assert isinstance(result, ClaudeIntegrationSession)
        assert result.error_collection.total_errors > 0
        mock_adapter.export_errors_for_claude.assert_called_once()

    @pytest.mark.spec("SPEC-CLAUDE-002")
    async def test_export_file_errors_specific_file(self):
        """特定ファイルのエラー出力"""
        # Arrange
        file_path = FilePath("noveler/test_error_file.py")
        error_session = self._create_error_session(file_path)

        mock_session_repo = Mock()
        mock_session_repo.find_by_file_path = AsyncMock(return_value=[error_session])

        mock_format_service = Mock()
        mock_adapter = Mock(spec=ClaudeCodeAdapter)
        mock_adapter.export_errors_for_claude = Mock()

        use_case = ExportErrorsForClaudeUseCase(
            session_repository=mock_session_repo, format_service=mock_format_service, claude_adapter=mock_adapter
        )

        # Act
        result = await use_case.export_file_errors(file_path)

        # Assert
        assert isinstance(result, ClaudeIntegrationSession)
        mock_session_repo.find_by_file_path.assert_called_once_with(file_path)
        mock_adapter.export_errors_for_claude.assert_called_once()

    @pytest.mark.spec("SPEC-CLAUDE-002")
    async def test_export_recent_errors_incremental(self):
        """増分エラー出力(最近のエラーのみ)"""
        # Arrange
        recent_session = self._create_error_session()

        mock_session_repo = Mock()
        mock_session_repo.find_since_timestamp = AsyncMock(return_value=[recent_session])

        mock_format_service = Mock()
        mock_adapter = Mock(spec=ClaudeCodeAdapter)
        mock_adapter.get_claude_integration_status = Mock(return_value={"last_updated": "2025-07-28T10:00:00"})

        mock_adapter.export_errors_for_claude = Mock()

        use_case = ExportErrorsForClaudeUseCase(
            session_repository=mock_session_repo, format_service=mock_format_service, claude_adapter=mock_adapter
        )

        # Act
        result = await use_case.export_recent_errors()

        # Assert
        assert isinstance(result, ClaudeIntegrationSession)
        mock_adapter.get_claude_integration_status.assert_called_once()
        mock_session_repo.find_since_timestamp.assert_called_once()

    @pytest.mark.spec("SPEC-CLAUDE-002")
    async def test_export_with_format_customization(self):
        """カスタムフォーマットでのエクスポート"""
        # Arrange
        custom_format = ErrorExportFormat(
            format_type=ExportFormatType.JSON,
            structure_version="1.0",
            max_errors_per_file=10,
            include_suggestions=True,
            priority_filter="high",
        )

        error_session = self._create_error_session()

        mock_session_repo = Mock()
        mock_session_repo.find_recent_sessions = AsyncMock(return_value=[error_session])

        mock_format_service = Mock()
        mock_adapter = Mock(spec=ClaudeCodeAdapter)
        mock_adapter.export_errors_for_claude = Mock()

        use_case = ExportErrorsForClaudeUseCase(
            session_repository=mock_session_repo, format_service=mock_format_service, claude_adapter=mock_adapter
        )

        # Act
        result = await use_case.execute_export(format_config=custom_format)

        # Assert
        assert isinstance(result, ClaudeIntegrationSession)
        assert result.suggestion_metadata.format_used == custom_format

    @pytest.mark.spec("SPEC-CLAUDE-002")
    async def test_handle_export_failure(self):
        """エクスポート失敗時のエラーハンドリング"""
        # Arrange
        error_session = self._create_error_session()

        mock_session_repo = Mock()
        mock_session_repo.find_recent_sessions = AsyncMock(return_value=[error_session])

        mock_format_service = Mock()
        mock_adapter = Mock(spec=ClaudeCodeAdapter)
        mock_adapter.export_errors_for_claude = Mock(side_effect=Exception("Export failed"))

        use_case = ExportErrorsForClaudeUseCase(
            session_repository=mock_session_repo, format_service=mock_format_service, claude_adapter=mock_adapter
        )

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await use_case.execute_export()

        assert "Export failed" in str(exc_info.value)

    def _create_error_session(self, file_path: FilePath = None) -> FileQualityCheckSession:
        """テスト用エラーセッション作成"""
        if file_path is None:
            file_path = FilePath("noveler/test_error_file.py")

        session = FileQualityCheckSession(session_id="test-session-001", file_path=file_path)

        # エラー詳細を設定
        session._error_details = [
            {"code": "E999", "line_number": 3, "message": "SyntaxError: invalid syntax", "column": 20}
        ]
        session._status = "completed"

        return session
