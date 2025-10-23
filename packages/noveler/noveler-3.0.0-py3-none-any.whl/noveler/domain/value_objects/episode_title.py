#!/usr/bin/env python3
"""エピソードタイトル値オブジェクト

DDD原則に基づく不変の値オブジェクト
"""

import re
from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class EpisodeTitle:
    """エピソードタイトルを表す値オブジェクト."""

    value: str

    MAX_LENGTH: ClassVar[int] = 100
    # Note: '?' と '!' は強調表現として許可（!? や ?! パターンのため）
    _INVALID_CHARS: ClassVar[re.Pattern[str]] = re.compile(r"[\\/*\"<>|]")
    _WHITESPACE_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"\s+")
    _FILENAME_REPLACEMENTS: ClassVar[dict[str, str]] = {
        ":": "_",
        "、": "_",
        "。": "",
        "!": "",
        "?": "",
        " ": "_",
    }

    def __post_init__(self) -> None:
        """バリデーションと正規化処理."""
        if not isinstance(self.value, str):
            raise ValueError("タイトルは文字列である必要があります")

        normalized_value, _allow_colon = self._normalize_value(self.value)
        object.__setattr__(self, "value", normalized_value)

        if not self.value:
            raise ValueError("タイトルは空にできません")

        if len(self.value) > self.MAX_LENGTH:
            msg = f"タイトルは{self.MAX_LENGTH}文字以内である必要があります: {len(self.value)}文字"
            raise ValueError(msg)

        if self._INVALID_CHARS.search(self.value):
            msg = "タイトルに使用できない文字が含まれています"
            raise ValueError(msg)

        # コロンはスラッグ変換時に安全化されるため許可する

    @staticmethod
    def _normalize_value(raw_value: str) -> tuple[str, bool]:
        """タイトル値を正規化する."""
        normalized = raw_value.strip()

        if "\n" in normalized or "\r" in normalized:
            raise ValueError("タイトルに改行文字を含めることはできません")

        # 標準的な「第X話:タイトル」フォーマットをサポート
        # 第X話: のパターンがある場合はコロンを許可
        episode_pattern = re.compile(r"^第\d+話[:：]")
        allow_colon = bool(episode_pattern.match(normalized))

        # 特殊シーケンス "!?" / "?!" は強調表現として許可（削除せず保持）
        # Note: これらの文字列はタイトルの一部として保持される
        return normalized, allow_colon

    def __str__(self) -> str:
        """文字列表現."""
        return self.value

    def contains(self, keyword: str) -> bool:
        """キーワードを含むかどうかを判定する."""
        if not keyword:
            return False
        return keyword.strip().casefold() in self.value.casefold()

    def to_slug(self) -> str:
        """スラッグ文字列を生成する."""
        slug = self.value
        for src, dest in self._FILENAME_REPLACEMENTS.items():
            slug = slug.replace(src, dest)
        slug = slug.replace("/", "_").replace("\\", "_")
        slug = self._WHITESPACE_PATTERN.sub("_", slug)
        slug = re.sub(r"_+", "_", slug)
        return slug.strip("_")

    def to_filename_safe(self) -> str:
        """ファイル名として安全な形式に変換."""
        slug = self.to_slug()
        slug = slug.replace("__", "_")
        return slug
