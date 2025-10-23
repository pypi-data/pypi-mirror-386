"""Minimal TaskManager stub for integration tests.

Tests may patch this class to observe progress handling. The production
implementation lives elsewhere; this stub avoids import errors during patching.
"""

from __future__ import annotations

from typing import Any


class TaskManager:
    """No-op stub. Methods are intentionally minimal and safe to call."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover
        self._status = "idle"

    def register_subtasks(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover
        self._status = "in_progress"

    def update_task_progress(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover
        self._status = "in_progress"

    def complete_task(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover
        self._status = "completed"

    def get_task_status(self) -> str:  # pragma: no cover
        return self._status
