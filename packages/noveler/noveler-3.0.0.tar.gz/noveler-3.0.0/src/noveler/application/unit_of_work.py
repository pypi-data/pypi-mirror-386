"""
Unit of Work 基底クラス - Domain Events対応拡張
SPEC-901-DDD-REFACTORING 対応

既存のIUnitOfWorkProtocolを拡張してDomain Events収集機能を追加
参照: goldensamples/ddd_patterns_golden_sample.py
"""
import abc
from typing import NoReturn

from noveler.domain.entities.base import AggregateRoot
from noveler.domain.events.base import DomainEvent
from noveler.domain.protocols.unit_of_work_protocol import IUnitOfWorkProtocol


class AbstractUnitOfWork(IUnitOfWorkProtocol, abc.ABC):
    """
    Unit of Work パターン抽象基底クラス - Domain Events収集機能付き

    特徴:
    - 既存のIUnitOfWorkProtocolを拡張
    - ドメインイベント自動収集
    - コンテキストマネージャー対応
    """

    def __init__(self) -> None:
        """Unit of Work初期化 - イベント管理機能追加"""
        super().__init__()
        self._events: list[DomainEvent] = []

    def __enter__(self) -> "AbstractUnitOfWork":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()

    def commit(self):
        """コミット実行"""
        self._commit()

    def add_event(self, event: DomainEvent) -> None:
        """ドメインイベント追加

        Args:
            event: 追加するドメインイベント
        """
        self._events.append(event)

    def collect_new_events(self) -> list[DomainEvent]:
        """
        新しいドメインイベント収集 - Message Bus との連携ポイント

        全てのリポジトリから集約ルートを取得し、
        蓄積されたドメインイベントを収集する
        """
        events = []

        # 手動追加されたイベントを収集
        events.extend(self._events)
        self._events.clear()  # イベントクリア

        # 各リポジトリから変更された集約を収集
        for repository in self._get_repositories():
            if hasattr(repository, "seen"):
                for aggregate in repository.seen:
                    if isinstance(aggregate, AggregateRoot):
                        events.extend(aggregate.collect_events())

        return events

    def _get_repositories(self):
        """リポジトリ一覧取得 - 具象クラスでオーバーライド可能"""
        repositories = []

        # Protocol定義からリポジトリを取得
        if hasattr(self, "episode_repository"):
            repositories.append(self.episode_repository)
        if hasattr(self, "project_repository"):
            repositories.append(self.project_repository)
        if hasattr(self, "character_repository") and self.character_repository:
            repositories.append(self.character_repository)
        if hasattr(self, "plot_repository") and self.plot_repository:
            repositories.append(self.plot_repository)
        if hasattr(self, "backup_repository") and self.backup_repository:
            repositories.append(self.backup_repository)
        if hasattr(self, "configuration_repository") and self.configuration_repository:
            repositories.append(self.configuration_repository)

        return repositories

    @abc.abstractmethod
    def _commit(self) -> NoReturn:
        """具象実装用コミット"""
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        """具象実装用ロールバック"""
        raise NotImplementedError


class InMemoryUnitOfWork(AbstractUnitOfWork):
    """テスト用の最小InMemory UoW実装

    SPEC-901 のMessage Busテストで使用されるシンプルなUoW。
    リポジトリは保持せず、イベント収集のみ提供する。
    """

    def _commit(self) -> None:  # type: ignore[override]
        # メモリ上のため特別なコミット処理は不要
        return None

    def rollback(self) -> None:  # type: ignore[override]
        # メモリ上のため特別なロールバック処理は不要
        return None
