"""Message bus implementations for synchronous and asynchronous workflows."""

from __future__ import annotations

import asyncio
import contextlib
from contextlib import asynccontextmanager
import time
from collections.abc import Callable
from typing import Any

from noveler.infrastructure.repositories.outbox_repository import OutboxRepository
from noveler.infrastructure.services.idempotency_store import IdempotencyStore

from noveler.domain.commands.base import DomainCommand
from noveler.domain.events.base import DomainEvent

Handler = Callable[..., Any]


class MessageBus:
    """Lightweight synchronous message bus compliant with SPEC-901."""

    def __init__(
        self,
        *,
        uow: Any | None = None,
        event_handlers: dict[type, list[Handler]] | None = None,
        command_handlers: dict[type, Handler] | None = None,
        logger: Any | None = None,
        enable_async: bool | None = None,
        outbox_repository: OutboxRepository | None = None,
        idempotency_store: IdempotencyStore | None = None,
    ) -> None:
        self.uow = uow
        self.event_handlers: dict[type, list[Handler]] = event_handlers or {}
        self.command_handlers: dict[type, Handler] = command_handlers or {}
        self.logger = logger
        self._enable_async = bool(enable_async)
        self._outbox_repository = outbox_repository
        self._idempotency_store = idempotency_store

        # metrics
        self._messages_processed = 0
        self._events_processed = 0
        self._commands_processed = 0
        self._total_processing_time = 0.0

    def handle(self, message: Any) -> Any:
        """Process a command or event synchronously.

        Args:
            message: Domain event or command instance.

        Returns:
            Any: Handler response or ``None`` if no handler is registered.
        """
        start = time.time()
        try:
            if isinstance(message, DomainEvent):
                self._handle_event(message)
                return None
            if isinstance(message, DomainCommand):
                return self._handle_command(message)
            return None
        finally:
            self._messages_processed += 1
            self._total_processing_time += (time.time() - start)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _handle_event(self, event: DomainEvent) -> None:
        """Dispatch an event and persist it to the outbox."""

        if self._outbox_repository and event:
            with contextlib.suppress(Exception):
                self._outbox_repository.enqueue_event(event)

        handlers = self._get_event_handlers_for(event)
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                if self.logger and hasattr(self.logger, "exception"):
                    with contextlib.suppress(Exception):
                        self.logger.exception("event handler error")
        self._events_processed += 1

    def _handle_command(self, command: DomainCommand) -> Any:
        """Dispatch a command with optional idempotency guarantees."""

        handler = self._get_command_handler_for(command)
        if handler is None:
            self._commands_processed += 1
            return {"success": False, "error": f"No handler for {type(command).__name__}"}

        idempotency_key = None
        if self._idempotency_store:
            idempotency_key = command.get_metadata("idempotency_key")
            if not idempotency_key:
                idempotency_key = command.metadata.get("idempotency_key")
            if idempotency_key:
                record = self._idempotency_store.get(idempotency_key)
                if record and record.status == "success":
                    self._commands_processed += 1
                    return record.result
                if record and record.status == "pending":
                    self._commands_processed += 1
                    return {"success": False, "error": "duplicate command pending"}
                self._idempotency_store.record_pending(idempotency_key)

        try:
            result = handler(command)
            if idempotency_key and self._idempotency_store:
                with contextlib.suppress(Exception):
                    self._idempotency_store.record_success(idempotency_key, result)
            return result
        except Exception:
            if self.logger and hasattr(self.logger, "exception"):
                with contextlib.suppress(Exception):
                    self.logger.exception("command handler error")
            if idempotency_key and self._idempotency_store:
                with contextlib.suppress(Exception):
                    self._idempotency_store.record_failure(idempotency_key, "handler error")
            return {"success": False, "error": "handler error"}
        finally:
            self._commands_processed += 1

    def _get_event_handlers_for(self, event: DomainEvent) -> list[Handler]:
        """Return handlers registered for the concrete event type."""
        handlers: list[Handler] = []
        for etype, handler_list in self.event_handlers.items():
            if isinstance(event, etype):
                handlers.extend(handler_list)
        return handlers

    def _get_command_handler_for(self, command: DomainCommand) -> Handler | None:
        """Return the handler mapped to the command type, if any."""
        for ctype, handler in self.command_handlers.items():
            if isinstance(command, ctype):
                return handler
        return None

    def get_metrics(self) -> dict[str, Any]:
        """Return runtime metrics collected by the bus."""
        count = max(1, self._messages_processed)
        return {
            "messages_processed": self._messages_processed,
            "events_processed": self._events_processed,
            "commands_processed": self._commands_processed,
            "total_processing_time": self._total_processing_time,
            "average_processing_time": self._total_processing_time / count,
        }


class AsyncMessageBus(MessageBus):
    """Asynchronous message bus that can offload synchronous handlers."""

    def __init__(
        self,
        *,
        uow: Any | None = None,
        event_handlers: dict[type, list[Handler]] | None = None,
        command_handlers: dict[type, Handler] | None = None,
        logger: Any | None = None,
        max_concurrent_events: int = 10,
        outbox_repository: OutboxRepository | None = None,
        idempotency_store: IdempotencyStore | None = None,
    ) -> None:
        super().__init__(
            uow=uow,
            event_handlers=event_handlers,
            command_handlers=command_handlers,
            logger=logger,
            enable_async=True,
            outbox_repository=outbox_repository,
            idempotency_store=idempotency_store,
        )
        self.max_concurrent_events = max(1, int(max_concurrent_events))
        self._sem = asyncio.Semaphore(self.max_concurrent_events)

    async def handle_async(self, message: Any) -> Any:
        """Process a command or event using asynchronous execution."""
        start = time.time()
        try:
            if isinstance(message, DomainEvent):
                self._handle_event(message)

                handlers = self._get_event_handlers_for(message)

                async def run_handler(h: Handler):
                    async with self._async_slot():
                        try:
                            if asyncio.iscoroutinefunction(h):
                                return await h(message)
                            return await asyncio.to_thread(h, message)
                        except Exception:
                            if self.logger and hasattr(self.logger, "exception"):
                                with contextlib.suppress(Exception):
                                    self.logger.exception("async event handler error")
                            return None

                await asyncio.gather(*(run_handler(h) for h in handlers))
                self._events_processed += 1
                return None

            if isinstance(message, DomainCommand):
                handler = self._get_command_handler_for(message)
                if handler is None:
                    self._commands_processed += 1
                    return {"success": False, "error": f"No handler for {type(message).__name__}"}

                idempotency_key = None
                if self._idempotency_store:
                    idempotency_key = message.get_metadata("idempotency_key")
                    if not idempotency_key:
                        idempotency_key = message.metadata.get("idempotency_key")
                    if idempotency_key:
                        record = self._idempotency_store.get(idempotency_key)
                        if record and record.status == "success":
                            self._commands_processed += 1
                            return record.result
                        if record and record.status == "pending":
                            self._commands_processed += 1
                            return {"success": False, "error": "duplicate command pending"}
                        self._idempotency_store.record_pending(idempotency_key)

                try:
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(message)
                    else:
                        result = await asyncio.to_thread(handler, message)
                    if idempotency_key and self._idempotency_store:
                        with contextlib.suppress(Exception):
                            self._idempotency_store.record_success(idempotency_key, result)
                except Exception:
                    if self.logger and hasattr(self.logger, "exception"):
                        with contextlib.suppress(Exception):
                            self.logger.exception("async command handler error")
                    if idempotency_key and self._idempotency_store:
                        with contextlib.suppress(Exception):
                            self._idempotency_store.record_failure(idempotency_key, "handler error")
                    result = {"success": False, "error": "handler error"}
                self._commands_processed += 1
                return result
            return None
        finally:
            self._messages_processed += 1
            self._total_processing_time += (time.time() - start)


    @asynccontextmanager
    async def _async_slot(self):
        """Serialize access to concurrent event handler execution."""
        await self._sem.acquire()
        try:
            yield
        finally:
            self._sem.release()


def create_mcp_message_bus(
    *,
    uow: Any | None,
    event_handlers: dict[type, list[Handler]] | None,
    command_handlers: dict[type, Handler] | None,
    logger: Any | None = None,
    async_mode: bool = True,
    outbox_repository: OutboxRepository | None = None,
    idempotency_store: IdempotencyStore | None = None,
) -> MessageBus:
    """Factory that builds a message bus configured for MCP integrations.

    Args:
        uow: Unit of work instance injected into handlers.
        event_handlers: Mapping of event types to handler lists.
        command_handlers: Mapping of command types to handlers.
        logger: Optional logger used for diagnostics.
        async_mode: When ``True`` return an asynchronous bus implementation.

    Returns:
        MessageBus: Configured synchronous or asynchronous bus.
    """
    if async_mode:
        return AsyncMessageBus(
            uow=uow,
            event_handlers=event_handlers,
            command_handlers=command_handlers,
            logger=logger,
            max_concurrent_events=5,
            outbox_repository=outbox_repository,
            idempotency_store=idempotency_store,
        )
    return MessageBus(
        uow=uow,
        event_handlers=event_handlers,
        command_handlers=command_handlers,
        logger=logger,
        enable_async=False,
        outbox_repository=outbox_repository,
        idempotency_store=idempotency_store,
    )
