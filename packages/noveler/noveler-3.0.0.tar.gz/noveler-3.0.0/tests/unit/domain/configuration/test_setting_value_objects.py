#!/usr/bin/env python3
"""TDD RED: 設定値オブジェクトのテスト

SPEC-CONFIGURATION-001準拠のテスト実装
"""

import pytest

from noveler.domain.configuration.value_objects.environment import Environment
from noveler.domain.configuration.value_objects.profile_id import ProfileId
from noveler.domain.configuration.value_objects.setting_key import SettingCategory, SettingKey
from noveler.domain.configuration.value_objects.setting_value import SettingValue, SettingValueType


@pytest.mark.spec("SPEC-CONFIGURATION-001")
class TestProfileId:
    """ProfileId 値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-SETTING_VALUE_OBJECTS-CREATE_VALID_PROFILE")
    def test_create_valid_profile_id(self):
        """正常なProfileIDを作成"""
        # Given/When
        profile_id = ProfileId("profile-001")

        # Then
        assert profile_id.value == "profile-001"
        assert str(profile_id) == "profile-001"

    @pytest.mark.spec("SPEC-SETTING_VALUE_OBJECTS-PROFILE_ID_EQUALITY")
    def test_profile_id_equality(self):
        """ProfileIDの等価性チェック"""
        # Given
        profile_id1 = ProfileId("same-id")
        profile_id2 = ProfileId("same-id")
        profile_id3 = ProfileId("different-id")

        # When/Then
        assert profile_id1 == profile_id2
        assert profile_id1 != profile_id3

    @pytest.mark.spec("SPEC-SETTING_VALUE_OBJECTS-CANNOT_CREATE_EMPTY_")
    def test_cannot_create_empty_profile_id(self):
        """空のProfileIDは作成不可"""
        # Given/When/Then
        with pytest.raises(ValueError, match="ProfileID cannot be empty"):
            ProfileId("")

    @pytest.mark.spec("SPEC-SETTING_VALUE_OBJECTS-CANNOT_CREATE_WHITES")
    def test_cannot_create_whitespace_only_profile_id(self):
        """空白のみのProfileIDは作成不可"""
        # Given/When/Then
        with pytest.raises(ValueError, match="ProfileID cannot be empty"):
            ProfileId("   ")


@pytest.mark.spec("SPEC-CONFIGURATION-001")
class TestEnvironment:
    """Environment 列挙型のテスト"""

    @pytest.mark.spec("SPEC-SETTING_VALUE_OBJECTS-ENVIRONMENT_ENUM_VAL")
    def test_environment_enum_values(self):
        """環境列挙型の値を確認"""
        # Given/When/Then
        assert Environment.DEVELOPMENT.value == "development"
        assert Environment.TESTING.value == "testing"
        assert Environment.STAGING.value == "staging"
        assert Environment.PRODUCTION.value == "production"

    @pytest.mark.spec("SPEC-SETTING_VALUE_OBJECTS-ENVIRONMENT_FROM_STR")
    def test_environment_from_string(self):
        """文字列から環境を作成"""
        # Given/When
        env = Environment("development")

        # Then
        assert env == Environment.DEVELOPMENT


@pytest.mark.spec("SPEC-CONFIGURATION-001")
class TestSettingKey:
    """SettingKey 値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-SETTING_VALUE_OBJECTS-CREATE_VALID_SETTING")
    def test_create_valid_setting_key(self):
        """正常なSettingKeyを作成"""
        # Given/When
        setting_key = SettingKey("quality.threshold", SettingCategory.QUALITY)

        # Then
        assert setting_key.key == "quality.threshold"
        assert setting_key.category == SettingCategory.QUALITY

    @pytest.mark.spec("SPEC-SETTING_VALUE_OBJECTS-SETTING_KEY_EQUALITY")
    def test_setting_key_equality(self):
        """SettingKeyの等価性チェック"""
        # Given
        key1 = SettingKey("quality.threshold", SettingCategory.QUALITY)
        key2 = SettingKey("quality.threshold", SettingCategory.QUALITY)
        key3 = SettingKey("performance.timeout", SettingCategory.PERFORMANCE)

        # When/Then
        assert key1 == key2
        assert key1 != key3

    @pytest.mark.spec("SPEC-SETTING_VALUE_OBJECTS-CANNOT_CREATE_EMPTY_")
    def test_cannot_create_empty_setting_key(self):
        """空のキーは作成不可"""
        # Given/When/Then
        with pytest.raises(ValueError, match="Setting key cannot be empty"):
            SettingKey("", SettingCategory.QUALITY)

    @pytest.mark.spec("SPEC-SETTING_VALUE_OBJECTS-SETTING_KEY_VALIDATI")
    def test_setting_key_validation_with_invalid_format(self):
        """無効な形式のキーは作成不可"""
        # Given/When/Then
        with pytest.raises(ValueError, match="Setting key must contain"):
            SettingKey("invalid_key_format", SettingCategory.QUALITY)


@pytest.mark.spec("SPEC-CONFIGURATION-001")
class TestSettingValue:
    """SettingValue 値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-SETTING_VALUE_OBJECTS-CREATE_FLOAT_SETTING")
    def test_create_float_setting_value(self):
        """Float型設定値を作成"""
        # Given/When
        setting_value = SettingValue(70.0, SettingValueType.FLOAT, {"min": 0.0, "max": 100.0})

        # Then
        assert setting_value.value == 70.0
        assert setting_value.value_type == SettingValueType.FLOAT
        assert setting_value.constraints["min"] == 0.0
        assert setting_value.constraints["max"] == 100.0

    @pytest.mark.spec("SPEC-SETTING_VALUE_OBJECTS-CREATE_INTEGER_SETTI")
    def test_create_integer_setting_value(self):
        """Integer型設定値を作成"""
        # Given/When
        setting_value = SettingValue(30, SettingValueType.INTEGER, {"min": 1, "max": 60})

        # Then
        assert setting_value.value == 30
        assert setting_value.value_type == SettingValueType.INTEGER

    @pytest.mark.spec("SPEC-SETTING_VALUE_OBJECTS-CREATE_STRING_SETTIN")
    def test_create_string_setting_value(self):
        """String型設定値を作成"""
        # Given/When
        setting_value = SettingValue(
            "INFO", SettingValueType.STRING, {"allowed": ["DEBUG", "INFO", "WARNING", "ERROR"]}
        )

        # Then
        assert setting_value.value == "INFO"
        assert setting_value.value_type == SettingValueType.STRING

    @pytest.mark.spec("SPEC-SETTING_VALUE_OBJECTS-SETTING_VALUE_VALIDA")
    def test_setting_value_validation_with_constraints(self):
        """制約に基づく設定値検証"""
        # Given/When/Then - 制約を満たす値
        valid_value = SettingValue(50.0, SettingValueType.FLOAT, {"min": 0.0, "max": 100.0})
        assert valid_value.is_valid() is True

    @pytest.mark.spec("SPEC-SETTING_VALUE_OBJECTS-SETTING_VALUE_VALIDA")
    def test_setting_value_validation_fails_with_invalid_constraints(self):
        """制約を満たさない設定値は無効"""
        # Given/When/Then
        with pytest.raises(ValueError, match="Value 150.0 exceeds maximum"):
            SettingValue(150.0, SettingValueType.FLOAT, {"min": 0.0, "max": 100.0})

    @pytest.mark.spec("SPEC-SETTING_VALUE_OBJECTS-SETTING_VALUE_TYPE_M")
    def test_setting_value_type_mismatch_validation(self):
        """型不一致の設定値は無効"""
        # Given/When/Then
        with pytest.raises(ValueError, match="Value type mismatch"):
            SettingValue("not a number", SettingValueType.FLOAT)


@pytest.mark.spec("SPEC-CONFIGURATION-001")
class TestSettingCategory:
    """SettingCategory 列挙型のテスト"""

    @pytest.mark.spec("SPEC-SETTING_VALUE_OBJECTS-SETTING_CATEGORY_ENU")
    def test_setting_category_enum_values(self):
        """設定カテゴリ列挙型の値を確認"""
        # Given/When/Then
        assert SettingCategory.QUALITY.value == "quality"
        assert SettingCategory.PERFORMANCE.value == "performance"
        assert SettingCategory.INFRASTRUCTURE.value == "infrastructure"
        assert SettingCategory.FEATURE.value == "feature"
        assert SettingCategory.SECURITY.value == "security"
