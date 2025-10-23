"""Infrastructure.repositories.base_yaml_repository
Where: Infrastructure repository base class for YAML storage.
What: Provides shared YAML loading, saving, and validation utilities for repositories.
Why: Reduces duplication across YAML-backed repositories.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""YAML設定ファイル読み込み基底クラス

YamlConfigurationRepositoryとYamlProjectConfigRepositoryの共通処理を抽出。
DRY原則に基づき、YAML読み込みとエラーハンドリングの重複を排除。
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from pathlib import Path


class BaseYamlRepository(ABC):
    """YAML設定ファイル読み込み基底クラス

    共通のYAML読み込み処理とエラーハンドリングを提供。
    各実装クラスは具体的な設定ファイルパスの解決を実装する。
    """

    def _load_yaml_file(self, config_path: Path) -> dict[str, Any]:
        """YAML設定ファイルを読み込む（共通処理）

        Args:
            config_path: 設定ファイルパス

        Returns:
            設定データ辞書

        Raises:
            FileNotFoundError: ファイルが見つからない場合
            yaml.YAMLError: YAML解析エラーの場合
            OSError: その他のファイル読み込みエラー
        """
        if not config_path.exists():
            msg = f"設定ファイルが見つかりません: {config_path}"
            raise FileNotFoundError(msg)

        try:
            with config_path.open(encoding="utf-8") as f:
                config_data: dict[str, Any] = yaml.safe_load(f)

            # Noneの場合は空辞書を返す
            if config_data is None:
                config_data = {}

            return config_data

        except yaml.YAMLError as e:
            msg = f"YAML解析エラー: {config_path}: {e}"
            raise yaml.YAMLError(msg) from e
        except Exception as e:
            msg = f"設定ファイル読み込みエラー: {config_path}: {e}"
            raise OSError(msg) from e

    def _validate_config_data(self, config_data: dict[str, Any], required_keys: list[str] | None = None) -> bool:
        """設定データの基本検証

        Args:
            config_data: 設定データ辞書
            required_keys: 必須キー（オプション）

        Returns:
            検証結果（True: 有効、False: 無効）
        """
        if not isinstance(config_data, dict):
            return False

        if required_keys:
            missing_keys = [key for key in required_keys if key not in config_data]
            if missing_keys:
                return False

        return True

    @abstractmethod
    def load_config(self, *args, **kwargs) -> dict[str, Any]:
        """設定ファイルを読み込む（抽象メソッド）

        各実装クラスで具体的な読み込み処理を実装する。
        """
