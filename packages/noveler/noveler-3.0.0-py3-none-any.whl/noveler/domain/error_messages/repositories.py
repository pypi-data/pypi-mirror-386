"""エラーメッセージドメインのリポジトリインターフェース

エラーパターンと改善例の永続化を抽象化
"""

from abc import ABC, abstractmethod


class ErrorPatternRepository(ABC):
    """エラーパターンリポジトリインターフェース"""

    @abstractmethod
    def get_pattern(self, error_code: str) -> dict:
        """エラーコードに対応するパターンを取得"""

    @abstractmethod
    def get_all_patterns(self) -> dict[str, dict]:
        """すべてのエラーパターンを取得"""


class ExampleRepository(ABC):
    """改善例リポジトリインターフェース"""

    @abstractmethod
    def get_examples(self, error_type: str, sub_type: str) -> list[dict]:
        """エラータイプに対応する改善例を取得"""

    @abstractmethod
    def add_example(self, error_type: str, example: dict) -> None:
        """新しい改善例を追加"""

    @abstractmethod
    def get_popular_examples(self, error_type: str, limit: int) -> list[dict]:
        """人気の高い改善例を取得"""
