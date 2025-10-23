#!/usr/bin/env python3
"""設定セクション値オブジェクトのテスト

REQ-1.2: 型安全な設定値アクセス機能のテスト実装
"""

import pytest

from noveler.domain.value_objects.configuration_section import ConfigurationSection

pytestmark = pytest.mark.vo_smoke



@pytest.mark.spec("SPEC-CONFIG-001")
class TestConfigurationSection:
    @pytest.mark.spec("SPEC-CONFIGURATION_SECTION-GET_STRING_VALUE_RET")
    def test_get_string_value_returns_string_when_exists(self):
        """仕様要件REQ-1.2: 文字列設定値の正常取得"""
        # Arrange
        data = {"app_name": "小説執筆支援システム", "version": "1.0.0"}
        section = ConfigurationSection("system", data)

        # Act
        result = section.get_string("app_name")

        # Assert
        assert result == "小説執筆支援システム"

    @pytest.mark.spec("SPEC-CONFIGURATION_SECTION-GET_STRING_VALUE_RET")
    def test_get_string_value_returns_default_when_not_exists(self):
        """仕様要件REQ-1.4: 存在しないキーでのデフォルト値返却"""
        # Arrange
        data = {"app_name": "小説執筆支援システム"}
        section = ConfigurationSection("system", data)

        # Act
        result = section.get_string("missing_key", "default")

        # Assert
        assert result == "default"

    @pytest.mark.spec("SPEC-CONFIGURATION_SECTION-GET_INT_VALUE_RETURN")
    def test_get_int_value_returns_int_when_exists(self):
        """仕様要件REQ-1.2: 整数設定値の正常取得"""
        # Arrange
        data = {"timeout_ms": 2000}
        section = ConfigurationSection("system", data)

        # Act
        result = section.get_int("timeout_ms")

        # Assert
        assert result == 2000

    @pytest.mark.spec("SPEC-CONFIGURATION_SECTION-GET_BOOL_VALUE_RETUR")
    def test_get_bool_value_returns_bool_when_exists(self):
        """仕様要件REQ-1.2: 真偽値設定値の正常取得"""
        # Arrange
        data = {"debug": True, "verbose": False}
        section = ConfigurationSection("system", data)

        # Act
        debug_result = section.get_bool("debug")
        verbose_result = section.get_bool("verbose")

        # Assert
        assert debug_result is True
        assert verbose_result is False

    @pytest.mark.spec("SPEC-CONFIGURATION_SECTION-GET_NESTED_VALUE_RET")
    def test_get_nested_value_returns_correct_value(self):
        """仕様要件REQ-1.2: ネストされた設定値の取得"""
        # Arrange
        data = {"logging": {"level": "INFO", "file_logging": {"enabled": True}}}
        section = ConfigurationSection("root", data)

        # Act
        level = section.get_nested_string(["logging", "level"])
        enabled = section.get_nested_bool(["logging", "file_logging", "enabled"])

        # Assert
        assert level == "INFO"
        assert enabled is True

    @pytest.mark.spec("SPEC-CONFIGURATION_SECTION-SECTION_NAME_PROPERT")
    def test_section_name_property_returns_correct_name(self):
        """仕様要件REQ-1.2: セクション名の正常取得"""
        # Arrange
        section = ConfigurationSection("system", {})

        # Act & Assert
        assert section.section_name == "system"
