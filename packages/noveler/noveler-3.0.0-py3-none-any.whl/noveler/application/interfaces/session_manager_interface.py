"""セッション管理インターフェース

インタラクティブ執筆セッションの管理を行うサービスインターフェースの定義。
DDD原則に従い、ドメイン層とインフラ層の依存関係を逆転させます。
"""

from abc import ABC, abstractmethod
from typing import Any

from noveler.domain.entities.interactive_writing_session import InteractiveWritingSession


class ISessionManager(ABC):
    """セッション管理インターフェース

    インタラクティブ執筆セッションの作成、保存、読み込み、復旧を管理します。
    インフラ層での具体的な実装（キャッシュ、ファイルシステム等）に依存しない
    抽象インターフェースを提供します。
    """

    @abstractmethod
    async def create_session(
        self,
        episode_number: int,
        project_root: str,
        configuration: dict[str, Any] | None = None
    ) -> InteractiveWritingSession:
        """新規セッション作成

        Args:
            episode_number: 執筆話数
            project_root: プロジェクトルートパス
            configuration: セッション設定（省略時はデフォルト）

        Returns:
            作成されたセッション
        """

    @abstractmethod
    async def load_session(self, session_id: str) -> InteractiveWritingSession | None:
        """セッション読み込み

        Args:
            session_id: セッションID

        Returns:
            セッション（存在しない場合はNone）
        """

    @abstractmethod
    async def save_session(self, session: InteractiveWritingSession) -> None:
        """セッション保存

        Args:
            session: 保存するセッション
        """

    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """セッション削除

        Args:
            session_id: セッションID

        Returns:
            削除成功時True、存在しない場合False
        """

    @abstractmethod
    async def list_sessions(
        self,
        episode_number: int | None = None,
        status_filter: str | None = None
    ) -> list[dict[str, Any]]:
        """セッション一覧取得

        Args:
            episode_number: 話数フィルター（省略時は全話数）
            status_filter: 状態フィルター（省略時は全状態）

        Returns:
            セッション要約のリスト
        """

    @abstractmethod
    async def recover_session(self, session_id: str) -> InteractiveWritingSession | None:
        """セッション復旧

        中断されたセッションやエラー状態のセッションを復旧します。

        Args:
            session_id: セッションID

        Returns:
            復旧されたセッション（復旧不可時はNone）
        """

    @abstractmethod
    async def cleanup_expired_sessions(self) -> int:
        """期限切れセッションのクリーンアップ

        Returns:
            削除されたセッション数
        """

    @abstractmethod
    async def create_session_snapshot(self, session_id: str) -> str:
        """セッションスナップショット作成

        復旧用のセッションスナップショットを作成します。

        Args:
            session_id: セッションID

        Returns:
            スナップショットファイルパス
        """

    @abstractmethod
    async def restore_from_snapshot(self, snapshot_path: str) -> InteractiveWritingSession:
        """スナップショットから復元

        Args:
            snapshot_path: スナップショットファイルパス

        Returns:
            復元されたセッション
        """
