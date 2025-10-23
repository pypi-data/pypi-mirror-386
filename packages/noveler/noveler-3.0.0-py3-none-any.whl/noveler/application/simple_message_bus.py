"""Simplified asynchronous message bus for application-level scenarios."""

from __future__ import annotations

import asyncio
import contextlib
import inspect
from random import SystemRandom
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from noveler.infrastructure.logging.unified_logger import get_logger

from noveler.domain.events.base import DomainEvent, SystemEvent
from noveler.application.outbox import OutboxEntry, OutboxRepository
from noveler.application.idempotency import IdempotencyStore


JITTER_RNG = SystemRandom()

logger = get_logger(__name__)


@dataclass
class GenericEvent(SystemEvent):
    """Generic event used when only a name/payload pair is available."""

    event_name: str = "generic"
    payload: dict[str, Any] = field(default_factory=dict)


CommandHandler = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]
EventHandler = Callable[[DomainEvent], Awaitable[None]]


@dataclass
class BusConfig:
    """Configuration for retry behaviour and backoff within the bus."""

    max_retries: int = 3
    backoff_base_sec: float = 0.05
    backoff_max_sec: float = 0.5
    jitter_sec: float = 0.05
    dlq_max_attempts: int = 5  # DLQ移行までの最大試行回数

@dataclass
class BusMetrics:
    """MessageBusメトリクス情報"""

    command_count: int = 0
    event_count: int = 0
    failed_commands: int = 0
    failed_events: int = 0
    command_durations: list[float] = field(default_factory=list)
    event_durations: list[float] = field(default_factory=list)

    def get_command_stats(self) -> dict[str, float]:
        """コマンド処理統計の取得"""
        if not self.command_durations:
            return {"count": 0, "avg_ms": 0.0, "p50_ms": 0.0, "p95_ms": 0.0, "failure_rate": 0.0}

        durations_ms = [d * 1000 for d in self.command_durations]  # ミリ秒変換
        durations_ms.sort()

        count = len(durations_ms)
        avg_ms = sum(durations_ms) / count
        p50_ms = durations_ms[int(count * 0.5)]
        p95_ms = durations_ms[int(count * 0.95)] if count > 20 else durations_ms[-1]
        failure_rate = self.failed_commands / self.command_count if self.command_count > 0 else 0.0

        return {
            "count": self.command_count,
            "avg_ms": avg_ms,
            "p50_ms": p50_ms,
            "p95_ms": p95_ms,
            "failure_rate": failure_rate
        }

    def get_event_stats(self) -> dict[str, float]:
        """イベント処理統計の取得"""
        if not self.event_durations:
            return {"count": 0, "avg_ms": 0.0, "p50_ms": 0.0, "p95_ms": 0.0, "failure_rate": 0.0}

        durations_ms = [d * 1000 for d in self.event_durations]  # ミリ秒変換
        durations_ms.sort()

        count = len(durations_ms)
        avg_ms = sum(durations_ms) / count
        p50_ms = durations_ms[int(count * 0.5)]
        p95_ms = durations_ms[int(count * 0.95)] if count > 20 else durations_ms[-1]
        failure_rate = self.failed_events / self.event_count if self.event_count > 0 else 0.0

        return {
            "count": self.event_count,
            "avg_ms": avg_ms,
            "p50_ms": p50_ms,
            "p95_ms": p95_ms,
            "failure_rate": failure_rate
        }

    def reset(self) -> None:
        """メトリクスをリセット（定期レポート後に使用）"""
        self.command_count = 0
        self.event_count = 0
        self.failed_commands = 0
        self.failed_events = 0
        # 履歴は最新100件程度に制限
        self.command_durations = self.command_durations[-100:]
        self.event_durations = self.event_durations[-100:]


@dataclass
class MessageBus:
    """Minimal asynchronous message bus keyed by string commands/events."""

    command_handlers: dict[str, CommandHandler] = field(default_factory=dict)
    event_handlers: dict[str, list[EventHandler]] = field(default_factory=dict)
    processed_events: list[DomainEvent] = field(default_factory=list)
    config: BusConfig = field(default_factory=BusConfig)
    uow_factory: Optional[Callable[[], Any]] = None
    outbox_repo: Optional[OutboxRepository] = None
    idempotency_store: Optional[IdempotencyStore] = None
    dispatch_inline: bool = True
    metrics: BusMetrics = field(default_factory=BusMetrics)

    async def handle_command(self, name: str, data: dict[str, Any]) -> dict[str, Any]:
        """Execute a command handler and manage unit-of-work boundaries."""
        import time
        start_time = time.perf_counter()

        if name not in self.command_handlers:
            self.metrics.command_count += 1
            self.metrics.failed_commands += 1
            return {"success": False, "error": f"Unknown command: {name}"}

        uow = self.uow_factory() if self.uow_factory else None
        if uow:
            try:
                uow.begin()
            except Exception:
                self.metrics.command_count += 1
                self.metrics.failed_commands += 1
                return {"success": False, "error": "UoW begin failed"}

        try:
            handler = self.command_handlers[name]
            if _accepts_kwarg(handler, "uow"):
                result = await handler(data, uow=uow)
            else:
                result = await handler(data)

            if uow:
                try:
                    events_to_emit = uow.get_events()
                    uow.commit()
                except Exception as commit_err:
                    with contextlib.suppress(Exception):
                        uow.rollback()
                    self.metrics.command_count += 1
                    self.metrics.failed_commands += 1
                    raise commit_err

                # commit後にイベント発行（Outbox優先）
                for ename, payload in events_to_emit:
                    if self.outbox_repo:
                        temp_event = GenericEvent(event_name=ename, payload=payload)
                        entry = OutboxEntry(
                            id=temp_event.event_id,
                            name=ename,
                            payload=payload,
                            created_at=datetime.utcnow(),
                        )
                        self.outbox_repo.add(entry)
                    else:
                        await self.emit(ename, payload)
                uow.clear_events()

                # Outboxを同期フラッシュ（テスト/小規模用途）
                if self.outbox_repo and self.dispatch_inline:
                    with contextlib.suppress(Exception):
                        await self.flush_outbox()

            # 成功時のメトリクス記録
            duration = time.perf_counter() - start_time
            self.metrics.command_count += 1
            self.metrics.command_durations.append(duration)
            return result
        except Exception as exc:
            if uow:
                with contextlib.suppress(Exception):
                    uow.rollback()
            # 失敗時のメトリクス記録
            duration = time.perf_counter() - start_time
            self.metrics.command_count += 1
            self.metrics.failed_commands += 1
            self.metrics.command_durations.append(duration)
            raise exc

    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event, enforcing idempotency when configured."""
        import time
        start_time = time.perf_counter()

        try:
            # べき等: 処理済みイベントはスキップ
            if self.idempotency_store and hasattr(event, "event_id"):
                if self.idempotency_store.was_processed(event.event_id):
                    return
            key = getattr(event, "event_name", None) or event.__class__.__name__
            handlers = self.event_handlers.get(key, [])
            for handler in handlers:
                try:
                    await _run_with_retry(lambda: _invoke_handler(handler, event), self.config)
                except Exception:
                    logger.error(
                        "Event handler failed for %s", type(event).__name__, exc_info=True
                    )
                    self.metrics.failed_events += 1
            self.processed_events.append(event)
            if self.idempotency_store and hasattr(event, "event_id"):
                self.idempotency_store.mark_processed(event.event_id)

            # 成功時のメトリクス記録
            duration = time.perf_counter() - start_time
            self.metrics.event_count += 1
            self.metrics.event_durations.append(duration)
        except Exception:
            # 失敗時のメトリクス記録
            duration = time.perf_counter() - start_time
            self.metrics.event_count += 1
            self.metrics.failed_events += 1
            self.metrics.event_durations.append(duration)
            raise

    async def _handle_event(self, event: DomainEvent) -> None:
        """Compatibility shim for legacy tests expecting a private handler."""
        await self.publish(event)

    async def emit(self, name: str, payload: dict[str, Any] | None = None) -> None:
        """Convenience method that emits a ``GenericEvent`` by name."""
        await self.publish(GenericEvent(event_name=name, payload=payload or {}))

    async def flush_outbox(self, limit: int = 100) -> int:
        """Dispatch pending events stored in the outbox repository."""
        if not self.outbox_repo:
            return 0
        count = 0
        pending = self.outbox_repo.load_pending(limit)
        for e in pending:
            try:
                # Outboxからの再構築時は試行回数をチェック
                storage_key = getattr(e, "storage_key", e.id)
                if e.attempts >= max(1, self.config.dlq_max_attempts - 1):
                    # DLQに移動して監視ログ出力
                    self.outbox_repo.move_to_dlq(storage_key)

                    logger.warning(
                        f"Event {e.id} ({e.name}) moved to DLQ after {e.attempts} attempts. Last error: {e.last_error}"
                    )
                    count += 1
                    continue

                # OutboxからGenericEventを再構築（event_idも維持）
                ge = GenericEvent(event_name=e.name, payload=e.payload, event_id=e.id)  # type: ignore[arg-type]
                await self.publish(ge)
                self.outbox_repo.mark_dispatched(storage_key)
                count += 1
            except Exception as exc:
                # 失敗時は試行回数を増やして次回リトライ対象にする
                error_msg = str(exc)
                self.outbox_repo.increment_attempts(storage_key, error_msg)
                logger.error(
                    f"Event {e.id} ({e.name}) dispatch failed (attempt {e.attempts + 1}): {error_msg}"
                )
                continue
        return count

    async def start_background_flusher(self, interval_seconds: float = 30.0) -> None:
        """Outbox背景フラッシュタスクを開始（非同期ディスパッチ）

        Args:
            interval_seconds: フラッシュ間隔（秒）

        Note:
            テスト時は環境変数 NOVELER_DISABLE_BACKGROUND_FLUSH=1 で無効化
        """
        import os
        if os.getenv("NOVELER_DISABLE_BACKGROUND_FLUSH", "0") == "1":
            return

        if not self.outbox_repo:
            return

        import asyncio

        async def background_flush_loop():
            """背景フラッシュループ"""
            while True:
                try:
                    await asyncio.sleep(interval_seconds)
                    if self.outbox_repo:
                        flushed_count = await self.flush_outbox()
                        if flushed_count > 0:
                            # ログ出力（Domain層ではないのでlogging使用可能）

                            logger.info(
                                f"Background flush dispatched {flushed_count} events"
                            )
                except Exception as e:
                    # エラーが発生してもループを継続
                    logger.error(f"Background flush error: {e}")

        # 背景タスクとして実行
        asyncio.create_task(background_flush_loop())

    def stop_background_flusher(self) -> None:
        """背景フラッシュタスクを停止（将来実装）

        Note:
            現在の実装では背景タスクの明示的停止は未実装
            プロセス終了時に自動的に停止される
        """
        # TODO: 背景タスクの参照を保持し、明示的にキャンセルする機能を追加
        pass

    async def get_dlq_stats(self) -> dict[str, Any]:
        """DLQ統計情報の取得（監視用）

        Returns:
            DLQエントリ数、最古エラー日時、エラー種別統計等
        """
        if not self.outbox_repo:
            return {"error": "No outbox repository configured"}

        try:
            dlq_entries = self.outbox_repo.load_dlq_entries(limit=1000)  # 統計用に多めに取得

            if not dlq_entries:
                return {"total_count": 0, "oldest_error": None, "error_types": {}}

            # エラー種別の集計
            error_types: dict[str, int] = {}
            oldest_error = None

            for entry in dlq_entries:
                if entry.last_error:
                    # エラーメッセージの先頭50文字で分類
                    error_key = entry.last_error[:50] + "..." if len(entry.last_error) > 50 else entry.last_error
                    error_types[error_key] = error_types.get(error_key, 0) + 1

                if entry.failed_at and (oldest_error is None or entry.failed_at < oldest_error):
                    oldest_error = entry.failed_at

            return {
                "total_count": len(dlq_entries),
                "oldest_error": oldest_error.isoformat() if oldest_error else None,
                "error_types": error_types,
                "sample_entries": [
                    {
                        "id": e.id,
                        "name": e.name,
                        "attempts": e.attempts,
                        "last_error": e.last_error[:100] + "..." if e.last_error and len(e.last_error) > 100 else e.last_error,
                        "failed_at": e.failed_at.isoformat() if e.failed_at else None
                    }
                    for e in dlq_entries[:5]  # 最初の5件をサンプルとして
                ]
            }
        except Exception as exc:
            return {"error": f"Failed to get DLQ stats: {exc}"}

    async def log_bus_health(self) -> None:
        """バス健全性の定期ログ出力（監視用）"""

        # use module-level logger

        # 処理済みイベント数
        processed_count = len(self.processed_events)

        # Outbox待機数
        pending_count = 0
        if self.outbox_repo:
            try:
                pending_entries = self.outbox_repo.load_pending(limit=1000)
                pending_count = len(pending_entries)
            except Exception:
                pending_count = -1  # エラー時は-1で表現

        # DLQ統計
        dlq_stats = await self.get_dlq_stats()
        dlq_count = dlq_stats.get("total_count", 0)

        # メトリクス統計
        cmd_stats = self.metrics.get_command_stats()
        event_stats = self.metrics.get_event_stats()

        logger.info(
            f"MessageBus Health: processed={processed_count}, "
            f"pending_outbox={pending_count}, dlq_count={dlq_count}"
        )

        logger.info(
            f"MessageBus Metrics: cmd_count={cmd_stats['count']}, "
            f"cmd_p95={cmd_stats['p95_ms']:.1f}ms, cmd_fail_rate={cmd_stats['failure_rate']:.2%}, "
            f"event_count={event_stats['count']}, event_p95={event_stats['p95_ms']:.1f}ms, "
            f"event_fail_rate={event_stats['failure_rate']:.2%}"
        )

        # DLQに問題がある場合は警告ログも出力
        if dlq_count > 0:
            logger.warning(
                f"DLQ contains {dlq_count} failed events. "
                f"Oldest error: {dlq_stats.get('oldest_error', 'unknown')}"
            )

    def get_metrics_summary(self) -> dict[str, Any]:
        """メトリクス要約の取得（可視化用）"""
        return {
            "commands": self.metrics.get_command_stats(),
            "events": self.metrics.get_event_stats(),
            "processed_events_total": len(self.processed_events)
        }

    def reset_metrics(self) -> None:
        """メトリクスのリセット（定期レポート後に使用）"""
        self.metrics.reset()

    enable_validation: bool = True

    async def handle_command_with_validation(self, name: str, data: dict[str, Any]) -> dict[str, Any]:
        """Execute a command handler with schema validation.

        Args:
            name: Command name
            data: Command data

        Returns:
            Command execution result with validation
        """
        if self.enable_validation:
            try:
                from noveler.application.schemas import validate_command
                validated_command = validate_command(name, data)
                # Convert back to dict for existing handlers
                validated_data = validated_command.dict()
            except (KeyError, ValueError) as e:
                return {"success": False, "error": f"Validation failed: {e}"}
        else:
            validated_data = data

        return await self.handle_command(name, validated_data)

    async def emit_with_validation(self, name: str, payload: dict[str, Any] | None = None) -> None:
        """Emit an event with schema validation.

        Args:
            name: Event name
            payload: Event payload
        """
        if self.enable_validation and payload:
            try:
                from noveler.application.schemas import validate_event
                validated_event = validate_event(name, payload)
                validated_payload = validated_event.dict()
            except ValueError as e:
                logger.warning(f"Event validation failed for {name}: {e}")
                # Continue with original payload for backward compatibility
                validated_payload = payload
        else:
            validated_payload = payload

        await self.emit(name, validated_payload or {})


def _accepts_kwarg(func: Any, kw: str) -> bool:
    try:
        sig = inspect.signature(func)
        if kw in sig.parameters:
            return True
        # キーワード可変を受けられる場合（簡易判定）
        return any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
    except Exception:
        return False


async def _run_with_retry(coro_factory: Callable[[], Awaitable[Any]], cfg: BusConfig) -> Any:
    """Execute the provided coroutine factory with retry and backoff."""
    attempt = 0
    while attempt <= cfg.max_retries:
        try:
            return await coro_factory()
        except Exception:
            if attempt == cfg.max_retries:
                raise
            delay = min(cfg.backoff_base_sec * (2 ** attempt), cfg.backoff_max_sec)
            delay = delay + JITTER_RNG.uniform(0, cfg.jitter_sec)
            await asyncio.sleep(delay)
            attempt += 1


async def _invoke_handler(handler: EventHandler | Callable[[DomainEvent], Any], event: DomainEvent) -> Any:
    """Invoke handler supporting both sync and async callables."""

    result = handler(event)
    if inspect.isawaitable(result):
        return await result
    return result
