"""Domain.value_objects.check_context
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

from __future__ import annotations

"""チェックコンテキスト値オブジェクト

属性チェックに必要な情報をまとめて管理する値オブジェクト。
"""


from dataclasses import dataclass


@dataclass(frozen=True)
class CheckContext:
    """属性チェックのコンテキスト情報

    関連するパラメータを値オブジェクトとしてまとめ、
    コードの可読性と保守性を向上させる。
    """

    line: str
    """チェック対象の行"""

    line_number: int
    """行番号"""

    character_name: str
    """キャラクター名"""

    expected_value: str
    """期待される値"""

    recent_characters: list[str]
    """最近言及されたキャラクター一覧"""

    def get_stripped_line(self) -> str:
        """空白を除去した行を取得"""
        return self.line.strip()

    def contains_keywords(self, keywords: list[str]) -> bool:
        """指定したキーワードが行に含まれているかチェック"""
        return any(keyword in self.line for keyword in keywords)

    def extract_speech(self) -> str | None:
        """セリフ部分を抽出"""
        if "「" in self.line and "」" in self.line:
            return self.line[self.line.index("「") + 1 : self.line.index("」")]
        return None

    def is_character_mentioned(self) -> bool:
        """キャラクター名が言及されているかチェック"""
        return self.character_name in self.line

    def is_recent_character_mentioned(self) -> bool:
        """最近言及されたキャラクターかチェック"""
        return self.character_name in self.recent_characters
