#!/usr/bin/env python3
"""プロジェクト情報リポジトリインターフェース
プロジェクトファイルからの情報取得を抽象化
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class ProjectInfoRepository(ABC):
    """プロジェクト情報リポジトリインターフェース

    プロジェクトファイルの読み込みと管理を抽象化し、
    ドメイン層が技術的実装に依存しないようにする
    """

    @abstractmethod
    def load_project_files(self, project_root: str) -> dict[str, Any]:
        """プロジェクトファイルを読み込み

        Args:
            project_root: プロジェクトルートパス(省略時は現在位置から検索)

        Returns:
            Dict[str, Any]: 読み込まれたプロジェクトファイルデータ
            {
                "project_settings": {...},
                "character_settings": {...},
                "plot_settings": {...},
                "episode_management": {...}
            }

        Raises:
            FileNotFoundError: プロジェクトルートが見つからない場合
            PermissionError: ファイル読み込み権限がない場合
            ValueError: ファイル形式が不正な場合
        """

    @abstractmethod
    def get_project_root(self, start_path: str) -> str:
        """プロジェクトルートパスを取得

        Args:
            start_path: 検索開始パス(省略時は現在ディレクトリ)

        Returns:
            str: プロジェクトルートパス

        Raises:
            FileNotFoundError: プロジェクトルートが見つからない場合
        """

    @abstractmethod
    def file_exists(self, file_path: Path) -> bool:
        """ファイルの存在確認

        Args:
            file_path: 確認するファイルパス

        Returns:
            bool: ファイルが存在する場合True
        """

    @abstractmethod
    def get_file_path(self, project_root: str, file_type: str) -> str:
        """ファイルタイプから実際のファイルパスを取得

        Args:
            project_root: プロジェクトルートパス
            file_type: ファイルタイプ(project_settings, character_settings等)

        Returns:
            str: 実際のファイルパス
        """
