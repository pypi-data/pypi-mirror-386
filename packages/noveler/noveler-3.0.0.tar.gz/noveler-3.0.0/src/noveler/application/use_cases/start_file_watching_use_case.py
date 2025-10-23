#!/usr/bin/env python3

"""Application.use_cases.start_file_watching_use_case
Where: Application use case that starts file watching workflows.
What: Sets up watchers, registers callbacks, and reports status for live monitoring.
Why: Gives callers a simple entry point to enable file watching without manual wiring.
"""

from __future__ import annotations

from typing import Any



import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

try:
    from watchdog.events import FileSystemEvent, FileSystemEventHandler
    from watchdog.observers import Observer

    WATCHDOG_AVAILABLE = True
except ImportError:
    FileSystemEvent = None
    WATCHDOG_AVAILABLE = False

from noveler.application.use_cases.export_errors_for_claude_use_case import (
    ExportErrorsRequest,
)
from noveler.domain.entities.file_change_event import (
    ChangeType,
    FileChangeEvent,
    FilePattern,
    WatchMode,
)
from noveler.domain.services.claude_code_format_service import ClaudeCodeFormatService
from noveler.domain.value_objects.error_export_format import ErrorExportFormat, ExportFormatType
from noveler.domain.value_objects.file_path import FilePath

# DDD準拠: Application→Presentation違反を遅延初期化で回避


@dataclass
class FileWatchRequest:
    """ファイル監視リクエスト"""

    watch_directory: Path
    watch_mode: WatchMode = field(default_factory=WatchMode.continuous)
    file_pattern: FilePattern | None = None
    debounce_interval: float = 0.5  # 秒
    verbose: bool = False
    auto_export: bool = True


@dataclass
class FileWatchResponse:
    """ファイル監視レスポンス"""

    success: bool
    session_id: str
    watched_directory: Path | None = None
    events_processed: int = 0
    exports_triggered: int = 0
    error_message: str | None = None
    is_watching: bool = False


class FileWatchingService:
    """ファイル監視サービス(watchdog統合)"""

    def __init__(self) -> None:
        self.is_watching = False
        self.watch_thread: threading.Thread | None = None
        self.pending_events: dict[str, FileChangeEvent] = {}
        self.debounce_timers: dict[str, threading.Timer] = {}

    def start_watching(
        self, directory: Path, file_pattern: FilePattern, on_file_change: callable, debounce_interval: float = 0.5
    ) -> bool:
        """ファイル監視開始

        Args:
            directory: 監視ディレクトリ
            file_pattern: ファイルパターン
            on_file_change: ファイル変更時のコールバック
            debounce_interval: デバウンス間隔(秒)

        Returns:
            監視開始成功時True
        """
        try:
            if not WATCHDOG_AVAILABLE:
                msg = "watchdog module not available"
                raise ImportError(msg)

            class ChangeHandler(FileSystemEventHandler):
                def __init__(self, service: FileWatchingService) -> None:
                    self.service = service

                def on_modified(self, event: FileSystemEvent) -> None:
                    if not event.is_directory:
                        self.service._handle_file_event(
                            Path(event.src_path), ChangeType.MODIFIED, file_pattern, on_file_change, debounce_interval
                        )

                def on_created(self, event: FileSystemEvent) -> None:
                    if not event.is_directory:
                        self.service._handle_file_event(
                            Path(event.src_path), ChangeType.CREATED, file_pattern, on_file_change, debounce_interval
                        )

            self.observer = Observer()
            self.event_handler = ChangeHandler(self)
            self.observer.schedule(self.event_handler, str(directory), recursive=True)
            self.observer.start()
            self.is_watching = True

            # ログ出力（logger_serviceが利用可能な場合）
            return True

        except ImportError:
            # watchdogライブラリ不足の警告
            return False
        except Exception:
            # エラーログ（必要に応じて外部でログ出力）
            return False

    def stop_watching(self) -> None:
        """ファイル監視停止"""
        if hasattr(self, "observer") and self.observer.is_alive():
            self.observer.stop()
            self.observer.join()

        # 残っているタイマーをキャンセル
        for timer in self.debounce_timers.values():
            timer.cancel()

        self.is_watching = False
        # ファイル監視停止（外部でログ出力）

    def _handle_file_event(
        self,
        file_path: Path,
        change_type: ChangeType,
        file_pattern: FilePattern,
        on_file_change: callable,
        debounce_interval: float,
    ) -> None:
        """ファイルイベント処理(デバウンス付き)"""
        file_key = str(file_path)

        # 既存のタイマーをキャンセル
        if file_key in self.debounce_timers:
            self.debounce_timers[file_key].cancel()

        # 新しいイベントを作成
        event = FileChangeEvent(file_path=str(file_path), change_type=change_type.value)

        # 処理すべきファイルかチェック
        if not event.should_process(file_pattern):
            return

        # デバウンスタイマーを設定
        timer = threading.Timer(debounce_interval, lambda: self._process_debounced_event(event, on_file_change))

        self.debounce_timers[file_key] = timer
        self.pending_events[file_key] = event
        timer.start()

    def _process_debounced_event(self, event: FileChangeEvent, on_file_change: callable) -> None:
        """デバウンス後のイベント処理"""
        file_key = str(event.file_path)

        try:
            # コールバック実行
            on_file_change(event)

            # クリーンアップ
            if file_key in self.pending_events:
                del self.pending_events[file_key]
            if file_key in self.debounce_timers:
                del self.debounce_timers[file_key]

        except Exception:
            # エラーログ（必要に応じて外部でログ出力）
            pass


class StartFileWatchingUseCase:
    """ファイル監視開始ユースケース

    SPEC-CLAUDE-003に基づく実装:
    1. ファイル監視開始
    2. ファイル変更時の品質チェック
    3. Claude向け自動エクスポート
    """

    def __init__(self, claude_format_service: ClaudeCodeFormatService = None, path_service=None) -> None:
        """Initialize file watching use case

        Args:
            claude_format_service: Claude format service for export functionality
            path_service: Path service for directory management
        """
        self.claude_format_service = claude_format_service
        self.path_service = path_service

        # Initialize export use case if service is available
        if claude_format_service:
            from noveler.application.use_cases.export_errors_for_claude_use_case import ExportErrorsForClaudeUseCase

            self.export_use_case = ExportErrorsForClaudeUseCase(claude_format_service)
        else:
            self.export_use_case = None

        self.file_watching_service = FileWatchingService()
        self.events_processed = 0
        self.exports_triggered = 0

    def execute(self, request: FileWatchRequest) -> FileWatchResponse:
        """ファイル監視開始実行

        Args:
            request: ファイル監視リクエスト

        Returns:
            ファイル監視レスポンス
        """
        session_id = f"file-watch-{uuid.uuid4()}"

        try:
            # デフォルトパターンの設定
            file_pattern = request.file_pattern or FilePattern.python_files()

            if hasattr(self, "_get_console"):
                console = self._get_console()
                console.print("[cyan]🔄 ファイル監視を開始します...[/cyan]")
                console.print(f"[blue]📁 監視ディレクトリ: {request.watch_directory}[/blue]")
                console.print(f"[blue]🎯 監視パターン: {file_pattern.include_patterns}[/blue]")
                console.print(f"[blue]🚫 除外パターン: {file_pattern.exclude_patterns}[/blue]")
                console.print(f"[blue]⏱️ デバウンス間隔: {request.debounce_interval}秒[/blue]")
                console.print(f"[blue]🤖 自動エクスポート: {'有効' if request.auto_export else '無効'}[/blue]")

            # ファイル変更時のコールバック関数
            def on_file_change(event: FileChangeEvent) -> None:
                self._handle_file_change(event, request.auto_export, request.verbose)

            # ファイル監視開始
            success = self.file_watching_service.start_watching(
                directory=request.watch_directory,
                file_pattern=file_pattern,
                on_file_change=on_file_change,
                debounce_interval=request.debounce_interval,
            )

            if not success:
                return FileWatchResponse(
                    success=False, session_id=session_id, error_message="ファイル監視の開始に失敗しました"
                )

            if request.watch_mode.mode == "oneshot":
                # ワンショットモードの場合は短時間監視後停止
                if hasattr(self, "_get_console"):
                    console = self._get_console()
                    console.print("[yellow]⏰ ワンショットモード: 10秒間監視...[/yellow]")
                time.sleep(10)
                self.file_watching_service.stop_watching()
                if hasattr(self, "_get_console"):
                    console.print("[green]✅ ワンショット監視完了[/green]")
            else:
                # 継続モードの場合は監視継続
                if hasattr(self, "_get_console"):
                    console = self._get_console()
                    console.print("[cyan]🔄 継続監視モード: Ctrl+Cで停止[/cyan]")
                    console.print("[cyan]ファイル保存を監視中...[/cyan]")

                try:
                    while self.file_watching_service.is_watching:
                        time.sleep(1)
                except KeyboardInterrupt:
                    if hasattr(self, "_get_console"):
                        console = self._get_console()
                        console.print("\n[yellow]⚠️ ユーザーによる監視停止[/yellow]")
                    self.file_watching_service.stop_watching()

            return FileWatchResponse(
                success=True,
                session_id=session_id,
                watched_directory=request.watch_directory,
                events_processed=self.events_processed,
                exports_triggered=self.exports_triggered,
                is_watching=self.file_watching_service.is_watching,
            )

        except Exception as e:
            return FileWatchResponse(success=False, session_id=session_id, error_message=f"ファイル監視エラー: {e!s}")

    def _handle_file_change(self, event: FileChangeEvent, auto_export: bool, verbose: bool) -> None:
        """Handle file change events with quality checking and export

        Args:
            event: File change event to process
            auto_export: Whether to automatically export errors to Claude format
            verbose: Whether to show detailed logging output
        """
        try:
            event.start_processing()
            self.events_processed += 1

            if verbose:
                self._get_console().print(f"📝 File change detected: {event.file_path}")
                self._get_console().print(f"🔧 Change type: {event.change_type}")
            else:
                self._get_console().print(f"📝 {Path(event.file_path).name} was modified")

            # Ruffによる自動修正を最初に実行
            auto_format_result = self._apply_auto_formatting(event.file_path, verbose)
            if auto_format_result["fixes_applied"]:
                self._get_console().print(f"🔧 Auto-fixed: {', '.join(auto_format_result['fixes_applied'])}")

            if auto_export:
                self._get_console().print("🤖 Running Claude error check...")

                format_config: dict[str, Any] = ErrorExportFormat(
                    format_type=ExportFormatType.JSON,
                    structure_version="1.0",
                    max_errors_per_file=50,
                    include_suggestions=True,
                    priority_filter="all",
                )

                # B20準拠: パスサービス経由でtemp pathを取得
                temp_path = self.path_service.get_temp_dir() if self.path_service else Path.cwd() / "temp"

                export_request = ExportErrorsRequest(
                    target_file=FilePath(str(Path(event.file_path))),
                    output_path=FilePath(str(temp_path / f"claude_export_auto_{int(time.time())}.json")),
                    format_config=format_config,
                    priority_filter=None,
                    include_suggestions=True,
                )

                if self.export_use_case is None:
                    self._get_console().print("⚠️ Export use case not initialized (skipping)")
                    event.complete_processing(trigger_export=False)
                    return

                response = self.export_use_case.execute(export_request)

                if response.success:
                    if response.error_count > 0:
                        self._get_console().print(f"⚠️ Detected {response.error_count} errors")
                        self._get_console().print(f"📂 Export: {response.output_path}")
                        event.complete_processing(trigger_export=True)
                        self.exports_triggered += 1
                    else:
                        self._get_console().print("✅ No errors found")
                        event.complete_processing(trigger_export=False)
                else:
                    self._get_console().print(f"❌ Error check failed: {response.error_message}")
                    event.fail_processing(response.error_message or "Unknown error")
            else:
                event.complete_processing(trigger_export=False)
                self._get_console().print("ℹ️ Auto-export is disabled")

        except Exception as e:
            self._get_console().print(f"❌ File change processing error: {e}")
            event.fail_processing(str(e))

    def _apply_auto_formatting(self, file_path: str, verbose: bool) -> dict[str, Any]:
        """Ruffによる自動修正を適用

        Args:
            file_path: 修正対象ファイルパス
            verbose: 詳細ログ出力フラグ

        Returns:
            修正結果の詳細情報
        """
        try:
            from noveler.infrastructure.tools.ruff_auto_formatter import RuffAutoFormatter

            formatter = RuffAutoFormatter()
            result = formatter.format_file_on_save(file_path)

            if verbose and result["errors"]:
                for error in result["errors"]:
                    self._get_console().print(f"⚠️ Auto-format warning: {error}")

            return result

        except ImportError:
            self._get_console().print("⚠️ RuffAutoFormatter not available")
            return {"fixes_applied": [], "errors": ["RuffAutoFormatter not found"]}
        except Exception as e:
            self._get_console().print(f"⚠️ Auto-format error: {e}")
            return {"fixes_applied": [], "errors": [str(e)]}

    def _get_console(self) -> Any:
        """DDD準拠: Application→Presentation違反を遅延初期化で回避"""
        from noveler.presentation.shared.shared_utilities import console

        return console

    def stop(self) -> None:
        """Stop file monitoring"""
        self.file_watching_service.stop_watching()
