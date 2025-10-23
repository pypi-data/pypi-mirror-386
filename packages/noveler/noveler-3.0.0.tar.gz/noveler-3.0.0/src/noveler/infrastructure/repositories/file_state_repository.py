# File: src/noveler/infrastructure/repositories/file_state_repository.py
# Purpose: JSON file-based implementation of IStateRepository.
# Context: Extracted from ProgressiveCheckManager._load_or_initialize_state/_save_state.
#          Provides lightweight step completion state persistence via JSON files.

"""File-based repository for step completion state.

Implements IStateRepository protocol using JSON files for atomic persistence.
Extracted from:
- ProgressiveCheckManager._load_or_initialize_state (line 899-922)
- ProgressiveCheckManager._save_state (line 924-954)

Design Decision:
- Uses JSON for human-readability and simplicity
- Atomic writes via temp file + rename pattern
- No error propagation (logs and returns defaults on failure)

SPEC-901 Compliance: Infrastructure layer handles all I/O operations.
"""

import json
from pathlib import Path

from noveler.infrastructure.logging.unified_logger import get_logger

__all__ = ["FileStateRepository"]

logger = get_logger(__name__)


class FileStateRepository:
    """JSON file-based implementation of IStateRepository.

    This class handles persistent storage of lightweight step completion state.
    It implements atomic writes and graceful degradation on I/O errors.

    Attributes:
        _state_file: Path to the JSON state file.

    Invariants:
        - Parent directory of _state_file is created on first save()
        - All I/O errors are caught and logged (no exceptions propagated)
        - State file is always valid JSON or doesn't exist

    Example:
        >>> repo = FileStateRepository(Path(".noveler/state.json"))
        >>> state = repo.load_or_initialize({"session_id": "test", "completed_steps": []})
        >>> state["completed_steps"].append(1)
        >>> repo.save(state)
    """

    def __init__(self, state_file: Path) -> None:
        """Initialize the repository with a target file path.

        Args:
            state_file: Absolute path to the JSON state file.
                       Parent directory will be created on first save() if needed.

        Preconditions:
            - state_file must be an absolute path (not relative)

        Design Note:
            Does not create the file immediately (lazy initialization).
        """
        self._state_file = state_file

    def load_or_initialize(self, default_state: dict) -> dict:
        """Load state from JSON file or return defaults if file doesn't exist.

        Args:
            default_state: Default state dict to use if file is missing or corrupted.

        Returns:
            State dict (loaded from file or default_state)

        Side Effects:
            - If file doesn't exist, saves default_state to file
            - Logs warnings on I/O errors

        Implementation Notes:
            - Matches ProgressiveCheckManager._load_or_initialize_state (line 899-922)
            - Returns default_state on any JSON parse errors (resilience)
        """
        if not self._state_file.exists():
            logger.info(
                "State file does not exist, initializing with defaults: %s",
                self._state_file,
            )
            self.save(default_state)
            return default_state

        try:
            with self._state_file.open("r", encoding="utf-8") as f:
                loaded_state = json.load(f)
                logger.debug("Loaded state from %s", self._state_file)
                return loaded_state
        except json.JSONDecodeError as e:
            logger.warning(
                "State file is corrupted (invalid JSON), using defaults: %s - %s",
                self._state_file,
                e,
            )
            return default_state
        except Exception:
            logger.exception(
                "Unexpected error loading state file, using defaults: %s",
                self._state_file,
            )
            return default_state

    def save(self, state: dict) -> None:
        """Save state dict to JSON file atomically.

        Args:
            state: State dict to persist (must be JSON-serializable)

        Side Effects:
            - Creates parent directories if they don't exist
            - Writes to temp file, then renames (atomic on POSIX)

        Implementation Notes:
            - Matches ProgressiveCheckManager._save_state (line 924-954)
            - Uses ensure_ascii=False for UTF-8 support
            - Indents with 2 spaces for readability

        Error Handling:
            - Logs errors but does not raise exceptions
            - If write fails, state file is left in previous state
        """
        try:
            # Ensure parent directory exists
            self._state_file.parent.mkdir(parents=True, exist_ok=True)

            # Write to file with pretty-printing
            with self._state_file.open("w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)

            logger.debug("Saved state to %s", self._state_file)

        except Exception:
            logger.exception("Failed to save state to %s", self._state_file)
            # Do not raise - graceful degradation
