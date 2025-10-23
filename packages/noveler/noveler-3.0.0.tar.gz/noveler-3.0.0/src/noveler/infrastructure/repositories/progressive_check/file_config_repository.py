# File: src/noveler/infrastructure/repositories/progressive_check/file_config_repository.py
# Purpose: File-based config repository implementation
# Context: Phase 5 - Infrastructure layer I/O implementations

"""File-based configuration repository implementation.

Provides file-based YAML configuration loading for Progressive Check system.
"""

from pathlib import Path
from typing import Any

import yaml

from noveler.domain.interfaces.logger_interface import ILogger, NullLogger


class FileConfigRepository:
    """File-based configuration loading.

    Implementation of IConfigRepository protocol using YAML files.

    File Location:
        - config/ or templates/ directory (relative to project root)
        - Configurable via config_dirs parameter
    """

    def __init__(
        self,
        project_root: Path,
        config_dirs: list[Path] | None = None,
        logger: ILogger | None = None
    ):
        """Initialize file config repository.

        Args:
            project_root: Project root directory
            config_dirs: List of config directories to search (defaults to [templates/])
            logger: Optional logger (defaults to NullLogger)
        """
        self.project_root = project_root
        self.config_dirs = config_dirs or [project_root / "templates"]
        self.logger = logger or NullLogger()

    def load_config(self, config_name: str) -> dict[str, Any]:
        """Load YAML configuration file.

        Args:
            config_name: Config filename (e.g., "check_tasks.yaml")

        Returns:
            Parsed YAML content as dict

        Raises:
            FileNotFoundError: If config file not found
            ValueError: If YAML parsing fails

        Side Effects:
            - Reads from file system
            - Parses YAML content
            - Logs error if config invalid
        """
        config_path = self._resolve_config_path(config_name)

        if config_path is None:
            msg = f"Config file not found: {config_name} (searched: {self.config_dirs})"
            self.logger.error(msg)
            raise FileNotFoundError(msg)

        try:
            with config_path.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if not isinstance(data, dict):
                    raise ValueError(f"Invalid config format (not dict): {config_path}")
                return data
        except yaml.YAMLError as e:
            msg = f"Failed to parse config YAML: {config_path}, error: {e}"
            self.logger.error(msg)
            raise ValueError(msg) from e
        except Exception as e:
            self.logger.error(f"Failed to load config: {config_path}, error: {e}")
            raise

    def load_check_tasks_config(self) -> dict[str, Any]:
        """Load check_tasks.yaml configuration.

        Convenience method for loading the standard check tasks configuration.
        First searches in project templates/, then falls back to infrastructure config/.

        Returns:
            Parsed check tasks configuration

        Raises:
            FileNotFoundError: If check_tasks.yaml not found
            ValueError: If YAML parsing fails
        """
        # Try templates/ first (project-specific), then infrastructure/config/ (default)
        config_name = "check_tasks.yaml"

        # Add infrastructure config directory as fallback
        # __file__ is in: src/noveler/infrastructure/repositories/progressive_check/file_config_repository.py
        # We need: src/noveler/infrastructure/config
        infra_config_dir = Path(__file__).parent.parent.parent / "config"
        search_dirs = list(self.config_dirs) + [infra_config_dir]

        for config_dir in search_dirs:
            candidate = config_dir / config_name
            if candidate.exists():
                try:
                    with candidate.open(encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                        if not isinstance(data, dict):
                            raise ValueError(f"Invalid config format (not dict): {candidate}")
                        return data
                except yaml.YAMLError as e:
                    msg = f"Failed to parse config YAML: {candidate}, error: {e}"
                    self.logger.error(msg)
                    raise ValueError(msg) from e
                except Exception as e:
                    self.logger.error(f"Failed to load config: {candidate}, error: {e}")
                    raise

        msg = f"Config file not found: {config_name} (searched: {search_dirs})"
        self.logger.error(msg)
        raise FileNotFoundError(msg)

    def config_exists(self, config_name: str) -> bool:
        """Check if configuration file exists.

        Args:
            config_name: Config filename

        Returns:
            True if config file exists, False otherwise
        """
        config_path = self._resolve_config_path(config_name)
        return config_path is not None and config_path.exists()

    def _resolve_config_path(self, config_name: str) -> Path | None:
        """Resolve config name to file path.

        Args:
            config_name: Config filename or relative path

        Returns:
            Resolved Path if config can be found, None otherwise

        Resolution Strategy:
            1. Search each config_dir for config_name
            2. Return first match
            3. Return None if not found
        """
        for config_dir in self.config_dirs:
            candidate = config_dir / config_name
            if candidate.exists():
                return candidate

        return None
