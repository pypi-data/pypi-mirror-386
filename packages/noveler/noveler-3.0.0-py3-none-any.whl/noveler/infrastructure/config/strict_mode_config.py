# File: src/noveler/infrastructure/config/strict_mode_config.py
# Purpose: Strict mode configuration for gradual fallback removal
# Context: Part of Option A (complete fallback removal) migration strategy

"""Strict mode configuration for infrastructure fallback control.

This module provides granular control over fallback behavior during the
migration from lenient (fallback-allowed) to strict (fallback-forbidden) mode.

The migration follows three stages:
1. OFF: Fallback allowed, no warnings
2. WARNING: Fallback allowed, warnings logged
3. ERROR: Fallback forbidden, exceptions raised

Architecture:
    Domain Layer: StrictLevel enum, StrictModeConfig dataclass
    Infrastructure Layer: Integration with PathServiceAdapter
    Environment: Controlled via NOVELER_STRICT_* environment variables
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum


class StrictLevel(str, Enum):
    """Strictness level for fallback control.

    Attributes:
        OFF: Fallback permitted without warnings (legacy behavior)
        WARNING: Fallback permitted with logged warnings (migration phase)
        ERROR: Fallback forbidden, raises exceptions (target state)
    """

    OFF = "off"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class StrictModeConfig:
    """Configuration for strict mode enforcement.

    Controls fallback behavior at different system layers. During migration,
    each layer can be independently moved through OFF → WARNING → ERROR stages.

    Attributes:
        path_service: Strictness level for Path Service operations
        config_service: Strictness level for Configuration Service operations
        repository_service: Strictness level for repository layer operations
    """

    path_service: StrictLevel = StrictLevel.WARNING  # Default: migration phase
    config_service: StrictLevel = StrictLevel.WARNING  # Default: migration phase
    repository_service: StrictLevel = StrictLevel.WARNING  # Default: migration phase

    @classmethod
    def from_env(cls) -> "StrictModeConfig":
        """Load strict mode configuration from environment variables.

        Environment Variables:
            NOVELER_STRICT_PATH: Path Service strictness (off/warning/error)
            NOVELER_STRICT_CONFIG: Configuration Service strictness (off/warning/error)
            NOVELER_STRICT_REPOSITORY: Repository layer strictness (off/warning/error)

        Returns:
            StrictModeConfig: Configuration instance with env-based overrides

        Examples:
            # Default (WARNING mode)
            config = StrictModeConfig.from_env()

            # Override to ERROR mode for CI
            os.environ["NOVELER_STRICT_PATH"] = "error"
            os.environ["NOVELER_STRICT_CONFIG"] = "error"
            os.environ["NOVELER_STRICT_REPOSITORY"] = "error"
            config = StrictModeConfig.from_env()
        """
        path_strict = os.getenv("NOVELER_STRICT_PATH", "warning").lower()
        config_strict = os.getenv("NOVELER_STRICT_CONFIG", "warning").lower()
        repository_strict = os.getenv("NOVELER_STRICT_REPOSITORY", "warning").lower()

        try:
            path_level = StrictLevel(path_strict)
        except ValueError:
            # Invalid value: default to WARNING with debug hint
            path_level = StrictLevel.WARNING

        try:
            config_level = StrictLevel(config_strict)
        except ValueError:
            config_level = StrictLevel.WARNING

        try:
            repository_level = StrictLevel(repository_strict)
        except ValueError:
            repository_level = StrictLevel.WARNING

        return cls(path_service=path_level, config_service=config_level, repository_service=repository_level)

    def is_path_strict(self) -> bool:
        """Check if Path Service is in ERROR (strict) mode.

        Returns:
            bool: True if fallback is forbidden, False otherwise
        """
        return self.path_service == StrictLevel.ERROR

    def should_warn_on_path_fallback(self) -> bool:
        """Check if Path Service fallback should trigger warnings.

        Returns:
            bool: True if warnings should be logged, False otherwise
        """
        return self.path_service == StrictLevel.WARNING

    def is_config_strict(self) -> bool:
        """Check if Configuration Service is in ERROR (strict) mode.

        Returns:
            bool: True if fallback is forbidden, False otherwise
        """
        return self.config_service == StrictLevel.ERROR

    def should_warn_on_config_fallback(self) -> bool:
        """Check if Configuration Service fallback should trigger warnings.

        Returns:
            bool: True if warnings should be logged, False otherwise
        """
        return self.config_service == StrictLevel.WARNING

    def is_repository_strict(self) -> bool:
        """Check if repository layer is in ERROR (strict) mode.

        Returns:
            bool: True if fallback is forbidden, False otherwise
        """
        return self.repository_service == StrictLevel.ERROR

    def should_warn_on_repository_fallback(self) -> bool:
        """Check if repository fallback should trigger warnings.

        Returns:
            bool: True if warnings should be logged, False otherwise
        """
        return self.repository_service == StrictLevel.WARNING
