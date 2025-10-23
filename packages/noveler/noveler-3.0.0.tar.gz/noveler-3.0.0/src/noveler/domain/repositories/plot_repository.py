#!/usr/bin/env python3
"""プロットリポジトリインターフェース

DDD原則に基づくリポジトリインターフェース
プロット情報の永続化を抽象化
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, TypedDict


class PlotInfo(TypedDict):
    """プロット情報の型定義"""

    title: str
    summary: str
    chapter_number: int | None
    scenes: list[dict[str, str]]


class MasterPlotData(TypedDict):
    """マスタープロットデータの型定義"""

    title: str
    genre: str
    concept: str
    chapters: list[dict[str, str]]


class PlotRepository(ABC):
    """プロットリポジトリインターフェース"""

    @abstractmethod
    def find_episode_plot(self, project_name: str, episode_number: int) -> dict[str, Any] | None:
        """エピソードのプロット情報を取得

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号

        Returns:
            プロット情報の辞書、見つからない場合はNone
        """

    @abstractmethod
    def find_chapter_plot(self, project_name: str, chapter_number: int) -> dict[str, Any] | None:
        """章のプロット情報を取得

        Args:
            project_name: プロジェクト名
            chapter_number: 章番号

        Returns:
            章プロット情報の辞書、見つからない場合はNone
        """

    @abstractmethod
    def save_episode_plot(self, project_name: str, episode_number: int) -> None:
        """エピソードのプロット情報を保存

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号
            plot_data: プロット情報
        """

    @abstractmethod
    def exists(self, project_name: str, episode_number: int) -> bool:
        """話プロットが存在するか確認

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号

        Returns:
            存在する場合True
        """

    @abstractmethod
    def get_all_episode_plots(self, project_name: str) -> list[dict[str, Any]]:
        """プロジェクトの全話プロットを取得

        Args:
            project_name: プロジェクト名

        Returns:
            話プロットのリスト
        """

    @abstractmethod
    def find_all_episodes(self) -> list[Any]:
        """全エピソードのプロット情報を取得

        Returns:
            話プロット情報のリスト
        """

    @abstractmethod
    def find_episode_plot_by_number(self, episode_number: int) -> PlotInfo | None:
        """エピソード番号でプロット情報を取得

        Args:
            episode_number: エピソード番号

        Returns:
            プロット情報、見つからない場合はNone
        """

    @abstractmethod
    def load_master_plot(self, project_root: Path) -> MasterPlotData:
        """全体構成(マスタープロット)を読み込む

        Args:
            project_root: プロジェクトのルートディレクトリ

        Returns:
            全体構成データの辞書

        Raises:
            FileNotFoundError: 全体構成.yamlが存在しない場合
        """

    @abstractmethod
    def get_chapter_plot_files(self, project_root: Path) -> list[Path]:
        """章別プロットファイルのリストを取得

        Args:
            project_root: プロジェクトのルートディレクトリ

        Returns:
            章別プロットファイルのパスリスト
        """

    @abstractmethod
    def load_chapter_plot(self, chapter_file: str) -> dict[str, str]:
        """章別プロットファイルを読み込む

        Args:
            chapter_file: 章別プロットファイルのパス

        Returns:
            章別プロットデータの辞書
        """
