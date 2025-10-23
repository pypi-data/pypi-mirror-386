"""Infrastructure.services.codemap_async_service
Where: Infrastructure service orchestrating asynchronous codemap operations.
What: Manages asynchronous codemap refreshes and broadcasts updates.
Why: Keeps codemap data current without blocking user workflows.
"""

from noveler.presentation.shared.shared_utilities import console


"CODEMAP非同期処理サービス\n\nPhase 3: AsyncIO統合による非同期I/O最適化\nファイル読み込みやネットワーク通信の非同期化。\n\n設計原則:\n    - 非同期ファイルI/O\n    - コルーチンベースの並行処理\n    - イベント駆動アーキテクチャ\n"
import asyncio
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiofiles
import yaml

from noveler.infrastructure.logging.unified_logger import get_logger
import importlib


@dataclass
class AsyncLoadResult:
    """非同期読み込み結果"""

    section: str
    data: dict[str, Any]
    load_time: float
    cached: bool = False


class CodeMapAsyncService:
    """CODEMAP非同期処理サービス

    責務:
        - 非同期ファイル読み込み
        - 並行セクション読み込み
        - リアルタイム更新通知
        - WebSocket統合準備
    """

    def __init__(self, project_root: Path) -> None:
        """初期化

        Args:
            project_root: プロジェクトルート
        """
        self.project_root = project_root
        self.logger = get_logger(__name__)
        self._cache: dict[str, AsyncLoadResult] = {}
        self._subscribers: list[asyncio.Queue] = []
        self._lock = asyncio.Lock()

    async def load_async(self, sections: list[str] | None = None, parallel: bool = True) -> dict[str, Any]:
        """非同期でCODEMAPを読み込む

        Args:
            sections: 読み込むセクションリスト（Noneの場合は全て）
            parallel: 並行読み込みを行うか

        Returns:
            統合された読み込み結果
        """
        start_time = time.time()
        if sections is None:
            sections = ["core", "violations", "stats"]
        if parallel:
            results: Any = await self._load_sections_parallel(sections)
        else:
            results: Any = await self._load_sections_sequential(sections)
        merged_data: dict[str, Any] = self._merge_async_results(results)
        load_time = time.time() - start_time
        console.print(f"Async load completed: {len(sections)} sections in {load_time:.3f}s")
        await self._notify_subscribers({"event": "load_complete", "sections": sections, "load_time": load_time})
        return merged_data

    async def _load_sections_parallel(self, sections: list[str]) -> list[AsyncLoadResult]:
        """セクションを並行で読み込む"""
        tasks = [self._load_section_async(section) for section in sections]
        results: Any = await asyncio.gather(*tasks, return_exceptions=True)
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                console.print(f"Failed to load section {sections[i]}: {result}")
                valid_results.append(AsyncLoadResult(section=sections[i], data={}, load_time=0.0, cached=False))
            else:
                valid_results.append(result)
        return valid_results

    async def _load_sections_sequential(self, sections: list[str]) -> list[AsyncLoadResult]:
        """セクションを順次読み込む"""
        results: list[Any] = []
        for section in sections:
            try:
                result = await self._load_section_async(section)
                results.append(result)
            except Exception:
                self.logger.exception("Failed to load section %s", section)
                results.append(AsyncLoadResult(section=section, data={}, load_time=0.0, cached=False))
        return results

    async def _load_section_async(self, section: str) -> AsyncLoadResult:
        """特定セクションを非同期で読み込む"""
        start_time = time.time()
        async with self._lock:
            if section in self._cache:
                cached_result = self._cache[section]
                cached_result.cached = True
                return cached_result
        file_path = self._get_section_file_path(section)
        try:
            async with aiofiles.open(file_path, encoding="utf-8") as f:
                content = await f.read()
            data = await asyncio.to_thread(yaml.safe_load, content)
            load_time = time.time() - start_time
            result = AsyncLoadResult(section=section, data=data, load_time=load_time, cached=False)
            async with self._lock:
                self._cache[section] = result
            return result
        except FileNotFoundError:
            return await self._load_section_from_main(section)

    async def _load_section_from_main(self, section: str) -> AsyncLoadResult:
        """メインファイルから特定セクションを抽出"""
        start_time = time.time()
        main_file = self.project_root / "CODEMAP_dependencies.yaml"
        async with aiofiles.open(main_file, encoding="utf-8") as f:
            content = await f.read()
        full_data: dict[str, Any] = await asyncio.to_thread(yaml.safe_load, content)
        section_data: dict[str, Any] = self._extract_section(full_data, section)
        load_time = time.time() - start_time
        return AsyncLoadResult(section=section, data=section_data, load_time=load_time, cached=False)

    def _get_section_file_path(self, section: str) -> Path:
        """セクションに対応するファイルパスを取得"""
        if section == "core":
            return self.project_root / "CODEMAP_dependencies_core.yaml"
        if section == "violations":
            return self.project_root / "CODEMAP_dependencies_violations.yaml"
        if section == "stats":
            return self.project_root / "CODEMAP_dependencies_stats.yaml"
        return self.project_root / "CODEMAP_dependencies.yaml"

    def _extract_section(self, full_data: dict[str, Any], section: str) -> dict[str, Any]:
        """フルデータから特定セクションを抽出"""
        dependency_map = full_data.get("dependency_map", {})
        if section == "core":
            return {
                "dependency_map": {
                    "version": dependency_map.get("version"),
                    "core_dependencies": dependency_map.get("core_dependencies", {}),
                }
            }
        if section == "violations":
            return {
                "dependency_map": {
                    "version": dependency_map.get("version"),
                    "dependency_issues": dependency_map.get("dependency_issues", {}),
                }
            }
        if section == "stats":
            return {
                "dependency_map": {
                    "version": dependency_map.get("version"),
                    "dependency_statistics": dependency_map.get("dependency_statistics", {}),
                },
                "quality_metrics": full_data.get("quality_metrics", {}),
                "automation_config": full_data.get("automation_config", {}),
            }
        return full_data

    def _merge_async_results(self, results: list[AsyncLoadResult]) -> dict[str, Any]:
        """非同期結果を統合"""
        merged = {
            "dependency_map": {"version": "1.0.0", "generated_at": datetime.now(timezone.utc).isoformat()},
            "load_performance": {"total_load_time": 0.0, "sections_loaded": [], "cache_hits": 0},
        }
        for result in results:
            if result.data:
                for key, value in result.data.items():
                    if key == "dependency_map":
                        for sub_key, sub_value in value.items():
                            if sub_key not in ["version", "generated_at"]:
                                merged["dependency_map"][sub_key] = sub_value
                    else:
                        merged[key] = value
            merged["load_performance"]["total_load_time"] += result.load_time
            merged["load_performance"]["sections_loaded"].append(result.section)
            if result.cached:
                merged["load_performance"]["cache_hits"] += 1
        return merged

    async def watch_changes(self, callback=None):
        """ファイル変更を監視（WebSocket統合準備）"""
        "\n        将来的なWebSocket実装のプレースホルダー\n        リアルタイムでCODEMAP更新を通知\n        "
        console.print("File watching started (placeholder for WebSocket integration)")
        queue = asyncio.Queue()
        self._subscribers.append(queue)
        try:
            while True:
                event = await queue.get()
                if callback:
                    await callback(event)
                if event.get("type") == "stop":
                    break
        finally:
            self._subscribers.remove(queue)

    async def _notify_subscribers(self, event: dict[str, Any]) -> None:
        """購読者にイベントを通知"""
        for queue in self._subscribers:
            await queue.put(event)

    async def invalidate_cache(self, sections: list[str] | None = None):
        """キャッシュを無効化"""
        async with self._lock:
            if sections:
                for section in sections:
                    self._cache.pop(section, None)
            else:
                self._cache.clear()
        await self._notify_subscribers({"event": "cache_invalidated", "sections": sections or "all"})

    async def get_cache_status(self) -> dict[str, Any]:
        """キャッシュ状態を取得"""
        async with self._lock:
            return {
                "cached_sections": list(self._cache.keys()),
                "cache_size": len(self._cache),
                "cache_entries": {
                    section: {"load_time": result.load_time, "cached": result.cached}
                    for (section, result) in self._cache.items()
                },
            }


async def load_codemap_async(sections: list[str] | None = None, parallel: bool = True) -> dict[str, Any]:
    """CODEMAPを非同期で読み込む便利関数"""
    try:
        # Intentional lazy import to avoid hard dependency at module import time
        _ps = importlib.import_module('noveler.presentation.shared.shared_utilities')
        get_common_path_service = getattr(_ps, 'get_common_path_service')
        path_service = get_common_path_service()
        project_root = path_service.get_project_root()
    except ImportError:
        project_root = Path(os.environ.get("PROJECT_ROOT", Path.cwd()))
    service = CodeMapAsyncService(project_root)
    return await service.load_async(sections, parallel)
