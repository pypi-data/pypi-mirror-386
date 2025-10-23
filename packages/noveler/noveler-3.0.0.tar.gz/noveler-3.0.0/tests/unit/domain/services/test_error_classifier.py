# File: tests/unit/domain/services/test_error_classifier.py
# Purpose: Verify the unified error handling stack (classifier, service, logger) against SPEC-ERR-001.
# Context: Exercises domain/application/infrastructure error modules through pytest fixtures.

"""統一エラーハンドリングシステムのテスト
SPEC-ERR-001準拠
"""

import json

import pytest

from noveler.application.services.error_handling_service import ErrorHandlingService
from noveler.domain.errors import ApplicationError, DomainError
from noveler.domain.services.error_classifier import ErrorClassifier, ErrorLevel
from noveler.infrastructure.logging.error_logger import ErrorLogger


@pytest.mark.spec("SPEC-ERR-001")
class TestErrorClassifier:
    """ErrorClassifier純粋関数のテスト（Functional Core）"""

    @pytest.mark.spec("SPEC-ERROR_CLASSIFIER-CLASSIFY_DOMAIN_ERRO")
    def test_classify_domain_error(self):
        """ドメインエラーの分類テスト"""
        error = DomainError("ビジネスルール違反")

        # Act
        level = ErrorClassifier.classify(error)

        # Assert
        assert level == ErrorLevel.ERROR
        assert ErrorClassifier.is_pure_function()  # 純粋関数であることを保証

    @pytest.mark.spec("SPEC-ERROR_CLASSIFIER-CLASSIFY_CRITICAL_ER")
    def test_classify_critical_error(self):
        """致命的エラーの分類テスト"""
        error = SystemError("システム停止が必要なエラー")

        # Act
        level = ErrorClassifier.classify(error)

        # Assert
        assert level == ErrorLevel.CRITICAL

    @pytest.mark.spec("SPEC-ERROR_CLASSIFIER-CLASSIFY_WARNING")
    def test_classify_warning(self):
        """警告レベルの分類テスト"""
        error = UserWarning("非推奨機能の使用")

        # Act
        level = ErrorClassifier.classify(error)

        # Assert
        assert level == ErrorLevel.WARNING

    @pytest.mark.spec("SPEC-ERROR_CLASSIFIER-ERROR_CONTEXT_EXTRAC")
    def test_error_context_extraction(self):
        """エラーコンテキスト抽出テスト"""
        error = ValueError("Invalid parameter: age=-1")

        # Act
        context = ErrorClassifier.extract_context(error)

        # Assert
        assert context["error_type"] == "ValueError"
        assert context["message"] == "Invalid parameter: age=-1"
        assert "traceback" not in context  # 純粋関数なのでトレースバックは含まない

    @pytest.mark.spec("SPEC-ERROR_CLASSIFIER-DETERMINISTIC_CLASSI")
    def test_deterministic_classification(self):
        """決定論的分類（同じ入力→同じ出力）"""
        error = RuntimeError("Test error")

        # Act
        level1 = ErrorClassifier.classify(error)
        level2 = ErrorClassifier.classify(error)

        # Assert
        assert level1 == level2  # 決定論的であること


@pytest.mark.spec("SPEC-ERR-001")
class TestErrorHandlingService:
    """ErrorHandlingServiceの統合テスト"""

    @pytest.fixture
    def mock_logger(self, mocker):
        """モックロガー"""
        return mocker.Mock()

    @pytest.fixture
    def mock_console(self, mocker):
        """モックコンソール"""
        return mocker.Mock()

    @pytest.mark.spec("SPEC-ERROR_CLASSIFIER-HANDLE_ERROR_WITH_LO")
    def test_handle_error_with_logging(self, mock_logger, mock_console):
        """エラーハンドリングとログ記録の統合テスト"""
        service = ErrorHandlingService(
            logger_service=mock_logger,
            console_service=mock_console
        )
        error = ApplicationError("処理に失敗しました")

        # Act
        result = service.handle_error(error)

        # Assert
        assert result.handled is True
        assert result.user_message == "処理中にエラーが発生しました。"
        mock_logger.error.assert_called_once()
        # console_serviceはhandle_errorでは使用されないため、呼び出されない

    @pytest.mark.spec("SPEC-ERROR_CLASSIFIER-HANDLE_CRITICAL_ERRO")
    def test_handle_critical_error(self, mock_logger, mock_console):
        """致命的エラーの特別処理テスト"""
        service = ErrorHandlingService(
            logger_service=mock_logger,
            console_service=mock_console
        )
        error = SystemError("データベース接続失敗")

        # Act
        result = service.handle_error(error)

        # Assert
        assert result.handled is True
        assert result.requires_restart is True
        mock_logger.critical.assert_called_once()


@pytest.mark.spec("SPEC-ERR-001")
class TestErrorLogger:
    """ErrorLogger実装のテスト（Imperative Shell）"""

    @pytest.mark.spec("SPEC-ERROR_CLASSIFIER-LOG_ERROR_TO_FILE")
    def test_log_error_to_file(self, tmp_path):
        """ファイルへのエラーログ出力テスト"""
        log_file = tmp_path / "error.log"
        logger = ErrorLogger(log_file=log_file)
        error = ValueError("Test error")

        # Act
        logger.log(error, ErrorLevel.ERROR)

        # Assert
        assert log_file.exists()
        content = log_file.read_text()
        assert "ValueError" in content
        assert "Test error" in content

    @pytest.mark.spec("SPEC-ERROR_CLASSIFIER-STRUCTURED_LOGGING")
    def test_structured_logging(self):
        """構造化ログ出力テスト"""
        logger = ErrorLogger(format="json")
        error = RuntimeError("Structured error")

        # Act
        log_entry = logger.format_log_entry(error, ErrorLevel.ERROR)

        # Assert
        parsed = json.loads(log_entry)
        assert parsed["level"] == "ERROR"
        assert parsed["error_type"] == "RuntimeError"
        assert parsed["message"] == "Structured error"
