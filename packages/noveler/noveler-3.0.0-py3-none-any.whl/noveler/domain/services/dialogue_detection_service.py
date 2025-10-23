# File: src/noveler/domain/services/dialogue_detection_service.py
# Purpose: Provide robust dialogue line detection for Japanese manuscripts.
# Context: Used by readability/rhythm analysis to exclude dialogue lines from length checks.
"""Dialogue detection service for Japanese manuscripts.

This module offers helpers to detect dialogue lines using Japanese quotes
(e.g., 「...」, 『...』). It supports one-sided brackets and multi-line
continuations by tracking an "inside-dialogue" state across lines.

Functions are side-effect free and purely compute boolean flags so they can be
used by tools and tests without I/O.
"""
from __future__ import annotations

from typing import Iterable, List

OPEN_QUOTES = ("「", "『")
CLOSE_QUOTES = ("」", "』")


def _count_quote_delta(text: str) -> int:
    """Return open-close quote delta in the given text.

    Positive delta means more openings than closings; negative otherwise.
    """
    opens = sum(text.count(q) for q in OPEN_QUOTES)
    closes = sum(text.count(q) for q in CLOSE_QUOTES)
    return opens - closes


def detect_dialogue_flags(lines: Iterable[str]) -> List[bool]:
    """Detect whether each line is part of a dialogue block.

    Args:
        lines: Iterable of text lines (newline trimmed or not; newlines are ignored).

    Returns:
        List[bool]: True for lines considered dialogue.

    Rules:
    - A line starting with an opening quote (「 or 『) is considered dialogue.
    - One-sided opening (more openings than closings in a line) starts a dialogue block.
    - Once inside a dialogue block, subsequent lines remain dialogue until the
      cumulative quote balance returns to zero (i.e., all openings closed).
    - A closing-only line (more closings than openings) still counts as dialogue
      if it finishes an open dialogue.
    """
    flags: List[bool] = []
    balance = 0
    for raw in lines:
        line = raw.rstrip("\n")
        delta = _count_quote_delta(line)
        starts_with_open = line.lstrip().startswith(OPEN_QUOTES)
        inside = balance > 0 or starts_with_open or delta > 0
        flags.append(bool(inside))
        balance = max(0, balance + delta)
    return flags


def is_dialogue_line(line: str, previous_open_balance: int = 0) -> bool:
    """Return True if the line is dialogue given previous open balance.

    Args:
        line: Single line of text.
        previous_open_balance: Count of unclosed quotes carried from previous lines.

    Notes:
        Use when evaluating lines incrementally. For batch processing prefer
        ``detect_dialogue_flags``.
    """
    delta = _count_quote_delta(line)
    starts_with_open = line.lstrip().startswith(OPEN_QUOTES)
    inside = previous_open_balance > 0 or starts_with_open or delta > 0
    return bool(inside)
