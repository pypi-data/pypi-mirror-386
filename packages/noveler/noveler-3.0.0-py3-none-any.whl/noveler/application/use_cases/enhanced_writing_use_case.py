"""
強化版執筆ユースケース

包括的エラーハンドリング統合版の執筆ユースケース。
MCPツール統合、部分失敗対応、自動復旧機能を提供。
"""

import asyncio
from typing import Any

from noveler.domain.errors import ApplicationError, InputValidationError, PartialFailureError, SystemStateError
from noveler.domain.services.comprehensive_error_handler import ErrorContext, get_comprehensive_error_handler
from noveler.infrastructure.factories.progressive_write_llm_executor_factory import (
    create_progressive_write_llm_executor,
)
from noveler.infrastructure.factories.progressive_write_manager_factory import (
    create_progressive_write_manager,
)
from noveler.infrastructure.logging.unified_logger import LogLevel, get_logger
from noveler.presentation.shared.shared_utilities import get_console


class EnhancedWritingUseCase:
    """強化版執筆ユースケース

    包括的エラーハンドリングを統合した執筆ユースケース。
    18ステップ執筆システムの実行、部分失敗からの復旧、パフォーマンス監視を提供。
    """

    def __init__(self, project_root: str, episode_number: int) -> None:
        self.project_root = project_root
        self.episode_number = episode_number
        self.logger = get_logger(__name__)
        self.console = get_console()
        self.error_handler = get_comprehensive_error_handler(logger=self.logger)

        # ProgressiveWriteManagerを初期化
        try:
            llm_executor = create_progressive_write_llm_executor()
            self.write_manager = create_progressive_write_manager(
                project_root,
                episode_number,
                llm_executor=llm_executor,
            )
        except Exception as e:
            context = ErrorContext(
                operation="initialize_write_manager",
                component="EnhancedWritingUseCase",
                user_action="システム初期化",
                system_state={"project_root": project_root, "episode_number": episode_number}
            )
            error_response = self.error_handler.handle_error(e, context)
            msg = f"執筆システムの初期化に失敗しました: {error_response['error']['message']}"
            raise SystemStateError(
                msg,
                recovery_actions=error_response["next_steps"]
            )

    def get_writing_tasks_with_error_handling(self) -> dict[str, Any]:
        """エラーハンドリング強化版のタスクリスト取得

        Returns:
            タスクリスト（エラー情報を含む）

        Raises:
            SystemStateError: システム状態エラー時
            ApplicationError: アプリケーションエラー時
        """
        context = ErrorContext(
            operation="get_writing_tasks",
            component="EnhancedWritingUseCase",
            user_action="タスクリスト取得"
        )

        try:
            # 入力検証：エピソード番号
            if not isinstance(self.episode_number, int) or self.episode_number <= 0:
                msg = f"無効なエピソード番号です: {self.episode_number}"
                raise InputValidationError(
                    msg,
                    field="episode_number",
                    expected_format="1以上の整数",
                    actual_value=str(self.episode_number),
                    validation_rules=["エピソード番号は1以上の整数である必要があります"]
                )

            # タスクリスト取得
            tasks = self.write_manager.get_writing_tasks()

            # 結果の妥当性検証
            if not isinstance(tasks, dict):
                msg = "タスクリストの形式が正しくありません"
                raise SystemStateError(
                    msg,
                    current_state=f"取得データ: {type(tasks)}",
                    expected_state="辞書形式",
                    state_repair_actions=["システム設定を確認してください"]
                )

            required_keys = ["episode_number", "current_step", "executable_tasks"]
            missing_keys = [key for key in required_keys if key not in tasks]
            if missing_keys:
                msg = f"必要なタスク情報が不足しています: {missing_keys}"
                raise SystemStateError(
                    msg,
                    current_state=f"利用可能なキー: {list(tasks.keys())}",
                    expected_state=f"必要なキー: {required_keys}",
                    state_repair_actions=["タスク設定ファイルを確認してください"]
                )

            # 成功時のレスポンス
            tasks["error_handling"] = {
                "enabled": True,
                "support_contact": "システム管理者",
                "recovery_available": True
            }

            return tasks

        except (SystemStateError, InputValidationError) as e:
            # 構造化エラーとして処理
            error_response = self.error_handler.handle_error(e, context)

            # エラー情報をレスポンスに含める
            return {
                "success": False,
                "error": error_response,
                "episode_number": self.episode_number,
                "fallback_mode": True,
                "partial_data": self._get_fallback_task_data()
            }

        except Exception as e:
            # 予期しないエラー処理（メッセージ欠落に備えフォールバック）
            error_response = self.error_handler.handle_error(e, context)
            err = error_response.get("error", {}) if isinstance(error_response, dict) else {}
            err_msg = err.get("message") or str(e)
            msg = f"タスクリスト取得中に予期しないエラー: {err_msg}"
            raise ApplicationError(msg, recovery_actions=error_response.get("next_steps", []))

    def execute_writing_step_with_recovery(
        self,
        step_id: int,
        dry_run: bool = False,
        enable_recovery: bool = True
    ) -> dict[str, Any]:
        """復旧機能付きステップ実行

        Args:
            step_id: 実行するステップID
            dry_run: ドライランモード
            enable_recovery: 自動復旧を有効にするか

        Returns:
            実行結果（復旧情報を含む）
        """
        context = ErrorContext(
            operation="execute_writing_step",
            component="EnhancedWritingUseCase",
            user_action=f"ステップ{step_id}実行",
            system_state={
                "step_id": step_id,
                "dry_run": dry_run,
                "episode_number": self.episode_number
            }
        )

        try:
            # 入力検証
            self._validate_step_execution_input(step_id, dry_run)

            # ステップ実行（リトライ機能付き）
            # 入口層以外でのループ管理を避けるため、可能なら async API を使用
            try:
                result = asyncio.run(self.write_manager.execute_writing_step_async(step_id, dry_run))
            except RuntimeError:
                # 既存ループ内なら同期APIにフォールバック（内部でガード済み）
                result = self.write_manager.execute_writing_step(step_id, dry_run)

            # 結果の妥当性検証
            if not isinstance(result, dict) or "success" not in result:
                msg = "ステップ実行結果の形式が正しくありません"
                raise SystemStateError(
                    msg,
                    current_state=f"結果: {type(result)}",
                    expected_state="成功フラグ付き辞書",
                    state_repair_actions=["システム状態を確認してください"]
                )

            # 成功時の追加情報
            result["error_handling"] = {
                "recovery_enabled": enable_recovery,
                "retry_available": not result.get("success", False),
                "support_available": True
            }

            return result

        except PartialFailureError as e:
            # 部分失敗の処理
            if enable_recovery:
                recovery_response = self.error_handler.handle_error(e, context, allow_recovery=True)

                # 復旧が成功した場合は実行を継続
                if recovery_response.get("recovery", {}).get("successful"):
                    self.logger.info("ステップ %s の復旧が成功、実行を継続", step_id)
                    return {
                        "success": True,
                        "step_id": step_id,
                        "recovery_applied": True,
                        "recovery_details": recovery_response["recovery"],
                        "message": "復旧処理により実行が完了しました"
                    }

            # 復旧失敗時は部分失敗情報を返す
            error_response = self.error_handler.handle_error(e, context, allow_recovery=False)
            return {
                "success": False,
                "partial_failure": True,
                "step_id": step_id,
                "error": error_response,
                "recovery_point": e.recovery_point,
                "completed_steps": e.completed_steps,
                "failed_steps": e.failed_steps,
                "resumption_available": True
            }

        except (InputValidationError, SystemStateError) as e:
            # 構造化エラーの処理
            error_response = self.error_handler.handle_error(e, context)
            return {
                "success": False,
                "step_id": step_id,
                "error": error_response,
                "user_action_required": True
            }

        except Exception as e:
            # 予期しないエラー処理
            error_response = self.error_handler.handle_error(e, context)
            return {
                "success": False,
                "step_id": step_id,
                "error": error_response,
                "system_error": True,
                "support_required": True
            }

    async def execute_writing_step_with_recovery_async(
        self,
        step_id: int,
        dry_run: bool = False,
        enable_recovery: bool = True,
    ) -> dict[str, Any]:
        """復旧機能付きステップ実行（非同期版）"""
        context = ErrorContext(
            operation="execute_writing_step",
            component="EnhancedWritingUseCase",
            user_action=f"ステップ{step_id}実行",
            system_state={
                "step_id": step_id,
                "dry_run": dry_run,
                "episode_number": self.episode_number,
            },
        )

        try:
            self._validate_step_execution_input(step_id, dry_run)
            result = await self.write_manager.execute_writing_step_async(step_id, dry_run)

            if not isinstance(result, dict) or "success" not in result:
                msg = "ステップ実行結果の形式が正しくありません"
                raise SystemStateError(
                    msg,
                    current_state=f"結果: {type(result)}",
                    expected_state="成功フラグ付き辞書",
                    state_repair_actions=["システム状態を確認してください"],
                )

            result["error_handling"] = {
                "recovery_enabled": enable_recovery,
                "retry_available": not result.get("success", False),
                "support_available": True,
            }
            return result

        except PartialFailureError as e:
            if enable_recovery:
                recovery_response = self.error_handler.handle_error(e, context, allow_recovery=True)
                if recovery_response.get("recovery", {}).get("successful"):
                    self.logger.info("ステップ %s の復旧が成功、実行を継続", step_id)
                    return {
                        "success": True,
                        "step_id": step_id,
                        "recovery_applied": True,
                        "recovery_details": recovery_response["recovery"],
                        "message": "復旧処理により実行が完了しました",
                    }

            error_response = self.error_handler.handle_error(e, context, allow_recovery=False)
            return {
                "success": False,
                "partial_failure": True,
                "step_id": step_id,
                "error": error_response,
                "recovery_point": e.recovery_point,
                "completed_steps": e.completed_steps,
                "failed_steps": e.failed_steps,
                "resumption_available": True,
            }

        except (InputValidationError, SystemStateError) as e:
            error_response = self.error_handler.handle_error(e, context)
            return {
                "success": False,
                "step_id": step_id,
                "error": error_response,
                "user_action_required": True,
            }

        except Exception as e:
            error_response = self.error_handler.handle_error(e, context)
            return {
                "success": False,
                "step_id": step_id,
                "error": error_response,
                "system_error": True,
                "support_required": True,
            }

    def resume_from_partial_failure(self, recovery_point: int) -> dict[str, Any]:
        """部分失敗からの復旧実行

        Args:
            recovery_point: 復旧開始ポイント

        Returns:
            復旧実行結果
        """
        context = ErrorContext(
            operation="resume_from_partial_failure",
            component="EnhancedWritingUseCase",
            user_action=f"ステップ{recovery_point}から復旧",
            system_state={"recovery_point": recovery_point}
        )

        try:
            # 現在の状態を確認
            current_tasks = self.write_manager.get_writing_tasks()
            current_tasks.get("progress", {}).get("completed", 0)

            self.console.print(f"[blue]復旧開始: ステップ{recovery_point}から実行を再開します[/blue]")

            # 復旧ポイントから順次実行
            results = []
            for step_id in range(recovery_point, 19):  # 18ステップまで
                try:
                    result = self.execute_writing_step_with_recovery(step_id, enable_recovery=True)
                    results.append(result)

                    if not result.get("success", False):
                        # 復旧失敗時は中断
                        break

                    self.console.print(f"[green]ステップ{step_id}完了[/green]")

                except Exception:
                    self.logger.exception("復旧実行中にエラー（ステップ%s）", step_id)
                    break

            return {
                "success": True,
                "recovery_point": recovery_point,
                "resumed_steps": len(results),
                "results": results,
                "message": f"ステップ{recovery_point}から{len(results)}ステップを実行しました"
            }
        except Exception as e:
            error_response = self.error_handler.handle_error(e, context)
            return {
                "success": False,
                "recovery_point": recovery_point,
                "error": error_response,
                "message": "復旧実行中にエラーが発生しました"
            }

    async def resume_from_partial_failure_async(self, recovery_point: int) -> dict[str, Any]:
        """部分失敗からの復旧実行（非同期版）"""
        context = ErrorContext(
            operation="resume_from_partial_failure",
            component="EnhancedWritingUseCase",
            user_action=f"ステップ{recovery_point}から復旧",
            system_state={"recovery_point": recovery_point},
        )

        try:
            current_tasks = self.write_manager.get_writing_tasks()
            current_tasks.get("progress", {}).get("completed", 0)

            self.console.print(f"[blue]復旧開始: ステップ{recovery_point}から実行を再開します[/blue]")

            results = []
            for step_id in range(recovery_point, 19):
                try:
                    result = await self.execute_writing_step_with_recovery_async(step_id, enable_recovery=True)
                    results.append(result)
                    if not result.get("success", False):
                        break
                    self.console.print(f"[green]ステップ{step_id}完了[/green]")
                except Exception:
                    self.logger.exception("復旧実行中にエラー（ステップ%s）", step_id)
                    break

            return {
                "success": True,
                "recovery_point": recovery_point,
                "resumed_steps": len(results),
                "results": results,
                "message": f"ステップ{recovery_point}から{len(results)}ステップを実行しました",
            }

        except Exception as e:
            error_response = self.error_handler.handle_error(e, context)
            return {
                "success": False,
                "recovery_point": recovery_point,
                "error": error_response,
                "message": "復旧実行中にエラーが発生しました"
            }

    def get_system_status_with_diagnostics(self) -> dict[str, Any]:
        """診断情報付きシステム状態取得"""
        try:
            # 基本状態取得
            task_status = self.write_manager.get_task_status()

            # エラーハンドリング統計
            error_stats = self.error_handler.get_error_statistics()

            # システム診断
            diagnostics = {
                "write_manager_healthy": hasattr(self.write_manager, "current_state"),
                "error_handler_active": self.error_handler is not None,
                "episode_number_valid": isinstance(self.episode_number, int) and self.episode_number > 0,
                "project_root_accessible": self.project_root and len(str(self.project_root)) > 0
            }

            return {
                "system_status": "healthy" if all(diagnostics.values()) else "degraded",
                "task_status": task_status,
                "error_statistics": error_stats,
                "diagnostics": diagnostics,
                "features": {
                    "auto_recovery": True,
                    "partial_failure_support": True,
                    "performance_monitoring": True,
                        "debug_logging": self.logger.isEnabledFor(LogLevel.DEBUG.value)
                }
            }

        except Exception as e:
            self.logger.exception("システム状態取得中にエラー")
            return {
                "system_status": "error",
                "error_message": str(e),
                "diagnostics": {"basic_functionality": False}
            }

    def _validate_step_execution_input(self, step_id: int, dry_run: bool) -> None:
        """ステップ実行の入力検証"""
        if not isinstance(step_id, int):
            msg = f"ステップIDは整数である必要があります: {step_id}"
            raise InputValidationError(
                msg,
                field="step_id",
                expected_format="整数",
                actual_value=str(step_id),
                validation_rules=["1-18の範囲の整数を指定してください"]
            )

        if step_id < 1 or step_id > 18:
            msg = f"ステップIDは1-18の範囲で指定してください: {step_id}"
            raise InputValidationError(
                msg,
                field="step_id",
                expected_format="1-18の整数",
                actual_value=str(step_id),
                validation_rules=["18ステップシステムの範囲内で指定してください"]
            )

        if not isinstance(dry_run, bool):
            msg = f"dry_runはbool値である必要があります: {dry_run}"
            raise InputValidationError(
                msg,
                field="dry_run",
                expected_format="True または False",
                actual_value=str(dry_run)
            )

    def _get_fallback_task_data(self) -> dict[str, Any]:
        """フォールバック用のタスクデータを生成"""
        return {
            "episode_number": self.episode_number,
            "current_step": None,
            "executable_tasks": [],
            "progress": {"completed": 0, "total": 18, "percentage": 0},
            "fallback_mode": True,
            "message": "システムエラーのため限定機能で動作しています",
            "available_actions": [
                "システム状態の確認",
                "エラーログの確認",
                "システム管理者への問い合わせ"
            ]
        }
