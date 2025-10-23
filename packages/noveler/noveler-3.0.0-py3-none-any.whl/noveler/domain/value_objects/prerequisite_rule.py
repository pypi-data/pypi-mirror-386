#!/usr/bin/env python3
"""前提条件ルール値オブジェクト

プロット作成の前提条件を表現する値オブジェクト
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PrerequisiteRule:
    """前提条件ルール値オブジェクト"""

    file_path: str
    required: bool
    description: str

    def expand_path(self, **parameters: str) -> str:
        """パラメータを使ってファイルパスを展開

        Args:
            **parameters: パス展開用パラメータ

        Returns:
            str: 展開されたファイルパス
        """
        try:
            return self.file_path.format(**parameters)
        except KeyError:
            return self.file_path

    def is_optional(self) -> bool:
        """オプション(必須でない)前提条件かどうか

        Returns:
            bool: オプションの場合True
        """
        return not self.required
