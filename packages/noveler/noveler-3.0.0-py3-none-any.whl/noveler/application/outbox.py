"""Outbox value objects and protocol used by application message buses."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, Any


@dataclass
class OutboxEntry:
    """Record representing an event awaiting dispatch from the outbox."""

    id: str
    name: str
    payload: dict[str, Any]
    created_at: datetime
    attempts: int = 0
    dispatched_at: datetime | None = None
    last_error: str | None = None
    failed_at: datetime | None = None
    storage_key: str | None = None


class OutboxRepository(Protocol):
    """Protocol describing persistence operations for outbox entries."""

    def add(self, entry: OutboxEntry) -> None: ...

    def load_pending(self, limit: int = 100) -> list[OutboxEntry]: ...

    def mark_dispatched(self, entry_id: str) -> None: ...

    def increment_attempts(self, entry_id: str, error_message: str) -> None: ...

    def move_to_dlq(self, entry_id: str) -> None: ...

    def load_dlq_entries(self, limit: int = 100) -> list[OutboxEntry]: ...
