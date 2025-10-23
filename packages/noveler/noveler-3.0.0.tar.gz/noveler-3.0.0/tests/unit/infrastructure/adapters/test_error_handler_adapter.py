#!/usr/bin/env python3
"""ErrorHandlerAdapterのテスト

TDD+DDD原則に基づくインフラストラクチャ層アダプターのテスト
仕様書: error_handler_adapter.spec.md
"""

import tempfile
import time
from pathlib import Path
from typing import NoReturn
from unittest.mock import Mock, patch

import pytest
import yaml

from noveler.infrastructure.adapters import error_handler_adapter
from noveler.infrastructure.adapters.error_handler_adapter import (
    LOG_DIR,
    ConfigError,
    DependencyError,
    ErrorContext,
    FileAccessError,
    NovelSystemError,
    ValidationError,
    create_error_report,
    handle_error,
    log_performance,
    logger,
    safe_file_operation,
    safe_yaml_operation,
    setup_logger,
    validate_required_fields,
)


class TestErrorHandlerAdapter:
    """ErrorHandlerAdapterのテストクラス"""

    def setup_method(self) -> None:
        """テストメソッドごとの初期設定"""
        # テスト用ログディレクトリ
        self.test_log_dir = Path(tempfile.mkdtemp())

        # モックサービス
        self.mock_error_service = Mock()

        # デフォルトモック戻り値設定
        self.mock_logger = Mock()
        self.mock_error_service.setup_logger.return_value = self.mock_logger
        self.mock_error_service.handle_error.return_value = None
        self.mock_error_service.create_error_report.return_value = Mock(
            error_type="TestError",
            message="テストエラーメッセージ",
            context={"test": "context"},
            timestamp=Mock(isoformat=Mock(return_value="2025-07-21T14:30:45.123456")),
            level=Mock(value="ERROR"),
            traceback="test traceback",
            additional_info={"test_info": "value"},
        )

    # -----------------------------------------------------------------
    # RED Phase: 失敗するテストを先に書く
    # -----------------------------------------------------------------

    def test_setup_logger_basic_functionality(self) -> None:
        """TDD RED: ロガー基本機能のテスト

        ロガーが適切にセットアップされることを確認
        """
        with patch("noveler.infrastructure.adapters.error_handler_adapter._error_service") as mock_service:
            mock_service.setup_logger.return_value = self.mock_logger

            # When: ロガーをセットアップ
            result_logger = setup_logger("test_module")

            # Then: 適切なロガーが返される
            assert result_logger == self.mock_logger
            mock_service.setup_logger.assert_called_once_with("test_module", None)

    def test_setup_logger_with_log_file(self) -> None:
        """TDD RED: ログファイル指定時のロガーセットアップ

        ログファイルを指定した場合の動作を確認
        """
        with patch("noveler.infrastructure.adapters.error_handler_adapter._error_service") as mock_service:
            mock_service.setup_logger.return_value = self.mock_logger

            # When: ログファイル指定でロガーをセットアップ
            result_logger = setup_logger("test_module", "test.log")

            # Then: ログファイル指定が渡される
            assert result_logger == self.mock_logger
            mock_service.setup_logger.assert_called_once_with("test_module", "test.log")

    def test_handle_error_basic_flow(self) -> None:
        """TDD RED: 基本的なエラーハンドリングフロー

        エラーが適切に処理されることを確認
        """
        with patch("noveler.infrastructure.adapters.error_handler_adapter._error_service") as mock_service:
            # Given: テスト用エラー
            test_error = ValueError("テストエラー")

            # When: エラーを処理
            handle_error(test_error, "テストコンテキスト", fatal=False)

            # Then: エラーサービスが呼ばれる
            mock_service.handle_error.assert_called_once_with(test_error, "テストコンテキスト", False)

    def test_handle_error_fatal_default(self) -> None:
        """TDD RED: Fatal フラグのデフォルト値テスト

        fatal引数のデフォルト値がFalseであることを確認
        """
        with patch("noveler.infrastructure.adapters.error_handler_adapter._error_service") as mock_service:
            test_error = RuntimeError("Fatal エラー")

            # When: fatalフラグを省略
            handle_error(test_error, "Fatal テスト")

            # Then: fatal=False で呼ばれる（デフォルト値）
            mock_service.handle_error.assert_called_once_with(test_error, "Fatal テスト", False)

    def test_safe_file_operation_decorator_success(self) -> None:
        """TDD RED: 安全ファイル操作デコレータ成功時のテスト

        ファイル操作が成功した場合の動作を確認
        """
        with patch("noveler.infrastructure.adapters.error_handler_adapter._error_service") as mock_service:
            mock_service.safe_file_operation.return_value = lambda func: func

            # Given: デコレータで装飾された関数
            @safe_file_operation("テストファイル操作")
            def test_file_operation() -> str:
                return "成功"

            # When: 関数を実行
            result = test_file_operation()

            # Then: 正常に実行される
            assert result == "成功"
            mock_service.safe_file_operation.assert_called_once_with("テストファイル操作")

    def test_safe_yaml_operation_decorator_success(self) -> None:
        """TDD RED: 安全YAML操作デコレータ成功時のテスト

        YAML操作が成功した場合の動作を確認
        """
        with patch("noveler.infrastructure.adapters.error_handler_adapter._error_service") as mock_service:
            mock_service.safe_yaml_operation.return_value = lambda func: func

            # Given: デコレータで装飾された関数
            @safe_yaml_operation("テストYAML操作")
            def test_yaml_operation():
                return {"result": "success"}

            # When: 関数を実行
            result = test_yaml_operation()

            # Then: 正常に実行される
            assert result == {"result": "success"}
            mock_service.safe_yaml_operation.assert_called_once_with("テストYAML操作")

    def test_validate_required_fields_success(self) -> None:
        """TDD RED: 必須フィールド検証成功のテスト

        必須フィールドが全て存在する場合の動作を確認
        """
        with patch("noveler.infrastructure.adapters.error_handler_adapter._error_service") as mock_service:
            # Given: 完全なデータ
            data = {"name": "テスト", "value": 123, "enabled": True}
            required_fields = ["name", "value", "enabled"]

            # When: 必須フィールドを検証
            validate_required_fields(data, required_fields, "テスト検証")

            # Then: エラーサービスが呼ばれる(例外なし)
            mock_service.validate_required_fields.assert_called_once_with(data, required_fields, "テスト検証")

    def test_validate_required_fields_missing_field(self) -> None:
        """TDD RED: 必須フィールド不足時のエラー

        必須フィールドが不足している場合にValidationErrorが発生することを確認
        """
        with patch("noveler.infrastructure.adapters.error_handler_adapter._error_service") as mock_service:
            # Given: エラーサービスが例外を発生
            mock_service.validate_required_fields.side_effect = ValidationError("必須フィールドが不足: value")

            data = {"name": "テスト"}  # valueフィールド不足
            required_fields = ["name", "value"]

            # When & Then: ValidationErrorが発生
            with pytest.raises(ValidationError) as exc_info:
                validate_required_fields(data, required_fields, "不完全データ検証")

            assert "必須フィールドが不足" in str(exc_info.value)

    def test_create_error_report_basic(self) -> None:
        """TDD RED: エラーレポート作成基本機能のテスト

        エラーレポートが適切な形式で作成されることを確認
        """
        with patch("noveler.infrastructure.adapters.error_handler_adapter._error_service") as mock_service:
            mock_service.create_error_report.return_value = self.mock_error_service.create_error_report.return_value

            # Given: テストエラー
            test_error = FileNotFoundError("ファイルが見つかりません")
            context = {"file_path": "/test/path.yaml", "operation": "load"}

            # When: エラーレポートを作成
            report = create_error_report(test_error, context)

            # Then: 適切な形式のレポートが返される
            assert isinstance(report, dict)
            assert report["error_type"] == "TestError"
            assert report["message"] == "テストエラーメッセージ"
            assert report["context"] == {"test": "context"}
            assert report["timestamp"] == "2025-07-21T14:30:45.123456"
            assert report["level"] == "ERROR"
            assert report["traceback"] == "test traceback"
            assert report["additional_info"] == {"test_info": "value"}

            # Then: エラーサービスが呼ばれる
            mock_service.create_error_report.assert_called_once_with(test_error, context)

    def test_log_performance_basic(self) -> None:
        """TDD RED: パフォーマンスログ記録基本機能のテスト

        パフォーマンス情報が適切に記録されることを確認
        """
        with patch("noveler.infrastructure.adapters.error_handler_adapter._error_service") as mock_service:
            # Given: パフォーマンス情報
            operation_name = "品質チェック"
            duration = 2.345
            context = {"file_size": 15420, "check_types": ["basic", "composition"]}

            # When: パフォーマンスログを記録
            log_performance(operation_name, duration, context)

            # Then: エラーサービスが呼ばれる
            mock_service.log_performance.assert_called_once_with(operation_name, duration, context)

    # -----------------------------------------------------------------
    # GREEN Phase: テストを通す最小実装(実装は既存コードで対応)
    # -----------------------------------------------------------------

    def test_default_logger_availability(self) -> None:
        """TDD GREEN: デフォルトロガーの利用可能性テスト

        モジュールレベルのデフォルトロガーが利用可能であることを確認
        """
        # Then: デフォルトロガーが存在
        assert logger is not None
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "debug")

    def test_log_dir_creation(self) -> None:
        """TDD GREEN: ログディレクトリ作成のテスト

        LOG_DIRが適切に定義され、存在することを確認
        """
        # Then: ログディレクトリが定義されている
        assert LOG_DIR is not None
        assert isinstance(LOG_DIR, Path)
        assert ".novel" in str(LOG_DIR)
        assert "logs" in str(LOG_DIR)

    def test_error_classes_inheritance(self) -> None:
        """TDD GREEN: エラークラスの継承関係テスト

        カスタムエラークラスが適切に継承されていることを確認
        """
        # Then: 全てNovelSystemErrorを継承
        assert issubclass(ConfigError, NovelSystemError)
        assert issubclass(FileAccessError, NovelSystemError)
        assert issubclass(ValidationError, NovelSystemError)
        assert issubclass(DependencyError, NovelSystemError)

        # Then: NovelSystemErrorはExceptionを継承
        assert issubclass(NovelSystemError, Exception)

    def test_error_instantiation(self) -> None:
        """TDD GREEN: エラーインスタンス化テスト

        各エラークラスが適切にインスタンス化できることを確認
        """
        # When & Then: 各エラーをインスタンス化
        config_error = ConfigError("設定エラー")
        assert str(config_error) == "設定エラー"

        file_error = FileAccessError("ファイルアクセスエラー")
        assert str(file_error) == "ファイルアクセスエラー"

        validation_error = ValidationError("検証エラー")
        assert str(validation_error) == "検証エラー"

        dependency_error = DependencyError("依存関係エラー")
        assert str(dependency_error) == "依存関係エラー"

    # -----------------------------------------------------------------
    # REFACTOR Phase: より良い設計へ
    # -----------------------------------------------------------------

    def test_safe_file_operation_real_file_success(self) -> None:
        """TDD REFACTOR: 実際のファイル操作での成功テスト

        実際のファイルを使用した安全操作の動作確認
        """
        # Given: 一時ファイル
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("テストデータ")
            temp_path = Path(f.name)

        try:
            # Given: 実際のサービスを使用(モックなし)
            @safe_file_operation("実ファイル読み込み")
            def read_test_file(filepath: Path) -> str:
                return filepath.read_text(encoding="utf-8")

            # When: ファイル読み込み
            content = read_test_file(temp_path)

            # Then: 正常に読み込める
            assert content == "テストデータ"

        finally:
            temp_path.unlink()

    def test_safe_yaml_operation_real_yaml_success(self) -> None:
        """TDD REFACTOR: 実際のYAML操作での成功テスト

        実際のYAMLファイルを使用した安全操作の動作確認
        """
        # Given: YAML データ
        test_data = {
            "project_name": "テストプロジェクト",
            "episodes": [{"number": 1, "title": "第1話"}, {"number": 2, "title": "第2話"}],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
            yaml.dump(test_data, f, allow_unicode=True)
            temp_path = Path(f.name)

        try:
            # Given: 実際のサービスを使用
            @safe_yaml_operation("実YAML読み込み")
            def load_test_yaml(filepath: Path) -> dict:
                return yaml.safe_load(filepath.read_text(encoding="utf-8"))

            # When: YAML読み込み
            loaded_data = load_test_yaml(temp_path)

            # Then: 正常に読み込める
            assert loaded_data["project_name"] == "テストプロジェクト"
            assert len(loaded_data["episodes"]) == 2
            assert loaded_data["episodes"][0]["title"] == "第1話"

        finally:
            temp_path.unlink()

    def test_performance_logging_with_real_timing(self) -> None:
        """TDD REFACTOR: 実際の時間測定でのパフォーマンスログテスト

        実際の処理時間を測定してのログ記録確認
        """
        with patch("noveler.infrastructure.adapters.error_handler_adapter._error_service") as mock_service:
            # Given: 実際に時間のかかる処理
            def slow_operation() -> str:
                time.sleep(0.1)  # 100ms の処理
                return "完了"

            start_time = time.time()
            result = slow_operation()
            duration = time.time() - start_time

            # When: パフォーマンスログを記録
            log_performance("遅い処理テスト", duration, {"result": result})

            # Then: 適切な時間が記録される
            mock_service.log_performance.assert_called_once()
            call_args = mock_service.log_performance.call_args[0]
            assert call_args[0] == "遅い処理テスト"
            assert 0.09 <= call_args[1] <= 0.2  # 実際の処理時間の範囲
            assert call_args[2]["result"] == "完了"

    def test_comprehensive_error_report_content(self) -> None:
        """TDD REFACTOR: 包括的エラーレポート内容テスト

        エラーレポートに必要な全ての情報が含まれることを確認
        """
        with patch("noveler.infrastructure.adapters.error_handler_adapter._error_service") as mock_service:
            # Given: 詳細なエラーレポートのモック
            detailed_report = Mock()
            detailed_report.error_type = "FileAccessError"
            detailed_report.message = "プロジェクト設定ファイルが見つかりません"
            detailed_report.context = {
                "operation": "load_project_config",
                "file_path": "/path/to/プロジェクト設定.yaml",
                "attempted_paths": ["/path1", "/path2"],
            }
            detailed_report.timestamp.isoformat.return_value = "2025-07-21T15:45:30.999999"
            detailed_report.level.value = "ERROR"
            detailed_report.traceback = "Traceback (most recent call last):\n  File..."
            detailed_report.additional_info = {
                "recovery_suggestions": ["設定ファイルを作成してください"],
                "related_files": ["/path/to/template.yaml"],
                "system_info": {"platform": "linux", "python": "3.10"},
            }

            mock_service.create_error_report.return_value = detailed_report

            # Given: 複雑なエラーシナリオ
            test_error = FileNotFoundError("No such file or directory: 'プロジェクト設定.yaml'")
            complex_context = {
                "user_action": "プロジェクト初期化",
                "expected_files": ["プロジェクト設定.yaml", "話数管理.yaml"],
                "current_directory": "/current/path",
            }

            # When: 詳細エラーレポートを作成
            report = create_error_report(test_error, complex_context)

            # Then: 全ての必要情報が含まれる
            assert report["error_type"] == "FileAccessError"
            assert "プロジェクト設定ファイル" in report["message"]
            assert report["context"]["operation"] == "load_project_config"
            assert len(report["context"]["attempted_paths"]) == 2
            assert report["timestamp"].endswith("999999")
            assert report["level"] == "ERROR"
            assert "Traceback" in report["traceback"]
            assert len(report["additional_info"]["recovery_suggestions"]) == 1
            assert "template.yaml" in report["additional_info"]["related_files"][0]
            assert report["additional_info"]["system_info"]["platform"] == "linux"

    def test_legacy_compatibility_pattern(self) -> None:
        """TDD REFACTOR: レガシー互換性パターンテスト

        既存コードパターンとの互換性を確認
        """
        # Given: レガシーコードのパターン(グローバルロガー使用)
        # from noveler.infrastructure.adapters.error_handler_adapter import logger  # Moved to top-level

        # When: レガシーパターンでログ出力
        logger.info("レガシーコードからの情報ログ")
        logger.error("レガシーコードからのエラーログ")

        # Then: ロガーが正常に動作(例外なし)
        # 実際のロガーが動作することを確認
        assert logger is not None
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "debug")

    def test_decorator_error_handling_flow(self) -> None:
        """TDD REFACTOR: デコレータエラーハンドリングフローテスト

        デコレータによる例外処理の完全なフローを確認
        """
        with patch("noveler.infrastructure.adapters.error_handler_adapter._error_service") as mock_service:
            # Given: エラーを発生するデコレータ
            def error_decorator(operation_name):
                def decorator(func):
                    def wrapper(*args, **kwargs):
                        try:
                            return func(*args, **kwargs)
                        except Exception as e:
                            # デコレータ内でエラーハンドリング
                            handle_error(e, operation_name, fatal=False)
                            raise

                    return wrapper

                return decorator

            mock_service.safe_file_operation.return_value = error_decorator("危険なファイル操作")

            # Given: エラーを発生する関数
            @safe_file_operation("危険なファイル操作")
            def dangerous_file_operation() -> NoReturn:
                msg = "危険な操作でファイルが見つからない"
                raise FileNotFoundError(msg)

            # When & Then: エラーが適切に処理される
            with pytest.raises(FileNotFoundError, match=".*"):
                dangerous_file_operation()

            # Then: エラーハンドリングが呼ばれる
            mock_service.handle_error.assert_called()

    def test_module_exports_completeness(self) -> None:
        """TDD REFACTOR: モジュールエクスポートの完全性テスト

        仕様書記載の全ての公開関数・クラスがエクスポートされることを確認
        """
        # from noveler.infrastructure.adapters import error_handler_adapter  # Moved to top-level

        # Then: __all__ に記載された全ての要素がエクスポートされている
        expected_exports = [
            "LOG_DIR",
            "ConfigError",
            "DependencyError",
            "ErrorContext",
            "ErrorHandlingService",
            "FileAccessError",
            "NovelSystemError",
            "ValidationError",
            "create_error_report",
            "handle_error",
            "log_performance",
            "logger",
            "safe_file_operation",
            "safe_yaml_operation",
            "setup_logger",
            "validate_required_fields",
        ]

        for export in expected_exports:
            assert hasattr(error_handler_adapter, export), f"{export} がエクスポートされていません"
            assert export in error_handler_adapter.__all__, f"{export} が __all__ に含まれていません"

    def test_error_context_integration(self) -> None:
        """TDD REFACTOR: エラーコンテキスト統合テスト

        エラーコンテキストが適切に構築・利用されることを確認
        """
        with patch("noveler.infrastructure.adapters.error_handler_adapter._error_service") as mock_service:
            # Given: ErrorContextが利用可能
            # from noveler.infrastructure.adapters.error_handler_adapter import ErrorContext  # Moved to top-level

            # When: エラーコンテキストを作成(error_serviceを第一引数として渡す)
            context = ErrorContext(
                mock_service,  # error_service 引数
                context="テスト操作",
                file_path="/test/path.yaml",
                user_data={"input": "test"},
                system_state={"memory_usage": "50%"},
            )

            # Then: エラーコンテキストが適切に構築される
            assert context.error_service == mock_service
            assert context.context == "テスト操作"
            assert context.kwargs["file_path"] == "/test/path.yaml"
            assert context.kwargs["user_data"]["input"] == "test"
            assert context.kwargs["system_state"]["memory_usage"] == "50%"
