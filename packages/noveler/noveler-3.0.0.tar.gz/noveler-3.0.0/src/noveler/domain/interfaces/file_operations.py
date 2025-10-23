"""ファイル操作のインターフェース"""

from abc import ABC, abstractmethod
from pathlib import Path


class IFileOperations(ABC):
    """ファイル操作のインターフェース"""

    @abstractmethod
    def read_file(self, file_path: Path) -> str:
        """ファイルを読み込み"""

    @abstractmethod
    def write_file(self, file_path: Path, content: str) -> None:
        """ファイルに書き込み"""

    @abstractmethod
    def exists(self, file_path: Path) -> bool:
        """ファイルの存在確認"""

    @abstractmethod
    def list_files(self, directory: Path, pattern: str) -> list[Path]:
        """ディレクトリ内のファイル一覧"""
