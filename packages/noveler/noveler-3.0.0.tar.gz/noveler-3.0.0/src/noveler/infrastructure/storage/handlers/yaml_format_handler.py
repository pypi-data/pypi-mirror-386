# File: src/noveler/infrastructure/storage/handlers/yaml_format_handler.py
# Purpose: YAML format serialization/deserialization handler
# Context: Infrastructure implementation of IFileFormatHandler for YAML format

from typing import Any

import yaml

from noveler.domain.interfaces.i_file_format_handler import IFileFormatHandler


class YamlFormatHandler(IFileFormatHandler):
    """YAML format handler implementation.

    Responsibilities:
    - Serialize Python dict to YAML string
    - Deserialize YAML string to Python dict
    - Handle metadata via "_meta" key convention

    Design Decisions:
    - Metadata stored as {"content": {...}, "_meta": {...}} for dict content
    - Use safe_load for security (prevents arbitrary code execution)
    - Use allow_unicode=True for international characters
    - Use sort_keys=False to preserve key order
    - Use indent=2 for readability

    Error Handling:
    - YAMLError → ValueError with context
    - Type errors → ValueError with type info
    """

    def serialize(self, content: Any, metadata: dict | None = None) -> str:
        """Convert Python object to YAML string.

        Args:
            content: Python object to serialize (dict, list, primitive types)
            metadata: Optional metadata to include in YAML

        Returns:
            YAML string with human-readable formatting

        Raises:
            ValueError: If content is not YAML-serializable
            TypeError: If content type cannot be converted to YAML

        Side Effects:
            None (pure function)
        """
        try:
            # Integrate metadata into serialization
            save_data = content
            if isinstance(content, dict) and metadata:
                # Metadata stored as "_meta" key to separate from content
                save_data = {**content, "_meta": metadata}

            # Serialize to YAML with human-readable formatting
            return yaml.dump(
                save_data,
                default_flow_style=False,  # Block style (multiline)
                allow_unicode=True,  # Preserve Unicode characters
                sort_keys=False,  # Maintain insertion order
                indent=2,  # Pretty print
            )

        except yaml.YAMLError as e:
            msg = f"Failed to serialize content to YAML: {e}"
            raise ValueError(msg) from e
        except (TypeError, ValueError) as e:
            msg = f"Failed to serialize content to YAML: {e}"
            raise ValueError(msg) from e

    def deserialize(self, data: str | bytes) -> tuple[Any, dict | None]:
        """Convert YAML string to Python object with metadata.

        Args:
            data: YAML string or bytes

        Returns:
            Tuple of (content, metadata)
            - content: Deserialized Python object (dict keys "_meta" removed)
            - metadata: Extracted "_meta" dict or empty dict

        Raises:
            ValueError: If data is not valid YAML

        Side Effects:
            None (pure function)
        """
        try:
            # Parse YAML using safe_load (security best practice)
            parsed_data = yaml.safe_load(data)

            # Extract metadata if present
            if isinstance(parsed_data, dict) and "_meta" in parsed_data:
                metadata = parsed_data["_meta"]
                content = {k: v for k, v in parsed_data.items() if k != "_meta"}
                return content, metadata

            # No metadata found
            return parsed_data, {}

        except yaml.YAMLError as e:
            msg = f"Failed to deserialize YAML data: {e}"
            raise ValueError(msg) from e

    def get_supported_extensions(self) -> list[str]:
        """Return supported file extensions for YAML format.

        Returns:
            List containing [".yaml", ".yml"]

        Side Effects:
            None (pure function)
        """
        return [".yaml", ".yml"]
