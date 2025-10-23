# File: src/noveler/infrastructure/storage/handlers/json_format_handler.py
# Purpose: JSON format serialization/deserialization handler
# Context: Infrastructure implementation of IFileFormatHandler for JSON format

import json
from typing import Any

from noveler.domain.interfaces.i_file_format_handler import IFileFormatHandler


class JsonFormatHandler(IFileFormatHandler):
    """JSON format handler implementation.

    Responsibilities:
    - Serialize Python dict/list to JSON string
    - Deserialize JSON string to Python object
    - Handle metadata via "_meta" key convention

    Design Decisions:
    - Metadata stored as {"content": {...}, "_meta": {...}} for dict content
    - Use ensure_ascii=False for Unicode support
    - Use indent=2 for human-readable output
    - Use default=str for datetime/non-serializable type handling

    Error Handling:
    - JSONDecodeError → ValueError with context
    - TypeError (non-serializable) → ValueError with type info
    """

    def serialize(self, content: Any, metadata: dict | None = None) -> str:
        """Convert Python object to JSON string.

        Args:
            content: Python object to serialize (dict, list, primitive types)
            metadata: Optional metadata to include in JSON

        Returns:
            JSON string with pretty formatting (indent=2)

        Raises:
            ValueError: If content is not JSON-serializable
            TypeError: If content type cannot be converted to JSON

        Side Effects:
            None (pure function)
        """
        try:
            # Integrate metadata into serialization
            save_data = content
            if isinstance(content, dict) and metadata:
                # Metadata stored as "_meta" key to separate from content
                save_data = {**content, "_meta": metadata}

            # Serialize to JSON with human-readable formatting
            return json.dumps(
                save_data,
                ensure_ascii=False,  # Preserve Unicode characters
                indent=2,  # Pretty print
                default=str,  # Fallback for datetime, Path, etc.
            )

        except (TypeError, ValueError) as e:
            msg = f"Failed to serialize content to JSON: {e}"
            raise ValueError(msg) from e

    def deserialize(self, data: str | bytes) -> tuple[Any, dict | None]:
        """Convert JSON string to Python object with metadata.

        Args:
            data: JSON string or bytes

        Returns:
            Tuple of (content, metadata)
            - content: Deserialized Python object (dict keys "_meta" removed)
            - metadata: Extracted "_meta" dict or empty dict

        Raises:
            ValueError: If data is not valid JSON

        Side Effects:
            None (pure function)
        """
        try:
            # Parse JSON (handles both str and bytes)
            parsed_data = json.loads(data)

            # Extract metadata if present
            if isinstance(parsed_data, dict) and "_meta" in parsed_data:
                metadata = parsed_data["_meta"]
                content = {k: v for k, v in parsed_data.items() if k != "_meta"}
                return content, metadata

            # No metadata found
            return parsed_data, {}

        except json.JSONDecodeError as e:
            msg = f"Failed to deserialize JSON data: {e}"
            raise ValueError(msg) from e

    def get_supported_extensions(self) -> list[str]:
        """Return supported file extensions for JSON format.

        Returns:
            List containing [".json"]

        Side Effects:
            None (pure function)
        """
        return [".json"]
