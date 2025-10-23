"""エピソードタイトル値オブジェクト(Design by Contract強化版)"""

import re
import unicodedata
from dataclasses import dataclass

from noveler.domain.exceptions import DomainException


@dataclass(frozen=True)
class EnhancedEpisodeTitle:
    """エピソードタイトルを表す値オブジェクト(契約強化版)

    不変条件:
    - タイトルは空文字列ではない
    - タイトルは100文字以下
    - ファイル名として使用可能な形式に変換できる
    """

    value: str

    # タイトルの制限
    MAX_LENGTH = 100
    INVALID_FILENAME_CHARS = r'[<>:"/\\|?*]'

    def __post_init__(self) -> None:
        """不変条件の検証"""
        # 基本検証
        if not isinstance(self.value, str):
            msg = "タイトルは文字列である必要があります"
            raise DomainException(msg)

        # 前後の空白を除去
        object.__setattr__(self, "value", self.value.strip())

        if not self.value:
            msg = "タイトルは空文字列にできません"
            raise DomainException(msg)

        if len(self.value) > self.MAX_LENGTH:
            msg = f"タイトルは{self.MAX_LENGTH}文字以下である必要があります"
            raise DomainException(msg)

        if not self.value:
            msg = "タイトルは空にできません"
            raise DomainException(msg)

        if len(self.value) > self.MAX_LENGTH:
            msg = f"タイトルは{self.MAX_LENGTH}文字以下である必要があります"
            raise DomainException(msg)

    def __str__(self) -> str:
        return self.value

    def to_filename_safe(self) -> str:
        """ファイル名として安全な文字列に変換"""
        # Unicodeの正規化
        normalized = unicodedata.normalize("NFKC", self.value)

        # ファイル名に使用できない文字を置換
        safe_title = re.sub(self.INVALID_FILENAME_CHARS, "_", normalized)

        # 連続するアンダースコアを1つに
        safe_title = re.sub(r"_+", "_", safe_title)

        # 前後のアンダースコアを除去
        safe_title = safe_title.strip("_")

        return safe_title or "untitled"

    def truncate(self, max_length: int) -> "EnhancedEpisodeTitle":
        """指定文字数で切り詰め"""
        if not isinstance(max_length, int):
            msg = "max_length must be an integer"
            raise TypeError(msg)
        if max_length <= 0:
            msg = "max_length must be positive"
            raise ValueError(msg)

        if len(self.value) <= max_length:
            return self

        truncated = self.value[: max_length - 3] + "..."
        return EnhancedEpisodeTitle(truncated)

    def contains_keyword(self, keyword: str) -> bool:
        """キーワードを含むかチェック"""
        return keyword.lower() in self.value.lower()

    def _invariant(self) -> None:
        """クラス不変条件"""
