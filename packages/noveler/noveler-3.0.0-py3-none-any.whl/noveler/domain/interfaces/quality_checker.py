"""品質チェッカーのインターフェース"""

from abc import ABC, abstractmethod
from typing import Any


class IQualityChecker(ABC):
    """品質チェッカーのインターフェース"""

    @abstractmethod
    def check_file(self, file_path: str) -> dict[str, Any]:
        """ファイルの品質をチェック"""

    @abstractmethod
    def check_text(self, text: str) -> dict[str, Any]:
        """テキストの品質をチェック"""
