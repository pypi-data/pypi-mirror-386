#!/usr/bin/env python3
# File: src/noveler/infrastructure/performance/comprehensive_performance_optimizer.py
# Purpose: Provide lightweight yet feature-complete performance optimisation helpers with graceful fallbacks.
# Context: Imported by CLI tools, MCP servers, and the test-suite to monitor workflow performance and optimise I/O.
"""Comprehensive performance optimisation utilities.

The real system relies on optional third-party libraries such as ``psutil`` and
``PyYAML``.  This module keeps the production API intact while exposing
lightweight fallbacks so that unit tests can exercise the behaviour even when
those dependencies are unavailable on the executing machine.
"""

from __future__ import annotations

import asyncio
import functools
import gc
import json
import os
import sys
import time
import tracemalloc
from collections import deque
from collections.abc import Callable, Iterable
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

try:  # Optional dependency – the code falls back to tracemalloc when missing.
    import psutil  # type: ignore[import]
except Exception:  # pragma: no cover - absence is expected in some environments
    psutil = None  # type: ignore[assignment]

try:  # PyYAML is optional for environments focusing on dry tests.
    import yaml  # type: ignore[import]
except Exception:  # pragma: no cover - handled by runtime checks
    yaml = None  # type: ignore[assignment]


def _now() -> float:
    """Return a high-resolution time stamp."""
    return time.perf_counter()


def _process() -> Any | None:
    """Return a process handle when ``psutil`` is available."""
    if psutil is None:
        return None
    try:
        return psutil.Process()
    except Exception:  # pragma: no cover - defensive guard only
        return None


def _memory_usage_mb(process: Any | None = None) -> float:
    """Return RSS memory usage in megabytes."""
    if process is None:
        process = _process()
    if process is None:
        if tracemalloc.is_tracing():
            current, _ = tracemalloc.get_traced_memory()
            return current / (1024 * 1024)
        return 0.0
    try:
        return process.memory_info().rss / (1024 * 1024)
    except Exception:  # pragma: no cover - platform dependent
        return 0.0


def _cpu_percent(process: Any | None) -> float:
    """Return CPU percentage delta."""
    if process is None:
        return 0.0
    try:
        return process.cpu_percent(interval=None)
    except Exception:  # pragma: no cover - platform dependent
        return 0.0


def _io_counters(process: Any | None) -> tuple[int, int]:
    """Return (read_bytes, write_bytes) counters."""
    if process is None:
        return (0, 0)
    try:
        counters = process.io_counters()
        return counters.read_bytes, counters.write_bytes
    except Exception:  # pragma: no cover - platform dependent
        return (0, 0)


@dataclass
class PerformanceMetrics:
    """Aggregate metrics captured for an observed function."""

    function_name: str
    duration: float
    memory_start: float
    memory_end: float
    memory_peak: float
    cpu_percent: float
    io_read: int
    io_write: int
    timestamp: float
    call_count: int = 1
    error_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0


@dataclass
class OptimizationResult:
    """Describe an optimisation pass result."""

    optimization_type: str
    before_metrics: dict[str, Any]
    after_metrics: dict[str, Any]
    improvement_percent: float
    memory_savings_mb: float
    time_savings_seconds: float
    recommendations: list[str] = field(default_factory=list)


class PerformanceProfiler:
    """Collect execution metrics with minimal dependencies."""

    def __init__(self, operation_name: str | None = None) -> None:
        self.metrics: dict[str, PerformanceMetrics] = {}
        self.call_stack: deque[str] = deque(maxlen=1000)
        self.memory_snapshots: list[tuple[float, float]] = []
        self.bottlenecks: list[dict[str, Any]] = []
        self.operation_name: str | None = None
        self.start_time: float | None = None
        self.memory_before: float | None = None
        self.memory_after: float | None = None
        self.memory_peak_mb: float | None = None
        self._active_session: dict[str, Any] | None = None
        if operation_name:
            self.start(operation_name)

    def start(self, operation_name: str) -> None:
        """Begin a profiling session."""
        process = _process()
        self.operation_name = operation_name
        self.start_time = _now()
        self.memory_before = _memory_usage_mb(process)
        self._active_session = {
            "process": process,
            "cpu_start": _cpu_percent(process),
            "io_start": _io_counters(process),
            "timestamp": time.time(),
        }
        if not tracemalloc.is_tracing():
            tracemalloc.start()

    def stop(self) -> dict[str, Any]:
        """Stop the active session and return captured metrics."""
        if not self._active_session or self.operation_name is None or self.start_time is None:
            raise RuntimeError("Profiling session has not been started.")

        process = self._active_session["process"]
        end_time = _now()
        memory_end = _memory_usage_mb(process)
        cpu_end = _cpu_percent(process)
        io_read_end, io_write_end = _io_counters(process)
        io_read_start, io_write_start = self._active_session["io_start"]

        if tracemalloc.is_tracing():
            current_bytes, peak_bytes = tracemalloc.get_traced_memory()
            tracemalloc.stop()
        else:  # pragma: no cover - defensive guard only
            current_bytes = peak_bytes = 0
        self.memory_after = memory_end
        self.memory_peak_mb = peak_bytes / (1024 * 1024)

        duration = end_time - self.start_time
        metrics = PerformanceMetrics(
            function_name=self.operation_name,
            duration=duration,
            memory_start=self.memory_before or 0.0,
            memory_end=memory_end,
            memory_peak=self.memory_peak_mb,
            cpu_percent=cpu_end - self._active_session["cpu_start"],
            io_read=io_read_end - io_read_start,
            io_write=io_write_end - io_write_start,
            timestamp=self._active_session["timestamp"],
        )

        existing = self.metrics.get(self.operation_name)
        if existing:
            existing.duration += metrics.duration
            existing.call_count += 1
            existing.memory_end = metrics.memory_end
            existing.memory_peak = max(existing.memory_peak, metrics.memory_peak)
            existing.cpu_percent = metrics.cpu_percent
            existing.io_read += metrics.io_read
            existing.io_write += metrics.io_write
        else:
            self.metrics[self.operation_name] = metrics

        snapshot_time = time.time()
        self.memory_snapshots.append((snapshot_time, memory_end))

        result = {
            "operation_name": self.operation_name,
            "execution_time": duration,
            "memory_start_mb": metrics.memory_start,
            "memory_end_mb": metrics.memory_end,
            "memory_peak_mb": metrics.memory_peak,
            "cpu_percent": metrics.cpu_percent,
            "io_read_bytes": metrics.io_read,
            "io_write_bytes": metrics.io_write,
            "timestamp": metrics.timestamp,
        }
        self._active_session = None
        return result

    def start_profiling(self) -> None:
        """Legacy API retained for backward compatibility."""
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        gc.collect()

    def stop_profiling(self) -> tuple[int, int]:
        """Legacy API retained for backward compatibility."""
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return current, peak

    @contextmanager
    def profile_function(self, function_name: str) -> None:
        """Context manager wrapper for profiling function bodies."""
        self.start(function_name)
        try:
            yield
        finally:
            self.stop()


class CacheManager:
    """Simple LRU cache with TTL support."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int | None = None, ttl: int | None = None) -> None:
        ttl_value = ttl_seconds if ttl_seconds is not None else ttl
        self.ttl_seconds = ttl_value if ttl_value is not None else 3600
        self.cache: dict[str, tuple[Any, float]] = {}
        self.access_times: dict[str, float] = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Any | None:
        """Return a cached entry when still valid."""
        if key in self.cache:
            value, created = self.cache[key]
            if time.time() - created < self.ttl_seconds:
                self.hits += 1
                self.access_times[key] = time.time()
                return value
            self.invalidate(key)
        self.misses += 1
        return None

    def set(self, key: str, value: Any) -> None:
        """Store an entry respecting the cache size."""
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        self.cache[key] = (value, time.time())
        self.access_times[key] = time.time()

    def _evict_lru(self) -> None:
        if not self.access_times:
            return
        oldest_key = min(self.access_times, key=self.access_times.__getitem__)
        self.cache.pop(oldest_key, None)
        self.access_times.pop(oldest_key, None)

    def invalidate(self, key: str) -> None:
        """Invalidate a single entry."""
        self.cache.pop(key, None)
        self.access_times.pop(key, None)

    def clear(self) -> None:
        """Clear all entries."""
        self.cache.clear()
        self.access_times.clear()

    def get_hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total else 0.0

    def get_hit_ratio(self) -> float:
        """Alias used by parts of the code base."""
        return self.get_hit_rate()


class FileIOOptimizer:
    """Provide cached reads and batched writes for file operations."""

    def __init__(self, read_cache: CacheManager | None = None) -> None:
        self.read_cache = read_cache or CacheManager(max_size=512, ttl_seconds=600)
        self.batch_operations: list[tuple[Path, str, str]] = []

    def optimized_read_text(self, file_path: Path | str, encoding: str = "utf-8") -> str:
        path = Path(file_path)
        with path.open("r", encoding=encoding) as handle:
            return handle.read()

    def optimized_read(self, file_path: Path | str) -> str:
        return self.optimized_read_text(file_path)

    def cached_read(self, file_path: Path | str, encoding: str = "utf-8") -> str:
        path = Path(file_path)
        cache_key = f"read::{path.resolve()}::{encoding}"
        cached = self.read_cache.get(cache_key)
        if cached is not None:
            return cached
        content = self.optimized_read_text(path, encoding)
        self.read_cache.set(cache_key, content)
        return content

    def schedule_write(self, file_path: Path | str, content: str, encoding: str = "utf-8") -> None:
        self.batch_operations.append((Path(file_path), content, encoding))

    def flush_batch_operations(self) -> None:
        operations = [(path, content) for (path, content, _) in self.batch_operations]
        self.batch_write(operations)
        self.batch_operations.clear()

    def batch_write(self, operations: Iterable[tuple[Path | str, str]]) -> list[tuple[Path, bool]]:
        results: list[tuple[Path, bool]] = []
        for file_path, content in operations:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            results.append((path, True))
        return results

    def async_write(self, file_path: Path | str, content: str, encoding: str = "utf-8") -> bool:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding=encoding)
        return True

    def batch_read(self, file_paths: Iterable[Path | str], encoding: str = "utf-8") -> list[tuple[Path, str, bool]]:
        results: list[tuple[Path, str, bool]] = []
        for file_path in file_paths:
            path = Path(file_path)
            try:
                content = self.cached_read(path, encoding)
                results.append((path, content, True))
            except Exception:
                results.append((path, "", False))
        return results


class YAMLOptimizer:
    """Optimise YAML load/dump operations with caching."""

    def __init__(self) -> None:
        self.yaml_cache = CacheManager(max_size=200, ttl_seconds=600)

    @staticmethod
    def _ensure_yaml() -> None:
        if yaml is None:
            raise RuntimeError("PyYAML is required for YAML optimisations.")

    def optimized_yaml_load(self, file_path: Path) -> Any:
        self._ensure_yaml()
        with file_path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle)  # type: ignore[union-attr]

    def optimized_yaml_dump(self, data: Any, file_path: Path, **kwargs: Any) -> bool:
        self._ensure_yaml()
        yaml_kwargs = {"allow_unicode": True, "default_flow_style": False, "sort_keys": False, **kwargs}
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as handle:
            yaml.dump(data, handle, **yaml_kwargs)  # type: ignore[union-attr]
        return True

    def optimized_load(self, file_path: Path) -> Any:
        return self.optimized_yaml_load(file_path)

    def optimized_dump(self, data: Any, file_path: Path, **kwargs: Any) -> bool:
        return self.optimized_yaml_dump(data, file_path, **kwargs)

    def cached_load(self, file_path: Path) -> Any:
        cache_key = f"yaml::{file_path.resolve()}::{file_path.stat().st_mtime}"
        cached = self.yaml_cache.get(cache_key)
        if cached is not None:
            return cached
        data = self.optimized_yaml_load(file_path)
        self.yaml_cache.set(cache_key, data)
        return data

    def batch_load(self, file_paths: Iterable[Path]) -> list[tuple[Path, Any, bool]]:
        results: list[tuple[Path, Any, bool]] = []
        for file_path in file_paths:
            try:
                data = self.cached_load(file_path)
                results.append((file_path, data, True))
            except Exception:
                results.append((file_path, {}, False))
        return results


class AsyncOperationOptimizer:
    """Throttle asynchronous file operations."""

    def __init__(self, max_concurrent: int = 10) -> None:
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def parallel_file_processing(self, file_paths: Iterable[Path], processor_func: Callable[[Path], Any]) -> list[Any]:
        async def _process(path: Path) -> Any:
            async with self.semaphore:
                return await asyncio.to_thread(processor_func, path)

        return await asyncio.gather(*[_process(Path(path)) for path in file_paths])


class MemoryOptimizer:
    """Utility helpers for memory focussed workflows."""

    def get_memory_usage(self) -> dict[str, float]:
        process = _process()
        rss_mb = _memory_usage_mb(process)
        vms_mb = 0.0
        if process is not None:
            try:
                vms_mb = process.memory_info().vms / (1024 * 1024)
            except Exception:  # pragma: no cover - platform dependent
                vms_mb = 0.0
        return {"rss_mb": rss_mb, "vms_mb": vms_mb}

    def force_garbage_collection(self) -> int:
        return gc.collect()

    def chunk_process_large_data(self, data: Iterable[Any], processor_func: Callable[[list[Any]], list[Any]], chunk_size: int = 100) -> list[Any]:
        processed: list[Any] = []
        chunk: list[Any] = []
        for item in data:
            chunk.append(item)
            if len(chunk) >= chunk_size:
                processed.extend(processor_func(chunk))
                chunk = []
        if chunk:
            processed.extend(processor_func(chunk))
        return processed

    def optimize_data_structure(self, data: dict[str, Any]) -> dict[str, Any]:
        optimized = {}
        for key, value in data.items():
            if isinstance(value, list) and len(value) > 256:
                optimized[key] = tuple(value)
            else:
                optimized[key] = value
        return optimized


class ComprehensivePerformanceOptimizer:
    """Facade combining profiling, caching and optimisation helpers."""

    def __init__(self) -> None:
        self.profiler = PerformanceProfiler()
        self.cache_manager = CacheManager()
        self.file_io_optimizer = FileIOOptimizer(self.cache_manager)
        self.yaml_optimizer = YAMLOptimizer()
        self.memory_optimizer = MemoryOptimizer()
        self.async_optimizer = AsyncOperationOptimizer()
        self.optimization_results: list[OptimizationResult] = []
        self._profiling_history: list[dict[str, Any]] = []
        self._profiling_depth = 0

    def performance_monitor(self, name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator capturing metrics for synchronous and asynchronous callables."""

        def _decorate(func: Callable[..., Any], label: str | None) -> Callable[..., Any]:
            target_name = label or f"{func.__module__}.{func.__name__}"

            if asyncio.iscoroutinefunction(func):

                @functools.wraps(func)
                async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                    self.start_profiling(target_name)
                    try:
                        return await func(*args, **kwargs)
                    finally:
                        self.stop_profiling()

                return async_wrapper

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                self.start_profiling(target_name)
                try:
                    return func(*args, **kwargs)
                finally:
                    self.stop_profiling()

            return sync_wrapper

        if callable(name):  # type: ignore[unreachable]
            return _decorate(name, None)
        return lambda func: _decorate(func, name)

    def start_profiling(self, operation_name: str) -> None:
        if self._profiling_depth == 0:
            self.profiler.start(operation_name)
        self._profiling_depth += 1

    def stop_profiling(self) -> dict[str, Any]:
        if self._profiling_depth == 0:
            return {}
        self._profiling_depth -= 1
        if self._profiling_depth > 0:
            return {}
        try:
            result = self.profiler.stop()
        except RuntimeError:
            return {}
        self._profiling_history.append(result)
        return result

    def optimize_file_operations(self, file_paths: Iterable[Path], mode: str = "read") -> list[Any]:
        if mode == "read":
            return [self.file_io_optimizer.cached_read(path) for path in file_paths]
        if mode == "write":
            operations = [(path, Path(path).read_text(encoding="utf-8")) for path in file_paths]
            return self.file_io_optimizer.batch_write(operations)
        return []

    def optimize_yaml_processing(self, yaml_files: Iterable[Path], mode: str = "load") -> list[Any]:
        if mode == "load":
            return [self.yaml_optimizer.cached_load(path) for path in yaml_files]
        if mode == "dump":
            return [self.yaml_optimizer.optimized_dump(data, path) for path, data in yaml_files]  # type: ignore[arg-type]
        return []

    def optimize_memory_usage(self) -> dict[str, Any]:
        before = self.memory_optimizer.get_memory_usage()
        collected = self.memory_optimizer.force_garbage_collection()
        after = self.memory_optimizer.get_memory_usage()
        return {
            "before_memory_mb": before["rss_mb"],
            "after_memory_mb": after["rss_mb"],
            "collected_objects": collected,
        }

    def analyze_bottlenecks(self) -> dict[str, Any]:
        if not self.profiler.metrics:
            return {"error": "No profiling data captured."}
        sorted_metrics = sorted(
            self.profiler.metrics.values(), key=lambda metric: metric.duration, reverse=True
        )
        total_duration = sum(metric.duration for metric in sorted_metrics)
        total_memory_change = sum(abs(metric.memory_end - metric.memory_start) for metric in sorted_metrics)
        top_bottlenecks: list[dict[str, Any]] = []
        for metric in sorted_metrics[:10]:
            percentage = (metric.duration / total_duration * 100) if total_duration else 0.0
            top_bottlenecks.append(
                {
                    "function": metric.function_name,
                    "duration": metric.duration,
                    "percentage_of_total": percentage,
                    "memory_delta": metric.memory_end - metric.memory_start,
                    "call_count": metric.call_count,
                    "average_duration": metric.duration / metric.call_count,
                    "io_operations": metric.io_read + metric.io_write,
                    "severity": self._classify_bottleneck_severity(metric, percentage),
                }
            )
        return {
            "total_functions_analyzed": len(self.profiler.metrics),
            "total_execution_time": total_duration,
            "total_memory_change": total_memory_change,
            "top_bottlenecks": top_bottlenecks,
            "cache_performance": {
                "hit_rate": self.cache_manager.get_hit_ratio(),
                "total_hits": self.cache_manager.hits,
                "total_misses": self.cache_manager.misses,
            },
        }

    def _classify_bottleneck_severity(self, metric: PerformanceMetrics, percentage: float) -> str:
        if percentage > 30 or metric.duration > 10:
            return "critical"
        if percentage > 15 or metric.duration > 5:
            return "high"
        if percentage > 5 or metric.duration > 1:
            return "medium"
        return "low"

    def generate_optimization_recommendations(self) -> list[str]:
        analysis = self.analyze_bottlenecks()
        if analysis.get("error"):
            return ["Not enough profiling data to determine recommendations."]
        recommendations: list[str] = []
        for bottleneck in analysis.get("top_bottlenecks", []):
            severity = bottleneck.get("severity")
            function_name = bottleneck.get("function")
            if severity in {"critical", "high"} and function_name:
                recommendations.append(f"Review {function_name} for optimisation opportunities.")
        cache_hit_rate = analysis["cache_performance"]["hit_rate"]
        if cache_hit_rate < 0.7:
            recommendations.append(f"Cache hit rate is {cache_hit_rate:.1%}. Consider increasing cache size or TTL.")
        return recommendations

    def generate_performance_report(self, output_path: Path | None = None) -> dict[str, Any]:
        analysis = self.analyze_bottlenecks()
        report = {
            "summary": {
                "operation_count": len(self._profiling_history),
                "total_execution_time": sum(item["execution_time"] for item in self._profiling_history),
            },
            "profiling_results": list(self._profiling_history),
            "cache_performance": {
                "hit_rate": self.cache_manager.get_hit_ratio(),
                "hits": self.cache_manager.hits,
                "misses": self.cache_manager.misses,
            },
            "analysis": analysis,
            "optimization_recommendations": self.generate_optimization_recommendations(),
            "optimization_results": [asdict(result) for result in self.optimization_results],
        }
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return report

    def apply_optimizations(self, target_functions: list[str] | None = None) -> list[OptimizationResult]:
        self.optimization_results.clear()
        if not target_functions or "file_io" in target_functions:
            result = OptimizationResult(
                optimization_type="file_io_batch_processing",
                before_metrics={"pending_operations": len(self.file_io_optimizer.batch_operations)},
                after_metrics={"pending_operations": 0},
                improvement_percent=0.0,
                memory_savings_mb=0.0,
                time_savings_seconds=0.0,
                recommendations=["Batch file writes to reduce I/O overhead."],
            )
            self.file_io_optimizer.flush_batch_operations()
            self.optimization_results.append(result)
        return self.optimization_results


performance_optimizer = ComprehensivePerformanceOptimizer()


def performance_monitor(name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Expose the decorator via a module-level helper."""
    return performance_optimizer.performance_monitor(name)


def generate_performance_summary() -> None:
    """Emit a human-readable performance summary."""
    analysis = performance_optimizer.analyze_bottlenecks()
    lines = ["=" * 80, "🚀 Comprehensive Performance Analysis", "=" * 80]
    if analysis.get("error"):
        lines.append(f"⚠️ {analysis['error']}")
    else:
        lines.append(f"Total functions analysed: {analysis['total_functions_analyzed']}")
        lines.append(f"Total execution time: {analysis['total_execution_time']:.3f} seconds")
        lines.append(f"Cache hit rate: {analysis['cache_performance']['hit_rate']:.1%}")
        lines.append("Top bottlenecks:")
        for bottleneck in analysis.get("top_bottlenecks", [])[:5]:
            lines.append(
                f" - {bottleneck['function']} :: {bottleneck['duration']:.3f}s ({bottleneck['severity']})"
            )
    lines.append("=" * 80)

    try:
        from noveler.presentation.shared.shared_utilities import console  # type: ignore

        for line in lines:
            console.print(line)
    except Exception:  # pragma: no cover - console unavailable outside CLI
        for line in lines:
            print(line)


if __name__ == "__main__":  # pragma: no cover - manual smoke execution
    @performance_monitor("example_operation")
    def _demo_operation(delay: float) -> str:
        time.sleep(delay)
        return "done"

    _demo_operation(0.01)
    performance_optimizer.generate_performance_report(Path("temp/performance_report.json"))
    generate_performance_summary()
