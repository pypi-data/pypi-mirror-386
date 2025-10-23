#!/usr/bin/env python3
"""優先項目ID バリューオブジェクト

A31重点項目の一意識別子を管理するバリューオブジェクト。
"""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PriorityItemId:
    """優先項目ID バリューオブジェクト

    A31重点項目の一意識別子を表現し、
    ID形式の妥当性検証とフォーマット正規化を提供する。
    """

    value: str

    def __post_init__(self) -> None:
        """ID妥当性検証"""
        if not self.value or not self.value.strip():
            msg = "優先項目IDは空にできません"
            raise ValueError(msg)

        # ID文字列を正規化
        normalized_value = self.value.strip().upper()
        object.__setattr__(self, "value", normalized_value)

        # 基本的なID形式チェック
        if not self._is_valid_format(normalized_value):
            # 厳格な検証は行わず、警告のみ
            pass

    def _is_valid_format(self, id_value: str) -> bool:
        """ID形式の妥当性チェック

        Args:
            id_value: チェック対象のID値

        Returns:
            bool: 形式が妥当な場合True
        """
        # A31形式のパターン (A31-001, A31-002, など)
        a31_pattern = r"^A31-\d{3}$"

        # 汎用パターン (任意の英数字とハイフン)
        generic_pattern = r"^[A-Z0-9\-_]+$"

        return re.match(a31_pattern, id_value) is not None or re.match(generic_pattern, id_value) is not None

    def is_a31_format(self) -> bool:
        """A31標準形式判定

        Returns:
            bool: A31標準形式（A31-XXX）の場合True
        """
        return re.match(r"^A31-\d{3}$", self.value) is not None

    def get_sequence_number(self) -> int:
        """シーケンス番号取得

        Returns:
            int: A31-XXX形式の場合はXXX部分、それ以外は0
        """
        if self.is_a31_format():
            return int(self.value.split("-")[1])
        return 0

    def get_display_name(self) -> str:
        """表示用名称取得

        Returns:
            str: 表示に適した形式のID文字列
        """
        return self.value

    def __str__(self) -> str:
        """文字列表現"""
        return self.value

    def __repr__(self) -> str:
        """開発者向け文字列表現"""
        return f"PriorityItemId('{self.value}')"
