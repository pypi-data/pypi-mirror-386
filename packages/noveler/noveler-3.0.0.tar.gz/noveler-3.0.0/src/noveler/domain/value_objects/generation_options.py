"""Domain.value_objects.generation_options
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""生成オプション値オブジェクト
シーン自動生成のオプション設定
"""


from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GenerationOptions:
    """生成オプション値オブジェクト"""

    title: str | None = None
    importance_level: str = "A"
    episode_range: str | None = None
    template_name: str | None = None
    detail_level: str = "standard"  # basic, standard, full
    minimal_mode: bool = False

    def __post_init__(self) -> None:
        """値オブジェクトの不変条件を検証"""
        self._validate_importance_level()
        self._validate_detail_level()

    def _validate_importance_level(self) -> None:
        """重要度レベルの検証"""
        valid_levels = {"S", "A", "B", "C"}
        if self.importance_level not in valid_levels:
            msg = f"重要度レベルは {valid_levels} のいずれかを指定してください"
            raise ValueError(msg)

    def _validate_detail_level(self) -> None:
        """詳細レベルの検証"""
        valid_levels = {"basic", "standard", "full"}
        if self.detail_level not in valid_levels:
            msg = f"詳細レベルは {valid_levels} のいずれかを指定してください"
            raise ValueError(msg)

    def is_valid(self) -> bool:
        """オプションの有効性をチェック"""
        try:
            self._validate_importance_level()
            self._validate_detail_level()
            return True
        except ValueError:
            return False

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "title": self.title,
            "importance_level": self.importance_level,
            "episode_range": self.episode_range,
            "template_name": self.template_name,
            "detail_level": self.detail_level,
            "minimal_mode": self.minimal_mode,
        }

    @classmethod
    def from_cli_args(cls, args: dict[str, Any]) -> GenerationOptions:
        """CLIコマンド引数から構築"""
        return cls(
            title=args.get("title"),
            importance_level=args.get("importance", "A"),
            episode_range=args.get("episode"),
            template_name=args.get("template"),
            detail_level=args.get("detail_level", "standard"),
            minimal_mode=args.get("minimal", False),
        )
