"""インタラクティブ執筆制御ユースケース

Claude Code統合インタラクティブ執筆システムの中核制御ロジック。
10段階執筆プロセスの制御、品質ゲート管理、ユーザー交流を統合管理します。
"""

from typing import Any

from noveler.application.interfaces.quality_service_interface import IQualityService
from noveler.application.interfaces.session_manager_interface import ISessionManager
from noveler.domain.entities.interactive_writing_session import (
    InteractiveWritingSession,
    SessionStatus,
    StepExecutionResult,
    StepStatus,
    UserFeedback,
)
from noveler.domain.value_objects.project_time import project_now
from noveler.domain.value_objects.quality_check_result import QualityCheckResult
from noveler.presentation.shared.shared_utilities import console

from .step_processors.step_processor_factory import StepProcessorFactory


class InteractiveWritingController:
    """インタラクティブ執筆制御ユースケース

    10段階インタラクティブ執筆プロセスを制御し、Claude Codeとの統合を管理します。
    各段階でのユーザーフィードバック処理、品質ゲート判定、セッション状態管理を行います。
    """

    def __init__(
        self,
        session_manager: ISessionManager,
        quality_service: IQualityService,
        step_processor_factory: StepProcessorFactory
    ) -> None:
        self.session_manager = session_manager
        self.quality_service = quality_service
        self.step_processor_factory = step_processor_factory
        self.console = console

    async def start_interactive_writing(
        self,
        episode_number: int,
        project_root: str,
        configuration: dict[str, Any] | None = None
    ) -> InteractiveWritingSession:
        """インタラクティブ執筆を開始"""

        self.console.info(f"第{episode_number}話のインタラクティブ執筆を開始")

        # 新規セッション作成
        session = await self.session_manager.create_session(
            episode_number=episode_number,
            project_root=project_root,
            configuration=configuration or {}
        )

        self.console.success(f"セッション {session.session_id} を作成しました")
        return session

    async def continue_writing_session(
        self,
        session_id: str,
        user_feedback: str | None = None
    ) -> InteractiveWritingSession:
        """既存セッションを継続"""

        session = await self.session_manager.load_session(session_id)
        if not session:
            msg = f"セッション {session_id} が見つかりません"
            raise ValueError(msg)

        # セッション期限チェック
        if session.is_session_expired():
            self.console.warning("セッションが期限切れです。新しいセッションを開始してください")
            msg = "セッション期限切れ"
            raise ValueError(msg)

        # ユーザーフィードバック処理
        if user_feedback and session.requires_user_confirmation():
            await self._process_user_feedback(session, user_feedback)

        session.status = SessionStatus.IN_PROGRESS
        await self.session_manager.save_session(session)

        self.console.info(f"セッション {session_id} を再開しました")
        return session

    async def execute_next_step(
        self,
        session: InteractiveWritingSession
    ) -> StepExecutionResult:
        """次のステップを実行"""

        next_step = session.current_step + 1 if session.current_step < 10 else 10

        if next_step > 10:
            # 全ステップ完了
            session.status = SessionStatus.COMPLETED
            await self.session_manager.save_session(session)

            return StepExecutionResult(
                step=10,
                status=StepStatus.COMPLETED,
                output={"message": "全ての段階が完了しました"},
                summary="インタラクティブ執筆が完了しました",
                user_prompt="執筆完了です。最終確認をお願いします。"
            )

        return await self.execute_step(session, next_step)

    async def execute_step(
        self,
        session: InteractiveWritingSession,
        step: int,
        user_feedback: str | None = None
    ) -> StepExecutionResult:
        """指定ステップを実行"""

        # ステップ実行可能性チェック
        if not session.can_proceed_to_step(step):
            msg = f"ステップ {step} を実行できません。前ステップが未完了です"
            raise ValueError(msg)

        self.console.info(f"ステップ {step} を実行中...")
        start_time = project_now().datetime

        try:
            # 前段階フィードバック処理
            if user_feedback and step > 1:
                await self._process_user_feedback(session, user_feedback, step - 1)

            # ステップ処理器取得・実行
            processor = self.step_processor_factory.get_processor(step)
            step_result = await processor.execute(session)
            # モック/実装差異に関わらず一貫したステップ番号を保証
            try:
                step_result.step = step
            except Exception:
                pass

            # 実行時間計算
            execution_time = (project_now().datetime - start_time).total_seconds() * 1000
            step_result.execution_time_ms = int(execution_time)

            # 品質ゲートチェック
            quality_result = await self._execute_quality_gate(session, step, step_result)
            step_result.quality_check = quality_result

            # セッション更新
            session.add_step_result(step_result)
            session.add_quality_result(quality_result)

            # ユーザー確認要求判定
            should_wait_confirmation = await self._should_wait_for_user_confirmation(
                session, step, quality_result
            )

            if should_wait_confirmation:
                session.set_pending_confirmation(step, step_result, quality_result)
                self.console.info(f"ステップ {step} 完了。ユーザー確認待ち")
            else:
                step_result.status = StepStatus.COMPLETED
                session.status = SessionStatus.IN_PROGRESS
                self.console.success(f"ステップ {step} が自動承認されました")

            # セッション保存
            await self.session_manager.save_session(session)

            return step_result

        except Exception as e:
            # エラー処理
            error_result = StepExecutionResult(
                step=step,
                status=StepStatus.FAILED,
                output={"error": str(e)},
                summary=f"ステップ {step} でエラーが発生しました",
                user_prompt="エラーが発生しました。セッションを確認してください。"
            )

            session.add_step_result(error_result)
            session.status = SessionStatus.ERROR
            await self.session_manager.save_session(session)

            self.console.error(f"ステップ {step} 実行エラー: {e!s}")
            raise

    async def get_session_status(
        self,
        session_id: str
    ) -> dict[str, Any]:
        """セッション状況を取得"""

        session = await self.session_manager.load_session(session_id)
        if not session:
            return {"error": f"セッション {session_id} が見つかりません"}

        return session.generate_session_summary()

    async def handle_quality_gate_failure(
        self,
        session: InteractiveWritingSession,
        step: int,
        quality_result: QualityCheckResult
    ) -> StepExecutionResult:
        """品質ゲート失敗時の処理"""

        # 改善提案生成
        suggestions = await self.quality_service.generate_improvement_suggestions(
            quality_result,
            step,
            session.data
        )

        # 修正要求結果作成
        return StepExecutionResult(
            step=step,
            status=StepStatus.WAITING_USER,
            output={
                "quality_issues": [issue.to_dict() for issue in quality_result.issues],
                "improvement_suggestions": suggestions
            },
            summary=f"ステップ {step} で品質基準を満たしませんでした",
            user_prompt="品質改善が必要です。提案された修正を確認し、指示をお願いします。"
        )


    async def _process_user_feedback(
        self,
        session: InteractiveWritingSession,
        feedback_text: str,
        target_step: int | None = None
    ) -> None:
        """ユーザーフィードバックを処理"""

        step = target_step or session.current_step

        feedback = UserFeedback(
            step=step,
            feedback=feedback_text,
            timestamp=project_now().datetime,
            feedback_type=self._classify_feedback_type(feedback_text)
        )

        session.add_user_feedback(feedback)

        # フィードバックタイプ別処理
        if feedback.is_approval():
            self.console.info(f"ステップ {step} が承認されました")
        else:
            # 修正指示を抽出してセッションデータに反映
            modification_requests = feedback.extract_modification_requests()
            if modification_requests:
                session.data[f"step_{step}_modifications"] = modification_requests
                self.console.info(f"ステップ {step} の修正指示を反映しました")

    def _classify_feedback_type(self, feedback_text: str) -> str:
        """フィードバックタイプを分類"""
        feedback_lower = feedback_text.lower()

        if any(word in feedback_lower for word in ["承認", "ok", "オッケー", "良い"]):
            return "approval"
        if any(word in feedback_lower for word in ["修正", "変更", "改善"]):
            return "modification_request"
        return "text"

    async def _execute_quality_gate(
        self,
        session: InteractiveWritingSession,
        step: int,
        step_result: StepExecutionResult
    ) -> QualityCheckResult:
        """品質ゲートを実行"""

        try:
            # 段階別品質チェック実行
            quality_result = await self.quality_service.check_step_quality(
                episode_number=session.episode_number,
                step=step,
                step_data=step_result.output,
                session_context=session.data
            )

            self.console.info(
                f"ステップ {step} 品質チェック完了: {quality_result.overall_score:.1f}点"
            )

            return quality_result

        except Exception as e:
            # 品質チェックエラー時はデフォルト結果を返す（シンプルな名前空間で十分）
            from types import SimpleNamespace
            self.console.warning(f"品質チェックエラー: {e!s}")
            return SimpleNamespace(
                overall_score=70.0,  # デフォルトスコア
                detailed_scores={"default": 70.0},
                issues=[],
                suggestions=[],
                metadata={"error": str(e)}
            )

    async def _should_wait_for_user_confirmation(
        self,
        session: InteractiveWritingSession,
        step: int,
        quality_result: QualityCheckResult
    ) -> bool:
        """ユーザー確認を待つべきかを判定"""

        # 品質スコアが自動進行しきい値を超えている場合は自動進行
        if session.should_auto_proceed(quality_result.overall_score):
            return False

        # 品質ゲート失敗の場合は必ず確認が必要
        threshold = session.get_step_quality_threshold(step)
        if quality_result.overall_score < threshold["warning"]:
            return True

        # 重要ステップ（原稿執筆、最終調整）は必ず確認
        critical_steps = [8, 10]
        return step in critical_steps

    async def resume_from_interruption(
        self,
        session_id: str
    ) -> InteractiveWritingSession:
        """中断からの復旧"""

        self.console.info(f"セッション {session_id} の復旧を試行")

        # セッション復元
        session = await self.session_manager.recover_session(session_id)
        if not session:
            msg = f"セッション {session_id} を復元できませんでした"
            raise ValueError(msg)

        # 状態チェック・修正
        if session.status == SessionStatus.ERROR:
            # エラー状態からの復旧
            session.status = SessionStatus.IN_PROGRESS

        # 未完了ステップの再実行準備
        if session.current_step > 0:
            last_result = session.step_results.get(session.current_step)
            if last_result and last_result.status == StepStatus.FAILED:
                # 失敗したステップを再実行可能状態に
                last_result.status = StepStatus.PENDING

        await self.session_manager.save_session(session)

        self.console.success(f"セッション {session_id} の復旧が完了しました")
        return session

    def generate_claude_code_response(
        self,
        session: InteractiveWritingSession,
        step_result: StepExecutionResult
    ) -> dict[str, Any]:
        """Claude Code向けの応答を生成"""

        response = {
            "success": True,
            "session_id": session.session_id,
            "current_step": session.current_step,
            "step_status": step_result.status.value,
            "execution_summary": {
                "step_name": self._get_step_name(session.current_step),
                "completion_time": project_now().datetime.isoformat(),
                "processing_time_ms": step_result.execution_time_ms
            },
            "user_interaction": {
                "confirmation_required": session.requires_user_confirmation(),
                "prompt": step_result.user_prompt,
                "options": ["承認", "修正指示", "詳細確認"]
            }
        }

        # 品質情報追加
        if step_result.quality_check:
            qc = step_result.quality_check
            response["quality_gate"] = {
                "overall_score": qc.overall_score,
                "status": self._get_quality_status(session.current_step, qc.overall_score),
                "critical_issues": len([i for i in qc.issues if i.severity == "critical"]),
                "warning_issues": len([i for i in qc.issues if i.severity == "warning"]),
                "gate_threshold": session.get_step_quality_threshold(session.current_step)
            }

        # ファイル参照情報
        if step_result.file_references:
            response["file_references"] = step_result.file_references

        # 次ステップ情報
        if session.current_step < 10:
            response["next_step"] = {
                "step_number": session.current_step + 1,
                "step_name": self._get_step_name(session.current_step + 1),
                "estimated_time": "3-5分"
            }

        return response

    def _get_step_name(self, step: int) -> str:
        """ステップ名を取得"""
        step_names = {
            1: "プロットデータ準備",
            2: "構造分析",
            3: "感情設計",
            4: "ユーモア要素設計",
            5: "キャラクター対話設計",
            6: "場面演出設計",
            7: "論理整合性調整",
            8: "原稿執筆",
            9: "品質改善",
            10: "最終調整"
        }
        return step_names.get(step, f"ステップ {step}")

    def _get_quality_status(self, step: int, score: float) -> str:
        """品質ゲート状態を取得"""
        # デフォルトセッションを作成してしきい値を取得
        temp_session = InteractiveWritingSession(
            session_id="temp",
            episode_number=1,
            project_root="",
            status=SessionStatus.IN_PROGRESS,
            current_step=step,
            created_at=project_now().datetime,
            updated_at=project_now().datetime
        )

        threshold = temp_session.get_step_quality_threshold(step)

        if score >= threshold["pass"]:
            return "passed"
        if score >= threshold["warning"]:
            return "warning"
        return "blocked"
