# File: tests/_utils/slow_marker_utils.py
# Purpose: Provide helper utilities for detecting slow-test keywords.
# Context: Used by pytest collection hooks and unit tests covering slow markers.
"""Helpers for slow test marker detection.

The pytest collection hook relies on these helpers to normalise test names
before matching against keyword heuristics.
"""

from __future__ import annotations

import re
from typing import Iterable

_TOKEN_PATTERN = re.compile(r"[_\W]+")


def extract_slow_marker_tokens(test_name: str) -> set[str]:
    """Return normalised tokens derived from a test name.

    Args:
        test_name: Raw pytest item name.

    Returns:
        A set containing the lower-cased name plus individual tokens split on
        underscores and non-word characters.
    """
    if not test_name:
        return set()

    lowered = test_name.lower()
    tokens: set[str] = {lowered}
    split_parts: Iterable[str] = _TOKEN_PATTERN.split(lowered)
    tokens.update(part for part in split_parts if part)
    return tokens


__all__ = ["extract_slow_marker_tokens"]
