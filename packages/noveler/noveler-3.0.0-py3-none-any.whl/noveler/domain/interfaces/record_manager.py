"""記録マネージャーのインターフェース"""

from abc import ABC, abstractmethod
from typing import Any


class IRecordManager(ABC):
    """記録マネージャーのインターフェース"""

    @abstractmethod
    def create_record(self, episode: int, data: dict[str, Any]) -> str:
        """記録を作成"""

    @abstractmethod
    def load_record(self, episode: int) -> dict[str, Any] | None:
        """記録を読み込み"""

    @abstractmethod
    def update_record(self, episode: int, data: dict[str, Any]) -> None:
        """記録を更新"""

    @abstractmethod
    def list_records(self) -> list[dict[str, Any]]:
        """記録一覧を取得"""
