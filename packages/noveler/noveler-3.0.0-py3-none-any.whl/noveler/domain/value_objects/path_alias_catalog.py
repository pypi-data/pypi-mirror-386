"""Domain.value_objects.path_alias_catalog
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""ディレクトリエイリアスカタログ

PathServiceとCommonPathServiceで共有するディレクトリ名のエイリアス集合。
共通基盤で定義することで、ハードコーディングを防ぎ、旧構成との互換を確保する。
"""

from collections.abc import Iterable

from noveler.domain.value_objects.path_configuration import PathConfiguration

_DEFAULT_CONFIG = PathConfiguration()

_DIRECTORY_ALIAS_CATALOG: dict[str, dict[str, Iterable[str]]] = {
    "manuscript": {
        "primary": [_DEFAULT_CONFIG.manuscripts],
        "aliases": ["manuscripts", "manuscript", "原稿", "drafts"],
    },
    "management": {
        "primary": [_DEFAULT_CONFIG.management],
        "aliases": ["management", "management_docs", "管理資料"],
    },
    "settings": {
        "primary": [_DEFAULT_CONFIG.settings],
        "aliases": ["settings", "settings_collection", "設定集"],
    },
    "plots": {
        "primary": [_DEFAULT_CONFIG.plots],
        "aliases": ["plots", "plot", "プロット"],
    },
    "prompts": {
        "primary": [_DEFAULT_CONFIG.prompts],
        "aliases": ["prompts", "prompt", "プロンプト"],
    },
    "quality": {
        "primary": [_DEFAULT_CONFIG.quality],
        "aliases": ["quality", "quality_checks", "品質記録", "品質"],
    },
    "reports": {
        "primary": [_DEFAULT_CONFIG.reports],
        "aliases": ["reports", "report", "レポート"],
    },
    "backup": {
        "primary": [_DEFAULT_CONFIG.backup],
        "aliases": ["backup", "backups", "バックアップ"],
    },
}


def get_directory_aliases(directory_key: str) -> list[str]:
    """指定されたディレクトリのフォールバック候補名を取得"""
    entry = _DIRECTORY_ALIAS_CATALOG.get(directory_key)
    if not entry:
        return []

    seen: set[str] = set()
    ordered: list[str] = []

    for name in (*entry.get("primary", []), *entry.get("aliases", [])):
        if not name:
            continue
        normalized = str(name)
        if normalized not in seen:
            ordered.append(normalized)
            seen.add(normalized)
    return ordered
