# File: src/noveler/infrastructure/repositories/progressive_check/file_state_repository.py
# Purpose: File-based implementations of state repository protocols
# Context: Phase 5 - Infrastructure layer I/O implementations

"""File-based state repository implementations.

Provides file-based persistence for:
- Session state (FileStateRepository)
- Session manifest (FileManifestRepository)
- Step input/output (FileStepIORepository)
"""

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from noveler.domain.interfaces.logger_interface import ILogger, NullLogger


class FileStateRepository:
    """File-based session state persistence.

    Implementation of IStateRepository protocol using JSON files.

    File Structure:
        .noveler/checks/{session_id}/{session_id}_session_state.json

    Thread Safety:
        - Not thread-safe (single-writer assumption)
        - File writes are atomic (write + rename pattern not used)
    """

    def __init__(self, project_root: Path, logger: ILogger | None = None):
        """Initialize file state repository.

        Args:
            project_root: Project root directory
            logger: Optional logger (defaults to NullLogger)
        """
        self.project_root = project_root
        self.checks_root = project_root / ".noveler" / "checks"
        self.logger = logger or NullLogger()

    def load_state(self, session_id: str, episode_number: int) -> dict[str, Any] | None:
        """Load session state from JSON file.

        Args:
            session_id: Session ID (e.g., "EP001_202510041230")
            episode_number: Episode number (not used in current implementation)

        Returns:
            Session state dict if found and valid, None otherwise

        Side Effects:
            - Reads from file system
            - Logs warning if state corrupted
        """
        state_file = self._get_state_file_path(session_id)
        if not state_file.exists():
            return None

        try:
            with state_file.open("r", encoding="utf-8") as f:
                state = json.load(f)
                if not isinstance(state, dict):
                    self.logger.warning(f"Invalid state format (not dict): {state_file}")
                    return None
                return state
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse state JSON: {state_file}, error: {e}")
            return None
        except Exception as e:
            self.logger.warning(f"Failed to load state: {state_file}, error: {e}")
            return None

    def save_state(self, session_id: str, episode_number: int, state: dict[str, Any]) -> None:
        """Save session state to JSON file.

        Args:
            session_id: Session ID
            episode_number: Episode number (not used in current implementation)
            state: State dict to save

        Side Effects:
            - Writes to file system
            - Updates last_updated timestamp
            - Creates parent directories if needed
            - Also saves session-specific state file (for backward compatibility)

        Raises:
            OSError: If file write fails
            ValueError: If state cannot be serialized to JSON
        """
        state_file = self._get_state_file_path(session_id)
        state_file.parent.mkdir(parents=True, exist_ok=True)

        # Update timestamp
        state["last_updated"] = datetime.now(timezone.utc).isoformat()

        try:
            # Save main state file
            with state_file.open("w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False, default=self._json_default)

            # Save session-specific state file (backward compatibility)
            session_state_file = state_file.parent / f"{session_id}_session_state.json"
            with session_state_file.open("w", encoding="utf-8") as sf:
                json.dump(
                    state | {"session_id": session_id},
                    sf,
                    ensure_ascii=False,
                    indent=2,
                    default=self._json_default,
                )
        except Exception as e:
            self.logger.error(f"Failed to save state: {state_file}, error: {e}")
            raise

    def state_exists(self, session_id: str, episode_number: int) -> bool:
        """Check if state file exists.

        Args:
            session_id: Session ID
            episode_number: Episode number (not used)

        Returns:
            True if state file exists, False otherwise
        """
        return self._get_state_file_path(session_id).exists()

    def _get_state_file_path(self, session_id: str) -> Path:
        """Get state file path for session.

        Args:
            session_id: Session ID

        Returns:
            Path to state file
        """
        return self.checks_root / session_id / f"{session_id}_session_state.json"

    @staticmethod
    def _json_default(o: Any) -> Any:
        """JSON serialization fallback for non-standard types.

        Args:
            o: Object to serialize

        Returns:
            Serializable representation of object
        """
        try:
            if is_dataclass(o):
                return asdict(o)
            if hasattr(o, "model_dump") and callable(o.model_dump):
                return o.model_dump()
            if hasattr(o, "to_dict") and callable(o.to_dict):
                return o.to_dict()
            if hasattr(o, "__dict__"):
                return {k: str(v) for k, v in o.__dict__.items()}
        except Exception:
            pass
        return str(o)


class FileManifestRepository:
    """File-based manifest persistence.

    Implementation of IManifestRepository protocol using JSON files.

    File Structure:
        .noveler/checks/{session_id}/manifest.json
    """

    def __init__(self, project_root: Path, logger: ILogger | None = None):
        """Initialize file manifest repository.

        Args:
            project_root: Project root directory
            logger: Optional logger (defaults to NullLogger)
        """
        self.project_root = project_root
        self.checks_root = project_root / ".noveler" / "checks"
        self.logger = logger or NullLogger()

    def load_manifest(self, session_id: str) -> dict[str, Any] | None:
        """Load manifest from JSON file.

        Args:
            session_id: Session ID

        Returns:
            Manifest dict if found and valid, None otherwise

        Side Effects:
            - Reads from file system
            - Logs warning if manifest corrupted
        """
        manifest_path = self._get_manifest_path(session_id)
        if not manifest_path.exists():
            return None

        try:
            with manifest_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    self.logger.warning(f"Invalid manifest format (not dict): {manifest_path}")
                    return None
                return data
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse manifest JSON: {manifest_path}, error: {e}")
            return None
        except Exception as e:
            self.logger.warning(f"Failed to load manifest: {manifest_path}, error: {e}")
            return None

    def save_manifest(self, session_id: str, manifest: dict[str, Any]) -> None:
        """Save manifest to JSON file.

        Args:
            session_id: Session ID
            manifest: Manifest dict to save

        Side Effects:
            - Writes to file system
            - Updates last_updated timestamp
            - Creates parent directories if needed

        Raises:
            OSError: If file write fails
            ValueError: If manifest cannot be serialized to JSON
        """
        manifest_path = self._get_manifest_path(session_id)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)

        # Update timestamp
        manifest["last_updated"] = datetime.now(timezone.utc).isoformat()

        try:
            with manifest_path.open("w", encoding="utf-8") as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save manifest: {manifest_path}, error: {e}")
            raise

    def manifest_exists(self, session_id: str) -> bool:
        """Check if manifest file exists.

        Args:
            session_id: Session ID

        Returns:
            True if manifest file exists, False otherwise
        """
        return self._get_manifest_path(session_id).exists()

    def _get_manifest_path(self, session_id: str) -> Path:
        """Get manifest file path for session.

        Args:
            session_id: Session ID

        Returns:
            Path to manifest file
        """
        return self.checks_root / session_id / "manifest.json"


class FileStepIORepository:
    """File-based step I/O persistence.

    Implementation of IStepIORepository protocol using timestamped JSON files.

    File Naming:
        - Input: EP{episode:04d}_step{step:02d}_{timestamp}_input.json
        - Output: EP{episode:04d}_step{step:02d}_{timestamp}_output.json
    """

    def __init__(self, project_root: Path, logger: ILogger | None = None):
        """Initialize file step I/O repository.

        Args:
            project_root: Project root directory
            logger: Optional logger (defaults to NullLogger)
        """
        self.project_root = project_root
        self.checks_root = project_root / ".noveler" / "checks"
        self.logger = logger or NullLogger()

    def save_step_input(
        self,
        session_id: str,
        episode_number: int,
        step_id: int,
        input_data: dict[str, Any]
    ) -> Path:
        """Save step input data to timestamped JSON file.

        Args:
            session_id: Session ID
            episode_number: Episode number
            step_id: Step ID (1-12)
            input_data: Input data dict

        Returns:
            Path to saved input file

        Side Effects:
            - Writes JSON file to file system
            - Generates timestamp for filename
            - Creates parent directories if needed
        """
        io_dir = self._get_io_dir(session_id)
        io_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        filename = f"EP{episode_number:04d}_step{step_id:02d}_{timestamp}_input.json"
        path = io_dir / filename

        try:
            with path.open("w", encoding="utf-8") as f:
                json.dump({"step_id": step_id, "input": input_data}, f, ensure_ascii=False, indent=2)
            return path
        except Exception as e:
            self.logger.error(f"Failed to save step input: {path}, error: {e}")
            raise

    def save_step_output(
        self,
        session_id: str,
        episode_number: int,
        step_id: int,
        output_data: dict[str, Any]
    ) -> Path:
        """Save step output data to timestamped JSON file.

        Args:
            session_id: Session ID
            episode_number: Episode number
            step_id: Step ID (1-12)
            output_data: Output data dict

        Returns:
            Path to saved output file

        Side Effects:
            - Writes JSON file to file system
            - Generates timestamp for filename
            - Creates parent directories if needed
        """
        io_dir = self._get_io_dir(session_id)
        io_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        filename = f"EP{episode_number:04d}_step{step_id:02d}_{timestamp}_output.json"
        path = io_dir / filename

        try:
            with path.open("w", encoding="utf-8") as f:
                json.dump({"step_id": step_id, "output": output_data}, f, ensure_ascii=False, indent=2)
            return path
        except Exception as e:
            self.logger.error(f"Failed to save step output: {path}, error: {e}")
            raise

    def _get_io_dir(self, session_id: str) -> Path:
        """Get I/O directory for session.

        Args:
            session_id: Session ID

        Returns:
            Path to I/O directory
        """
        return self.checks_root / session_id
