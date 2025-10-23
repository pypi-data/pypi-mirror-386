#!/usr/bin/env python3
"""改善提案バリューオブジェクト.

Provides a unified representation for quality improvement suggestions coming
from writing analysis. Supports both the legacy "content + suggestion type"
structure and the richer structured payload used by the new quality tools.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Sequence

from noveler.domain.exceptions import ValidationError


class SuggestionType(Enum):
    """改善提案種別."""

    ENHANCEMENT = "enhancement"
    FIX = "fix"
    STYLE = "style"
    OPTIMIZATION = "optimization"
    CONTENT_ENHANCEMENT = "content_enhancement"
    READABILITY_IMPROVEMENT = "readability_improvement"
    STYLE_REFINEMENT = "style_refinement"
    BALANCE_ADJUSTMENT = "balance_adjustment"
    GENERAL_IMPROVEMENT = "general_improvement"


_PRIORITY_SCORE = {"high": 3, "medium": 2, "low": 1}
_ALLOWED_IMPLEMENTATION_DIFFICULTY = {"easy", "medium", "hard"}


def _trim(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed if trimmed else None


@dataclass(frozen=True, slots=True)
class ImprovementSuggestion:
    """改善提案バリューオブジェクト.

    The instance is immutable and value-based. It can be initialised in two
    modes:

    * Legacy mode — using ``content`` + ``suggestion_type`` + ``confidence``
      (and optional ``fix_example`` / ``expected_impact`` /
      ``implementation_difficulty``).
    * Structured mode — using the richer ``category``/``priority``/``title``
      payload along with ``specific_actions`` and other fields.
    """

    # Structured suggestion fields
    category: str | None = field(default=None)
    priority: str | None = field(default=None)
    title: str | None = field(default=None)
    description: str | None = field(default=None)
    specific_actions: tuple[str, ...] = field(default_factory=tuple)
    estimated_impact: float | None = field(default=None)

    # Shared attributes
    confidence: float = field(default=0.0)
    suggestion_type: SuggestionType | None = field(default=None)
    content: str | None = field(default=None)
    fix_example: str | None = field(default=None)
    expected_impact: str | None = field(default=None)
    implementation_difficulty: str = field(default="medium")

    def __init__(
        self,
        *,
        # Structured payload
        category: str | None = None,
        priority: str | None = None,
        title: str | None = None,
        description: str | None = None,
        specific_actions: Sequence[str] | None = None,
        estimated_impact: float | None = None,
        # Legacy payload
        content: str | None = None,
        suggestion_type: SuggestionType | None = None,
        # Shared
        confidence: float,
        fix_example: str | None = None,
        expected_impact: str | None = None,
        implementation_difficulty: str = "medium",
    ) -> None:
        object.__setattr__(self, "confidence", confidence)
        object.__setattr__(self, "suggestion_type", suggestion_type)
        object.__setattr__(self, "content", None)
        object.__setattr__(self, "fix_example", _trim(fix_example))
        object.__setattr__(self, "expected_impact", _trim(expected_impact))
        object.__setattr__(self, "implementation_difficulty", implementation_difficulty)

        is_structured = any(
            value is not None
            for value in (category, priority, title, description, specific_actions, estimated_impact)
        )

        if is_structured:
            self._init_structured(
                category=category,
                priority=priority,
                title=title,
                description=description,
                specific_actions=specific_actions,
                estimated_impact=estimated_impact,
            )
            # Provide content fallback for legacy accessors
            object.__setattr__(self, "content", self.description)
        else:
            self._init_legacy(
                content=content,
                suggestion_type=suggestion_type,
            )

        self._validate_confidence()
        self._validate_implementation_difficulty()

    @classmethod
    def create(cls, **payload: Any) -> "ImprovementSuggestion":
        """Construct an improvement suggestion from flexible keyword payloads.

        Purpose:
            Provide a resilient factory that accepts both legacy (content-based)
            and structured keyword arguments. Callers may provide ``suggestion_type``
            as either a string or ``SuggestionType`` enum and omit ``confidence``
            to rely on the default confidence value.

        Args:
            **payload: Keyword arguments matching the constructor parameters.
                ``confidence`` and ``estimated_impact`` are coerced to floats when
                provided as numeric-compatible values.

        Returns:
            ImprovementSuggestion: An immutable suggestion instance populated with
            normalised data.

        Raises:
            ValidationError: If numeric fields cannot be coerced or if the
            ``suggestion_type`` value is unknown.
        """

        data = dict(payload)

        confidence_raw = data.pop("confidence", 0.5)
        try:
            confidence = float(confidence_raw)
        except (TypeError, ValueError) as exc:  # pragma: no cover - defensive guard
            raise ValidationError("confidence", "信頼度は数値で指定してください", confidence_raw) from exc

        suggestion_type_value = data.get("suggestion_type")
        if suggestion_type_value is not None and not isinstance(suggestion_type_value, SuggestionType):
            try:
                suggestion_type_enum = SuggestionType(str(suggestion_type_value))
            except ValueError as exc:  # pragma: no cover - defensive guard
                raise ValidationError("suggestion_type", "無効な提案種別です", suggestion_type_value) from exc
            data["suggestion_type"] = suggestion_type_enum

        estimated = data.get("estimated_impact")
        if estimated is not None and not isinstance(estimated, (int, float)):
            try:
                data["estimated_impact"] = float(estimated)
            except (TypeError, ValueError) as exc:  # pragma: no cover - defensive guard
                raise ValidationError("estimated_impact", "推定インパクトは数値で指定してください", estimated) from exc

        specific_actions = data.get("specific_actions")
        if specific_actions is not None and not isinstance(specific_actions, (list, tuple)):
            raise ValidationError(
                "specific_actions",
                "具体的アクションはリストまたはタプルで指定してください",
                specific_actions,
            )

        return cls(confidence=confidence, **data)

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------
    def _init_structured(
        self,
        *,
        category: str | None,
        priority: str | None,
        title: str | None,
        description: str | None,
        specific_actions: Sequence[str] | None,
        estimated_impact: float | None,
    ) -> None:
        category_value = _trim(category)
        if not category_value:
            raise ValidationError("category", "カテゴリは必須です", category)

        priority_value = _trim(priority)
        if priority_value not in _PRIORITY_SCORE:
            raise ValidationError("priority", "優先度は 'high', 'medium', 'low' のいずれかを指定してください", priority)

        title_value = _trim(title)
        if not title_value:
            raise ValidationError("title", "タイトルは必須です", title)
        if len(title_value) > 100:
            raise ValidationError("title", "タイトルは100文字以内で指定してください", title_value)

        description_value = _trim(description)
        if not description_value:
            raise ValidationError("description", "説明は必須です", description)
        if len(description_value) > 500:
            raise ValidationError("description", "説明は500文字以内で指定してください", description_value)

        actions_value = self._normalise_actions(specific_actions)
        if not actions_value:
            raise ValidationError("specific_actions", "具体的アクションは最低1つ必要です", specific_actions)

        impact_value = estimated_impact
        if impact_value is None:
            raise ValidationError("estimated_impact", "推定インパクトは必須です", estimated_impact)
        if not 0.0 <= impact_value <= 10.0:
            raise ValidationError("estimated_impact", "推定インパクトは0.0から10.0の範囲で指定してください", impact_value)

        object.__setattr__(self, "category", category_value)
        object.__setattr__(self, "priority", priority_value)
        object.__setattr__(self, "title", title_value)
        object.__setattr__(self, "description", description_value)
        object.__setattr__(self, "specific_actions", actions_value)
        object.__setattr__(self, "estimated_impact", impact_value)

    def _init_legacy(self, *, content: str | None, suggestion_type: SuggestionType | None) -> None:
        content_value = _trim(content)
        if not content_value:
            raise ValidationError("content", "改善提案内容は空にできません", content)
        if suggestion_type is None:
            raise ValidationError("suggestion_type", "提案種別は必須です", suggestion_type)

        object.__setattr__(self, "category", suggestion_type.value)
        object.__setattr__(self, "priority", None)
        object.__setattr__(self, "title", None)
        object.__setattr__(self, "description", content_value)
        object.__setattr__(self, "specific_actions", tuple())
        object.__setattr__(self, "estimated_impact", None)
        object.__setattr__(self, "content", content_value)

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _normalise_actions(actions: Sequence[str] | None) -> tuple[str, ...]:
        if actions is None:
            return tuple()

        normalised: list[str] = []
        for action in actions:
            if not isinstance(action, str):
                raise ValidationError("specific_actions", "具体的アクションは文字列で指定してください", action)
            trimmed = action.strip()
            if not trimmed:
                raise ValidationError("specific_actions", "具体的アクションは空文字にできません", action)
            if len(trimmed) > 200:
                raise ValidationError("specific_actions", "具体的アクションは200文字以内で指定してください", trimmed)
            normalised.append(trimmed)

        return tuple(normalised)

    def _validate_confidence(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValidationError("confidence", "信頼度は0.0から1.0の範囲で指定してください", self.confidence)

    def _validate_implementation_difficulty(self) -> None:
        if self.implementation_difficulty not in _ALLOWED_IMPLEMENTATION_DIFFICULTY:
            raise ValidationError(
                "implementation_difficulty",
                "実装難易度はeasy/medium/hardのいずれかである必要があります",
                self.implementation_difficulty,
            )

    # ------------------------------------------------------------------
    # Priority helpers
    # ------------------------------------------------------------------
    def is_high_priority(self) -> bool:
        return self.priority == "high"

    def is_medium_priority(self) -> bool:
        return self.priority == "medium"

    def is_low_priority(self) -> bool:
        return self.priority == "low"

    def get_priority_score(self) -> int:
        return _PRIORITY_SCORE.get(self.priority or "", 0)

    # ------------------------------------------------------------------
    # Impact helpers
    # ------------------------------------------------------------------
    def is_high_impact(self, threshold: float = 7.0) -> bool:
        if self.estimated_impact is None:
            return False
        return self.estimated_impact >= threshold

    def is_reliable(self, threshold: float = 0.7) -> bool:
        return self.confidence >= threshold

    def get_action_count(self) -> int:
        return len(self.specific_actions)

    def get_suggestion_summary(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "priority": self.priority,
            "priority_score": self.get_priority_score(),
            "title": self.title,
            "description": self.description,
            "action_count": self.get_action_count(),
            "estimated_impact": self.estimated_impact,
            "confidence": self.confidence,
            "is_high_priority": self.is_high_priority(),
            "is_high_impact": self.is_high_impact(),
            "is_reliable": self.is_reliable(),
        }

    # ------------------------------------------------------------------
    # Convenience predicates (legacy compatibility)
    # ------------------------------------------------------------------
    def has_fix_example(self) -> bool:
        return bool(self.fix_example)

    def is_high_impact_legacy(self) -> bool:
        """Retained for backward compatibility with legacy callers."""
        return self.is_high_impact()

    def is_easy_to_implement(self) -> bool:
        return self.implementation_difficulty == "easy"

    def get_formatted_suggestion(self) -> str:
        parts: list[str] = []
        if self.content:
            parts.append(self.content)
        if self.fix_example:
            parts.append(f"修正例: {self.fix_example}")
        if self.expected_impact:
            parts.append(f"効果: {self.expected_impact}")
        return " | ".join(parts) if parts else ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "priority": self.priority,
            "title": self.title,
            "description": self.description,
            "specific_actions": list(self.specific_actions),
            "estimated_impact": self.estimated_impact,
            "confidence": self.confidence,
            "suggestion_type": self.suggestion_type.value if self.suggestion_type else None,
            "content": self.content,
            "fix_example": self.fix_example,
            "expected_impact": self.expected_impact,
            "implementation_difficulty": self.implementation_difficulty,
        }
