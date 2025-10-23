"""Infrastructure.services.ddd_compliance_cache
Where: Infrastructure service caching DDD compliance results.
What: Stores compliance analysis outcomes for quick retrieval.
Why: Speeds up repeated compliance checks across development sessions.
"""

from noveler.presentation.shared.shared_utilities import console

"DDD準拠性チェック結果キャッシュシステム\n\n仕様書: SPEC-DDD-CACHE-001\nインクリメンタル分析による性能最適化\n\n設計原則:\n    - ファイル変更検出によるキャッシュ無効化\n- 違反結果のハッシュベース管理\n- 高速アクセスのための効率的データ構造\n"
import hashlib
import pickle
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from noveler.infrastructure.logging.unified_logger import get_logger


class ViolationSeverity(Enum):
    """違反重要度（循環依存解消）"""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class DDDViolation:
    """DDD違反情報（循環依存解消）"""

    file_path: str
    line_number: int
    violation_type: str
    severity: ViolationSeverity
    description: str
    recommendation: str
    rule_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FileAnalysisCache:
    """ファイル分析キャッシュエントリ"""

    file_path: str
    file_hash: str
    last_modified: datetime
    violations: list[DDDViolation]
    analysis_duration: float


@dataclass
class ProjectAnalysisCache:
    """プロジェクト全体キャッシュ"""

    project_root: str
    cache_version: str
    last_analysis: datetime
    file_caches: dict[str, FileAnalysisCache]
    global_violations: list[DDDViolation]


class DDDComplianceCacheManager:
    """DDD準拠性キャッシュ管理システム

    責務:
        - ファイル変更検出とキャッシュ管理
        - インクリメンタル分析による性能向上
        - キャッシュの整合性保証
    """

    def __init__(self, project_root: Path, cache_dir: Path | None = None) -> None:
        """初期化

        Args:
            project_root: プロジェクトルートパス
            cache_dir: キャッシュディレクトリ（デフォルト: .ddd_cache）
        """
        self.project_root = project_root
        self.cache_dir = cache_dir or project_root / ".ddd_cache"
        self.cache_file = self.cache_dir / "compliance_cache.pkl"
        self.logger = get_logger(__name__)
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            fallback_dir = Path.cwd() / ".ddd_cache"
            fallback_dir.mkdir(parents=True, exist_ok=True)
            self.cache_dir = fallback_dir
            self.cache_file = self.cache_dir / "compliance_cache.pkl"
        self.cache_version = "1.0.0"
        self.cache = self._load_cache()

    def _load_cache(self) -> ProjectAnalysisCache | None:
        """キャッシュファイルの読み込み

        Returns:
            プロジェクト分析キャッシュ（存在しない場合はNone）
        """
        if not self.cache_file.exists():
            return None
        try:
            with open(self.cache_file, "rb") as f:
                cache = pickle.load(f)
            if cache.cache_version != self.cache_version:
                console.print(f"キャッシュバージョン不整合: {cache.cache_version} -> {self.cache_version}")
                return None
            return cache
        except (FileNotFoundError, pickle.UnpicklingError, AttributeError) as e:
            console.print(f"キャッシュ読み込みエラー: {e}")
            self._handle_corrupted_cache()
            return None

    def _handle_corrupted_cache(self) -> None:
        """破損したキャッシュの処理"""
        try:
            if self.cache_file.exists():
                backup_file = self.cache_file.with_suffix(".pkl.corrupted")
                self.cache_file.rename(backup_file)
                console.print(f"破損キャッシュをバックアップ: {backup_file}")
        except OSError as e:
            self.logger.exception("破損キャッシュ処理エラー: %s", e)

    def _save_cache(self) -> None:
        """キャッシュファイルの保存"""
        try:
            with open(self.cache_file, "wb") as f:
                pickle.dump(self.cache, f)
            console.print(f"キャッシュ保存完了: {self.cache_file}")
        except (OSError, pickle.PicklingError) as e:
            self.logger.exception("キャッシュ保存エラー: %s", e)

    def _calculate_file_hash(self, file_path: Path) -> str:
        """ファイルハッシュの計算

        Args:
            file_path: ファイルパス

        Returns:
            SHA256ハッシュ文字列
        """
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            return hashlib.sha256(content).hexdigest()
        except (FileNotFoundError, OSError) as e:
            console.print(f"ファイルハッシュ計算エラー: {file_path} - {e}")
            return ""

    def is_file_cached(self, file_path: Path) -> bool:
        """ファイルがキャッシュされているかチェック

        Args:
            file_path: チェック対象ファイルパス

        Returns:
            キャッシュ存在フラグ
        """
        if not self.cache:
            return False
        file_key = str(file_path.relative_to(self.project_root))
        if file_key not in self.cache.file_caches:
            return False
        cached_entry = self.cache.file_caches[file_key]
        current_hash = self._calculate_file_hash(file_path)
        return cached_entry.file_hash == current_hash

    def get_cached_violations(self, file_path: Path) -> list[DDDViolation]:
        """キャッシュされた違反情報の取得

        Args:
            file_path: 対象ファイルパス

        Returns:
            違反リスト（キャッシュされていない場合は空リスト）
        """
        if not self.is_file_cached(file_path):
            return []
        file_key = str(file_path.relative_to(self.project_root))
        return self.cache.file_caches[file_key].violations

    def cache_file_analysis(self, file_path: Path, violations: list[DDDViolation], analysis_duration: float) -> None:
        """ファイル分析結果のキャッシュ

        Args:
            file_path: 分析済みファイルパス
            violations: 検出違反リスト
            analysis_duration: 分析所要時間
        """
        file_key = str(file_path.relative_to(self.project_root))
        file_hash = self._calculate_file_hash(file_path)
        cache_entry = FileAnalysisCache(
            file_path=file_key,
            file_hash=file_hash,
            last_modified=datetime.now(timezone.utc),
            violations=violations,
            analysis_duration=analysis_duration,
        )
        if not self.cache:
            self.cache = ProjectAnalysisCache(
                project_root=str(self.project_root),
                cache_version=self.cache_version,
                last_analysis=datetime.now(timezone.utc),
                file_caches={},
                global_violations=[],
            )
        self.cache.file_caches[file_key] = cache_entry
        self._save_cache()

    def get_changed_files(self, file_paths: list[Path]) -> list[Path]:
        """変更されたファイルのリストを取得

        Args:
            file_paths: チェック対象ファイルリスト

        Returns:
            変更されたファイルのリスト
        """
        changed_files = []
        for file_path in file_paths:
            if not self.is_file_cached(file_path):
                changed_files.append(file_path)
        return changed_files

    def get_cache_statistics(self) -> dict[str, Any]:
        """キャッシュ統計情報の取得

        Returns:
            キャッシュ統計情報
        """
        if not self.cache:
            return {"cache_exists": False, "cached_files": 0, "total_violations": 0, "cache_hit_rate": 0.0}
        total_violations = sum(len(entry.violations) for entry in self.cache.file_caches.values())
        return {
            "cache_exists": True,
            "cached_files": len(self.cache.file_caches),
            "total_violations": total_violations,
            "last_analysis": self.cache.last_analysis.isoformat(),
            "cache_version": self.cache.cache_version,
        }

    def clear_cache(self) -> None:
        """キャッシュの完全クリア"""
        if self.cache_file.exists():
            self.cache_file.unlink()
        self.cache = None
        console.print("DDD準拠性キャッシュをクリアしました")

    def cleanup_old_entries(self, max_age_days: int = 7) -> None:
        """古いキャッシュエントリのクリーンアップ

        Args:
            max_age_days: 保持期間（日数）
        """
        if not self.cache:
            return
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        files_to_remove = []
        for file_key, entry in self.cache.file_caches.items():
            if entry.last_modified < cutoff_date:
                files_to_remove.append(file_key)
        for file_key in files_to_remove:
            del self.cache.file_caches[file_key]
        if files_to_remove:
            console.print(f"古いキャッシュエントリを{len(files_to_remove)}件削除しました")
            self._save_cache()
