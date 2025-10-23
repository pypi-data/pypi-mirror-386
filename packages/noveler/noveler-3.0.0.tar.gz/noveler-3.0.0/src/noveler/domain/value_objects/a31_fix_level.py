#!/usr/bin/env python3
"""A31修正レベル値オブジェクト

SPEC-QUALITY-001に基づく修正レベルの表現。
安全性とリスクのバランスを管理。
"""

from enum import Enum


class FixLevel(Enum):
    """修正レベル列挙型

    自動修正の安全性レベルを定義。
    レベルが上がるほど高機能だがリスクも増加。
    """

    SAFE = "safe"  # 確実な修正(フォーマット系)
    STANDARD = "standard"  # パターンベース修正(中精度)
    INTERACTIVE = "interactive"  # 人的確認付き修正(高精度)

    def get_risk_level(self) -> str:
        """リスクレベルの取得

        Returns:
            str: リスクレベル("low", "medium", "high")
        """
        risk_map = {FixLevel.SAFE: "low", FixLevel.STANDARD: "medium", FixLevel.INTERACTIVE: "high"}
        return risk_map[self]

    def get_description(self) -> str:
        """修正レベルの説明取得

        Returns:
            str: レベルの説明文
        """
        descriptions = {
            FixLevel.SAFE: "フォーマット系の確実な修正のみ実行",
            FixLevel.STANDARD: "パターンベースの中精度修正も含む",
            FixLevel.INTERACTIVE: "人的確認を伴う高精度修正も実行",
        }
        return descriptions[self]

    def allows_format_fixes(self) -> bool:
        """フォーマット修正を許可するか

        Returns:
            bool: フォーマット修正を許可する場合True
        """
        return True  # 全レベルでフォーマット修正は許可

    def allows_pattern_fixes(self) -> bool:
        """パターンベース修正を許可するか

        Returns:
            bool: パターンベース修正を許可する場合True
        """
        return self in (FixLevel.STANDARD, FixLevel.INTERACTIVE)

    def allows_interactive_fixes(self) -> bool:
        """対話的修正を許可するか

        Returns:
            bool: 対話的修正を許可する場合True
        """
        return self == FixLevel.INTERACTIVE

    def get_max_auto_changes(self) -> int:
        """自動変更の最大数取得

        Returns:
            int: 一度に実行可能な最大変更数
        """
        limits = {
            FixLevel.SAFE: 50,  # 安全な修正は多数実行可能
            FixLevel.STANDARD: 20,  # 中精度修正は制限付き
            FixLevel.INTERACTIVE: 5,  # 高精度修正は少数ずつ
        }
        return limits[self]

    @classmethod
    def from_string(cls, level_str: str) -> "FixLevel":
        """文字列からの変換

        Args:
            level_str: 修正レベル文字列

        Returns:
            FixLevel: 対応する修正レベル

        Raises:
            ValueError: 無効な文字列の場合
        """
        try:
            return cls(level_str.lower())
        except ValueError as e:
            valid_values = [level.value for level in cls]
            msg = f"無効な修正レベル: {level_str}. 有効な値: {valid_values}"
            raise ValueError(msg) from e
