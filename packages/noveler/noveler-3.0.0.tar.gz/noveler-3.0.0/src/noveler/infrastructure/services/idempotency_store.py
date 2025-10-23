# File: src/noveler/infrastructure/services/idempotency_store.py
# Purpose: Provide a lightweight, file-backed idempotency store used by the
#          application message bus to deduplicate command executions.

"""Idempotency persistence helpers for the SPEC-901 message bus."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from noveler.domain.value_objects.message_bus_outbox import IdempotencyRecord


class IdempotencyStore(Protocol):
    """Protocol describing idempotency persistence operations."""

    def get(self, key: str) -> IdempotencyRecord | None:
        """Return the record for `key` if one exists."""

    def record_pending(self, key: str) -> None:
        """Mark that command execution for `key` has started."""

    def record_success(self, key: str, result: Any | None) -> None:
        """Persist a successful execution result for `key`."""

    def record_failure(self, key: str, error: str | None = None) -> None:
        """Persist a failed execution result for `key`."""


class FileIdempotencyStore:
    """Simple JSON-file backed idempotency register."""

    def __init__(self, store_path: Path) -> None:
        self.store_path = store_path
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.store_path.exists():
            self.store_path.write_text("{}", encoding="utf-8")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get(self, key: str) -> IdempotencyRecord | None:
        data = self._load().get(key)
        if not data:
            return None
        return IdempotencyRecord.from_dict(data)

    def record_pending(self, key: str) -> None:
        records = self._load()
        now = datetime.now(timezone.utc).isoformat()
        records[key] = {
            "key": key,
            "status": "pending",
            "created_at": records.get(key, {}).get("created_at", now),
            "updated_at": now,
            "result": None,
            "last_error": None,
        }
        self._save(records)

    def record_success(self, key: str, result: Any | None) -> None:
        records = self._load()
        now = datetime.now(timezone.utc).isoformat()
        records[key] = {
            "key": key,
            "status": "success",
            "created_at": records.get(key, {}).get("created_at", now),
            "updated_at": now,
            "result": result,
            "last_error": None,
        }
        self._save(records)

    def record_failure(self, key: str, error: str | None = None) -> None:
        records = self._load()
        now = datetime.now(timezone.utc).isoformat()
        records[key] = {
            "key": key,
            "status": "failed",
            "created_at": records.get(key, {}).get("created_at", now),
            "updated_at": now,
            "result": None,
            "last_error": error,
        }
        self._save(records)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load(self) -> dict[str, dict[str, Any]]:
        raw = self.store_path.read_text(encoding="utf-8")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {}
        if not isinstance(data, dict):  # type: ignore[unreachable]
            data = {}
        return data  # type: ignore[return-value]

    def _save(self, data: dict[str, dict[str, Any]]) -> None:
        self.store_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class SQLiteIdempotencyStore:
    """SQLite-backed idempotency register for persistent deduplication."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _init_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS idempotency_records (
                    key TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    result TEXT,
                    last_error TEXT
                )
                """
            )
            conn.commit()

    def get(self, key: str) -> IdempotencyRecord | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM idempotency_records WHERE key = ?",
                (key,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        result = None
        if row["result"]:
            try:
                result = json.loads(row["result"])
            except json.JSONDecodeError:
                result = None

        return IdempotencyRecord(
            key=row["key"],
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            result=result,
            last_error=row["last_error"],
        )

    def record_pending(self, key: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT created_at FROM idempotency_records WHERE key = ?",
                (key,),
            )
            existing = cursor.fetchone()
            created_at = existing[0] if existing else now

            conn.execute(
                """
                INSERT OR REPLACE INTO idempotency_records
                (key, status, created_at, updated_at, result, last_error)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (key, "pending", created_at, now, None, None),
            )
            conn.commit()

    def record_success(self, key: str, result: Any | None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        result_json = json.dumps(result, ensure_ascii=False) if result is not None else None
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT created_at FROM idempotency_records WHERE key = ?",
                (key,),
            )
            existing = cursor.fetchone()
            created_at = existing[0] if existing else now

            conn.execute(
                """
                INSERT OR REPLACE INTO idempotency_records
                (key, status, created_at, updated_at, result, last_error)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (key, "success", created_at, now, result_json, None),
            )
            conn.commit()

    def record_failure(self, key: str, error: str | None = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT created_at FROM idempotency_records WHERE key = ?",
                (key,),
            )
            existing = cursor.fetchone()
            created_at = existing[0] if existing else now

            conn.execute(
                """
                INSERT OR REPLACE INTO idempotency_records
                (key, status, created_at, updated_at, result, last_error)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (key, "failed", created_at, now, None, error),
            )
            conn.commit()

