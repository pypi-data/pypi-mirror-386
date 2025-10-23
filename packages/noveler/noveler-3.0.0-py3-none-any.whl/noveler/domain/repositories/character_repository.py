"""キャラクターリポジトリインターフェース

キャラクター情報の永続化を抽象化するリポジトリインターフェース。
"""

from abc import ABC, abstractmethod

from noveler.domain.value_objects.character_profile import CharacterProfile


class CharacterRepository(ABC):
    """キャラクターリポジトリ

    プロジェクトのキャラクター情報を管理するリポジトリ。
    """

    @abstractmethod
    def find_all_by_project(self, project_name: str) -> list[CharacterProfile]:
        """プロジェクトの全キャラクターを取得

        Args:
            project_name: プロジェクト名

        Returns:
            キャラクタープロファイルのリスト
        """

    @abstractmethod
    def find_by_name(self, project_name: str, character_name: str) -> CharacterProfile | None:
        """名前でキャラクターを検索

        Args:
            project_name: プロジェクト名
            character_name: キャラクター名

        Returns:
            キャラクタープロファイル(見つからない場合None)
        """

    @abstractmethod
    def save(self, project_name: str, character: CharacterProfile) -> None:
        """キャラクターを保存

        Args:
            project_name: プロジェクト名
            character: 保存するキャラクター
        """

    @abstractmethod
    def delete(self, project_name: str, character_name: str) -> None:
        """キャラクターを削除

        Args:
            project_name: プロジェクト名
            character_name: 削除するキャラクター名
        """

    @abstractmethod
    def exists(self, project_name: str, character_name: str) -> bool:
        """キャラクターが存在するかチェック

        Args:
            project_name: プロジェクト名
            character_name: キャラクター名

        Returns:
            存在する場合True
        """
