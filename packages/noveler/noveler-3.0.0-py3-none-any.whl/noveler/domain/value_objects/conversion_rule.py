"""変換ルール値オブジェクト."""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from noveler.domain.exceptions import ValidationError


class ConversionType(Enum):
    """変換タイプ."""

    TEXT_REPLACE = "text_replace"
    FORMAT_CHANGE = "format_change"
    STRUCTURE_CHANGE = "structure_change"
    ENCODING_CHANGE = "encoding_change"


@dataclass(frozen=True)
class ConversionRule:
    """変換ルール値オブジェクト."""

    rule_id: str
    name: str
    conversion_type: ConversionType
    source_pattern: str
    target_pattern: str
    enabled: bool = True
    priority: int = 0
    conditions: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """値オブジェクトの不変条件を検証."""
        if self.conditions is None:
            object.__setattr__(self, "conditions", {})

        self._validate_rule_id()
        self._validate_name()
        self._validate_patterns()
        self._validate_priority()

    def _validate_rule_id(self) -> None:
        """ルールIDの妥当性検証."""
        if not self.rule_id or not self.rule_id.strip():
            msg = "rule_id"
            raise ValidationError(msg, "ルールIDは必須です")

    def _validate_name(self) -> None:
        """ルール名の妥当性検証."""
        if not self.name or not self.name.strip():
            msg = "name"
            raise ValidationError(msg, "ルール名は必須です")

    def _validate_patterns(self) -> None:
        """パターンの妥当性検証."""
        if not self.source_pattern:
            msg = "source_pattern"
            raise ValidationError(msg, "変換元パターンは必須です")
        if not self.target_pattern:
            msg = "target_pattern"
            raise ValidationError(msg, "変換先パターンは必須です")

    def _validate_priority(self) -> None:
        """優先度の妥当性検証."""
        if self.priority < 0:
            msg = "priority"
            raise ValidationError(msg, "優先度は0以上である必要があります")

    def is_applicable(self, context: dict[str, Any]) -> bool:
        """指定されたコンテキストでルールが適用可能かチェック."""
        if not self.enabled:
            return False

        # 条件チェック
        for key, expected_value in self.conditions.items():
            if key not in context or context[key] != expected_value:
                return False

        return True
