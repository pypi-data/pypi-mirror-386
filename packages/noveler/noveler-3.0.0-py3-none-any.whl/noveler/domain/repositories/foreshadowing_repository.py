"""
伏線管理リポジトリのインターフェース
ドメイン層で定義し、インフラ層で実装する
"""

from abc import ABC, abstractmethod

from noveler.domain.value_objects.foreshadowing import Foreshadowing, ForeshadowingId


class ForeshadowingRepository(ABC):
    """伏線管理リポジトリのインターフェース"""

    @abstractmethod
    def load_all(self, project_root: str) -> list[Foreshadowing]:
        """
        プロジェクトのすべての伏線を読み込む

        Args:
            project_root: プロジェクトのルートディレクトリ

        Returns:
            伏線のリスト

        Raises:
            FileNotFoundError: 伏線管理ファイルが存在しない場合
        """

    @abstractmethod
    def save_all(self, foreshadowings: list[Foreshadowing], project_root: str) -> None:
        """
        すべての伏線を保存する

        Args:
            foreshadowings: 保存する伏線のリスト
            project_root: プロジェクトのルートディレクトリ
        """

    @abstractmethod
    def find_by_id(self, foreshadowing_id: ForeshadowingId, project_root: str) -> Foreshadowing | None:
        """
        IDで伏線を検索する

        Args:
            foreshadowing_id: 伏線ID
            project_root: プロジェクトのルートディレクトリ

        Returns:
            見つかった伏線、存在しない場合はNone
        """

    @abstractmethod
    def exists(self, project_root: str) -> bool:
        """
        伏線管理ファイルが存在するか確認する

        Args:
            project_root: プロジェクトのルートディレクトリ

        Returns:
            存在する場合True
        """

    @abstractmethod
    def create_from_template(self, project_root: str) -> None:
        """
        テンプレートから伏線管理ファイルを作成する

        Args:
            project_root: プロジェクトのルートディレクトリ
        """
