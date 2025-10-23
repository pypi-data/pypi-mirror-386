# File: src/noveler/domain/services/progressive_check/session_coordinator.py
# Purpose: Session lifecycle management for Progressive Check system
# Context: Extracted from ProgressiveCheckManager (Phase 6 Step 1)

"""Session Coordinator for Progressive Check System.

This module handles all session-related operations including:
- Session initialization and resumption
- State persistence and retrieval
- Session metadata management
- Workflow integration
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from noveler.domain.interfaces.logger_interface import ILogger, NullLogger
from noveler.domain.repositories import IStateRepository, IManifestRepository
from noveler.domain.value_objects.project_time import (
    parse_project_time_iso,
    parse_compact_timestamp,
    project_now,
)


class SessionCoordinator:
    """Manages session lifecycle and state for Progressive Check execution.

    Responsibilities:
    - Create and initialize new sessions
    - Resume existing sessions from persisted state
    - Manage session timestamps and metadata
    - Coordinate state persistence via repositories
    - Integrate with workflow state store when enabled

    Args:
        project_root: Root directory of the project
        episode_number: Episode number for this session
        session_id: Optional session ID (generated if None)
        state_repository: Repository for state persistence
        manifest_repository: Repository for manifest persistence
        logger: Optional logger instance
        workflow_state_store_factory: Optional factory for workflow integration
    """

    def __init__(
        self,
        project_root: Path,
        episode_number: int,
        session_id: str | None,
        state_repository: IStateRepository,
        manifest_repository: IManifestRepository,
        logger: ILogger | None = None,
        workflow_state_store_factory: Any | None = None,
    ) -> None:
        self.project_root = Path(project_root)
        self.episode_number = episode_number
        self.logger = logger or NullLogger()

        # Repositories
        self.state_repo = state_repository
        self.manifest_repo = manifest_repository

        # Session state
        self.session_id = session_id or self._generate_session_id()
        self.session_start_ts: str | None = None
        self.session_start_iso: str | None = None

        # Workflow integration
        self._workflow_state_store_factory = workflow_state_store_factory
        self._workflow_state_store: Any | None = None
        self._workflow_session: Any | None = None

        # I/O directories
        self.checks_root = self.project_root / ".noveler" / "checks"
        self.io_dir = self.checks_root / f"EP{self.episode_number:04d}" / "io"
        self.manifest_path = self.checks_root / f"EP{self.episode_number:04d}" / "manifest.json"

    def _generate_session_id(self) -> str:
        """Generate a unique session ID based on timestamp."""
        now = project_now().datetime
        return now.strftime("%Y%m%d%H%M%S%f")

    def initialize_session(
        self,
        resume: bool = False,
    ) -> dict[str, Any]:
        """Initialize or resume a session.

        Args:
            resume: If True, attempt to resume existing session

        Returns:
            Session state dictionary

        Raises:
            FileNotFoundError: If resume=True but session state not found
        """
        if resume:
            return self._resume_session()
        else:
            return self._start_new_session()

    def _start_new_session(self) -> dict[str, Any]:
        """Start a new session with fresh state."""
        # Load or initialize state
        state = self._load_or_initialize_state()

        # Initialize workflow store if available
        if self._workflow_state_store_factory is not None:
            self._initialize_workflow_store()

        return state

    def _resume_session(self) -> dict[str, Any]:
        """Resume an existing session from persisted state."""
        state = self.state_repo.load_state(self.session_id, self.episode_number)

        if state is None:
            msg = f"Session state not found for session_id={self.session_id}"
            raise FileNotFoundError(msg)

        # Initialize workflow store if available
        if self._workflow_state_store_factory is not None:
            self._initialize_workflow_store()

        return state

    def _load_or_initialize_state(self) -> dict[str, Any]:
        """Load session state or create initial state.

        Returns:
            State dictionary (either loaded or newly created)
        """
        # Try loading existing state
        state = self.state_repo.load_state(self.session_id, self.episode_number)
        if state is not None:
            return state

        # Create initial state if not found
        initial_state = {
            "episode_number": self.episode_number,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "current_step": 1,  # Start from STEP 1
            "completed_steps": [],
            "failed_steps": [],
            "step_results": {},
            "overall_status": "not_started",
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

        self.save_state(initial_state)
        return initial_state

    def save_state(self, state: dict[str, Any]) -> None:
        """Save session state via repository.

        Args:
            state: State dictionary to persist
        """
        self.state_repo.save_state(self.session_id, self.episode_number, state)

    def can_resume_session(self, session_id: str) -> bool:
        """Check if a session can be resumed.

        Args:
            session_id: Session ID to check

        Returns:
            True if session state exists, False otherwise
        """
        return self.state_repo.state_exists(session_id, self.episode_number)

    def get_execution_status(self, current_state: dict[str, Any]) -> dict[str, Any]:
        """Get current execution status.

        Args:
            current_state: Current session state

        Returns:
            Status dictionary with session metadata and progress
        """
        completed = current_state.get("completed_steps", [])
        return {
            "session_id": self.session_id,
            "episode_number": self.episode_number,
            "completed_steps": len(completed),
            "last_completed_step": max(completed) if completed else 0,
            "overall_status": current_state.get("overall_status", "unknown"),
            "progress": self._get_progress_info(current_state),
        }

    def _get_progress_info(self, current_state: dict[str, Any]) -> dict[str, Any]:
        """Calculate progress information.

        Args:
            current_state: Current session state

        Returns:
            Progress dictionary with step counts and percentages
        """
        completed = current_state.get("completed_steps", [])
        failed = current_state.get("failed_steps", [])

        return {
            "completed": len(completed),
            "failed": len(failed),
            "current_step": current_state.get("current_step", 1),
        }

    def ensure_session_start_ts(self, manifest: dict[str, Any]) -> tuple[str, str]:
        """Ensure session start timestamps are resolved and persisted.

        Args:
            manifest: Current manifest dictionary

        Returns:
            Tuple of (compact_timestamp, iso_timestamp)
        """
        if self.session_start_ts and self.session_start_iso:
            return self.session_start_ts, self.session_start_iso

        # Try to use existing values from manifest directly (preserve original timestamps)
        record = manifest.get("first_step_started_at")
        if isinstance(record, dict):
            compact = record.get("compact")
            iso = record.get("iso")
            if isinstance(compact, str) and isinstance(iso, str):
                self.session_start_ts = compact
                self.session_start_iso = iso
                return self.session_start_ts, self.session_start_iso

        # Try to parse from manifest for datetime calculation
        dt = self._parse_session_start_record(record)

        # Fallback to manifest created_at
        if dt is None:
            created_at = manifest.get("created_at")
            if isinstance(created_at, str):
                try:
                    dt = parse_project_time_iso(created_at).datetime
                except ValueError:
                    dt = None

        # Fallback to I/O directory timestamps
        if dt is None and self.io_dir.exists():
            candidates: list[datetime] = []
            for file_path in self.io_dir.glob("*.json"):
                for match in re.findall(r"\d{12,20}", file_path.name):
                    try:
                        candidates.append(parse_compact_timestamp(match).datetime)
                    except ValueError:
                        continue
            if candidates:
                dt = min(candidates)

        # Final fallback to current time
        if dt is None:
            dt = project_now().datetime

        self.session_start_ts = dt.strftime("%Y%m%d%H%M")
        self.session_start_iso = dt.isoformat()

        # Persist to manifest
        new_record = manifest.setdefault("first_step_started_at", {})
        new_record["compact"] = self.session_start_ts
        new_record["iso"] = self.session_start_iso

        self.manifest_repo.save_manifest(self.session_id, manifest)

        return self.session_start_ts, self.session_start_iso

    def _parse_session_start_record(
        self, record: dict[str, Any] | None
    ) -> datetime | None:
        """Parse session start record from manifest.

        Args:
            record: Session start record dictionary

        Returns:
            Parsed datetime or None if parsing fails
        """
        if not isinstance(record, dict):
            return None

        iso_str = record.get("iso")
        if isinstance(iso_str, str):
            try:
                return parse_project_time_iso(iso_str).datetime
            except ValueError:
                pass

        compact_str = record.get("compact")
        if isinstance(compact_str, str):
            try:
                return parse_compact_timestamp(compact_str).datetime
            except ValueError:
                pass

        return None

    def hydrate_session_start_from_manifest(self, manifest: dict[str, Any]) -> None:
        """Hydrate session start timestamps from manifest.

        Args:
            manifest: Manifest dictionary containing session metadata
        """
        record = manifest.get("first_step_started_at")
        if not isinstance(record, dict):
            return

        if "compact" in record:
            self.session_start_ts = record["compact"]
        if "iso" in record:
            self.session_start_iso = record["iso"]

    def merge_previous_session_completion(
        self,
        current_state: dict[str, Any],
        manifest: dict[str, Any],
    ) -> dict[str, Any]:
        """Merge completion info from previous session into current state.

        Args:
            current_state: Current session state
            manifest: Manifest with historical data

        Returns:
            Updated state with merged completion info
        """
        previous_completed = manifest.get("previous_session_completed_steps", [])
        if not isinstance(previous_completed, list):
            return current_state

        # Merge with current completed steps
        current_completed = set(current_state.get("completed_steps", []))
        merged_completed = sorted(current_completed | set(previous_completed))

        current_state["completed_steps"] = merged_completed

        # Update step results from manifest history if available
        manifest_history = manifest.get("step_execution_history", {})
        if isinstance(manifest_history, dict):
            step_results = current_state.setdefault("step_results", {})
            for step_id_str, history_entry in manifest_history.items():
                if step_id_str not in step_results and isinstance(history_entry, dict):
                    step_results[step_id_str] = {
                        "status": history_entry.get("status", "completed"),
                        "result": history_entry.get("result", {}),
                    }

        return current_state

    # Workflow integration methods

    def _initialize_workflow_store(self) -> None:
        """Initialize workflow state store if factory is available."""
        if self._workflow_state_store_factory is None:
            return

        try:
            self._workflow_state_store = self._workflow_state_store_factory()
        except Exception as e:
            self.logger.warning(f"Failed to initialize workflow store: {e}")
            self._workflow_state_store = None

    def ensure_workflow_session(self) -> Any | None:
        """Ensure workflow session exists and return it.

        Returns:
            Workflow session object or None if not available
        """
        if self._workflow_state_store is None:
            return None

        if self._workflow_session is not None:
            return self._workflow_session

        try:
            # Create or get workflow session
            self._workflow_session = self._workflow_state_store.create_session(
                session_id=self.session_id,
                episode_number=self.episode_number,
            )
            return self._workflow_session
        except Exception as e:
            self.logger.warning(f"Failed to create workflow session: {e}")
            return None

    def record_step_execution_to_workflow_store(
        self,
        step_id: int,
        execution_data: dict[str, Any],
    ) -> None:
        """Record step execution to workflow state store.

        Args:
            step_id: Step ID
            execution_data: Execution data to record
        """
        workflow_session = self.ensure_workflow_session()
        if workflow_session is None:
            return

        try:
            workflow_session.record_step_execution(
                step_id=step_id,
                data=execution_data,
            )
        except Exception as e:
            self.logger.warning(f"Failed to record step execution to workflow store: {e}")
