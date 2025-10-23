"""YAML操作のインターフェース"""

from abc import ABC, abstractmethod
from typing import Any


class IYamlHandler(ABC):
    """YAML操作のインターフェース"""

    @abstractmethod
    def load_yaml(self, file_path: str) -> dict[str, Any]:
        """YAMLファイルを読み込み"""

    @abstractmethod
    def save_yaml(self, data: dict[str, Any], file_path: str) -> None:
        """YAMLファイルに保存"""

    @abstractmethod
    def format_yaml(self, data: dict[str, Any]) -> str:
        """データをYAML形式にフォーマット"""
