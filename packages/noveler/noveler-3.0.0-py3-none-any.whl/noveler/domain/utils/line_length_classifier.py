# File: src/noveler/domain/utils/line_length_classifier.py
# Purpose: Classify line lengths against warn/critical thresholds.
# Context: Allows tests to verify boundary behaviour (e.g., 80/120) without enforcing wrapping.
"""Small helper to classify line length severity.

This module does not enforce any policy; it simply classifies a numeric length
so tests and tools can reason about thresholds without side-effects.
"""
from __future__ import annotations

from typing import Literal

Severity = Literal['ok','warn','critical']


def classify_length(length: int, warn: int = 80, critical: int = 120) -> Severity:
    """Classify ``length`` into 'ok' | 'warn' | 'critical'.

    Args:
        length: Measured length (non-negative integer).
        warn: Lower threshold (inclusive) for warnings.
        critical: Upper threshold (exclusive) above which severity is critical.

    Returns:
        Severity: 'ok' if length < warn; 'warn' if warn <= length <= critical;
        'critical' if length > critical.
    """
    if length < warn:
        return 'ok'
    if length <= critical:
        return 'warn'
    return 'critical'
