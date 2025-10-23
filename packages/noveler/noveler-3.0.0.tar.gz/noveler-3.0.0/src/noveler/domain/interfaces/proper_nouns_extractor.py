"""固有名詞抽出のインターフェース"""

from abc import ABC, abstractmethod


class IProperNounsExtractor(ABC):
    """固有名詞抽出のインターフェース"""

    @abstractmethod
    def extract_from_yaml(self, yaml_path: str) -> set[str]:
        """YAMLファイルから固有名詞を抽出"""

    @abstractmethod
    def extract_all(self) -> set[str]:
        """全ての固有名詞を抽出"""
