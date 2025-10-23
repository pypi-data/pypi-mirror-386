#!/usr/bin/env python3
# File: src/noveler/infrastructure/logging/log_decorators.py
# Purpose: Decorators for automatic logging of execution metrics and errors
# Context: Integrates with structured_logger for standardized performance tracking

"""ロギング用デコレータ

実行時メトリクスの自動ログ出力、エラーハンドリング、
パフォーマンス計測を提供するデコレータ集。
"""

import asyncio
import random
import time
import traceback
import warnings
from functools import wraps
from typing import Any, Callable, Mapping, Optional, TypeVar, Union

from noveler.infrastructure.logging.structured_logger import (
    ErrorCategory,
    RequestContext,
    StructuredLogger,
    get_structured_logger,
)

F = TypeVar('F', bound=Callable[..., Any])


def log_execution(
    operation_name: Optional[str] = None,
    include_args: bool = False,
    include_result: bool = False,
    error_category: ErrorCategory = ErrorCategory.BUSINESS_LOGIC,
    sample_rate: float = 1.0,
    *,
    logger: Optional[StructuredLogger] = None,
) -> Callable[[F], F]:
    """実行時メトリクスを自動的にログ出力するデコレータ

    Args:
        operation_name: 操作名（省略時は関数名を使用）
        include_args: 引数をログに含めるか
        include_result: 結果をログに含めるか
        error_category: エラー時のカテゴリ
        sample_rate: サンプリングレート（0.0-1.0）

    Returns:
        デコレートされた関数
    """
    def decorator(func: F) -> F:
        # 互換性のため、logger引数が設定されている場合は使用。
        # v3.0.0以降は内部で自動解決されるため、指定された場合は非推奨とする。
        if logger is not None:
            warnings.warn(
                "Passing logger to log_execution is deprecated; StructuredLogger is resolved internally.",
                DeprecationWarning,
                stacklevel=2,
            )

        # 非同期関数の場合
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # サンプリング判定
                if random.random() > sample_rate:
                    return await func(*args, **kwargs)

                op_name = operation_name or f"{func.__module__}.{func.__name__}"
                structured_logger = logger or get_structured_logger(func.__module__)
                start_time = time.time()

                # コンテキスト情報を準備
                context = {"operation": op_name}
                if include_args:
                    context["args"] = str(args)[:500]  # 長すぎる場合は切り詰め
                    context["kwargs"] = str(kwargs)[:500]

                try:
                    result = await func(*args, **kwargs)
                    elapsed_ms = (time.time() - start_time) * 1000

                    log_context = {
                        "elapsed_ms": elapsed_ms,
                        "execution_time_ms": elapsed_ms,
                        "success": True,
                        **context
                    }

                    if include_result:
                        log_context["result"] = str(result)[:500]

                    structured_logger.info(f"{op_name}完了", **log_context)
                    return result

                except Exception as e:
                    elapsed_ms = (time.time() - start_time) * 1000

                    structured_logger.error(
                        f"{op_name}失敗",
                        error=e,
                        category=error_category,
                        elapsed_ms=elapsed_ms,
                        execution_time_ms=elapsed_ms,
                        **context
                    )
                    raise

            return async_wrapper  # type: ignore

        # 同期関数の場合
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # サンプリング判定
                if random.random() > sample_rate:
                    return func(*args, **kwargs)

                op_name = operation_name or f"{func.__module__}.{func.__name__}"
                structured_logger = logger or get_structured_logger(func.__module__)
                start_time = time.time()

                # コンテキスト情報を準備
                context = {"operation": op_name}
                if include_args:
                    context["args"] = str(args)[:500]
                    context["kwargs"] = str(kwargs)[:500]

                try:
                    result = func(*args, **kwargs)
                    elapsed_ms = (time.time() - start_time) * 1000

                    log_context = {
                        "elapsed_ms": elapsed_ms,
                        "execution_time_ms": elapsed_ms,
                        "success": True,
                        **context
                    }

                    if include_result:
                        log_context["result"] = str(result)[:500]

                    structured_logger.info(f"{op_name}完了", **log_context)
                    return result

                except Exception as e:
                    elapsed_ms = (time.time() - start_time) * 1000

                    structured_logger.error(
                        f"{op_name}失敗",
                        error=e,
                        category=error_category,
                        elapsed_ms=elapsed_ms,
                        execution_time_ms=elapsed_ms,
                        **context
                    )
                    raise

            return sync_wrapper  # type: ignore

    return decorator


def log_llm_execution(
    model_name: str = "unknown",
    *,
    logger: Optional[StructuredLogger] = None,
) -> Callable[[F], F]:
    """LLM呼び出し専用のログデコレータ

    Args:
        model_name: 使用モデル名

    Returns:
        デコレートされた関数
    """
    def decorator(func: F) -> F:
        if logger is not None:
            warnings.warn(
                "Passing logger to log_llm_execution is deprecated; StructuredLogger is resolved internally.",
                DeprecationWarning,
                stacklevel=2,
            )

        @wraps(func)
        async def wrapper(*args, **kwargs):
            structured_logger = logger or get_structured_logger(func.__module__)
            start_time = time.time()

            prompt_text = _extract_prompt(args, kwargs)

            try:
                # LLM呼び出し実行
                result = await func(*args, **kwargs)
                elapsed_ms = (time.time() - start_time) * 1000

                model, prompt_tokens, completion_tokens, total_cost, extra_info = _extract_llm_metadata(result)
                extra_info.setdefault("prompt_length", len(prompt_text) if prompt_text else 0)
                extra_info.setdefault("operation", f"{func.__module__}.{func.__name__}")

                structured_logger.log_llm_call(
                    model=model or model_name,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_cost=total_cost,
                    elapsed_ms=elapsed_ms,
                    success=True,
                    **extra_info,
                )

                return result

            except Exception as e:
                elapsed_ms = (time.time() - start_time) * 1000

                structured_logger.error(
                    f"LLM呼び出し失敗: {model_name}",
                    error=e,
                    category=ErrorCategory.LLM,
                    model=model_name,
                    elapsed_ms=elapsed_ms
                )
                raise

        return wrapper  # type: ignore

    return decorator


def _extract_prompt(args: tuple[Any, ...], kwargs: dict[str, Any]) -> Optional[str]:
    if args:
        candidate = args[0]
        if isinstance(candidate, str):
            return candidate
    prompt_kw = kwargs.get("prompt")
    if isinstance(prompt_kw, str):
        return prompt_kw
    return None


def _extract_llm_metadata(result: Any) -> tuple[Optional[str], int, int, float, dict[str, Any]]:
    data: Optional[Mapping[str, Any]] = None
    if isinstance(result, Mapping):
        data = result
    elif hasattr(result, "__dict__"):
        data = getattr(result, "__dict__")

    model: Optional[str] = None
    prompt_tokens = 0
    completion_tokens = 0
    total_cost = 0.0
    extra_info: dict[str, Any] = {}

    if data:
        model = data.get("model") or data.get("model_name")
        tokens = data.get("tokens")
        if isinstance(tokens, Mapping):
            prompt_tokens = int(tokens.get("input") or tokens.get("prompt") or 0)
            completion_tokens = int(tokens.get("output") or tokens.get("completion") or 0)
            extra_info["tokens"] = dict(tokens)

        if "prompt_tokens" in data:
            prompt_tokens = int(data.get("prompt_tokens", prompt_tokens))
        if "completion_tokens" in data:
            completion_tokens = int(data.get("completion_tokens", completion_tokens))

        if "total_cost" in data:
            try:
                total_cost = float(data.get("total_cost", total_cost))
            except (TypeError, ValueError):
                total_cost = total_cost

        # carry additional scalar metadata for logging insight
        for key in ("temperature", "stop_reason", "usage", "response", "raw_response"):
            if key in data and key not in extra_info:
                extra_info[key] = data[key]

    return model, prompt_tokens, completion_tokens, total_cost, extra_info


def log_cache_operation(cache_name: str = "default") -> Callable[[F], F]:
    """キャッシュ操作のログデコレータ

    Args:
        cache_name: キャッシュ名

    Returns:
        デコレートされた関数
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_structured_logger(func.__module__)
            operation = func.__name__

            # キャッシュキーを引数から推定（最初の引数をキーとする）
            cache_key = str(args[0]) if args else "unknown"

            try:
                result = func(*args, **kwargs)

                # キャッシュヒット/ミスの判定
                if operation == "get":
                    is_hit = result is not None
                    logger.debug(
                        f"キャッシュ{'ヒット' if is_hit else 'ミス'}",
                        cache_name=cache_name,
                        cache_key=cache_key,
                        operation=operation,
                        cache_hit=is_hit
                    )
                else:
                    logger.debug(
                        f"キャッシュ操作: {operation}",
                        cache_name=cache_name,
                        cache_key=cache_key,
                        operation=operation
                    )

                return result

            except Exception as e:
                logger.error(
                    f"キャッシュ操作失敗: {operation}",
                    error=e,
                    category=ErrorCategory.CACHE,
                    cache_name=cache_name,
                    cache_key=cache_key,
                    operation=operation
                )
                raise

        return wrapper  # type: ignore

    return decorator


def with_request_context(
    operation: Optional[str] = None,
    episode_number: Optional[int] = None,
    **context: Any,
) -> Callable[[F], F]:
    """リクエストコンテキストを自動設定するデコレータ

    Args:
        operation: 操作名（省略時は関数のモジュール+関数名）
        episode_number: エピソード番号
        **context: request_id など追加のリクエストコンテキスト情報

    Returns:
        デコレートされた関数
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation or f"{func.__module__}.{func.__name__}"
            payload = dict(context)
            if episode_number is not None:
                payload.setdefault("episode_number", episode_number)
            payload.setdefault("operation", op_name)

            existing_context = RequestContext.get_current()
            if existing_context:
                existing_context.update(**payload)
                return func(*args, **kwargs)

            with RequestContext(**payload):
                return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


def log_on_error(
    category: ErrorCategory = ErrorCategory.BUSINESS_LOGIC,
    reraise: bool = True,
    default_return: Any = None
) -> Callable[[F], F]:
    """エラー時のみログを出力するデコレータ

    Args:
        category: エラーカテゴリ
        reraise: エラーを再発生させるか
        default_return: reraiseがFalseの場合の返り値

    Returns:
        デコレートされた関数
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger = get_structured_logger(func.__module__)
                logger.error(
                    f"{func.__name__}でエラー発生",
                    error=e,
                    category=category,
                    function=func.__name__,
                    module=func.__module__,
                    traceback=traceback.format_exc()
                )

                if reraise:
                    raise
                return default_return

        return wrapper  # type: ignore

    return decorator


def sampled_log(rate: float = 0.1) -> Callable[[F], F]:
    """高頻度イベントのサンプリングログデコレータ

    Args:
        rate: サンプリングレート（0.0-1.0）

    Returns:
        デコレートされた関数
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # サンプリング判定
            if random.random() < rate:
                logger = get_structured_logger(func.__module__)
                logger.debug(
                    f"[SAMPLED] {func.__name__}実行",
                    function=func.__name__,
                    sample_rate=rate
                )

            return result

        return wrapper  # type: ignore

    return decorator
