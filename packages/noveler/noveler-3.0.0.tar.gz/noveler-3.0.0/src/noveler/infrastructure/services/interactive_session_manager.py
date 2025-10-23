"""インタラクティブセッション管理サービス

インタラクティブ執筆セッションの永続化・キャッシュ・復旧を管理するサービス実装。
キャッシュとファイルシステムによる二重永続化でセッション安全性を確保します。
"""

import asyncio
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from noveler.application.interfaces.session_manager_interface import ISessionManager
from noveler.domain.entities.interactive_writing_session import (
    InteractiveWritingSession,
    SessionStatus,
)
from noveler.domain.value_objects.project_time import project_now
from noveler.infrastructure.cache.cache_service import CacheService
from noveler.infrastructure.factories.path_service_factory import create_path_service
from noveler.presentation.shared.shared_utilities import console


class InteractiveSessionManager(ISessionManager):
    """インタラクティブセッション管理サービス

    セッション管理の具体実装。キャッシュによる高速アクセスと
    ファイルシステムによる永続化を組み合わせて実装します。
    """

    def __init__(self, cache_service: CacheService, project_root: str) -> None:
        self.cache_service = cache_service
        self.console = console
        self.path_service = create_path_service(project_root)

        # セッション保存ディレクトリ
        self.session_dir = self.path_service.get_cache_dir() / "interactive_sessions"
        self.session_dir.mkdir(parents=True, exist_ok=True)

        # スナップショットディレクトリ
        self.snapshot_dir = self.session_dir / "snapshots"
        self.snapshot_dir.mkdir(exist_ok=True)

        # セッション設定
        self.default_ttl = 3600 * 24  # 24時間
        self.cleanup_interval = 3600 * 6  # 6時間ごとにクリーンアップ

        # バックグラウンドクリーンアップタスク開始（テスト時は無効化）
        self._cleanup_task: asyncio.Task | None = None
        if not os.environ.get("PYTEST_CURRENT_TEST") and not os.environ.get("NOVELER_DISABLE_BACKGROUND_TASKS"):
            try:
                self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            except RuntimeError:
                # イベントループ未初期化などの場合はスキップ
                self._cleanup_task = None

    async def __aenter__(self) -> "InteractiveSessionManager":
        """Async context support for graceful shutdown."""
        return self

    async def __aexit__(self, _exc_type, _exc, _tb) -> None:
        await self.close()

    async def close(self) -> None:
        """バックグラウンドタスクのクリーンアップ"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except Exception:
                pass

    def __del__(self) -> None:  # best-effort cleanup
        task = getattr(self, "_cleanup_task", None)
        if task and not task.done():
            try:
                task.cancel()
            except Exception:
                pass

    async def create_session(
        self,
        episode_number: int,
        project_root: str,
        configuration: dict[str, Any] | None = None
    ) -> InteractiveWritingSession:
        """新規セッション作成"""

        # セッションID生成（ユニークかつ推測困難）
        timestamp = int(project_now().datetime.timestamp())
        unique_id = str(uuid.uuid4())[:8]
        session_id = f"write_{episode_number}_{timestamp}_{unique_id}"

        # セッション作成
        session = InteractiveWritingSession(
            session_id=session_id,
            episode_number=episode_number,
            project_root=project_root,
            status=SessionStatus.INITIALIZING,
            current_step=0,
            created_at=project_now().datetime,
            updated_at=project_now().datetime,
            configuration=configuration or {}
        )

        # 初期保存
        await self.save_session(session)
        await self.create_session_snapshot(session_id)

        self.console.info(f"セッション {session_id} を作成しました")
        return session

    async def load_session(self, session_id: str) -> InteractiveWritingSession | None:
        """セッション読み込み"""

        # キャッシュから高速読み込み
        cached_session = await self.cache_service.get(f"session:{session_id}")
        if cached_session and isinstance(cached_session, InteractiveWritingSession):
            self.console.debug(f"セッション {session_id} をキャッシュから読み込み")
            return cached_session

        # ファイルシステムから読み込み
        session_file = self.session_dir / f"{session_id}.yaml"
        if not session_file.exists():
            self.console.debug(f"セッション {session_id} が見つかりません")
            return None

        try:
            with session_file.open(encoding="utf-8") as f:
                session_data = yaml.safe_load(f)

            session = InteractiveWritingSession.from_dict(session_data)

            # キャッシュに保存
            await self.cache_service.set(
                f"session:{session_id}",
                session,
                ttl=self.default_ttl
            )

            self.console.debug(f"セッション {session_id} をファイルから読み込み")
            return session

        except Exception as e:
            self.console.error(f"セッション {session_id} の読み込みに失敗: {e!s}")
            return None

    async def save_session(self, session: InteractiveWritingSession) -> None:
        """セッション保存"""

        session.updated_at = project_now().datetime

        try:
            # キャッシュ保存（高速アクセス用）
            await self.cache_service.set(
                f"session:{session.session_id}",
                session,
                ttl=self.default_ttl
            )

            # ファイル保存（永続化）
            session_file = self.session_dir / f"{session.session_id}.yaml"
            session_data = session.to_dict()

            with session_file.open("w", encoding="utf-8") as f:
                yaml.dump(session_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

            self.console.debug(f"セッション {session.session_id} を保存しました")

            # 重要な節目でスナップショット作成
            if self._should_create_snapshot(session):
                await self.create_session_snapshot(session.session_id)

        except Exception as e:
            self.console.error(f"セッション {session.session_id} の保存に失敗: {e!s}")
            raise

    async def delete_session(self, session_id: str) -> bool:
        """セッション削除"""

        try:
            # キャッシュから削除
            await self.cache_service.delete(f"session:{session_id}")

            # ファイル削除
            session_file = self.session_dir / f"{session_id}.yaml"
            if session_file.exists():
                session_file.unlink()

            # スナップショット削除
            snapshot_files = list(self.snapshot_dir.glob(f"{session_id}_*.yaml"))
            for snapshot_file in snapshot_files:
                snapshot_file.unlink()

            self.console.info(f"セッション {session_id} を削除しました")
            return True

        except Exception as e:
            self.console.error(f"セッション {session_id} の削除に失敗: {e!s}")
            return False

    async def list_sessions(
        self,
        episode_number: int | None = None,
        status_filter: str | None = None
    ) -> list[dict[str, Any]]:
        """セッション一覧取得"""

        sessions = []

        try:
            # セッションファイル一覧取得
            session_files = list(self.session_dir.glob("write_*.yaml"))

            for session_file in session_files:
                try:
                    with session_file.open(encoding="utf-8") as f:
                        session_data = yaml.safe_load(f)

                    # フィルタリング
                    if episode_number and session_data.get("episode_number") != episode_number:
                        continue

                    if status_filter and session_data.get("status") != status_filter:
                        continue

                    # 要約情報作成
                    session_summary = {
                        "session_id": session_data["session_id"],
                        "episode_number": session_data["episode_number"],
                        "status": session_data["status"],
                        "current_step": session_data["current_step"],
                        "created_at": session_data["created_at"],
                        "updated_at": session_data["updated_at"],
                        "completion_percentage": self._calculate_completion(session_data),
                        "feedback_count": len(session_data.get("feedback_history", [])),
                        "quality_score": self._get_latest_quality_score(session_data)
                    }

                    sessions.append(session_summary)

                except Exception as e:
                    self.console.warning(f"セッションファイル {session_file} の読み込みに失敗: {e!s}")
                    continue

            # 更新日時で降順ソート
            sessions.sort(key=lambda x: x["updated_at"], reverse=True)

        except Exception as e:
            self.console.error(f"セッション一覧取得に失敗: {e!s}")

        return sessions

    async def recover_session(self, session_id: str) -> InteractiveWritingSession | None:
        """セッション復旧"""

        self.console.info(f"セッション {session_id} の復旧を開始")

        # 通常の読み込みを試行
        session = await self.load_session(session_id)
        if session and session.status != SessionStatus.ERROR:
            return session

        # スナップショットからの復旧を試行
        snapshot_files = list(self.snapshot_dir.glob(f"{session_id}_*.yaml"))
        if not snapshot_files:
            self.console.warning(f"セッション {session_id} のスナップショットが見つかりません")
            return None

        # 最新のスナップショットを選択
        latest_snapshot = max(snapshot_files, key=lambda f: f.stat().st_mtime)

        try:
            session = await self.restore_from_snapshot(str(latest_snapshot))

            # 復旧後の状態調整
            if session.status == SessionStatus.ERROR:
                session.status = SessionStatus.IN_PROGRESS

            session.updated_at = project_now().datetime

            # 復旧されたセッションを保存
            await self.save_session(session)

            self.console.success(f"セッション {session_id} をスナップショットから復旧しました")
            return session

        except Exception as e:
            self.console.error(f"セッション {session_id} の復旧に失敗: {e!s}")
            return None

    async def cleanup_expired_sessions(self) -> int:
        """期限切れセッションのクリーンアップ"""

        expired_count = 0
        cutoff_time = project_now().datetime - timedelta(days=7)  # 7日以上古いセッション

        try:
            session_files = list(self.session_dir.glob("write_*.yaml"))

            for session_file in session_files:
                try:
                    # ファイル更新日時チェック
                    file_mtime = datetime.fromtimestamp(session_file.stat().st_mtime)
                    if file_mtime < cutoff_time:
                        # セッション内容確認
                        with session_file.open(encoding="utf-8") as f:
                            session_data = yaml.safe_load(f)

                        # 完了セッションまたは長期間更新されていないセッションを削除
                        status = session_data.get("status", "")
                        updated_at = datetime.fromisoformat(session_data.get("updated_at", ""))

                        if (status == "completed" or
                            (updated_at < cutoff_time and status in ["error", "paused"])):

                            session_id = session_data["session_id"]
                            if await self.delete_session(session_id):
                                expired_count += 1
                                self.console.debug(f"期限切れセッション {session_id} を削除")

                except Exception as e:
                    self.console.warning(f"セッションファイル {session_file} のクリーンアップ中にエラー: {e!s}")
                    continue

            if expired_count > 0:
                self.console.info(f"{expired_count} 件の期限切れセッションを削除しました")

        except Exception as e:
            self.console.error(f"セッションクリーンアップに失敗: {e!s}")

        return expired_count

    async def create_session_snapshot(self, session_id: str) -> str:
        """セッションスナップショット作成"""

        session = await self.load_session(session_id)
        if not session:
            msg = f"セッション {session_id} が見つかりません"
            raise ValueError(msg)

        # スナップショットファイル名（タイムスタンプ付き）
        timestamp = project_now().datetime.strftime("%Y%m%d_%H%M%S")
        snapshot_file = self.snapshot_dir / f"{session_id}_{timestamp}.yaml"

        # スナップショットデータ作成
        snapshot_data = {
            **session.to_dict(),
            "snapshot_created_at": project_now().datetime.isoformat(),
            "snapshot_version": "1.0"
        }

        with snapshot_file.open("w", encoding="utf-8") as f:
            yaml.dump(snapshot_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        self.console.debug(f"セッション {session_id} のスナップショットを作成: {snapshot_file}")
        return str(snapshot_file)

    async def restore_from_snapshot(self, snapshot_path: str) -> InteractiveWritingSession:
        """スナップショットから復元"""

        snapshot_file = Path(snapshot_path)
        if not snapshot_file.exists():
            msg = f"スナップショットファイルが見つかりません: {snapshot_path}"
            raise FileNotFoundError(msg)

        try:
            with snapshot_file.open(encoding="utf-8") as f:
                snapshot_data = yaml.safe_load(f)

            # スナップショット情報を除去
            session_data = {k: v for k, v in snapshot_data.items()
                           if not k.startswith("snapshot_")}

            session = InteractiveWritingSession.from_dict(session_data)

            self.console.info(f"スナップショットから復元: {snapshot_path}")
            return session

        except Exception as e:
            self.console.error(f"スナップショット復元に失敗: {e!s}")
            raise

    def _should_create_snapshot(self, session: InteractiveWritingSession) -> bool:
        """スナップショット作成が必要かどうか判定"""

        # 重要なステップ（原稿執筆、最終調整）でスナップショット作成
        snapshot_steps = [1, 5, 8, 10]
        if session.current_step in snapshot_steps:
            return True

        # セッション完了時
        if session.status == SessionStatus.COMPLETED:
            return True

        # エラー発生前の保護
        return session.status == SessionStatus.ERROR

    def _calculate_completion(self, session_data: dict[str, Any]) -> float:
        """完了率計算"""
        step_results = session_data.get("step_results", {})
        completed_steps = sum(
            1 for result in step_results.values()
            if result.get("status") == "completed"
        )
        return (completed_steps / 10) * 100

    def _get_latest_quality_score(self, session_data: dict[str, Any]) -> float | None:
        """最新品質スコア取得"""
        quality_history = session_data.get("quality_history", [])
        if quality_history:
            return quality_history[-1].get("overall_score", 0.0)
        return None

    async def _periodic_cleanup(self) -> None:
        """定期的なクリーンアップタスク

        キャンセル要求を受けたら速やかに終了する。
        """
        while True:
            try:
                # sleep中のキャンセルにも即応
                await asyncio.sleep(self.cleanup_interval)
                await self.cleanup_expired_sessions()
            except asyncio.CancelledError:
                # グレースフルシャットダウン
                break
            except Exception as e:
                self.console.error(f"定期クリーンアップでエラー: {e!s}")
                # エラーが発生してもタスクは継続
                continue
