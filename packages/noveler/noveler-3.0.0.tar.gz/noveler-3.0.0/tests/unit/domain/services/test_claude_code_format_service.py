#!/usr/bin/env python3
"""Claude Code フォーマットサービス テスト

SPEC-CLAUDE-002に基づくTDD実装
"""

import pytest

from noveler.domain.entities.file_quality_check_session import (
    CheckStatus,
    FileQualityCheckSession,
)
from noveler.domain.services.claude_code_format_service import ClaudeCodeFormatService
from noveler.domain.value_objects.file_path import FilePath


class TestClaudeCodeFormatService:
    """Claude Codeフォーマットサービス テストクラス"""

    @pytest.mark.spec("SPEC-CLAUDE-002")
    def test_should_exist(self):
        """サービスクラスが存在することを確認"""
        # RED段階: まだ実装されていないので失敗
        assert ClaudeCodeFormatService

    @pytest.mark.spec("SPEC-CLAUDE-002")
    def test_format_errors_for_claude_empty_sessions(self):
        """エラーセッションが空の場合のフォーマット"""
        # Arrange
        service = ClaudeCodeFormatService()
        sessions = []

        # Act
        result = service.format_errors_for_claude(sessions)

        # Assert
        assert result == []

    @pytest.mark.spec("SPEC-CLAUDE-002")
    def test_format_errors_for_claude_with_syntax_errors(self):
        """構文エラーがある場合のフォーマット"""
        # Arrange
        service = ClaudeCodeFormatService()
        session = self._create_syntax_error_session()
        sessions = [session]

        # Act
        result = service.format_errors_for_claude(sessions)

        # Assert
        assert len(result) == 1
        error = result[0]
        assert error["error_type"] == "syntax"
        assert error["priority"] == "high"
        assert "file_path" in error
        assert "line_number" in error

    @pytest.mark.spec("SPEC-CLAUDE-002")
    def test_generate_fix_suggestions_syntax_error(self):
        """構文エラーの修正提案生成"""
        # Arrange
        service = ClaudeCodeFormatService()
        session = self._create_syntax_error_session()
        sessions = [session]

        # Act
        suggestions = service.generate_fix_suggestions(sessions)

        # Assert
        assert len(suggestions) == 1
        suggestion = suggestions[0]
        assert "構文エラー" in suggestion["message"]
        assert suggestion["priority"] == "high"

    @pytest.mark.spec("SPEC-CLAUDE-002")
    def test_create_priority_ranking_mixed_errors(self):
        """混在エラーの優先度ランキング作成"""
        # Arrange
        service = ClaudeCodeFormatService()
        sessions = [
            self._create_syntax_error_session(),
            self._create_type_error_session(),
            self._create_style_error_session(),
        ]

        # Act
        ranking = service.create_priority_ranking(sessions)

        # Assert
        assert len(ranking) == 3
        # 構文エラーが最優先
        assert ranking[0]["priority"] == "high"
        assert ranking[0]["error_type"] == "syntax"

    @pytest.mark.spec("SPEC-CLAUDE-002")
    def test_filter_by_priority_high_only(self):
        """高優先度エラーのみフィルタ"""
        # Arrange
        service = ClaudeCodeFormatService()
        sessions = [
            self._create_syntax_error_session(),
            self._create_type_error_session(),
            self._create_style_error_session(),
        ]

        # Act
        high_priority = service.filter_by_priority(sessions, "high")

        # Assert
        assert len(high_priority) == 1
        assert high_priority[0]["priority"] == "high"

    def _create_syntax_error_session(self) -> FileQualityCheckSession:
        """構文エラーセッション作成"""
        # from noveler.domain.entities.file_quality_check_session import CheckStatus  # Moved to top-level

        session = FileQualityCheckSession(
            session_id="syntax-test-001", file_path=FilePath("noveler/test_syntax.py"), status=CheckStatus.COMPLETED
        )

        # モックのQualityCheckResultオブジェクトを作成
        class MockQualityCheckResult:
            def __init__(
                self, is_valid: bool, message: str, error_code: str | None = None, line_number: int | None = None
            ) -> None:
                self.is_valid = is_valid
                self.message = message
                self.error_code = error_code
                self.line_number = line_number

        error_result = MockQualityCheckResult(
            is_valid=False, message="SyntaxError: invalid syntax", error_code="E999", line_number=3
        )

        session.results.append(error_result)
        return session

    def _create_type_error_session(self) -> FileQualityCheckSession:
        """型エラーセッション作成"""
        # from noveler.domain.entities.file_quality_check_session import CheckStatus  # Moved to top-level

        session = FileQualityCheckSession(
            session_id="type-test-001", file_path=FilePath("noveler/test_type.py"), status=CheckStatus.COMPLETED
        )

        # モックのQualityCheckResultオブジェクトを作成
        class MockQualityCheckResult:
            def __init__(
                self, is_valid: bool, message: str, error_code: str | None = None, line_number: int | None = None
            ) -> None:
                self.is_valid = is_valid
                self.message = message
                self.error_code = error_code
                self.line_number = line_number

        error_result = MockQualityCheckResult(
            is_valid=False, message="Missing type annotation for function argument", error_code="ANN001", line_number=5
        )

        session.results.append(error_result)
        return session

    def _create_style_error_session(self) -> FileQualityCheckSession:
        """スタイルエラーセッション作成"""
        # from noveler.domain.entities.file_quality_check_session import CheckStatus  # Moved to top-level

        session = FileQualityCheckSession(
            session_id="style-test-001", file_path=FilePath("noveler/test_style.py"), status=CheckStatus.COMPLETED
        )

        # モックのQualityCheckResultオブジェクトを作成
        class MockQualityCheckResult:
            def __init__(
                self, is_valid: bool, message: str, error_code: str | None = None, line_number: int | None = None
            ) -> None:
                self.is_valid = is_valid
                self.message = message
                self.error_code = error_code
                self.line_number = line_number

        error_result = MockQualityCheckResult(
            is_valid=False, message="line too long (85 > 79 characters)", error_code="E501", line_number=10
        )

        session.results.append(error_result)
        return session
