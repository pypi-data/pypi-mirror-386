"""ファイル保存ストラテジーインターフェース

統一ファイル保存サービスで使用するストラテジーパターンの基底インターフェース
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class IFileStorageStrategy(ABC):
    """ファイル保存ストラテジーの基底インターフェース"""

    @abstractmethod
    def save(self, file_path: Path, content: Any, metadata: dict | None = None) -> bool:
        """ファイルを保存

        Args:
            file_path: 保存先パス
            content: 保存内容
            metadata: メタデータ（オプション）

        Returns:
            保存成功時True
        """

    @abstractmethod
    def load(self, file_path: Path) -> Any | None:
        """ファイルを読み込み

        Args:
            file_path: 読み込みファイルパス

        Returns:
            ファイル内容、失敗時はNone
        """

    @abstractmethod
    def load_with_metadata(self, file_path: Path) -> tuple[Any | None, dict | None]:
        """ファイルをメタデータと共に読み込み

        Args:
            file_path: 読み込みファイルパス

        Returns:
            (ファイル内容, メタデータ)のタプル、失敗時は(None, None)
        """

    @abstractmethod
    def get_supported_extensions(self) -> list[str]:
        """サポートする拡張子を取得

        Returns:
            サポートする拡張子のリスト
        """

    @abstractmethod
    def can_handle(self, file_path: Path, content_type: str) -> bool:
        """指定されたファイルパス・内容タイプを処理できるかチェック

        Args:
            file_path: ファイルパス
            content_type: 内容タイプ

        Returns:
            処理可能時True
        """
