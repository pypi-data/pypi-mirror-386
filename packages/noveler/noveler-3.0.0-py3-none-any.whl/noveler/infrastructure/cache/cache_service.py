"""キャッシュサービス

セッションデータやテンポラリデータのキャッシュ管理
"""

import contextlib
import json
import time
from pathlib import Path
from typing import Any


class CacheService:
    """キャッシュサービス実装"""

    def __init__(self, cache_dir: Path | None = None) -> None:
        self.cache_dir = cache_dir or Path.cwd() / ".cache"
        self.cache_dir.mkdir(exist_ok=True)

    def get(self, key: str) -> Any | None:
        """キャッシュデータを取得"""
        cache_file = self.cache_dir / f"{key}.json"

        if not cache_file.exists():
            return None

        try:
            with cache_file.open("r", encoding="utf-8") as f:
                cache_data = json.load(f)

            # TTLチェック
            if cache_data.get("expires_at") and time.time() > cache_data["expires_at"]:
                cache_file.unlink()
                return None

            return cache_data.get("data")

        except (json.JSONDecodeError, OSError):
            return None

    def set(self, key: str, data: Any, ttl: int | None = None) -> None:
        """キャッシュデータを設定"""
        cache_file = self.cache_dir / f"{key}.json"

        cache_data = {
            "data": data,
            "created_at": time.time(),
            "expires_at": time.time() + ttl if ttl else None
        }

        try:
            with cache_file.open("w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except OSError:
            pass  # キャッシュ保存失敗は無視

    def delete(self, key: str) -> None:
        """キャッシュデータを削除"""
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            with contextlib.suppress(OSError):
                cache_file.unlink()

    def clear(self) -> None:
        """全キャッシュを削除"""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
        except OSError:
            pass
