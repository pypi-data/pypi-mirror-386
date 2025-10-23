# File: src/noveler/domain/services/sanitization/content_sanitizer.py
# Purpose: Sanitize values for JSON serialization
# Context: Extracted from ProgressiveCheckManager._sanitize_for_json

import json
from pathlib import Path
from typing import Any


class ContentSanitizer:
    """Content sanitization for JSON serialization (Domain layer - no I/O).

    Responsibilities:
    - Convert non-serializable values to JSON-safe types
    - Recursively sanitize nested structures (dict/list/tuple/set)
    - Handle Path objects, custom objects

    Extracted from:
    - ProgressiveCheckManager._sanitize_for_json (lines 1591-1603)
    """

    @staticmethod
    def sanitize_for_json(value: Any) -> Any:
        """Convert values into JSON serializable structures.

        Args:
            value: Any Python value

        Returns:
            JSON-serializable equivalent:
            - Already serializable → unchanged
            - dict → recursively sanitized dict
            - list/tuple/set → recursively sanitized list
            - Path → str
            - Other → str(value)

        Strategy:
            1. Try json.dumps() - return if successful
            2. Recursively sanitize containers
            3. Convert Path to str
            4. Fallback: str(value)
        """
        # Try direct serialization first
        try:
            json.dumps(value, ensure_ascii=False)
            return value
        except (TypeError, ValueError):
            pass

        # Recursively sanitize containers
        if isinstance(value, dict):
            return {str(k): ContentSanitizer.sanitize_for_json(v) for k, v in value.items()}

        if isinstance(value, (list, tuple, set)):
            return [ContentSanitizer.sanitize_for_json(v) for v in value]

        # Handle Path objects
        if isinstance(value, Path):
            return str(value)

        # Fallback: stringify
        return str(value)
