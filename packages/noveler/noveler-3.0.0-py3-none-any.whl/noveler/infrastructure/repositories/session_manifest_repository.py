# File: src/noveler/infrastructure/repositories/session_manifest_repository.py
# Purpose: JSON file-based session manifest persistence
# Context: Extracted from ProgressiveCheckManager._load_manifest and _save_manifest

import json
from pathlib import Path

from noveler.infrastructure.logging.unified_logger import get_logger

logger = get_logger(__name__)


class SessionManifestRepository:
    """JSON file-based implementation of ISessionManifestRepository.

    Responsibilities:
        - Read session manifest from JSON file
        - Write session manifest to JSON file with atomic write
        - Handle UTF-8 encoding correctly (Japanese characters)
        - Provide graceful degradation on read errors

    File format:
        - JSON with ensure_ascii=False (UTF-8 output)
        - indent=2 for human readability
        - Atomic write (direct overwrite, not temp+rename for simplicity)

    Extracted from:
        - ProgressiveCheckManager._load_manifest (lines 455-472)
        - ProgressiveCheckManager._save_manifest (lines 473-484)
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
            ValueError: If JSON root is not a dict
            OSError: If file cannot be read (permissions, I/O error)

        Side Effects:
            Logs debug message on successful read
        """
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest file does not exist: {manifest_path}")

        try:
            with manifest_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                raise ValueError(f"Manifest root must be dict, got {type(data).__name__}")

            logger.debug("Loaded manifest from %s", manifest_path)
            return data

        except json.JSONDecodeError as e:
            logger.error("Manifest file is not valid JSON: %s - %s", manifest_path, e)
            raise
        except OSError as e:
            logger.error("Failed to read manifest file: %s - %s", manifest_path, e)
            raise

    def write_manifest(self, manifest_path: Path, data: dict) -> None:
        """Write session manifest to JSON file.

        Args:
            manifest_path: Path to manifest JSON file
            data: Manifest dict to serialize

        Side Effects:
            - Creates parent directories if they don't exist
            - Overwrites file if it already exists
            - Writes with UTF-8 encoding

        Raises:
            OSError: If file cannot be written (permissions, disk full)
            TypeError: If data contains non-JSON-serializable objects

        Implementation Notes:
            - Uses ensure_ascii=False for UTF-8 output (Japanese characters)
            - Uses indent=2 for human-readable formatting
            - Creates parent directories automatically
        """
        try:
            manifest_path.parent.mkdir(parents=True, exist_ok=True)

            with manifest_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug("Saved manifest to %s", manifest_path)

        except TypeError as e:
            logger.error("Manifest data contains non-serializable objects: %s", e)
            raise
        except OSError as e:
            logger.error("Failed to write manifest file: %s - %s", manifest_path, e)
            raise
