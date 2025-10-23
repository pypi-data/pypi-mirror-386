"""Infrastructure.adapters.configuration_service_adapter
Where: Infrastructure adapter bridging domain configuration services to concrete implementations.
What: Wraps configuration loading and provides domain-compliant interfaces.
Why: Allows domain code to remain decoupled from infrastructure-specific configuration logic.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""Adapter that exposes configuration services through a unified interface.

It bridges the legacy `ConfigurationManager` and the expected
`IConfigurationService` contract.
"""


from typing import Any


class ConfigurationServiceAdapter:
    """Wrap a legacy configuration manager to match the expected interface."""

    def __init__(self) -> None:
        """Initialize the adapter and resolve the underlying manager."""
        try:
            from noveler.infrastructure.factories.configuration_service_factory import get_configuration_manager

            self._wrapped_manager = get_configuration_manager()
        except ImportError:
            # フォールバック実装
            self._wrapped_manager = None
            self._fallback_config = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a configuration value from the wrapped manager.

        Args:
            key: Dot-delimited configuration key.
            default: Value returned when the key cannot be resolved.

        Returns:
            Any: Stored configuration value or the provided default.
        """
        if self._wrapped_manager and hasattr(self._wrapped_manager, "get"):
            return self._wrapped_manager.get(key, default)
        return self._fallback_config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Persist a configuration value.

        Args:
            key: Dot-delimited configuration key.
            value: New value to persist.
        """
        if self._wrapped_manager and hasattr(self._wrapped_manager, "set"):
            self._wrapped_manager.set(key, value)
        else:
            self._fallback_config[key] = value

    def get_project_root(self) -> str:
        """Return the project root path from configuration.

        Returns:
            str: Configured project root; defaults to ``'.'``.
        """
        if self._wrapped_manager and hasattr(self._wrapped_manager, "get"):
            return self._wrapped_manager.get("project_root", ".")
        return self._fallback_config.get("project_root", ".")

    def get_environment(self) -> str:
        """Return the current execution environment label.

        Returns:
            str: Environment name such as ``"development"``.
        """
        if self._wrapped_manager and hasattr(self._wrapped_manager, "get"):
            return self._wrapped_manager.get("environment", "development")
        return self._fallback_config.get("environment", "development")

    def get_api_config(self, service_name: str) -> dict[str, Any]:
        """Retrieve API configuration for a specific service.

        Args:
            service_name: Logical API service identifier.

        Returns:
            dict[str, Any]: Service configuration dictionary.
        """
        if self._wrapped_manager and hasattr(self._wrapped_manager, "get"):
            return self._wrapped_manager.get(f"api.{service_name}", {})
        return self._fallback_config.get(f"api.{service_name}", {})

    def get_database_config(self) -> dict[str, Any]:
        """Return database connection configuration details.

        Returns:
            dict[str, Any]: Database configuration dictionary.
        """
        if self._wrapped_manager and hasattr(self._wrapped_manager, "get"):
            return self._wrapped_manager.get("database", {})
        return self._fallback_config.get("database", {})

    def get_logging_config(self) -> dict[str, Any]:
        """Return logging configuration settings.

        Returns:
            dict[str, Any]: Logging configuration dictionary.
        """
        if self._wrapped_manager and hasattr(self._wrapped_manager, "get"):
            return self._wrapped_manager.get("logging", {})
        return self._fallback_config.get("logging", {})

    def get_feature_flags(self) -> dict[str, bool]:
        """Return all known feature flags.

        Returns:
            dict[str, bool]: Mapping of feature names to their enabled state.
        """
        if self._wrapped_manager and hasattr(self._wrapped_manager, "get"):
            return self._wrapped_manager.get("features", {})
        return self._fallback_config.get("features", {})

    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check whether a particular feature flag is enabled.

        Args:
            feature_name: Name of the feature flag to inspect.

        Returns:
            bool: ``True`` when the feature flag evaluates to enabled.
        """
        features = self.get_feature_flags()
        return features.get(feature_name, False)

    def reload(self) -> None:
        """Trigger a reload of the underlying configuration store."""
        if self._wrapped_manager and hasattr(self._wrapped_manager, "reload"):
            self._wrapped_manager.reload()
