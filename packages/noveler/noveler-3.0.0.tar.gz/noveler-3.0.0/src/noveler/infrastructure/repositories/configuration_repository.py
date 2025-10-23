#!/usr/bin/env python3
"""設定リポジトリ
プロジェクト設定の永続化とアクセスを管理
"""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import yaml

from noveler.infrastructure.adapters.hierarchical_config_adapter import HierarchicalConfig


class IConfigurationRepository(ABC):
    """設定リポジトリのインターフェース"""

    @abstractmethod
    def find_project_config(self, start_path: str | Path | None = None) -> Path | None:
        """プロジェクト設定ファイルを検索"""

    @abstractmethod
    def load_project_config(self, config_path: str | Path) -> dict[str, Any]:
        """プロジェクト設定を読み込み"""

    @abstractmethod
    def get_project_paths(self) -> dict[str, str]:
        """プロジェクトのパス情報を取得"""

    @abstractmethod
    def get_project_info(self) -> dict[str, Any]:
        """プロジェクト情報を取得"""

    @abstractmethod
    def get_config(self, key: str | None = None, default: object = None) -> object:
        """設定値を取得"""


class ConfigurationRepository(IConfigurationRepository):
    """設定リポジトリの実装"""

    def __init__(self) -> None:
        # 階層的設定をインポート
        try:
            self._hierarchical_config = HierarchicalConfig()
            self._has_hierarchical = True
        except Exception:
            self._hierarchical_config = None
            self._has_hierarchical = False

    def find_project_config(self, start_path: str | Path | None = None) -> Path | None:
        """プロジェクト設定.yamlを検索"""
        if start_path is None:
            start_path = Path.cwd()

        current = start_path.resolve()

        # 現在のディレクトリから上に向かって検索
        while current != current.parent:
            config_path = current / "プロジェクト設定.yaml"
            if config_path.exists():
                return config_path
            current = current.parent

        return None

    def load_project_config(self, config_path: str | Path | None = None) -> dict[str, Any]:
        """プロジェクト設定を読み込み"""
        if config_path is None:
            config_path = self.find_project_config()

        if config_path is None or not config_path.exists():
            return {}

        try:
            with Path(config_path).open(encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def get_project_paths(self) -> dict[str, str]:
        """プロジェクトのパス情報を取得"""
        paths = {}

        # 環境変数が設定されている場合は優先
        if "PROJECT_ROOT" in os.environ:
            paths["project_root"] = os.environ["PROJECT_ROOT"]
            paths["guide_root"] = os.environ.get(
                "GUIDE_ROOT",
                os.path.join(os.path.dirname(paths["project_root"]), "00_ガイド"),
            )

            return paths

        # プロジェクト設定.yamlから読み込み
        config = self.load_project_config()
        if "paths" in config and "project_root" in config["paths"]:
            paths["project_root"] = config["paths"]["project_root"]
            # guide_rootが明示的に設定されていない場合は自動計算
            if "guide_root" in config["paths"]:
                paths["guide_root"] = config["paths"]["guide_root"]
            else:
                paths["guide_root"] = os.path.join(os.path.dirname(paths["project_root"]), "00_ガイド")
            return paths

        # どちらも設定されていない場合は、現在のディレクトリから推測
        config_path = self.find_project_config()
        if config_path:
            project_root = str(config_path.parent)
            paths["project_root"] = project_root
            paths["guide_root"] = os.path.join(os.path.dirname(project_root), "00_ガイド")
            return paths

        # 何も見つからない場合は空の辞書を返す
        return paths

    def setup_environment(self) -> bool:
        """環境変数を設定(スクリプト実行時の自動設定用・DDD準拠)"""
        paths = self.get_project_paths()
        if paths:
            # DDD準拠修正: 既に設定された環境変数は尊重し、副作用のある上書きを廃止
            existing_project_root = os.environ.get("PROJECT_ROOT")
            if not existing_project_root:
                os.environ["PROJECT_ROOT"] = paths.get("project_root", "")
            os.environ["GUIDE_ROOT"] = paths.get("guide_root", "")
            return True
        return False

    def get_project_info(self) -> dict[str, Any]:
        """プロジェクト情報を取得"""
        if self._has_hierarchical:
            return self._hierarchical_config.get("project", {})
        config = self.load_project_config()
        return config.get("project", {})

    def get_ncode(self) -> str | None:
        """ncodeを取得"""
        project_info = self.get_project_info()
        return project_info.get("ncode")

    def get_config(self, key: str | None = None, default: object = None) -> object:
        """階層的設定から値を取得"""
        if self._has_hierarchical:
            return self._hierarchical_config.get(key, default)
        # 従来の方法
        config = self.load_project_config()
        if key is None:
            return config

        # ドット記法でネストされた値を取得
        keys = key.split(".")
        current = config

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default

        return current

    def get_author_info(self) -> dict[str, str]:
        """著者情報を取得(グローバル設定を優先)"""
        if self._has_hierarchical:
            # プロジェクト固有の著者情報があればそれを使用
            author = self._hierarchical_config.get("author")
            if author and author.get("pen_name"):
                return author
            # なければデフォルト著者情報を使用
            return self._hierarchical_config.get("default_author", {})
        config = self.load_project_config()
        return config.get("author", {})

    def get_quality_threshold(self) -> int:
        """品質閾値を取得"""
        if self._has_hierarchical:
            return self._hierarchical_config.get("quality_management.default_threshold", 80)
        config = self.load_project_config()
        return config.get("settings", {}).get("quality_threshold", 80)
