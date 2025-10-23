# File: src/noveler/domain/interfaces/state_repository.py
# Purpose: Protocol definition for lightweight step completion state persistence.
# Context: Separates state persistence interface (domain) from file I/O (infrastructure).
#          Works alongside WorkflowStateStore (detailed telemetry) for different purposes.

"""Protocol for step completion state repository.

This interface defines the contract for persisting lightweight step execution state
(completed steps, current progress). It is separate from WorkflowStateStore which
handles detailed telemetry and LLM execution history.

Design Rationale:
- IStateRepository: High-frequency access for "which steps are done?" queries
- WorkflowStateStore: Low-frequency access for "why did step X fail?" analysis

SPEC-901 Compliance: Uses Protocol pattern for dependency inversion (DDD).
"""

from typing import Protocol

__all__ = ["IStateRepository"]


class IStateRepository(Protocol):
    """Protocol for lightweight step completion state persistence.

    This repository manages simple state tracking for step execution progress.
    For detailed execution telemetry, use WorkflowStateStore instead.

    Expected state schema:
        {
            "session_id": str,
            "completed_steps": list[int],
            "current_step": int | None,
            "last_updated": str  # ISO8601 timestamp
        }

    Contract Notes:
    - Implementations MUST handle missing files gracefully (initialize with defaults)
    - save() MUST be atomic (write to temp file, then rename)
    - load_or_initialize() MUST return a valid dict even on I/O errors
    """

    def load_or_initialize(self, default_state: dict) -> dict:
        """Load state file or initialize with defaults if file does not exist.

        Args:
            default_state: Default state dict to use if file doesn't exist.
                          MUST include all required keys (session_id, completed_steps, etc.)

        Returns:
            State dict (either loaded from file or initialized with default_state)

        Raises:
            No exceptions should be raised. If file is corrupted, log warning and return default_state.
        """
        ...

    def save(self, state: dict) -> None:
        """Save state dict to persistent storage.

        Args:
            state: State dict to persist (must match expected schema)

        Raises:
            No exceptions should be raised. If write fails, log error silently.

        Side Effects:
            - Creates parent directories if they don't exist
            - Writes atomically (temp file + rename)
        """
        ...
