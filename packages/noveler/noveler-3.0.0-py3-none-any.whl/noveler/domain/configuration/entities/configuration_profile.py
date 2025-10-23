"""ConfigurationProfile エンティティ

SPEC-CONFIGURATION-001準拠
"""

from dataclasses import dataclass
from typing import Any

from noveler.domain.configuration.value_objects.setting_key import SettingKey


@dataclass
class ValidationError:
    """検証エラー情報"""

    key: str
    message: str


@dataclass
class ValidationResult:
    """検証結果"""

    is_valid: bool
    errors: list[ValidationError]


class ConfigurationProfile:
    """設定プロファイルエンティティ"""

    def __init__(
        self,
        profile_id: str,
        name: str,
        environment: str = "production",
        settings: dict | None = None,
        created_at: str | None = None,
        is_active: bool = False,
    ) -> None:
        if not name or not name.strip():
            msg = "Profile name cannot be empty"
            raise ValueError(msg)

        self.profile_id = profile_id
        self.name = name.strip()
        self.environment = environment
        self.settings = (settings or {}).copy()
        self.created_at = created_at
        self.is_active = is_active

    def activate(self) -> None:
        """プロファイルをアクティブ化"""
        self.is_active = True

    def update_setting(self, key: SettingKey, value: str | int | bool) -> None:
        """設定値を更新"""
        self.settings[key.key] = value.value

    def validate_settings(self) -> ValidationResult:
        """設定値を検証"""
        errors: list[Any] = []

        # 基本的な検証ルール
        for key, value in self.settings.items():
            if key == "quality.threshold":
                if not isinstance(value, int | float) or value < 0 or value > 100:
                    errors.append(
                        ValidationError(key="quality.threshold", message="Quality threshold must be between 0 and 100")
                    )
            elif key == "performance.timeout" and isinstance(value, str):
                errors.append(ValidationError(key="performance.timeout", message="Performance timeout must be numeric"))
            elif key == "infrastructure.log_level" and value not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
                errors.append(ValidationError(key="infrastructure.log_level", message="Invalid log level"))

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
