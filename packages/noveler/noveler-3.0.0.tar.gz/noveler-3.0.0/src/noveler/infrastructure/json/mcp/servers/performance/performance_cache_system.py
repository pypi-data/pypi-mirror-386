"""Performance monitoring and caching utilities for JSON conversion."""

import asyncio
import time
from pathlib import Path
from typing import Any

from noveler.infrastructure.logging.unified_logger import get_logger


class WritingSessionManager:
    """Manage writing session metadata for the JSON conversion server."""

    def __init__(self) -> None:
        self.sessions: dict[str, dict[str, Any]] = {}
        self.logger = get_logger(__name__)

    def create_session(self, session_id: str, metadata: dict[str, Any]) -> None:
        """Create a new session entry with the provided metadata."""
        self.sessions[session_id] = {
            "id": session_id,
            "created_at": time.time(),
            "metadata": metadata,
            "status": "active",
            "last_activity": time.time()
        }
        self.logger.info(f"Writing session created: {session_id}")

    def update_session(self, session_id: str, updates: dict[str, Any]) -> None:
        """Update session metadata and refresh the activity timestamp."""
        if session_id in self.sessions:
            self.sessions[session_id].update(updates)
            self.sessions[session_id]["last_activity"] = time.time()

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Return the session metadata or ``None`` when missing."""
        return self.sessions.get(session_id)

    def cleanup_inactive_sessions(self, timeout_seconds: int = 3600) -> int:
        """Remove inactive sessions older than ``timeout_seconds``."""
        current_time = time.time()
        inactive_sessions = []

        for session_id, session in self.sessions.items():
            if current_time - session["last_activity"] > timeout_seconds:
                inactive_sessions.append(session_id)

        for session_id in inactive_sessions:
            del self.sessions[session_id]
            self.logger.info(f"Cleaned up inactive session: {session_id}")

        return len(inactive_sessions)


class PerformanceCacheSystem:
    """Coordinate caching and performance helpers for the MCP server."""

    def __init__(self, project_root: Path) -> None:
        """Initialise caches and monitoring helpers for the given project."""
        self.project_root = project_root
        self.logger = get_logger(__name__)

        # キャッシュシステム
        self._json_conversion_cache: dict[str, dict[str, Any]] = {}
        self._json_cache_access: dict[str, float] = {}
        self._path_resolution_cache: dict[str, Path] = {}

        # パフォーマンス監視
        self._monitoring_initialized = False
        self._async_tasks: set[asyncio.Task] = set()

        # 執筆セッション管理
        self.session_manager = WritingSessionManager()

        # パフォーマンス最適化
        try:
            from noveler.infrastructure.optimization.performance_optimizer import PerformanceOptimizer
            self.performance_optimizer = PerformanceOptimizer()
        except ImportError:
            self.logger.warning("PerformanceOptimizer not available, using fallback")
            self.performance_optimizer = None

    def _optimize_json_conversion(self, data: dict[str, Any], max_size: int = 50000) -> dict[str, Any]:
        """Return an optimised JSON payload using caching and truncation."""
        cache_key = str(hash(str(data)))

        # キャッシュチェック
        if cache_key in self._json_conversion_cache:
            self._json_cache_access[cache_key] = time.time()
            return self._json_conversion_cache[cache_key]

        # 最適化実行
        optimized = self._perform_json_optimization(data, max_size)

        # キャッシュ保存
        self._json_conversion_cache[cache_key] = optimized
        self._json_cache_access[cache_key] = time.time()

        # キャッシュサイズ制限
        if len(self._json_conversion_cache) > 100:
            self._cleanup_json_cache()

        return optimized

    def _perform_json_optimization(self, data: dict[str, Any], max_size: int) -> dict[str, Any]:
        """Fallback implementation for JSON optimisation when no optimiser is available."""
        if self.performance_optimizer:
            return self.performance_optimizer.optimize_json_output(data, max_size)

        # フォールバック実装
        result = data.copy()
        if "output" in result and isinstance(result["output"], str):
            if len(result["output"]) > max_size:
                result["output"] = self._summarize_long_text(result["output"], max_size)

        return result

    def _summarize_long_text(self, text: str, max_length: int) -> str:
        """Return a truncated text representation ensuring the string fits ``max_length``."""
        if len(text) <= max_length:
            return text
        return text[:max_length-20] + "...(truncated)"

    def _cleanup_json_cache(self) -> None:
        """Remove the oldest entries from the JSON cache using an LRU approach."""
        # 古いエントリを削除（最も古い20%）
        sorted_entries = sorted(
            self._json_cache_access.items(),
            key=lambda x: x[1]
        )

        entries_to_remove = len(sorted_entries) // 5
        for cache_key, _ in sorted_entries[:entries_to_remove]:
            if cache_key in self._json_conversion_cache:
                del self._json_conversion_cache[cache_key]
            if cache_key in self._json_cache_access:
                del self._json_cache_access[cache_key]

        self.logger.debug(f"Cleaned up {entries_to_remove} JSON cache entries")

    async def _cleanup_async_tasks(self) -> None:
        """完了した非同期タスクのクリーンアップ"""
        completed_tasks = [task for task in self._async_tasks if task.done()]
        for task in completed_tasks:
            self._async_tasks.remove(task)
            if task.exception():
                self.logger.warning(f"Async task failed: {task.exception()}")

    def _schedule_async_task(self, coro) -> asyncio.Task:
        """非同期タスクスケジューリング"""
        task = asyncio.create_task(coro)
        self._async_tasks.add(task)
        task.add_done_callback(lambda t: self._async_tasks.discard(t))
        return task

    def _init_performance_monitoring(self) -> None:
        """パフォーマンス監視初期化"""
        if self._monitoring_initialized:
            return

        # バックグラウンドタスクスケジューリング
        self._schedule_async_task(self._run_performance_monitoring())
        self._schedule_async_task(self._periodic_cache_cleanup())

        self._monitoring_initialized = True
        self.logger.info("Performance monitoring initialized")

    async def _run_performance_monitoring(self) -> None:
        """パフォーマンス監視実行"""
        while True:
            try:
                await asyncio.sleep(300)  # 5分間隔

                # メモリ使用量監視
                cache_count = len(self._json_conversion_cache)
                task_count = len(self._async_tasks)
                session_count = len(self.session_manager.sessions)

                self.logger.debug(
                    f"Performance stats - Cache: {cache_count}, Tasks: {task_count}, Sessions: {session_count}"
                )

                # 非アクティブセッションクリーンアップ
                cleaned_sessions = self.session_manager.cleanup_inactive_sessions()
                if cleaned_sessions > 0:
                    self.logger.info(f"Cleaned up {cleaned_sessions} inactive sessions")

                # 非同期タスククリーンアップ
                await self._cleanup_async_tasks()

            except Exception as e:
                self.logger.exception(f"Performance monitoring error: {e}")

    async def _periodic_cache_cleanup(self) -> None:
        """定期キャッシュクリーンアップ"""
        while True:
            try:
                await asyncio.sleep(1800)  # 30分間隔
                self._cleanup_cache_systems()
            except Exception as e:
                self.logger.exception(f"Cache cleanup error: {e}")

    def _cleanup_cache_systems(self) -> None:
        """キャッシュシステム全体クリーンアップ"""
        # JSONキャッシュクリーンアップ
        self._cleanup_json_cache()

        # パス解決キャッシュクリーンアップ（サイズ制限）
        if len(self._path_resolution_cache) > 500:
            # 半分を削除
            keys_to_remove = list(self._path_resolution_cache.keys())[:250]
            for key in keys_to_remove:
                del self._path_resolution_cache[key]

        self.logger.info("Cache systems cleaned up")

    def _emergency_cache_cleanup(self) -> None:
        """緊急時キャッシュクリーンアップ"""
        self._json_conversion_cache.clear()
        self._json_cache_access.clear()
        self._path_resolution_cache.clear()

        # セッションクリーンアップ
        self.session_manager.sessions.clear()

        self.logger.warning("Emergency cache cleanup performed")

    def get_cache_statistics(self) -> dict[str, Any]:
        """キャッシュ統計取得"""
        return {
            "json_cache_entries": len(self._json_conversion_cache),
            "path_cache_entries": len(self._path_resolution_cache),
            "active_tasks": len(self._async_tasks),
            "active_sessions": len(self.session_manager.sessions),
            "monitoring_active": self._monitoring_initialized
        }

    def initialize_monitoring(self) -> None:
        """監視システム初期化（外部呼び出し用）"""
        self._init_performance_monitoring()
