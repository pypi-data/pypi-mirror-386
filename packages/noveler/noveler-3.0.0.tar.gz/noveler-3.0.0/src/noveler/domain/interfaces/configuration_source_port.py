# File: src/noveler/domain/interfaces/configuration_source_port.py
# Purpose: Define a port interface for retrieving configuration snapshots and diffs.
# Context: Used by infrastructure integration services to access configuration state.

"""Purpose: Provide configuration source protocols for snapshot and diff operations.
Context: Enables application use cases to inspect configuration changes without coupling to storage details.
Side Effects: None within the protocol definition.
"""

from __future__ import annotations

from typing import Any, Protocol, Tuple


class ConfigurationSourcePort(Protocol):
    """Purpose: Describe configuration snapshot and diff capabilities.

    Side Effects:
        Implementations may read from configuration storage systems.
    """

    def snapshot(self, project_id: str) -> Tuple[dict[str, Any], str]:
        """Purpose: Capture the current configuration snapshot for a project.

        Args:
            project_id: Identifier of the project whose configuration is requested.

        Returns:
            Tuple of (configuration_dict, version_token) where:
                - configuration_dict is the current configuration state.
                - version_token is an opaque token representing this version.

        Side Effects:
            Implementation defined; may read from configuration storage.
        """
        ...

    def diff_since(self, project_id: str, previous_token: str) -> Tuple[dict[str, Any], dict[str, Any]]:
        """Purpose: Compute configuration changes since a previous snapshot.

        Args:
            project_id: Identifier of the project.
            previous_token: Token representing the previous snapshot version.

        Returns:
            Tuple of (old_config, new_config) representing configuration changes.

        Side Effects:
            Implementation defined; may read from configuration storage.
        """
        ...
