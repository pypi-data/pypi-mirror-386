# File: src/noveler/domain/interfaces/session_manifest_repository.py
# Purpose: Protocol for session manifest persistence (JSON format)
# Context: Used by SessionCoordinator to read/write session metadata

from typing import Protocol
from pathlib import Path


class ISessionManifestRepository(Protocol):
    """Protocol for session manifest file persistence.

    Responsibilities:
        - Read session manifest from JSON file
        - Write session manifest to JSON file
        - Abstract file I/O from domain layer

    Expected manifest schema:
        {
            "session_id": str,
            "session_start_ts": str,  # ISO8601 timestamp
            "session_start_compact": str,  # yyyyMMddHHMM format
            "episode_number": int,
            "project_root": str,
            "metadata": dict  # Optional additional metadata
        }

    File format: JSON with UTF-8 encoding
    """

    def read_manifest(self, manifest_path: Path) -> dict:
        """Read session manifest from JSON file.

        Args:
            manifest_path: Path to manifest JSON file

        Returns:
            Manifest data as dict

        Raises:
            FileNotFoundError: If manifest_path does not exist
            json.JSONDecodeError: If file is not valid JSON
            OSError: If file cannot be read (permissions, I/O error)

        Side Effects:
            May log debug messages about file read
        """
        ...

    def write_manifest(self, manifest_path: Path, data: dict) -> None:
        """Write session manifest to JSON file.

        Args:
            manifest_path: Path to manifest JSON file
            data: Manifest dict to serialize

        Side Effects:
            - Creates parent directories if they don't exist
            - Overwrites file if it already exists
            - Writes atomically (temp file + rename)

        Raises:
            OSError: If file cannot be written (permissions, disk full)
            TypeError: If data contains non-serializable objects

        Implementation Notes:
            - Should use ensure_ascii=False for UTF-8 output
            - Should use indent=2 for human-readable formatting
            - Should handle Japanese characters correctly
        """
        ...
