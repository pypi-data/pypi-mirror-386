"""Domain.value_objects.genre_type
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

from __future__ import annotations

"""ジャンルタイプ値オブジェクト"""


from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GenreType:
    """ジャンルを表す値オブジェクト"""

    value: str

    def __post_init__(self) -> None:
        """バリデーション"""
        if not self.value:
            msg = "ジャンル名は空にできません"
            raise ValueError(msg)

    @property
    def name(self) -> str:
        """ジャンル名を返す"""
        return self.value

    def get_default_quality_config(self) -> dict[str, Any]:
        """ジャンルに応じたデフォルト品質設定を返す"""
        # ジャンル別のデフォルト設定
        genre_configs = {
            "ファンタジー": {
                "basic_style": {
                    "max_hiragana_ratio": 0.45,  # やや高め(魔法用語等のルビ考慮)
                    "min_sentence_variety": 0.25,
                },
                "composition": {
                    "dialog_ratio_range": [0.25, 0.55],  # バトルシーン考慮
                    "short_sentence_ratio": 0.4,  # アクション描写用
                },
            },
            "恋愛": {
                "basic_style": {
                    "max_hiragana_ratio": 0.40,
                    "min_sentence_variety": 0.30,
                },
                "composition": {
                    "dialog_ratio_range": [0.35, 0.65],  # 会話重視
                    "short_sentence_ratio": 0.3,
                },
            },
            "ミステリー": {
                "basic_style": {
                    "max_hiragana_ratio": 0.35,  # 説明的文章多め
                    "min_sentence_variety": 0.35,
                },
                "composition": {
                    "dialog_ratio_range": [0.30, 0.55],
                    "short_sentence_ratio": 0.25,  # 論理的説明重視
                },
            },
        }

        # ジャンルが定義されていない場合はデフォルト設定を返す
        if self.value not in genre_configs:
            return {
                "basic_style": {
                    "max_hiragana_ratio": 0.40,
                    "min_sentence_variety": 0.30,
                },
                "composition": {
                    "dialog_ratio_range": [0.30, 0.60],
                    "short_sentence_ratio": 0.35,
                },
            }

        return genre_configs[self.value]

    def __eq__(self, other: object) -> bool:
        """等価性の比較"""
        if not isinstance(other, GenreType):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        """ハッシュ値を返す"""
        return hash(self.value)
