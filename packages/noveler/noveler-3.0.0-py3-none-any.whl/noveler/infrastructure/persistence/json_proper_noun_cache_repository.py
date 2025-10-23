#!/usr/bin/env python3
"""JSONベース固有名詞キャッシュリポジトリ実装

ProperNounCacheRepositoryインターフェースの実装
固有名詞をJSONファイルでキャッシュする
"""

import json
import os
import time
from pathlib import Path
from typing import Any

from noveler.domain.entities.proper_noun_collection import ProperNounCollection
from noveler.domain.repositories.proper_noun_cache_repository import ProperNounCacheRepository


class JsonProperNounCacheRepository(ProperNounCacheRepository):
    """JSON固有名詞キャッシュリポジトリ実装"""

    def __init__(self, project_root: Path, cache_filename) -> None:
        """Args:
        project_root: プロジェクトのルートディレクトリ
        cache_filename: キャッシュファイル名
        """
        self.project_root = Path(project_root)
        self.cache_dir = self.project_root / "logs"
        self.cache_file = self.cache_dir / cache_filename

        # キャッシュディレクトリを作成
        self.cache_dir.mkdir(exist_ok=True)

    def save_terms(self, collection) -> None:
        """固有名詞コレクションを保存

        Args:
            collection: 保存する固有名詞コレクション

        Raises:
            IOError: 保存に失敗した場合
        """
        try:
            cache_data: dict[str, Any] = {
                "terms": list(collection._terms),
                "timestamp": time.time(),
                "count": len(collection),
                "version": "1.0",
            }

            with Path(self.cache_file).open("w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

        except (OSError, json.JSONEncodeError) as e:
            msg = f"キャッシュ保存エラー: {e}"
            raise OSError(msg) from e

    def get_cached_terms(self) -> ProperNounCollection:
        """キャッシュされた固有名詞コレクションを取得

        Returns:
            ProperNounCollection: キャッシュされたコレクション
                                 キャッシュが存在しない場合は空のコレクション
        """
        if not self.cache_file.exists():
            return ProperNounCollection(set())

        try:
            with Path(self.cache_file).open(encoding="utf-8") as f:
                cache_data: dict[str, Any] = json.load(f)

            # データ構造の検証
            if not isinstance(cache_data, dict) or "terms" not in cache_data:
                return ProperNounCollection(set())

            terms = cache_data.get("terms", [])
            if not isinstance(terms, list):
                return ProperNounCollection(set())

            # 文字列のリストからセットに変換
            term_set = {term for term in terms if isinstance(term, str)}
            return ProperNounCollection(term_set)

        except (OSError, json.JSONDecodeError):
            # エラーの場合は空のコレクションを返す
            return ProperNounCollection(set())

    def clear_cache(self) -> None:
        """キャッシュをクリア

        Raises:
            IOError: クリアに失敗した場合
        """
        try:
            if self.cache_file.exists():
                os.remove(self.cache_file)
        except OSError as e:
            msg = f"キャッシュクリアエラー: {e}"
            raise OSError(msg) from e

    def is_cache_valid(self) -> bool:
        """キャッシュが有効かどうかの判定

        Returns:
            bool: キャッシュが有効な場合True
        """
        if not self.cache_file.exists():
            return False

        try:
            # ファイルサイズチェック
            if self.cache_file.stat().st_size == 0:
                return False

            # JSON構造チェック
            with Path(self.cache_file).open(encoding="utf-8") as f:
                cache_data: dict[str, Any] = json.load(f)

            # 必須フィールドの存在チェック
            required_fields = ["terms", "timestamp"]
            if not all(field in cache_data for field in required_fields):
                return False

            # データ型チェック
            if not isinstance(cache_data["terms"], list):
                return False

            return isinstance(cache_data["timestamp"], int | float)

        except (OSError, json.JSONDecodeError):
            return False

    def get_cache_timestamp(self) -> float:
        """キャッシュのタイムスタンプを取得

        Returns:
            float: UNIXタイムスタンプ(キャッシュが存在しない場合は0)
        """
        if not self.cache_file.exists():
            return 0.0

        try:
            with Path(self.cache_file).open(encoding="utf-8") as f:
                cache_data: dict[str, Any] = json.load(f)

            timestamp = cache_data.get("timestamp", 0)
            return float(timestamp) if isinstance(timestamp, int | float) else 0.0

        except (OSError, json.JSONDecodeError):
            return 0.0

    def get_cache_statistics(self) -> dict[str, Any]:
        """キャッシュ統計情報を取得

        Returns:
            Dict[str, Any]: 統計情報
        """
        if not self.cache_file.exists():
            return {
                "exists": False,
                "size": 0,
                "count": 0,
                "timestamp": 0.0,
                "age_seconds": 0.0,
                "valid": False,
            }

        try:
            file_stat = self.cache_file.stat()
            current_time = time.time()

            cache_data: dict[str, Any] = {}
            if self.is_cache_valid():
                with Path(self.cache_file).open(encoding="utf-8") as f:
                    cache_data: dict[str, Any] = json.load(f)

            cache_timestamp = cache_data.get("timestamp", file_stat.st_mtime)
            term_count = len(cache_data.get("terms", []))

            return {
                "exists": True,
                "size": file_stat.st_size,
                "count": term_count,
                "timestamp": cache_timestamp,
                "age_seconds": current_time - cache_timestamp,
                "valid": self.is_cache_valid(),
                "file_path": str(self.cache_file),
            }

        except OSError:
            return {
                "exists": False,
                "size": 0,
                "count": 0,
                "timestamp": 0.0,
                "age_seconds": 0.0,
                "valid": False,
                "error": "ファイルアクセスエラー",
            }
