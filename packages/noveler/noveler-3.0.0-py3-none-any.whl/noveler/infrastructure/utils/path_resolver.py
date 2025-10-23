"""Path resolution utilities for YAML/JSON data structures.

File: src/noveler/infrastructure/utils/path_resolver.py
Purpose: Provides dotted path resolution with array wildcard support for validators/adapters.
Context: Implements SPEC-YAML-021 for array addressing (v2.1).

Key Features:
- Dotted path resolution: metadata.title
- Array indexing: episodes[0].title
- Array wildcards: episodes[*].word_count
- Nested wildcards: chapters[*].sections[*].hook
- Numeric aggregation: min/max/avg
"""

import re
from dataclasses import dataclass
from itertools import chain
from statistics import mean
from typing import Any, Literal

from noveler.infrastructure.logging.unified_logger import get_logger

logger = get_logger(__name__)


class PathResolutionError(Exception):
    """Raised when path resolution fails."""

    pass


class AggregationError(Exception):
    """Raised when aggregation encounters invalid data."""

    pass


@dataclass(frozen=True)
class PathSegment:
    """Represents a single segment in a dotted path.

    Args:
        key: The key name (e.g., "episodes", "title").
        is_wildcard: True if this segment uses array wildcard [*].
        index: Specific array index (0-based) if provided.

    Examples:
        "episodes" → PathSegment(key="episodes", is_wildcard=False, index=None)
        "episodes[*]" → PathSegment(key="episodes", is_wildcard=True, index=None)
        "episodes[0]" → PathSegment(key="episodes", is_wildcard=False, index=0)
    """

    key: str
    is_wildcard: bool = False
    index: int | None = None

    def __post_init__(self) -> None:
        """Validate segment invariants."""
        if self.is_wildcard and self.index is not None:
            raise ValueError("Wildcard and specific index are mutually exclusive")


class PathResolver:
    """Resolves dotted paths in YAML/JSON data structures.

    Implements SPEC-YAML-021 for array addressing with wildcard support.

    Design Principles:
    - Stateless: all methods are static
    - Fail-fast: raises exceptions for invalid paths
    - Logging: warns on non-numeric elements during aggregation

    Usage:
        resolver = PathResolver()
        value = resolver.resolve(data, "episodes[0].title")
        values = resolver.resolve(data, "episodes[*].word_count")
        avg_wc = resolver.aggregate(data, "episodes[*].word_count", "avg")
    """

    # Pattern for parsing array notation: key[index] or key[*]
    # Note: Negative indices are rejected separately after matching
    ARRAY_PATTERN = re.compile(r"^([^\[]+)(?:\[(-?\d+|\*)\])?$")

    @staticmethod
    def parse_path(path: str) -> list[PathSegment]:
        """Parse a dotted path string into segments.

        Args:
            path: Dotted path string (e.g., "episodes[*].sections[0].hook").

        Returns:
            List of PathSegment objects.

        Raises:
            ValueError: If path syntax is invalid.

        Examples:
            "metadata.title" → [PathSegment(key="metadata"), PathSegment(key="title")]
            "episodes[*].word_count" → [PathSegment(key="episodes", is_wildcard=True), PathSegment(key="word_count")]
            "episodes[0].title" → [PathSegment(key="episodes", index=0), PathSegment(key="title")]
        """
        if not path or not path.strip():
            raise ValueError("Path cannot be empty")

        segments: list[PathSegment] = []
        parts = path.split(".")

        for part in parts:
            match = PathResolver.ARRAY_PATTERN.match(part)
            if not match:
                raise ValueError(f"Invalid path segment: {part}")

            key = match.group(1)
            array_spec = match.group(2)

            if array_spec is None:
                # Simple key without array notation
                segments.append(PathSegment(key=key))
            elif array_spec == "*":
                # Wildcard: key[*]
                segments.append(PathSegment(key=key, is_wildcard=True))
            else:
                # Specific index: key[0]
                # Check for negative index before parsing
                if array_spec.startswith("-"):
                    raise ValueError(f"Negative indices not supported: {part}")

                try:
                    index = int(array_spec)
                    segments.append(PathSegment(key=key, index=index))
                except ValueError:
                    raise ValueError(f"Invalid array index in segment: {part}")

        return segments

    @staticmethod
    def resolve(data: dict | list, path: str) -> Any:
        """Resolve a dotted path and return the value(s).

        Args:
            data: The data structure to traverse (dict or list).
            path: Dotted path string.

        Returns:
            - Single value if no wildcard is used
            - List of values if wildcard is used
            - List may be nested if multiple wildcards are used

        Raises:
            PathResolutionError: If path cannot be resolved.

        Examples:
            resolve({"a": {"b": 1}}, "a.b") → 1
            resolve({"items": [{"x": 1}, {"x": 2}]}, "items[*].x") → [1, 2]
            resolve({"items": [{"x": 1}]}, "items[0].x") → 1
        """
        try:
            segments = PathResolver.parse_path(path)
        except ValueError as e:
            raise PathResolutionError(f"Failed to parse path '{path}': {e}") from e

        return PathResolver._traverse(data, segments, path)

    @staticmethod
    def _traverse(current: Any, segments: list[PathSegment], original_path: str) -> Any:
        """Recursively traverse data structure following path segments.

        Args:
            current: Current position in data structure.
            segments: Remaining path segments to traverse.
            original_path: Original path string (for error messages).

        Returns:
            Resolved value(s).

        Raises:
            PathResolutionError: If traversal fails.
        """
        if not segments:
            return current

        segment = segments[0]
        remaining = segments[1:]

        # Handle wildcard
        if segment.is_wildcard:
            if not isinstance(current, dict):
                raise PathResolutionError(
                    f"Cannot apply wildcard to non-dict at '{segment.key}' in path '{original_path}'"
                )

            if segment.key not in current:
                raise PathResolutionError(f"Key '{segment.key}' not found in path '{original_path}'")

            target = current[segment.key]
            if not isinstance(target, list):
                raise PathResolutionError(
                    f"Wildcard requires array at '{segment.key}' in path '{original_path}', got {type(target).__name__}"
                )

            # Apply remaining segments to each array element
            if not remaining:
                # No more segments, return the array as-is
                return target

            results = []
            errors_encountered = []
            for item in target:
                try:
                    result = PathResolver._traverse(item, remaining, original_path)
                    # Flatten nested wildcards
                    if isinstance(result, list) and remaining and any(seg.is_wildcard for seg in remaining):
                        results.extend(result)
                    else:
                        results.append(result)
                except PathResolutionError as e:
                    # Track errors but continue processing other items
                    errors_encountered.append(str(e))

            # If all items failed, raise the first error
            if not results and errors_encountered:
                raise PathResolutionError(errors_encountered[0])

            return results

        # Handle specific index
        if segment.index is not None:
            if not isinstance(current, dict):
                raise PathResolutionError(
                    f"Cannot access key '{segment.key}' on non-dict at path '{original_path}'"
                )

            if segment.key not in current:
                raise PathResolutionError(f"Key '{segment.key}' not found in path '{original_path}'")

            target = current[segment.key]
            if not isinstance(target, list):
                raise PathResolutionError(
                    f"Index access requires array at '{segment.key}' in path '{original_path}', got {type(target).__name__}"
                )

            if segment.index >= len(target):
                raise PathResolutionError(
                    f"Index {segment.index} out of range for '{segment.key}' (length {len(target)}) in path '{original_path}'"
                )

            return PathResolver._traverse(target[segment.index], remaining, original_path)

        # Handle simple key access
        if isinstance(current, dict):
            if segment.key not in current:
                raise PathResolutionError(f"Key '{segment.key}' not found in path '{original_path}'")
            return PathResolver._traverse(current[segment.key], remaining, original_path)
        elif isinstance(current, list):
            # If current is a list and no index specified, fail
            raise PathResolutionError(
                f"Cannot access key '{segment.key}' on list at path '{original_path}' (use index or wildcard)"
            )
        else:
            raise PathResolutionError(
                f"Cannot access key '{segment.key}' on {type(current).__name__} at path '{original_path}'"
            )

    @staticmethod
    def aggregate(
        data: dict | list, path: str, func: Literal["min", "max", "avg"]
    ) -> float | None:
        """Aggregate numeric values from a path.

        Args:
            data: The data structure to traverse.
            path: Dotted path string (must resolve to numeric values).
            func: Aggregation function ("min", "max", "avg").

        Returns:
            Aggregated result, or None if no valid numeric values found.

        Raises:
            PathResolutionError: If path cannot be resolved.
            AggregationError: If non-numeric elements are encountered.

        Examples:
            aggregate({"items": [{"x": 1}, {"x": 2}]}, "items[*].x", "min") → 1
            aggregate({"items": [{"x": 1}, {"x": 2}]}, "items[*].x", "max") → 2
            aggregate({"items": [{"x": 1}, {"x": 2}]}, "items[*].x", "avg") → 1.5
        """
        values = PathResolver.resolve(data, path)

        # Flatten if nested list (from nested wildcards)
        if isinstance(values, list) and values and isinstance(values[0], list):
            values = list(chain.from_iterable(values))

        # Ensure we have a list
        if not isinstance(values, list):
            values = [values]

        # Filter numeric values
        numeric_values: list[float] = []
        non_numeric_count = 0

        for value in values:
            if isinstance(value, (int, float)):
                numeric_values.append(float(value))
            else:
                non_numeric_count += 1
                logger.warning(
                    f"Non-numeric value encountered during aggregation at path '{path}': {value} ({type(value).__name__})"
                )

        if non_numeric_count > 0:
            raise AggregationError(
                f"Path '{path}' contains {non_numeric_count} non-numeric element(s). Only numeric values are supported for aggregation."
            )

        if not numeric_values:
            logger.warning(f"No valid numeric values found at path '{path}' for aggregation")
            return None

        # Apply aggregation function
        if func == "min":
            return min(numeric_values)
        elif func == "max":
            return max(numeric_values)
        elif func == "avg":
            return round(mean(numeric_values), 2)
        else:
            raise ValueError(f"Unknown aggregation function: {func}")
