#!/usr/bin/env python3
"""プロジェクトファイルリポジトリインターフェース

プロジェクトファイルの操作を抽象化する
リポジトリインターフェース(ドメイン層で定義)
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class ProjectFileRepository(ABC):
    """プロジェクトファイルリポジトリインターフェース"""

    @abstractmethod
    def exists(self, file_path: Path) -> bool:
        """ファイルが存在するかチェック

        Args:
            file_path: ファイルパス

        Returns:
            bool: 存在する場合True
        """

    @abstractmethod
    def save_file(self, file_path: str, content: str) -> None:
        """ファイルを保存

        Args:
            file_path: 保存先ファイルパス
            content: 保存内容

        Raises:
            IOError: 保存に失敗した場合
        """

    @abstractmethod
    def load_project_config(self) -> dict[str, Any]:
        """プロジェクト設定を読み込み

        Returns:
            Dict[str, Any]: プロジェクト設定
        """

    @abstractmethod
    def create_directory(self, dir_path: Path) -> None:
        """ディレクトリを作成

        Args:
            dir_path: 作成するディレクトリパス
        """
