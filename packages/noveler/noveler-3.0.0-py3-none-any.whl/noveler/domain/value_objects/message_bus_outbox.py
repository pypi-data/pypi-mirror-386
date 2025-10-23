# File: src/noveler/domain/value_objects/message_bus_outbox.py
# Purpose: Define value objects for the SPEC-901 outbox/idempotency layer.
# Context: Consumed by the application message bus and infrastructure
#          repositories to persist integration events and idempotency records.
"""Value objects supporting SPEC-901 outbox and idempotency features."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid
from typing import Any


OUTBOX_STATUS_PENDING = "pending"
OUTBOX_STATUS_PROCESSING = "processing"
OUTBOX_STATUS_SENT = "sent"
OUTBOX_STATUS_ERRORED = "errored"


@dataclass(slots=True)
class OutboxMessage:
    """Persisted representation of a domain event awaiting dispatch."""

    event_type: str
    payload: dict[str, Any]
    occurred_at: datetime
    aggregate_id: str | None = None
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = OUTBOX_STATUS_PENDING
    attempts: int = 0
    last_error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Serialise the message into a JSON-friendly structure."""

        return {
            "message_id": self.message_id,
            "event_type": self.event_type,
            "payload": self.payload,
            "occurred_at": self.occurred_at.isoformat(),
            "aggregate_id": self.aggregate_id,
            "status": self.status,
            "attempts": self.attempts,
            "last_error": self.last_error,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OutboxMessage":
        """Rehydrate an :class:`OutboxMessage` from persisted data."""

        return cls(
            message_id=data.get("message_id", str(uuid.uuid4())),
            event_type=data["event_type"],
            payload=data.get("payload", {}),
            occurred_at=datetime.fromisoformat(data["occurred_at"]),
            aggregate_id=data.get("aggregate_id"),
            status=data.get("status", OUTBOX_STATUS_PENDING),
            attempts=int(data.get("attempts", 0)),
            last_error=data.get("last_error"),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now(timezone.utc).isoformat())),
        )


@dataclass(slots=True)
class IdempotencyRecord:
    """Stored metadata representing a processed command for deduplication."""

    key: str
    status: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    result: dict[str, Any] | None = None
    last_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialise the record for persistence."""

        return {
            "key": self.key,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "result": self.result,
            "last_error": self.last_error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IdempotencyRecord":
        """Rehydrate an :class:`IdempotencyRecord` from persisted data."""

        return cls(
            key=data["key"],
            status=data["status"],
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now(timezone.utc).isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now(timezone.utc).isoformat())),
            result=data.get("result"),
            last_error=data.get("last_error"),
        )

