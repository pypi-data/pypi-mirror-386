"""章別プロットリポジトリインターフェース

SPEC-PLOT-001: Claude Code連携プロット生成システム
"""

from abc import ABC, abstractmethod
from pathlib import Path

from noveler.domain.entities.chapter_plot import ChapterPlot
from noveler.domain.value_objects.chapter_number import ChapterNumber


class ChapterPlotNotFoundError(Exception):
    """章別プロットが見つからない場合のエラー"""


class ChapterPlotRepository(ABC):
    """章別プロットリポジトリインターフェース

    章別プロット情報の永続化・取得を担当するリポジトリの抽象インターフェース。
    DDD原則に従い、ドメイン層でインターフェースを定義し、
    インフラストラクチャ層で具象実装を行う。
    """

    def __init__(self, project_root: Path) -> None:
        """リポジトリ初期化

        Args:
            project_root: プロジェクトルートディレクトリ
        """
        self.project_root = project_root

    @abstractmethod
    def find_by_chapter_number(self, chapter_number: ChapterNumber) -> ChapterPlot:
        """章番号による章別プロット取得

        Args:
            chapter_number: 章番号

        Returns:
            ChapterPlot: 章別プロット情報

        Raises:
            ChapterPlotNotFoundError: 章別プロットが見つからない場合
        """

    @abstractmethod
    def find_by_episode_number(self, episode_number: int) -> ChapterPlot:
        """エピソード番号による章別プロット取得

        指定されたエピソードを含む章の章別プロット情報を取得する。
        内部的にはエピソード番号から章番号を推定し、該当する章別プロットを取得する。

        Args:
            episode_number: エピソード番号

        Returns:
            ChapterPlot: エピソードを含む章の章別プロット情報

        Raises:
            ChapterPlotNotFoundError: 該当する章別プロットが見つからない場合
        """

    @abstractmethod
    def exists(self, chapter_number: ChapterNumber) -> bool:
        """章別プロットの存在確認

        Args:
            chapter_number: 章番号

        Returns:
            bool: 存在する場合True
        """

    @abstractmethod
    def list_all(self) -> list[ChapterPlot]:
        """全ての章別プロット一覧取得

        Returns:
            list[ChapterPlot]: 章別プロットのリスト(章番号順)
        """

    @abstractmethod
    def get_chapter_plot_file_path(self, chapter_number: ChapterNumber) -> Path:
        """章別プロットファイルパスを取得

        Args:
            chapter_number: 章番号

        Returns:
            Path: 章別プロットファイルのパス
        """
