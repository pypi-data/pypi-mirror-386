# File: src/noveler/domain/adapters/character_profile_adapter.py
# Purpose: Adapter for converting A24 new character schema to legacy CharacterProfile
# Context: Bridges hierarchical layers structure with flat attributes interface

"""Character schema adapter for A24 new schema.

This module provides adapters to convert between:
- A24 new schema (hierarchical layers: layer1_psychology, layer2_physical, etc.)
- Legacy CharacterProfile (flat attributes dictionary)

The adapter enables backward compatibility while preserving new schema information
through _raw_* attributes for future direct access.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from noveler.domain.value_objects.character_profile import AttributeValue, CharacterProfile


@dataclass
class CharacterBookEntry:
    """A24 new schema character entry.

    Represents a character from character_book.characters.* with hierarchical layers.
    """

    character_id: str
    display_name: str
    status: dict[str, Any]
    layers: dict[str, Any] = field(default_factory=dict)
    narrative_notes: dict[str, Any] | None = None
    llm_prompt_profile: dict[str, Any] | None = None
    logging: dict[str, Any] | None = None
    lite_profile_hint: dict[str, Any] | None = None
    episode_snapshots: list[dict[str, Any]] = field(default_factory=list)


class CharacterProfileAdapter:
    """Adapter for converting new schema to CharacterProfile."""

    @staticmethod
    def from_character_book_entry(entry: CharacterBookEntry) -> CharacterProfile:
        """Convert A24 new schema to legacy CharacterProfile.

        Args:
            entry: Character entry from character_book

        Returns:
            CharacterProfile with legacy attributes and _raw_* for new schema access

        Mapping strategy:
        - Layer1 (psychology) → personality, traits, goals, likes, dislikes, fears
        - Layer2 (physical) → appearance attributes
        - Layer5 (expression) → speech attributes
        - Preserve raw layers for direct access via _raw_layers
        """
        layers = entry.layers or {}

        layer1 = layers.get("layer1_psychology", {})
        layer2 = layers.get("layer2_physical", {})
        layer5 = layers.get("layer5_expression_behavior", {})

        attributes: dict[str, AttributeValue] = {
            # Meta attributes
            "character_id": entry.character_id,
            "category": entry.status.get("lifecycle", "active"),
            # Layer1: Psychology → personality attributes
            "personality": _extract_personality(layer1),
            "traits": _extract_traits(layer1),
            "likes": _extract_likes(layer1),
            "dislikes": _extract_dislikes(layer1),
            "fears": _extract_fears(layer1),
            "goals": _extract_goals(layer1),
            # Layer2: Physical → appearance attributes
            "hair_color": _extract_nested(layer2, "appearance.hair"),
            "eye_color": _extract_nested(layer2, "appearance.eyes"),
            "height": _extract_nested(layer2, "appearance.height"),
            "build": _extract_nested(layer2, "appearance.build"),
            "facial_features": _extract_facial_features(layer2),
            "clothing_style": _extract_nested(layer2, "attire.typical"),
            # Layer5: Expression → speech attributes
            "speech_style": _extract_speech_style(layer5),
            "catchphrase": _extract_catchphrase(layer5),
            # Deprecated/unmapped attributes (empty for legacy compatibility)
            "dialect": "",  # Included in baseline_tone, not extracted
            "verbal_tics": [],  # Use sentence_endings directly from _raw_layers
            "formality_level": "",  # Included in baseline_tone, not extracted
            # Raw new schema data (for direct access)
            "_raw_layers": layers,
            "_raw_llm_prompt_profile": entry.llm_prompt_profile or {},
            "_raw_narrative_notes": entry.narrative_notes or {},
            "_raw_status": entry.status,
            "_raw_logging": entry.logging or {},
            "_raw_lite_profile_hint": entry.lite_profile_hint or {},
            "_raw_episode_snapshots": entry.episode_snapshots or [],
        }

        return CharacterProfile(name=entry.display_name, attributes=attributes)

    @staticmethod
    def to_character_book_entry(profile: CharacterProfile) -> CharacterBookEntry:
        """Convert CharacterProfile to A24 new schema (future use).

        Args:
            profile: Legacy CharacterProfile

        Returns:
            CharacterBookEntry

        Note:
            Not yet implemented. Reserved for future programmatic YAML generation.
        """
        msg = "Reverse conversion (CharacterProfile → CharacterBookEntry) not yet implemented"
        raise NotImplementedError(msg)


# ========================================
# Layer1: Psychology extraction functions
# ========================================


def _extract_personality(layer1: dict) -> str:
    """Extract personality string from psychological layer.

    Strategy:
    1. Priority: summary_bullets (comprehensive psychological model summary)
    2. Fallback: traits_positive + traits_negative (basic trait list)

    Args:
        layer1: layer1_psychology dictionary

    Returns:
        Personality description string
    """
    # Priority: summary_bullets (心理モデルの要約)
    psych_models = layer1.get("psychological_models", {})
    summary = psych_models.get("summary_bullets", [])
    if summary:
        return "\n".join(f"- {bullet}" for bullet in summary)

    # Fallback: traits
    traits_pos = layer1.get("traits_positive", [])
    traits_neg = layer1.get("traits_negative", [])
    if traits_pos or traits_neg:
        return f"Positive: {', '.join(traits_pos)}; Negative: {', '.join(traits_neg)}"

    return ""


def _extract_traits(layer1: dict) -> list[str]:
    """Extract traits list (positive + negative combined).

    Args:
        layer1: layer1_psychology dictionary

    Returns:
        Combined traits list
    """
    traits_pos = layer1.get("traits_positive", [])
    traits_neg = layer1.get("traits_negative", [])
    return traits_pos + traits_neg


def _extract_likes(layer1: dict) -> list[str]:
    """Extract likes from emotional_patterns.

    Args:
        layer1: layer1_psychology dictionary

    Returns:
        Likes list
    """
    emotional = layer1.get("emotional_patterns", {})
    return emotional.get("likes", [])


def _extract_dislikes(layer1: dict) -> list[str]:
    """Extract dislikes from emotional_patterns.

    Args:
        layer1: layer1_psychology dictionary

    Returns:
        Dislikes list
    """
    emotional = layer1.get("emotional_patterns", {})
    return emotional.get("dislikes", [])


def _extract_fears(layer1: dict) -> list[str]:
    """Extract fears (enduring + momentary combined).

    Strategy:
    - Combine enduring_fears (long-term traumas) and momentary_fears (situational)
    - Prioritize enduring_fears, then append momentary_fears
    - Remove duplicates while preserving order

    Args:
        layer1: layer1_psychology dictionary

    Returns:
        Combined fears list (duplicates removed)
    """
    enduring = layer1.get("enduring_fears", [])
    momentary = layer1.get("emotional_patterns", {}).get("momentary_fears", [])

    # Remove duplicates while preserving order (enduring first)
    all_fears = list(dict.fromkeys(enduring + momentary))
    return all_fears


def _extract_goals(layer1: dict) -> list[str]:
    """Extract goals from core_motivations.

    Args:
        layer1: layer1_psychology dictionary

    Returns:
        Goals list (primary + secondary)
    """
    motivations = layer1.get("core_motivations", {})
    goals = []

    primary = motivations.get("primary")
    if primary:
        goals.append(primary)

    secondary = motivations.get("secondary", [])
    goals.extend(secondary)

    return goals


# ========================================
# Layer2: Physical extraction functions
# ========================================


def _extract_facial_features(layer2: dict) -> str:
    """Extract facial features from distinguishing_features.

    Strategy:
    - Filter distinguishing_features for face-related keywords
    - Join with ", " separator

    Args:
        layer2: layer2_physical dictionary

    Returns:
        Facial features string
    """
    features = layer2.get("distinguishing_features", [])

    # Face-related keywords (Japanese)
    facial_keywords = ["目", "鼻", "口", "耳", "顔", "眉", "額", "頬", "あご", "まつ毛"]

    # Filter for facial features
    facial = [f for f in features if any(kw in f for kw in facial_keywords)]

    return ", ".join(facial) if facial else ""


# ========================================
# Layer5: Expression extraction functions
# ========================================


def _extract_speech_style(layer5: dict) -> str:
    """Extract speech style from speech_profile.baseline_tone.

    Args:
        layer5: layer5_expression_behavior dictionary

    Returns:
        Speech style string
    """
    speech = layer5.get("speech_profile", {})
    return speech.get("baseline_tone", "")


def _extract_catchphrase(layer5: dict) -> str:
    """Extract catchphrases from speech_profile.

    Strategy:
    - catchphrases is a dict {situation: phrase}
    - Convert to "situation: phrase; situation: phrase" format
    - Preserve situational context for LLM prompts

    Args:
        layer5: layer5_expression_behavior dictionary

    Returns:
        Catchphrases string with situational context
    """
    speech = layer5.get("speech_profile", {})
    catchphrases = speech.get("catchphrases", {})

    if not catchphrases:
        return ""

    # Format: "状況: フレーズ; 状況: フレーズ"
    phrases = [f"{situation}: {phrase}" for situation, phrase in catchphrases.items()]
    return "; ".join(phrases)


# ========================================
# Utility functions
# ========================================


def _extract_nested(data: dict, path: str) -> Any:
    """Extract nested value using dot notation path.

    Args:
        data: Dictionary to extract from
        path: Dot-separated path (e.g. "appearance.hair")

    Returns:
        Extracted value or None if not found

    Examples:
        >>> _extract_nested({"a": {"b": "value"}}, "a.b")
        'value'
        >>> _extract_nested({"a": {"b": "value"}}, "a.c")
        None
    """
    keys = path.split(".")
    value: Any = data

    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return None

    return value
