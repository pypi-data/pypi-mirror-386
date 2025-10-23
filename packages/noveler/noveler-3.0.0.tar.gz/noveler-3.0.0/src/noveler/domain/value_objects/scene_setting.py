"""Domain.value_objects.scene_setting
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""DDD Value Object: SceneSetting
シーン設定のバリューオブジェクト
"""


from dataclasses import dataclass
from typing import Any

from noveler.domain.exceptions import DomainException


@dataclass(frozen=True)
class SceneSetting:
    """シーン設定バリューオブジェクト"""

    location: str
    time: str
    weather: str
    atmosphere: str
    additional_details: dict[str, str] | None = None

    def __post_init__(self) -> None:
        """初期化後の検証"""
        self._validate()

    def _validate(self) -> None:
        """値の妥当性を検証"""
        if not self.location or not self.location.strip():
            msg = "location は必須です"
            raise DomainException(msg)

        if not self.time or not self.time.strip():
            msg = "time は必須です"
            raise DomainException(msg)

        if not self.atmosphere or not self.atmosphere.strip():
            msg = "atmosphere は必須です"
            raise DomainException(msg)

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        data: dict[str, Any] = {
            "location": self.location,
            "time": self.time,
            "weather": self.weather,
            "atmosphere": self.atmosphere,
        }

        if self.additional_details:
            data["additional_details"] = self.additional_details

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SceneSetting:
        """辞書から復元"""
        return cls(
            location=data["location"],
            time=data["time"],
            weather=data["weather"],
            atmosphere=data["atmosphere"],
            additional_details=data.get("additional_details"),
        )

    def get_description(self) -> str:
        """設定の説明文を生成"""
        desc = f"{self.location}、{self.time}"

        if self.weather and self.weather.strip():
            desc += f"、{self.weather}"

        desc += f"。{self.atmosphere}な雰囲気。"

        return desc
