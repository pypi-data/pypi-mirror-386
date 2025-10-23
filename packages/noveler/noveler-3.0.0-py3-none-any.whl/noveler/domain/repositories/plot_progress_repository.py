#!/usr/bin/env python3
"""プロット進捗リポジトリインターフェース(DDD)

ドメイン層で定義し、インフラ層で実装する
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class PlotProgressRepository(ABC):
    """プロット進捗リポジトリインターフェース"""

    @abstractmethod
    def read_file_content(self, file_path: Path) -> str:
        """ファイル内容を読み込む"""

    @abstractmethod
    def parse_yaml_content(self, content: str) -> dict[str, Any]:
        """YAML文字列を解析する"""

    @abstractmethod
    def file_exists(self, file_path: Path) -> bool:
        """ファイルの存在確認"""

    @abstractmethod
    def list_files(self, directory: Path, pattern: str) -> list[Path]:
        """ディレクトリ内のファイル一覧を取得"""

    def find_master_plot(self, project_id: str) -> dict[str, Any] | None:
        """マスタープロットを取得

        Args:
            project_id: プロジェクトID

        Returns:
            マスタープロット情報(存在しない場合はNone)
        """
        raise NotImplementedError('find_master_plot is not implemented')

    def find_chapter_plots(self, project_id: str) -> list[dict[str, Any]]:
        """章別プロットを取得

        Args:
            project_id: プロジェクトID

        Returns:
            章別プロットのリスト
        """
        raise NotImplementedError('find_chapter_plots is not implemented')

    def find_episode_plots(self, project_id: str) -> list[dict[str, Any]]:
        """話別プロットを取得

        Args:
            project_id: プロジェクトID

        Returns:
            話別プロットのリスト
        """
        raise NotImplementedError('find_episode_plots is not implemented')

    def find_incomplete_chapters(self, project_id: str) -> list[int]:
        """未完成の章番号を取得

        Args:
            project_id: プロジェクトID

        Returns:
            未完成章番号のリスト
        """
        raise NotImplementedError('find_incomplete_chapters is not implemented')

    def calculate_file_completion(self, file_content: dict[str, Any]) -> int:
        """ファイル完成度を計算(0-100)

        Args:
            file_content: ファイル内容

        Returns:
            完成度(0-100)
        """
        raise NotImplementedError('calculate_file_completion is not implemented')

    def get_project_root(self, project_id: str) -> str | None:
        """プロジェクトルートパスを取得

        Args:
            project_id: プロジェクトID

        Returns:
            プロジェクトルートパス(存在しない場合はNone)
        """
        raise NotImplementedError('get_project_root is not implemented')
