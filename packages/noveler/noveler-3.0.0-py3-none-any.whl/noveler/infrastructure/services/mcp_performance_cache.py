#!/usr/bin/env python3
"""MCPパフォーマンスキャッシュシステム

MCPサーバーの処理結果をキャッシュして高速化を実現する
"""

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from noveler.domain.value_objects.project_time import project_now
from noveler.presentation.shared.shared_utilities import console


class MCPCacheEntry:
    """MCPキャッシュエントリ"""

    def __init__(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        self.key = key
        self.value = value
        self.created_at = project_now().datetime
        self.expires_at = self.created_at + timedelta(seconds=ttl_seconds)
        self.access_count = 0
        self.last_accessed = self.created_at

    def is_expired(self) -> bool:
        """キャッシュが期限切れかチェック"""
        return project_now().datetime > self.expires_at

    def access(self) -> Any:
        """キャッシュにアクセスして値を取得"""
        self.access_count += 1
        self.last_accessed = project_now().datetime
        return self.value

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換（永続化用）"""
        return {
            "key": self.key,
            "value": self.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MCPCacheEntry":
        """辞書から復元"""
        entry = cls.__new__(cls)
        entry.key = data["key"]
        entry.value = data["value"]
        entry.created_at = datetime.fromisoformat(data["created_at"])
        entry.expires_at = datetime.fromisoformat(data["expires_at"])
        entry.access_count = data["access_count"]
        entry.last_accessed = datetime.fromisoformat(data["last_accessed"])
        return entry


class MCPPerformanceCache:
    """MCPパフォーマンスキャッシュ"""

    def __init__(self, cache_dir: Path | None = None, max_entries: int = 1000) -> None:
        self.cache_dir = cache_dir or Path.cwd() / "temp" / "mcp_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_entries = max_entries

        # メモリキャッシュ
        self.memory_cache: dict[str, MCPCacheEntry] = {}

        # 永続キャッシュファイル
        self.persistent_cache_file = self.cache_dir / "mcp_cache_persistent.json"

        # 統計情報
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "persistent_saves": 0,
            "persistent_loads": 0
        }

        # 初期化時に永続キャッシュを読み込み
        self._load_persistent_cache()

    def _generate_cache_key(self, tool_name: str, params: dict[str, Any]) -> str:
        """キャッシュキーを生成"""
        # パラメータを正規化してハッシュ化
        normalized_params = self._normalize_params(params)
        key_data = f"{tool_name}:{json.dumps(normalized_params, sort_keys=True)}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]

    def _normalize_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """パラメータを正規化（キャッシュキー生成用）"""
        normalized = {}
        for key, value in params.items():
            if isinstance(value, str | int | float | bool):
                normalized[key] = value
            elif isinstance(value, list | dict):
                # 複雑なデータ構造は文字列化してハッシュ
                normalized[key] = str(hash(str(value)))
            else:
                # その他のオブジェクトは型名のみ
                normalized[key] = type(value).__name__
        return normalized

    def get(self, tool_name: str, params: dict[str, Any]) -> Any | None:
        """キャッシュから値を取得"""
        cache_key = self._generate_cache_key(tool_name, params)

        # メモリキャッシュから検索
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            if not entry.is_expired():
                self.stats["hits"] += 1
                return entry.access()
            # 期限切れエントリを削除
            del self.memory_cache[cache_key]

        self.stats["misses"] += 1
        return None

    def set(self, tool_name: str, params: dict[str, Any], value: Any, ttl_seconds: int = 3600) -> None:
        """キャッシュに値を設定"""
        cache_key = self._generate_cache_key(tool_name, params)

        # メモリキャッシュ容量チェック
        if len(self.memory_cache) >= self.max_entries:
            self._evict_lru()

        # 新しいエントリを作成
        entry = MCPCacheEntry(cache_key, value, ttl_seconds)
        self.memory_cache[cache_key] = entry

        # 重要なデータは永続化
        if self._should_persist(tool_name, params):
            self._save_to_persistent_cache(entry)

    def _should_persist(self, tool_name: str, params: dict[str, Any]) -> bool:
        """永続化すべきかの判定"""
        # 高コストな処理結果は永続化
        persistent_tools = [
            "noveler_write",  # 執筆結果
            "check_story_structure",  # ストーリー構成分析
            "check_writing_expression",  # 文章表現分析
            "noveler_plot",  # プロット生成
        ]

        return tool_name in persistent_tools

    def _evict_lru(self) -> None:
        """LRU（最も使用されていないエントリ）を削除"""
        if not self.memory_cache:
            return

        # 最もアクセス時間が古いエントリを見つけて削除
        lru_key = min(
            self.memory_cache.keys(),
            key=lambda k: self.memory_cache[k].last_accessed
        )

        del self.memory_cache[lru_key]
        self.stats["evictions"] += 1

    def _save_to_persistent_cache(self, entry: MCPCacheEntry) -> None:
        """永続キャッシュに保存"""
        try:
            # 既存の永続キャッシュを読み込み
            if self.persistent_cache_file.exists():
                with open(self.persistent_cache_file, encoding="utf-8") as f:
                    persistent_data = json.load(f)
            else:
                persistent_data = {"entries": {}}

            # 新しいエントリを追加
            persistent_data["entries"][entry.key] = entry.to_dict()

            # ファイルに書き戻し
            with open(self.persistent_cache_file, "w", encoding="utf-8") as f:
                json.dump(persistent_data, f, ensure_ascii=False, indent=2)

            self.stats["persistent_saves"] += 1

        except Exception as e:
            console.print(f"[yellow]永続キャッシュ保存エラー: {e}[/yellow]")

    def _load_persistent_cache(self) -> None:
        """永続キャッシュを読み込み"""
        try:
            if not self.persistent_cache_file.exists():
                return

            with open(self.persistent_cache_file, encoding="utf-8") as f:
                persistent_data = json.load(f)

            # メモリキャッシュに復元（有効期限内のもののみ）
            entries = persistent_data.get("entries", {})
            loaded_count = 0

            for entry_data in entries.values():
                try:
                    entry = MCPCacheEntry.from_dict(entry_data)
                    if not entry.is_expired():
                        self.memory_cache[entry.key] = entry
                        loaded_count += 1
                except Exception:
                    continue  # 破損したエントリはスキップ

            if loaded_count > 0:
                console.print(f"[green]永続キャッシュから {loaded_count} 件のエントリを復元[/green]")
                self.stats["persistent_loads"] += loaded_count

        except Exception as e:
            console.print(f"[yellow]永続キャッシュ読み込みエラー: {e}[/yellow]")

    def clear_expired(self) -> int:
        """期限切れエントリをクリア"""
        expired_keys = [
            key for key, entry in self.memory_cache.items()
            if entry.is_expired()
        ]

        for key in expired_keys:
            del self.memory_cache[key]

        return len(expired_keys)

    def clear_all(self) -> None:
        """全てのキャッシュをクリア"""
        self.memory_cache.clear()
        if self.persistent_cache_file.exists():
            self.persistent_cache_file.unlink()

        # 統計情報もリセット
        for key in self.stats:
            self.stats[key] = 0

    def get_stats(self) -> dict[str, Any]:
        """キャッシュ統計情報を取得"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0

        return {
            "memory_entries": len(self.memory_cache),
            "hit_rate_percent": round(hit_rate, 2),
            "total_hits": self.stats["hits"],
            "total_misses": self.stats["misses"],
            "total_evictions": self.stats["evictions"],
            "persistent_saves": self.stats["persistent_saves"],
            "persistent_loads": self.stats["persistent_loads"],
            "cache_dir": str(self.cache_dir),
            "max_entries": self.max_entries
        }

    def invalidate_by_pattern(self, pattern: str) -> int:
        """パターンマッチングでキャッシュを無効化"""
        invalidated = 0
        keys_to_remove = []

        for key, entry in self.memory_cache.items():
            # エントリの元データからツール名をチェック
            if pattern in entry.key or (hasattr(entry, "tool_name") and pattern in entry.tool_name):
                keys_to_remove.append(key)
                invalidated += 1

        for key in keys_to_remove:
            del self.memory_cache[key]

        return invalidated

    def warm_up(self, common_requests: list[dict[str, Any]]) -> None:
        """キャッシュのウォームアップ（よく使われるリクエストを事前実行）"""
        console.print("[blue]MCPキャッシュのウォームアップを開始...[/blue]")

        warmed_count = 0
        for request in common_requests:
            tool_name = request.get("tool_name")
            params = request.get("params", {})

            if tool_name and not self.get(tool_name, params):
                # キャッシュミスの場合のみカウント（実際の処理は別途実装が必要）
                warmed_count += 1

        console.print(f"[green]ウォームアップ完了: {warmed_count} 件のリクエストを処理対象として特定[/green]")


# グローバルインスタンス（シングルトンパターン）
_cache_instance: MCPPerformanceCache | None = None

def get_mcp_cache() -> MCPPerformanceCache:
    """MCPパフォーマンスキャッシュのグローバルインスタンスを取得"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = MCPPerformanceCache()
    return _cache_instance


def cached_mcp_call(tool_name: str, params: dict[str, Any], ttl_seconds: int = 3600):
    """MCPツール呼び出しのキャッシュデコレータ"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache = get_mcp_cache()

            # キャッシュから取得を試行
            cached_result = cache.get(tool_name, params)
            if cached_result is not None:
                return cached_result

            # キャッシュミスの場合は実際に処理を実行
            result = func(*args, **kwargs)

            # 結果をキャッシュに保存
            cache.set(tool_name, params, result, ttl_seconds)

            return result
        return wrapper
    return decorator
