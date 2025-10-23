# File: src/noveler/domain/value_objects/domain_message.py
# Purpose: Represent structured domain-layer messages that can be surfaced by upper layers.
# Context: Enables domain services to record informational or warning messages without relying on UI consoles.
"""Structured message primitives for the domain layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class DomainMessage:
    """Lightweight container for domain-level messages.

    Attributes:
        level: Semantic level such as ``info``, ``warning``, or ``error``.
        message: Human-readable message text describing the event.
        suggestion: Optional follow-up action or remediation hint.
        code: Optional machine-friendly identifier for categorising the message.
        details: Arbitrary metadata captured alongside the message.
    """

    level: str
    message: str
    suggestion: str | None = None
    code: str | None = None
    details: Mapping[str, Any] = field(default_factory=dict)

