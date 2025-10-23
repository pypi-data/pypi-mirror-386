"""SettingKey 値オブジェクト

SPEC-CONFIGURATION-001準拠
"""

from enum import Enum


class SettingCategory(Enum):
    """設定カテゴリ列挙型"""

    QUALITY = "quality"
    PERFORMANCE = "performance"
    INFRASTRUCTURE = "infrastructure"
    FEATURE = "feature"
    SECURITY = "security"


class SettingKey:
    """設定キー値オブジェクト"""

    def __init__(self, key: str, category: SettingCategory) -> None:
        if not key or not key.strip():
            msg = "Setting key cannot be empty"
            raise ValueError(msg)

        if "." not in key:
            msg = "Setting key must contain a category prefix (e.g., 'quality.threshold')"
            raise ValueError(msg)

        self.key = key.strip()
        self.category = category

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SettingKey):
            return False
        return self.key == other.key and self.category == other.category

    def __hash__(self) -> int:
        return hash((self.key, self.category))
