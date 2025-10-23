#!/usr/bin/env python3

"""Domain.entities.episode_publisher
Where: Domain entity modelling episode publishing operations.
What: Tracks publishing parameters and history.
Why: Enables reproducible publishing workflows.
"""

from __future__ import annotations

"""エピソード公開責務エンティティ

Phase 1 Week 3-4: Episode.py分割 - 公開責務の分離実装
責務: エピソードの公開・レビュー・公開条件判定 (30行実装)

仕様書: Episode_Split_Design_Specification.md
"""


from dataclasses import dataclass

from noveler.domain.value_objects.project_time import project_now

# DDD準拠: Domain層はInterface経由でLoggerを取得
# Infrastructure直接依存除去（Phase 4: 契約違反修正）

# Phase 6修正: 完全な循環依存解消のため、全てのEpisode参照を除去
# if TYPE_CHECKING:
    #     from noveler.domain.entities.episode import Episode


"""エピソード公開エンティティ

Episode.pyから分離された公開・レビュー責務
DDD原則準拠・Infrastructure依存除去済み
"""

from dataclasses import field
from typing import TYPE_CHECKING

from noveler.domain.interfaces.logger_service import ILoggerService

if TYPE_CHECKING:
    from datetime import datetime

# Phase 6修正: 循環依存解消のため、Episodeの直接参照を除去
# if TYPE_CHECKING:
    #     from noveler.domain.entities.episode import Episode, EpisodeStatus


@dataclass
class PublishingResult:
    """公開結果"""

    success: bool
    message: str
    published_at: datetime | None = None


@dataclass
class EpisodePublisher:
    """エピソード公開エンティティ（30行・単一責務）"""

    episode_id: str
    logger_service: ILoggerService
    published_at: datetime | None = field(default=None)
    reviewed_at: datetime | None = field(default=None)

    def can_publish(self, episode_status: str, episode_content: str) -> bool:
        """公開可能か判定

        Phase 6修正: 循環依存解消のため、Episodeオブジェクトではなく必要なプロパティのみ受け取る
        """
        if episode_status != "reviewed":
            return False
        return episode_content.strip()

    def publish(self, episode_status: str, episode_content: str, episode_title: str) -> PublishingResult:
        """エピソード公開実行

        Phase 6修正: 循環依存解消のため、Episodeオブジェクトではなく必要なプロパティのみ受け取る
        """
        if not self.can_publish(episode_status, episode_content):
            return PublishingResult(success=False, message="公開条件を満たしていません")

        self.published_at = project_now().datetime
        self.logger_service.info(f"エピソード公開: {episode_title}")

        return PublishingResult(success=True, message="公開完了", published_at=self.published_at)

    def review(self, episode_title: str) -> bool:
        """レビュー完了設定

        Phase 6修正: 循環依存解消のため、Episodeオブジェクトではなく必要なプロパティのみ受け取る
        """
        self.reviewed_at = project_now().datetime
        self.logger_service.info(f"レビュー完了: {episode_title}")
        return True

    # Phase 4修正: Infrastructure依存完全除去のため create_with_di() メソッドを削除
    # Application層のDomainEntityFactoryServiceで依存性注入を管理
