"""ConfigurationValidationService ドメインサービス

SPEC-CONFIGURATION-001準拠
"""

from noveler.domain.configuration.entities.configuration_profile import ConfigurationProfile, ValidationResult
from noveler.domain.configuration.value_objects.setting_key import SettingKey


class ConfigurationValidationService:
    """設定検証ドメインサービス"""

    def validate_profile(self, profile: ConfigurationProfile) -> ValidationResult:
        """プロファイル全体の整合性を検証"""
        return profile.validate_settings()

    def validate_setting_constraints(self, _setting_key: SettingKey, setting_value: str | int | bool) -> bool:
        """設定値の制約を検証"""
        try:
            # SettingValueのコンストラクタが例外を投げる場合もテスト用に処理
            return setting_value.is_valid()
        except ValueError:
            return False
