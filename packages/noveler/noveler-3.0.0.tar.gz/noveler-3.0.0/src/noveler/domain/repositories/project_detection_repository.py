"""プロジェクト検出用リポジトリインターフェース."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from noveler.domain.value_objects.project_info import ProjectInfo


class ProjectDetectionRepository(ABC):
    """プロジェクト検出の永続化を担当するリポジトリインターフェース."""

    @abstractmethod
    def detect_project_root(self, start_path: Path) -> Path | None:
        """指定されたパスからプロジェクトルートを検出.

        Args:
            start_path: 検索開始パス

        Returns:
            プロジェクトルートパス、見つからない場合はNone
        """

    @abstractmethod
    def get_project_info(self, project_path: Path) -> ProjectInfo | None:
        """プロジェクト情報を取得.

        Args:
            project_path: プロジェクトパス

        Returns:
            プロジェクト情報、存在しない場合はNone
        """

    @abstractmethod
    def is_valid_project(self, project_path: Path) -> bool:
        """有効なプロジェクトかどうか判定.

        Args:
            project_path: プロジェクトパス

        Returns:
            有効なプロジェクトの場合True
        """

    @abstractmethod
    def list_projects(self, base_directory: Path) -> list[Path]:
        """指定ディレクトリ内のプロジェクト一覧を取得.

        Args:
            base_directory: 検索対象ディレクトリ

        Returns:
            プロジェクトパスのリスト
        """

    @abstractmethod
    def get_project_type(self, project_path: Path) -> str | None:
        """プロジェクトタイプを取得.

        Args:
            project_path: プロジェクトパス

        Returns:
            プロジェクトタイプ、判定できない場合はNone
        """

    @abstractmethod
    def get_project_metadata(self, project_path: Path) -> dict[str, Any]:
        """プロジェクトメタデータを取得.

        Args:
            project_path: プロジェクトパス

        Returns:
            メタデータ辞書
        """

    @abstractmethod
    def save_detection_cache(self, project_path: Path, metadata: dict[str, Any]) -> None:
        """検出結果をキャッシュに保存.

        Args:
            project_path: プロジェクトパス
            metadata: メタデータ
        """

    @abstractmethod
    def get_detection_cache(self, project_path: Path) -> dict[str, Any] | None:
        """検出キャッシュを取得.

        Args:
            project_path: プロジェクトパス

        Returns:
            キャッシュされたメタデータ、存在しない場合はNone
        """

    @abstractmethod
    def clear_detection_cache(self, project_path: Path | None = None) -> int:
        """検出キャッシュをクリア.

        Args:
            project_path: 特定プロジェクトのキャッシュのみクリア(省略時は全て)

        Returns:
            クリアされたキャッシュエントリ数
        """

    @abstractmethod
    def get_recent_projects(self, limit: int) -> list[Path]:
        """最近アクセスしたプロジェクト一覧を取得.

        Args:
            limit: 取得する最大数

        Returns:
            最近のプロジェクトパスのリスト
        """
