#!/usr/bin/env python3
# File: src/noveler/infrastructure/logging/structured_logger.py
# Purpose: Structured logging helper for enhanced debugging and traceability
# Context: Implements logging_guidelines.md requirements with extra_data standardization

"""構造化ログヘルパー

logging_guidelines.md準拠の構造化ログ機能を提供。
request_id自動付与、PII自動マスク、extra_data標準化を実装。
"""

import logging
import re
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from contextvars import ContextVar

from noveler.infrastructure.logging.unified_logger import get_logger


# リクエストコンテキストの管理
_request_context: ContextVar[Optional['RequestContext']] = ContextVar('request_context', default=None)


class ErrorCategory(Enum):
    """エラーカテゴリの標準化"""
    VALIDATION = "validation"
    NETWORK = "network"
    FILESYSTEM = "filesystem"
    PARSING = "parsing"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_SERVICE = "external_service"
    LLM = "llm"
    CACHE = "cache"
    DATABASE = "database"
    CONFIGURATION = "configuration"


class RequestContext:
    """リクエスト追跡用コンテキスト

    全ての処理で共通のrequest_idを伝播させ、
    トレーサビリティを向上させる。
    """

    def __init__(
        self,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        episode_number: Optional[int] = None,
        operation: Optional[str] = None,
        **extras: Any,
    ):
        self.request_id = request_id or str(uuid.uuid4())
        self.session_id = session_id
        self.user_id = user_id
        self.episode_number = episode_number
        self.operation = operation
        self.start_time = time.time()
        self.extras: dict[str, Any] = dict(extras)

    def to_dict(self) -> dict[str, Any]:
        """コンテキストを辞書形式で取得"""
        data = {
            "request_id": self.request_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "episode_number": self.episode_number,
            "operation": self.operation,
            "elapsed_ms": (time.time() - self.start_time) * 1000
        }
        data.update(self.extras)
        return data

    def set_value(self, key: str, value: Any) -> None:
        """コンテキストに任意フィールドを設定"""
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            self.extras[key] = value

    def update(self, **kwargs: Any) -> None:
        """複数フィールドをまとめて設定"""
        for k, v in kwargs.items():
            self.set_value(k, v)

    @classmethod
    def ensure(cls, **kwargs: Any) -> 'RequestContext':
        """現在のコンテキストを取得し、なければ新規作成"""
        ctx = cls.get_current()
        if ctx is None:
            ctx = cls(**kwargs) if kwargs else cls()
            cls.set_current(ctx)
        elif kwargs:
            ctx.update(**kwargs)
        return ctx

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """既存コンテキストに値を設定（後方互換API）"""
        ctx = cls.ensure()
        ctx.set_value(key, value)

    @classmethod
    def clear(cls) -> None:
        """現在のコンテキストをクリア"""
        _request_context.set(None)
    @classmethod
    def get_current(cls) -> Optional['RequestContext']:
        """現在のコンテキストを取得"""
        return _request_context.get()

    @classmethod
    def set_current(cls, context: 'RequestContext') -> None:
        """現在のコンテキストを設定"""
        _request_context.set(context)

    def __enter__(self):
        """コンテキストマネージャーとして使用"""
        self._token = _request_context.set(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキスト終了時の処理"""
        _request_context.reset(self._token)


class StructuredLogger:
    """構造化ログヘルパー

    logging_guidelines.md準拠の構造化ログを提供。
    - request_id必須化
    - elapsed_ms自動計測
    - PII自動マスク
    - extra_data標準化
    """

    # PIIパターン（例：メールアドレス、電話番号、IPアドレス）
    PII_PATTERNS = [
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
        (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]'),
        (r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[IP]'),
        (r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[CARD]'),
    ]

    def __init__(self, name: str):
        """初期化

        Args:
            name: ロガー名（通常は__name__）
        """
        self.logger = get_logger(name)
        self.name = name

    def _mask_pii(self, data: Any) -> Any:
        """PII（個人情報）をマスク

        Args:
            data: マスク対象のデータ

        Returns:
            マスク済みデータ
        """
        if isinstance(data, str):
            masked = data
            for pattern, replacement in self.PII_PATTERNS:
                masked = re.sub(pattern, replacement, masked)
            return masked
        elif isinstance(data, dict):
            return {k: self._mask_pii(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._mask_pii(item) for item in data]
        else:
            return data

    def _prepare_extra(self, **context: Any) -> dict[str, Any]:
        """extra_data構造を準備

        Args:
            **context: ログコンテキスト情報

        Returns:
            標準化されたextra構造
        """
        # 現在のリクエストコンテキストを取得
        request_context = RequestContext.get_current()

        # 基本情報
        extra_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "logger_name": self.name,
        }

        # リクエストコンテキストがあれば追加
        if request_context:
            extra_data.update(request_context.to_dict())

        # 追加のコンテキスト情報をマスクして追加
        masked_context = self._mask_pii(context)
        if isinstance(masked_context, dict):
            user_extra = masked_context.pop("extra_data", None)
            extra_data.update(masked_context)
            if isinstance(user_extra, dict):
                extra_data.update(user_extra)
        else:
            extra_data["context"] = masked_context

        return {"extra_data": extra_data}

    def debug(self, message: str, **context: Any) -> None:
        """DEBUGレベルのログ出力（遅延評価対応）"""
        if self.logger.isEnabledFor(logging.DEBUG):
            extra = self._prepare_extra(**context)
            self.logger.debug(message, extra=extra)

    def info(self, message: str, **context: Any) -> None:
        """INFOレベルのログ出力"""
        extra = self._prepare_extra(**context)
        self.logger.info(message, extra=extra)

    def warning(self, message: str, **context: Any) -> None:
        """WARNINGレベルのログ出力"""
        extra = self._prepare_extra(**context)
        self.logger.warning(message, extra=extra)

    def error(
        self,
        message: str,
        error: Optional[Exception] = None,
        category: Optional[ErrorCategory] = None,
        **context: Any
    ) -> None:
        """ERRORレベルのログ出力（カテゴリ分類付き）

        Args:
            message: エラーメッセージ
            error: 例外オブジェクト
            category: エラーカテゴリ
            **context: 追加のコンテキスト情報
        """
        error_info = {}
        if error:
            error_info["error_type"] = type(error).__name__
            error_info["error_message"] = str(error)

        if category:
            error_info["error_category"] = category.value

        extra = self._prepare_extra(**error_info, **context)
        self.logger.error(message, extra=extra, exc_info=error is not None)

    def critical(self, message: str, **context: Any) -> None:
        """CRITICALレベルのログ出力"""
        extra = self._prepare_extra(**context)
        self.logger.critical(message, extra=extra)

    def log_performance(
        self,
        operation: str,
        elapsed_ms: float,
        success: bool = True,
        **metrics: Any
    ) -> None:
        """パフォーマンスメトリクスのログ出力

        Args:
            operation: 操作名
            elapsed_ms: 実行時間（ミリ秒）
            success: 成功/失敗
            **metrics: 追加のメトリクス情報
        """
        level = logging.INFO if success else logging.WARNING
        message = f"{operation}{'完了' if success else '失敗'}"

        performance_data = {
            "operation": operation,
            "elapsed_ms": elapsed_ms,
            "success": success,
            **metrics
        }

        extra = self._prepare_extra(**performance_data)
        self.logger.log(level, message, extra=extra)

    def log_llm_call(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_cost: float,
        elapsed_ms: float,
        success: bool = True,
        **additional_info: Any
    ) -> None:
        """LLM呼び出しの詳細ログ

        Args:
            model: 使用モデル名
            prompt_tokens: プロンプトトークン数
            completion_tokens: 生成トークン数
            total_cost: 総コスト（USD）
            elapsed_ms: 実行時間
            success: 成功/失敗
            **additional_info: 追加情報
        """
        llm_data = {
            "llm_model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "total_cost_usd": total_cost,
            "elapsed_ms": elapsed_ms,
            "success": success,
            **additional_info
        }

        message = f"LLM呼び出し{'成功' if success else '失敗'}: {model}"
        level = logging.INFO if success else logging.WARNING

        extra = self._prepare_extra(**llm_data)
        self.logger.log(level, message, extra=extra)


class LogAggregator:
    """バッチ処理のログ集約

    複数のイベントを集約して、まとめてログ出力する。
    """

    def __init__(self, logger: StructuredLogger, max_events: int = 100):
        """初期化

        Args:
            logger: 構造化ログヘルパー
            max_events: 集約する最大イベント数
        """
        self.logger = logger
        self.max_events = max_events
        self.events: list[dict[str, Any]] = []
        self.start_time = time.time()

    def add_event(self, event_type: str, **kwargs: Any) -> None:
        """イベントを追加

        Args:
            event_type: イベントタイプ
            **kwargs: イベント詳細
        """
        self.events.append({
            "timestamp": time.time(),
            "type": event_type,
            **kwargs
        })

        # 最大数を超えたら自動的にフラッシュ
        if len(self.events) >= self.max_events:
            self.flush()

    def flush(self, operation: str = "バッチ処理") -> None:
        """集約したイベントをログ出力

        Args:
            operation: 操作名
        """
        if not self.events:
            return

        elapsed_ms = (time.time() - self.start_time) * 1000

        # サマリー情報を計算
        event_types = {}
        for event in self.events:
            event_type = event.get("type", "unknown")
            event_types[event_type] = event_types.get(event_type, 0) + 1

        self.logger.info(
            f"{operation}完了",
            event_count=len(self.events),
            event_summary=event_types,
            elapsed_ms=elapsed_ms,
            events=self.events[:100]  # 最大100件まで
        )

        # リセット
        self.events.clear()
        self.start_time = time.time()

    def __enter__(self):
        """コンテキストマネージャーとして使用"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキスト終了時に自動フラッシュ"""
        self.flush()


# 便利な関数
def get_structured_logger(name: str) -> StructuredLogger:
    """構造化ログヘルパーを取得

    Args:
        name: ロガー名（通常は__name__）

    Returns:
        構造化ログヘルパー
    """
    return StructuredLogger(name)