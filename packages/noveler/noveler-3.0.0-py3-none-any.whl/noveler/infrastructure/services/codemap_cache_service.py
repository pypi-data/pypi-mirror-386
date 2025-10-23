"""Infrastructure.services.codemap_cache_service
Where: Infrastructure service handling codemap caching.
What: Stores and invalidates codemap data in cache to optimise performance.
Why: Improves codemap access speed across the application.
"""

from noveler.presentation.shared.shared_utilities import console

"CODEMAPキャッシュサービス\n\nCODEMAP_dependencies.yamlの高速読み込みとキャッシュ管理を提供。\n大規模ファイル（134KB+）のパフォーマンス問題を解決。\n\n設計原則:\n    - ファイルハッシュベースの変更検出\n    - Pickleによる高速バイナリキャッシュ\n    - 部分読み込みサポート\n    - メモリ効率的なデータ構造\n"
import hashlib
import json
import os
import pickle
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

from noveler.infrastructure.logging.unified_logger import get_logger


@dataclass
class CodeMapCacheEntry:
    """CODEMAPキャッシュエントリ"""

    file_path: str
    file_hash: str
    last_modified: datetime
    data: dict[str, Any]
    section: str
    load_time: float

    def is_valid(self, current_hash: str) -> bool:
        """キャッシュの有効性を検証"""
        return self.file_hash == current_hash


@dataclass
class CodeMapIndex:
    """高速検索用インデックス"""

    module_locations: dict[str, int] = field(default_factory=dict)
    layer_modules: dict[str, set[str]] = field(default_factory=dict)
    high_coupling_modules: set[str] = field(default_factory=set)
    violation_modules: set[str] = field(default_factory=set)
    updated_at: datetime = field(default_factory=datetime.now)


class CodeMapCacheService:
    """CODEMAPキャッシュ管理サービス

    責務:
        - CODEMAP_dependencies.yamlの高速読み込み
        - 分割ファイル構造のサポート
        - インデックスベースの選択的読み込み
        - キャッシュの自動管理と無効化
    """

    CACHE_VERSION = "1.0.0"
    CACHE_DIR = ".codemap_cache"
    INDEX_FILE = "codemap.index.json"
    MAX_CACHE_AGE = timedelta(hours=24)

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.cache_dir = project_root / self.CACHE_DIR
        self.cache_dir.mkdir(exist_ok=True)
        self.logger = get_logger(__name__)
        self._cache: dict[str, CodeMapCacheEntry] = {}
        self._index: CodeMapIndex | None = None

    def load_dependencies(
        self, section: str = "full", use_cache: bool = True, force_reload: bool = False
    ) -> dict[str, Any]:
        """CODEMAP依存関係を読み込む

        Args:
            section: 読み込むセクション ('core', 'violations', 'stats', 'full')
            use_cache: キャッシュを使用するか
            force_reload: 強制的に再読み込みするか

        Returns:
            要求されたセクションのデータ
        """
        start_time = time.time()
        file_path = self._get_file_path(section)
        if use_cache and (not force_reload):
            cached_data: dict[str, Any] = self._load_from_cache(file_path, section)
            if cached_data:
                load_time = time.time() - start_time
                console.print(f"Loaded {section} from cache in {load_time:.3f}s")
                return cached_data
        data = self._load_from_file(file_path)
        if use_cache:
            self._save_to_cache(file_path, section, data)
        load_time = time.time() - start_time
        console.print(f"Loaded {section} from file in {load_time:.3f}s")
        return data

    def load_module_dependencies(self, module_name: str) -> dict[str, Any]:
        """特定モジュールの依存関係のみを読み込む

        Args:
            module_name: モジュール名（例: 'noveler.application.use_cases.xxx'）

        Returns:
            モジュールの依存関係情報
        """
        if not self._index:
            self._build_index()
        full_data: dict[str, Any] = self.load_dependencies(section="core")
        core_deps = full_data.get("core_dependencies", {})
        if module_name in core_deps:
            return {
                "module": module_name,
                "imports": core_deps[module_name].get("imports", []),
                "imported_by": core_deps[module_name].get("imported_by", []),
            }
        return {"module": module_name, "imports": [], "imported_by": []}

    def get_layer_modules(self, layer: str) -> list[str]:
        """特定レイヤーのモジュール一覧を取得

        Args:
            layer: レイヤー名 ('domain', 'application', 'infrastructure', 'presentation')

        Returns:
            モジュール名のリスト
        """
        if not self._index:
            self._build_index()
        return list(self._index.layer_modules.get(layer, set()))

    def get_violations(self) -> list[dict[str, str]]:
        """アーキテクチャ違反情報を取得"""
        data = self.load_dependencies(section="violations")
        return data.get("dependency_issues", {}).get("layer_violations", [])

    def get_statistics(self) -> dict[str, Any]:
        """統計情報を取得"""
        return self.load_dependencies(section="stats")

    def clear_cache(self) -> None:
        """キャッシュをクリア"""
        self._cache.clear()
        for cache_file in self.cache_dir.glob("*.pickle"):
            cache_file.unlink()
        console.print("Cache cleared")

    def _get_file_path(self, section: str) -> Path:
        """セクションに対応するファイルパスを取得"""
        base_path = self.project_root
        if section == "full":
            return base_path / "CODEMAP_dependencies.yaml"
        if section == "core":
            core_file = base_path / "CODEMAP_dependencies_core.yaml"
            if core_file.exists():
                return core_file
            return base_path / "CODEMAP_dependencies.yaml"
        if section == "violations":
            violations_file = base_path / "CODEMAP_dependencies_violations.yaml"
            if violations_file.exists():
                return violations_file
            return base_path / "CODEMAP_dependencies.yaml"
        if section == "stats":
            stats_file = base_path / "CODEMAP_dependencies_stats.yaml"
            if stats_file.exists():
                return stats_file
            return base_path / "CODEMAP_dependencies.yaml"
        return base_path / "CODEMAP_dependencies.yaml"

    def _calculate_file_hash(self, file_path: Path) -> str:
        """ファイルのハッシュ値を計算"""
        hasher = hashlib.sha256()
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _load_from_cache(self, file_path: Path, section: str) -> dict[str, Any] | None:
        """キャッシュから読み込み"""
        cache_key = f"{file_path.name}_{section}"
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            current_hash = self._calculate_file_hash(file_path)
            if entry.is_valid(current_hash):
                return entry.data
        cache_file = self.cache_dir / f"{cache_key}.pickle"
        if cache_file.exists():
            try:
                with cache_file.open("rb") as f:
                    entry = pickle.load(f)
                current_hash = self._calculate_file_hash(file_path)
                if entry.is_valid(current_hash):
                    self._cache[cache_key] = entry
                    return entry.data
            except Exception as e:
                console.print(f"Failed to load cache: {e}")
        return None

    def _load_from_file(self, file_path: Path) -> dict[str, Any]:
        """ファイルから読み込み"""
        with file_path.open(encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _save_to_cache(self, file_path: Path, section: str, data: dict[str, Any]) -> None:
        """キャッシュに保存"""
        cache_key = f"{file_path.name}_{section}"
        file_hash = self._calculate_file_hash(file_path)
        entry = CodeMapCacheEntry(
            file_path=str(file_path),
            file_hash=file_hash,
            last_modified=datetime.now(timezone.utc),
            data=data,
            section=section,
            load_time=0.0,
        )
        self._cache[cache_key] = entry
        cache_file = self.cache_dir / f"{cache_key}.pickle"
        try:
            with cache_file.open("wb") as f:
                pickle.dump(entry, f)
        except Exception as e:
            console.print(f"Failed to save cache: {e}")

    def _build_index(self) -> None:
        """インデックスを構築"""
        index_file = self.cache_dir / self.INDEX_FILE
        if index_file.exists():
            try:
                with index_file.open() as f:
                    index_data: dict[str, Any] = json.load(f)
                self._index = CodeMapIndex(
                    module_locations=index_data.get("module_locations", {}),
                    layer_modules={k: set(v) for (k, v) in index_data.get("layer_modules", {}).items()},
                    high_coupling_modules=set(index_data.get("high_coupling_modules", [])),
                    violation_modules=set(index_data.get("violation_modules", [])),
                    updated_at=datetime.fromisoformat(index_data.get("updated_at")),
                )
                return
            except Exception as e:
                console.print(f"Failed to load index: {e}")
        self._index = CodeMapIndex()
        data = self.load_dependencies(section="full", use_cache=False)
        core_deps = data.get("dependency_map", {}).get("core_dependencies", {})
        for module_name in core_deps:
            layer = self._get_layer(module_name)
            if layer:
                if layer not in self._index.layer_modules:
                    self._index.layer_modules[layer] = set()
                self._index.layer_modules[layer].add(module_name)
        violations: Any = data.get("dependency_map", {}).get("dependency_issues", {}).get("layer_violations", [])
        for violation in violations:
            self._index.violation_modules.add(violation.get("from", ""))
        self._save_index()

    def _get_layer(self, module_name: str) -> str | None:
        """モジュール名からレイヤーを判定"""
        if "domain" in module_name:
            return "domain"
        if "application" in module_name:
            return "application"
        if "infrastructure" in module_name:
            return "infrastructure"
        if "presentation" in module_name:
            return "presentation"
        return None

    def _save_index(self) -> None:
        """インデックスを保存"""
        if not self._index:
            return
        index_file = self.cache_dir / self.INDEX_FILE
        index_data: dict[str, Any] = {
            "module_locations": self._index.module_locations,
            "layer_modules": {k: list(v) for (k, v) in self._index.layer_modules.items()},
            "high_coupling_modules": list(self._index.high_coupling_modules),
            "violation_modules": list(self._index.violation_modules),
            "updated_at": self._index.updated_at.isoformat(),
        }
        try:
            with index_file.open("w") as f:
                json.dump(index_data, f, indent=2)
        except Exception as e:
            console.print(f"Failed to save index: {e}")


def get_codemap_cache_service() -> CodeMapCacheService:
    """CODEMAPキャッシュサービスのインスタンスを取得"""
    try:
        from noveler.presentation.shared.shared_utilities import get_test_path_service

        path_service = get_test_path_service()
        project_root = path_service.project_root
    except ImportError:
        project_root = Path(os.environ.get("PROJECT_ROOT", Path.cwd()))
    return CodeMapCacheService(project_root)
