#!/usr/bin/env python3
"""TDD RED: 設定ドメインサービスのテスト

SPEC-CONFIGURATION-001準拠のテスト実装
"""

import pytest

from noveler.domain.configuration.entities.configuration_profile import ConfigurationProfile
from noveler.domain.configuration.services.configuration_migration_service import ConfigurationMigrationService
from noveler.domain.configuration.services.configuration_validation_service import ConfigurationValidationService
from noveler.domain.configuration.value_objects.environment import Environment
from noveler.domain.configuration.value_objects.profile_id import ProfileId
from noveler.domain.configuration.value_objects.setting_key import SettingCategory, SettingKey
from noveler.domain.configuration.value_objects.setting_value import SettingValue, SettingValueType
from noveler.domain.value_objects.project_time import project_now


@pytest.mark.spec("SPEC-CONFIGURATION-001")
class TestConfigurationValidationService:
    """ConfigurationValidationService ドメインサービスのテスト"""

    def setUp(self) -> None:
        """テストセットアップ"""
        self.validation_service = ConfigurationValidationService()

    @pytest.mark.spec("SPEC-CONFIGURATION_SERVICES-VALIDATE_PROFILE_WIT")
    def test_validate_profile_with_valid_settings(self) -> None:
        """正常な設定のプロファイル検証"""
        # Given
        self.setUp()
        profile = self._create_valid_profile()

        # When
        result = self.validation_service.validate_profile(profile)

        # Then
        assert result.is_valid is True
        assert len(result.errors) == 0

    @pytest.mark.spec("SPEC-CONFIGURATION_SERVICES-VALIDATE_PROFILE_WIT")
    def test_validate_profile_with_invalid_quality_threshold(self) -> None:
        """無効な品質閾値のプロファイル検証"""
        # Given
        self.setUp()
        profile = self._create_invalid_profile()

        # When
        result = self.validation_service.validate_profile(profile)

        # Then
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("quality.threshold" in error.key for error in result.errors)

    @pytest.mark.spec("SPEC-CONFIGURATION_SERVICES-VALIDATE_SETTING_CON")
    def test_validate_setting_constraints_with_valid_float(self) -> None:
        """正常なFloat設定値の制約検証"""
        # Given
        self.setUp()
        setting_key = SettingKey("quality.threshold", SettingCategory.QUALITY)
        setting_value = SettingValue(70.0, SettingValueType.FLOAT, {"min": 0.0, "max": 100.0})

        # When
        is_valid = self.validation_service.validate_setting_constraints(setting_key, setting_value)

        # Then
        assert is_valid is True

    @pytest.mark.spec("SPEC-CONFIGURATION_SERVICES-VALIDATE_SETTING_CON")
    def test_validate_setting_constraints_with_invalid_float(self) -> None:
        """無効なFloat設定値の制約検証"""
        # Given
        self.setUp()
        setting_key = SettingKey("quality.threshold", SettingCategory.QUALITY)

        # When/Then - 制約違反値の検証
        try:
            setting_value = SettingValue(150.0, SettingValueType.FLOAT, {"min": 0.0, "max": 100.0})
            is_valid = self.validation_service.validate_setting_constraints(setting_key, setting_value)
            # もし例外が発生しなかった場合は、is_validがFalseであることを確認
            assert is_valid is False
        except ValueError:
            # 制約違反で例外が発生するのも正常な動作
            pass

    @pytest.mark.spec("SPEC-CONFIGURATION_SERVICES-VALIDATE_SETTING_CON")
    def test_validate_setting_constraints_with_string_enum(self) -> None:
        """文字列列挙型設定値の制約検証"""
        # Given
        self.setUp()
        setting_key = SettingKey("infrastructure.log_level", SettingCategory.INFRASTRUCTURE)
        setting_value = SettingValue(
            "INFO", SettingValueType.STRING, {"allowed": ["DEBUG", "INFO", "WARNING", "ERROR"]}
        )

        # When
        is_valid = self.validation_service.validate_setting_constraints(setting_key, setting_value)

        # Then
        assert is_valid is True

    @pytest.mark.spec("SPEC-CONFIGURATION_SERVICES-VALIDATE_SETTING_CON")
    def test_validate_setting_constraints_with_invalid_string_enum(self) -> None:
        """無効な文字列列挙型設定値の制約検証"""
        # Given
        self.setUp()
        setting_key = SettingKey("infrastructure.log_level", SettingCategory.INFRASTRUCTURE)

        # When/Then - 制約違反値の検証
        try:
            setting_value = SettingValue(
                "INVALID", SettingValueType.STRING, {"allowed": ["DEBUG", "INFO", "WARNING", "ERROR"]}
            )
            is_valid = self.validation_service.validate_setting_constraints(setting_key, setting_value)
            assert is_valid is False
        except ValueError:
            # 制約違反で例外が発生するのも正常な動作
            pass

    def _create_valid_profile(self) -> ConfigurationProfile:
        """正常なテストプロファイルを作成"""
        return ConfigurationProfile(
            profile_id=ProfileId("valid-profile"),
            name="valid-settings",
            environment=Environment.DEVELOPMENT,
            settings={"quality.threshold": 70.0, "performance.timeout": 30, "infrastructure.log_level": "INFO"},
            created_at=project_now().datetime,
        )

    def _create_invalid_profile(self) -> ConfigurationProfile:
        """無効なテストプロファイルを作成"""
        return ConfigurationProfile(
            profile_id=ProfileId("invalid-profile"),
            name="invalid-settings",
            environment=Environment.DEVELOPMENT,
            settings={
                "quality.threshold": -10.0,  # 無効:負の値
                "performance.timeout": "not_a_number",  # 無効:文字列
                "infrastructure.log_level": "INVALID_LEVEL",  # 無効:許可されていない値
            },
            created_at=project_now().datetime,
        )


@pytest.mark.spec("SPEC-CONFIGURATION-001")
class TestConfigurationMigrationService:
    """ConfigurationMigrationService ドメインサービスのテスト"""

    def setUp(self) -> None:
        """テストセットアップ"""
        self.migration_service = ConfigurationMigrationService()

    @pytest.mark.spec("SPEC-CONFIGURATION_SERVICES-MIGRATE_LEGACY_SETTI")
    def test_migrate_legacy_settings_to_new_format(self) -> None:
        """レガシー設定を新形式に移行"""
        # Given
        self.setUp()
        legacy_settings = {
            "quality_threshold": 70.0,
            "coverage_threshold": 60.0,
            "complexity_threshold": 10,
            "marathon_session_threshold_hours": 4.0,
            "log_level": "INFO",
        }

        # When
        profile = self.migration_service.migrate_legacy_settings(legacy_settings)

        # Then
        assert isinstance(profile, ConfigurationProfile)
        assert profile.environment == Environment.DEVELOPMENT  # デフォルト環境
        assert profile.settings["quality.threshold"] == 70.0
        assert profile.settings["quality.coverage_threshold"] == 60.0
        assert profile.settings["performance.complexity_threshold"] == 10
        assert profile.settings["performance.marathon_session_threshold_hours"] == 4.0
        assert profile.settings["infrastructure.log_level"] == "INFO"

    @pytest.mark.spec("SPEC-CONFIGURATION_SERVICES-MIGRATE_LEGACY_SETTI")
    def test_migrate_legacy_settings_with_missing_values(self) -> None:
        """欠損値を含むレガシー設定の移行"""
        # Given
        self.setUp()
        incomplete_legacy_settings = {
            "quality_threshold": 70.0
            # 他の設定は欠損
        }

        # When
        profile = self.migration_service.migrate_legacy_settings(incomplete_legacy_settings)

        # Then
        assert isinstance(profile, ConfigurationProfile)
        assert profile.settings["quality.threshold"] == 70.0
        # デフォルト値が設定されることを確認
        assert "quality.coverage_threshold" in profile.settings
        assert "performance.complexity_threshold" in profile.settings

    @pytest.mark.spec("SPEC-CONFIGURATION_SERVICES-MIGRATE_LEGACY_SETTI")
    def test_migrate_legacy_settings_with_invalid_values(self) -> None:
        """無効な値を含むレガシー設定の移行"""
        # Given
        self.setUp()
        invalid_legacy_settings = {
            "quality_threshold": "not_a_number",  # 無効な型
            "coverage_threshold": -10.0,  # 無効な値
        }

        # When/Then - Expect TypeError for type validation failure
        with pytest.raises(TypeError, match="Invalid legacy setting"):
            self.migration_service.migrate_legacy_settings(invalid_legacy_settings)
