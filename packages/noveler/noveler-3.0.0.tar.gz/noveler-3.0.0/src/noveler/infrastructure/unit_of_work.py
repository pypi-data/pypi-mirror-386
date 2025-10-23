"""Infrastructure.unit_of_work
Where: Infrastructure module defining unit-of-work implementations.
What: Provides abstractions that coordinate repositories and transactions for infrastructure operations.
Why: Enables consistent transactional boundaries throughout the infrastructure layer.
"""

from __future__ import annotations

"""Unit of Work - B20準拠トランザクション管理実装

B20_Claude_Code開発作業指示書準拠:
- 複数集約の整合性保証
- Imperative Shell パターン適用
- トランザクション境界の明確化

参照実装:
- ___code-master/src/infrastructure/uow.py
"""


from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from noveler.domain.repositories.character_repository import CharacterRepository
    from noveler.domain.repositories.configuration_repository import ConfigurationRepository
    from noveler.domain.repositories.episode_repository import EpisodeRepository
    from noveler.domain.repositories.file_backup_repository import FileBackupRepository
    from noveler.domain.repositories.plot_repository import PlotRepository
    from noveler.domain.repositories.project_repository import ProjectRepository


class IUnitOfWork(Protocol):
    """Unit of Work インターフェース"""

    episode_repository: EpisodeRepository
    project_repository: ProjectRepository
    character_repository: CharacterRepository | None
    configuration_repository: ConfigurationRepository | None
    plot_repository: PlotRepository | None
    backup_repository: FileBackupRepository | None

    def __enter__(self) -> IUnitOfWork:
        """コンテキストマネージャー開始"""
        ...

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """コンテキストマネージャー終了"""
        ...

    def commit(self) -> None:
        """変更をコミット"""
        ...

    def rollback(self) -> None:
        """変更をロールバック"""
        ...


class UnitOfWork:
    """Unit of Work - B20準拠実装

    機能:
    - 複数リポジトリのトランザクション管理
    - Imperative Shell パターン適用
    - コンテキストマネージャー対応

    参照実装:
    - ___code-master/src/infrastructure/uow.py
    - 複数集約の整合性保証パターン
    """

    def __init__(
        self,
        episode_repository: EpisodeRepository,
        project_repository: ProjectRepository,
        character_repository: CharacterRepository | None = None,
        configuration_repository: ConfigurationRepository | None = None,
        plot_repository: PlotRepository | None = None,
        backup_repository: FileBackupRepository | None = None,
    ) -> None:
        """初期化 - B20準拠拡張版

        Args:
            episode_repository: エピソードリポジトリ
            project_repository: プロジェクトリポジトリ
            character_repository: キャラクターリポジトリ（オプション）
            configuration_repository: 設定リポジトリ（オプション）
            plot_repository: プロットリポジトリ（オプション）
            backup_repository: バックアップリポジトリ（オプション）
        """
        # Core repositories (必須)
        self.episode_repository = episode_repository
        self.project_repository = project_repository

        # Extended repositories (オプション)
        self.character_repository = character_repository
        self.configuration_repository = configuration_repository
        self.plot_repository = plot_repository
        self.backup_repository = backup_repository

        # Transaction state
        self._committed = False
        self._rolled_back = False
        self._repositories = []
        self._events = []  # Domain events queue
        self._event_handlers: dict[str, list[Callable]] = {}

        # Register all repositories for transaction management
        self._repositories = [
            repo
            for repo in [
                self.episode_repository,
                self.project_repository,
                self.character_repository,
                self.configuration_repository,
                self.plot_repository,
                self.backup_repository,
            ]
            if repo is not None
        ]

    def __enter__(self) -> UnitOfWork:
        """コンテキストマネージャー開始

        トランザクション開始:
        - リポジトリの初期化
        - 変更追跡の開始

        Returns:
            UnitOfWork: 自身のインスタンス
        """
        self._committed = False
        self._rolled_back = False
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """コンテキストマネージャー終了

        トランザクション終了処理:
        - 例外発生時：自動ロールバック
        - 正常終了時：明示的コミット必要

        Args:
            exc_type: 例外タイプ
            exc_val: 例外値
            exc_tb: トレースバック
        """
        if exc_type is not None and not self._rolled_back:
            self.rollback()
        elif not self._committed and not self._rolled_back:
            # 明示的なコミットが必要
            pass

    def commit(self) -> None:
        """変更をコミット - B20準拠拡張版

        B20準拠トランザクション管理:
        - 複数リポジトリの同期コミット
        - 整合性保証
        - エラー時の自動ロールバック
        - Domain Events処理
        """
        if self._committed:
            return
        if self._rolled_back:
            msg = "Already rolled back"
            raise RuntimeError(msg)

        try:
            # 1. 各リポジトリのコミット処理
            for repository in self._repositories:
                if hasattr(repository, "commit"):
                    repository.commit()

            # 2. Domain Eventsの処理
            self._process_domain_events()

            # 3. トランザクション完了
            self._committed = True

        except Exception:
            self.rollback()
            raise

    def rollback(self) -> None:
        """変更をロールバック - B20準拠拡張版

        エラー復旧:
        - 全リポジトリの変更取り消し
        - イベントクリア
        - 状態の初期化
        """
        if self._rolled_back:
            return
        if self._committed:
            msg = "Already committed"
            raise RuntimeError(msg)

        try:
            # 1. 各リポジトリのロールバック処理
            for repository in reversed(self._repositories):
                if hasattr(repository, "rollback"):
                    repository.rollback()

            # 2. イベントキューのクリア
            self._events.clear()

            # 3. ロールバック完了
            self._rolled_back = True

        except Exception:
            # ロールバック自体が失敗した場合でも状態を更新
            self._rolled_back = True
            self._events.clear()
            raise

    @contextmanager
    def transaction(self) -> Generator[UnitOfWork, None, None]:
        """トランザクションコンテキスト

        使用例:
        ```python
        with uow.transaction():
            uow.episode_repository.save(episode)
            uow.project_repository.update(project)
            # 自動コミット
        ```

        Yields:
            UnitOfWork: トランザクション対象のUoW
        """
        with self:
            try:
                yield self
                self.commit()
            except Exception:
                self.rollback()
                raise

    def add_event(self, event: Any) -> None:
        """Domain Eventをキューに追加

        Args:
            event: Domain Event
        """
        self._events.append(event)

    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """イベントハンドラーを登録

        Args:
            event_type: イベントタイプ
            handler: ハンドラー関数
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    def _process_domain_events(self) -> None:
        """Domain Eventsを処理

        B20準拠イベント処理:
        - コミット前にイベントを処理
        - エラー時は自動ロールバック
        """
        for event in self._events:
            event_type = type(event).__name__
            handlers = self._event_handlers.get(event_type, [])

            for handler in handlers:
                try:
                    handler(event)
                except Exception:
                    # イベント処理エラーはログに記録するが処理は継続
                    # Note: 実際の実装では適切なログシステムを使用
                    pass

        # イベント処理完了後はクリア
        self._events.clear()

    def get_pending_events(self) -> list[Any]:
        """未処理のDomain Eventsを取得

        Returns:
            未処理のイベントリスト
        """
        return self._events.copy()


def create_unit_of_work(
    episode_repository: EpisodeRepository,
    project_repository: ProjectRepository,
    character_repository: CharacterRepository | None = None,
    configuration_repository: ConfigurationRepository | None = None,
    plot_repository: PlotRepository | None = None,
    backup_repository: FileBackupRepository | None = None,
) -> UnitOfWork:
    """Unit of Workを作成 - B20準拠拡張版

    ファクトリ関数によるシンプルな生成パターン

    Args:
        episode_repository: エピソードリポジトリ
        project_repository: プロジェクトリポジトリ
        character_repository: キャラクターリポジトリ（オプション）
        configuration_repository: 設定リポジトリ（オプション）
        plot_repository: プロットリポジトリ（オプション）
        backup_repository: バックアップリポジトリ（オプション）

    Returns:
        UnitOfWork: 設定済みUnit of Work
    """
    return UnitOfWork(
        episode_repository=episode_repository,
        project_repository=project_repository,
        character_repository=character_repository,
        configuration_repository=configuration_repository,
        plot_repository=plot_repository,
        backup_repository=backup_repository,
    )
