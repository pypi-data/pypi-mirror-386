#!/usr/bin/env python3
"""Compatibility adapter that exposes legacy configuration helpers."""

from pathlib import Path

from noveler.infrastructure.repositories.configuration_repository import ConfigurationRepository

# グローバルなリポジトリインスタンス(シングルトン)
_repository = ConfigurationRepository()


def find_project_config(start_path: Path | str | None = None) -> Path | None:
    """Locate the project configuration YAML using the legacy contract.

    Args:
        start_path: Optional directory to anchor the search.

    Returns:
        Path | None: Resolved configuration file path when found.
    """
    return _repository.find_project_config(start_path)


def load_project_config(config_path: Path | str | None = None) -> dict:
    """Load project configuration using the legacy interface.

    Args:
        config_path: Optional explicit path to the configuration file.

    Returns:
        dict: Parsed configuration payload.
    """
    return _repository.load_project_config(config_path)


def get_project_paths() -> dict[str, str]:
    """Return project path metadata via the legacy interface.

    Returns:
        dict[str, str]: Mapping of notable project path identifiers.
    """
    return _repository.get_project_paths()


def setup_environment() -> None:
    """Populate environment variables using legacy semantics."""
    return _repository.setup_environment()


def get_project_info() -> dict:
    """Fetch structured project information using the legacy API.

    Returns:
        dict: Project metadata exposed to legacy callers.
    """
    return _repository.get_project_info()


def get_ncode() -> str | None:
    """Retrieve the project NCODE identifier if available."""
    return _repository.get_ncode()


def get_config(key: str | None = None, default: object = None) -> object:
    """Return configuration values using legacy hierarchical lookup.

    Args:
        key: Dot-delimited path to the desired setting.
        default: Value returned when the key cannot be resolved.

    Returns:
        object: Retrieved configuration value or the provided default.
    """
    return _repository.get_config(key, default)


def get_author_info() -> dict[str, str]:
    """Return author metadata using the legacy interface.

    Returns:
        dict[str, str]: Author attributes such as name and contact.
    """
    return _repository.get_author_info()


def get_quality_threshold() -> int:
    """Read the quality threshold expected by the legacy workflow.

    Returns:
        int: Threshold value used to interpret quality scores.
    """
    return _repository.get_quality_threshold()
