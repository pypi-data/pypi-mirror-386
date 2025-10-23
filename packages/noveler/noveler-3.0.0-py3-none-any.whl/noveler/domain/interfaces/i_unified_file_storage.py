"""統一ファイル保存サービスインターフェース

用途に応じてファイル形式を自動判定し、適切な保存を行うサービスのインターフェース
"""

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any


class FileContentType(Enum):
    """ファイル内容タイプ"""

    MANUSCRIPT = "manuscript"  # 原稿・ドキュメント
    CONFIG = "config"  # 設定ファイル
    METADATA = "metadata"  # メタデータ
    CACHE = "cache"  # キャッシュデータ
    API_RESPONSE = "api_response"  # API応答
    AUTO = "auto"  # 自動判定


class IUnifiedFileStorage(ABC):
    """統一ファイル保存サービスインターフェース"""

    @abstractmethod
    def save(
        self,
        file_path: Path | str,
        content: Any,
        content_type: FileContentType = FileContentType.AUTO,
        metadata: dict | None = None,
        encoding: str = "utf-8",
    ) -> bool:
        """ファイルを保存（形式自動選択）

        Args:
            file_path: 保存先パス
            content: 保存内容
            content_type: 内容タイプ（AUTO時は自動判定）
            metadata: メタデータ
            encoding: エンコーディング

        Returns:
            保存成功時True
        """

    @abstractmethod
    def load(self, file_path: Path | str) -> Any | None:
        """ファイルを読み込み（形式自動判定）

        Args:
            file_path: 読み込みファイルパス

        Returns:
            ファイル内容、失敗時はNone
        """

    @abstractmethod
    def load_with_metadata(self, file_path: Path | str) -> tuple[Any | None, dict | None]:
        """ファイルをメタデータと共に読み込み

        Args:
            file_path: 読み込みファイルパス

        Returns:
            (ファイル内容, メタデータ)のタプル、失敗時は(None, None)
        """

    @abstractmethod
    def save_manuscript(
        self, episode: int | str, content: str, project_root: Path | None = None, metadata: dict | None = None
    ) -> bool:
        """原稿専用の保存メソッド

        Args:
            episode: エピソード番号
            content: 原稿内容
            project_root: プロジェクトルート
            metadata: メタデータ

        Returns:
            保存成功時True
        """

    @abstractmethod
    def get_optimal_format(self, content_type: FileContentType, file_path: Path | None = None) -> str:
        """最適なファイル形式を取得

        Args:
            content_type: 内容タイプ
            file_path: ファイルパス（拡張子判定用）

        Returns:
            推奨される拡張子
        """
