"""Domain.value_objects.scene_direction
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""DDD Value Object: SceneDirection
シーン演出指示のバリューオブジェクト
"""


from dataclasses import dataclass
from typing import Any

from noveler.domain.exceptions import DomainException


@dataclass(frozen=True)
class SceneDirection:
    """シーン演出指示バリューオブジェクト"""

    pacing: str  # slow, medium, fast
    tension_curve: str
    emotional_flow: str
    visual_direction: dict[str, Any] | None = None
    sound_design: dict[str, Any] | None = None
    special_effects: list[str] | None = None

    def __post_init__(self) -> None:
        """初期化後の検証"""
        self._validate()

    def _validate(self) -> None:
        """値の妥当性を検証"""
        valid_pacing = ["slow", "medium", "fast"]
        if self.pacing not in valid_pacing:
            error_msg = f"pacing は {valid_pacing} のいずれかである必要があります"
            raise DomainException(error_msg)

        if not self.tension_curve or not self.tension_curve.strip():
            error_msg = "tension_curve は必須です"
            raise DomainException(error_msg)

        if not self.emotional_flow or not self.emotional_flow.strip():
            error_msg = "emotional_flow は必須です"
            raise DomainException(error_msg)

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        data: dict[str, Any] = {
            "pacing": self.pacing,
            "tension_curve": self.tension_curve,
            "emotional_flow": self.emotional_flow,
        }

        if self.visual_direction:
            data["visual_direction"] = self.visual_direction

        if self.sound_design:
            data["sound_design"] = self.sound_design

        if self.special_effects:
            data["special_effects"] = self.special_effects

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SceneDirection:
        """辞書から復元"""
        return cls(
            pacing=data["pacing"],
            tension_curve=data["tension_curve"],
            emotional_flow=data["emotional_flow"],
            visual_direction=data.get("visual_direction"),
            sound_design=data.get("sound_design"),
            special_effects=data.get("special_effects"),
        )

    def get_summary(self) -> str:
        """演出指示の要約を生成"""
        summary = f"ペース: {self.pacing}, 緊張: {self.tension_curve}, 感情: {self.emotional_flow}"

        if self.special_effects:
            summary += f", 特殊効果: {', '.join(self.special_effects)}"

        return summary
