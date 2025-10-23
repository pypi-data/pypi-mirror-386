#!/usr/bin/env python3
# File: src/noveler/infrastructure/monitoring/performance_monitor_v2.py
# Purpose: Enhanced performance monitoring with structured logging integration
# Context: Combines existing performance_monitor with new structured logging capabilities

"""統合パフォーマンス監視ユーティリティ

既存のperformance_monitorを構造化ログと統合し、
詳細なメトリクスとトレーサビリティを提供。
"""

import asyncio
import functools
import time
from collections.abc import Callable
from typing import Any, Optional, TypeVar

import psutil

from noveler.infrastructure.logging.structured_logger import (
    RequestContext,
    get_structured_logger,
)

F = TypeVar('F', bound=Callable[..., Any])


class EnhancedPerformanceMonitor:
    """拡張パフォーマンス監視クラス

    構造化ログを使用し、より詳細なメトリクスを記録。
    """

    def __init__(self) -> None:
        self.metrics = []
        self.logger = get_structured_logger(__name__)

    def monitor(
        self,
        name: Optional[str] = None,
        log_args: bool = False,
        log_result: bool = False,
        threshold_ms: float = 1000,  # ログ出力閾値（ミリ秒）
        threshold_memory_mb: float = 10  # メモリ変化閾値（MB）
    ) -> Callable[[F], F]:
        """拡張パフォーマンス監視デコレータ

        Args:
            name: 操作名（省略時は関数名を使用）
            log_args: 引数をログに含めるか
            log_result: 結果をログに含めるか
            threshold_ms: ログ出力する実行時間の閾値
            threshold_memory_mb: ログ出力するメモリ変化の閾値

        Returns:
            デコレートされた関数
        """
        def decorator(func: F) -> F:
            # 非同期関数の場合
            if asyncio.iscoroutinefunction(func):
                @functools.wraps(func)
                async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                    return await self._monitor_async(
                        func, name, log_args, log_result,
                        threshold_ms, threshold_memory_mb,
                        *args, **kwargs
                    )
                return async_wrapper  # type: ignore

            # 同期関数の場合
            else:
                @functools.wraps(func)
                def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                    return self._monitor_sync(
                        func, name, log_args, log_result,
                        threshold_ms, threshold_memory_mb,
                        *args, **kwargs
                    )
                return sync_wrapper  # type: ignore

        return decorator

    async def _monitor_async(
        self,
        func: Callable,
        name: Optional[str],
        log_args: bool,
        log_result: bool,
        threshold_ms: float,
        threshold_memory_mb: float,
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """非同期関数の監視実装"""
        func_name = name or f"{func.__module__}.{func.__name__}"

        # 開始時の状態を記録
        start_time = time.time()
        process = psutil.Process()
        start_memory = process.memory_info().rss / 1024 / 1024  # MB

        # CPUタイムも記録
        start_cpu_times = process.cpu_times()

        # 現在のコンテキストを取得
        context = RequestContext.get_current()

        try:
            # 関数実行
            result = await func(*args, **kwargs)

            # 終了時の状態を記録
            elapsed_ms = (time.time() - start_time) * 1000
            end_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_delta_mb = end_memory - start_memory

            # CPU使用率を計算
            end_cpu_times = process.cpu_times()
            cpu_user = end_cpu_times.user - start_cpu_times.user
            cpu_system = end_cpu_times.system - start_cpu_times.system

            # メトリクスを記録
            metric = self._create_metric(
                func_name, elapsed_ms, memory_delta_mb,
                start_memory, end_memory,
                cpu_user, cpu_system,
                success=True
            )
            self.metrics.append(metric)

            # 閾値を超えた場合、または常にログ出力する場合
            if elapsed_ms > threshold_ms or abs(memory_delta_mb) > threshold_memory_mb:
                log_data = {
                    "operation": func_name,
                    "elapsed_ms": elapsed_ms,
                    "memory_delta_mb": memory_delta_mb,
                    "memory_start_mb": start_memory,
                    "memory_end_mb": end_memory,
                    "cpu_user_seconds": cpu_user,
                    "cpu_system_seconds": cpu_system,
                    "success": True
                }

                if log_args:
                    log_data["args"] = str(args)[:500]
                    log_data["kwargs"] = str(kwargs)[:500]

                if log_result:
                    log_data["result_preview"] = str(result)[:500]

                self.logger.log_performance(
                    operation=func_name,
                    elapsed_ms=elapsed_ms,
                    success=True,
                    **log_data
                )

            return result

        except Exception as e:
            # エラー時の記録
            elapsed_ms = (time.time() - start_time) * 1000
            end_memory = process.memory_info().rss / 1024 / 1024
            memory_delta_mb = end_memory - start_memory

            # メトリクスを記録
            metric = self._create_metric(
                func_name, elapsed_ms, memory_delta_mb,
                start_memory, end_memory,
                0, 0, success=False,
                error_type=type(e).__name__
            )
            self.metrics.append(metric)

            # エラーログ
            self.logger.error(
                f"パフォーマンス監視中にエラー: {func_name}",
                error=e,
                operation=func_name,
                elapsed_ms=elapsed_ms,
                memory_delta_mb=memory_delta_mb
            )

            raise

    def _monitor_sync(
        self,
        func: Callable,
        name: Optional[str],
        log_args: bool,
        log_result: bool,
        threshold_ms: float,
        threshold_memory_mb: float,
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """同期関数の監視実装"""
        func_name = name or f"{func.__module__}.{func.__name__}"

        # 開始時の状態を記録
        start_time = time.time()
        process = psutil.Process()
        start_memory = process.memory_info().rss / 1024 / 1024  # MB

        # CPUタイムも記録
        start_cpu_times = process.cpu_times()

        try:
            # 関数実行
            result = func(*args, **kwargs)

            # 終了時の状態を記録
            elapsed_ms = (time.time() - start_time) * 1000
            end_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_delta_mb = end_memory - start_memory

            # CPU使用率を計算
            end_cpu_times = process.cpu_times()
            cpu_user = end_cpu_times.user - start_cpu_times.user
            cpu_system = end_cpu_times.system - start_cpu_times.system

            # メトリクスを記録
            metric = self._create_metric(
                func_name, elapsed_ms, memory_delta_mb,
                start_memory, end_memory,
                cpu_user, cpu_system,
                success=True
            )
            self.metrics.append(metric)

            # 閾値を超えた場合、または常にログ出力する場合
            if elapsed_ms > threshold_ms or abs(memory_delta_mb) > threshold_memory_mb:
                log_data = {
                    "operation": func_name,
                    "elapsed_ms": elapsed_ms,
                    "memory_delta_mb": memory_delta_mb,
                    "memory_start_mb": start_memory,
                    "memory_end_mb": end_memory,
                    "cpu_user_seconds": cpu_user,
                    "cpu_system_seconds": cpu_system,
                    "success": True
                }

                if log_args:
                    log_data["args"] = str(args)[:500]
                    log_data["kwargs"] = str(kwargs)[:500]

                if log_result:
                    log_data["result_preview"] = str(result)[:500]

                self.logger.log_performance(
                    operation=func_name,
                    elapsed_ms=elapsed_ms,
                    success=True,
                    **log_data
                )

            return result

        except Exception as e:
            # エラー時の記録
            elapsed_ms = (time.time() - start_time) * 1000
            end_memory = process.memory_info().rss / 1024 / 1024
            memory_delta_mb = end_memory - start_memory

            # メトリクスを記録
            metric = self._create_metric(
                func_name, elapsed_ms, memory_delta_mb,
                start_memory, end_memory,
                0, 0, success=False,
                error_type=type(e).__name__
            )
            self.metrics.append(metric)

            # エラーログ
            self.logger.error(
                f"パフォーマンス監視中にエラー: {func_name}",
                error=e,
                operation=func_name,
                elapsed_ms=elapsed_ms,
                memory_delta_mb=memory_delta_mb
            )

            raise

    def _create_metric(
        self,
        func_name: str,
        elapsed_ms: float,
        memory_delta_mb: float,
        start_memory: float,
        end_memory: float,
        cpu_user: float,
        cpu_system: float,
        success: bool,
        error_type: Optional[str] = None
    ) -> dict[str, Any]:
        """メトリクス辞書を作成"""
        metric = {
            "function": func_name,
            "elapsed_ms": elapsed_ms,
            "memory_delta_mb": memory_delta_mb,
            "start_memory_mb": start_memory,
            "end_memory_mb": end_memory,
            "cpu_user_seconds": cpu_user,
            "cpu_system_seconds": cpu_system,
            "success": success,
            "timestamp": time.time()
        }

        # リクエストコンテキストがあれば追加
        context = RequestContext.get_current()
        if context:
            metric["request_id"] = context.request_id
            metric["operation"] = context.operation
            metric["episode_number"] = context.episode_number

        if error_type:
            metric["error_type"] = error_type

        return metric

    def get_summary(self) -> dict[str, Any]:
        """パフォーマンスサマリーを取得（構造化）"""
        if not self.metrics:
            return {}

        # 全体統計
        total_duration_ms = sum(m["elapsed_ms"] for m in self.metrics)
        total_memory_mb = sum(abs(m["memory_delta_mb"]) for m in self.metrics)
        success_count = sum(1 for m in self.metrics if m["success"])
        error_count = len(self.metrics) - success_count

        # 関数別の集計
        func_stats = {}
        for metric in self.metrics:
            func = metric["function"]
            if func not in func_stats:
                func_stats[func] = {
                    "count": 0,
                    "success_count": 0,
                    "error_count": 0,
                    "total_duration_ms": 0,
                    "max_duration_ms": 0,
                    "min_duration_ms": float('inf'),
                    "avg_duration_ms": 0,
                    "total_memory_mb": 0,
                    "total_cpu_seconds": 0,
                    "errors": []
                }

            stats = func_stats[func]
            stats["count"] += 1
            stats["total_duration_ms"] += metric["elapsed_ms"]
            stats["max_duration_ms"] = max(stats["max_duration_ms"], metric["elapsed_ms"])
            stats["min_duration_ms"] = min(stats["min_duration_ms"], metric["elapsed_ms"])
            stats["total_memory_mb"] += abs(metric["memory_delta_mb"])
            stats["total_cpu_seconds"] += metric["cpu_user_seconds"] + metric["cpu_system_seconds"]

            if metric["success"]:
                stats["success_count"] += 1
            else:
                stats["error_count"] += 1
                if "error_type" in metric:
                    stats["errors"].append(metric["error_type"])

        # 平均を計算
        for stats in func_stats.values():
            if stats["count"] > 0:
                stats["avg_duration_ms"] = stats["total_duration_ms"] / stats["count"]

        return {
            "total_calls": len(self.metrics),
            "success_calls": success_count,
            "error_calls": error_count,
            "total_duration_ms": total_duration_ms,
            "total_memory_change_mb": total_memory_mb,
            "function_stats": func_stats,
            "timestamp": time.time()
        }

    def log_summary(self) -> None:
        """サマリーを構造化ログに出力"""
        summary = self.get_summary()
        if not summary:
            self.logger.info("パフォーマンスデータなし")
            return

        self.logger.info(
            "パフォーマンスサマリー",
            total_calls=summary["total_calls"],
            success_calls=summary["success_calls"],
            error_calls=summary["error_calls"],
            total_duration_ms=summary["total_duration_ms"],
            total_memory_change_mb=summary["total_memory_change_mb"],
            function_count=len(summary["function_stats"]),
            top_functions=self._get_top_functions(summary["function_stats"], 5)
        )

    def _get_top_functions(self, func_stats: dict, limit: int = 5) -> list[dict]:
        """上位の重い関数を取得"""
        sorted_funcs = sorted(
            func_stats.items(),
            key=lambda x: x[1]["total_duration_ms"],
            reverse=True
        )

        top_funcs = []
        for func, stats in sorted_funcs[:limit]:
            top_funcs.append({
                "name": func,
                "calls": stats["count"],
                "total_ms": stats["total_duration_ms"],
                "avg_ms": stats["avg_duration_ms"],
                "memory_mb": stats["total_memory_mb"]
            })

        return top_funcs


# グローバルインスタンス
enhanced_monitor = EnhancedPerformanceMonitor()


def performance_monitor(
    name: Optional[str] = None,
    **kwargs: Any
) -> Callable[[F], F]:
    """拡張パフォーマンス監視デコレータ（便利関数）

    Args:
        name: 操作名
        **kwargs: monitor()メソッドの追加引数

    Returns:
        デコレートされた関数
    """
    return enhanced_monitor.monitor(name, **kwargs)


# 後方互換性のためのエイリアス
def print_performance_summary() -> None:
    """パフォーマンスサマリーをログ出力（後方互換）"""
    enhanced_monitor.log_summary()