#!/usr/bin/env python3
"""プロットデータリポジトリインターフェース
DDD原則:Domain層でインターフェースを定義
"""

from abc import ABC, abstractmethod
from typing import Any


class PlotDataRepository(ABC):
    """プロットデータアクセスのリポジトリインターフェース"""

    @abstractmethod
    def load_master_plot(self, project_path: str) -> dict[str, Any]:
        """
        マスタープロットを読み込む

        Args:
            project_path: プロジェクトのルートパス

        Returns:
            マスタープロットの辞書データ

        Raises:
            FileNotFoundError: プロットファイルが存在しない場合
        """

    @abstractmethod
    def save_master_plot(self, project_path: str, plot_data: dict[str, Any]) -> None:
        """
        マスタープロットを保存する

        Args:
            project_path: プロジェクトのルートパス
            plot_data: 保存するプロットデータ
        """

    @abstractmethod
    def load_chapter_plot(self, project_path: str, chapter_number: int) -> dict[str, Any]:
        """
        章別プロットを読み込む

        Args:
            project_path: プロジェクトのルートパス
            chapter_number: 章番号

        Returns:
            章別プロットの辞書データ
        """

    @abstractmethod
    def save_chapter_plot(self, project_path: str, chapter_number: int, plot_data: dict[str, Any]) -> None:
        """
        章別プロットを保存する

        Args:
            project_path: プロジェクトのルートパス
            chapter_number: 章番号
            plot_data: 保存するプロットデータ
        """

    @abstractmethod
    def list_chapter_plots(self, project_path: str) -> list[int]:
        """
        存在する章番号のリストを取得

        Args:
            project_path: プロジェクトのルートパス

        Returns:
            章番号のリスト
        """

    @abstractmethod
    def get_plot_progress(self, project_path: str) -> dict[str, Any]:
        """
        プロット作成進捗を取得

        Args:
            project_path: プロジェクトのルートパス

        Returns:
            進捗情報の辞書
        """

    @abstractmethod
    def update_plot_progress(self, project_path: str, progress_data: dict[str, Any]) -> None:
        """
        プロット作成進捗を更新

        Args:
            project_path: プロジェクトのルートパス
            progress_data: 更新する進捗データ
        """


class PlotValidationDataRepository(ABC):
    """プロット検証データアクセスのリポジトリインターフェース"""

    @abstractmethod
    def load_plot_validation_rules(self, project_path: str) -> dict[str, Any]:
        """
        プロット検証ルールを読み込む

        Args:
            project_path: プロジェクトのルートパス

        Returns:
            検証ルールの辞書データ
        """

    @abstractmethod
    def save_plot_validation_results(self, project_path: str, results: dict[str, Any]) -> None:
        """
        プロット検証結果を保存する

        Args:
            project_path: プロジェクトのルートパス
            results: 保存する検証結果
        """


class ProjectDetectionRepository(ABC):
    """プロジェクト検出データアクセスのリポジトリインターフェース"""

    @abstractmethod
    def scan_directory_structure(self, base_path: str) -> dict[str, Any]:
        """
        ディレクトリ構造をスキャンする

        Args:
            base_path: スキャンするベースパス

        Returns:
            ディレクトリ構造の情報
        """

    @abstractmethod
    def check_project_markers(self, project_path: str) -> dict[str, bool]:
        """
        プロジェクトマーカーファイルの存在確認

        Args:
            project_path: プロジェクトのルートパス

        Returns:
            マーカーファイルの存在状況
        """

    @abstractmethod
    def get_project_metadata(self, project_path: str) -> dict[str, Any]:
        """
        プロジェクトメタデータを取得

        Args:
            project_path: プロジェクトのルートパス

        Returns:
            プロジェクトメタデータ
        """
