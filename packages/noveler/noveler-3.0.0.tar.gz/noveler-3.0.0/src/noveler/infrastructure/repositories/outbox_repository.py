# File: src/noveler/infrastructure/repositories/outbox_repository.py
# Purpose: File-based implementation of the SPEC-901 outbox repository.
# Context: Provides a durable queue for integration events produced by the
#          application MessageBus. Future phases can swap this with a database
#          backed repository without changing the bus contracts.

"""Outbox repository implementations for SPEC-901 message dispatch."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, Protocol

from noveler.domain.events.base import DomainEvent
from noveler.domain.value_objects.message_bus_outbox import (
    OUTBOX_STATUS_PENDING,
    OUTBOX_STATUS_PROCESSING,
    OUTBOX_STATUS_SENT,
    OUTBOX_STATUS_ERRORED,
    OutboxMessage,
)


class OutboxRepository(Protocol):
    """Protocol for outbox repositories used by the message bus."""

    def enqueue_event(self, event: DomainEvent) -> OutboxMessage:
        """Persist an event for asynchronous dispatch."""

    def mark_processing(self, message_id: str) -> None:
        """Move a message into the processing state."""

    def mark_sent(self, message_id: str) -> None:
        """Mark a message as successfully dispatched."""

    def mark_failed(self, message_id: str, error: str) -> None:
        """Record a failed attempt and move the message back to pending."""

    def next_batch(self, limit: int = 10) -> list[OutboxMessage]:
        """Return and lock up to ``limit`` pending messages for processing."""


class FileOutboxRepository:
    """Simple file-system backed outbox storage.

    Structure (under ``base_path``):

    ```
    base_path/
      pending/
      processing/
      sent/
      errored/
    ```
    Each message is stored as ``<status>/<message_id>.json``.
    """

    def __init__(self, base_path: Path) -> None:
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)
        for status in (
            OUTBOX_STATUS_PENDING,
            OUTBOX_STATUS_PROCESSING,
            OUTBOX_STATUS_SENT,
            OUTBOX_STATUS_ERRORED,
        ):
            (self.base_path / status).mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def enqueue_event(self, event: DomainEvent) -> OutboxMessage:
        message = OutboxMessage(
            event_type=event.__class__.__name__,
            payload=event.to_dict(),
            occurred_at=event.occurred_at,
            aggregate_id=getattr(event, "aggregate_id", None),
        )
        self._write_message(message, OUTBOX_STATUS_PENDING)
        return message

    def mark_processing(self, message_id: str) -> None:
        self._move(message_id, OUTBOX_STATUS_PENDING, OUTBOX_STATUS_PROCESSING)

    def mark_sent(self, message_id: str) -> None:
        self._move(message_id, OUTBOX_STATUS_PROCESSING, OUTBOX_STATUS_SENT)

    def mark_failed(self, message_id: str, error: str) -> None:
        message = self._read(message_id)
        message.attempts += 1
        message.last_error = error
        self._write_message(message, OUTBOX_STATUS_ERRORED)
        # requeue for retry
        self._write_message(message, OUTBOX_STATUS_PENDING)

    def next_batch(self, limit: int = 10) -> list[OutboxMessage]:
        candidates = self._list_messages(OUTBOX_STATUS_PENDING)
        batch: list[OutboxMessage] = []
        for message in candidates[: max(0, limit)]:
            self.mark_processing(message.message_id)
            batch.append(self._read(message.message_id, expected_status=OUTBOX_STATUS_PROCESSING))
        return batch

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _status_dir(self, status: str) -> Path:
        return self.base_path / status

    def _write_message(self, message: OutboxMessage, status: str) -> None:
        target = self._status_dir(status) / f"{message.message_id}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(message.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    def _read(self, message_id: str, expected_status: str | None = None) -> OutboxMessage:
        statuses: Iterable[str]
        if expected_status:
            statuses = (expected_status,)
        else:
            statuses = (
                OUTBOX_STATUS_PENDING,
                OUTBOX_STATUS_PROCESSING,
                OUTBOX_STATUS_SENT,
                OUTBOX_STATUS_ERRORED,
            )
        for status in statuses:
            candidate = self._status_dir(status) / f"{message_id}.json"
            if candidate.exists():
                data = json.loads(candidate.read_text(encoding="utf-8"))
                message = OutboxMessage.from_dict(data)
                return message
        raise FileNotFoundError(f"Outbox message {message_id} not found")

    def _move(self, message_id: str, src_status: str, dst_status: str) -> None:
        src = self._status_dir(src_status) / f"{message_id}.json"
        if not src.exists():
            raise FileNotFoundError(f"Outbox message {message_id} missing in {src_status}")
        data = json.loads(src.read_text(encoding="utf-8"))
        src.unlink(missing_ok=True)
        message = OutboxMessage.from_dict(data)
        message.status = dst_status
        if dst_status == OUTBOX_STATUS_PROCESSING:
            message.attempts += 1
        self._write_message(message, dst_status)

    def _list_messages(self, status: str) -> list[OutboxMessage]:
        directory = self._status_dir(status)
        messages: list[OutboxMessage] = []
        for path in sorted(directory.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            messages.append(OutboxMessage.from_dict(data))
        return messages

