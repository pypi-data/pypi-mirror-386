"""SettingValue 値オブジェクト

SPEC-CONFIGURATION-001準拠
"""

from enum import Enum


class SettingValueType(Enum):
    """設定値型列挙型"""

    FLOAT = "float"
    INTEGER = "integer"
    STRING = "string"
    BOOLEAN = "boolean"


class SettingValue:
    """設定値オブジェクト"""

    def __init__(
        self, value: str | int | float | bool, value_type: SettingValueType, constraints: dict | None = None
    ) -> None:
        self.value = value
        self.value_type = value_type
        self.constraints = constraints or {}
        self._validate()

    def _validate(self) -> None:
        """設定値と制約を検証"""
        # 型チェック
        if not self._is_correct_type():
            msg = f"Value type mismatch: expected {self.value_type.value}, got {type(self.value).__name__}"
            raise ValueError(msg)

        # 制約チェック
        if not self._satisfies_constraints():
            if self.value_type == SettingValueType.FLOAT and "max" in self.constraints:
                if self.value > self.constraints["max"]:
                    msg = f"Value {self.value} exceeds maximum {self.constraints['max']}"
                    raise ValueError(msg)
            if self.value_type == SettingValueType.STRING and "allowed" in self.constraints:
                if self.value not in self.constraints["allowed"]:
                    msg = f"Value '{self.value}' not in allowed values: {self.constraints['allowed']}"
                    raise ValueError(msg)

    def _is_correct_type(self) -> bool:
        """型が正しいかチェック"""
        if self.value_type == SettingValueType.FLOAT:
            return isinstance(self.value, int | float)
        if self.value_type == SettingValueType.INTEGER:
            return isinstance(self.value, int)
        if self.value_type == SettingValueType.STRING:
            return isinstance(self.value, str)
        if self.value_type == SettingValueType.BOOLEAN:
            return isinstance(self.value, bool)
        return False

    def _satisfies_constraints(self) -> bool:
        """制約を満たすかチェック"""
        if not self.constraints:
            return True

        # 数値範囲チェック
        if self.value_type in [SettingValueType.FLOAT, SettingValueType.INTEGER]:
            if "min" in self.constraints and self.value < self.constraints["min"]:
                return False
            if "max" in self.constraints and self.value > self.constraints["max"]:
                return False

        # 文字列許可値チェック
        if self.value_type == SettingValueType.STRING:
            if "allowed" in self.constraints and self.value not in self.constraints["allowed"]:
                return False

        return True

    def is_valid(self) -> bool:
        """設定値が有効かチェック(例外を投げない版)"""
        try:
            return self._is_correct_type() and self._satisfies_constraints()
        except Exception:
            return False
