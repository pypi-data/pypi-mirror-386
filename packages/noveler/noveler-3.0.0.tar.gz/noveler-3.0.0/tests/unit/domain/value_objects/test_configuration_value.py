#!/usr/bin/env python3
"""設定値管理値オブジェクトのユニットテスト

TDD原則に従い、値オブジェクトの不変条件とビジネスロジックをテスト


仕様書: SPEC-DOMAIN-VALUE-OBJECTS
"""

import pytest

from noveler.domain.value_objects.configuration_value import (
    ConfigurationHierarchy,
    ConfigurationLevel,
    ConfigurationSource,
    ConfigurationValue,
    DefaultConfiguration,
    EnvironmentConfiguration,
)

pytestmark = pytest.mark.vo_smoke


class TestConfigurationLevel:
    """ConfigurationLevel列挙型のテスト"""

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-CONFIGURATION_LEVELS")
    def test_configuration_levels_defined(self) -> None:
        """設定階層レベルが定義されている"""
        assert ConfigurationLevel.ENVIRONMENT.value == "env"
        assert ConfigurationLevel.PROJECT.value == "project"
        assert ConfigurationLevel.GLOBAL.value == "global"
        assert ConfigurationLevel.DEFAULT.value == "default"

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-ALL_LEVELS_PRESENT")
    def test_all_levels_present(self) -> None:
        """全レベルが存在することを確認"""
        expected_levels = {"ENVIRONMENT", "PROJECT", "GLOBAL", "DEFAULT"}
        actual_levels = {level.name for level in ConfigurationLevel}
        assert actual_levels == expected_levels


class TestConfigurationSource:
    """ConfigurationSource値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-CREATE_VALID_ENVIRON")
    def test_create_valid_environment_source(self) -> None:
        """環境変数ソースの作成(正常)"""
        # When
        source = ConfigurationSource(level=ConfigurationLevel.ENVIRONMENT, path=None)

        # Then
        assert source.level == ConfigurationLevel.ENVIRONMENT
        assert source.path is None

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-CREATE_VALID_PROJECT")
    def test_create_valid_project_source(self) -> None:
        """プロジェクトソースの作成(正常)"""
        # When
        source = ConfigurationSource(level=ConfigurationLevel.PROJECT, path="/project/config.yaml")

        # Then
        assert source.level == ConfigurationLevel.PROJECT
        assert source.path == "/project/config.yaml"

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-CREATE_VALID_GLOBAL_")
    def test_create_valid_global_source(self) -> None:
        """グローバルソースの作成(正常)"""
        # When
        source = ConfigurationSource(level=ConfigurationLevel.GLOBAL, path="~/.novel/config.yaml")

        # Then
        assert source.level == ConfigurationLevel.GLOBAL
        assert source.path == "~/.novel/config.yaml"

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-PROJECT_LEVEL_REQUIR")
    def test_project_level_requires_path(self) -> None:
        """プロジェクトレベルはパスが必須"""
        # When & Then
        with pytest.raises(ValueError) as exc:
            ConfigurationSource(level=ConfigurationLevel.PROJECT, path=None)
        assert "project level requires a path" in str(exc.value)

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-GLOBAL_LEVEL_REQUIRE")
    def test_global_level_requires_path(self) -> None:
        """グローバルレベルはパスが必須"""
        # When & Then
        with pytest.raises(ValueError) as exc:
            ConfigurationSource(level=ConfigurationLevel.GLOBAL, path=None)
        assert "global level requires a path" in str(exc.value)

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-DEFAULT_LEVEL_PATH_O")
    def test_default_level_path_optional(self) -> None:
        """デフォルトレベルはパスがオプション"""
        # When
        source = ConfigurationSource(level=ConfigurationLevel.DEFAULT, path=None)

        # Then
        assert source.level == ConfigurationLevel.DEFAULT
        assert source.path is None

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-IMMUTABILITY")
    def test_immutability(self) -> None:
        """値オブジェクトの不変性"""
        # Given
        source = ConfigurationSource(level=ConfigurationLevel.ENVIRONMENT, path=None)

        # When & Then
        with pytest.raises(AttributeError, match=".*"):
            source.level = ConfigurationLevel.PROJECT

        with pytest.raises(AttributeError, match=".*"):
            source.path = "/new/path"


class TestConfigurationValue:
    """ConfigurationValue値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-CREATE_VALID_CONFIGU")
    def test_create_valid_configuration_value(self) -> None:
        """有効な設定値の作成"""
        # Given
        source = ConfigurationSource(level=ConfigurationLevel.PROJECT, path="/project/config.yaml")

        # When
        config_value = ConfigurationValue(key="quality.threshold", value=80, source=source)

        # Then
        assert config_value.key == "quality.threshold"
        assert config_value.value == 80
        assert config_value.source == source

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-EMPTY_KEY_VALIDATION")
    def test_empty_key_validation(self) -> None:
        """空のキーの検証"""
        # Given
        source = ConfigurationSource(level=ConfigurationLevel.DEFAULT, path=None)

        # When & Then
        with pytest.raises(ValueError) as exc:
            ConfigurationValue(key="", value=100, source=source)
        assert "Configuration key cannot be empty" in str(exc.value)

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-VARIOUS_VALUE_TYPES")
    def test_various_value_types(self) -> None:
        """様々な値の型をサポート"""
        # Given
        source = ConfigurationSource(level=ConfigurationLevel.DEFAULT, path=None)

        # String value
        config1 = ConfigurationValue(key="author.name", value="テスト作者", source=source)
        assert config1.value == "テスト作者"

        # Boolean value
        config2 = ConfigurationValue(key="quality.enabled", value=True, source=source)
        assert config2.value is True

        # List value
        config3 = ConfigurationValue(key="genres", value=["ファンタジー", "冒険"], source=source)
        assert config3.value == ["ファンタジー", "冒険"]

        # Dict value
        config4 = ConfigurationValue(key="settings", value={"theme": "dark", "lang": "ja"}, source=source)
        assert config4.value == {"theme": "dark", "lang": "ja"}

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-IMMUTABILITY")
    def test_immutability(self) -> None:
        """値オブジェクトの不変性"""
        # Given
        source = ConfigurationSource(level=ConfigurationLevel.DEFAULT, path=None)
        config_value = ConfigurationValue(key="test.key", value=100, source=source)

        # When & Then
        with pytest.raises(AttributeError, match=".*"):
            config_value.key = "new.key"

        with pytest.raises(AttributeError, match=".*"):
            config_value.value = 200

        with pytest.raises(AttributeError, match=".*"):
            config_value.source = source


class TestConfigurationHierarchy:
    """ConfigurationHierarchy値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-CREATE_EMPTY_HIERARC")
    def test_create_empty_hierarchy(self) -> None:
        """空の階層設定の作成"""
        # When
        hierarchy = ConfigurationHierarchy()

        # Then
        assert hierarchy.sources == {}
        assert hierarchy.project_root is None
        # Note: global_config_pathはPath型を使うためテストできない

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-GET_MERGED_CONFIG_EM")
    def test_get_merged_config_empty(self) -> None:
        """空の階層設定のマージ"""
        # Given
        hierarchy = ConfigurationHierarchy()

        # When
        merged = hierarchy.get_merged_config()

        # Then
        assert merged == {}

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-GET_MERGED_CONFIG_SI")
    def test_get_merged_config_single_level(self) -> None:
        """単一レベルの設定マージ"""
        # Given
        hierarchy = ConfigurationHierarchy(
            sources={ConfigurationLevel.DEFAULT: {"quality": {"threshold": 80}, "author": {"name": "Default Author"}}}
        )

        # When
        merged = hierarchy.get_merged_config()

        # Then
        assert merged == {"quality": {"threshold": 80}, "author": {"name": "Default Author"}}

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-GET_MERGED_CONFIG_OV")
    def test_get_merged_config_override_priority(self) -> None:
        """優先順位に従った設定マージ"""
        # Given
        hierarchy = ConfigurationHierarchy(
            sources={
                ConfigurationLevel.DEFAULT: {"quality": {"threshold": 70}, "author": {"name": "Default"}},
                ConfigurationLevel.PROJECT: {"quality": {"threshold": 85}},
                ConfigurationLevel.ENVIRONMENT: {"quality": {"threshold": 90}},
            }
        )

        # When
        merged = hierarchy.get_merged_config()

        # Then
        # ENVIRONMENT > PROJECT > DEFAULT
        assert merged["quality"]["threshold"] == 90
        assert merged["author"]["name"] == "Default"

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-GET_MERGED_CONFIG_DE")
    def test_get_merged_config_deep_merge(self) -> None:
        """深いマージの動作確認"""
        # Given
        hierarchy = ConfigurationHierarchy(
            sources={
                ConfigurationLevel.DEFAULT: {"writing": {"editor": "vim", "auto_save": True, "theme": "dark"}},
                ConfigurationLevel.PROJECT: {"writing": {"editor": "vscode", "font_size": 14}},
            }
        )

        # When
        merged = hierarchy.get_merged_config()

        # Then
        assert merged["writing"]["editor"] == "vscode"  # Overridden
        assert merged["writing"]["auto_save"] is True  # Inherited
        assert merged["writing"]["theme"] == "dark"  # Inherited
        assert merged["writing"]["font_size"] == 14  # New key

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-GET_VALUE_WITH_DOT_N")
    def test_get_value_with_dot_notation(self) -> None:
        """ドット記法での値取得"""
        # Given
        hierarchy = ConfigurationHierarchy(
            sources={ConfigurationLevel.DEFAULT: {"quality": {"checks": {"enabled": True, "threshold": 80}}}}
        )

        # When
        enabled = hierarchy.get_value("quality.checks.enabled")
        threshold = hierarchy.get_value("quality.checks.threshold")
        missing = hierarchy.get_value("quality.checks.missing", "default_value")

        # Then
        assert enabled is True
        assert threshold == 80
        assert missing == "default_value"

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-GET_VALUE_WITH_SOURC")
    def test_get_value_with_source_found(self) -> None:
        """ソース情報付きで値を取得(見つかった場合)"""
        # Given
        hierarchy = ConfigurationHierarchy(
            sources={
                ConfigurationLevel.DEFAULT: {"quality": {"threshold": 70}},
                ConfigurationLevel.PROJECT: {"quality": {"threshold": 85}},
            }
        )

        # When
        config_value = hierarchy.get_value_with_source("quality.threshold")

        # Then
        assert config_value is not None
        assert config_value.key == "quality.threshold"
        assert config_value.value == 85  # PROJECT level wins
        assert config_value.source.level == ConfigurationLevel.PROJECT

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-GET_VALUE_WITH_SOURC")
    def test_get_value_with_source_not_found(self) -> None:
        """ソース情報付きで値を取得(見つからない場合)"""
        # Given
        hierarchy = ConfigurationHierarchy(sources={ConfigurationLevel.DEFAULT: {"quality": {"threshold": 70}}})

        # When
        config_value = hierarchy.get_value_with_source("missing.key")

        # Then
        assert config_value is None

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-SET_VALUE_PROJECT_LE")
    def test_set_value_project_level(self) -> None:
        """プロジェクトレベルへの値設定"""
        # Given
        hierarchy = ConfigurationHierarchy()

        # When
        hierarchy.set_value("quality.threshold", 85, ConfigurationLevel.PROJECT)

        # Then
        assert hierarchy.sources[ConfigurationLevel.PROJECT] == {"quality": {"threshold": 85}}

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-SET_VALUE_GLOBAL_LEV")
    def test_set_value_global_level(self) -> None:
        """グローバルレベルへの値設定"""
        # Given
        hierarchy = ConfigurationHierarchy()

        # When
        hierarchy.set_value("author.name", "Test Author", ConfigurationLevel.GLOBAL)

        # Then
        assert hierarchy.sources[ConfigurationLevel.GLOBAL] == {"author": {"name": "Test Author"}}

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-SET_VALUE_INVALID_LE")
    def test_set_value_invalid_level(self) -> None:
        """無効なレベルへの値設定"""
        # Given
        hierarchy = ConfigurationHierarchy()

        # When & Then
        with pytest.raises(ValueError) as exc:
            hierarchy.set_value("test.key", "value", ConfigurationLevel.ENVIRONMENT)
        assert "Can only set values for GLOBAL or PROJECT levels" in str(exc.value)

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-SET_VALUE_TYPE_CONVE")
    def test_set_value_type_conversion(self) -> None:
        """値設定時の型変換"""
        # Given
        hierarchy = ConfigurationHierarchy()

        # When
        hierarchy._set_nested_value({}, "bool_true", "true")
        hierarchy._set_nested_value({}, "bool_false", "false")
        hierarchy._set_nested_value({}, "int_value", "123")
        hierarchy._set_nested_value({}, "float_value", "123.45")
        hierarchy._set_nested_value({}, "string_value", "hello")

        # Then
        config = {}
        hierarchy._set_nested_value(config, "bool_true", "true")
        assert config["bool_true"] is True

        hierarchy._set_nested_value(config, "bool_false", "false")
        assert config["bool_false"] is False

        hierarchy._set_nested_value(config, "int_value", "123")
        assert config["int_value"] == 123

        hierarchy._set_nested_value(config, "float_value", "123.45")
        assert config["float_value"] == 123.45

        hierarchy._set_nested_value(config, "string_value", "hello")
        assert config["string_value"] == "hello"

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-GET_CONFIG_SOURCES")
    def test_get_config_sources(self) -> None:
        """各設定項目のソース取得"""
        # Given
        hierarchy = ConfigurationHierarchy(
            sources={
                ConfigurationLevel.DEFAULT: {"quality": {"threshold": 70}, "author": {"name": "Default"}},
                ConfigurationLevel.PROJECT: {"quality": {"threshold": 85}},
            }
        )

        # When
        sources = hierarchy.get_config_sources()

        # Then
        assert "quality.threshold" in sources
        assert ConfigurationLevel.DEFAULT in sources["quality.threshold"]
        assert ConfigurationLevel.PROJECT in sources["quality.threshold"]
        assert "author.name" in sources
        assert ConfigurationLevel.DEFAULT in sources["author.name"]


class TestDefaultConfiguration:
    """DefaultConfiguration値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-GET_DEFAULT_CONFIG_S")
    def test_get_default_config_structure(self) -> None:
        """デフォルト設定の構造確認"""
        # When
        config = DefaultConfiguration.get_default_config()

        # Then
        assert "default_author" in config
        assert "default_project" in config
        assert "writing_environment" in config
        assert "quality_management" in config

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-DEFAULT_AUTHOR_CONFI")
    def test_default_author_config(self) -> None:
        """デフォルト作者設定"""
        # When
        config = DefaultConfiguration.get_default_config()

        # Then
        assert config["default_author"]["pen_name"] == "Unknown Author"

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-DEFAULT_PROJECT_CONF")
    def test_default_project_config(self) -> None:
        """デフォルトプロジェクト設定"""
        # When
        config = DefaultConfiguration.get_default_config()

        # Then
        project = config["default_project"]
        assert project["genre"] == "ファンタジー"
        assert project["target_platform"] == "小説家になろう"
        assert project["min_length_per_episode"] == 4000
        # target_length_per_episode と max_length_per_episode は削除済み

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-WRITING_ENVIRONMENT_")
    def test_writing_environment_config(self) -> None:
        """執筆環境設定"""
        # When
        config = DefaultConfiguration.get_default_config()

        # Then
        env = config["writing_environment"]
        assert env["preferred_editor"] == "code"
        assert env["auto_save"]["enabled"] is True
        assert env["auto_save"]["interval_minutes"] == 10
        assert env["backup"]["enabled"] is True
        assert env["backup"]["keep_versions"] == 5

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-QUALITY_MANAGEMENT_C")
    def test_quality_management_config(self) -> None:
        """品質管理設定"""
        # When
        config = DefaultConfiguration.get_default_config()

        # Then
        quality = config["quality_management"]
        assert quality["default_threshold"] == 80
        assert quality["auto_check"]["on_complete"] is True

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-IMMUTABILITY_OF_RETU")
    def test_immutability_of_returned_config(self) -> None:
        """返される設定の不変性(辞書は変更可能だが、メソッドは副作用なし)"""
        # When
        config1 = DefaultConfiguration.get_default_config()
        config2 = DefaultConfiguration.get_default_config()

        # Then
        # 同じ構造を返すが、別のインスタンス
        assert config1 == config2
        assert config1 is not config2

        # 一方を変更しても他方に影響しない
        config1["default_author"]["pen_name"] = "Modified Author"
        assert config2["default_author"]["pen_name"] == "Unknown Author"


class TestEnvironmentConfiguration:
    """EnvironmentConfiguration値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-LOAD_FROM_ENVIRONMEN")
    def test_load_from_environment_none(self) -> None:
        """環境変数なしの場合"""
        # When
        config = EnvironmentConfiguration.load_from_environment(None)

        # Then
        assert config == {}

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-LOAD_FROM_ENVIRONMEN")
    def test_load_from_environment_empty(self) -> None:
        """空の環境変数辞書"""
        # When
        config = EnvironmentConfiguration.load_from_environment({})

        # Then
        assert config == {}

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-LOAD_FROM_ENVIRONMEN")
    def test_load_from_environment_with_novel_prefix(self) -> None:
        """NOVEL_プレフィックス付き環境変数の読み込み"""
        # Given
        env_vars = {
            "NOVEL_AUTHOR_PEN_NAME": "Test Author",
            "NOVEL_QUALITY_THRESHOLD": "85",
            "NOVEL_AUTO_SAVE": "true",
            "OTHER_VAR": "ignored",
        }

        # When
        config = EnvironmentConfiguration.load_from_environment(env_vars)

        # Then
        assert config == {
            "author": {"pen": {"name": "Test Author"}},
            "quality": {"threshold": 85},
            "auto": {"save": True},
        }

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-ENVIRONMENT_VALUE_TY")
    def test_environment_value_type_conversion(self) -> None:
        """環境変数値の型変換"""
        # Given
        env_vars = {
            "NOVEL_BOOL_TRUE": "true",
            "NOVEL_BOOL_FALSE": "false",
            "NOVEL_INT_VALUE": "123",
            "NOVEL_FLOAT_VALUE": "123.45",
            "NOVEL_STRING_VALUE": "hello world",
        }

        # When
        config = EnvironmentConfiguration.load_from_environment(env_vars)

        # Then
        assert config["bool"]["true"] is True
        assert config["bool"]["false"] is False
        assert config["int"]["value"] == 123
        assert config["float"]["value"] == 123.45
        assert config["string"]["value"] == "hello world"

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-NESTED_ENVIRONMENT_V")
    def test_nested_environment_variables(self) -> None:
        """ネストした環境変数の処理"""
        # Given
        env_vars = {
            "NOVEL_QUALITY_CHECKS_ENABLED": "true",
            "NOVEL_QUALITY_CHECKS_THRESHOLD": "90",
            "NOVEL_QUALITY_CHECKS_AUTO_FIX": "false",
        }

        # When
        config = EnvironmentConfiguration.load_from_environment(env_vars)

        # Then
        assert config == {"quality": {"checks": {"enabled": True, "threshold": 90, "auto": {"fix": False}}}}

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-BOOLEAN_VALUE_VARIAT")
    def test_boolean_value_variations(self) -> None:
        """ブール値の様々な表現"""
        # Given
        env_vars = {
            "NOVEL_TEST_TRUE1": "True",
            "NOVEL_TEST_TRUE2": "TRUE",
            "NOVEL_TEST_FALSE1": "False",
            "NOVEL_TEST_FALSE2": "FALSE",
        }

        # When
        config = EnvironmentConfiguration.load_from_environment(env_vars)

        # Then
        assert config["test"]["true1"] is True
        assert config["test"]["true2"] is True
        assert config["test"]["false1"] is False
        assert config["test"]["false2"] is False

    @pytest.mark.spec("SPEC-CONFIGURATION_VALUE-SPECIAL_CHARACTERS_I")
    def test_special_characters_in_values(self) -> None:
        """値に特殊文字が含まれる場合"""
        # Given
        env_vars = {
            "NOVEL_SPECIAL_PATH": "/path/to/file.txt",
            "NOVEL_SPECIAL_URL": "https://example.com",
            "NOVEL_SPECIAL_VERSION": "1.2.3",
        }

        # When
        config = EnvironmentConfiguration.load_from_environment(env_vars)

        # Then
        assert config["special"]["path"] == "/path/to/file.txt"
        assert config["special"]["url"] == "https://example.com"
        assert config["special"]["version"] == "1.2.3"
