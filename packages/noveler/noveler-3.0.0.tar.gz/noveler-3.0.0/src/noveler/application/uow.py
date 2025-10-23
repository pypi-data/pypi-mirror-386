"""Unit-of-work protocol and simple in-memory implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, Any, List


class UnitOfWork(Protocol):
    """Protocol describing the contract for unit-of-work implementations."""

    def begin(self) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...

    def add_event(self, name: str, payload: dict[str, Any] | None = None) -> None: ...

    def get_events(self) -> list[tuple[str, dict[str, Any]]]: ...

    def clear_events(self) -> None: ...


@dataclass
class InMemoryUnitOfWork(UnitOfWork):
    """Minimal in-memory unit of work for testing and lightweight scenarios."""

    episode_repo: Any
    _started: bool = False
    _events: List[tuple[str, dict[str, Any]]] = field(default_factory=list)

    def begin(self) -> None:
        """Mark the unit of work as started."""
        self._started = True

    def commit(self) -> None:
        """Mark the unit of work as committed, resetting internal state."""
        if not self._started:
            return
        self._started = False
        self.clear_events()

    def rollback(self) -> None:
        """Rollback the unit of work; no persistence is performed in-memory."""
        self._started = False
        self.clear_events()

    def add_event(self, name: str, payload: dict[str, Any] | None = None) -> None:
        """Buffer a domain event to be published after commit."""
        self._events.append((name, payload or {}))

    def get_events(self) -> list[tuple[str, dict[str, Any]]]:
        """Return a copy of buffered events."""
        return list(self._events)

    def clear_events(self) -> None:
        """Clear buffered events."""
        self._events.clear()
