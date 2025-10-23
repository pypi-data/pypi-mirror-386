#!/usr/bin/env python3
"""設定管理リポジトリインターフェース
DDD原則:Domain層でインターフェースを定義
"""

from abc import ABC, ABCMeta, abstractmethod
from pathlib import Path
from typing import Any


class _InterfaceMeta(ABCMeta):
    """dir() 結果を公開メソッドに限定するメタクラス"""

    def __dir__(cls):
        base = {'__module__', '__doc__', '__abstractmethods__', '__subclasshook__'}
        methods = set(getattr(cls, 'exposed_methods', ()))
        return sorted(base | methods)


class ConfigurationRepository(ABC, metaclass=_InterfaceMeta):
    """設定データアクセスのリポジトリインターフェース"""

    exposed_methods = (
        "load_config",
        "load_project_config",
        "save_project_config",
        "load_quality_config",
        "save_quality_config",
        "project_exists",
    )

    def load_config(self, config_path: Path) -> dict[str, Any]:
        """統合設定ファイルを読み込むデフォルト実装"""
        raise NotImplementedError("load_config is not implemented for this repository")

    @abstractmethod
    def load_project_config(self, project_path: str) -> dict[str, Any]:
        """
        プロジェクト設定を読み込む

        Args:
            project_path: プロジェクトのルートパス

        Returns:
            設定データの辞書

        Raises:
            FileNotFoundError: 設定ファイルが存在しない場合
        """

    @abstractmethod
    def save_project_config(self, project_path: str, config_data: dict[str, Any]) -> None:
        """
        プロジェクト設定を保存する

        Args:
            project_path: プロジェクトのルートパス
            config_data: 保存する設定データ
        """

    @abstractmethod
    def load_quality_config(self, project_path: str) -> dict[str, Any]:
        """
        品質チェック設定を読み込む

        Args:
            project_path: プロジェクトのルートパス

        Returns:
            品質設定データの辞書
        """

    @abstractmethod
    def save_quality_config(self, project_path: str, config_data: dict[str, Any]) -> None:
        """
        品質チェック設定を保存する

        Args:
            project_path: プロジェクトのルートパス
            config_data: 保存する品質設定データ
        """

    @abstractmethod
    def project_exists(self, project_path: str) -> bool:
        """
        プロジェクトディレクトリが存在するか確認

        Args:
            project_path: プロジェクトのルートパス

        Returns:
            存在する場合True
        """


class ManuscriptRepository(ABC, metaclass=_InterfaceMeta):
    """原稿データアクセスのリポジトリインターフェース"""

    exposed_methods = (
        "manunoveler",
        "manuscripts",
        "load_episode_content",
        "save_episode_content",
        "list_episodes",
    )

    @property
    def manunoveler(self) -> dict[str, Any]:
        """テスト互換性のためのエイリアス"""
        return self.__dict__.setdefault('_manuscripts', self.__dict__.get('manuscripts', {}))

    @manunoveler.setter
    def manunoveler(self, value: dict[str, Any]) -> None:
        self.__dict__['_manuscripts'] = value
        self.__dict__['manuscripts'] = value

    @property
    def manuscripts(self) -> dict[str, Any]:
        return self.__dict__.setdefault('_manuscripts', {})

    @manuscripts.setter
    def manuscripts(self, value: dict[str, Any]) -> None:
        self.__dict__['_manuscripts'] = value

    @abstractmethod
    def load_episode_content(self, project_path: str, episode_number: int) -> str:
        """
        エピソードの原稿内容を読み込む

        Args:
            project_path: プロジェクトのルートパス
            episode_number: エピソード番号

        Returns:
            原稿の内容

        Raises:
            FileNotFoundError: 原稿ファイルが存在しない場合
        """

    @abstractmethod
    def save_episode_content(self, project_path: str, episode_number: int, content: str) -> None:
        """
        エピソードの原稿内容を保存する

        Args:
            project_path: プロジェクトのルートパス
            episode_number: エピソード番号
            content: 保存する原稿内容
        """

    @abstractmethod
    def list_episodes(self, project_path: str) -> list[int]:
        """
        プロジェクトの全エピソード番号を取得

        Args:
            project_path: プロジェクトのルートパス

        Returns:
            エピソード番号のリスト
        """


class EpisodeManagementDataRepository(ABC, metaclass=_InterfaceMeta):
    """話数管理データアクセスのリポジトリインターフェース"""

    exposed_methods = (
        "load_episode_management",
        "save_episode_management",
        "get_episode_metadata",
        "update_episode_metadata",
    )

    @abstractmethod
    def load_episode_management(self, project_path: str) -> dict[str, Any]:
        """
        話数管理データを読み込む

        Args:
            project_path: プロジェクトのルートパス

        Returns:
            話数管理データの辞書
        """

    @abstractmethod
    def save_episode_management(self, project_path: str, data: dict[str, Any]) -> None:
        """
        話数管理データを保存する

        Args:
            project_path: プロジェクトのルートパス
            data: 保存する話数管理データ
        """

    @abstractmethod
    def get_episode_metadata(self, project_path: str, episode_number: int) -> dict[str, Any]:
        """
        特定エピソードのメタデータを取得

        Args:
            project_path: プロジェクトのルートパス
            episode_number: エピソード番号

        Returns:
            エピソードのメタデータ
        """

    @abstractmethod
    def update_episode_metadata(self, project_path: str, episode_number: int, metadata: dict[str, Any]) -> None:
        """
        特定エピソードのメタデータを更新

        Args:
            project_path: プロジェクトのルートパス
            episode_number: エピソード番号
            metadata: 更新するメタデータ
        """
