# File: src/noveler/domain/adapters/__init__.py
# Purpose: Domain adapter layer for bridging legacy and new schemas
# Context: Provides adapters for CharacterProfile and other domain objects

"""Domain adapters for schema transformation and compatibility."""

from noveler.domain.adapters.character_profile_adapter import (
    CharacterBookEntry,
    CharacterProfileAdapter,
)

__all__ = [
    "CharacterBookEntry",
    "CharacterProfileAdapter",
]
