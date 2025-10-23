"""Domain.value_objects.file_content
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""ファイルコンテンツ値オブジェクト

品質チェック対象のファイル内容を表現する不変オブジェクト。
"""


import re
from dataclasses import dataclass


@dataclass(frozen=True)
class FileContent:
    """ファイルコンテンツ値オブジェクト

    品質チェック対象のファイル内容を表現。
    """

    filepath: str
    content: str
    encoding: str = "utf-8"

    def __post_init__(self) -> None:
        """バリデーション"""
        if not self.filepath:
            msg = "ファイルパスは必須です"
            raise ValueError(msg)
        if not self.content:
            msg = "コンテンツは必須です"
            raise ValueError(msg)
        if not self.encoding:
            msg = "エンコーディングは必須です"
            raise ValueError(msg)

    @property
    def line_count(self) -> int:
        """行数を取得"""
        return len(self.content.splitlines())

    @property
    def character_count(self) -> int:
        """文字数を取得(空白除く)"""

        return len(re.sub(r"\s", "", self.content))

    @property
    def word_count(self) -> int:
        """単語数を取得(概算)"""
        # 日本語の場合は文字数を概算単語数とする
        return self.character_count

    def get_lines(self) -> list[str]:
        """行のリストを取得"""
        return self.content.splitlines()

    def get_line(self, line_number: int) -> str | None:
        """指定行を取得(1ベース)"""
        lines = self.get_lines()
        if 1 <= line_number <= len(lines):
            return lines[line_number - 1]
        return None
