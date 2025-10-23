#!/usr/bin/env python3
# File: src/noveler/application/dead_letter_queue.py
# Purpose: Dead Letter Queue implementation for failed events/commands
# Context: SPEC-901 P1 requirement for production reliability

"""Purpose:
    Provide dead letter queue (DLQ) abstractions for commands and events that exhaust retries.

Inputs:
    Accepts failed message payloads, metadata, and persistence configuration (filesystem paths or in-memory maps).

Outputs:
    Stores DLQ entries for later inspection or replay and exposes query/manipulation helpers.

Preconditions:
    Callers must supply serialisable payloads and ensure the filesystem repository has write access.

Side Effects:
    Persists DLQ entries to disk, logs diagnostic information, and mutates in-memory repositories.

Exceptions:
    Propagates filesystem and JSON serialisation errors from repository implementations.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from noveler.infrastructure.logging.unified_logger import get_logger

logger = get_logger(__name__)


@dataclass
class DLQEntry:
    """Purpose:
        Represent a failed command or event captured by the dead letter queue.

    Attributes:
        id: Unique identifier for the DLQ entry.
        message_type: Type classification (`"command"` or `"event"`).
        message_name: Name of the message that failed.
        payload: Original message payload stored for replay.
        original_error: Error message captured during failure.
        attempt_count: Number of retry attempts performed.
        first_failed_at: Timestamp of the first failure occurrence (UTC).
        last_failed_at: Timestamp of the most recent failure (UTC).
        metadata: Additional diagnostic information supplied by callers.

    Preconditions:
        Timestamps must be timezone-aware UTC datetimes if provided explicitly.

    Side Effects:
        None; dataclass instantiation is pure.

    Exceptions:
        None.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    message_type: str = ""  # "command" or "event"
    message_name: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    original_error: str = ""
    attempt_count: int = 0
    first_failed_at: datetime = field(default_factory=datetime.utcnow)
    last_failed_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


class DLQRepository:
    """Purpose:
        Define the storage interface for persisting and retrieving dead letter queue entries.

    Preconditions:
        Concrete implementations must guarantee thread/process safety appropriate to their usage context.

    Side Effects:
        None at the interface level.

    Exceptions:
        Implementations should raise domain-specific exceptions when operations fail.
    """

    def add(self, entry: DLQEntry) -> None:
        """Purpose:
            Persist a failed message entry into the dead letter queue.

        Args:
            entry: DLQEntry describing the failed message and diagnostics.

        Returns:
            None.

        Preconditions:
            `entry` must be fully populated with serialisable fields.

        Side Effects:
            Mutates the underlying DLQ storage.

        Raises:
            NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError

    def list_all(self, limit: Optional[int] = None) -> list[DLQEntry]:
        """Purpose:
            Retrieve DLQ entries for inspection, optionally limiting the count.

        Args:
            limit: Maximum number of entries to return; `None` returns all entries.

        Returns:
            list[DLQEntry]: Ordered collection of DLQ entries.

        Preconditions:
            None.

        Side Effects:
            None.

        Raises:
            NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError

    def get_by_id(self, entry_id: str) -> Optional[DLQEntry]:
        """Purpose:
            Fetch a DLQ entry by its identifier.

        Args:
            entry_id: Identifier of the entry to retrieve.

        Returns:
            Optional[DLQEntry]: Matching entry or `None` when not found.

        Preconditions:
            `entry_id` must be a non-empty string.

        Side Effects:
            None.

        Raises:
            NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError

    def remove(self, entry_id: str) -> bool:
        """Purpose:
            Delete a DLQ entry, typically after successful replay.

        Args:
            entry_id: Identifier of the entry to remove.

        Returns:
            bool: True when the entry was removed, False otherwise.

        Preconditions:
            `entry_id` must reference an existing entry to succeed.

        Side Effects:
            Mutates DLQ storage by deleting records.

        Raises:
            NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError

    def clear(self) -> int:
        """Purpose:
            Remove all entries from the dead letter queue.

        Returns:
            int: Number of entries removed.

        Preconditions:
            None.

        Side Effects:
            Empties the DLQ storage.

        Raises:
            NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError


class FileDLQRepository(DLQRepository):
    """Purpose:
        Persist DLQ entries as JSON files on the local filesystem.

    Attributes:
        base_dir: Directory where DLQ entry files are stored.

    Preconditions:
        Caller must ensure the base directory is writable.

    Side Effects:
        Creates directories, writes and deletes files, and logs repository activity.

    Exceptions:
        Propagates filesystem and JSON-related errors during operations.
    """

    def __init__(self, base_dir: Path):
        """Purpose:
            Initialise the file-based DLQ repository and ensure storage directories exist.

        Args:
            base_dir: Root directory used to persist DLQ entry files.

        Returns:
            None.

        Preconditions:
            `base_dir` must point to a location with create/write permissions.

        Side Effects:
            Creates the directory structure when it does not exist and logs initialisation.

        Exceptions:
            Raises OSError if the directory cannot be created.
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized FileDLQRepository at {self.base_dir}")

    def _entry_path(self, entry_id: str) -> Path:
        """Purpose:
            Compute the filesystem path used to store a DLQ entry.

        Args:
            entry_id: Identifier of the DLQ entry.

        Returns:
            Path: Full path to the JSON file storing the entry.

        Preconditions:
            `entry_id` must be a valid filename segment.

        Side Effects:
            None.

        Raises:
            None.
        """
        return self.base_dir / f"dlq_{entry_id}.json"

    def add(self, entry: DLQEntry) -> None:
        """Purpose:
            Write a DLQ entry to the filesystem repository.

        Args:
            entry: DLQEntry containing failure metadata to persist.

        Returns:
            None.

        Preconditions:
            Repository directory must be writable.

        Side Effects:
            Serialises the entry to JSON and writes it to disk, logging warnings.

        Raises:
            OSError: When the entry cannot be written to disk.
            json.JSONDecodeError: If serialization fails unexpectedly.
        """
        try:
            entry_path = self._entry_path(entry.id)

            # Convert datetime to ISO format for JSON serialization
            entry_dict = asdict(entry)
            entry_dict["first_failed_at"] = entry.first_failed_at.isoformat()
            entry_dict["last_failed_at"] = entry.last_failed_at.isoformat()

            with open(entry_path, "w", encoding="utf-8") as f:
                json.dump(entry_dict, f, ensure_ascii=False, indent=2)

            logger.warning(
                f"Added to DLQ: {entry.message_type} '{entry.message_name}' "
                f"(attempts={entry.attempt_count}, error={entry.original_error[:100]})"
            )
        except Exception as e:
            logger.error(f"Failed to add DLQ entry {entry.id}: {e}")
            raise

    def list_all(self, limit: Optional[int] = None) -> list[DLQEntry]:
        """Purpose:
            Enumerate DLQ entries stored on disk.

        Args:
            limit: Optional maximum number of entries to return.

        Returns:
            list[DLQEntry]: Loaded entries up to the specified limit.

        Preconditions:
            Repository directory must be readable.

        Side Effects:
            Reads JSON files and logs failures; converts timestamps to datetime objects.

        Raises:
            OSError: When the directory cannot be read.
        """
        entries: list[DLQEntry] = []

        try:
            dlq_files = sorted(self.base_dir.glob("dlq_*.json"))

            for dlq_file in dlq_files[:limit] if limit else dlq_files:
                try:
                    with open(dlq_file, encoding="utf-8") as f:
                        data = json.load(f)

                    # Convert ISO format strings back to datetime
                    data["first_failed_at"] = datetime.fromisoformat(data["first_failed_at"])
                    data["last_failed_at"] = datetime.fromisoformat(data["last_failed_at"])

                    entries.append(DLQEntry(**data))
                except Exception as e:
                    logger.error(f"Failed to load DLQ entry from {dlq_file}: {e}")

            return entries
        except Exception as e:
            logger.error(f"Failed to list DLQ entries: {e}")
            return []

    def get_by_id(self, entry_id: str) -> Optional[DLQEntry]:
        """Purpose:
            Load a specific DLQ entry from the filesystem by identifier.

        Args:
            entry_id: Identifier of the DLQ entry to retrieve.

        Returns:
            Optional[DLQEntry]: Matching entry or `None` when absent.

        Preconditions:
            Entry file must exist and contain valid JSON.

        Side Effects:
            Reads from disk and logs lookup issues.

        Raises:
            OSError: If the entry file cannot be read.
            ValueError: If timestamp parsing fails.
        """
        try:
            entry_path = self._entry_path(entry_id)

            if not entry_path.exists():
                return None

            with open(entry_path, encoding="utf-8") as f:
                data = json.load(f)

            # Convert ISO format strings back to datetime
            data["first_failed_at"] = datetime.fromisoformat(data["first_failed_at"])
            data["last_failed_at"] = datetime.fromisoformat(data["last_failed_at"])

            return DLQEntry(**data)
        except Exception as e:
            logger.error(f"Failed to get DLQ entry {entry_id}: {e}")
            return None

    def remove(self, entry_id: str) -> bool:
        """Purpose:
            Delete a DLQ entry file after successful replay.

        Args:
            entry_id: Identifier of the entry to remove.

        Returns:
            bool: True when the entry was removed; False if missing or deletion failed.

        Preconditions:
            Entry file should exist to return True.

        Side Effects:
            Removes files from disk and writes log messages.

        Raises:
            OSError: When file deletion fails.
        """
        try:
            entry_path = self._entry_path(entry_id)

            if not entry_path.exists():
                return False

            entry_path.unlink()
            logger.info(f"Removed DLQ entry {entry_id} after successful replay")
            return True
        except Exception as e:
            logger.error(f"Failed to remove DLQ entry {entry_id}: {e}")
            return False

    def clear(self) -> int:
        """Purpose:
            Remove all DLQ entries from the filesystem storage.

        Returns:
            int: Number of entries deleted.

        Preconditions:
            Repository directory must be writable.

        Side Effects:
            Deletes JSON files and logs the cleanup outcome.

        Raises:
            OSError: When one or more DLQ files cannot be deleted.
        """
        try:
            dlq_files = list(self.base_dir.glob("dlq_*.json"))
            count = len(dlq_files)

            for dlq_file in dlq_files:
                dlq_file.unlink()

            logger.info(f"Cleared {count} DLQ entries")
            return count
        except Exception as e:
            logger.error(f"Failed to clear DLQ entries: {e}")
            return 0


class InMemoryDLQRepository(DLQRepository):
    """Purpose:
        Provide an in-memory DLQ repository suited for tests and development.

    Attributes:
        entries: Mutable mapping of entry IDs to DLQEntry instances.

    Preconditions:
        Intended for single-process usage; not thread-safe by default.

    Side Effects:
        Stores entries in memory and logs repository actions.

    Exceptions:
        None beyond standard dictionary operations.
    """

    def __init__(self):
        """Purpose:
            Initialise the in-memory repository with an empty entry mapping.

        Returns:
            None.

        Preconditions:
            None.

        Side Effects:
            Logs the repository initialisation.

        Exceptions:
            None.
        """
        self.entries: dict[str, DLQEntry] = {}
        logger.debug("Initialized InMemoryDLQRepository")

    def add(self, entry: DLQEntry) -> None:
        """Purpose:
            Store a DLQ entry in the in-memory repository.

        Args:
            entry: DLQEntry representing the failed message.

        Returns:
            None.

        Preconditions:
            Entry IDs should be unique to avoid overwriting.

        Side Effects:
            Mutates the internal entries mapping and logs a warning.

        Raises:
            None.
        """
        self.entries[entry.id] = entry
        logger.warning(
            f"Added to DLQ (in-memory): {entry.message_type} '{entry.message_name}' "
            f"(attempts={entry.attempt_count})"
        )

    def list_all(self, limit: Optional[int] = None) -> list[DLQEntry]:
        """Purpose:
            Retrieve stored DLQ entries from memory.

        Args:
            limit: Optional maximum number of entries to return.

        Returns:
            list[DLQEntry]: Entries up to the specified limit.

        Preconditions:
            None.

        Side Effects:
            None.

        Raises:
            None.
        """
        all_entries = list(self.entries.values())
        return all_entries[:limit] if limit else all_entries

    def get_by_id(self, entry_id: str) -> Optional[DLQEntry]:
        """Purpose:
            Retrieve a DLQ entry by identifier from the in-memory store.

        Args:
            entry_id: Identifier of the entry to fetch.

        Returns:
            Optional[DLQEntry]: Entry when found, otherwise None.

        Preconditions:
            `entry_id` must be a valid key in the repository.

        Side Effects:
            None.

        Exceptions:
            None.
        """
        return self.entries.get(entry_id)

    def remove(self, entry_id: str) -> bool:
        """Purpose:
            Remove a DLQ entry from memory after successful replay.

        Args:
            entry_id: Identifier of the entry to delete.

        Returns:
            bool: True if the entry existed and was removed, False otherwise.

        Preconditions:
            Entry should exist to return True.

        Side Effects:
            Mutates the internal entries mapping and logs removals.

        Raises:
            None.
        """
        if entry_id in self.entries:
            del self.entries[entry_id]
            logger.info(f"Removed DLQ entry {entry_id} (in-memory)")
            return True
        return False

    def clear(self) -> int:
        """Purpose:
            Remove all DLQ entries from the in-memory repository.

        Returns:
            int: Number of entries removed.

        Preconditions:
            None.

        Side Effects:
            Clears the backing dictionary and logs the action.

        Raises:
            None.
        """
        count = len(self.entries)
        self.entries.clear()
        logger.info(f"Cleared {count} DLQ entries (in-memory)")
        return count
