"""YAMLファイルキャッシュシステム"""

import time
from pathlib import Path
from threading import Lock
from typing import Any

import yaml


class YAMLCache:
    """シングルトンパターンによるYAMLファイルキャッシュ"""

    _instance = None
    _lock = Lock()

    def __new__(cls) -> None:
        """シングルトンインスタンスの作成。

        スレッドセーフなダブルチェックロッキングパターンを使用して
        クラスのシングルトンインスタンスを作成または取得する。

        Returns:
            YAMLCache: シングルトンインスタンス
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, "_initialized"):
            self._cache: dict[str, dict[str, Any]] = {}
            self._timestamps: dict[str, float] = {}
            self._file_mtimes: dict[str, float] = {}
            self.default_ttl = 3600  # 1時間
            self._initialized = True

    def get(self, filepath: Path, ttl: int = 3600) -> dict[str, Any] | None:
        """キャッシュからYAMLデータを取得"""
        filepath_str = str(filepath.resolve())
        ttl = ttl or self.default_ttl

        # ファイルが存在しない場合
        if not filepath.exists():
            return None

        # ファイルの更新時刻を確認
        current_mtime = filepath.stat().st_mtime

        # キャッシュチェック
        if filepath_str in self._cache:
            # ファイルが更新されていない場合
            if filepath_str in self._file_mtimes and self._file_mtimes[filepath_str] == current_mtime:
                # TTLチェック
                if time.time() - self._timestamps[filepath_str] < ttl:
                    return self._cache[filepath_str].copy()

        # キャッシュミスまたは期限切れ
        return self._load_and_cache(filepath, filepath_str, current_mtime)

    def _load_and_cache(self, filepath: Path, filepath_str: str, mtime: float) -> dict[str, Any] | None:
        """YAMLファイルを読み込んでキャッシュに保存"""
        try:
            with Path(filepath).open(encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if data:
                self._cache[filepath_str] = data
                self._timestamps[filepath_str] = time.time()
                self._file_mtimes[filepath_str] = mtime
                return data.copy()

            return None

        except (OSError, yaml.YAMLError, UnicodeDecodeError):
            # エラーの場合はNoneを返す
            return None

    def invalidate(self, filepath: Path) -> None:
        """特定のファイルのキャッシュを無効化"""
        filepath_str = str(filepath.resolve())
        self._cache.pop(filepath_str, None)
        self._timestamps.pop(filepath_str, None)
        self._file_mtimes.pop(filepath_str, None)

    def clear(self) -> None:
        """全てのキャッシュをクリア"""
        self._cache.clear()
        self._timestamps.clear()
        self._file_mtimes.clear()

    def get_cache_stats(self) -> dict[str, Any]:
        """キャッシュの統計情報を取得"""
        total_size = sum(len(str(v)) for v in self._cache.values())

        return {
            "cached_files": len(self._cache),
            "total_size_bytes": total_size,
            "oldest_entry": min(self._timestamps.values()) if self._timestamps else None,
            "newest_entry": max(self._timestamps.values()) if self._timestamps else None,
        }
