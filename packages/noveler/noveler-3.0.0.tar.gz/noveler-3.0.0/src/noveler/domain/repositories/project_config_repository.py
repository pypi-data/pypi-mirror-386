#!/usr/bin/env python3
"""プロジェクト設定リポジトリインターフェース

プロジェクト設定データの永続化インターフェース
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class ProjectConfigRepository(ABC):
    """プロジェクト設定リポジトリの抽象基底クラス"""

    @abstractmethod
    def load_config(self, project_path: Path) -> dict[str, Any]:
        """プロジェクト設定を読み込み

        Args:
            project_path: プロジェクトパス

        Returns:
            プロジェクト設定辞書
        """

    @abstractmethod
    def exists(self, project_path: Path) -> bool:
        """プロジェクト設定ファイルが存在するか

        Args:
            project_path: プロジェクトパス

        Returns:
            存在するかどうか
        """

    @abstractmethod
    def get_genre_info(self, project_path: Path) -> dict[str, Any]:
        """ジャンル情報を取得

        Args:
            project_path: プロジェクトパス

        Returns:
            ジャンル情報辞書
        """
