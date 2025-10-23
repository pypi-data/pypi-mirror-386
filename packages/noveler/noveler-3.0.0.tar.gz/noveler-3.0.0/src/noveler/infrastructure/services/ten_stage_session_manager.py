"""10段階執筆システム用セッションマネージャー（SPEC-MCP-001 v2.2.0対応）"""

import json
from pathlib import Path
from typing import Any

from noveler.domain.value_objects.project_time import project_now
from noveler.domain.value_objects.ten_stage_session_context import TenStageSessionContext
from noveler.domain.value_objects.ten_stage_writing_execution import TenStageExecutionStage
from noveler.infrastructure.factories.path_service_factory import create_path_service
from noveler.infrastructure.logging.unified_logger import get_logger


class TenStageSessionManager:
    """10段階執筆システム用のセッション管理"""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.path_service = create_path_service(project_root)
        self.logger = get_logger(__name__)

        # セッション保存ディレクトリ（50_管理資料配下に配置）
        self.sessions_dir = self.path_service.get_management_dir() / "ten_stage_sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        # 実行ログ保存ディレクトリ（共通基盤経由で取得）
        self.logs_dir = self.path_service.get_writing_logs_dir()

    def create_session(self, episode_number: int, **kwargs) -> TenStageSessionContext:
        """新規セッション作成"""
        context = TenStageSessionContext(episode_number=episode_number, **kwargs)

        # 初期段階設定
        context.current_stage = TenStageExecutionStage.PLOT_DATA_PREPARATION

        # セッション保存
        self.save_session(context)

        self.logger.info(f"10段階セッション作成: {context.session_id} (エピソード{episode_number})")
        return context

    def save_session(self, context: TenStageSessionContext) -> None:
        """セッション保存"""
        session_file = self.sessions_dir / f"{context.session_id}.json"

        try:
            with session_file.open("w", encoding="utf-8") as f:
                json.dump(context.to_dict(), f, ensure_ascii=False, indent=2)

            self.logger.debug(f"セッション保存完了: {session_file}")
        except Exception as e:
            self.logger.exception(f"セッション保存失敗: {session_file} - {e}")
            raise

    def load_session(self, session_id: str) -> TenStageSessionContext | None:
        """セッション読み込み"""
        session_file = self.sessions_dir / f"{session_id}.json"

        if not session_file.exists():
            self.logger.warning(f"セッションファイル未発見: {session_file}")
            return None

        try:
            with session_file.open("r", encoding="utf-8") as f:
                data = json.load(f)

            context = TenStageSessionContext.from_dict(data)
            self.logger.debug(f"セッション読み込み完了: {session_file}")
            return context

        except Exception as e:
            self.logger.exception(f"セッション読み込み失敗: {session_file} - {e}")
            return None

    def update_stage_completion(
        self,
        session_id: str,
        stage: TenStageExecutionStage,
        output_data: dict[str, Any],
        turns_used: int = 1,
        execution_time_ms: float = 0.0
    ) -> bool:
        """ステージ完了更新"""
        context = self.load_session(session_id)
        if not context:
            self.logger.error(f"セッション未発見: {session_id}")
            return False

        # ステージ完了マーク
        context.mark_stage_completed(stage, output_data)

        # パフォーマンス指標更新
        context.update_performance_metrics(turns_used, execution_time_ms)

        # 次のステージ設定
        next_stage = stage.get_next_stage()
        if next_stage:
            context.current_stage = next_stage
        else:
            context.current_stage = None  # 全完了

        # 保存
        self.save_session(context)

        self.logger.info(f"ステージ完了更新: {stage.display_name} (セッション: {session_id})")
        return True

    def get_session_status(self, session_id: str) -> dict[str, Any] | None:
        """セッション状況取得"""
        context = self.load_session(session_id)
        if not context:
            return None

        completed_count, total_count = context.get_completion_progress()

        return {
            "session_id": context.session_id,
            "episode_number": context.episode_number,
            "current_stage": context.current_stage.display_name if context.current_stage else "完了",
            "current_stage_number": context.current_stage.step_number if context.current_stage else 10,
            "progress": {
                "completed": completed_count,
                "total": total_count,
                "percentage": (completed_count / total_count) * 100,
            },
            "performance": {
                "total_turns_used": context.total_turns_used,
                "total_execution_time_ms": context.total_execution_time_ms,
            },
            "is_completed": context.is_all_completed(),
        }

    def get_active_sessions(self) -> list[dict[str, Any]]:
        """アクティブセッション一覧取得"""
        active_sessions = []

        for session_file in self.sessions_dir.glob("*.json"):
            session_id = session_file.stem
            status = self.get_session_status(session_id)

            if status and not status["is_completed"]:
                active_sessions.append(status)

        # 作成日時順でソート
        active_sessions.sort(key=lambda x: x.get("session_id"), reverse=True)
        return active_sessions

    def cleanup_old_sessions(self, keep_recent_count: int = 10) -> int:
        """古いセッションのクリーンアップ"""
        session_files = sorted(
            self.sessions_dir.glob("*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )

        if len(session_files) <= keep_recent_count:
            return 0

        files_to_remove = session_files[keep_recent_count:]
        removed_count = 0

        for file in files_to_remove:
            try:
                file.unlink()
                removed_count += 1
                self.logger.debug(f"古いセッションファイル削除: {file}")
            except Exception as e:
                self.logger.warning(f"セッションファイル削除失敗: {file} - {e}")

        self.logger.info(f"古いセッション {removed_count} 件をクリーンアップ")
        return removed_count

    def save_execution_log(
        self,
        episode_number: int,
        step_number: int,
        step_name: str,
        execution_data: dict[str, Any],
        timestamp: str | None = None
    ) -> Path:
        """実行ログを保存（episode000_step01形式）

        Args:
            episode_number: エピソード番号
            step_number: ステップ番号（1-10）
            step_name: ステップ名
            execution_data: 実行データ
            timestamp: タイムスタンプ（Noneの場合は自動生成）

        Returns:
            保存されたログファイルのパス
        """
        if timestamp is None:
            timestamp = project_now().datetime.strftime("%Y%m%d_%H%M%S")

        # ファイル名: episode000_step01_20250903_143000.json
        filename = f"episode{episode_number:03d}_step{step_number:02d}_{timestamp}.json"
        log_file = self.logs_dir / filename

        log_data = {
            "episode_number": episode_number,
            "step_number": step_number,
            "step_name": step_name,
            "timestamp": timestamp,
            "execution_data": execution_data
        }

        try:
            with log_file.open("w", encoding="utf-8") as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"実行ログ保存: {log_file}")
            return log_file

        except Exception as e:
            self.logger.exception(f"実行ログ保存失敗: {log_file} - {e}")
            raise

    def get_execution_logs(self, episode_number: int | None = None) -> list[dict[str, Any]]:
        """実行ログ一覧を取得

        Args:
            episode_number: エピソード番号（Noneの場合は全エピソード）

        Returns:
            実行ログ一覧（時系列順）
        """
        logs = []

        pattern = f"episode{episode_number:03d}_*.json" if episode_number else "episode*_step*.json"

        for log_file in sorted(self.logs_dir.glob(pattern)):
            try:
                with log_file.open("r", encoding="utf-8") as f:
                    log_data = json.load(f)
                    logs.append({
                        "file_path": str(log_file),
                        "file_name": log_file.name,
                        **log_data
                    })
            except Exception as e:
                self.logger.warning(f"ログファイル読み込みエラー: {log_file} - {e}")

        return logs
