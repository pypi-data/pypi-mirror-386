# File: src/noveler/domain/repositories/config_repository.py
# Purpose: Repository protocol for configuration file loading
# Context: Phase 5 - Separate I/O from Domain layer

"""Repository protocol for YAML configuration loading.

This module defines the Protocol interface for loading YAML configuration files
used by ProgressiveCheckManager. Concrete implementations are in Infrastructure layer.
"""

from typing import Any, Protocol


class IConfigRepository(Protocol):
    """Configuration file loading interface.

    Responsibilities:
        - Load YAML configuration files
        - Check configuration existence
        - Parse YAML content to dict

    Config Types:
        - check_tasks.yaml: Task definitions
        - Custom configs as needed

    File Location:
        - config/ or templates/ directory (configurable per implementation)
    """

    def load_config(self, config_name: str) -> dict[str, Any]:
        """Load YAML configuration file.

        Args:
            config_name: Config filename (e.g., "check_tasks.yaml")
                or config path relative to config directory

        Returns:
            Parsed YAML content as dict

        Raises:
            FileNotFoundError: If config file not found
            ValueError: If YAML parsing fails

        Side Effects:
            - Reads from file system
            - Parses YAML content
            - May log errors if config invalid

        Examples:
            >>> repo.load_config("check_tasks.yaml")
            {"tasks": [...], ...}

            >>> repo.load_config("nonexistent.yaml")
            FileNotFoundError: Config file not found: nonexistent.yaml
        """
        ...

    def config_exists(self, config_name: str) -> bool:
        """Check if configuration file exists.

        Args:
            config_name: Config filename or relative path

        Returns:
            True if config file exists, False otherwise

        Side Effects:
            - Checks file system existence

        Examples:
            >>> repo.config_exists("check_tasks.yaml")
            True

            >>> repo.config_exists("nonexistent.yaml")
            False
        """
        ...
