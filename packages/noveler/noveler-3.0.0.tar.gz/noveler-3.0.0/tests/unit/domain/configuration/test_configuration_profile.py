#!/usr/bin/env python3
"""TDD RED: ConfigurationProfile エンティティのテスト

SPEC-CONFIGURATION-001準拠のテスト実装
"""

import pytest

from noveler.domain.configuration.entities.configuration_profile import ConfigurationProfile
from noveler.domain.configuration.value_objects.environment import Environment
from noveler.domain.configuration.value_objects.profile_id import ProfileId
from noveler.domain.configuration.value_objects.setting_key import SettingCategory, SettingKey
from noveler.domain.configuration.value_objects.setting_value import SettingValue, SettingValueType
from noveler.domain.value_objects.project_time import project_now


@pytest.mark.spec("SPEC-CONFIGURATION-001")
class TestConfigurationProfile:
    """ConfigurationProfile エンティティのテスト"""

    @pytest.mark.spec("SPEC-CONFIGURATION_PROFILE-CREATE_CONFIGURATION")
    def test_create_configuration_profile_with_valid_data(self):
        """正常なデータでConfigurationProfileを作成"""
        # Given
        profile_id = ProfileId("profile-001")
        name = "development-settings"
        environment = Environment.DEVELOPMENT
        settings = {"quality.threshold": 70.0, "performance.timeout": 30}
        created_at = project_now().datetime

        # When
        profile = ConfigurationProfile(
            profile_id=profile_id, name=name, environment=environment, settings=settings, created_at=created_at
        )

        # Then
        assert profile.profile_id == profile_id
        assert profile.name == name
        assert profile.environment == environment
        assert profile.settings == settings
        assert profile.created_at == created_at
        assert profile.is_active is False  # デフォルトは非アクティブ

    @pytest.mark.spec("SPEC-CONFIGURATION_PROFILE-ACTIVATE_PROFILE_SET")
    def test_activate_profile_sets_active_flag(self):
        """プロファイルをアクティブ化"""
        # Given
        profile = self._create_test_profile()

        # When
        profile.activate()

        # Then
        assert profile.is_active is True

    @pytest.mark.spec("SPEC-CONFIGURATION_PROFILE-UPDATE_SETTING_MODIF")
    def test_update_setting_modifies_settings_dict(self):
        """設定値を更新"""
        # Given
        profile = self._create_test_profile()
        setting_key = SettingKey("quality.threshold", SettingCategory.QUALITY)
        setting_value = SettingValue(80.0, SettingValueType.FLOAT, {"min": 0.0, "max": 100.0})

        # When
        profile.update_setting(setting_key, setting_value)

        # Then
        assert profile.settings["quality.threshold"] == 80.0

    @pytest.mark.spec("SPEC-CONFIGURATION_PROFILE-VALIDATE_SETTINGS_RE")
    def test_validate_settings_returns_valid_result_for_correct_settings(self):
        """正しい設定値の検証"""
        # Given
        profile = self._create_test_profile()

        # When
        result = profile.validate_settings()

        # Then
        assert result.is_valid is True
        assert len(result.errors) == 0

    @pytest.mark.spec("SPEC-CONFIGURATION_PROFILE-VALIDATE_SETTINGS_RE")
    def test_validate_settings_returns_invalid_result_for_incorrect_settings(self):
        """不正な設定値の検証"""
        # Given
        profile = self._create_test_profile()
        profile.settings["quality.threshold"] = -10.0  # 無効な値

        # When
        result = profile.validate_settings()

        # Then
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert "quality.threshold" in str(result.errors[0])

    @pytest.mark.spec("SPEC-CONFIGURATION_PROFILE-CANNOT_CREATE_PROFIL")
    def test_cannot_create_profile_with_invalid_profile_id(self):
        """無効なプロファイルIDでの作成は失敗"""
        # Given/When/Then
        with pytest.raises(ValueError, match="ProfileID cannot be empty"):
            ProfileId("")

    @pytest.mark.spec("SPEC-CONFIGURATION_PROFILE-CANNOT_CREATE_PROFIL")
    def test_cannot_create_profile_with_invalid_name(self):
        """無効な名前でのプロファイル作成は失敗"""
        # Given/When/Then
        with pytest.raises(ValueError, match="Profile name cannot be empty"):
            ConfigurationProfile(
                profile_id=ProfileId("valid-id"),
                name="",  # 空文字は無効
                environment=Environment.DEVELOPMENT,
                settings={},
                created_at=project_now().datetime,
            )

    def _create_test_profile(self) -> ConfigurationProfile:
        """テスト用プロファイルを作成"""
        return ConfigurationProfile(
            profile_id=ProfileId("test-profile"),
            name="test-settings",
            environment=Environment.DEVELOPMENT,
            settings={"quality.threshold": 70.0, "performance.timeout": 30},
            created_at=project_now().datetime,
        )
