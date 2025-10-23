#!/usr/bin/env python3

"""Domain.entities.quality_record
Where: Domain entity storing quality record aggregates.
What: Captures quality metrics, history, and annotations.
Why: Provides a source of truth for quality tracking.
"""

from __future__ import annotations

"""品質記録ドメインエンティティ
記録の永続化とビジネスルールを管理
"""


from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from noveler.domain.exceptions import QualityRecordError
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.value_objects.quality_check_result import QualityCheckResult, QualityScore

if TYPE_CHECKING:
    from datetime import datetime

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


@dataclass
class QualityRecordEntry:
    """品質記録エントリ(イミュータブル)"""

    id: str
    quality_result: QualityCheckResult
    created_at: datetime
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.id:
            object.__setattr__(self, "id", str(uuid4()))

    @classmethod
    def create_from_result(
        cls, result: QualityCheckResult, metadata: dict[str, Any] | None = None
    ) -> QualityRecordEntry:
        """品質チェック結果からエントリを作成"""
        return cls(id=str(uuid4()), quality_result=result, created_at=project_now().datetime, metadata=metadata or {})


class QualityRecord:
    """品質記録ドメインエンティティ(アグリゲートルート)"""

    def __init__(self, project_name: str, entries: list[QualityRecordEntry] | None = None) -> None:
        self._project_name = self._validate_project_name(project_name)
        self._entries: list[QualityRecordEntry] = list(entries) if entries else []
        self._last_updated = project_now().datetime

        # ドメインイベント記録
        self._domain_events: list[Any] = []

    @staticmethod
    def _validate_project_name(project_name: str) -> str:
        """プロジェクト名の妥当性チェック"""
        if not project_name or not project_name.strip():
            msg = "Project name cannot be empty"
            raise QualityRecordError(None, msg)
        return project_name.strip()

    @property
    def project_name(self) -> str:
        """プロジェクト名を取得する。

        Returns:
            str: プロジェクト名
        """
        return self._project_name

    @property
    def last_updated(self) -> datetime:
        """最終更新日時を取得する。

        Returns:
            datetime: 最終更新日時
        """
        return self._last_updated

    @property
    def entries(self) -> list[QualityRecordEntry]:
        """記録エントリのコピーを返す(不変性保証)"""
        return list(self._entries)

    @property
    def entry_count(self) -> int:
        """記録エントリ数"""
        return len(self._entries)

    def add_quality_check_result(self, result: QualityCheckResult, metadata: dict[str, Any] | None = None) -> str:
        """品質チェック結果を追加"""
        # ビジネスルール: 同じエピソード・同じ時刻の重複チェック防止
        if self._has_duplicate_entry(result):
            msg = f"Duplicate quality check for episode {result.episode_number} at {result.timestamp}"
            raise QualityRecordError(None, msg)

        entry = QualityRecordEntry.create_from_result(result, metadata)
        self._entries.append(entry)
        now = project_now().datetime
        self._last_updated = now

        # ドメインイベント発行
        overall_score = entry.quality_result.overall_score.to_float()
        self._domain_events.append(
            {
                "type": "QualityCheckAdded",
                "entry_id": entry.id,
                "episode_number": entry.quality_result.episode_number,
                "score": overall_score,
                "timestamp": now,
            }
        )

        return entry.id

    def _has_duplicate_entry(self, result: QualityCheckResult) -> bool:
        """重複エントリチェック"""
        for entry in self._entries:
            if (
                entry.quality_result.episode_number == result.episode_number
                and abs((entry.quality_result.timestamp - result.timestamp).total_seconds()) < 60
            ):
                return True
        return False

    def get_latest_for_episode(self, episode_number: int) -> QualityRecordEntry | None:
        """指定エピソードの最新記録を取得"""
        episode_entries = [e for e in self._entries if e.quality_result.episode_number == episode_number]
        if not episode_entries:
            return None

        return max(episode_entries, key=lambda e: e.created_at)

    def get_quality_trend(self, episode_number: int, limit: int | None = None) -> list[QualityScore]:
        """品質スコアのトレンドを取得"""
        episode_entries = [e for e in self._entries if e.quality_result.episode_number == episode_number]

        # 時系列順でソート
        sorted_entries = sorted(episode_entries, key=lambda e: e.created_at)

        # 指定件数に制限
        if limit is not None and limit > 0:
            recent_entries = sorted_entries[-limit:]
        else:
            recent_entries = sorted_entries

        return [entry.quality_result.overall_score for entry in recent_entries]

    def calculate_average_score(self) -> QualityScore | None:
        """全エピソードの平均品質スコア"""
        if not self._entries:
            return None

        total_score = sum(entry.quality_result.overall_score.value for entry in self._entries)
        average = total_score / len(self._entries)
        return QualityScore(average)

    def get_episodes_below_threshold(self, threshold: QualityScore | None = None) -> list[int]:
        """閾値以下の品質スコアのエピソード一覧"""
        effective_threshold = threshold or QualityScore.from_float(80.0)

        low_quality_episodes = set()
        for entry in self._entries:
            if entry.quality_result.overall_score.value < effective_threshold.value:
                low_quality_episodes.add(entry.quality_result.episode_number)

        return sorted(low_quality_episodes)

    def purge_old_entries(self, days_to_keep: int) -> int:
        """古い記録のパージ(保持期間制御)"""
        if days_to_keep <= 0:
            msg = "Days to keep must be positive"
            raise QualityRecordError(None, msg)

        now = datetime.now(JST)
        cutoff_date = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_to_keep)

        original_count = len(self._entries)
        self._entries = [e for e in self._entries if e.created_at >= cutoff_date]
        purged_count = original_count - len(self._entries)

        if purged_count > 0:
            self._last_updated = now
            self._domain_events.append(
                {"type": "OldEntriesPurged", "purged_count": purged_count, "timestamp": now}
            )

        return purged_count

    def get_domain_events(self) -> list[Any]:
        """ドメインイベント取得"""
        return list(self._domain_events)

    def clear_domain_events(self) -> None:
        """ドメインイベントクリア"""
        self._domain_events.clear()

    def to_persistence_dict(self) -> dict[str, Any]:
        """永続化用辞書変換"""
        return {
            "metadata": {
                "project_name": self._project_name,
                "last_updated": self._last_updated.isoformat(),
                "entry_count": len(self._entries),
            },
            "quality_checks": [
                {
                    "id": entry.id,
                    "episode_number": entry.quality_result.episode_number,
                    "timestamp": entry.quality_result.timestamp.isoformat(),
                    "checker_version": entry.quality_result.checker_version,
                    "results": entry.quality_result.to_summary_dict(),
                    "created_at": entry.created_at.isoformat(),
                    "metadata": entry.metadata,
                }
                for entry in self._entries
            ],
        }
