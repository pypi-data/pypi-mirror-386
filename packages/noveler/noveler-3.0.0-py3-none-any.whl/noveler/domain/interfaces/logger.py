"""ロガーのインターフェース"""

from abc import ABC, abstractmethod


class ILogger(ABC):
    """ロガーのインターフェース"""

    @abstractmethod
    def debug(self, message: str) -> None:
        pass

    @abstractmethod
    def info(self, message: str) -> None:
        pass

    @abstractmethod
    def warning(self, message: str) -> None:
        pass

    @abstractmethod
    def error(self, message: str) -> None:
        pass

    @abstractmethod
    def exception(self, message: str) -> None:
        """例外情報付きでエラーレベルでログ出力"""
