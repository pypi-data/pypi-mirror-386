#!/usr/bin/env python3
"""パフォーマンス監視ユーティリティ
処理時間とメモリ使用量を監視
"""

import functools
import time
from collections.abc import Callable

import psutil

from noveler.infrastructure.logging.unified_logger import get_logger

# ロガー設定
logger = get_logger(__name__)


class PerformanceMonitor:
    """パフォーマンス監視クラス"""

    def __init__(self) -> None:
        self.metrics = []

    def monitor(self, name: str) -> Callable[[Callable], Callable]:
        """パフォーマンス監視デコレータ"""

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args: object, **kwargs: object) -> object:
                # 開始時の状態を記録
                start_time = time.time()
                process = psutil.Process()
                start_memory = process.memory_info().rss / 1024 / 1024  # MB

                # 関数名
                func_name = name or f"{func.__module__}.{func.__name__}"

                try:
                    # 関数実行
                    result = func(*args, **kwargs)

                    # 終了時の状態を記録
                    end_time = time.time()
                    end_memory = process.memory_info().rss / 1024 / 1024  # MB

                    # メトリクス計算
                    duration = end_time - start_time
                    memory_delta = end_memory - start_memory

                    # 記録
                    metric = {
                        "function": func_name,
                        "duration": duration,
                        "memory_delta": memory_delta,
                        "start_memory": start_memory,
                        "end_memory": end_memory,
                        "timestamp": start_time,
                    }
                    self.metrics.append(metric)

                    # ログ出力(1秒以上または10MB以上の場合)
                    if duration > 1.0 or abs(memory_delta) > 10:
                        self.logger_service.info(f"🔍 パフォーマンス: 実行時間 {duration:.2f}s, メモリ変化 {memory_delta:.1f}MB")

                    return result

                except Exception as e:
                    # エラー時も記録
                    end_time = time.time()
                    duration = end_time - start_time

                    logger.exception(
                        f"❌ エラー: {func_name} - 実行時間: {duration:.2f}秒で例外発生: {e}",
                    )

                    raise

            return wrapper

        return decorator

    def get_summary(self) -> dict[str, object]:
        """パフォーマンスサマリーを取得"""
        if not self.metrics:
            return {}

        total_duration = sum(m["duration"] for m in self.metrics)
        total_memory = sum(abs(m["memory_delta"]) for m in self.metrics)

        # 関数別の集計
        func_stats = {}
        for metric in self.metrics:
            func = metric["function"]
            if func not in func_stats:
                func_stats[func] = {
                    "count": 0,
                    "total_duration": 0,
                    "max_duration": 0,
                    "total_memory": 0,
                }

            stats = func_stats[func]
            stats["count"] += 1
            stats["total_duration"] += metric["duration"]
            stats["max_duration"] = max(stats["max_duration"], metric["duration"])
            stats["total_memory"] += abs(metric["memory_delta"])

        return {
            "total_calls": len(self.metrics),
            "total_duration": total_duration,
            "total_memory_change": total_memory,
            "function_stats": func_stats,
        }

    def print_summary(self) -> None:
        """サマリーを表示"""
        summary = self.get_summary()
        if not summary:
            self.console_service.print("📊 パフォーマンスデータなし")
            return

        self.console_service.print("\n" + "=" * 60)
        self.console_service.print("📊 パフォーマンスサマリー")
        self.console_service.print("=" * 60)

        self.console_service.print(f"総呼び出し回数: {summary['total_calls']}")
        self.console_service.print(f"総実行時間: {summary['total_duration']:.2f}秒")
        self.console_service.print(f"総メモリ変化: {summary['total_memory_change']:.1f}MB")

        self.console_service.print("\n関数別統計:")
        self.console_service.print("-" * 60)

        # 実行時間でソート
        func_stats = summary["function_stats"]
        sorted_funcs = sorted(
            func_stats.items(),
            key=lambda x: x[1]["total_duration"],
            reverse=True,
        )

        for func, stats in sorted_funcs[:10]:  # 上位10件
            avg_duration = stats["total_duration"] / stats["count"]
            self.console_service.print(f"\n{func}:")
            self.console_service.print(f"  呼び出し回数: {stats['count']}回")
            self.console_service.print(f"  総実行時間: {stats['total_duration']:.2f}秒")
            self.console_service.print(f"  平均実行時間: {avg_duration:.3f}秒")
            self.console_service.print(f"  最大実行時間: {stats['max_duration']:.3f}秒")
            self.console_service.print(f"  総メモリ変化: {stats['total_memory_change']:.2f}MB")


# グローバルインスタンス
monitor = PerformanceMonitor()


def performance_monitor(name: str) -> Callable[[Callable], Callable]:
    """簡易パフォーマンス監視デコレータ"""
    return monitor.monitor(name)


def print_performance_summary() -> None:
    """パフォーマンスサマリーを表示"""
    monitor.print_summary()


# 使用例:
# @performance_monitor()
# def heavy_process():
#     time.sleep(1)
#     return "完了"
#
# @performance_monitor("カスタム名")
# def another_process():
#     data = list(range(1000000))
#     return sum(data)
