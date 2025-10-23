#!/usr/bin/env python3
"""ファイルシステムリポジトリインターフェース(DDD)

ファイルシステム操作を抽象化
ドメイン層で定義し、インフラ層で実装
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class FileSystemRepository(ABC):
    """ファイルシステムリポジトリインターフェース"""

    @abstractmethod
    def exists(self, path: str) -> bool:
        """パスが存在するか確認

        Args:
            path: チェックするパス

        Returns:
            存在する場合True
        """

    @abstractmethod
    def is_directory(self, path: str) -> bool:
        """パスがディレクトリか確認

        Args:
            path: チェックするパス

        Returns:
            ディレクトリの場合True
        """

    @abstractmethod
    def list_files(self, directory: str, extensions: set[str]) -> list[str]:
        """ディレクトリ内のファイルをリスト

        Args:
            directory: 対象ディレクトリ
            extensions: フィルタする拡張子のセット(例: {'.yaml', '.yml'})

        Returns:
            ファイルパスのリスト
        """

    @abstractmethod
    def get_file_info(self, file_path: str) -> dict[str, Any] | None:
        """ファイル情報を取得

        Args:
            file_path: ファイルパス

        Returns:
            ファイル情報(存在しない場合None)
            {
                'mtime': float,  # 最終更新時刻
                'size': int,     # ファイルサイズ
                'hash': str,     # コンテンツハッシュ
                'path': str      # フルパス
            }
        """

    @abstractmethod
    def calculate_hash(self, file_path: str) -> str | None:
        """ファイルのハッシュ値を計算

        Args:
            file_path: ファイルパス

        Returns:
            ハッシュ値(読み取り失敗時None)
        """

    @abstractmethod
    def get_modification_time(self, file_path: str) -> datetime | None:
        """ファイルの最終更新時刻を取得

        Args:
            file_path: ファイルパス

        Returns:
            最終更新時刻(取得失敗時None)
        """

    @abstractmethod
    def read_yaml(self, file_path: str) -> dict[str, Any] | None:
        """YAMLファイルを読み込み

        Args:
            file_path: YAMLファイルパス

        Returns:
            パースされたデータ(読み込み失敗時None)
        """

    @abstractmethod
    def write_yaml(self, file_path: str, data: dict[str, Any]) -> bool:
        """YAMLファイルに書き込み

        Args:
            file_path: YAMLファイルパス
            data: 書き込むデータ

        Returns:
            成功時True
        """
