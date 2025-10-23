"""Provide the base implementation for JSON conversion MCP servers."""

import asyncio
import os
import signal
from pathlib import Path
from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import FastMCP

from noveler.infrastructure.json.conversion.optimized_json_converter import OptimizedJSONConverter
from noveler.infrastructure.logging.unified_logger import get_logger

if TYPE_CHECKING:
    # Kept for type-checkers; runtime import is above
    import asyncio


class FileIOCache:
    """Lightweight file I/O cache used by the JSON conversion server."""

    def __init__(self, max_size: int = 200) -> None:
        self.cache: dict[Path, tuple[str, float]] = {}
        self.max_size = max_size
        self.logger = get_logger(__name__)

    def get(self, path: Path) -> str | None:
        """Return cached file contents when still valid."""
        if path in self.cache:
            content, timestamp = self.cache[path]
            if path.exists() and path.stat().st_mtime <= timestamp:
                return content
            del self.cache[path]
        return None

    def set(self, path: Path, content: str) -> None:
        """Store file contents in the cache, evicting old entries as needed."""
        if len(self.cache) >= self.max_size:
            oldest_path = min(self.cache.keys(), key=lambda p: self.cache[p][1])
            del self.cache[oldest_path]

        self.cache[path] = (content, path.stat().st_mtime if path.exists() else 0)

    def clear(self) -> None:
        """Clear the cache contents and log the event."""
        self.cache.clear()
        self.logger.info("FileIOCache cleared")


class JSONConversionServerBase:
    """Base class that encapsulates shared MCP server functionality."""

    def __init__(self, project_root: str | None = None) -> None:
        """Initialise the server with optional project root overrides."""
        # 基本設定
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.logger = get_logger(__name__)

        # MCPサーバー初期化
        self.server = FastMCP("JSONConversionServer")

        # 出力ディレクトリ設定
        self.output_dir = self.project_root / "output" / "json"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # JSON変換器初期化
        self.converter = OptimizedJSONConverter()

        # パフォーマンスシステム初期化
        self._init_performance_systems()

        # プロセス管理
        self._handle_existing_processes()
        self._create_pid_file()

        # ツール登録（派生クラスで実装）
        self._register_tools()

        self.logger.info(f"JSONConversionServer initialized with project_root: {self.project_root}")

    def _init_performance_systems(self) -> None:
        """Initialise caches and performance optimisation helpers."""
        # ファイルキャッシュ
        self.file_cache = FileIOCache()

        # パフォーマンス最適化
        from noveler.infrastructure.optimization.performance_optimizer import PerformanceOptimizer
        self.performance_optimizer = PerformanceOptimizer()

        # JSON変換キャッシュ
        self._json_conversion_cache: dict[str, dict[str, Any]] = {}
        self._json_cache_access: dict[str, float] = {}

        # パス解決キャッシュ
        self._path_resolution_cache: dict[str, Path] = {}

        # 非同期タスク管理
        self._async_tasks: set[asyncio.Task] = set()

        # 監視システム
        self._monitoring_initialized = False

    def _register_tools(self) -> None:
        """Register MCP tools in subclasses."""
        msg = "Subclasses must implement _register_tools"
        raise NotImplementedError(msg)

    def _resolve_project_path(self, relative_path: str | None = None) -> Path:
        """Resolve and cache project-relative paths."""
        cache_key = relative_path or "root"
        if cache_key in self._path_resolution_cache:
            return self._path_resolution_cache[cache_key]

        resolved = self.project_root / relative_path if relative_path else self.project_root

        self._path_resolution_cache[cache_key] = resolved
        return resolved

    def _load_file_with_cache(self, file_path: Path) -> str:
        """Load file contents while consulting the cache."""
        cached_content = self.file_cache.get(file_path)
        if cached_content is not None:
            return cached_content

        content = file_path.read_text(encoding="utf-8")
        self.file_cache.set(file_path, content)
        return content

    def _handle_existing_processes(self) -> None:
        """Terminate stale server processes by inspecting PID files."""
        pid_file = self.project_root / ".json_conversion_server.pid"

        if pid_file.exists():
            try:
                old_pid = int(pid_file.read_text().strip())
                if self._is_process_running(old_pid):
                    self.logger.warning(f"Terminating existing process (PID: {old_pid})")
                    self._terminate_process_gracefully(old_pid)
                else:
                    self.logger.info(f"Cleaning up stale PID file (PID: {old_pid})")
                pid_file.unlink()
            except (ValueError, FileNotFoundError):
                self.logger.warning("Invalid PID file found, removing")
                pid_file.unlink(missing_ok=True)

    def _is_process_running(self, pid: int) -> bool:
        """Return ``True`` when the provided PID is currently running."""
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def _terminate_process_gracefully(self, pid: int) -> None:
        """Terminate the process identified by ``pid`` using SIGTERM/SIGKILL."""
        try:
            os.kill(pid, signal.SIGTERM)
            import time
            for _ in range(5):
                time.sleep(0.5)
                if not self._is_process_running(pid):
                    break
            else:
                os.kill(pid, signal.SIGKILL)
        except OSError:
            pass

    def _create_pid_file(self) -> None:
        """Persist the current process ID to the PID file."""
        pid_file = self.project_root / ".json_conversion_server.pid"
        try:
            pid_file.write_text(str(os.getpid()))
            self.logger.debug(f"PID file created: {pid_file}")
        except Exception as e:
            self.logger.warning(f"Failed to create PID file: {e}")

    def _cleanup_pid_file(self) -> None:
        """Remove the PID file if it exists."""
        pid_file = self.project_root / ".json_conversion_server.pid"
        pid_file.unlink(missing_ok=True)

    def __del__(self) -> None:
        """Destructor hook that removes the PID file on shutdown."""
        self._cleanup_pid_file()
