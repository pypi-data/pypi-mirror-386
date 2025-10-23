"""環境管理のインターフェース"""

from abc import ABC, abstractmethod


class IEnvironmentManager(ABC):
    """環境管理のインターフェース"""

    @abstractmethod
    def get_mode(self) -> str:
        """現在のモード(production/test)を取得"""

    @abstractmethod
    def is_test_mode(self) -> bool:
        """テストモードかどうか"""

    @abstractmethod
    def setup_environment(self, project_root: str) -> None:
        """環境変数を設定"""
