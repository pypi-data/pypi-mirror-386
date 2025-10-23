"""Domain.value_objects.configuration_key
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

from __future__ import annotations

"""設定キーを表す値オブジェクト"""


class ConfigurationKey:
    """設定キーを表す値オブジェクト


    設定ファイル内のキーを表現し、階層構造をドット区切りで表す。
    例: "database.host.port"
    """

    def __init__(self, key: str) -> None:
        """ConfigurationKeyを初期化する

        Args:
            key: 設定キー(ドット区切り)

        Raises:
            ValueError: 無効なキー形式の場合
            TypeError: keyが文字列でない場合
        """
        if not isinstance(key, str):
            msg = f"Configuration key must be a string, got {type(key).__name__}"
            raise TypeError(msg)

        # 空白を除去
        key = key.strip()

        if not key:
            msg = "Configuration key cannot be empty"
            raise ValueError(msg)

        if key.startswith(".") or key.endswith("."):
            msg = "Configuration key cannot start or end with a dot"
            raise ValueError(msg)

        if ".." in key:
            msg = "Configuration key cannot contain consecutive dots"
            raise ValueError(msg)

        self._key = key

    def as_path_segments(self) -> list[str]:
        """キーをパスセグメントのリストに変換する

        Returns:
            パスセグメントのリスト
        """
        return self._key.split(".")

    def __str__(self) -> str:
        """文字列表現を返す"""
        return self._key

    def __eq__(self, other: object) -> bool:
        """等価性を判定する"""
        if not isinstance(other, ConfigurationKey):
            return False
        return self._key == other._key

    def __hash__(self) -> int:
        """ハッシュ値を返す"""
        return hash(self._key)

    def __repr__(self) -> str:
        """デバッグ用の文字列表現を返す"""
        return f"ConfigurationKey('{self._key}')"

    def __setattr__(self, name: str, value: object) -> None:
        """属性の設定を制限して不変性を保証する"""
        if hasattr(self, "_key"):
            msg = f"ConfigurationKey is immutable, cannot set attribute '{name}'"
            raise AttributeError(msg)
        super().__setattr__(name, value)
