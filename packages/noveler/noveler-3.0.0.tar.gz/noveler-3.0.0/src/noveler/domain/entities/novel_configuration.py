#!/usr/bin/env python3
"""小説執筆支援システム統合設定エンティティ

システム全体の設定を管理するメインエンティティ
"""

import platform
from typing import Any

from noveler.domain.value_objects.configuration_section import ConfigurationSection


class NovelConfiguration:
    """小説執筆支援システム統合設定エンティティ

    config/novel_config.yamlから読み込まれた全設定を管理し、
    型安全なアクセス方法を提供する。
    """

    def __init__(self, sections: dict[str, ConfigurationSection]) -> None:
        """設定エンティティを初期化

        Args:
            sections: 設定セクション辞書
        """
        self._sections = sections

    @classmethod
    def from_dict(cls, config_data: dict[str, Any]) -> "NovelConfiguration":
        """辞書から設定エンティティを作成

        Args:
            config_data: 設定データ辞書

        Returns:
            NovelConfiguration インスタンス
        """
        sections = {}
        for section_name, section_data in config_data.items():
            sections[section_name] = ConfigurationSection(section_name, section_data)

        return cls(sections)

    def get_system_setting(self, key: str, default: Any = None) -> Any:
        """システム設定を取得

        Args:
            key: 設定キー
            default: デフォルト値

        Returns:
            設定値またはデフォルト値
        """
        system_section = self._sections.get("system")
        if system_section:
            return system_section.get_string(key, default)
        return default

    def get_default_setting(self, category: str, key: str, default: Any = None) -> Any:
        """デフォルト設定を取得

        Args:
            category: 設定カテゴリ（author, episode等）
            key: 設定キー
            default: デフォルト値

        Returns:
            設定値またはデフォルト値
        """
        defaults_section = self._sections.get("defaults")
        if defaults_section:
            # ネストされた値を直接取得（型変換なし）
            value = defaults_section._get_nested_value([category, key], default)
            return value if value is not None else default
        return default

    def get_path_setting(self, category: str, key: str, default: str | None = None) -> str:
        """パス設定を取得

        Args:
            category: パスカテゴリ（directories, project_paths等）
            key: パスキー
            default: デフォルト値

        Returns:
            パス文字列またはデフォルト値
        """
        paths_section = self._sections.get("paths")
        if paths_section:
            return paths_section.get_nested_string([category, key], default)
        return default

    def get_external_service_setting(self, service: str, key: str, default: Any = None) -> Any:
        """外部サービス設定を取得

        Args:
            service: サービス名（claude_code, git等）
            key: 設定キー
            default: デフォルト値

        Returns:
            設定値またはデフォルト値
        """
        external_section = self._sections.get("external_services")
        if external_section:
            return external_section._get_nested_value([service, key], default)
        return default

    def get_or_default(self, key: str, default: Any = None) -> Any:
        """Claude Code統合互換性メソッド

        ドット記法キー（例: claude_code.max_turns）を解析し、適切な設定を取得

        Args:
            key: ドット記法の設定キー
            default: デフォルト値

        Returns:
            設定値またはデフォルト値
        """
        parts = key.split(".")

        # claude_code.* の場合、external_servicesから取得
        if parts[0] == "claude_code":
            if len(parts) == 2:
                return self.get_external_service_setting("claude_code", parts[1], default)
            if len(parts) == 3 and parts[1] == "error_handling":
                # claude_code.error_handling.* の場合
                external_section = self._sections.get("external_services")
                if external_section:
                    return external_section._get_nested_value(["claude_code", "error_handling", parts[2]], default)

        # システム設定として検索
        system_section = self._sections.get("system")
        if system_section:
            if len(parts) == 1:
                return system_section.get_string(parts[0], default)
            return system_section._get_nested_value(parts, default)

        return default

    def get_platform_path(self, key: str, default: str | None = None) -> str:
        """プラットフォーム固有パスを取得

        現在のプラットフォームに応じて適切なパスを自動選択する。

        Args:
            key: パスキー
            default: デフォルト値

        Returns:
            プラットフォーム固有パスまたはデフォルト値
        """
        platform_paths_section = self._sections.get("platform_paths")
        if not platform_paths_section:
            return default

        current_platform = self._get_current_platform()
        return platform_paths_section.get_nested_string([current_platform, key], default)

    def is_feature_enabled(self, category: str, feature: str) -> bool:
        """機能フラグの有効性を確認

        Args:
            category: 機能カテゴリ（experimental, legacy等）
            feature: 機能名

        Returns:
            機能が有効かどうか
        """
        features_section = self._sections.get("features")
        if features_section:
            return features_section.get_nested_bool([category, feature], False)
        return False

    def _get_current_platform(self) -> str:
        """現在のプラットフォーム名を取得

        Returns:
            プラットフォーム名（linux, windows, darwin）
        """
        system = platform.system().lower()
        if system == "linux":
            return "linux"
        if system == "windows":
            return "windows"
        if system == "darwin":
            return "darwin"
        return "linux"  # デフォルト
