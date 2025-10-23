"""Domain.value_objects.configuration_value
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""設定値管理のValue Objects
階層的設定システムのドメインロジックを提供
"""


from copy import deepcopy

# os import removed - environment access through configuration
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

# 設定値の型
ConfigValue = str | int | float | bool | list[Any] | dict[str, Any] | None


class ConfigurationLevel(Enum):
    """設定の階層レベル"""

    ENVIRONMENT = "env"
    PROJECT = "project"
    GLOBAL = "global"
    DEFAULT = "default"


@dataclass(frozen=True)
class ConfigurationSource:
    """設定ソースの値オブジェクト"""

    level: ConfigurationLevel
    path: str | None = None

    def __post_init__(self) -> None:
        if self.level in [ConfigurationLevel.PROJECT, ConfigurationLevel.GLOBAL] and self.path is None:
            msg = f"{self.level.value} level requires a path"
            raise ValueError(msg)


@dataclass(frozen=True)
class ConfigurationValue:
    """設定値のValue Object"""

    key: str
    value: object
    source: ConfigurationSource

    def __post_init__(self) -> None:
        if not self.key:
            msg = "Configuration key cannot be empty"
            raise ValueError(msg)


@dataclass(frozen=True)
class ConfigurationHierarchy:
    """設定階層のValue Object"""

    sources: dict[ConfigurationLevel, dict[str, Any]] = field(default_factory=dict)
    project_root: Path | None = None
    global_config_path: Path | None = None

    def __post_init__(self) -> None:
        # デフォルト設定パスを設定
        if self.global_config_path is None:
            object.__setattr__(self, "global_config_path", Path.home() / ".novel" / "config.yaml")

    def get_merged_config(self) -> dict[str, Any]:
        """優先順位に従って設定をマージ"""
        merged = {}

        # 優先順位: DEFAULT -> GLOBAL -> PROJECT -> ENVIRONMENT
        for level in [
            ConfigurationLevel.DEFAULT,
            ConfigurationLevel.GLOBAL,
            ConfigurationLevel.PROJECT,
            ConfigurationLevel.ENVIRONMENT,
        ]:
            if level in self.sources:
                merged = self._merge_configs(merged, self.sources[level])

        return merged

    def get_value(self, key: str, default: ConfigValue = None) -> ConfigValue:
        """ドット記法で設定値を取得"""
        merged = self.get_merged_config()
        return self._get_nested_value(merged, key, default)

    def get_value_with_source(self, key: str) -> ConfigurationValue | None:
        """設定値をソース情報付きで取得"""
        # 優先順位の逆順で検索(最初に見つかったものが最も優先度が高い)
        for level in [
            ConfigurationLevel.ENVIRONMENT,
            ConfigurationLevel.PROJECT,
            ConfigurationLevel.GLOBAL,
            ConfigurationLevel.DEFAULT,
        ]:
            if level in self.sources:
                value = self._get_nested_value(self.sources[level], key, None)
                if value is not None:
                    # PathがNoneの場合はダミーパスを使用する(必須のため)
                    if level == ConfigurationLevel.PROJECT:
                        source_path = (
                            str(self.project_root / "プロジェクト設定.yaml") if self.project_root else "project.yaml"
                        )

                    elif level == ConfigurationLevel.GLOBAL:
                        source_path = (
                            str(self.global_config_path) if self.global_config_path else "~/.novel/config.yaml"
                        )

                    else:
                        source_path = None

                    source = ConfigurationSource(level=level, path=source_path)
                    return ConfigurationValue(key=key, value=value, source=source)

        return None

    def _merge_configs(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """設定を再帰的にマージ"""
        result = deepcopy(base)

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = deepcopy(value)

        return result

    def _get_nested_value(self, config: dict[str, Any], key: str, default: ConfigValue = None) -> ConfigValue:
        """ネストされた設定値を取得"""
        keys = key.split(".")
        current = config

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default

        return current

    def _set_nested_value(self, config: dict[str, Any], key: str, value: ConfigValue) -> None:
        """ネストされた設定値を設定"""
        keys = key.split(".")
        current = config

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        # 型変換の試行
        if isinstance(value, str):
            if value.lower() in ["true", "false"]:
                value = value.lower() == "true"
            elif value.isdigit():
                value = int(value)
            elif value.replace(".", "").replace("-", "").isdigit() and value.count(".") == 1:
                # 小数点が1つだけの場合のみfloatに変換
                value = float(value)

        current[keys[-1]] = value

    def set_value(self, key: str, value: ConfigValue, level: ConfigurationLevel = ConfigurationLevel.PROJECT) -> None:
        """設定値を指定レベルに設定"""
        if level not in [ConfigurationLevel.GLOBAL, ConfigurationLevel.PROJECT]:
            msg = "Can only set values for GLOBAL or PROJECT levels"
            raise ValueError(msg)

        if level not in self.sources:
            self.sources[level] = {}

        self._set_nested_value(self.sources[level], key, value)

    def get_config_sources(self) -> dict[str, list[ConfigurationLevel]]:
        """各設定項目のソースを取得"""
        sources = {}

        for level in [
            ConfigurationLevel.ENVIRONMENT,
            ConfigurationLevel.PROJECT,
            ConfigurationLevel.GLOBAL,
            ConfigurationLevel.DEFAULT,
        ]:
            if level in self.sources:
                self._collect_sources(self.sources[level], level, "", sources)

        return sources

    def _collect_sources(
        self,
        config: dict[str, Any],
        level: ConfigurationLevel,
        prefix: str = "",
        sources: dict[str, ConfigurationSource] | None = None,
    ) -> None:
        """設定ソースを収集"""
        if sources is None:
            sources = {}
        for key, value in config.items():
            full_key = f"{prefix}.{key}" if prefix else key

            if full_key not in sources:
                sources[full_key] = []
            sources[full_key].append(level)

            if isinstance(value, dict):
                self._collect_sources(value, level, full_key, sources)


@dataclass(frozen=True)
class DefaultConfiguration:
    """デフォルト設定のValue Object"""

    @staticmethod
    def get_default_config() -> dict[str, Any]:
        """システムデフォルト設定を取得"""
        return {
            "default_author": {
                "pen_name": "Unknown Author",
            },
            "default_project": {
                "genre": "ファンタジー",
                "target_platform": "小説家になろう",
                "min_length_per_episode": 4000,
            },
            "writing_environment": {
                "preferred_editor": "code",
                "auto_save": {
                    "enabled": True,
                    "interval_minutes": 10,
                },
                "backup": {
                    "enabled": True,
                    "keep_versions": 5,
                },
            },
            "quality_management": {
                "default_threshold": 80,
                "auto_check": {
                    "on_complete": True,
                },
            },
        }


@dataclass(frozen=True)
class EnvironmentConfiguration:
    """環境変数設定のValue Object"""

    @staticmethod
    def load_from_environment(environment_vars: dict[str, str] | None = None) -> dict[str, Any]:
        """環境変数から設定を読み込み"""
        env_config: dict[str, Any] = {}

        # environment_varsが渡されない場合は空の辞書を返す(インフラ層で環境変数を渡す)
        if environment_vars is None:
            return env_config

        # NOVEL_で始まる環境変数を設定として読み込み
        for key, value in environment_vars.items():
            if key.startswith("NOVEL_"):
                # NOVEL_AUTHOR_PEN_NAME -> author.pen_name
                config_key = key[6:].lower().replace("_", ".")
                EnvironmentConfiguration._set_nested_value(env_config, config_key, value)

        return env_config

    @staticmethod
    def _set_nested_value(config: dict[str, Any], key: str, value: ConfigValue) -> None:
        """ネストされた設定値を設定"""
        keys = key.split(".")
        current = config

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        # 型変換の試行
        if isinstance(value, str):
            if value.lower() in ["true", "false"]:
                value = value.lower() == "true"
            elif value.isdigit():
                value = int(value)
            elif value.replace(".", "").replace("-", "").isdigit() and value.count(".") == 1:
                # 小数点が1つだけの場合のみfloatに変換
                value = float(value)

        current[keys[-1]] = value
