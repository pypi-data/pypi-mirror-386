"""
集約ルート基底クラス
SPEC-901-DDD-REFACTORING 対応

参照: goldensamples/ddd_patterns_golden_sample.py
"""
from abc import ABC

from noveler.domain.events.base import DomainEvent


class AggregateRoot(ABC):
    """
    集約ルート基底クラス - ドメインイベント管理機能付き

    特徴:
    - ドメインイベントの自動収集
    - バージョン管理（楽観的ロック用）
    - 整合性境界の明確化
    """

    def __init__(self) -> None:
        self._events: list[DomainEvent] = []
        self._version: int = 0

    @property
    def version(self) -> int:
        """現在のバージョン取得"""
        return self._version

    def add_event(self, event: DomainEvent) -> None:
        """ドメインイベント追加"""
        self._events.append(event)

    def collect_events(self) -> list[DomainEvent]:
        """イベント収集（クリア付き）"""
        events = self._events.copy()
        self._events.clear()
        return events

    def clear_events(self) -> None:
        """イベントリストクリア"""
        self._events.clear()

    def increment_version(self) -> None:
        """バージョン増加（楽観的ロック用）"""
        self._version += 1

    @property
    def events(self) -> list[DomainEvent]:
        """現在のイベントリスト取得（読み取り専用）"""
        return self._events.copy()
