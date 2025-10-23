"""固有名詞キャッシュシステム"""

import time
from pathlib import Path
from threading import Lock

from noveler.quality.proper_nouns_extractor import ProperNounsExtractor


class ProperNounsCache:
    """固有名詞のメモリキャッシュ"""

    def __init__(self, ttl: int = 3600) -> None:
        """Args:
        ttl: キャッシュの有効期限(秒)デフォルト1時間
        """
        self._cache: dict[str, set[str]] = {}
        self._timestamps: dict[str, float] = {}
        self._project_mtimes: dict[str, dict[str, float]] = {}
        self.ttl = ttl
        self._lock = Lock()
        self._extractor = ProperNounsExtractor()

    def get(self, project_root: str) -> set[str]:
        """プロジェクトの固有名詞を取得(キャッシュ優先)"""
        project_root = str(Path(project_root).resolve())

        with self._lock:
            # キャッシュチェック
            if self._is_cache_valid(project_root):
                return self._cache[project_root].copy()

            # キャッシュミスまたは期限切れ
            return self._load_and_cache(project_root)

    def _is_cache_valid(self, project_root: str) -> bool:
        """キャッシュが有効かチェック"""
        # キャッシュが存在しない
        if project_root not in self._cache:
            return False

        # TTLチェック
        if time.time() - self._timestamps[project_root] > self.ttl:
            return False

        # ファイル更新チェック
        return not self._has_files_changed(project_root)

    def _has_files_changed(self, project_root: str) -> bool:
        """設定ファイルが更新されたかチェック"""
        if project_root not in self._project_mtimes:
            return True

        settings_dir = Path(project_root) / "30_設定集"
        if not settings_dir.exists():
            return False

        # 監視対象ファイル
        yaml_files = [
            "世界観.yaml",
            "キャラクター.yaml",
            "魔法システム.yaml",
            "用語集.yaml",
        ]

        current_mtimes = {}
        for yaml_file in yaml_files:
            file_path = settings_dir / yaml_file
            if file_path.exists():
                current_mtimes[yaml_file] = file_path.stat().st_mtime

        # 更新チェック
        stored_mtimes = self._project_mtimes[project_root]
        return current_mtimes != stored_mtimes

    def _load_and_cache(self, project_root: str) -> set[str]:
        """固有名詞を抽出してキャッシュに保存"""
        # 固有名詞を抽出
        proper_nouns = self._extractor.extract_from_project(project_root)

        # キャッシュに保存
        self._cache[project_root] = proper_nouns
        self._timestamps[project_root] = time.time()

        # ファイル更新時刻を記録
        self._update_file_mtimes(project_root)

        return proper_nouns.copy()

    def _update_file_mtimes(self, project_root: str) -> None:
        """ファイル更新時刻を記録"""
        settings_dir = Path(project_root) / "30_設定集"
        if not settings_dir.exists():
            self._project_mtimes[project_root] = {}
            return

        yaml_files = [
            "世界観.yaml",
            "キャラクター.yaml",
            "魔法システム.yaml",
            "用語集.yaml",
        ]

        mtimes = {}
        for yaml_file in yaml_files:
            file_path = settings_dir / yaml_file
            if file_path.exists():
                mtimes[yaml_file] = file_path.stat().st_mtime

        self._project_mtimes[project_root] = mtimes

    def invalidate(self, project_root: str) -> None:
        """特定プロジェクトのキャッシュを無効化"""
        project_root = str(Path(project_root).resolve())

        with self._lock:
            self._cache.pop(project_root, None)
            self._timestamps.pop(project_root, None)
            self._project_mtimes.pop(project_root, None)

    def clear(self) -> None:
        """全てのキャッシュをクリア"""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
            self._project_mtimes.clear()

    def get_stats(self) -> dict[str, any]:
        """キャッシュ統計情報を取得"""
        with self._lock:
            total_terms = sum(len(terms) for terms in self._cache.values())

            return {
                "cached_projects": len(self._cache),
                "total_proper_nouns": total_terms,
                "ttl_seconds": self.ttl,
                "oldest_cache": min(self._timestamps.values()) if self._timestamps else None,
                "newest_cache": max(self._timestamps.values()) if self._timestamps else None,
            }
