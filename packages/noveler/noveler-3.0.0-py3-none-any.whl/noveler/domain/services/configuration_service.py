"""Domain.services.configuration_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""設定管理ドメインサービス"""


from typing import Any, TypeVar

from noveler.domain.value_objects.configuration_key import ConfigurationKey
from noveler.domain.value_objects.file_path import FilePath

# 設定値の型を定義
ConfigValue = str | int | float | bool | list | dict
T = TypeVar("T")

# Phase 6修正: Service → Repository循環依存解消
from typing import Protocol


class IConfigurationRepository(Protocol):
    """設定リポジトリインターフェース（循環依存解消）"""

    def get_config_value(self, key: ConfigurationKey) -> Any: ...
    def set_config_value(self, key: ConfigurationKey, value: Any) -> bool: ...
    def load(self, file_path: str | FilePath) -> dict[str, Any]: ...
    def load_all_configs(self) -> dict[str, Any]: ...


class ConfigurationService:
    """設定管理を行うドメインサービス


    設定ファイルの読み込み、値の取得、検証などの
    設定に関するビジネスロジックを提供する。
    """

    def __init__(self, repository: IConfigurationRepository) -> None:
        """ConfigurationServiceを初期化する

        Args:
            repository: 設定の永続化を行うリポジトリ
        """
        self._repository = repository
        self._config: dict[str, ConfigValue] | None = None

    def load_configuration(self, file_path: str) -> dict[str, ConfigValue]:
        """設定ファイルを読み込む

        Args:
            file_path: 設定ファイルのパス

        Returns:
            読み込んだ設定の辞書

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            ValueError: ファイル形式が不正な場合
        """
        config = self._repository.load(file_path)
        self._config = config
        return config

    def get_value(self, key: ConfigurationKey, default: ConfigValue | None = None) -> ConfigValue | None:
        """指定したキーの設定値を取得する

        Args:
            key: 取得する設定のキー
            default: キーが存在しない場合のデフォルト値

        Returns:
            設定値またはデフォルト値
        """
        if self._config is None:
            return default

        # キーをパスセグメントに分解して階層的にアクセス
        current = self._config
        for segment in key.as_path_segments():
            if not isinstance(current, dict) or segment not in current:
                return default
            current = current[segment]

        return current

    def set_value(self, key: ConfigurationKey, value: ConfigValue) -> None:
        """指定したキーに設定値を設定する

        Args:
            key: 設定するキー
            value: 設定する値
        """
        if self._config is None:
            self._config = {}

        # 階層構造を作成
        current = self._config
        segments = key.as_path_segments()

        # 最後のセグメント以外を処理(階層を作成)
        for segment in segments[:-1]:
            if segment not in current:
                current[segment] = {}
            current = current[segment]

        # 最後のセグメントに値を設定
        current[segments[-1]] = value

    def has_key(self, key: ConfigurationKey) -> bool:
        """指定したキーが存在するかを確認する

        Args:
            key: 確認するキー

        Returns:
            キーが存在する場合True
        """
        if self._config is None:
            return False

        current = self._config
        for segment in key.as_path_segments():
            if not isinstance(current, dict) or segment not in current:
                return False
            current = current[segment]

        return True

    def validate_configuration(self, config: dict[str, Any] | None) -> bool:
        """設定の妥当性を検証する

        Args:
            config: 検証する設定

        Returns:
            有効な設定の場合True
        """
        if config is None:
            return False

        if not isinstance(config, dict):
            return False

        return len(config) != 0
