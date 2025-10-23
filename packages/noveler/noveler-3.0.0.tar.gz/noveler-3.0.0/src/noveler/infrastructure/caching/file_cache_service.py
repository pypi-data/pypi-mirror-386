"""
ファイルキャッシュサービス

パフォーマンス最適化: 200+箇所の.glob()操作をキャッシュ化
- ファイル存在確認とパターンマッチングの高速化
- メモリ使用量の最適化
- DDD準拠の実装
"""

import re
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from importlib import resources
try:  # Python 3.11+
    from importlib.resources.abc import Traversable  # type: ignore[attr-defined]
except ModuleNotFoundError:  # Python 3.10 compatibility
    from importlib.abc import Traversable  # type: ignore[assignment]
from pathlib import Path

from noveler.domain.interfaces.logger_service import ILoggerService
from noveler.domain.value_objects.project_time import project_now
from noveler.infrastructure.logging.unified_logger import get_logger


A38_CONFIG_RELATIVE_PATH = Path("config") / "a38_path_settings.yaml"
DEFAULT_A38_MANUSCRIPT_PATTERN = "第{episode:03d}話_*.md"


def _find_a38_config_path() -> Path | Traversable | None:
    """A38設定ファイルを可能なロケーションから探索する"""

    searched: set[Path] = set()
    current_file = Path(__file__).resolve()

    for offset in (4, 3, 2):
        try:
            root_candidate = current_file.parents[offset]
        except IndexError:
            continue

        candidate = root_candidate / A38_CONFIG_RELATIVE_PATH
        if candidate in searched:
            continue
        searched.add(candidate)

        if candidate.exists():
            return candidate

    cwd_candidate = Path.cwd() / A38_CONFIG_RELATIVE_PATH
    if cwd_candidate not in searched and cwd_candidate.exists():
        return cwd_candidate

    try:
        package_candidate = resources.files("noveler").joinpath(
            "config", "a38_path_settings.yaml"
        )
    except (ImportError, AttributeError, ModuleNotFoundError):
        return None

    if package_candidate.is_file():
        return package_candidate

    return None

@dataclass
class FileCacheEntry:
    """ファイルキャッシュエントリ"""
    files: list[Path]
    last_modified: datetime
    pattern: str
    directory: Path
    ttl_seconds: int = 300  # 5分間有効

    def is_expired(self) -> bool:
        """キャッシュの有効期限切れ確認"""
        return project_now().datetime > self.last_modified + timedelta(seconds=self.ttl_seconds)

    def is_directory_modified(self) -> bool:
        """ディレクトリの変更確認"""
        if not self.directory.exists():
            return True

        # タイムゾーンを明示して比較の一貫性を担保
        directory_mtime = datetime.fromtimestamp(
            self.directory.stat().st_mtime, tz=timezone.utc
        )
        return directory_mtime > self.last_modified


class FileGlobCacheService:
    """ファイルグロビングキャッシュサービス

    DDD準拠:
    - Infrastructure層のサービス
    - ドメインロジックには依存しない純粋な技術的最適化
    """

    def __init__(self, logger: ILoggerService | None = None) -> None:
        self._cache: dict[str, FileCacheEntry] = {}
        self._cache_lock = threading.RLock()
        self._logger = logger or get_logger(__name__)
        self._hit_count = 0
        self._miss_count = 0

    def get_matching_files(
        self,
        directory: Path,
        pattern: str,
        ttl_seconds: int = 300,
        force_refresh: bool = False
    ) -> list[Path]:
        """パターンマッチングファイル取得（キャッシュ付き）

        Args:
            directory: 検索対象ディレクトリ
            pattern: globパターン
            ttl_seconds: キャッシュ有効時間（秒）
            force_refresh: 強制リフレッシュ

        Returns:
            マッチしたファイルのリスト
        """
        cache_key = f"{directory.absolute()}::{pattern}"

        with self._cache_lock:
            # キャッシュヒット確認
            if not force_refresh and cache_key in self._cache:
                entry = self._cache[cache_key]

                if not entry.is_expired() and not entry.is_directory_modified():
                    self._hit_count += 1
                    self._logger.debug(
                        "ファイルキャッシュヒット: %s (%d件)", pattern, len(entry.files)
                    )
                    return entry.files.copy()
                # 期限切れまたはディレクトリ変更により削除
                del self._cache[cache_key]

            # キャッシュミス: 実際のファイル検索を実行
            self._miss_count += 1
            files = self._perform_glob_search(directory, pattern)

            # キャッシュに保存
            self._cache[cache_key] = FileCacheEntry(
                files=files.copy(),
                last_modified=project_now().datetime,
                pattern=pattern,
                directory=directory,
                ttl_seconds=ttl_seconds
            )

            self._logger.debug(
                "ファイルキャッシュミス: %s (%d件)", pattern, len(files)
            )
            return files

    def _perform_glob_search(self, directory: Path, pattern: str) -> list[Path]:
        """実際のglob検索実行"""
        if not directory.exists():
            return []

        try:
            return list(directory.glob(pattern))
        except Exception:
            self._logger.exception("ファイル検索エラー %s/%s", directory, pattern)
            return []

    def invalidate_cache(self, directory: Path | None = None, pattern: str | None = None) -> int:
        """キャッシュの無効化

        Args:
            directory: 特定ディレクトリのキャッシュのみ無効化（Noneで全体）
            pattern: 特定パターンのキャッシュのみ無効化

        Returns:
            無効化されたエントリ数
        """
        with self._cache_lock:
            if directory is None and pattern is None:
                # 全キャッシュクリア
                count = len(self._cache)
                self._cache.clear()
                self._logger.info("ファイルキャッシュ全削除: %d件", count)
                return count

            # 条件付きクリア
            keys_to_remove = []
            for cache_key, entry in self._cache.items():
                should_remove = False

                if directory is not None:
                    cache_dir = Path(cache_key.split("::")[0])
                    if cache_dir == directory.absolute():
                        should_remove = True

                if pattern is not None and entry.pattern == pattern:
                    should_remove = True

                if should_remove:
                    keys_to_remove.append(cache_key)

            for key in keys_to_remove:
                del self._cache[key]

            count = len(keys_to_remove)
            self._logger.info("ファイルキャッシュ部分削除: %d件", count)
            return count

    def cleanup_expired_entries(self) -> int:
        """期限切れエントリのクリーンアップ"""
        with self._cache_lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired() or entry.is_directory_modified()
            ]

            for key in expired_keys:
                del self._cache[key]

            count = len(expired_keys)
            if count > 0:
                self._logger.debug("期限切れファイルキャッシュ削除: %d件", count)
            return count

    def get_cache_stats(self) -> dict[str, any]:
        """キャッシュ統計情報取得"""
        with self._cache_lock:
            total_requests = self._hit_count + self._miss_count
            hit_rate = (self._hit_count / total_requests * 100) if total_requests > 0 else 0

            return {
                "cache_entries": len(self._cache),
                "hit_count": self._hit_count,
                "miss_count": self._miss_count,
                "hit_rate_percent": round(hit_rate, 2),
                "total_requests": total_requests
            }

    def get_episode_file_cached(self, manuscript_dir: Path, episode_number: int) -> Path | None:
        """エピソードファイル取得（A38設定準拠）

        B20: A38設定から動的にパターンを取得（ハードコーディング禁止）
        互換性向上: ゼロ埋め/非ゼロ埋め双方をサポート
        """
        # B20: A38設定からパターン取得
        pattern_template = self._get_manuscript_pattern_from_a38()

        # パターンをglob用に変換（{episode:03d} → 3桁ゼロ埋め）
        glob_pattern_padded = pattern_template.format(episode=episode_number)

        # まずゼロ埋めパターンで検索（優先）
        candidates = self.get_matching_files(
            manuscript_dir, glob_pattern_padded, ttl_seconds=600
        )

        if candidates:
            # ゼロ埋めパターンで見つかった場合、最初のものを返す
            return candidates[0]

        # フォールバック: 非ゼロ埋めパターンで再検索
        glob_pattern_no_pad = f"第{episode_number}話_*.md"
        candidates_no_pad = self.get_matching_files(
            manuscript_dir, glob_pattern_no_pad, ttl_seconds=600
        )

        if candidates_no_pad:
            return candidates_no_pad[0]

        # 見つからない場合はNone
        self._logger.warning(
            "エピソード%d の原稿ファイルが見つかりません（A38パターン: %s）",
            episode_number,
            pattern_template
        )
        return None

    def _get_manuscript_pattern_from_a38(self) -> str:
        """A38設定から原稿命名パターンを取得

        Returns:
            str: A38準拠のパターン（例: "第{episode:03d}話_*.md"）
        """
        try:
            import yaml
            config_path = _find_a38_config_path()

            if config_path is None:
                self._logger.warning(
                    "A38設定ファイルが見つかりません: %s（デフォルトパターンを使用）",
                    A38_CONFIG_RELATIVE_PATH,
                )
                return DEFAULT_A38_MANUSCRIPT_PATTERN

            config_data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
            pattern = config_data.get("naming_patterns", {}).get(
                "manuscript", DEFAULT_A38_MANUSCRIPT_PATTERN
            )

            self._logger.debug("A38設定から取得したパターン: %s (%s)", pattern, config_path)
            return pattern

        except Exception as e:
            self._logger.warning(
                "A38設定の読み込みに失敗: %s（デフォルトパターンを使用）",
                e
            )
            return DEFAULT_A38_MANUSCRIPT_PATTERN

    def reset_stats(self) -> None:
        """統計情報リセット"""
        self._hit_count = 0
        self._miss_count = 0
        # 上位のget_matching_filesにキャッシュ戦略を委譲


# グローバルインスタンス（シングルトンパターン）
_global_cache_service: FileGlobCacheService | None = None
_cache_lock = threading.Lock()


def get_file_cache_service() -> FileGlobCacheService:
    """ファイルキャッシュサービス取得（シングルトン）"""
    global _global_cache_service

    if _global_cache_service is None:
        with _cache_lock:
            if _global_cache_service is None:
                _global_cache_service = FileGlobCacheService()

    return _global_cache_service


# ---------------------------------------------------------------------------
# File content read cache (path + mtime_ns)
# ---------------------------------------------------------------------------

from dataclasses import dataclass as _dataclass_text  # local alias to avoid confusion

@_dataclass_text(frozen=True)
class _TextEntry:
    text: str
    mtime_ns: int
    size: int

_text_cache: dict[Path, _TextEntry] = {}
_text_lock = threading.RLock()


def read_text_cached(path: Path, encoding: str = "utf-8") -> str:
    """Fast-path text reader using a tiny in-memory cache keyed by mtime.

    Purpose:
        Reduce repeated disk I/O for frequently accessed manuscript/config
        files within a single process execution.

    Notes:
        - Cache key is the absolute path and its current ``stat().st_mtime_ns``.
        - If the file changed, the cache entry is transparently refreshed.
        - This cache is process-local and bounded by usage patterns; no TTL is
          required because mtime invalidates entries.
    """
    ap = path.absolute()
    try:
        st = ap.stat()
        mtime_ns = getattr(st, "st_mtime_ns", int(st.st_mtime * 1e9))
        size = st.st_size
    except FileNotFoundError:
        raise

    with _text_lock:
        entry = _text_cache.get(ap)
        if entry and entry.mtime_ns == mtime_ns and entry.size == size:
            return entry.text

    text = ap.read_text(encoding=encoding)

    with _text_lock:
        _text_cache[ap] = _TextEntry(text=text, mtime_ns=mtime_ns, size=size)
    return text


def invalidate_text_cache(path: Path | None = None) -> int:
    """Invalidate cached text entries.

    Args:
        path: Specific path to invalidate; None clears all entries.

    Returns:
        int: Number of removed entries.
    """
    with _text_lock:
        if path is None:
            n = len(_text_cache)
            _text_cache.clear()
            return n
        ap = path.absolute()
        return 1 if _text_cache.pop(ap, None) is not None else 0
