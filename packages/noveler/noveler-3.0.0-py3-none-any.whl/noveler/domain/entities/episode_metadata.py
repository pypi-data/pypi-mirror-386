#!/usr/bin/env python3

"""Domain.entities.episode_metadata
Where: Domain entity holding metadata about episodes.
What: Stores identifiers, titles, and structural attributes.
Why: Keeps episode metadata consistent across services.
"""

from __future__ import annotations

"""エピソードメタデータ責務エンティティ

Phase 1 Week 3-4: Episode.py分割 - メタデータ責務の分離実装
責務: タグ・統計情報・付加的メタデータ管理 (25行実装)

仕様書: Episode_Split_Design_Specification.md
"""


from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from noveler.domain.value_objects.project_time import project_now

# DDD準拠: Domain層はInterface経由でLoggerを取得
# Infrastructure直接依存除去（Phase 4: 契約違反修正）

# Phase 6修正: 循環依存解消のため、Episodeの直接参照を除去
# if TYPE_CHECKING:
    #     from noveler.domain.entities.episode import Episode


"""エピソードメタデータエンティティ

Episode.pyから分離されたメタデータ管理の責務
DDD原則準拠・Infrastructure依存除去済み
"""


from noveler.domain.interfaces.logger_service import ILoggerService

if TYPE_CHECKING:
    from datetime import datetime


@dataclass
class EpisodeMetadata:
    """エピソードメタデータエンティティ（25行・単一責務）"""

    episode_id: str
    logger_service: ILoggerService
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: project_now().datetime)
    updated_at: datetime = field(default_factory=lambda: project_now().datetime)

    def add_tag(self, tag: str) -> None:
        """タグ追加"""
        if tag and tag not in self.tags:
            self.tags.append(tag)
            self._update_timestamp()
            self.logger_service.debug(f"タグ追加: {tag}")

    def remove_tag(self, tag: str) -> None:
        """タグ削除"""
        if tag in self.tags:
            self.tags.remove(tag)
            self._update_timestamp()
            self.logger_service.debug(f"タグ削除: {tag}")

    def set_metadata(self, key: str, value: Any) -> None:
        """メタデータ設定"""
        self.metadata[key] = value
        self._update_timestamp()

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """メタデータ取得"""
        return self.metadata.get(key, default)

    def _update_timestamp(self) -> None:
        """更新日時の更新"""
        self.updated_at = project_now().datetime

    # Phase 4修正: Infrastructure依存完全除去のため create_with_di() メソッドを削除
    # Application層のDomainEntityFactoryServiceで依存性注入を管理
