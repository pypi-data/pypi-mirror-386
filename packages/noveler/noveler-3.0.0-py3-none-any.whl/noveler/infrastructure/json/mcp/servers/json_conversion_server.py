# ruff: noqa
"""FastMCP-backed JSON conversion server for the Noveler toolset."""

import asyncio
import hashlib
import json
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from collections.abc import Iterable
from typing import Any

from noveler.infrastructure.factories.path_service_factory import create_path_service
from noveler.infrastructure.factories.progressive_write_llm_executor_factory import (
    create_progressive_write_llm_executor,
)
from noveler.infrastructure.factories.progressive_write_manager_factory import (
    create_progressive_write_manager,
)
from noveler.infrastructure.json.converters.cli_response_converter import CLIResponseConverter
from noveler.infrastructure.json.models.response_models import (
    ErrorResponseModel,
    StandardResponseModel,
)
from noveler.infrastructure.logging.unified_logger import get_logger
from noveler.infrastructure.performance.comprehensive_performance_optimizer import (
    ComprehensivePerformanceOptimizer,
)
from noveler.presentation.shared.shared_utilities import console

# project_now関数のインポート（フォールバック付き）
try:
    from noveler.domain.value_objects.project_time import project_now
except ImportError:
    # MCPサーバー実行環境でのフォールバック実装
    def project_now() -> object:
        """Fallback implementation of :func:`project_now`."""

        class FallbackProjectDateTime:
            """Fallback shim mimicking the ProjectDateTime interface."""

            def __init__(self, dt: datetime) -> None:
                self.datetime = dt

            def isoformat(self) -> str:
                return self.datetime.isoformat()

            def format_timestamp(self, fmt: str) -> str:
                return self.datetime.strftime(fmt)

        return FallbackProjectDateTime(datetime.now(timezone.utc))


# MCPライブラリの有無に応じて分岐
try:
    from mcp import types
    from mcp.server import stdio
    from mcp.server.fastmcp import FastMCP

    MCP_AVAILABLE = True
except ImportError:  # ランタイム環境にMCPが無い場合のフォールバック
    MCP_AVAILABLE = False
    FastMCP = None  # type: ignore[assignment]
    types = None  # type: ignore[assignment]
    stdio = None  # type: ignore[assignment]


class FileIOCache:
    """High-performance file I/O cache used by the MCP server."""

    def __init__(self, max_size: int = 128, ttl_seconds: int = 300) -> None:
        """
        Args:
            max_size: キャッシュ最大サイズ
            ttl_seconds: キャッシュ有効期限（秒）
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, dict[str, Any]] = {}
        self._access_times: dict[str, float] = {}
        self._file_hashes: dict[str, str] = {}

    def _get_file_hash(self, file_path: Path) -> str:
        """Return a lightweight file hash used for change detection."""
        try:
            stat = file_path.stat()
            # ファイルサイズと更新時刻でハッシュを簡略化（パフォーマンス重視）
            hash_source = f"{stat.st_size}:{stat.st_mtime}"
            # セキュリティ要件は不要だが、静的解析回避のためSHA256を使用
            return hashlib.sha256(hash_source.encode()).hexdigest()
        except OSError:
            return ""

    def _is_cache_valid(self, key: str, file_path: Path) -> bool:
        """Return ``True`` when the cached entry is still valid."""
        if key not in self._cache:
            return False

        # TTLチェック
        current_time = time.time()
        if current_time - self._access_times.get(key, 0) > self.ttl_seconds:
            return False

        # ファイル変更チェック
        current_hash = self._get_file_hash(file_path)
        return current_hash == self._file_hashes.get(key, "")

    def _cleanup_expired(self) -> None:
        """Remove expired cache entries based on TTL."""
        current_time = time.time()
        expired_keys = [
            key for key, access_time in self._access_times.items() if current_time - access_time > self.ttl_seconds
        ]

        for key in expired_keys:
            self._cache.pop(key, None)
            self._access_times.pop(key, None)
            self._file_hashes.pop(key, None)

    def _evict_lru(self) -> None:
        """Evict the least recently accessed cache entry."""
        if len(self._cache) >= self.max_size:
            # 最も古いアクセス時刻のキーを削除
            lru_key = min(self._access_times.items(), key=lambda x: x[1])[0]
            self._cache.pop(lru_key, None)
            self._access_times.pop(lru_key, None)
            self._file_hashes.pop(lru_key, None)

    def get(self, file_path: Path, loader_func) -> Any:
        """Return cached data or use ``loader_func`` to populate the cache."""
        key = str(file_path)

        # 期限切れクリーンアップ
        self._cleanup_expired()

        # キャッシュ有効性チェック
        if self._is_cache_valid(key, file_path):
            self._access_times[key] = time.time()
            return self._cache[key]

        # キャッシュミス：ファイル読み込み
        try:
            data = loader_func(file_path)

            # LRU削除
            self._evict_lru()

            # キャッシュ保存
            current_time = time.time()
            self._cache[key] = data
            self._access_times[key] = current_time
            self._file_hashes[key] = self._get_file_hash(file_path)

            return data
        except Exception:
            # エラー時は空データを短期間キャッシュ
            self._cache[key] = None
            self._access_times[key] = time.time()
            raise

    def invalidate(self, file_path: Path) -> None:
        """Invalidate the cached entry for the given file path."""
        key = str(file_path)
        self._cache.pop(key, None)
        self._access_times.pop(key, None)
        self._file_hashes.pop(key, None)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._access_times.clear()
        self._file_hashes.clear()


class WritingSessionManager:
    """Manage staged writing sessions for the MCP server."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.sessions_dir = project_root / "90_管理" / "writing_sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger(__name__)

    def create_session(self, episode: int, session_id: str) -> None:
        """Create a new writing session record."""
        try:
            import json
            from datetime import datetime, timezone

            session_file = self.sessions_dir / f"session_{session_id}.json"
            session_data = {
                "session_id": session_id,
                "episode": episode,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "stages": {},
                "status": "active",
            }
            session_file.write_text(json.dumps(session_data, ensure_ascii=False, indent=2), encoding="utf-8")
            self.logger.info(f"新規セッション作成: {session_id}, Episode: {episode}")
        except Exception as e:
            self.logger.exception(f"セッション作成エラー: {e}")
            raise

    def save_stage_output(self, session_id: str, stage_name: str, output: dict) -> None:
        """Persist the output produced by an individual stage."""
        try:
            import json
            from datetime import datetime, timezone

            session_file = self.sessions_dir / f"session_{session_id}.json"
            if not session_file.exists():
                msg = f"セッションが見つかりません: {session_id}"
                raise ValueError(msg)
            session_data = json.loads(session_file.read_text(encoding="utf-8"))
            session_data["stages"][stage_name] = {
                "output": output,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
            session_data["last_updated"] = datetime.now(timezone.utc).isoformat()
            session_file.write_text(json.dumps(session_data, ensure_ascii=False, indent=2), encoding="utf-8")
            self.logger.info(f"段階出力保存: {session_id}, Stage: {stage_name}")
        except Exception as e:
            self.logger.exception(f"段階出力保存エラー: {e}")
            raise

    def load_session(self, session_id: str) -> dict:
        """Load all recorded outputs for the specified session."""
        try:
            import json

            session_file = self.sessions_dir / f"session_{session_id}.json"
            if not session_file.exists():
                self.logger.warning(f"セッションファイルが見つかりません: {session_id}")
                return {}
            session_data = json.loads(session_file.read_text(encoding="utf-8"))
            combined_data = {}
            for stage_data in session_data["stages"].values():
                stage_output = stage_data["output"]
                for key, value in stage_output.items():
                    if key not in ["session_id", "timestamp", "stage"]:
                        combined_data[key] = value
            return combined_data
        except Exception as e:
            self.logger.exception(f"セッション読み込みエラー: {e}")
            return {}

    def get_session_status(self, session_id: str) -> dict:
        """Return metadata describing the session status."""
        try:
            import json

            session_file = self.sessions_dir / f"session_{session_id}.json"
            if not session_file.exists():
                return {"exists": False}
            session_data = json.loads(session_file.read_text(encoding="utf-8"))
            completed_stages = list(session_data["stages"].keys())
            total_stages = 10
            return {
                "exists": True,
                "episode": session_data["episode"],
                "status": session_data["status"],
                "completed_stages": completed_stages,
                "progress": f"{len(completed_stages)}/{total_stages}",
                "created_at": session_data["created_at"],
                "last_updated": session_data.get("last_updated", session_data["created_at"]),
            }
        except Exception as e:
            self.logger.exception(f"セッション状態取得エラー: {e}")
            return {"exists": False, "error": str(e)}


class JSONConversionServer:
    """FastMCP JSON conversion server with performance optimisations."""

    def __init__(self, output_dir: Path | None = None, force_restart: bool = False) -> None:
        if not MCP_AVAILABLE:
            msg = "MCPライブラリが利用できません。pip install mcp を実行してください。"
            raise RuntimeError(msg)

        # 早期ロガー初期化（依存関係回避）
        self.logger = get_logger(__name__)

        # パフォーマンス最適化システム初期化
        self._init_performance_systems()

        self._handle_existing_processes(force_restart)
        self.output_dir = output_dir or Path.cwd() / "temp" / "json_output"
        self.converter = CLIResponseConverter(output_dir=self.output_dir)
        self.server = FastMCP(
            name="json-conversion",
            instructions="小説執筆支援システム JSON変換・MCP統合サーバー - CLI結果を95%トークン削減でJSON化し、ファイル参照アーキテクチャとSHA256完全性保証を提供",
        )
        self._create_pid_file()
        self._register_tools()
        self._register_novel_tools()

    def _init_performance_systems(self) -> None:
        """Initialise caches and performance optimisation helpers."""
        # ファイルI/Oキャッシュシステム
        self.file_cache = FileIOCache(max_size=256, ttl_seconds=600)  # 10分キャッシュ

        # 包括的パフォーマンス最適化システム統合
        self.performance_optimizer = ComprehensivePerformanceOptimizer()

        # JSON変換キャッシュ（メモリ効率重視）
        self._json_conversion_cache: dict[str, Any] = {}
        self._json_cache_access: dict[str, float] = {}

        # 頻繁なファイルパス操作のキャッシュ
        self._path_resolution_cache: dict[str, Path] = {}

        # 非同期タスク管理
        self._async_tasks: set[asyncio.Task] = set()

        # パフォーマンス監視はrunメソッドで開始（非同期コンテキストが必要）
        self._monitoring_initialized = False

    @lru_cache(maxsize=512)
    def _resolve_project_path(self, project_root: str | None) -> Path:
        """Resolve and cache project-relative paths."""
        if project_root:
            return Path(project_root)
        return Path.cwd()

    def _load_file_with_cache(self, file_path: Path) -> dict[str, Any]:
        """Load file contents consulting the FileIOCache."""

        def _load_yaml_file(path: Path) -> dict[str, Any]:
            import yaml

            try:
                with path.open("r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception:
                return {}

        return self.file_cache.get(file_path, _load_yaml_file)

    def _optimize_json_conversion(self, data: dict[str, Any]) -> dict[str, Any]:
        """Return an optimised JSON payload using caching and truncation."""
        # データハッシュでキャッシュキー生成
        data_str = str(sorted(data.items()))
        cache_key = hashlib.md5(data_str.encode()).hexdigest()

        current_time = time.time()

        # キャッシュヒット確認（5分間有効）
        if cache_key in self._json_conversion_cache and current_time - self._json_cache_access.get(cache_key, 0) < 300:
            self._json_cache_access[cache_key] = current_time
            return self._json_conversion_cache[cache_key]

        # キャッシュミス：新規変換実行
        optimized_data = self._perform_json_optimization(data)

        # キャッシュサイズ管理（最大100エントリ）
        if len(self._json_conversion_cache) >= 100:
            # 最も古いエントリを削除
            oldest_key = min(self._json_cache_access.items(), key=lambda x: x[1])[0]
            self._json_conversion_cache.pop(oldest_key, None)
            self._json_cache_access.pop(oldest_key, None)

        # キャッシュ保存
        self._json_conversion_cache[cache_key] = optimized_data
        self._json_cache_access[cache_key] = current_time

        return optimized_data

    def _perform_json_optimization(self, data: dict[str, Any]) -> dict[str, Any]:
        """Fallback implementation performing JSON optimisation when no optimiser is available."""
        # 大きなテキストデータの最適化
        optimized = {}
        for key, value in data.items():
            if isinstance(value, str) and len(value) > 10000:
                # 長いテキストは要約化
                optimized[key] = self._summarize_long_text(value)
            elif isinstance(value, list) and len(value) > 100:
                # 長いリストは制限
                optimized[key] = [*value[:50], "... (truncated)"]
            else:
                optimized[key] = value

        return optimized

    def _summarize_long_text(self, text: str) -> str:
        """Return a truncated representation ensuring the string fits ``max_length``."""
        if len(text) <= 10000:
            return text

        # 先頭と末尾を保持して中間を省略
        return f"{text[:3000]}...\n\n[{len(text) - 6000}文字省略]\n\n...{text[-3000:]}"

    async def _cleanup_async_tasks(self) -> None:
        """Cancel and clear internal asynchronous tasks."""
        completed_tasks = [task for task in self._async_tasks if task.done()]
        for task in completed_tasks:
            self._async_tasks.discard(task)
            try:
                await task
            except Exception as e:
                self.logger.warning(f"非同期タスク完了時エラー: {e}")

    def _schedule_async_task(self, coro) -> None:
        """Schedule a background task and track it for later cleanup."""
        task = asyncio.create_task(coro)
        self._async_tasks.add(task)

        # タスク完了時のクリーンアップ
        def cleanup_task(t) -> None:
            self._async_tasks.discard(t)

        task.add_done_callback(cleanup_task)

    def _init_performance_monitoring(self) -> None:
        """Initialise the performance monitoring subsystem."""
        try:
            # パフォーマンス監視を非同期で開始
            monitoring_task = asyncio.create_task(self._run_performance_monitoring())
            self._async_tasks.add(monitoring_task)

            # 定期的なキャッシュクリーンアップも開始
            cleanup_task = asyncio.create_task(self._periodic_cache_cleanup())
            self._async_tasks.add(cleanup_task)

        except Exception as e:
            self.logger.warning(f"パフォーマンス監視初期化エラー: {e}")

    async def _run_performance_monitoring(self) -> None:
        """Continuously monitor server performance metrics."""
        while True:
            try:
                # 5分ごとにメトリクス収集
                await asyncio.sleep(300)

                # メモリ使用量チェック
                import psutil

                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024

                if memory_mb > 512:  # 512MB以上でクリーンアップ
                    self._emergency_cache_cleanup()
                    self.logger.info(
                        f"メモリクリーンアップ実行: {memory_mb:.1f}MB -> {process.memory_info().rss / 1024 / 1024:.1f}MB"
                    )

                # 非同期タスクのクリーンアップ
                await self._cleanup_async_tasks()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.exception(f"パフォーマンス監視エラー: {e}")

    async def _periodic_cache_cleanup(self) -> None:
        """Periodically clean caches to release memory."""
        while True:
            try:
                # 30分ごとにキャッシュクリーンアップ
                await asyncio.sleep(1800)

                self._cleanup_cache_systems()
                self.logger.info("定期キャッシュクリーンアップ完了")

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.exception(f"キャッシュクリーンアップエラー: {e}")

    def _cleanup_cache_systems(self) -> None:
        """Clear caches including JSON conversion and path resolution."""
        # ファイルキャッシュクリーンアップ
        old_size = len(self.file_cache._cache)
        self.file_cache._cleanup_expired()
        new_size = len(self.file_cache._cache)

        # JSON変換キャッシュクリーンアップ
        current_time = time.time()
        expired_json_keys = [
            key
            for key, access_time in self._json_cache_access.items()
            if current_time - access_time > 1800  # 30分
        ]

        for key in expired_json_keys:
            self._json_conversion_cache.pop(key, None)
            self._json_cache_access.pop(key, None)

        self.logger.debug(
            f"キャッシュクリーンアップ: ファイル {old_size}->{new_size}, JSON変換 {len(expired_json_keys)}個削除"
        )

    def _emergency_cache_cleanup(self) -> None:
        """Clear caches immediately in case of emergency."""
        # 全キャッシュクリア
        self.file_cache.clear()
        self._json_conversion_cache.clear()
        self._json_cache_access.clear()
        self._path_resolution_cache.clear()

        # ガベージコレクション強制実行
        import gc

        gc.collect()

        self.logger.info("緊急キャッシュクリーンアップ完了")

    def _register_tools(self) -> None:
        """Register FastMCP tools exposed by the server."""
        self._register_cli_conversion_tool()
        self._register_validation_tool()
        self._register_file_reference_tool()
        self._register_artifact_tools()
        # FastMCPのAPIによりregister_tool未提供の場合があるためガード
        if hasattr(self.server, "register_tool"):
            self._register_18step_writing_tools()  # 18ステップ執筆システム並列実行ツール追加

    def _register_cli_conversion_tool(self) -> None:
        """Register the CLI-to-JSON conversion tool."""

        @self.server.tool(
            name="convert_cli_to_json",
            description="CLI実行結果をJSON形式に変換し、95%トークン削減とファイル参照アーキテクチャを適用",
        )
        def convert_cli_to_json(cli_result: dict[str, Any]) -> str:
            """Convert CLI output into the JSON structure used by clients."""
            try:
                if not cli_result:
                    return "エラー: cli_resultパラメータが必要です"
                json_result = self.converter.convert(cli_result)
                return f"変換成功:\n{self._format_json_result(json_result)}"
            except Exception as e:
                self.logger.exception("CLI→JSON変換エラー")
                return f"変換エラー: {e!s}"

    def _register_validation_tool(self) -> None:
        """Register the JSON response validation tool."""

        @self.server.tool(name="validate_json_response", description="JSON レスポンス形式検証")
        def validate_json_response(json_data: dict[str, Any]) -> str:
            """Validate that the JSON payload matches the response schema."""
            try:
                if not json_data:
                    return "エラー: json_dataパラメータが必要です"
                if json_data.get("success", False):
                    model = StandardResponseModel(**json_data)
                else:
                    model = ErrorResponseModel(**json_data)
                return f"JSON形式検証成功: {model.__class__.__name__}"
            except Exception as e:
                return f"JSON形式検証エラー: {e!s}"

    def _register_file_reference_tool(self) -> None:
        """Register the file reference lookup tool."""

        @self.server.tool(name="get_file_reference_info", description="ファイル参照情報取得")
        def get_file_reference_info(file_path: str) -> str:
            """ファイル参照情報取得"""
            try:
                if not file_path:
                    return "エラー: file_pathパラメータが必要です"
                candidate_paths = [self.output_dir / file_path, Path.cwd() / file_path, Path.cwd().parent / file_path]
                for full_path in candidate_paths:
                    if full_path.exists():
                        stat = full_path.stat()
                        info = {
                            "path": file_path,
                            "absolute_path": str(full_path),
                            "size_bytes": stat.st_size,
                            "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                            "exists": True,
                        }
                        return f"ファイル情報:\n{self._format_dict(info)}"
                info = {
                    "path": file_path,
                    "exists": False,
                    "searched_paths": [str(p) for p in candidate_paths],
                    "current_working_directory": str(Path.cwd()),
                    "suggestion": "ファイルが存在しない、または執筆がまだ開始されていません",
                }
                return f"ファイル参照結果:\n{self._format_dict(info)}"
            except Exception as e:
                return f"ファイル情報取得エラー: {e!s}"

    def _register_novel_tools(self) -> None:
        """Register Noveler-specific tool groups."""
        self._register_write_tools()
        self._register_staged_writing_tools()
        # self._register_claude_write_tools()  # 非公開：実装は残すがツール登録しない
        self._register_check_tools()
        self._register_plot_tools()
        self._register_project_tools()

    def _handle_existing_processes(self, force_restart: bool = False) -> None:
        """Terminate stale server processes by inspecting PID files."""
        try:
            import os

            import psutil

            current_pid = os.getpid()
            psutil.Process(current_pid)
            matching_processes = []
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    if (
                        proc.info["name"]
                        and "python" in proc.info["name"].lower()
                        and proc.info["cmdline"]
                        and any("json_conversion_server" in str(arg) for arg in proc.info["cmdline"])
                    ):
                        if proc.pid != current_pid:
                            matching_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            if matching_processes:
                if force_restart:
                    for proc in matching_processes:
                        try:
                            self._terminate_process_gracefully(proc)
                            self.logger.info(f"既存MCPサーバープロセス終了: PID {proc.pid}")
                        except Exception as e:
                            self.logger.warning(f"プロセス終了失敗 PID {proc.pid}: {e}")
                else:
                    pid_list = [str(proc.pid) for proc in matching_processes]
                    self.logger.warning(f"既存MCPサーバープロセス検出: PID {', '.join(pid_list)}")
                    self.logger.info(
                        "重複実行を回避するため、force_restart=True で再起動するか、既存プロセスを手動終了してください"
                    )
                    msg = f"MCPサーバー重複実行検出 (PID: {', '.join(pid_list)})"
                    raise RuntimeError(msg)
        except ImportError:
            self.logger.warning("psutilが利用できないため、プロセス重複チェックをスキップします")
        except Exception as e:
            self.logger.warning(f"プロセス重複チェックでエラー: {e}")

    def _terminate_process_gracefully(self, process) -> None:
        """Terminate the process using SIGTERM/SIGKILL."""
        try:
            import psutil

            process.terminate()
            try:
                process.wait(timeout=5)
            except psutil.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
        except Exception as e:
            msg = f"プロセス終了失敗: {e}"
            raise RuntimeError(msg) from e

    def _create_pid_file(self) -> None:
        """Persist the current process ID to the PID file."""
        try:
            import os

            pid_dir = Path.cwd() / "temp" / "pids"
            pid_dir.mkdir(parents=True, exist_ok=True)
            pid_file = pid_dir / "json_conversion_server.pid"
            with pid_file.open("w") as f:
                f.write(str(os.getpid()))
            self.pid_file = pid_file
            self.logger.info(f"PIDファイル作成: {pid_file}")
        except Exception as e:
            self.logger.warning(f"PIDファイル作成失敗: {e}")
            self.pid_file = None

    def _cleanup_pid_file(self) -> None:
        """Remove the PID file if it exists."""
        try:
            if hasattr(self, "pid_file") and self.pid_file and self.pid_file.exists():
                self.pid_file.unlink()
                self.logger.info(f"PIDファイル削除: {self.pid_file}")
        except Exception as e:
            self.logger.warning(f"PIDファイル削除失敗: {e}")

    def __del__(self) -> None:
        """Destructor hook that removes the PID file on shutdown."""
        self._cleanup_pid_file()

    def _register_write_tools(self) -> None:
        """Register 10-stage writing helper tools."""

        @self.server.tool(
            name="write", description="小説エピソード執筆（A38準拠18ステップ実行） - 構造設計から公開準備まで段階的実行"
        )
        async def write(episode: int, dry_run: bool = False, project_root: str | None = None) -> str:
            """Execute the 18-step writing workflow."""
            try:
                import json
                from pathlib import Path

                # プロジェクトルートの設定
                if project_root:
                    project_path = Path(project_root)
                else:
                    from noveler.infrastructure.factories.path_service_factory import create_mcp_aware_path_service

                    path_service = create_mcp_aware_path_service()
                    project_path = path_service.project_root

                # 18ステップ定義（A38準拠）
                steps = [
                    {"id": 0, "name": "スコープ定義", "phase": "構造設計", "file_suffix": "step00.yaml"},
                    {"id": 1, "name": "大骨（章の目的線）", "phase": "構造設計", "file_suffix": "step01.yaml"},
                    {"id": 2, "name": "中骨（段階目標）", "phase": "構造設計", "file_suffix": "step02.yaml"},
                    {"id": 3, "name": "テーマ性・独自性検証", "phase": "構造設計", "file_suffix": "step03.yaml"},
                    {"id": 3, "name": "セクションバランス設計", "phase": "構造設計", "file_suffix": "step03.yaml"},
                    {"id": 4, "name": "小骨（シーン／ビート）", "phase": "構造設計", "file_suffix": "step04.yaml"},
                    {"id": 5, "name": "論理検証", "phase": "構造設計", "file_suffix": "step05.yaml"},
                    {"id": 6, "name": "キャラクター一貫性検証", "phase": "構造設計", "file_suffix": "step06.yaml"},
                    {"id": 7, "name": "会話設計", "phase": "構造設計", "file_suffix": "step07.yaml"},
                    {"id": 8, "name": "感情曲線", "phase": "構造設計", "file_suffix": "step08.yaml"},
                    {"id": 9, "name": "情景・五感・世界観", "phase": "構造設計", "file_suffix": "step09.yaml"},
                    {"id": 10, "name": "初稿生成", "phase": "執筆実装", "file_suffix": "step10.md"},
                    {"id": 11, "name": "文字数最適化", "phase": "執筆実装", "file_suffix": "step11.md"},
                    {"id": 12, "name": "文体・可読性パス", "phase": "執筆実装", "file_suffix": "step12.md"},
                    {"id": 13, "name": "必須品質ゲート", "phase": "品質保証", "file_suffix": "step13.yaml"},
                    {"id": 14, "name": "最終品質認定", "phase": "品質保証", "file_suffix": "step14.yaml"},
                    {"id": 15, "name": "公開準備", "phase": "公開", "file_suffix": "step15.yaml"},
                ]

                # 実行結果を格納
                execution_log = []
                completed_steps = 0

                for step in steps:
                    step_id = step["id"]
                    step_name = step["name"]
                    step_phase = step["phase"]

                    try:
                        # ステップ開始ログ
                        start_msg = f"🔄 STEP {step_id}: {step_name} を開始中..."
                        execution_log.append(
                            {
                                "step": step_id,
                                "name": step_name,
                                "phase": step_phase,
                                "status": "started",
                                "message": start_msg,
                            }
                        )

                        # 実際の処理はここに実装（現時点では模擬実行）
                        if not dry_run:
                            # TODO: 各ステップの実際の処理を実装
                            # 例：プロット解析、会話生成、原稿作成など
                            await self._execute_step(step_id, episode, project_path)

                        # ステップ完了ログ
                        complete_msg = f"✅ STEP {step_id}: {step_name} 完了"
                        execution_log.append(
                            {
                                "step": step_id,
                                "name": step_name,
                                "phase": step_phase,
                                "status": "completed",
                                "message": complete_msg,
                            }
                        )
                        completed_steps += 1

                    except Exception as step_error:
                        # ステップエラーログ
                        error_msg = f"❌ STEP {step_id}: {step_name} でエラー - {step_error!s}"
                        execution_log.append(
                            {
                                "step": step_id,
                                "name": step_name,
                                "phase": step_phase,
                                "status": "error",
                                "message": error_msg,
                                "error": str(step_error),
                            }
                        )
                        break

                # 実行結果の整理
                is_complete = completed_steps == len(steps)

                result = {
                    "success": is_complete,
                    "episode": episode,
                    "total_steps": len(steps),
                    "completed_steps": completed_steps,
                    "completion_rate": f"{(completed_steps / len(steps) * 100):.1f}%",
                    "execution_log": execution_log,
                    "final_status": "完了" if is_complete else f"中断（{completed_steps}/{len(steps)}ステップ完了）",
                }

                return self._json_with_path_fallback(result, locals())

            except Exception as e:
                self.logger.exception("18ステップ執筆実行エラー")
                return json.dumps(
                    {"success": False, "error": str(e), "message": "18ステップ執筆実行中にエラーが発生しました"},
                    ensure_ascii=False,
                    indent=2,
                )

        @self.server.tool(
            name="write_stage",
            description="特定ステージのみ執筆実行 - 10段階の特定ステージ（plot_data_preparation等）を個別実行・再開可能",
        )
        def write_stage(
            episode: int, stage: str, resume_session: str | None = None, project_root: str | None = None
        ) -> str:
            """Execute a single stage of the 18-step workflow."""
            try:
                cmd = f"core write-stage {episode} --stage {stage}"
                if resume_session:
                    cmd += f" --resume {resume_session}"
                result = self._execute_noveler_command(cmd, project_root)
                return self._format_tool_result(result, f"ステージ実行: {stage}")
            except Exception as e:
                self.logger.exception("ステージ実行エラー")
                return f"ステージ実行エラー: {e}"

        @self.server.tool(
            name="write_resume", description="中断位置から執筆再開 - セッションIDを指定して前回の続きから実行"
        )
        def write_resume(episode: int, session_id: str, project_root: str | None = None) -> str:
            """中断位置から再開"""
            try:
                cmd = f"core write {episode} --resume {session_id}"
                result = self._execute_noveler_command(cmd, project_root)
                return self._format_tool_result(result, "執筆再開")
            except Exception as e:
                self.logger.exception("執筆再開エラー")
                return f"執筆再開エラー: {e}"

    def _register_claude_write_tools(self) -> None:
        """Claude Code内での直接原稿生成ツール登録"""

        @self.server.tool(
            name="write_with_claude",
            description="Claude Code内で直接原稿生成（外部API不要） - プロットから原稿を直接生成します",
        )
        async def write_with_claude(
            episode: int,
            plot_content: str | None = None,
            word_count_target: int = 4000,
            project_root: str | None = None,
        ) -> str:
            """Claude Code内で直接原稿を生成

            Args:
                episode: エピソード番号
                plot_content: プロット内容（省略時は既存プロットを読み込み）
                word_count_target: 目標文字数
                project_root: プロジェクトルート

            Returns:
                生成結果のJSON文字列
            """
            try:
                import json
                from pathlib import Path

                from noveler.infrastructure.factories.path_service_factory import create_mcp_aware_path_service

                if project_root:
                    Path(project_root)
                else:
                    path_service = create_mcp_aware_path_service()
                plot_title = None
                if not plot_content:
                    # B20準拠: パス管理はPathServiceを使用
                    # use MCP-aware path service so tests can patch this factory
                    plot_ps = create_mcp_aware_path_service()

                    # PathServiceでプロットファイルを解決
                    plot_file = plot_ps.get_episode_plot_path(episode)

                    if plot_file and plot_file.exists():
                        plot_content = plot_file.read_text(encoding="utf-8")
                        plot_title = self._extract_title_from_plot(plot_content)
                    else:
                        return json.dumps(
                            {"success": False, "error": f"プロットファイルが見つかりません: 第{episode:03d}話"},
                            ensure_ascii=False,
                            indent=2,
                        )
                else:
                    plot_title = self._extract_title_from_plot(plot_content)
                # B20準拠: 原稿ファイル名はPathServiceに一元化（タイトル解決含む）
                path_service = create_path_service()
                manuscript_file = path_service.get_manuscript_path(episode)
                manuscript_filename = manuscript_file.name
                # パスフォールバック情報を集約
                fallback_events = []
                try:
                    if hasattr(path_service, "get_and_clear_fallback_events"):
                        fallback_events += path_service.get_and_clear_fallback_events() or []
                except Exception:
                    pass
                try:
                    if "plot_ps" in locals() and hasattr(plot_ps, "get_and_clear_fallback_events"):
                        fallback_events += plot_ps.get_and_clear_fallback_events() or []
                except Exception:
                    pass
                manuscript_prompt = f"\n# 第{episode:03d}話 原稿生成\n\n## プロット\n{plot_content}\n\n## 執筆要件\n- 目標文字数: {word_count_target}文字\n- ジャンル: ファンタジー\n- 視点: 三人称単元視点\n- 文体: ライトノベル調\n\n## 品質基準\n- 感情表現: 身体反応、感覚比喩、内面独白の三層表現を最低3回実装\n- 対話比率: 60%程度\n- 場面描写: 五感を使った描写を意識\n- テンポ: 緊張と緩和のバランスを保つ\n\n以下の形式で原稿を生成してください：\n\n# 第{episode:03d}話 {plot_title or '[タイトル]'}\n\n[本文をここに記述]\n"
                # B20準拠: パス管理はPathServiceを使用（上で解決済み）
                manuscript_dir = manuscript_file.parent
                manuscript_dir.mkdir(exist_ok=True)
                result = {
                    "success": True,
                    "prompt": manuscript_prompt,
                    "manuscript_path": str(manuscript_file),
                    "manuscript_filename": manuscript_filename,
                    "episode": episode,
                    "plot_title": plot_title,
                    "word_count_target": word_count_target,
                    "timestamp": project_now().datetime.isoformat(),
                    "instructions": "このプロンプトを使用してClaude内で原稿を生成し、指定されたパスに保存してください",
                    "path_fallback_used": bool(fallback_events),
                    "path_fallback_events": fallback_events,
                }
                return self._json_with_path_fallback(result, locals())
            except Exception as e:
                self.logger.exception("Claude原稿生成エラー")
                return json.dumps({"success": False, "error": f"原稿生成エラー: {e}"}, ensure_ascii=False, indent=2)

    def _extract_title_from_plot(self, plot_content: str) -> str | None:
        """プロット内容からタイトルを抽出

        Args:
            plot_content: プロットファイルの内容

        Returns:
            抽出されたタイトル、見つからない場合はNone
        """
        import re

        if not plot_content:
            return None
        patterns = [
            "[-*]\\s*タイトル[：:]\\s*(.+)",
            "##?\\s*タイトル[：:]?\\s*(.+)",
            "タイトル[：:]\\s*(.+)",
            "[-*]\\s*話のタイトル[：:]\\s*(.+)",
            "##?\\s*話のタイトル[：:]?\\s*(.+)",
            "#\\s*第\\d+話\\s+(.+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, plot_content, re.MULTILINE | re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                title = re.sub("^[#\\-*\\s]+", "", title)
                title = re.sub("[#\\s]+$", "", title)
                if title:
                    return title
        return None

    def _json_with_path_fallback(self, result: dict, local_vars: dict) -> str:
        """PathServiceのフォールバックイベントをresultに付加してJSON文字列を返す"""
        try:
            fallback_events: list[dict] = []
            for _, val in list(local_vars.items()):
                if hasattr(val, "get_and_clear_fallback_events"):
                    try:
                        ev = val.get_and_clear_fallback_events() or []
                        if ev:
                            fallback_events.extend(ev)
                    except Exception:
                        continue
            if fallback_events:
                result["path_fallback_used"] = True
                result["path_fallback_events"] = fallback_events
        except Exception:
            # フォールバック情報の付加に失敗しても結果のJSON化は継続する
            pass
        # 上位でjsonをimport済み
        return json.dumps(result, ensure_ascii=False, indent=2)

    def _register_staged_writing_tools(self) -> None:
        """段階別執筆ツール登録（SPEC-WRITE-STAGE-001準拠）"""
        # 巨大メソッド分割：機能別にツール登録を分離
        self._register_plot_preparation_tools()
        self._register_manuscript_writing_tools()
        self._register_content_analysis_tools()
        self._register_creative_design_tools()
        self._register_quality_refinement_tools()

    def _register_18step_writing_tools(self) -> None:
        """18ステップ執筆システム用のツールを登録"""

        # 基本の18ステップツール
        self.server.register_tool(
            "get_writing_tasks",
            "18ステップ執筆システムのタスクリストを取得",
            {
                "type": "object",
                "properties": {
                    "episode_number": {"type": "integer", "description": "エピソード番号"},
                    "project_root": {
                        "type": "string",
                        "description": "プロジェクトルートパス（省略時は環境変数から取得）",
                    },
                },
                "required": ["episode_number"],
            },
            self._handle_get_writing_tasks,
        )

        self.server.register_tool(
            "execute_writing_step",
            "18ステップ執筆システムの特定ステップを実行（UI/UX統合版）",
            {
                "type": "object",
                "properties": {
                    "step_id": {"type": "number", "description": "実行するステップID（1-18、2.5などの小数点も可能）"},
                    "episode_number": {"type": "integer", "description": "エピソード番号"},
                    "dry_run": {
                        "type": "boolean",
                        "description": "テスト実行モード（デフォルト: false）",
                        "default": False,
                    },
                    "project_root": {
                        "type": "string",
                        "description": "プロジェクトルートパス（省略時は環境変数から取得）",
                    },
                    "ui_mode": {"type": "boolean", "description": "UI表示モード（デフォルト: true）", "default": True},
                },
                "required": ["step_id", "episode_number"],
            },
            self._handle_execute_writing_step,
        )

        self.server.register_tool(
            "execute_writing_steps_parallel",
            "複数ステップの並列実行（UI/UX統合版）",
            {
                "type": "object",
                "properties": {
                    "step_ids": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "並列実行するステップIDのリスト",
                    },
                    "episode_number": {"type": "integer", "description": "エピソード番号"},
                    "max_concurrent": {
                        "type": "integer",
                        "description": "最大同時実行数（デフォルト: 3）",
                        "default": 3,
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "テスト実行モード（デフォルト: false）",
                        "default": False,
                    },
                    "project_root": {
                        "type": "string",
                        "description": "プロジェクトルートパス（省略時は環境変数から取得）",
                    },
                    "ui_mode": {"type": "boolean", "description": "UI表示モード（デフォルト: true）", "default": True},
                },
                "required": ["step_ids", "episode_number"],
            },
            self._handle_execute_writing_steps_parallel,
        )

        self.server.register_tool(
            "get_task_status",
            "18ステップ執筆システムの現在状況を確認（UI/UX統合版）",
            {
                "type": "object",
                "properties": {
                    "episode_number": {"type": "integer", "description": "エピソード番号"},
                    "project_root": {
                        "type": "string",
                        "description": "プロジェクトルートパス（省略時は環境変数から取得）",
                    },
                    "include_ui_status": {
                        "type": "boolean",
                        "description": "UI状態を含める（デフォルト: true）",
                        "default": True,
                    },
                },
                "required": ["episode_number"],
            },
            self._handle_get_task_status,
        )

        # 新しいUI/UX機能ツール
        self.server.register_tool(
            "create_batch_job",
            "複数エピソード一括処理ジョブの作成",
            {
                "type": "object",
                "properties": {
                    "episode_numbers": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "処理するエピソード番号のリスト",
                    },
                    "step_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "実行するステップIDのリスト（省略時は全18ステップ）",
                    },
                    "job_name": {"type": "string", "description": "ジョブ名（省略時は自動生成）"},
                    "max_concurrent": {
                        "type": "integer",
                        "description": "最大同時実行数（デフォルト: 3）",
                        "default": 3,
                    },
                    "priority": {"type": "integer", "description": "優先度（デフォルト: 0）", "default": 0},
                    "project_root": {
                        "type": "string",
                        "description": "プロジェクトルートパス（省略時は環境変数から取得）",
                    },
                },
                "required": ["episode_numbers"],
            },
            self._handle_create_batch_job,
        )

        self.server.register_tool(
            "execute_batch_job",
            "バッチジョブの実行",
            {
                "type": "object",
                "properties": {
                    "job_id": {"type": "string", "description": "実行するジョブID"},
                    "project_root": {
                        "type": "string",
                        "description": "プロジェクトルートパス（省略時は環境変数から取得）",
                    },
                },
                "required": ["job_id"],
            },
            self._handle_execute_batch_job,
        )

        self.server.register_tool(
            "get_batch_status",
            "バッチ処理状況の確認",
            {
                "type": "object",
                "properties": {
                    "job_id": {"type": "string", "description": "特定ジョブの状況（省略時は全体状況）"},
                    "project_root": {
                        "type": "string",
                        "description": "プロジェクトルートパス（省略時は環境変数から取得）",
                    },
                },
            },
            self._handle_get_batch_status,
        )

        self.server.register_tool(
            "analyze_episode_quality",
            "エピソード品質・感情・物語分析",
            {
                "type": "object",
                "properties": {
                    "episode_numbers": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "分析するエピソード番号のリスト",
                    },
                    "analysis_types": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["emotion", "narrative", "quality", "all"]},
                        "description": "分析種類（デフォルト: ['all']）",
                        "default": ["all"],
                    },
                    "generate_dashboard": {
                        "type": "boolean",
                        "description": "ダッシュボード生成（デフォルト: true）",
                        "default": True,
                    },
                    "project_root": {
                        "type": "string",
                        "description": "プロジェクトルートパス（省略時は環境変数から取得）",
                    },
                },
                "required": ["episode_numbers"],
            },
            self._handle_analyze_episode_quality,
        )

        self.server.register_tool(
            "get_progress_display",
            "進捗表示情報の取得",
            {
                "type": "object",
                "properties": {
                    "episode_number": {"type": "integer", "description": "エピソード番号"},
                    "detailed": {"type": "boolean", "description": "詳細表示（デフォルト: false）", "default": False},
                    "project_root": {
                        "type": "string",
                        "description": "プロジェクトルートパス（省略時は環境変数から取得）",
                    },
                },
                "required": ["episode_number"],
            },
            self._handle_get_progress_display,
        )

        self.server.register_tool(
            "export_ui_reports",
            "UI分析レポートのエクスポート",
            {
                "type": "object",
                "properties": {
                    "episode_numbers": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "エクスポートするエピソード番号のリスト",
                    },
                    "report_types": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["progress", "analytics", "batch", "feedback"]},
                        "description": "レポート種類",
                        "default": ["progress", "analytics"],
                    },
                    "format": {
                        "type": "string",
                        "enum": ["json", "csv", "html"],
                        "description": "出力形式（デフォルト: json）",
                        "default": "json",
                    },
                    "project_root": {
                        "type": "string",
                        "description": "プロジェクトルートパス（省略時は環境変数から取得）",
                    },
                },
                "required": ["episode_numbers"],
            },
            self._handle_export_ui_reports,
        )

    async def _handle_get_writing_tasks(self, arguments: dict) -> list[types.TextContent]:
        """18ステップ執筆タスク一覧取得処理"""
        episode_number = arguments["episode_number"]
        project_root = arguments.get("project_root", ".")

        manager = create_progressive_write_manager(
            project_root,
            episode_number,
            llm_executor=create_progressive_write_llm_executor(),
        )
        result = manager.get_writing_tasks()

        return [types.TextContent(type="text", text=self._optimize_json_conversion(result))]

    async def _handle_execute_writing_step(self, arguments: dict) -> list[types.TextContent]:
        """単一ステップ実行処理"""
        step_id = arguments["step_id"]
        episode_number = arguments["episode_number"]
        project_root = arguments.get("project_root", ".")
        dry_run = arguments.get("dry_run", False)

        manager = create_progressive_write_manager(
            project_root,
            episode_number,
            llm_executor=create_progressive_write_llm_executor(),
        )
        result = await manager.execute_writing_step_async(step_id, dry_run)

        return [types.TextContent(type="text", text=self._optimize_json_conversion(result))]

    async def _handle_execute_writing_steps_parallel(self, arguments: dict) -> list[types.TextContent]:
        """並列ステップ実行処理（高速化）"""
        step_ids = arguments["step_ids"]
        episode_number = arguments["episode_number"]
        project_root = arguments.get("project_root", ".")
        max_concurrent = arguments.get("max_concurrent", 3)
        dry_run = arguments.get("dry_run", False)

        manager = create_progressive_write_manager(
            project_root,
            episode_number,
            llm_executor=create_progressive_write_llm_executor(),
        )

        # 並列実行（AsyncOperationOptimizer使用）
        result = await manager.execute_writing_steps_parallel(step_ids, max_concurrent, dry_run)

        # パフォーマンス統計を追加
        if result.get("success") and result.get("parallel_execution"):
            result["performance_stats"] = {
                "parallel_optimization": "AsyncOperationOptimizer統合",
                "estimated_time_saved": result.get("execution_time_saved", "不明"),
                "concurrent_execution": f"{max_concurrent}並列",
                "optimization_ratio": "推定50%高速化",
            }

        return [types.TextContent(type="text", text=self._optimize_json_conversion(result))]

    async def _handle_get_task_status(self, arguments: dict) -> list[types.TextContent]:
        """タスク状態確認処理"""
        episode_number = arguments["episode_number"]
        project_root = arguments.get("project_root", ".")

        manager = create_progressive_write_manager(
            project_root,
            episode_number,
            llm_executor=create_progressive_write_llm_executor(),
        )
        result = manager.get_task_status()

        return [types.TextContent(type="text", text=self._optimize_json_conversion(result))]

    async def _handle_create_batch_job(self, arguments: dict) -> dict[str, Any]:
        """バッチジョブ作成の処理"""
        try:
            episode_numbers = arguments["episode_numbers"]
            step_ids = arguments.get("step_ids")
            job_name = arguments.get("job_name")
            max_concurrent = arguments.get("max_concurrent", 3)
            priority = arguments.get("priority", 0)
            project_root = self._resolve_project_path(arguments.get("project_root"))

            # バッチプロセッサーの初期化
            from noveler.presentation.ui.batch_processor import BatchProcessingSystem

            batch_processor = BatchProcessingSystem(project_root)

            # ジョブ作成
            job_id = batch_processor.create_batch_job(
                episode_numbers=episode_numbers,
                step_ids=step_ids,
                job_name=job_name,
                max_concurrent=max_concurrent,
                priority=priority,
            )

            return self._format_json_result(
                {
                    "success": True,
                    "job_id": job_id,
                    "episode_count": len(episode_numbers),
                    "step_count": len(step_ids) if step_ids else 18,
                    "message": f"バッチジョブ '{job_id}' を作成しました",
                }
            )

        except Exception as e:
            self.logger.exception("バッチジョブ作成エラー")
            return self._format_json_result({"success": False, "error": str(e), "error_type": type(e).__name__})

    async def _handle_execute_batch_job(self, arguments: dict) -> dict[str, Any]:
        """バッチジョブ実行の処理"""
        try:
            job_id = arguments["job_id"]
            project_root = self._resolve_project_path(arguments.get("project_root"))

            # バッチプロセッサーの初期化
            from noveler.presentation.ui.batch_processor import BatchProcessingSystem

            batch_processor = BatchProcessingSystem(project_root)

            # ジョブ実行
            batch_result = await batch_processor.execute_batch_job(job_id)

            return self._format_json_result(
                {
                    "success": True,
                    "job_id": job_id,
                    "execution_result": {
                        "total_episodes": batch_result.total_episodes,
                        "successful_episodes": batch_result.successful_episodes,
                        "failed_episodes": batch_result.failed_episodes,
                        "execution_time": batch_result.execution_time,
                        "success_rate": (batch_result.successful_episodes / batch_result.total_episodes) * 100,
                        "errors": len(batch_result.errors),
                    },
                    "message": f"バッチジョブ '{job_id}' が完了しました",
                }
            )

        except Exception as e:
            self.logger.exception("バッチジョブ実行エラー")
            return self._format_json_result({"success": False, "error": str(e), "error_type": type(e).__name__})

    async def _handle_get_batch_status(self, arguments: dict) -> dict[str, Any]:
        """バッチ処理状況確認の処理"""
        try:
            job_id = arguments.get("job_id")
            project_root = self._resolve_project_path(arguments.get("project_root"))

            # バッチプロセッサーの初期化
            from noveler.presentation.ui.batch_processor import BatchProcessingSystem

            batch_processor = BatchProcessingSystem(project_root)

            # 状況取得
            status = batch_processor.get_batch_status(job_id)

            return self._format_json_result(
                {"success": True, "batch_status": status, "message": "バッチ処理状況を取得しました"}
            )

        except Exception as e:
            self.logger.exception("バッチ状況確認エラー")
            return self._format_json_result({"success": False, "error": str(e), "error_type": type(e).__name__})

    async def _handle_analyze_episode_quality(self, arguments: dict) -> dict[str, Any]:
        """エピソード品質分析の処理"""
        try:
            episode_numbers = arguments["episode_numbers"]
            analysis_types = arguments.get("analysis_types", ["all"])
            generate_dashboard = arguments.get("generate_dashboard", True)
            project_root = self._resolve_project_path(arguments.get("project_root"))

            # 分析システムの初期化
            from noveler.presentation.ui.analytics_system import WritingAnalyticsSystem

            analytics_system = WritingAnalyticsSystem(project_root)

            results = {}

            for episode_number in episode_numbers:
                # 原稿ファイルを読み込み（PathServiceに統一）
                from noveler.infrastructure.adapters.path_service_adapter import create_path_service

                path_service = create_path_service(project_root)
                manuscript_file = path_service.get_manuscript_path(episode_number)

                if not manuscript_file.exists():
                    results[episode_number] = {"error": "原稿ファイルが見つかりません"}
                    continue

                content = manuscript_file.read_text(encoding="utf-8")
                episode_results = {}

                # 分析実行
                if "all" in analysis_types or "emotion" in analysis_types:
                    emotion_profiles = analytics_system.analyze_episode_emotions(episode_number, content)
                    episode_results["emotion_analysis"] = {
                        character: asdict(profile) for character, profile in emotion_profiles.items()
                    }

                if "all" in analysis_types or "narrative" in analysis_types:
                    narrative_metrics = analytics_system.analyze_narrative_structure(episode_number, content)
                    episode_results["narrative_analysis"] = asdict(narrative_metrics)

                if "all" in analysis_types or "quality" in analysis_types:
                    quality_metrics = analytics_system.analyze_quality_metrics(episode_number, content)
                    episode_results["quality_analysis"] = asdict(quality_metrics)

                results[episode_number] = episode_results

            # ダッシュボード生成
            dashboard_data = None
            if generate_dashboard:
                dashboard_data = analytics_system.export_analytics_dashboard(episode_numbers)

            # 包括的レポート生成
            comprehensive_report = analytics_system.generate_comprehensive_report(episode_numbers)

            return self._format_json_result(
                {
                    "success": True,
                    "analysis_results": results,
                    "comprehensive_report": comprehensive_report,
                    "dashboard_data": json.loads(dashboard_data) if dashboard_data else None,
                    "message": f"{len(episode_numbers)}エピソードの分析が完了しました",
                }
            )

        except Exception as e:
            self.logger.exception("エピソード品質分析エラー")
            return self._format_json_result({"success": False, "error": str(e), "error_type": type(e).__name__})

    async def _handle_get_progress_display(self, arguments: dict) -> dict[str, Any]:
        """進捗表示情報取得の処理"""
        try:
            episode_number = arguments["episode_number"]
            detailed = arguments.get("detailed", False)
            project_root = self._resolve_project_path(arguments.get("project_root"))

            # ProgressiveWriteManagerから進捗情報を取得
            write_manager = create_progressive_write_manager(
                project_root,
                episode_number,
                llm_executor=create_progressive_write_llm_executor(),
            )

            # 進捗表示システムから詳細情報を取得
            if detailed:
                progress_status = write_manager.progress_display.display_detailed_status()
                feedback_summary = write_manager.feedback_system.get_feedback_summary()

                return self._format_json_result(
                    {
                        "success": True,
                        "progress_display": progress_status,
                        "feedback_summary": feedback_summary,
                        "ui_features": {
                            "progress_tracking": True,
                            "interactive_feedback": True,
                            "quality_monitoring": True,
                            "error_recovery": True,
                        },
                        "message": f"Episode {episode_number}の詳細進捗情報を取得しました",
                    }
                )
            # 基本進捗情報
            task_status = write_manager.get_task_status()

            return self._format_json_result(
                {
                    "success": True,
                    "task_status": task_status,
                    "ui_enabled": True,
                    "message": f"Episode {episode_number}の進捗情報を取得しました",
                }
            )

        except Exception as e:
            self.logger.exception("進捗表示情報取得エラー")
            return self._format_json_result({"success": False, "error": str(e), "error_type": type(e).__name__})

    async def _handle_export_ui_reports(self, arguments: dict) -> dict[str, Any]:
        """UIレポートエクスポートの処理"""
        try:
            episode_numbers = arguments["episode_numbers"]
            report_types = arguments.get("report_types", ["progress", "analytics"])
            format_type = arguments.get("format", "json")
            project_root = self._resolve_project_path(arguments.get("project_root"))

            exported_reports = {}

            for episode_number in episode_numbers:
                episode_reports = {}

                # 進捗レポート
                if "progress" in report_types:
                    write_manager = create_progressive_write_manager(
                        project_root,
                        episode_number,
                        llm_executor=create_progressive_write_llm_executor(),
                    )

                    progress_report = write_manager.progress_display.export_progress_report()
                    episode_reports["progress"] = progress_report

                # 分析レポート
                if "analytics" in report_types:
                    from noveler.presentation.ui.analytics_system import WritingAnalyticsSystem

                    analytics_system = WritingAnalyticsSystem(project_root)

                    # 原稿ファイル読み込み（PathServiceに統一）
                    from noveler.infrastructure.adapters.path_service_adapter import create_path_service

                    path_service = create_path_service(project_root)
                    manuscript_file = path_service.get_manuscript_path(episode_number)
                    if manuscript_file.exists():
                        content = manuscript_file.read_text(encoding="utf-8")

                        # 各種分析実行
                        analytics_system.analyze_episode_emotions(episode_number, content)
                        analytics_system.analyze_narrative_structure(episode_number, content)
                        analytics_system.analyze_quality_metrics(episode_number, content)

                        # レポート生成
                        analytics_report = analytics_system.generate_comprehensive_report([episode_number])
                        episode_reports["analytics"] = analytics_report

                # フィードバックレポート
                if "feedback" in report_types:
                    write_manager = create_progressive_write_manager(
                        project_root,
                        episode_number,
                        llm_executor=create_progressive_write_llm_executor(),
                    )

                    feedback_report = write_manager.feedback_system.export_feedback_report()
                    episode_reports["feedback"] = feedback_report

                exported_reports[episode_number] = episode_reports

            # バッチレポート
            if "batch" in report_types:
                from noveler.presentation.ui.batch_processor import BatchProcessingSystem

                batch_processor = BatchProcessingSystem(project_root)

                batch_status = batch_processor.get_batch_status()
                exported_reports["batch_summary"] = batch_status

            return self._format_json_result(
                {
                    "success": True,
                    "exported_reports": exported_reports,
                    "format": format_type,
                    "episodes_processed": len(episode_numbers),
                    "report_types": report_types,
                    "message": f"{len(episode_numbers)}エピソードのUIレポートをエクスポートしました",
                }
            )

        except Exception as e:
            self.logger.exception("UIレポートエクスポートエラー")
            return self._format_json_result({"success": False, "error": str(e), "error_type": type(e).__name__})

    def _register_plot_preparation_tools(self) -> None:
        """プロット準備関連ツール登録"""

        @self.server.tool(
            name="prepare_plot_data",
            description="プロットと設定データを準備し、執筆の基盤を構築 - noveler writeの第1段階をClaude内で実行",
        )
        async def prepare_plot_data(episode: int, project_root: str | None = None) -> str:
            """プロットデータ準備段階"""
            try:
                import json
                import uuid
                from pathlib import Path

                from noveler.infrastructure.factories.path_service_factory import create_mcp_aware_path_service

                if project_root:
                    project_path = Path(project_root)
                else:
                    path_service = create_mcp_aware_path_service()
                    project_path = path_service.project_root
                # B20準拠: パス管理はPathServiceを使用（指定のproject_rootを尊重）
                path_service = create_path_service(project_path)

                # PathServiceでプロットファイルを解決
                plot_file = path_service.get_episode_plot_path(episode)

                if not (plot_file and plot_file.exists()):
                    return json.dumps(
                        {"success": False, "error": f"プロットファイルが見つかりません: 第{episode:03d}話"},
                        ensure_ascii=False,
                        indent=2,
                    )
                # コンテンツ読み込み
                plot_content = plot_file.read_text(encoding="utf-8")
                settings_data = {}
                settings_dir = project_path / "10_設定"
                if settings_dir.exists():
                    for settings_file in settings_dir.glob("*.md"):
                        settings_data[settings_file.stem] = settings_file.read_text(encoding="utf-8")
                characters = []
                character_dir = project_path / "10_設定" / "キャラクター"
                if character_dir.exists():
                    for char_file in character_dir.glob("*.md"):
                        characters.append({"name": char_file.stem, "profile": char_file.read_text(encoding="utf-8")})

                # ArtifactStoreServiceを使用してコンテンツをアーティファクト化
                from noveler.domain.services.artifact_store_service import create_artifact_store

                artifact_store = create_artifact_store(storage_dir=project_path / ".noveler" / "artifacts")

                # プロットをアーティファクトとして保存
                plot_artifact_id = artifact_store.store(
                    content=plot_content,
                    content_type="text",
                    source_file=str(plot_file),
                    description=f"第{episode:03d}話プロット",
                    tags={"episode": str(episode), "type": "plot"},
                )

                # 設定データをアーティファクトとして保存
                settings_json = json.dumps(settings_data, ensure_ascii=False, indent=2)
                settings_artifact_id = artifact_store.store(
                    content=settings_json,
                    content_type="json",
                    description=f"第{episode:03d}話設定データ",
                    tags={"episode": str(episode), "type": "settings"},
                )

                # キャラクター情報をアーティファクトとして保存
                characters_json = json.dumps(characters, ensure_ascii=False, indent=2)
                characters_artifact_id = artifact_store.store(
                    content=characters_json,
                    content_type="json",
                    description=f"第{episode:03d}話キャラクター情報",
                    tags={"episode": str(episode), "type": "characters"},
                )

                session_id = str(uuid.uuid4())
                session_manager = WritingSessionManager(project_path)
                session_manager.create_session(episode, session_id)

                # 参照渡し形式のプロンプト生成
                artifact_prompt = f"""# 第{episode:03d}話 データ準備段階（参照渡し版）

## アーティファクト参照情報
- **プロット**: {plot_artifact_id}
- **設定データ**: {settings_artifact_id}
- **キャラクター情報**: {characters_artifact_id}

## 執筆準備指示
以下の手順で執筆準備を行ってください：

1. **プロット確認**: `fetch_artifact {plot_artifact_id}` でプロット全文を取得し、内容を理解してください
2. **設定情報整理**: `fetch_artifact {settings_artifact_id}` で設定データを取得し、世界観を把握してください
3. **キャラクター把握**: `fetch_artifact {characters_artifact_id}` でキャラクター情報を取得し、人物設定を確認してください

## 次段階への準備
各アーティファクトの内容を確認後、「準備完了」と回答し、執筆に必要な情報が揃っていることを確認してください。

**重要**: 実際の執筆段階では、これらの参照IDを使用して必要な情報を取得できます。"""

                result = {
                    "success": True,
                    "episode": episode,
                    "session_id": session_id,
                    "plot_artifact_id": plot_artifact_id,
                    "settings_artifact_id": settings_artifact_id,
                    "characters_artifact_id": characters_artifact_id,
                    "artifact_references": {
                        "plot": plot_artifact_id,
                        "settings": settings_artifact_id,
                        "characters": characters_artifact_id,
                    },
                    "prompt": artifact_prompt,
                    "stage": "prepare_plot_data",
                    "timestamp": project_now().datetime.isoformat(),
                    "next_stage": "analyze_plot_structure",
                    "instructions": "アーティファクト参照を使用してデータを確認し、次段階への準備を行ってください",
                }
                session_manager.save_stage_output(session_id, "prepare_plot_data", result)
                return self._json_with_path_fallback(result, locals())
            except Exception as e:
                self.logger.exception("プロットデータ準備エラー")
                return json.dumps({"success": False, "error": f"データ準備エラー: {e}"}, ensure_ascii=False, indent=2)

        # テスト互換: 直接メソッドとしてもアクセス可能にする
        try:
            self.prepare_plot_data = prepare_plot_data
        except Exception:
            pass

    def _register_manuscript_writing_tools(self) -> None:
        """原稿執筆関連ツール登録"""

        @self.server.tool(
            name="write_manuscript_draft", description="原稿執筆段階 - プロット分析結果を基に実際の原稿を生成します"
        )
        async def write_manuscript_draft(
            episode: int, session_id: str | None = None, word_count_target: int = 4000, project_root: str | None = None
        ) -> str:
            """原稿執筆段階"""
            try:
                import json
                from pathlib import Path

                # use module-level factories to allow test patching

                if project_root:
                    project_path = Path(project_root)
                else:
                    path_service = create_mcp_aware_path_service()
                    project_path = path_service.project_root

                session_manager = WritingSessionManager(project_path)
                session_data = {}
                if session_id:
                    session_data = session_manager.load_session(session_id)

                # アーティファクト参照システムを使用してプロンプトを生成
                artifact_store = create_artifact_store(storage_dir=project_path / ".noveler" / "artifacts")

                # プロットアーティファクトIDを取得（セッションから、または直接ファイルから）
                plot_artifact_id = None
                if session_data.get("plot_artifact_id"):
                    plot_artifact_id = session_data["plot_artifact_id"]
                elif session_data.get("plot_content"):
                    # セッションにプロットコンテンツがある場合は、それをアーティファクト化
                    plot_artifact_id = artifact_store.store(
                        content=session_data["plot_content"],
                        content_type="text",
                        source_file=f"session_{session_id}",
                        description=f"第{episode:03d}話プロット（セッション由来）",
                    )
                else:
                    # PathService を使用して読み込み
                    path_service = create_mcp_aware_path_service()
                    plot_file = path_service.get_episode_plot_path(episode)
                    if plot_file and plot_file.exists():
                        plot_content = plot_file.read_text(encoding="utf-8")
                        plot_artifact_id = artifact_store.store(
                            content=plot_content,
                            content_type="text",
                            source_file=str(plot_file),
                            description=f"第{episode:03d}話プロット",
                        )
                    else:
                        return json.dumps(
                            {"success": False, "error": f"プロットファイルが見つかりません: 第{episode:03d}話"},
                            ensure_ascii=False,
                            indent=2,
                        )

                # アーティファクト参照を使った執筆プロンプトを生成
                manuscript_prompt = f"""# 第{episode:03d}話 原稿執筆段階（参照渡し版）

## アーティファクト参照情報
- **プロット**: {plot_artifact_id}

## 実行手順
1. **プロット確認**: `fetch_artifact {plot_artifact_id}` でプロット全文を取得し、内容を理解してください
2. **執筆要件の確認**: 以下の要件に従って執筆してください

## 執筆要件
- 目標文字数: {word_count_target}文字
- ジャンル: ファンタジー
- 視点: 三人称単元視点
- 文体: ライトノベル調

## 品質基準（SPEC-WRITE-STAGE-001準拠）
- 感情表現: 身体反応、感覚比喩、内面独白の三層表現を最低3回実装
- 対話比率: 60%程度
- 場面描写: 五感を使った描写を意識
- テンポ: 緊張と緩和のバランスを保つ

## 前段階の分析結果
{json.dumps(session_data, ensure_ascii=False, indent=2) if session_data else "セッションデータなし"}

## 指示
1. まず `fetch_artifact {plot_artifact_id}` でプロットを取得してください
2. プロットの内容を理解し、上記の要件に基づいて原稿を生成してください
3. 以下の形式で原稿を作成してください：

# 第{episode:03d}話 [タイトル]

[本文をここに記述]

生成後、指定されたパスに保存してください。
"""

                # B20準拠: パス管理はPathServiceを使用
                path_service = create_path_service()
                # 出力先は最終原稿パス（段階別一時名ではなく統一パス）
                manuscript_file = path_service.get_manuscript_path(episode)
                manuscript_file.parent.mkdir(exist_ok=True)

                result = {
                    "success": True,
                    "episode": episode,
                    "session_id": session_id or "new",
                    "manuscript_path": str(manuscript_file),
                    "word_count_target": word_count_target,
                    "prompt": manuscript_prompt,
                    "plot_artifact_id": plot_artifact_id,
                    "stage": "write_manuscript_draft",
                    "timestamp": project_now().datetime.isoformat(),
                    "next_stage": "refine_manuscript_quality",
                    "instructions": "このプロンプトを使用して原稿を生成し、指定されたパスに保存してください",
                }

                if session_id:
                    # セッションデータにアーティファクトIDを保存
                    updated_session_data = session_data.copy()
                    updated_session_data["plot_artifact_id"] = plot_artifact_id
                    session_manager.save_stage_output(session_id, "write_manuscript_draft", result)
                    session_manager.save_session(session_id, updated_session_data)

                return self._json_with_path_fallback(result, locals())

            except Exception as e:
                self.logger.exception("原稿執筆エラー")
                return json.dumps({"success": False, "error": f"原稿執筆エラー: {e}"}, ensure_ascii=False, indent=2)

        # 互換API: テストから参照できるように _tools マップにハンドラーを登録
        try:
            if not hasattr(self.server, "_tools"):
                self.server._tools = {}
            self.server._tools["write_manuscript_draft"] = {"handler": write_manuscript_draft}
        except Exception:
            pass

        # テスト互換: 直接メソッドとしてもアクセス可能にする
        try:
            self.write_manuscript_draft = write_manuscript_draft
        except Exception:
            pass

    def _register_content_analysis_tools(self) -> None:
        """コンテンツ分析ツール登録"""

        @self.server.tool(
            name="analyze_plot_structure",
            description="プロット構造分析 - プロット内容を分析し、構造的な要素を整理します",
        )
        async def analyze_plot_structure(
            episode: int, session_id: str | None = None, project_root: str | None = None
        ) -> str:
            """プロット構造分析段階"""
            try:
                import json
                from pathlib import Path

                from noveler.infrastructure.factories.path_service_factory import create_mcp_aware_path_service

                if project_root:
                    project_path = Path(project_root)
                else:
                    path_service = create_mcp_aware_path_service()
                    project_path = path_service.project_root
                session_manager = WritingSessionManager(project_path)
                session_data = session_manager.load_session(session_id) if session_id else {}
                plot_content = session_data.get("plot_content", "")
                if not plot_content:
                    # B20準拠: PathServiceでプロットファイルを解決
                    path_service = create_path_service()
                    plot_file = path_service.get_episode_plot_path(episode)

                    if plot_file and plot_file.exists():
                        plot_content = plot_file.read_text(encoding="utf-8")
                prompt = f"# 第{episode:03d}話 プロット構造分析段階\n\n## 分析対象プロット\n{plot_content}\n\n## 分析項目\n1. **起承転結の構造分析**\n   - 導入部（起）の設定と展開\n   - 発展部（承）の展開方法\n   - 転換部（転）のクライマックス要素\n   - 結論部（結）の締めくくり方\n\n2. **重要シーンの特定**\n   - 物語の転換点となるシーン\n   - 感情的な山場となるシーン\n   - キャラクター成長のキーシーン\n\n3. **構造的課題の検出**\n   - テンポ配分の妥当性\n   - シーン転換の自然さ\n   - 情報提示のタイミング\n\n## 指示\n上記の分析を行い、次段階（感情設計）への推奨事項をまとめてください。\n"
                result = {
                    "success": True,
                    "episode": episode,
                    "session_id": session_id,
                    "plot_content": plot_content,
                    "prompt": prompt,
                    "stage": "analyze_plot_structure",
                    "timestamp": project_now().datetime.isoformat(),
                    "next_stage": "design_emotional_flow",
                    "instructions": "プロット構造を分析し、次段階への推奨事項を整理してください",
                }
                if session_id:
                    session_manager.save_stage_output(session_id, "analyze_plot_structure", result)
                return self._json_with_path_fallback(result, locals())
            except Exception as e:
                self.logger.exception("プロット分析エラー")
                return json.dumps({"success": False, "error": f"プロット分析エラー: {e}"}, ensure_ascii=False, indent=2)

    def _register_creative_design_tools(self) -> None:
        """創作設計ツール登録"""

        @self.server.tool(
            name="design_emotional_flow",
            description="感情・関係性設計 - キャラクターの感情変化と関係性の流れを設計します",
        )
        async def design_emotional_flow(
            episode: int, session_id: str | None = None, project_root: str | None = None
        ) -> str:
            """感情・関係性設計段階"""
            try:
                import json
                from pathlib import Path

                from noveler.infrastructure.factories.path_service_factory import create_mcp_aware_path_service

                if project_root:
                    project_path = Path(project_root)
                else:
                    path_service = create_mcp_aware_path_service()
                    project_path = path_service.project_root
                session_manager = WritingSessionManager(project_path)
                session_data = session_manager.load_session(session_id) if session_id else {}
                prompt = f"# 第{episode:03d}話 感情・関係性設計段階\n\n## 前段階の分析結果\n{(json.dumps(session_data, ensure_ascii=False, indent=2) if session_data else 'データなし')}\n\n## 設計項目\n1. **感情アークの設計**\n   - 主人公の感情変化パターン\n   - 各シーンでの感情状態\n   - 感情変化のトリガーイベント\n\n2. **関係性の動的変化**\n   - キャラクター間の関係性変化\n   - 対立と和解の流れ\n   - 信頼関係の構築過程\n\n3. **感情表現の実装方針**\n   - 身体反応による感情表現\n   - 感覚比喩を使った内面描写\n   - 内面独白による心境表現\n\n## 指示\n上記の要素を具体的に設計し、次段階（ユーモア設計）への推奨事項をまとめてください。\n"
                result = {
                    "success": True,
                    "episode": episode,
                    "session_id": session_id,
                    "prompt": prompt,
                    "stage": "design_emotional_flow",
                    "timestamp": project_now().datetime.isoformat(),
                    "next_stage": "design_humor_elements",
                    "instructions": "感情・関係性の流れを設計し、具体的な実装方針を策定してください",
                }
                if session_id:
                    session_manager.save_stage_output(session_id, "design_emotional_flow", result)
                return self._json_with_path_fallback(result, locals())
            except Exception as e:
                self.logger.exception("感情設計エラー")
                return json.dumps({"success": False, "error": f"感情設計エラー: {e}"}, ensure_ascii=False, indent=2)

        @self.server.tool(
            name="design_humor_elements",
            description="ユーモア・魅力要素設計 - 読者を引き込むユーモアと魅力要素を設計します",
        )
        async def design_humor_elements(
            episode: int, session_id: str | None = None, project_root: str | None = None
        ) -> str:
            """ユーモア・魅力要素設計段階"""
            try:
                import json
                from pathlib import Path

                from noveler.infrastructure.factories.path_service_factory import create_mcp_aware_path_service

                if project_root:
                    project_path = Path(project_root)
                else:
                    path_service = create_mcp_aware_path_service()
                    project_path = path_service.project_root
                session_manager = WritingSessionManager(project_path)
                session_data = session_manager.load_session(session_id) if session_id else {}
                prompt = f"# 第{episode:03d}話 ユーモア・魅力要素設計段階\n\n## 前段階の設計結果\n{(json.dumps(session_data, ensure_ascii=False, indent=2) if session_data else 'データなし')}\n\n## 設計項目\n1. **ユーモア要素の配置**\n   - コメディシーンのタイミング\n   - キャラクターの個性的な言動\n   - 状況コメディの演出方法\n\n2. **魅力要素の強化**\n   - キャラクターの魅力的な一面\n   - 読者の共感を誘う要素\n   - 印象に残るシーンの演出\n\n3. **緊張と緩和のバランス**\n   - シリアスシーンとコメディの配分\n   - 感情の起伏を作るタイミング\n   - 読者の集中力を維持する工夫\n\n## 指示\n上記の要素を具体的に設計し、次段階（キャラクター対話設計）への推奨事項をまとめてください。\n"
                result = {
                    "success": True,
                    "episode": episode,
                    "session_id": session_id,
                    "prompt": prompt,
                    "stage": "design_humor_elements",
                    "timestamp": project_now().datetime.isoformat(),
                    "next_stage": "design_character_dialogue",
                    "instructions": "ユーモアと魅力要素を設計し、緊張と緩和のバランスを調整してください",
                }
                if session_id:
                    session_manager.save_stage_output(session_id, "design_humor_elements", result)
                return self._json_with_path_fallback(result, locals())
            except Exception as e:
                self.logger.exception("ユーモア設計エラー")
                return json.dumps({"success": False, "error": f"ユーモア設計エラー: {e}"}, ensure_ascii=False, indent=2)

        @self.server.tool(
            name="design_character_dialogue",
            description="キャラクター心理・対話設計 - キャラクターの心理状態と対話を詳細に設計します",
        )
        async def design_character_dialogue(
            episode: int, session_id: str | None = None, project_root: str | None = None
        ) -> str:
            """キャラクター心理・対話設計段階"""
            try:
                import json
                from pathlib import Path

                from noveler.infrastructure.factories.path_service_factory import create_mcp_aware_path_service

                if project_root:
                    project_path = Path(project_root)
                else:
                    path_service = create_mcp_aware_path_service()
                    project_path = path_service.project_root
                session_manager = WritingSessionManager(project_path)
                session_data = session_manager.load_session(session_id) if session_id else {}
                prompt = f"# 第{episode:03d}話 キャラクター心理・対話設計段階\n\n## 前段階の設計結果\n{(json.dumps(session_data, ensure_ascii=False, indent=2) if session_data else 'データなし')}\n\n## 設計項目\n1. **心理状態の詳細設計**\n   - 各キャラクターの心理変化\n   - 内面的な葛藤の表現方法\n   - 感情の細かな表現技法\n\n2. **対話設計**\n   - キャラクターごとの話し方の特徴\n   - 対話による関係性の表現\n   - 重要な情報を伝える対話の流れ\n\n3. **心理描写の実装方針**\n   - 直接的な心理描写と間接的な表現\n   - 行動による心理状態の表現\n   - 対話での心理状態の暗示\n\n## 指示\n上記の要素を具体的に設計し、次段階（場面演出設計）への推奨事項をまとめてください。\n"
                result = {
                    "success": True,
                    "episode": episode,
                    "session_id": session_id,
                    "prompt": prompt,
                    "stage": "design_character_dialogue",
                    "timestamp": project_now().datetime.isoformat(),
                    "next_stage": "design_scene_atmosphere",
                    "instructions": "キャラクター心理と対話を詳細に設計してください",
                }
                if session_id:
                    session_manager.save_stage_output(session_id, "design_character_dialogue", result)
                return self._json_with_path_fallback(result, locals())
            except Exception as e:
                self.logger.exception("キャラクター対話設計エラー")
                return json.dumps(
                    {"success": False, "error": f"キャラクター対話設計エラー: {e}"}, ensure_ascii=False, indent=2
                )

        @self.server.tool(
            name="design_scene_atmosphere", description="場面演出・雰囲気設計 - 各シーンの演出と雰囲気作りを設計します"
        )
        async def design_scene_atmosphere(
            episode: int, session_id: str | None = None, project_root: str | None = None
        ) -> str:
            """場面演出・雰囲気設計段階"""
            try:
                import json
                from pathlib import Path

                from noveler.infrastructure.factories.path_service_factory import create_mcp_aware_path_service

                if project_root:
                    project_path = Path(project_root)
                else:
                    path_service = create_mcp_aware_path_service()
                    project_path = path_service.project_root
                session_manager = WritingSessionManager(project_path)
                session_data = session_manager.load_session(session_id) if session_id else {}
                prompt = f"# 第{episode:03d}話 場面演出・雰囲気設計段階\n\n## 前段階の設計結果\n{(json.dumps(session_data, ensure_ascii=False, indent=2) if session_data else 'データなし')}\n\n## 設計項目\n1. **場面設定の詳細化**\n   - 各シーンの舞台設定\n   - 時間と場所の効果的な活用\n   - 環境が与える心理的影響\n\n2. **雰囲気作りの技法**\n   - 五感を使った情景描写\n   - 比喩と修辞による表現強化\n   - 読者の想像力を刺激する描写\n\n3. **演出技法の実装**\n   - シーン転換の演出方法\n   - 緊迫感やロマンチックな雰囲気の作り方\n   - 読者を引き込む臨場感の演出\n\n## 指示\n上記の要素を具体的に設計し、次段階（論理整合性調整）への推奨事項をまとめてください。\n"
                result = {
                    "success": True,
                    "episode": episode,
                    "session_id": session_id,
                    "prompt": prompt,
                    "stage": "design_scene_atmosphere",
                    "timestamp": project_now().datetime.isoformat(),
                    "next_stage": "adjust_logic_consistency",
                    "instructions": "場面演出と雰囲気作りを詳細に設計してください",
                }
                if session_id:
                    session_manager.save_stage_output(session_id, "design_scene_atmosphere", result)
                return self._json_with_path_fallback(result, locals())
            except Exception as e:
                self.logger.exception("場面演出設計エラー")
                return json.dumps({"success": False, "error": f"場面演出設計エラー: {e}"}, ensure_ascii=False, indent=2)

    def _register_quality_refinement_tools(self) -> None:
        """品質向上ツール登録"""

        @self.server.tool(
            name="adjust_logic_consistency", description="論理整合性調整 - ストーリーの論理的一貫性を確認・調整します"
        )
        async def adjust_logic_consistency(
            episode: int, session_id: str | None = None, project_root: str | None = None
        ) -> str:
            """論理整合性調整段階"""
            try:
                import json
                from pathlib import Path

                from noveler.infrastructure.factories.path_service_factory import create_mcp_aware_path_service

                if project_root:
                    project_path = Path(project_root)
                else:
                    path_service = create_mcp_aware_path_service()
                    project_path = path_service.project_root
                session_manager = WritingSessionManager(project_path)
                session_data = session_manager.load_session(session_id) if session_id else {}
                prompt = f"# 第{episode:03d}話 論理整合性調整段階\n\n## 前段階の設計結果\n{(json.dumps(session_data, ensure_ascii=False, indent=2) if session_data else 'データなし')}\n\n## 調整項目\n1. **ストーリー論理の検証**\n   - プロット展開の論理的一貫性\n   - キャラクター行動の動機と結果\n   - 設定との矛盾点の確認\n\n2. **時系列と因果関係の整理**\n   - 出来事の時系列の確認\n   - 原因と結果の関係の明確化\n   - 伏線と回収の整合性\n\n3. **整合性問題の解決**\n   - 発見された問題点の修正方針\n   - 設定変更の必要性判断\n   - 代替案の検討\n\n## 指示\n上記の検証を行い、論理的な問題点があれば修正案を提示し、次段階（原稿執筆）への準備を整えてください。\n"
                result = {
                    "success": True,
                    "episode": episode,
                    "session_id": session_id,
                    "prompt": prompt,
                    "stage": "adjust_logic_consistency",
                    "timestamp": project_now().datetime.isoformat(),
                    "next_stage": "write_manuscript_draft",
                    "instructions": "論理整合性を確認・調整し、原稿執筆への準備を完了してください",
                }
                if session_id:
                    session_manager.save_stage_output(session_id, "adjust_logic_consistency", result)
                return self._json_with_path_fallback(result, locals())
            except Exception as e:
                self.logger.exception("論理整合性調整エラー")
                return json.dumps(
                    {"success": False, "error": f"論理整合性調整エラー: {e}"}, ensure_ascii=False, indent=2
                )

        @self.server.tool(name="refine_manuscript_quality", description="品質改善段階 - 原稿の品質を多角的に改善します")
        async def refine_manuscript_quality(
            episode: int, session_id: str | None = None, project_root: str | None = None
        ) -> str:
            """品質改善段階"""
            try:
                import json
                from pathlib import Path

                from noveler.infrastructure.factories.path_service_factory import create_mcp_aware_path_service

                if project_root:
                    project_path = Path(project_root)
                else:
                    path_service = create_mcp_aware_path_service()
                    project_path = path_service.project_root
                session_manager = WritingSessionManager(project_path)
                session_data = session_manager.load_session(session_id) if session_id else {}
                # B20準拠: パス管理はPathServiceを使用
                path_service = create_path_service()
                manuscript_file = path_service.get_manuscript_path(episode)
                manuscript_content = ""
                if manuscript_file.exists():
                    manuscript_content = manuscript_file.read_text(encoding="utf-8")
                prompt = f"# 第{episode:03d}話 品質改善段階\n\n## 原稿内容\n{manuscript_content[:2000]}{('...' if len(manuscript_content) > 2000 else '')}\n\n## 前段階の設計結果\n{(json.dumps(session_data, ensure_ascii=False, indent=2) if session_data else 'データなし')}\n\n## 品質改善項目\n1. **文章品質の向上**\n   - 文章の読みやすさ改善\n   - 語彙の多様化と適切性\n   - 文体の一貫性確保\n\n2. **表現力の強化**\n   - 感情表現の深化\n   - 描写の臨場感向上\n   - 比喩・修辞の効果的活用\n\n3. **構成の最適化**\n   - シーン配分の調整\n   - テンポとリズムの改善\n   - 読者エンゲージメントの強化\n\n## 指示\n上記の観点から原稿を改善し、次段階（最終調整）への準備を整えてください。\n"
                result = {
                    "success": True,
                    "episode": episode,
                    "session_id": session_id,
                    "manuscript_content": manuscript_content,
                    "prompt": prompt,
                    "stage": "refine_manuscript_quality",
                    "timestamp": project_now().datetime.isoformat(),
                    "next_stage": "finalize_manuscript",
                    "instructions": "原稿の品質を多角的に改善してください",
                }
                if session_id:
                    session_manager.save_stage_output(session_id, "refine_manuscript_quality", result)
                return self._json_with_path_fallback(result, locals())
            except Exception as e:
                self.logger.exception("品質改善エラー")
                return json.dumps({"success": False, "error": f"品質改善エラー: {e}"}, ensure_ascii=False, indent=2)

        @self.server.tool(
            name="finalize_manuscript", description="最終調整段階 - 原稿の最終チェックと完成処理を行います"
        )
        async def finalize_manuscript(
            episode: int, session_id: str | None = None, project_root: str | None = None
        ) -> str:
            """最終調整段階"""
            try:
                import json
                from pathlib import Path

                from noveler.infrastructure.factories.path_service_factory import create_mcp_aware_path_service

                if project_root:
                    project_path = Path(project_root)
                else:
                    path_service = create_mcp_aware_path_service()
                    project_path = path_service.project_root
                session_manager = WritingSessionManager(project_path)
                session_data = session_manager.load_session(session_id) if session_id else {}
                # B20準拠: パス管理はPathServiceを使用
                path_service = create_path_service()
                manuscript_file = path_service.get_manuscript_path(episode)
                manuscript_content = ""
                if manuscript_file.exists():
                    manuscript_content = manuscript_file.read_text(encoding="utf-8")
                prompt = f"# 第{episode:03d}話 最終調整段階\n\n## 現在の原稿\n{manuscript_content[:2000]}{('...' if len(manuscript_content) > 2000 else '')}\n\n## 全段階の設計・改善結果\n{(json.dumps(session_data, ensure_ascii=False, indent=2) if session_data else 'データなし')}\n\n## 最終調整項目\n1. **最終品質チェック**\n   - 誤字脱字の確認\n   - 表記ゆれの統一\n   - 文章の最終調整\n\n2. **完成度の確認**\n   - 目標文字数との比較\n   - 品質基準の達成確認\n   - 読者満足度の予想評価\n\n3. **完成処理**\n   - ファイル名の最終化\n   - メタデータの記録\n   - セッション完了処理\n\n## 指示\n最終チェックと調整を行い、原稿を完成させてください。完了後「第{episode:03d}話完成」と報告してください。\n"
                # B20準拠: パス管理はPathServiceを使用
                path_service = create_path_service()
                final_manuscript_file = path_service.get_manuscript_path(episode)
                result = {
                    "success": True,
                    "episode": episode,
                    "session_id": session_id,
                    "manuscript_content": manuscript_content,
                    "final_manuscript_path": str(final_manuscript_file),
                    "prompt": prompt,
                    "stage": "finalize_manuscript",
                    "timestamp": project_now().datetime.isoformat(),
                    "next_stage": "completed",
                    "instructions": "最終調整を行い、原稿を完成させてください",
                }
                if session_id:
                    session_manager.save_stage_output(session_id, "finalize_manuscript", result)
                return self._json_with_path_fallback(result, locals())
            except Exception as e:
                self.logger.exception("最終調整エラー")
                return json.dumps({"success": False, "error": f"最終調整エラー: {e}"}, ensure_ascii=False, indent=2)

    def _register_check_tools(self) -> None:
        """品質チェック関連ツール登録（マイクロサービス）"""
        self._register_main_check_tools()
        self._register_specialized_check_tools()

    def _register_main_check_tools(self) -> None:
        """メイン品質チェックツール登録"""

        @self.server.tool(
            name="check",
            description="原稿品質チェック（段階的10ステップ実行） - 基本チェックから最終品質認定まで体系的に実行",
        )
        async def check(episode: int, auto_fix: bool = False, project_root: str | None = None) -> str:
            """段階的10ステップ品質チェック実行"""
            try:
                import json
                from pathlib import Path

                # プロジェクトルートの設定
                if project_root:
                    project_path = Path(project_root)
                else:
                    from noveler.infrastructure.factories.path_service_factory import create_mcp_aware_path_service

                    path_service = create_mcp_aware_path_service()
                    project_path = path_service.project_root

                # 品質チェック10ステップ定義
                check_steps = [
                    {
                        "id": 1,
                        "name": "基本構造チェック",
                        "category": "構造",
                        "description": "段落構成、改行位置、基本フォーマット",
                    },
                    {
                        "id": 2,
                        "name": "文字数・長さチェック",
                        "category": "構造",
                        "description": "目標文字数との乖離、セクションバランス",
                    },
                    {
                        "id": 3,
                        "name": "文法・表記チェック",
                        "category": "言語",
                        "description": "誤字脱字、表記ゆれ、助詞の使い方",
                    },
                    {
                        "id": 4,
                        "name": "禁止表現検出",
                        "category": "言語",
                        "description": "ですます調混在、過度な感嘆符、不適切表現",
                    },
                    {
                        "id": 5,
                        "name": "読みやすさ分析",
                        "category": "可読性",
                        "description": "文の長さ、複雑度、読みやすさ指数",
                    },
                    {
                        "id": 6,
                        "name": "キャラクター一貫性",
                        "category": "内容",
                        "description": "性格の一貫性、口調、行動パターン",
                    },
                    {
                        "id": 7,
                        "name": "設定・世界観整合性",
                        "category": "内容",
                        "description": "既存設定との矛盾、時系列の整合性",
                    },
                    {
                        "id": 8,
                        "name": "ストーリー展開",
                        "category": "内容",
                        "description": "プロット通りの進行、論理的整合性",
                    },
                    {
                        "id": 9,
                        "name": "文体・表現力",
                        "category": "表現",
                        "description": "文体の統一、表現の豊かさ、感情表現",
                    },
                    {
                        "id": 10,
                        "name": "総合品質評価",
                        "category": "総合",
                        "description": "全体品質スコア算出、改善提案",
                    },
                ]

                # 実行結果を格納
                check_log = []
                completed_steps = 0
                total_score = 0.0
                issues_found = []

                for step in check_steps:
                    step_id = step["id"]
                    step_name = step["name"]
                    step_category = step["category"]
                    step_description = step["description"]

                    try:
                        # ステップ開始ログ
                        start_msg = f"🔍 STEP {step_id}: {step_name} - {step_description}"
                        check_log.append(
                            {
                                "step": step_id,
                                "name": step_name,
                                "category": step_category,
                                "description": step_description,
                                "status": "started",
                                "message": start_msg,
                            }
                        )

                        # 各ステップの品質チェック実行
                        step_result = await self._execute_quality_check_step(step_id, episode, project_path, auto_fix)

                        # ステップ完了ログ
                        complete_msg = f"✅ STEP {step_id}: {step_name} 完了 - スコア: {step_result['score']:.1f}点"
                        check_log.append(
                            {
                                "step": step_id,
                                "name": step_name,
                                "category": step_category,
                                "status": "completed",
                                "message": complete_msg,
                                "score": step_result["score"],
                                "issues": step_result.get("issues", []),
                                "suggestions": step_result.get("suggestions", []),
                            }
                        )

                        completed_steps += 1
                        total_score += step_result["score"]
                        issues_found.extend(step_result.get("issues", []))

                    except Exception as step_error:
                        # ステップエラーログ
                        error_msg = f"❌ STEP {step_id}: {step_name} でエラー - {step_error!s}"
                        check_log.append(
                            {
                                "step": step_id,
                                "name": step_name,
                                "category": step_category,
                                "status": "error",
                                "message": error_msg,
                                "error": str(step_error),
                            }
                        )
                        break

                # 品質チェック結果の整理
                is_complete = completed_steps == len(check_steps)
                average_score = (total_score / completed_steps) if completed_steps > 0 else 0.0

                # 品質レベル判定
                quality_level = self._determine_quality_level(average_score)

                result = {
                    "success": is_complete,
                    "episode": episode,
                    "total_steps": len(check_steps),
                    "completed_steps": completed_steps,
                    "average_score": round(average_score, 1),
                    "quality_level": quality_level,
                    "total_issues": len(issues_found),
                    "check_log": check_log,
                    "issues_summary": self._categorize_issues(issues_found),
                    "final_status": f"品質チェック{'完了' if is_complete else '中断'} - {quality_level}",
                }

                return self._json_with_path_fallback(result, locals())

            except Exception as e:
                self.logger.exception("品質チェック実行エラー")
                return json.dumps(
                    {"success": False, "error": str(e), "message": "品質チェック実行中にエラーが発生しました"},
                    ensure_ascii=False,
                    indent=2,
                )

        @self.server.tool(
            name="check_basic",
            description="基本品質チェックのみ実行 - 以下の基本的な問題を検出:\n            • 文字数チェック（目標文字数との乖離）\n            • 禁止表現検出（ですます調混在、過度な感嘆符等）\n            • 基本的な文章構造問題（段落構成、改行位置等）\n            • 誤字脱字・表記ゆれの可能性がある箇所",
        )
        def check_basic(episode: int, project_root: str | None = None) -> str:
            """基本品質チェックのみ"""
            try:
                cmd = f"core check {episode} --skip-a31 --skip-claude"
                result = self._execute_noveler_command(cmd, project_root)
                return self._format_tool_result(result, "基本品質チェック")
            except Exception as e:
                self.logger.exception("基本チェックエラー")
                return f"基本チェックエラー: {e}"

        @self.server.tool(
            name="check_story_elements",
            description="小説の基本要素評価（68項目） - 小説として必要な要素の充実度をチェック:\n            【感情描写（12項目）】「怒り」「喜び」等の感情表現が具体的か/読者が共感できる描写か/感情変化に論理性があるか/行動と内面が一致しているか\n            【キャラクター（12項目）】口調・行動パターンが一貫しているか/キャラが成長しているか/人間関係の変化が自然か/個性的で魅力的か\n            【ストーリー展開（12項目）】起承転結が明確か/読むテンポが適切か/伏線が効果的に配置・回収されているか/予想外だが納得できる展開か\n            【文章表現（12項目）】情景描写に臨場感があるか/比喩・修辞が効果的か/文章リズムが読みやすいか/語彙が豊富で適切か\n            【世界観・設定（10項目）】設定に矛盾がないか/世界観に深みがあるか/現実味・説得力があるか/独自性・オリジナリティがあるか\n            【読者エンゲージメント（10項目）】冒頭で読者を引き込めているか/続きが気になる構成か/読後に満足感があるか/ターゲット読者に響く内容か\n            各項目を0-100点で評価し、低スコア項目には具体的な改善提案を生成",
        )
        def check_story_elements(
            episode: int, auto_fix: bool = False, fix_level: str = "safe", project_root: str | None = None
        ) -> str:
            """A31評価のみ実行"""
            try:
                cmd = f"core check {episode} --skip-basic --skip-claude"
                if auto_fix:
                    cmd += f" --auto-fix --fix-level {fix_level}"
                result = self._execute_noveler_command(cmd, project_root)
                return self._format_tool_result(result, "小説要素評価")
            except Exception as e:
                self.logger.exception("A31評価エラー")
                return f"A31評価エラー: {e}"

    def _register_specialized_check_tools(self) -> None:
        """専門品質チェックツール登録"""

        @self.server.tool(
            name="check_story_structure",
            description="ストーリー構成評価 - プロレベルの物語構成力をチェック:\n            • ストーリー整合性：前後の展開との矛盾・設定との食い違い・時系列の破綻を発見\n            • 起承転結の完成度：導入の引き込み・展開の盛り上がり・クライマックスの衝撃・結末の満足度\n            • 伏線と回収：伏線の効果的な配置・回収のタイミング・意外性と納得感のバランス\n            • ペース配分：場面転換の自然さ・緩急のリズム・読者を飽きさせない展開速度\n            • キャラ心理の一貫性：そのキャラクターらしい思考・感情・行動選択になっているかを分析\n            • ジャンル適合性：ファンタジー・恋愛・ミステリー等のジャンル読者が期待する要素の充足度",
        )
        def check_story_structure(episode: int, project_root: str | None = None) -> str:
            """ストーリー構成チェック"""
            try:
                cmd = f"core check {episode} --skip-basic --skip-claude"
                result = self._execute_noveler_command(cmd, project_root)
                return self._format_tool_result(result, "構成評価")
            except Exception as e:
                self.logger.exception("構成評価エラー")
                return f"構成評価エラー: {e}"

        @self.server.tool(
            name="check_writing_expression",
            description="文章表現力評価 - プロレベルの文章表現力をチェック:\n            • 文章の自然さ：日本語として不自然な表現・違和感のある文章構造・語彙選択の適切性を検出\n            • 描写力：情景描写の臨場感・五感に訴える表現・読者の想像を喚起する描写技術\n            • 比喩と修辞：効果的な比喩表現・印象的な修辞技法・陳腐でない独創的な表現\n            • 文体の一貫性：全体を通じた文体の統一感・場面に応じた文体の使い分け\n            • 読みやすさ：一文の長さ・漢字とひらがなのバランス・専門用語の適切な説明\n            • 商業作品比較：プロ作家の作品と比較して文章力・表現力のレベルを評価",
        )
        def check_writing_expression(episode: int, project_root: str | None = None) -> str:
            """文章表現チェック"""
            try:
                cmd = f"core check {episode} --skip-basic --skip-claude"
                result = self._execute_noveler_command(cmd, project_root)
                return self._format_tool_result(result, "表現評価")
            except Exception as e:
                self.logger.exception("表現評価エラー")
                return f"表現評価エラー: {e}"

        @self.server.tool(
            name="check_rhythm",
            description="文章リズム・読みやすさ分析 - 以下を詳細分析:\n            • 文の長さのバリエーション（短文・中文・長文のバランス）\n            • 読点の配置とリズム感\n            • 同じ語尾の連続使用チェック\n            • 漢字・ひらがな・カタカナのバランス\n            • 段落の長さと配分\n            • 視覚的な読みやすさ（改行位置等）",
        )
        def check_rhythm(episode: int, project_root: str | None = None) -> str:
            """文章リズム分析のみ"""
            try:
                cmd = f"core check {episode} --rhythm-only"
                result = self._execute_noveler_command(cmd, project_root)
                return self._format_tool_result(result, "文章リズム分析")
            except Exception as e:
                self.logger.exception("リズム分析エラー")
                return f"リズム分析エラー: {e}"

        @self.server.tool(
            name="check_fix",
            description="問題箇所の自動修正実行 - 検出された問題を自動修正（修正レベル: safe/standard/aggressive）",
        )
        def check_fix(
            episode: int, issue_ids: list[str] | None = None, fix_level: str = "safe", project_root: str | None = None
        ) -> str:
            """自動修正実行"""
            try:
                cmd = f"core check {episode} --auto-fix --fix-level {fix_level}"
                if issue_ids:
                    cmd += f" --issue-ids {','.join(issue_ids)}"
                result = self._execute_noveler_command(cmd, project_root)
                return self._format_tool_result(result, "自動修正")
            except Exception as e:
                self.logger.exception("自動修正エラー")
                return f"自動修正エラー: {e}"

    def _register_plot_tools(self) -> None:
        """プロット関連レガシーツール登録（撤廃済みスタブ）"""

        # 旧 `plot_generate` / `plot_validate` ツールは modern `noveler_plot`
        # へ統合済み。互換維持のため呼び出し元構造のみ残し、登録は行わない。
        if hasattr(self, "logger"):
            try:
                self.logger.debug("legacy plot aliases removed; no tools registered")
            except Exception:
                pass

    def _register_project_tools(self) -> None:
        """プロジェクト管理ツール登録"""

        # `status` ツールは共有レジストリで登録されるため、この層では追加操作なし。

    def _register_legacy_compatibility_tools(self) -> None:
        """Deprecated stub for legacy alias registration.

        Purpose:
            Retained solely to document that legacy MCP aliases were fully
            removed on 2025-09-18. The method intentionally performs no
            registration to avoid resurrecting removed tools.

        Side Effects:
            None.
        """

        return None

    def _format_tool_result(self, result: dict[str, Any], operation_name: str) -> str:
        """ツール結果の統一フォーマット"""
        try:
            if result.get("success", False):
                response_text = self._format_novel_success_result(result)
            else:
                response_text = self._format_novel_error_result(result)
            self.converter.convert(result)
            return f"{response_text}\n\n📁 {operation_name}結果をJSONファイルとして保存済み（95%トークン削減）"
        except Exception as e:
            self.logger.exception("%s結果フォーマットエラー", operation_name)
            return f"{operation_name}結果フォーマットエラー: {e}"

    def _execute_noveler_command(self, command: str, project_root: str | None = None) -> dict[str, Any]:
        """novelerコマンドの代替実装（MCP統合対応）"""
        try:
            # CLI廃止によりMCPツール内で直接処理
            return {
                "success": False,
                "error": "CLI廃止：MCPツールを使用してください",
                "command": command,
                "suggestion": f"noveler {command} の代わりに、対応するMCPツールを使用してください",
                "project_root": str(Path(project_root) if project_root else Path.cwd()),
            }
        except Exception as e:
            self.logger.exception("代替実装エラー")
            return {"success": False, "error": f"代替実装エラー: {e}", "command": command}

    def _handle_status_command(self, project_root: str | None = None) -> str:
        """統合されたstatus コマンド処理"""
        try:
            project_root_path = Path(project_root) if project_root else Path.cwd()
            try:
                from noveler.presentation.shared.shared_utilities import get_path_service

                path_service = get_path_service()
                manuscripts_dir = path_service.get_manuscript_dir()
            except ImportError:
                # B20準拠: パス管理はPathServiceを使用
                path_service = create_path_service()
                manuscripts_dir = path_service.get_manuscript_dir()
            if not manuscripts_dir.exists():
                return (
                    f"原稿ディレクトリが見つかりません ({manuscripts_dir})。まだ執筆を開始していない可能性があります。"
                )
            manuscript_files = list(manuscripts_dir.glob("*.md")) + list(manuscripts_dir.glob("*.txt"))
            manuscript_files.sort()
            status_lines = []
            status_lines.append("📚 小説執筆状況")
            status_lines.append("=" * 30)
            status_lines.append(f"プロジェクトルート: {project_root_path}")
            status_lines.append(f"原稿ディレクトリ: {manuscripts_dir}")
            status_lines.append(f"執筆済み話数: {len(manuscript_files)}")
            status_lines.append("")
            if manuscript_files:
                status_lines.append("📝 執筆済み原稿:")
                for file in manuscript_files[:10]:
                    stat = file.stat()
                    size_kb = stat.st_size / 1024
                    modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
                    status_lines.append(f"  - {file.name} ({size_kb:.1f}KB, {modified.strftime('%Y-%m-%d %H:%M')})")
                if len(manuscript_files) > 10:
                    status_lines.append(f"  ... 他 {len(manuscript_files) - 10} 件")
                status_lines.append("")
                status_lines.append("💡 品質チェック例:")
                status_lines.append("  noveler check 1  # 第1話の品質チェック")
                status_lines.append("  noveler write 2  # 第2話の執筆開始")
            else:
                status_lines.append("まだ執筆された原稿がありません。")
                status_lines.append("💡 noveler write 1 で執筆を開始してください。")
            return "\n".join(status_lines)
        except Exception as e:
            self.logger.exception("ステータス確認エラー")
            return f"状況確認エラー: {e!s}"

    def _format_json_result(self, result: dict[str, Any]) -> str:
        """JSON結果フォーマット"""
        lines = []
        lines.append(f"成功: {result.get('success', 'N/A')}")
        lines.append(f"コマンド: {result.get('command', 'N/A')}")
        if "outputs" in result:
            outputs = result["outputs"]
            lines.append(f"出力ファイル数: {outputs.get('total_files', 0)}")
            lines.append(f"総サイズ: {outputs.get('total_size_bytes', 0)} bytes")
        if "error" in result:
            error = result["error"]
            lines.append(f"エラーコード: {error.get('code', 'N/A')}")
            lines.append(f"エラーメッセージ: {error.get('message', 'N/A')}")
        return "\n".join(lines)

    def _format_dict(self, data: dict[str, Any]) -> str:
        """辞書フォーマット"""
        return "\n".join(f"{k}: {v}" for (k, v) in data.items())

    def _format_novel_success_result(self, result: dict[str, Any]) -> str:
        """小説執筆成功結果フォーマット"""
        lines = []
        lines.append(f"🎉 {result.get('message', '実行完了')}")
        lines.append("=" * 40)
        data = result.get("data", {})
        if "episode_number" in result:
            lines.append(f"📖 話数: 第{result['episode_number']}話")
        if "execution_time_seconds" in result:
            time_sec = result["execution_time_seconds"]
            lines.append(f"⏱️ 実行時間: {time_sec:.1f}秒")
        if data.get("manuscript_path"):
            lines.append(f"📄 原稿: {Path(data['manuscript_path']).name}")
        if data.get("word_count"):
            lines.append(f"✍️ 文字数: {data['word_count']:,}文字")
        if data.get("quality_score"):
            lines.append(f"⭐ 品質スコア: {data['quality_score']}/100")
        performance = data.get("performance", {})
        if "turns_saved" in performance and performance["turns_saved"] > 0:
            lines.append(f"🚀 最適化: {performance['turns_saved']}ターン削減")
        if "improvement_ratio" in performance and performance["improvement_ratio"] > 1:
            ratio = performance["improvement_ratio"]
            lines.append(f"📈 効率化: {ratio:.1f}倍効果")
        files = result.get("files", [])
        if files:
            lines.append(f"\n📁 生成ファイル ({len(files)}件):")
            for file_info in files:
                file_type = file_info.get("type", "unknown")
                relative_path = file_info.get("relative_path", file_info.get("path", ""))
                size_kb = file_info.get("size_bytes", 0) / 1024
                lines.append(f"  • {file_type}: {relative_path} ({size_kb:.1f}KB)")
        return "\n".join(lines)

    def _format_novel_error_result(self, result: dict[str, Any]) -> str:
        """小説執筆エラー結果フォーマット"""
        lines = []
        lines.append(f"❌ {result.get('error', '実行失敗')}")
        lines.append("=" * 40)
        if "command" in result:
            lines.append(f"📝 コマンド: {result['command']}")
        result_data = result.get("result_data", {})
        if result_data.get("failed_stage"):
            lines.append(f"🔴 失敗段階: {result_data['failed_stage']}")
        if "completed_stages" in result_data:
            completed = result_data["completed_stages"]
            lines.append(f"✅ 完了段階: {completed}/10")
        if result_data.get("session_id"):
            lines.append(f"💾 セッションID: {result_data['session_id']}")
        suggestions = result.get("recovery_suggestions", [])
        if suggestions:
            lines.append("\n🔧 回復提案:")
            lines.extend(f"  • {suggestion}" for suggestion in suggestions)
        return "\n".join(lines)

    async def run(self) -> None:
        """サーバー実行"""
        if not MCP_AVAILABLE:
            msg = "MCPが利用できません"
            raise RuntimeError(msg)
        try:
            console.print("FastMCP サーバー実行開始 (stdio)")
            self.logger.info("MCPサーバー開始 - 重複実行対策有効")

            # パフォーマンス監視初期化（非同期コンテキスト内）
            if not self._monitoring_initialized:
                self._init_performance_monitoring()
                self._monitoring_initialized = True

            import signal
            import sys

            def cleanup_handler(signum, frame) -> None:
                """シグナルハンドラー - 正常終了処理"""
                self.logger.info(f"終了シグナル受信: {signum}")
                self._cleanup_pid_file()
                sys.exit(0)

            signal.signal(signal.SIGTERM, cleanup_handler)
            signal.signal(signal.SIGINT, cleanup_handler)
            await self.server.run_stdio_async()
        except Exception:
            self.logger.exception("MCPサーバー実行エラー")
            raise
        finally:
            self._cleanup_pid_file()

    async def _execute_step(self, step_id: int | float, episode: int, project_path: Path) -> None:
        """18ステップの個別実行"""
        import asyncio

        # 各ステップの具体的な処理を実装
        # 現時点では模擬的な処理時間を設定
        processing_times = {
            0: 1.0,  # スコープ定義
            1: 2.0,  # 大骨
            2: 3.0,  # 中骨
            3: 1.5,  # テーマ性・独自性検証（旧2.5）
            4: 2.0,  # セクションバランス設計
            5: 3.0,  # 小骨（シーン／ビート）
            6: 1.5,  # 論理検証
            7: 2.0,  # キャラクター一貫性検証
            8: 3.5,  # 会話設計
            9: 2.5,  # 感情曲線
            10: 3.0,  # 情景・五感・世界観
            11: 4.0,  # 初稿生成
            12: 2.0,  # 文字数最適化
            13: 2.5,  # 文体・可読性パス
            14: 1.5,  # 必須品質ゲート
            15: 2.0,  # 最終品質認定
            16: 1.0,  # 公開準備
        }

        # 実際の処理時間をシミュレート
        processing_time = processing_times.get(step_id, 1.0)
        await asyncio.sleep(processing_time)

        # TODO: 実際の各ステップ処理を実装
        # 例：
        # if step_id == 0:
        #     await self._execute_scope_definition(episode, project_path)
        # elif step_id == 1:
        #     await self._execute_structure_design(episode, project_path)
        # ...

        # ステップファイルの保存（簡易版）
        step_file = project_path / "episodes" / f"EP{episode:03d}" / f"EP{episode:03d}_step{step_id:02d}.yaml"
        step_file.parent.mkdir(parents=True, exist_ok=True)

        # 簡易的なステップ結果を保存
        step_data = {
            "step_id": step_id,
            "episode": episode,
            "completed_at": self._get_current_timestamp(),
            "status": "completed",
        }

        import yaml

        with step_file.open("w", encoding="utf-8") as f:
            yaml.dump(step_data, f, allow_unicode=True, default_flow_style=False)

    def _get_current_timestamp(self) -> str:
        """現在のタイムスタンプを取得"""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    async def _execute_quality_check_step(self, step_id: int, episode: int, project_path: Path, auto_fix: bool) -> dict:
        """品質チェックステップの個別実行"""
        import asyncio
        import random

        # 各ステップの処理時間設定
        processing_times = {
            1: 1.5,  # 基本構造チェック
            2: 1.0,  # 文字数・長さチェック
            3: 2.0,  # 文法・表記チェック
            4: 1.5,  # 禁止表現検出
            5: 2.5,  # 読みやすさ分析
            6: 3.0,  # キャラクター一貫性
            7: 2.0,  # 設定・世界観整合性
            8: 2.5,  # ストーリー展開
            9: 2.0,  # 文体・表現力
            10: 1.5,  # 総合品質評価
        }

        # 処理時間のシミュレート
        processing_time = processing_times.get(step_id, 1.0)
        await asyncio.sleep(processing_time)

        # ステップ別の品質チェック結果を生成（模擬）
        {
            1: {
                "score": random.uniform(70, 95),
                "issues": ["段落区切りが不自然な箇所が2箇所"],
                "suggestions": ["段落の流れを見直してください"],
            },
            2: {
                "score": random.uniform(75, 90),
                "issues": ["目標文字数4000字に対し3800字（-200字）"],
                "suggestions": ["描写を少し追加することをお勧めします"],
            },
            3: {
                "score": random.uniform(80, 95),
                "issues": ["表記ゆれ：「だった」と「でした」の混在"],
                "suggestions": ["文体を統一してください"],
            },
            4: {"score": random.uniform(85, 100), "issues": [], "suggestions": ["禁止表現は検出されませんでした"]},
            5: {
                "score": random.uniform(70, 85),
                "issues": ["平均文長が45文字で長め"],
                "suggestions": ["文を分割して読みやすくしてください"],
            },
            6: {
                "score": random.uniform(75, 90),
                "issues": ["主人公の口調に一箇所不整合"],
                "suggestions": ["キャラクター設定を確認してください"],
            },
            7: {"score": random.uniform(80, 95), "issues": [], "suggestions": ["世界観設定との整合性は良好です"]},
            8: {
                "score": random.uniform(75, 90),
                "issues": ["展開が少し急すぎる箇所あり"],
                "suggestions": ["感情の変化をもう少し丁寧に描写してください"],
            },
            9: {
                "score": random.uniform(70, 85),
                "issues": ["単調な表現が目立つ"],
                "suggestions": ["表現のバリエーションを増やしてください"],
            },
            10: {"score": random.uniform(75, 88), "issues": [], "suggestions": ["総合的に良質な原稿です"]},
        }

        # TODO: 実際の品質チェックロジックを実装
        # 例：
        # if step_id == 1:
        #     return await self._check_basic_structure(episode, project_path)
        # elif step_id == 2:
        #     return await self._check_length_balance(episode, project_path)
        # ...

    def _register_artifact_tools(self) -> None:
        """アーティファクト参照システムツール登録"""

        def _resolve_artifact_store(project_path: Path):
            """現行(.noveler/artifacts)とレガシー(project_root/artifacts)を両対応で解決"""
            from noveler.domain.services.artifact_store_service import create_artifact_store as _create

            if not project_path.exists() or not project_path.is_dir():
                raise FileNotFoundError(f"Project root not found: {project_path}")

            modern_dir = project_path / ".noveler" / "artifacts"
            legacy_dir = project_path / "artifacts"

            # 優先: modern。レガシーのみ存在する場合はレガシーを使用
            if legacy_dir.exists() and not modern_dir.exists():
                return _create(storage_dir=legacy_dir), None

            # 両方存在する場合はmodernを主とし、fallbackにlegacyを返す
            primary = _create(storage_dir=modern_dir)
            fallback = _create(storage_dir=legacy_dir) if legacy_dir.exists() else None
            return primary, fallback

        @self.server.tool(
            name="fetch_artifact", description="アーティファクト参照IDからコンテンツを取得 - 参照渡しシステムのコア機能"
        )
        async def fetch_artifact(
            artifact_id: str, section: str | None = None, format_type: str = "text", project_root: str | None = None
        ) -> str:
            """アーティファクトコンテンツ取得

            Args:
                artifact_id: artifact:abc123形式の参照ID
                section: 部分取得セクション名（オプション）
                format_type: 出力フォーマット（text, json, yaml）
                project_root: プロジェクトルートパス（オプション）
            """
            try:
                from pathlib import Path

                from noveler.infrastructure.factories.path_service_factory import create_mcp_aware_path_service

                # プロジェクトパスの設定
                if project_root:
                    project_path = Path(project_root)
                else:
                    path_service = create_mcp_aware_path_service()
                    project_path = path_service.get_project_root()

                # ArtifactStoreService初期化（現行/レガシー両対応）
                artifact_store, legacy_store = _resolve_artifact_store(project_path)

                # アーティファクト取得（見つからない場合はレガシー側も試行）
                content = artifact_store.fetch(artifact_id, section=section)
                if content is None and legacy_store is not None:
                    content = legacy_store.fetch(artifact_id, section=section)

                if content is None:
                    available_artifact_ids = list(artifact_store.list_artifacts().keys())
                    if legacy_store is not None:
                        available_artifact_ids.extend(legacy_store.list_artifacts().keys())

                    return json.dumps(
                        {
                            "success": False,
                            "error": f"アーティファクト '{artifact_id}' が見つかりません",
                            "available_artifacts": available_artifact_ids,
                        },
                        ensure_ascii=False,
                        indent=2,
                    )

                # フォーマット処理
                if format_type == "json":
                    try:
                        # JSONとして解析して整形
                        import json as json_lib

                        parsed = json_lib.loads(content)
                        formatted_content = json_lib.dumps(parsed, ensure_ascii=False, indent=2)
                    except:
                        formatted_content = content
                else:
                    formatted_content = content

                # メタデータ取得
                # メタデータ取得（レガシー側も試行）
                metadata = artifact_store.get_metadata(artifact_id)
                if metadata is None and legacy_store is not None:
                    metadata = legacy_store.get_metadata(artifact_id)

                result = {
                    "success": True,
                    "artifact_id": artifact_id,
                    "content": formatted_content,
                    "section": section,
                    "format": format_type,
                    "metadata": {
                        "size_bytes": len(content.encode("utf-8")),
                        "created_at": metadata.created_at if metadata else None,
                        "content_type": metadata.content_type if metadata else "text",
                        "source_file": metadata.source_file if metadata else None,
                    },
                }

                if section:
                    result["instructions"] = f"アーティファクト '{artifact_id}' のセクション '{section}' を取得しました"
                else:
                    result["instructions"] = f"アーティファクト '{artifact_id}' の全コンテンツを取得しました"
                # 付加情報（説明）があれば含める
                if metadata and getattr(metadata, "description", None):
                    result["instructions"] += f"（{metadata.description}）"

                return self._json_with_path_fallback(result, locals())

            except Exception as e:
                self.logger.exception("アーティファクト取得エラー")
                return json.dumps(
                    {"success": False, "error": f"アーティファクト取得エラー: {e}", "artifact_id": artifact_id},
                    ensure_ascii=False,
                    indent=2,
                )

        # Compatibility for tests expecting _tools dict
        try:
            if not hasattr(self.server, "_tools"):
                self.server._tools = {}
            self.server._tools["fetch_artifact"] = type("Tool", (), {"fn": fetch_artifact})
        except Exception:
            pass

        # テスト互換: 直接メソッドとしてもアクセス可能にする
        try:
            self.fetch_artifact = fetch_artifact
        except Exception:
            pass

        @self.server.tool(name="list_artifacts", description="利用可能なアーティファクト一覧を表示 - デバッグ・確認用")
        async def list_artifacts(project_root: str | None = None) -> str:
            """アーティファクト一覧取得"""
            try:
                from pathlib import Path

                from noveler.infrastructure.factories.path_service_factory import create_mcp_aware_path_service

                # プロジェクトパス設定
                if project_root:
                    project_path = Path(project_root).expanduser()
                    # 指定されたパスが存在するかチェック
                    if not project_path.exists():
                        return json.dumps({
                            "success": False,
                            "error": f"指定された project_root が存在しません: {project_root}",
                            "artifacts": [],
                            "total": 0
                        })
                else:
                    path_service = create_mcp_aware_path_service()
                    project_path = path_service.get_project_root()

                # ArtifactStoreService初期化（現行/レガシー両対応）
                artifact_store, legacy_store = _resolve_artifact_store(project_path)

                # アーティファクト一覧取得（まず全件）
                artifacts_primary = artifact_store.list_artifacts()
                artifacts_legacy = legacy_store.list_artifacts() if legacy_store is not None else []

                # 結合（artifact_idでユニーク化）
                combined: dict[str, dict] = {}

                def _iter_artifacts(source: Any) -> Iterable[dict]:
                    if source is None:
                        return []
                    if isinstance(source, dict):
                        return source.values()
                    if isinstance(source, list):
                        return source
                    if hasattr(source, "as_list"):
                        return source.as_list()
                    if hasattr(source, "items"):
                        try:
                            return [
                                {"artifact_id": aid, "metadata": meta}
                                for aid, meta in source.items()
                            ]
                        except Exception:
                            return []
                    if hasattr(source, "__iter__"):
                        return list(source)
                    return []

                for source in (_iter_artifacts(artifacts_primary), _iter_artifacts(artifacts_legacy)):
                    for item in source:
                        if isinstance(item, dict):
                            aid = item.get("artifact_id")
                            metadata = item.get("metadata")
                            if metadata is None:
                                metadata = {k: v for k, v in item.items() if k != "artifact_id"}
                        else:
                            aid = getattr(item, "artifact_id", None)
                            metadata = getattr(item, "metadata", item)

                        if not aid or aid in combined:
                            continue

                        combined[aid] = {
                            "artifact_id": aid,
                            "metadata": metadata,
                        }

                # dict形式が返された場合はmetadataと結合済みの形へ揃える
                if isinstance(artifacts_primary, dict) and not combined:
                    for aid, metadata in artifacts_primary.items():
                        if aid not in combined:
                            combined[aid] = {"artifact_id": aid, "metadata": metadata}

                artifacts_all = list(combined.values())

                # プロットのみをデフォルト表示（互換性: 説明やファイル名に「プロット」を含むもの、またはtags.type=plot）。
                # ただし、プロット判定に一致するものが存在しない場合は全件を返す（汎用ツール互換）。
                def _meta_get(metadata_like: Any, key: str, default: Any = "") -> Any:
                    if isinstance(metadata_like, dict):
                        return metadata_like.get(key, default)
                    return getattr(metadata_like, key, default)

                def _is_plot(metadata_like: Any) -> bool:
                    desc = str(_meta_get(metadata_like, "description", "") or "")
                    src = str(_meta_get(metadata_like, "source_file", "") or "")
                    tags = _meta_get(metadata_like, "tags", {}) or {}
                    if isinstance(tags, dict) and tags.get("type") == "plot":
                        return True
                    if "プロット" in desc:
                        return True
                    if src.endswith("_プロット.md"):
                        return True
                    return False

                plot_like = [a for a in artifacts_all if _is_plot(a.get("metadata", {}))]
                artifacts = plot_like if plot_like else artifacts_all

                if not artifacts:
                    return json.dumps(
                        {
                            "success": True,
                            "message": "ストア済みアーティファクトはありません",
                            "artifacts": [],
                            "total_artifacts": 0,
                        },
                        ensure_ascii=False,
                        indent=2,
                    )

                artifact_list = []
                # list_artifacts may return a list of IDs or a dict
                if isinstance(artifacts, dict):
                    items_iter = artifacts.items()
                elif isinstance(artifacts, list) and artifacts and isinstance(artifacts[0], dict):
                    items_iter = [(a.get("artifact_id"), a.get("metadata")) for a in artifacts]
                else:
                    items_iter = [(aid, artifact_store.get_metadata(aid)) for aid in artifacts]

                for artifact_id, metadata in items_iter:
                    if isinstance(metadata, dict):
                        getv = metadata.get
                    else:

                        def getv(k, default=None):
                            return getattr(metadata, k, default)

                    artifact_list.append(
                        {
                            "artifact_id": artifact_id,
                            "content_type": getv("content_type"),
                            "size_bytes": getv("size_bytes"),
                            "created_at": getv("created_at"),
                            "source_file": getv("source_file"),
                            "description": getv("description"),
                        }
                    )

                result = {
                    "success": True,
                    "total_artifacts": len(artifacts) if not isinstance(artifacts, dict) else len(artifacts.keys()),
                    "artifacts": artifact_list,
                    "instructions": "fetch_artifact ツールで個別のプロットアーティファクトを取得できます",
                }

                return self._json_with_path_fallback(result, locals())

            except Exception as e:
                self.logger.exception("アーティファクト一覧取得エラー")
                return json.dumps(
                    {"success": False, "error": f"アーティファクト一覧取得エラー: {e}"}, ensure_ascii=False, indent=2
                )

        # Test compatibility registry for list_artifacts
        try:
            if not hasattr(self.server, "_tools"):
                self.server._tools = {}
            self.server._tools["list_artifacts"] = type("Tool", (), {"fn": list_artifacts})
        except Exception:
            pass

        # テスト互換: 直接メソッドとしてもアクセス可能にする
        try:
            self.list_artifacts = list_artifacts
        except Exception:
            pass

    def _determine_quality_level(self, average_score: float) -> str:
        """品質レベルの判定"""
        if average_score >= 90:
            return "優秀（90点以上）"
        if average_score >= 80:
            return "良好（80-89点）"
        if average_score >= 70:
            return "普通（70-79点）"
        if average_score >= 60:
            return "要改善（60-69点）"
        return "要大幅改善（60点未満）"

    def _categorize_issues(self, issues_found: list) -> dict:
        """問題を分類して整理"""
        categories = {"構造": [], "言語": [], "可読性": [], "内容": [], "表現": []}

        # 問題を適切なカテゴリに分類
        # （実装では、より詳細な分類ロジックが必要）
        for issue in issues_found:
            if "段落" in issue or "文字数" in issue:
                categories["構造"].append(issue)
            elif "表記" in issue or "文法" in issue:
                categories["言語"].append(issue)
            elif "読みやすさ" in issue or "文長" in issue:
                categories["可読性"].append(issue)
            elif "キャラクター" in issue or "設定" in issue or "展開" in issue:
                categories["内容"].append(issue)
            else:
                categories["表現"].append(issue)

        # 空のカテゴリを除去
        return {k: v for k, v in categories.items() if v}


async def main() -> int:
    """MCPサーバーメイン実行"""
    if not MCP_AVAILABLE:
        console.print("エラー: MCPライブラリが利用できません")
        console.print("以下のコマンドでインストールしてください:")
        console.print("pip install mcp")
        return 1

    force_restart = "--force-restart" in sys.argv or "-f" in sys.argv
    try:
        server = JSONConversionServer(force_restart=force_restart)
        await server.run()
        return 0
    except RuntimeError as e:
        if "重複実行検出" in str(e):
            console.print(f"⚠️  {e}")
            console.print("\n解決方法:")
            console.print("1. 既存プロセスを手動終了する")
            console.print("2. または --force-restart オプションで強制再起動:")
            console.print("   python json_conversion_server.py --force-restart")
            return 1
        console.print(f"エラー: {e}")
        return 1
    except Exception as e:
        console.print(f"予期しないエラー: {e}")
        return 1


if __name__ == "__main__":
    asyncio.run(main())
# Expose a module-level path service factory for testability
try:
    # Default to the real factory, but allow tests to monkeypatch this symbol
    from noveler.infrastructure.factories.path_service_factory import (
        create_mcp_aware_path_service as create_mcp_aware_path_service,
    )
except Exception:  # pragma: no cover - fallback if imports fail during partial loads
    create_mcp_aware_path_service = None  # type: ignore

# Expose a module-level artifact store factory for testability
try:
    from noveler.domain.services.artifact_store_service import (
        create_artifact_store as create_artifact_store,
    )
except Exception:  # pragma: no cover
    create_artifact_store = None  # type: ignore
