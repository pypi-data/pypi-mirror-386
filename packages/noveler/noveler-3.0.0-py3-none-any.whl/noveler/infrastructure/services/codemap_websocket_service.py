"""Infrastructure.services.codemap_websocket_service
Where: Infrastructure service streaming codemap updates via websockets.
What: Pushes codemap events to clients in real time.
Why: Provides immediate feedback when codemap data changes.
"""

from noveler.presentation.shared.shared_utilities import console


"CODEMAP WebSocketサービス\n\nPhase 3: リアルタイム更新通知機能\nWebSocket経由でCODEMAP更新をリアルタイム配信。\n\n設計原則:\n    - イベント駆動アーキテクチャ\n    - 購読/配信パターン\n    - 自動再接続機能\n"
import asyncio
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from noveler.infrastructure.logging.unified_logger import get_logger


class EventType(Enum):
    """イベントタイプ定義"""

    FILE_CHANGED = "file_changed"
    DEPENDENCY_UPDATED = "dependency_updated"
    VIOLATION_DETECTED = "violation_detected"
    CACHE_INVALIDATED = "cache_invalidated"
    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_COMPLETED = "analysis_completed"
    ERROR_OCCURRED = "error_occurred"


@dataclass
class CodeMapEvent:
    """CODEMAPイベント"""

    type: EventType
    timestamp: datetime
    data: dict[str, Any]
    source: str = "codemap_service"

    def to_json(self) -> str:
        """JSON形式に変換"""
        return json.dumps(
            {"type": self.type.value, "timestamp": self.timestamp.isoformat(), "data": self.data, "source": self.source}
        )


class CodeMapWebSocketService:
    """CODEMAP WebSocketサービス

    責務:
        - リアルタイムイベント配信
        - クライアント接続管理
        - ファイル監視統合
        - 自動再接続サポート

    Note: 実際のWebSocket実装はaiohttp等のフレームワークと
          組み合わせて使用することを想定
    """

    def __init__(self, project_root: Path) -> None:
        """初期化

        Args:
            project_root: プロジェクトルート
        """
        self.project_root = project_root
        self.logger = get_logger(__name__)
        self._subscribers: dict[str, asyncio.Queue] = {}
        self._event_history: list[CodeMapEvent] = []
        self._max_history = 100
        self._file_watcher_task = None
        self._analysis_task = None

    async def start(self) -> None:
        """サービスを開始"""
        console.print("WebSocket service starting...")
        self._file_watcher_task = asyncio.create_task(self._watch_files())
        self._analysis_task = asyncio.create_task(self._periodic_analysis())
        console.print("WebSocket service started")

    async def stop(self) -> None:
        """サービスを停止"""
        console.print("WebSocket service stopping...")
        if self._file_watcher_task:
            self._file_watcher_task.cancel()
        if self._analysis_task:
            self._analysis_task.cancel()
        await self._broadcast_event(
            CodeMapEvent(
                type=EventType.ERROR_OCCURRED,
                timestamp=datetime.now(timezone.utc),
                data={"message": "Service shutting down"},
            )
        )
        self._subscribers.clear()
        console.print("WebSocket service stopped")

    async def subscribe(self, client_id: str) -> asyncio.Queue:
        """クライアントを購読登録"""
        if client_id in self._subscribers:
            console.print(f"Client {client_id} already subscribed")
            return self._subscribers[client_id]
        queue = asyncio.Queue(maxsize=100)
        self._subscribers[client_id] = queue
        console.print(f"Client {client_id} subscribed")
        await self._send_initial_state(client_id)
        return queue

    async def unsubscribe(self, client_id: str) -> None:
        """クライアントの購読を解除"""
        if client_id in self._subscribers:
            del self._subscribers[client_id]
            console.print(f"Client {client_id} unsubscribed")

    async def _send_initial_state(self, client_id: str) -> None:
        """初期状態をクライアントに送信"""
        # Intentional lazy import: avoid heavy cache service at module import time
        # noqa: PLC0415
        from noveler.infrastructure.services.codemap_cache_service import get_codemap_cache_service

        cache_service = get_codemap_cache_service()
        stats = cache_service.get_statistics()
        event = CodeMapEvent(
            type=EventType.DEPENDENCY_UPDATED,
            timestamp=datetime.now(timezone.utc),
            data={"statistics": stats, "cache_status": "ready", "history_size": len(self._event_history)},
        )
        await self._send_to_client(client_id, event)

    async def _send_to_client(self, client_id: str, event: CodeMapEvent) -> None:
        """特定クライアントにイベントを送信"""
        if client_id in self._subscribers:
            queue = self._subscribers[client_id]
            try:
                await asyncio.wait_for(queue.put(event), timeout=1.0)
            except asyncio.TimeoutError:
                console.print(f"Failed to send event to {client_id}: queue full")
                try:
                    queue.get_nowait()
                    await queue.put(event)
                except asyncio.QueueEmpty:
                    pass

    async def _broadcast_event(self, event: CodeMapEvent) -> None:
        """全クライアントにイベントをブロードキャスト"""
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        tasks = [self._send_to_client(client_id, event) for client_id in self._subscribers]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _watch_files(self) -> None:
        """ファイル変更を監視"""
        try:
            last_mtimes = {}
            while True:
                changed_files = []
                for py_file in self.project_root.rglob("*.py"):
                    if "__pycache__" in str(py_file):
                        continue
                    try:
                        mtime = py_file.stat().st_mtime
                        if py_file not in last_mtimes:
                            last_mtimes[py_file] = mtime
                        elif last_mtimes[py_file] != mtime:
                            changed_files.append(py_file)
                            last_mtimes[py_file] = mtime
                    except FileNotFoundError:
                        if py_file in last_mtimes:
                            del last_mtimes[py_file]
                            changed_files.append(py_file)
                if changed_files:
                    await self._handle_file_changes(changed_files)
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            console.print("File watcher stopped")
            raise
        except Exception as e:
            self.logger.exception("File watcher error")
            await self._broadcast_event(
                CodeMapEvent(
                    type=EventType.ERROR_OCCURRED,
                    timestamp=datetime.now(timezone.utc),
                    data={"error": str(e), "component": "file_watcher"},
                )
            )

    async def _handle_file_changes(self, changed_files: list[Path]) -> None:
        """ファイル変更を処理"""
        console.print(f"Detected changes in {len(changed_files)} files")
        await self._broadcast_event(
            CodeMapEvent(
                type=EventType.FILE_CHANGED,
                timestamp=datetime.now(timezone.utc),
                data={"files": [str(f) for f in changed_files], "count": len(changed_files)},
            )
        )
        asyncio.create_task(self._analyze_changes(changed_files))

    async def _analyze_changes(self, changed_files: list[Path]) -> None:
        """変更ファイルを解析"""
        await self._broadcast_event(
            CodeMapEvent(
                type=EventType.ANALYSIS_STARTED,
                timestamp=datetime.now(timezone.utc),
                data={"files": [str(f) for f in changed_files], "type": "incremental"},
            )
        )
        try:
            # Intentional lazy import to defer parallel processor init
            # noqa: PLC0415
            from noveler.infrastructure.services.codemap_parallel_processor import get_parallel_processor

            processor = get_parallel_processor()
            result = processor.analyze_parallel(changed_files, "full")
            violations: Any = result["dependency_map"]["dependency_issues"].get("layer_violations", [])
            if violations:
                await self._broadcast_event(
                    CodeMapEvent(
                        type=EventType.VIOLATION_DETECTED,
                        timestamp=datetime.now(timezone.utc),
                        data={"violations": violations, "count": len(violations)},
                    )
                )
            await self._broadcast_event(
                CodeMapEvent(
                    type=EventType.DEPENDENCY_UPDATED,
                    timestamp=datetime.now(timezone.utc),
                    data={
                        "modules_updated": len(result["dependency_map"]["core_dependencies"]),
                        "statistics": result["dependency_map"]["dependency_statistics"],
                        "performance": result["performance"],
                    },
                )
            )
            await self._broadcast_event(
                CodeMapEvent(
                    type=EventType.CACHE_INVALIDATED,
                    timestamp=datetime.now(timezone.utc),
                    data={"reason": "file_changes", "affected_files": [str(f) for f in changed_files]},
                )
            )
        except Exception as e:
            self.logger.exception("Analysis error")
            await self._broadcast_event(
                CodeMapEvent(
                    type=EventType.ERROR_OCCURRED,
                    timestamp=datetime.now(timezone.utc),
                    data={"error": str(e), "component": "analyzer"},
                )
            )
        finally:
            await self._broadcast_event(
                CodeMapEvent(
                    type=EventType.ANALYSIS_COMPLETED,
                    timestamp=datetime.now(timezone.utc),
                    data={"type": "incremental"},
                )
            )

    async def _periodic_analysis(self) -> None:
        """定期的な全体解析"""
        try:
            while True:
                await asyncio.sleep(3600)
                console.print("Starting periodic full analysis")
                await self._broadcast_event(
                    CodeMapEvent(
                        type=EventType.ANALYSIS_STARTED,
                        timestamp=datetime.now(timezone.utc),
                        data={"type": "full", "scheduled": True},
                    )
                )
                # Intentional lazy import for scheduled full analysis
                # noqa: PLC0415
                from noveler.infrastructure.services.codemap_parallel_processor import get_parallel_processor

                processor = get_parallel_processor()
                py_files = [f for f in self.project_root.rglob("*.py") if "__pycache__" not in str(f)]
                result = processor.analyze_parallel(py_files, "full")
                await self._broadcast_event(
                    CodeMapEvent(
                        type=EventType.DEPENDENCY_UPDATED,
                        timestamp=datetime.now(timezone.utc),
                        data={
                            "type": "full",
                            "modules_analyzed": len(result["dependency_map"]["core_dependencies"]),
                            "statistics": result["dependency_map"]["dependency_statistics"],
                            "quality_metrics": result.get("quality_metrics", {}),
                        },
                    )
                )
                await self._broadcast_event(
                    CodeMapEvent(
                        type=EventType.ANALYSIS_COMPLETED,
                        timestamp=datetime.now(timezone.utc),
                        data={"type": "full", "scheduled": True},
                    )
                )
        except asyncio.CancelledError:
            console.print("Periodic analysis stopped")
            raise
        except Exception:
            self.logger.exception("Periodic analysis error")

    def get_event_history(self, limit: int = 10) -> list[CodeMapEvent]:
        """イベント履歴を取得

        Args:
            limit: 取得する最大件数

        Returns:
            イベントリスト
        """
        return self._event_history[-limit:]


class CodeMapWebSocketClient:
    """WebSocketクライアントの例"""

    def __init__(self, client_id: str, service: CodeMapWebSocketService) -> None:
        self.client_id = client_id
        self.service = service
        self.queue: asyncio.Queue | None = None
        self.logger = get_logger(f"{__name__}.client.{client_id}")

    async def connect(self) -> None:
        """サービスに接続"""
        self.queue = await self.service.subscribe(self.client_id)
        console.print("Connected to WebSocket service")

    async def disconnect(self) -> None:
        """サービスから切断"""
        await self.service.unsubscribe(self.client_id)
        console.print("Disconnected from WebSocket service")

    async def listen(self, callback: Callable[[CodeMapEvent], None] | None = None) -> None:
        """イベントをリッスン"""
        if not self.queue:
            msg = "Not connected"
            raise RuntimeError(msg)
        try:
            while True:
                event = await self.queue.get()
                if callback:
                    await callback(event)
                else:
                    console.print(f"Received event: {event.type.value}")
        except asyncio.CancelledError:
            console.print("Listener stopped")
            raise


def get_websocket_service() -> CodeMapWebSocketService:
    """WebSocketサービスのインスタンスを取得"""
    try:
        # Intentional lazy import to avoid presentation dependency at import time
        # noqa: PLC0415
        from noveler.presentation.shared.shared_utilities import get_common_path_service

        path_service = get_common_path_service()
        project_root = path_service.get_project_root()
    except ImportError:
        import os
        from pathlib import Path

        project_root = Path(os.environ.get("PROJECT_ROOT", Path.cwd()))
    return CodeMapWebSocketService(project_root)
