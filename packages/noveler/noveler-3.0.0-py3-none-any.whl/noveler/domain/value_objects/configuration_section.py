#!/usr/bin/env python3
"""設定セクション値オブジェクト

型安全な設定値アクセスを提供する値オブジェクト実装
"""

from typing import Any


class ConfigurationSection:
    """設定セクション値オブジェクト

    個別の設定セクション（system, paths等）を表現し、
    型安全な設定値アクセスを提供する。
    """

    def __init__(self, section_name: str, data: dict[str, Any]) -> None:
        """設定セクション値オブジェクトを初期化

        Args:
            section_name: セクション名
            data: 設定データ辞書
        """
        self._section_name = section_name
        self._data = data or {}

    @property
    def section_name(self) -> str:
        """セクション名を取得"""
        return self._section_name

    def get_string(self, key: str, default: str | None = None) -> str:
        """文字列設定値を取得

        Args:
            key: 設定キー
            default: デフォルト値

        Returns:
            設定値またはデフォルト値
        """
        value = self._data.get(key, default)
        if value is None:
            return default
        return str(value)

    def get_int(self, key: str, default: int = 0) -> int:
        """整数設定値を取得

        Args:
            key: 設定キー
            default: デフォルト値

        Returns:
            設定値またはデフォルト値
        """
        value = self._data.get(key, default)
        if value is None:
            return default
        return int(value)

    def get_bool(self, key: str, default: bool = False) -> bool:
        """真偽値設定値を取得

        Args:
            key: 設定キー
            default: デフォルト値

        Returns:
            設定値またはデフォルト値
        """
        value = self._data.get(key, default)
        if value is None:
            return default
        return bool(value)

    def get_nested_string(self, key_path: list[str], default: str | None = None) -> str:
        """ネストされた文字列設定値を取得

        Args:
            key_path: ネストされたキーのパス
            default: デフォルト値

        Returns:
            設定値またはデフォルト値
        """
        value = self._get_nested_value(key_path, default)
        if value is None:
            return default
        return str(value)

    def get_nested_bool(self, key_path: list[str], default: bool = False) -> bool:
        """ネストされた真偽値設定値を取得

        Args:
            key_path: ネストされたキーのパス
            default: デフォルト値

        Returns:
            設定値またはデフォルト値
        """
        value = self._get_nested_value(key_path, default)
        if value is None:
            return default
        return bool(value)

    def _get_nested_value(self, key_path: list[str], default: Any = None) -> Any:
        """ネストされた値を取得する内部メソッド

        Args:
            key_path: ネストされたキーのパス
            default: デフォルト値

        Returns:
            設定値またはデフォルト値
        """
        current_data: dict[str, Any] = self._data

        for key in key_path:
            if isinstance(current_data, dict) and key in current_data:
                current_data: dict[str, Any] = current_data[key]
            else:
                return default

        return current_data
