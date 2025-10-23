"""Infrastructure.adapters.yaml_handler_adapter
Where: Infrastructure adapter responsible for YAML I/O utilities.
What: Loads, saves, and validates YAML documents on behalf of domain services.
Why: Ensures YAML handling is consistent and easily replaceable.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""Adapter that exposes the infrastructure `YAMLHandler` via domain interfaces."""


from pathlib import Path
from typing import Any
import yaml

from noveler.domain.interfaces.yaml_handler import IYamlHandler
from noveler.infrastructure.utils.yaml_utils import YAMLHandler


class YAMLHandlerAdapter(IYamlHandler):
    """Implement the domain `IYamlHandler` using the shared YAML utilities."""

    def load_yaml(self, file_path: str) -> dict[str, Any]:
        """Load YAML content from the provided file path.

        Args:
            file_path: Path string pointing to the YAML file.

        Returns:
            dict[str, Any]: Parsed YAML payload.
        """
        return YAMLHandler.load_yaml(Path(file_path))

    def save_yaml(self, data: dict[str, Any], file_path: str) -> None:
        """Persist data to disk in YAML format.

        Args:
            data: Payload to serialize.
            file_path: Destination path string.
        """
        YAMLHandler.save_yaml(Path(file_path), data, use_formatter=True)

    def format_yaml(self, data: dict[str, Any]) -> str:
        """Serialize a dictionary into a YAML-formatted string.

        Args:
            data: Payload to format.

        Returns:
            str: YAML representation of the payload.
        """
        return yaml.dump(data, allow_unicode=True, default_flow_style=False)
