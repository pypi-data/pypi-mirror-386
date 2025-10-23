# File: src/noveler/domain/repositories/check_state_repository.py
# Purpose: Repository protocols for Progressive Check state management
# Context: Phase 5 - Separate I/O from Domain layer

"""Repository protocols for Progressive Check state persistence.

This module defines Protocol interfaces for session state, manifest,
and step I/O operations. Concrete implementations are in Infrastructure layer.
"""

from pathlib import Path
from typing import Any, Protocol


class IStateRepository(Protocol):
    """Session state persistence interface.

    Responsibilities:
        - Load session state from storage
        - Save session state to storage
        - Check state existence

    Implementation:
        - FileStateRepository: File-based JSON storage
        - InMemoryStateRepository: Dict-based testing storage
    """

    def load_state(self, session_id: str, episode_number: int) -> dict[str, Any] | None:
        """Load session state.

        Args:
            session_id: Session ID (e.g., "EP001_202510041230")
            episode_number: Episode number (e.g., 1)

        Returns:
            Session state dict if found, None otherwise

        Side Effects:
            - Reads from storage
            - May log warnings if state corrupted
        """
        ...

    def save_state(self, session_id: str, episode_number: int, state: dict[str, Any]) -> None:
        """Save session state.

        Args:
            session_id: Session ID
            episode_number: Episode number
            state: State dict to save

        Side Effects:
            - Writes to storage
            - Updates last_updated timestamp
            - Creates directories if needed
            - May raise on I/O errors
        """
        ...

    def state_exists(self, session_id: str, episode_number: int) -> bool:
        """Check if state exists.

        Args:
            session_id: Session ID
            episode_number: Episode number

        Returns:
            True if state file exists, False otherwise

        Side Effects:
            - Checks storage existence
        """
        ...


class IManifestRepository(Protocol):
    """Manifest persistence interface.

    Responsibilities:
        - Load session manifest from storage
        - Save session manifest to storage
        - Check manifest existence

    Manifest Structure:
        {
            "session_id": str,
            "episode_number": int,
            "current_step": int,
            "completed_steps": list[dict],
            "template_version_set": dict[str, dict],
            "target_length": dict[str, int],
            "last_updated": str (ISO8601),
        }
    """

    def load_manifest(self, session_id: str) -> dict[str, Any] | None:
        """Load manifest.

        Args:
            session_id: Session ID

        Returns:
            Manifest dict if found, None otherwise

        Side Effects:
            - Reads from storage
            - May log warnings if manifest corrupted
        """
        ...

    def save_manifest(self, session_id: str, manifest: dict[str, Any]) -> None:
        """Save manifest.

        Args:
            session_id: Session ID
            manifest: Manifest dict to save

        Side Effects:
            - Writes to storage
            - Updates last_updated timestamp
            - Creates directories if needed
            - May raise on I/O errors
        """
        ...

    def manifest_exists(self, session_id: str) -> bool:
        """Check if manifest exists.

        Args:
            session_id: Session ID

        Returns:
            True if manifest file exists, False otherwise

        Side Effects:
            - Checks storage existence
        """
        ...


class IStepIORepository(Protocol):
    """Step input/output persistence interface.

    Responsibilities:
        - Save step input data
        - Save step output data
        - Generate timestamped filenames to avoid overwrite

    File Naming:
        - Input: EP{episode:04d}_step{step:02d}_{timestamp}_input.json
        - Output: EP{episode:04d}_step{step:02d}_{timestamp}_output.json
    """

    def save_step_input(
        self,
        session_id: str,
        episode_number: int,
        step_id: int,
        input_data: dict[str, Any]
    ) -> Path:
        """Save step input data.

        Args:
            session_id: Session ID
            episode_number: Episode number
            step_id: Step ID (1-12)
            input_data: Input data dict

        Returns:
            Path to saved input file

        Side Effects:
            - Writes JSON file to storage
            - Generates timestamp for filename
            - Creates directories if needed
        """
        ...

    def save_step_output(
        self,
        session_id: str,
        episode_number: int,
        step_id: int,
        output_data: dict[str, Any]
    ) -> Path:
        """Save step output data.

        Args:
            session_id: Session ID
            episode_number: Episode number
            step_id: Step ID (1-12)
            output_data: Output data dict

        Returns:
            Path to saved output file

        Side Effects:
            - Writes JSON file to storage
            - Generates timestamp for filename
            - Creates directories if needed
        """
        ...
