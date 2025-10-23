"""Backward-compatible adapter that exposes shared error handling helpers."""

import sys as _sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from noveler.infrastructure.shared.error_handling_service import (
    ConfigError,
    DependencyError,
    ErrorContext,
    ErrorHandlingService,
    FileAccessError,
    NovelSystemError,
    ValidationError,
)

# グローバルサービスインスタンス
_error_service = ErrorHandlingService(None)

# ログディレクトリ(レガシー互換性)
LOG_DIR = Path.home() / ".novel" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def setup_logger(name: str, log_file: str | Path | None = None) -> object:
    """Return a logger configured through the legacy service entrypoint.

    Args:
        name: Logger identifier, typically ``__name__``.
        log_file: Optional log file path; ``None`` delegates to the service default.

    Returns:
        object: Logger instance produced by the shared error handling service.
    """
    # テスト仕様に合わせ、log_file=None はそのまま渡す
    # 実際の既定ファイル名の決定はサービス側に委譲する
    return _error_service.setup_logger(name, log_file)  # type: ignore[arg-type]


def handle_error(error: Exception, context: str | ErrorContext, fatal: bool = False) -> None:
    """Delegate unified error handling to the shared service.

    Args:
        error: Raised exception to handle.
        context: String or context object describing the failing operation.
        fatal: When ``True`` the process may terminate after handling.
    """
    _error_service.handle_error(error, context, fatal)


def safe_file_operation(operation_name: str) -> Callable:
    """Return a decorator that guards file operations with error handling.

    Args:
        operation_name: Human readable name emitted on failure.
    """
    return _error_service.safe_file_operation(operation_name)


def safe_yaml_operation(operation_name: str) -> Callable:
    """Return a decorator that guards YAML operations with error handling.

    Args:
        operation_name: Human readable name emitted on failure.
    """
    return _error_service.safe_yaml_operation(operation_name)


def validate_required_fields(data: dict[str, Any], required_fields: list[str], context: str | None = None) -> None:
    """Ensure required keys are present in the provided payload.

    Args:
        data: Input payload to validate.
        required_fields: List of keys that must exist.
        context: Optional context string reported on failure.

    Raises:
        ValidationError: When any required key is missing.
    """
    _error_service.validate_required_fields(data, required_fields, context)


def create_error_report(error: Exception, context: str | ErrorContext) -> dict:
    """Generate a legacy-formatted error report dictionary.

    Args:
        error: Exception instance to describe.
        context: String or object that provides additional detail.

    Returns:
        dict: Error report formatted for legacy consumers.
    """
    report = _error_service.create_error_report(error, context)

    # レガシー形式の辞書に変換
    return {
        "error_type": report.error_type,
        "message": report.message,
        "context": report.context,
        "timestamp": report.timestamp.isoformat(),
        "level": report.level.value,
        "traceback": report.traceback,
        "additional_info": report.additional_info,
    }


def log_performance(operation_name: str, duration: float, context: str | None = None) -> None:
    """Record a performance metric via the shared error handling service.

    Args:
        operation_name: Name of the measured operation.
        duration: Execution time in seconds.
        context: Optional contextual information for the metric.
    """
    _error_service.log_performance(operation_name, duration, context)


# デフォルトロガー(レガシー互換性)
logger = setup_logger(__name__)

# エクスポートする関数とクラス
__all__ = [
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

# --- Legacy import path alias (for tests/legacy code) ---
# 一部のテストが "infrastructure.adapters.error_handler_adapter" をパッチ対象にしているため、
# 現在のモジュールにエイリアスを張って互換性を提供する。
from types import ModuleType as _ModuleType

# ルート疑似パッケージとサブパッケージを作成し、属性を結線
_infra_pkg = _sys.modules.setdefault("infrastructure", _ModuleType("infrastructure"))
_infra_adapters_pkg = _sys.modules.setdefault("infrastructure.adapters", _ModuleType("infrastructure.adapters"))
_sys.modules.setdefault("infrastructure.adapters.error_handler_adapter", _sys.modules[__name__])
_infra_adapters_pkg.error_handler_adapter = _sys.modules[__name__]
_infra_pkg.adapters = _infra_adapters_pkg
