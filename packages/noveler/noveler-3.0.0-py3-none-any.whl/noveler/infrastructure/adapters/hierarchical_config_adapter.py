"""Provide backward-compatible helpers for hierarchical configuration management."""

from noveler.presentation.shared.shared_utilities import console
import argparse
import json
import os
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.value_objects.configuration_value import (
    ConfigurationHierarchy,
    ConfigurationLevel,
    DefaultConfiguration,
    EnvironmentConfiguration,
)


class HierarchicalConfigAdapter:
    """Manage layered configuration sources while retaining legacy interfaces."""

    def __init__(self, project_root: Path | str | None = None, logger_service=None, console_service=None) -> None:
        """Build the adapter and eagerly load configuration sources.

        Args:
            project_root: Optional base path that anchors project configuration.
            logger_service: Optional logger used for diagnostic messaging.
            console_service: Optional console used for user-facing output.
        """
        self.project_root = project_root or self._find_project_root()
        self.global_config_path = Path.home() / ".novel" / "config.yaml"
        self.config_hierarchy = ConfigurationHierarchy(
            project_root=self.project_root, global_config_path=self.global_config_path
        )
        self.logger_service = logger_service
        self.console_service = console_service or console
        self._load_all_configs()

    def _find_project_root(self) -> Path | None:
        """Search upward from the current directory to locate the project root.

        Returns:
            Path | None: Directory containing ``"プロジェクト設定.yaml"``.
        """
        current = Path.cwd()
        while current != current.parent:
            if (current / "プロジェクト設定.yaml").exists():
                return current
            current = current.parent
        return None

    def _load_all_configs(self) -> None:
        """Populate the configuration hierarchy for each supported level."""
        self.config_hierarchy.sources[ConfigurationLevel.DEFAULT] = DefaultConfiguration.get_default_config()
        if self.global_config_path.exists():
            with Path(self.global_config_path).open(encoding="utf-8") as f:
                self.config_hierarchy.sources[ConfigurationLevel.GLOBAL] = yaml.safe_load(f) or {}
        else:
            self.config_hierarchy.sources[ConfigurationLevel.GLOBAL] = {}
        if self.project_root:
            project_config_path = self.project_root / "プロジェクト設定.yaml"
            if project_config_path.exists():
                try:
                    with Path(project_config_path).open(encoding="utf-8") as f:
                        self.config_hierarchy.sources[ConfigurationLevel.PROJECT] = yaml.safe_load(f) or {}
                except yaml.YAMLError as e:
                    self.console_service.print(f"⚠️ プロジェクト設定ファイルの読み込みに失敗しました: {e}")
                    self.config_hierarchy.sources[ConfigurationLevel.PROJECT] = {}
            else:
                self.config_hierarchy.sources[ConfigurationLevel.PROJECT] = {}
        else:
            self.config_hierarchy.sources[ConfigurationLevel.PROJECT] = {}
        self.config_hierarchy.sources[ConfigurationLevel.ENVIRONMENT] = EnvironmentConfiguration.load_from_environment(
            os.environ
        )

    def get(self, key: str | None = None, default: object = None) -> object:
        """Return a configuration value using legacy semantics.

        Args:
            key: Dot-delimited configuration key; ``None`` returns all settings.
            default: Value supplied when the key is missing.

        Returns:
            object: Configuration value or fallback default.
        """
        if key is None:
            return self.config_hierarchy.get_merged_config()
        return self.config_hierarchy.get_value(key, default)

    def all(self) -> dict[str, Any]:
        """Return the merged configuration across all hierarchy levels."""
        return self.config_hierarchy.get_merged_config()

    def set(self, key: str, value: object, level: str = "project") -> None:
        """Persist a configuration value at the requested level.

        Args:
            key: Dot-delimited configuration key.
            value: Value to store.
            level: ``"global"`` or ``"project"`` selection.
        """
        if level not in ["global", "project"]:
            msg = "level must be 'global' or 'project'"
            raise ValueError(msg)
        config_level = ConfigurationLevel.GLOBAL if level == "global" else ConfigurationLevel.PROJECT
        self.config_hierarchy.set_value(key, value, config_level)

    def save(self, level: str) -> None:
        """Persist configuration changes for the requested hierarchy level.

        Args:
            level: ``"global"`` or ``"project"`` target to persist.
        """
        if level == "global":
            self.global_config_path.parent.mkdir(parents=True, exist_ok=True)
            with Path(self.global_config_path).open("w", encoding="utf-8") as f:
                yaml.dump(
                    self.config_hierarchy.sources.get(ConfigurationLevel.GLOBAL, {}),
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                )
            self.console_service.print("✅ グローバル設定を保存しました")
        elif level == "project":
            if not self.project_root:
                msg = "プロジェクトルートが見つかりません"
                raise ValueError(msg)
            project_config_path = self.project_root / "プロジェクト設定.yaml"
            with Path(project_config_path).open("w", encoding="utf-8") as f:
                yaml.dump(
                    self.config_hierarchy.sources.get(ConfigurationLevel.PROJECT, {}),
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                )
            self.console_service.print("✅ プロジェクト設定を保存しました")

    def show_config_sources(self) -> dict[str, list[str]]:
        """Return a mapping of configuration keys to contributing levels.

        Returns:
            dict[str, list[str]]: Hierarchy levels contributing each key.
        """
        sources = self.config_hierarchy.get_config_sources()
        str_sources = {}
        for key, levels in sources.items():
            str_sources[key] = [level.value for level in levels]
        return str_sources

    def init_global_config(self) -> None:
        """Create a global configuration file from a template when missing."""
        if self.global_config_path.exists():
            self.console_service.print("⚠️  グローバル設定は既に存在します")
            return
        template_path = (
            Path(__file__).parent.parent.parent
            / "B_技術ガイド"
            / "B40_システム運用"
            / "templates"
            / "グローバル設定テンプレート.yaml"
        )
        if template_path.exists():
            self.global_config_path.parent.mkdir(parents=True, exist_ok=True)
            template_content = Path(template_path).read_text(encoding="utf-8")

            with Path(self.global_config_path).open("w", encoding="utf-8") as f:
                f.write(template_content)
            self.console_service.print("✅ グローバル設定を作成しました")
            self.console_service.print("📝 設定を編集してください")
        else:
            self.console_service.print("❌ テンプレートが見つかりません")

    @property
    def configs(self) -> dict[str, dict[str, object]]:
        """Expose configuration sources for legacy callers."""
        return {
            "default": self.config_hierarchy.sources.get(ConfigurationLevel.DEFAULT, {}),
            "global": self.config_hierarchy.sources.get(ConfigurationLevel.GLOBAL, {}),
            "project": self.config_hierarchy.sources.get(ConfigurationLevel.PROJECT, {}),
            "env": self.config_hierarchy.sources.get(ConfigurationLevel.ENVIRONMENT, {}),
        }


HierarchicalConfig = HierarchicalConfigAdapter


def main() -> None:
    """Entry point for manual testing of the adapter."""
    parser = argparse.ArgumentParser(description="階層的設定管理")
    parser.add_argument("command", choices=["get", "set", "show", "init"])
    parser.add_argument("key", nargs="?", help="設定キー(ドット記法)")
    parser.add_argument("value", nargs="?", help="設定値")
    parser.add_argument("--level", choices=["global", "project"], default="project")
    parser.add_argument("--json", action="store_true", help="JSON形式で出力")
    args = parser.parse_args()
    config = HierarchicalConfigAdapter()
    if args.command == "init":
        config.init_global_config()
    elif args.command == "get":
        if args.key:
            value = config.get(args.key)
            if args.json:
                console.print(json.dumps(value, ensure_ascii=False, indent=2))
            else:
                console.print(f"{args.key}: {value}")
        else:
            all_config: dict[str, Any] = config.get()
            if args.json:
                console.print(json.dumps(all_config, ensure_ascii=False, indent=2))
            else:
                console.print(yaml.dump(all_config, default_flow_style=False, allow_unicode=True))
    elif args.command == "set":
        if not args.key or args.value is None:
            console.print("エラー: キーと値が必要です")
            return
        config.set(args.key, args.value, args.level)
        config.save(args.level)
    elif args.command == "show":
        sources = config.show_config_sources()
        console.print("設定ソース一覧:")
        for key, levels in sorted(sources.items()):
            console.print(f"  {key}: {levels}")


if __name__ == "__main__":
    main()
