# File: src/noveler/domain/interfaces/i_file_format_handler.py
# Purpose: Define format conversion contract for file serialization/deserialization
# Context: Separates format conversion from file I/O operations (SOLID: SRP, ISP, DIP)

from abc import ABC, abstractmethod
from typing import Any


class IFileFormatHandler(ABC):
    """Format conversion handler interface.

    Responsibilities:
    - Convert Python objects to format-specific strings/bytes (serialize)
    - Convert format-specific data to Python objects (deserialize)
    - Provide format detection capability (get_supported_extensions)

    Design Constraints:
    - NO file I/O operations allowed (Path objects prohibited in signatures)
    - Pure transformation functions only (no side effects)
    - Metadata integrated into serialization (not separate files)

    SOLID Compliance:
    - SRP: Single responsibility (format conversion only)
    - OCP: Open for extension (new formats via new handlers)
    - LSP: All implementations substitutable
    - ISP: Minimal interface (3 methods)
    - DIP: High-level modules depend on this abstraction
    """

    @abstractmethod
    def serialize(self, content: Any, metadata: dict | None = None) -> str | bytes:
        """Convert Python object to format-specific string or bytes.

        Args:
            content: Python object to serialize (dict, list, str, etc.)
            metadata: Optional metadata to include in serialization

        Returns:
            Serialized data as string or bytes

        Raises:
            ValueError: If content is not serializable to target format
            TypeError: If content type is incompatible with format

        Side Effects:
            None (pure function)

        Preconditions:
            - content must be serializable to target format
            - metadata (if provided) must be dict

        Postconditions:
            - Returns valid format-specific representation
            - Round-trip: deserialize(serialize(x)) == x (for serializable x)
        """

    @abstractmethod
    def deserialize(self, data: str | bytes) -> tuple[Any, dict | None]:
        """Convert format-specific data to Python object with metadata.

        Args:
            data: Serialized data as string or bytes

        Returns:
            Tuple of (content, metadata)
            - content: Deserialized Python object
            - metadata: Extracted metadata dict or None

        Raises:
            ValueError: If data is not valid format
            TypeError: If data type is incompatible

        Side Effects:
            None (pure function)

        Preconditions:
            - data must be valid format string/bytes

        Postconditions:
            - Returns tuple with content and metadata
            - Round-trip: serialize(content, meta) → deserialize() → (content, meta)
        """

    @abstractmethod
    def get_supported_extensions(self) -> list[str]:
        """Return list of file extensions this handler supports.

        Returns:
            List of extensions with leading dot (e.g., [".json", ".jsonl"])

        Side Effects:
            None (pure function)

        Preconditions:
            None

        Postconditions:
            - Returns non-empty list of lowercase extensions
            - All extensions start with "."
        """
