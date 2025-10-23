"""Idempotency helpers used by message buses."""

from __future__ import annotations

from typing import Protocol


class IdempotencyStore(Protocol):
    """Protocol describing idempotency markers for processed events."""

    def was_processed(self, event_id: str) -> bool: ...

    def mark_processed(self, event_id: str) -> None: ...


class InMemoryIdempotencyStore(IdempotencyStore):
    """Naive in-memory idempotency store suitable for tests."""

    def __init__(self) -> None:
        self._seen: set[str] = set()
        self._processed_events: list[str] = []

    def was_processed(self, event_id: str) -> bool:
        """Return ``True`` when the event identifier has been seen before."""

        return event_id in self._seen

    def is_processed(self, event_id: str) -> bool:
        """Compatibility alias for was_processed."""
        return self.was_processed(event_id)

    def mark_processed(self, event_id: str) -> None:
        """Record the event identifier as processed."""

        if event_id not in self._seen:
            self._processed_events.append(event_id)
        self._seen.add(event_id)
