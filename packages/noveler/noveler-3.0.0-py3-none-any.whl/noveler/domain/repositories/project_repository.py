#!/usr/bin/env python3
"""プロジェクトリポジトリインターフェース

DDD原則に基づくドメイン層のプロジェクト管理抽象化
"""

from abc import ABC, ABCMeta, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from noveler.domain.entities.a31_checklist_item import A31ChecklistItem

class ProjectRepositoryMeta(ABCMeta):
    """set_project_metadata の命名互換性を提供するメタクラス"""

    def __getattr__(cls, name: str):
        if name == "set_project_metadata":
            def alias(self, project_id: str, key: str, value: Any) -> bool:
                return self.update_project_metadata(project_id, key, value)
            return alias
        raise AttributeError(name)

    def __dir__(cls):
        base_dir = super().__dir__()
        return [attr for attr in base_dir if attr != "set_project_metadata"]


class ProjectRepository(ABC, metaclass=ProjectRepositoryMeta):
    """プロジェクトリポジトリインターフェース"""

    def __getattr__(self, name: str):
        if name == "set_project_metadata":
            return lambda project_id, key, value: self.update_project_metadata(project_id, key, value)
        raise AttributeError(name)

    @abstractmethod
    def exists(self, project_id: str) -> bool:
        """プロジェクトの存在確認

        Args:
            project_id: プロジェクトID

        Returns:
            bool: 存在する場合True
        """

    @abstractmethod
    def create(self, project_id: str, project_data: dict[str, Any]) -> bool:
        """プロジェクトを作成

        Args:
            project_id: プロジェクトID
            project_data: プロジェクトデータ

        Returns:
            bool: 作成成功時True
        """

    @abstractmethod
    def get_project_info(self, project_id: str) -> dict[str, Any] | None:
        """プロジェクト情報を取得

        Args:
            project_id: プロジェクトID

        Returns:
            Dict[str, Any]: プロジェクト情報、なければNone
        """

    @abstractmethod
    def update_project_info(self, project_id: str, project_data: dict[str, Any]) -> bool:
        """プロジェクト情報を更新

        Args:
            project_id: プロジェクトID
            project_data: 更新データ

        Returns:
            bool: 更新成功時True
        """

    @abstractmethod
    def delete(self, project_id: str) -> bool:
        """プロジェクトを削除

        Args:
            project_id: プロジェクトID

        Returns:
            bool: 削除成功時True
        """

    @abstractmethod
    def get_all_projects(self) -> list[dict[str, Any]]:
        """全プロジェクトを取得

        Returns:
            list[Dict[str, Any]]: プロジェクトリスト
        """

    @abstractmethod
    def get_project_settings(self, project_id: str) -> dict[str, Any] | None:
        """プロジェクト設定を取得

        Args:
            project_id: プロジェクトID

        Returns:
            Dict[str, Any]: プロジェクト設定、なければNone
        """

    @abstractmethod
    def update_project_settings(self, project_id: str, settings: dict[str, Any]) -> bool:
        """プロジェクト設定を更新

        Args:
            project_id: プロジェクトID
            settings: 設定データ

        Returns:
            bool: 更新成功時True
        """

    @abstractmethod
    def get_project_metadata(self, project_id: str) -> dict[str, Any] | None:
        """プロジェクトメタデータを取得

        Args:
            project_id: プロジェクトID

        Returns:
            Dict[str, Any]: メタデータ、なければNone
        """

    def update_project_metadata(self, project_id: str, key: str, value: Any) -> bool:
        """プロジェクトメタデータを更新"""
        raise NotImplementedError('update_project_metadata is not implemented')

    @abstractmethod
    def archive_project(self, project_id: str) -> bool:
        """プロジェクトをアーカイブ

        Args:
            project_id: プロジェクトID

        Returns:
            bool: アーカイブ成功時True
        """

    @abstractmethod
    def restore_project(self, project_id: str) -> bool:
        """プロジェクトをアーカイブから復元

        Args:
            project_id: プロジェクトID

        Returns:
            bool: 復元成功時True
        """

    @abstractmethod
    def get_project_statistics(self, project_id: str) -> dict[str, Any] | None:
        """プロジェクト統計情報を取得

        Args:
            project_id: プロジェクトID

        Returns:
            Dict[str, Any]: 統計情報、なければNone
        """

    @abstractmethod
    def backup_project(self, project_id: str) -> bool:
        """プロジェクトをバックアップ

        Args:
            project_id: プロジェクトID

        Returns:
            bool: バックアップ成功時True
        """

    @abstractmethod
    def get_project_directory(self, project_id: str) -> str | None:
        """プロジェクトディレクトリパスを取得

        Args:
            project_id: プロジェクトID

        Returns:
            str: ディレクトリパス、なければNone
        """

    @abstractmethod
    def validate_project_structure(self, project_id: str) -> dict[str, Any]:
        """プロジェクト構造の検証

        Args:
            project_id: プロジェクトID

        Returns:
            Dict[str, Any]: 検証結果
        """

    @abstractmethod
    def initialize_project_structure(self, project_id: str) -> bool:
        """プロジェクト構造を初期化

        Args:
            project_id: プロジェクトID

        Returns:
            bool: 初期化成功時True
        """

    @abstractmethod
    def get_project_root(self, project_id: str) -> Path | None:
        """プロジェクトのルートディレクトリを取得

        Args:
            project_id: プロジェクトID

        Returns:
            プロジェクトのルートディレクトリパス
        """

    def get_checklist_items(self, project_name: str, item_ids: list[str]) -> list["A31ChecklistItem"]:
        """チェックリスト項目を取得

        Args:
            project_name: プロジェクト名
            item_ids: 取得する項目IDのリスト

        Returns:
            list[A31ChecklistItem]: チェックリスト項目のリスト
        """

        # モック化テストとの互換性を保つため、抽象メソッドにはせずここで未実装扱いとする
        raise NotImplementedError("get_checklist_items is not implemented")

    def get_project_config(self, project_name: str) -> dict[str, Any]:
        """プロジェクト設定を取得

        Args:
            project_name: プロジェクト名

        Returns:
            Dict[str, Any]: プロジェクト設定データ
        """

        # モック化テストとの互換性を保つため、抽象メソッドにはせずここで未実装扱いとする
        raise NotImplementedError("get_project_config is not implemented")

    def get_episode_management(self, project_name: str) -> dict[str, Any]:
        """エピソード管理データを取得

        Args:
            project_name: プロジェクト名

        Returns:
            Dict[str, Any]: エピソード管理データ
        """

        # モック化テストとの互換性を保つため、抽象メソッドにはせずここで未実装扱いとする
        raise NotImplementedError("get_episode_management is not implemented")
