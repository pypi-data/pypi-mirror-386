"""ローカルファイルシステムリポジトリ実装

ファイルI/Oとハッシュ計算の実装をインフラ層に配置
"""

import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.repositories.file_system_repository import FileSystemRepository


class LocalFileSystemRepository(FileSystemRepository):
    """ローカルファイルシステムベースのリポジトリ"""

    def exists(self, path: str | Path) -> bool:
        """パスの存在を確認する

        Args:
            path: 確認対象のパス(文字列)

        Returns:
            パスが存在する場合True
        """
        return Path(path).exists()

    def is_directory(self, path: str | Path) -> bool:
        """パスがディレクトリかどうか確認する

        Args:
            path: 確認対象のパス(文字列)

        Returns:
            パスがディレクトリの場合True
        """
        return Path(path).is_dir()

    def list_files(self, directory: str, extensions: set[str]) -> list[str]:
        """指定拡張子のファイルをリストアップする

        Args:
            directory: 検索対象ディレクトリ
            extensions: 対象拡張子のセット(例: {'.yaml', '.yml'})

        Returns:
            マッチしたファイルのリスト
        """
        directory_path = Path(directory)
        if not directory_path.exists() or not directory_path.is_dir():
            return []

        return [
            str(file_path)
            for file_path in directory_path.iterdir()
            if file_path.is_file() and file_path.suffix.lower() in extensions
        ]

    def get_file_info(self, file_path: str | Path) -> dict[str, str | int | float] | None:
        """ファイルの状態情報を取得する

        Args:
            file_path: ファイルパス(文字列)

        Returns:
            ファイル状態情報の辞書(mtime, size, hash等)
            ファイルが存在しない場合はNone
        """
        try:
            path_obj = Path(file_path)
            if not path_obj.exists():
                return None

            stat = path_obj.stat()

            # ファイルハッシュ計算
            file_hash = self.calculate_hash(file_path)

            return {
                "mtime": stat.st_mtime,
                "size": stat.st_size,
                "hash": file_hash,
                "last_checked": time.time(),
                "path": str(file_path),
            }
        except OSError:
            # ファイルアクセスエラーは通常の状況として扱う
            return None

    def calculate_hash(self, file_path: str | Path) -> str | None:
        """ファイルのハッシュ値を計算する

        Args:
            file_path: ファイルパス(文字列)

        Returns:
            ハッシュ値(MD5)
            ファイルが読み込めない場合はNone
        """
        try:
            with Path(file_path).open("rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except OSError:
            return None

    def get_modification_time(self, file_path: str | Path) -> datetime | None:
        """ファイルの最終更新時刻を取得

        Args:
            file_path: ファイルパス(文字列)

        Returns:
            最終更新時刻(取得失敗時None)
        """
        try:
            path_obj = Path(file_path)
            if path_obj.exists():
                return datetime.fromtimestamp(path_obj.stat().st_mtime, tz=timezone.utc)
            return None
        except OSError:
            return None

    def read_yaml(self, file_path: str | Path) -> dict[str, Any] | None:
        """YAMLファイルを読み込み

        Args:
            file_path: YAMLファイルパス(文字列)

        Returns:
            パースされたデータ(読み込み失敗時None)
        """
        try:
            with Path(file_path).open(encoding="utf-8") as f:
                return yaml.safe_load(f)
        except (OSError, yaml.YAMLError):
            return None

    def write_yaml(self, file_path: str | Path, data: dict[str, Any]) -> bool:
        """YAMLファイルに書き込み

        Args:
            file_path: YAMLファイルパス(文字列)
            data: 書き込むデータ

        Returns:
            成功時True
        """
        try:
            path_obj = Path(file_path)
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            with Path(path_obj).open("w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
            return True
        except (OSError, yaml.YAMLError):
            return False
