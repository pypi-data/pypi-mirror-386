"""Domain.value_objects.proper_noun
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""固有名詞値オブジェクト

DDD原則に基づく不変の値オブジェクト
"""


import re
from dataclasses import dataclass
from enum import Enum


class ProperNounType(Enum):
    """固有名詞のタイプ"""

    PERSON = "person"  # 人名
    PLACE = "place"  # 地名
    ORGANIZATION = "organization"  # 組織名
    ITEM = "item"  # アイテム・道具名
    SKILL = "skill"  # スキル・魔法名
    TECHNOLOGY = "technology"  # 技術・システム名
    OTHER = "other"  # その他


@dataclass(frozen=True)
class ProperNoun:
    """固有名詞を表す値オブジェクト"""

    value: str
    noun_type: ProperNounType
    source_file: str | None = None

    def __post_init__(self) -> None:
        """バリデーション"""
        if not isinstance(self.value, str):
            msg = "固有名詞は文字列である必要があります"
            raise ValueError(msg)

        if not self.value or not self.value.strip():
            msg = "固有名詞は空にできません"
            raise ValueError(msg)

        if len(self.value) > 100:
            msg = f"固有名詞は100文字以内である必要があります: {len(self.value)}文字"
            raise ValueError(msg)

        if not isinstance(self.noun_type, ProperNounType):
            msg = "無効な固有名詞タイプ"
            raise ValueError(msg)

    def __str__(self) -> str:
        """文字列表現"""
        return self.value

    def is_person_name(self) -> bool:
        """人名かどうか"""
        return self.noun_type == ProperNounType.PERSON

    def is_place_name(self) -> bool:
        """地名かどうか"""
        return self.noun_type == ProperNounType.PLACE

    def is_organization_name(self) -> bool:
        """組織名かどうか"""
        return self.noun_type == ProperNounType.ORGANIZATION

    def contains_special_chars(self) -> bool:
        """特殊文字を含むかどうか"""
        special_chars = r"[A-Z\-\.・]"
        return bool(re.search(special_chars, self.value))

    def get_length(self) -> int:
        """文字数を取得"""
        return len(self.value)

    def starts_with(self, prefix: str) -> bool:
        """指定された接頭辞で始まるかどうか"""
        return self.value.startswith(prefix)

    def ends_with(self, suffix: str) -> bool:
        """指定された接尾辞で終わるかどうか"""
        return self.value.endswith(suffix)

    def contains(self, substring: str) -> bool:
        """指定された文字列を含むかどうか"""
        return substring in self.value

    def to_display_string(self) -> str:
        """表示用文字列(タイプ情報付き)"""
        type_name = {
            ProperNounType.PERSON: "人名",
            ProperNounType.PLACE: "地名",
            ProperNounType.ORGANIZATION: "組織",
            ProperNounType.ITEM: "アイテム",
            ProperNounType.SKILL: "スキル",
            ProperNounType.TECHNOLOGY: "技術",
            ProperNounType.OTHER: "その他",
        }
        return f"{self.value} ({type_name[self.noun_type]})"

    def __lt__(self, other: ProperNoun) -> bool:
        """比較演算子(小なり)"""
        if not isinstance(other, ProperNoun):
            return NotImplemented
        return self.value < other.value

    def __le__(self, other: ProperNoun) -> bool:
        """比較演算子(小なりイコール)"""
        if not isinstance(other, ProperNoun):
            return NotImplemented
        return self.value <= other.value

    def __gt__(self, other: ProperNoun) -> bool:
        """比較演算子(大なり)"""
        if not isinstance(other, ProperNoun):
            return NotImplemented
        return self.value > other.value

    def __ge__(self, other: ProperNoun) -> bool:
        """比較演算子(大なりイコール)"""
        if not isinstance(other, ProperNoun):
            return NotImplemented
        return self.value >= other.value
