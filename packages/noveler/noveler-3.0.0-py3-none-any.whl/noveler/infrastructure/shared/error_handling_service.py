"""Infrastructure層のShared Kernel: エラーハンドリングサービス

統一的なエラーハンドリングを提供するサービス
"""
import functools
import sys
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, TypeVar

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.infrastructure.logging.unified_logger import get_logger
from noveler.presentation.shared.shared_utilities import console

F = TypeVar("F", bound=Callable[..., Any])
import yaml

ContextData = dict[str, Any]
DecoratorCallable = Callable[..., Any]
ExceptionType = type[BaseException] | None
from noveler.application.services.message_service import MessageService

JST = ProjectTimezone.jst().timezone

class ErrorLevel(Enum):
    """エラーレベル"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class ErrorReport:
    """エラーレポート"""
    error_type: str
    message: str
    context: str
    timestamp: datetime
    level: ErrorLevel
    traceback: str | None = None
    additional_info: dict[str, Any] | None = None

class NovelSystemError(Exception):
    """小説執筆支援システムの基本エラークラス"""

class ConfigError(NovelSystemError):
    """設定関連のエラー"""

class ValidationError(NovelSystemError):
    """検証エラー"""

class FileAccessError(NovelSystemError):
    """ファイルアクセスエラー"""

class DependencyError(NovelSystemError):
    """依存関係エラー"""

class ErrorHandlingService:
    """エラーハンドリングサービス"""

    def __init__(self, log_dir: Path | str | None) -> None:
        self.log_dir = log_dir or Path.home() / ".novel" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        try:
            from noveler.infrastructure.adapters.logger_service_adapter import LoggerServiceAdapter
            logger_service = LoggerServiceAdapter("error_handling")
            self.message_service = MessageService(logger_service)
        except (ImportError, TypeError):

            class NullLogger:

                def log(self, *args, **kwargs) -> None:
                    pass

                def info(self, *args, **kwargs) -> None:
                    pass

                def error(self, *args, **kwargs) -> None:
                    pass

                def debug(self, *args, **kwargs) -> None:
                    pass
            self.message_service = MessageService(NullLogger())
        self._loggers: dict[str, object] = {}

    def setup_logger(self, name: str, log_file: str | Path) -> object:
        """ロガーをセットアップ

        Args:
            name: ロガー名(通常は__name__)
            log_file: ログファイル名(指定しない場合は自動生成)

        Returns:
            設定済みのロガー
        """
        if name in self._loggers:
            return self._loggers[name]
        logger = get_logger(name)
        self._loggers[name] = logger
        return logger

    def handle_error(self, error: BaseException, context: str, fatal: bool=False) -> None:
        """エラーを統一的に処理

        Args:
            error: 発生したエラー
            context: エラーが発生した文脈
            fatal: Trueの場合、プログラムを終了
        """
        error_type = type(error).__name__
        error_msg = str(error)
        full_msg = f"{context}: {error_msg}" if context else error_msg
        logger = self.setup_logger(__name__, f"novel_{project_now().datetime.strftime('%Y%m%d')}.log")
        logger.error("%s: %s", error_type, full_msg)
        logger.debug(traceback.format_exc())
        try:
            self.message_service.show_error(error, context)
        except Exception as msg_error:
            console.print(f"ERROR: {full_msg}")
            console.print(f"メッセージサービスエラー: {msg_error}")
        if fatal:
            console.print("\nプログラムを終了します。")
            sys.exit(1)

    def create_error_context(self, **kwargs) -> "ErrorContext":
        """エラーコンテキストを作成"""
        return ErrorContext(self, **kwargs)

    def safe_file_operation(self, operation_name: str) -> Callable[[F], F]:
        """安全なファイル操作デコレータ

        Args:
            operation_name: 操作名(エラー時に表示)
        """

        def decorator(func: F) -> F:

            @functools.wraps(func)
            def wrapper(*args: object, **kwargs) -> Any:
                try:
                    return func(*args, **kwargs)
                except (FileNotFoundError, PermissionError, OSError):
                    self.handle_error(FileAccessError(f"{operation_name}中にエラーが発生しました"), f"{func.__name__}", fatal=False)
                    raise
                except Exception as e:
                    self.handle_error(e, f"{func.__name__}の{operation_name}", fatal=False)
                    raise
            return wrapper
        return decorator

    def safe_yaml_operation(self, operation_name: str) -> Callable[[F], F]:
        """安全なYAML操作デコレータ

        Args:
            operation_name: 操作名(エラー時に表示)
        """

        def decorator(func: F) -> F:

            @functools.wraps(func)
            def wrapper(*args: object, **kwargs) -> Any:
                try:
                    return func(*args, **kwargs)
                except yaml.YAMLError:
                    self.handle_error(ValidationError(f"YAML{operation_name}エラー"), f"{func.__name__}", fatal=False)
                    raise
                except Exception as e:
                    self.handle_error(e, f"{func.__name__}の{operation_name}", fatal=False)
                    raise
            return wrapper
        return decorator

    def validate_required_fields(self, data: dict[str, object], required_fields: list[str], context: str | None=None) -> None:
        """必須フィールドの存在を検証

        Args:
            data: 検証対象のデータ
            required_fields: 必須フィールドのリスト
            context: エラー時のコンテキスト情報

        Raises:
            ValidationError: 必須フィールドが不足している場合
        """
        missing_fields = []
        for field in required_fields:
            if "." in field:
                keys = field.split(".")
                current = data
                for key in keys:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        missing_fields.append(field)
                        break
            elif field not in data:
                missing_fields.append(field)
        if missing_fields:
            msg = f"必須項目が不足しています: {', '.join(missing_fields)}"
            if context:
                msg = f"{context} - {msg}"
            raise ValidationError(msg)

    def create_error_report(self, error: Exception, context: str) -> ErrorReport:
        """エラーレポートを作成

        Args:
            error: 発生したエラー
            context: 追加のコンテキスト情報

        Returns:
            エラーレポート
        """
        error_level = ErrorLevel.ERROR
        if isinstance(error, ConfigError | ValidationError):
            error_level = ErrorLevel.WARNING
        elif isinstance(error, DependencyError):
            error_level = ErrorLevel.CRITICAL
        return ErrorReport(error_type=type(error).__name__, message=str(error), context=context.get("context", "") if context else "", timestamp=project_now().datetime, level=error_level, traceback=traceback.format_exc(), additional_info=context)

    def log_performance(self, operation_name: str, duration: float, context: str | None=None) -> None:
        """パフォーマンスログを記録

        Args:
            operation_name: 操作名
            duration: 実行時間(秒)
            context: 追加のコンテキスト情報
        """
        logger = self.setup_logger("performance", f"performance_{project_now().datetime.strftime('%Y%m%d')}.log")
        logger.info("Performance: %s - %.3fs", operation_name, duration)
        if context:
            logger.debug("Context: %s", context)

class ErrorContext:
    """エラーコンテキストマネージャー"""

    def __init__(self, error_service: ErrorHandlingService, context: str, **kwargs: object) -> None:
        self.error_service = error_service
        self.context = context
        self.kwargs = kwargs

    def __enter__(self) -> Any:
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: object=None) -> None:
        if exc_type:
            self.error_service.handle_error(exc_val, self.context, fatal=False)
        return False
