#!/usr/bin/env python3
# File: src/noveler/domain/services/claude_code_execution_service.py
# Purpose: Execute Claude Code requests with error recovery and detailed LLM logging
# Context: Domain service for Claude Code integration with structured logging support

"""Claude Code実行サービス

Claude Codeの実行、エラー回復、プロンプト最適化を担当するドメインサービス
EnhancedIntegratedWritingUseCaseから分離されたコンポーネント
"""

import time
from typing import TYPE_CHECKING, Any, Dict, Protocol

if TYPE_CHECKING:
    from noveler.domain.interfaces.console_service_protocol import IConsoleService
    from noveler.domain.interfaces.logger import ILogger

from noveler.domain.value_objects.claude_code_execution import ClaudeCodeExecutionRequest, ClaudeCodeExecutionResponse


class IClaudeCodeIntegrationService(Protocol):
    """Claude Code統合サービスのインターフェース（ドメイン層用）"""

    async def execute_request(self, request: ClaudeCodeExecutionRequest) -> ClaudeCodeExecutionResponse:
        """実行リクエストを処理"""
        ...


class IConfigurationService(Protocol):
    """設定サービスのインターフェース（ドメイン層用）"""

    def get_max_turns_setting(self) -> int:
        """最大ターン数設定を取得"""
        ...

    def get_retry_setting(self) -> int:
        """リトライ設定を取得"""
        ...


class ClaudeCodeExecutionService:
    """Claude Code実行ドメインサービス

    責務:
    - Claude Code実行リクエストの構築と実行
    - max_turnsエラーの自動回復処理
    - プロンプト最適化機能
    """

    def __init__(
        self,
        claude_code_service: IClaudeCodeIntegrationService,
        console_service: "IConsoleService",
        configuration_service: IConfigurationService,
        logger: "ILogger",
    ) -> None:
        """初期化

        Args:
            claude_code_service: Claude Code統合サービス（インターフェース）
            console_service: コンソールサービス
            configuration_service: 設定サービス（インターフェース）
            logger: ロガー（インターフェース）
        """
        self.claude_code_service = claude_code_service
        self.console_service = console_service
        self.configuration_service = configuration_service
        self.logger = logger

    async def execute_claude_code(
        self, prompt_content: str, project_root_paths: list, session_id: str
    ) -> ClaudeCodeExecutionResponse:
        """Claude Code実行

        Args:
            prompt_content: プロンプト内容
            project_root_paths: プロジェクトルートパス一覧
            session_id: セッションID

        Returns:
            ClaudeCodeExecutionResponse: 実行結果
        """
        start_time = time.time()

        # Structured logging with extra data
        extra_data: Dict[str, Any] = {
            "session_id": session_id,
            "prompt_length": len(prompt_content),
            "estimated_tokens": self._estimate_token_count(prompt_content),
            "project_paths": project_root_paths,
            "operation": "claude_code_execution",
        }

        self.logger.info(
            "Claude Code直接実行開始",
            extra={"extra_data": extra_data}
        )
        self.console_service.print_info("処理中...")

        try:
            # 設定サービスから設定取得（ドメインインターフェース経由）
            max_turns = self.configuration_service.get_max_turns_setting()

            claude_request = ClaudeCodeExecutionRequest(
                prompt_content=prompt_content,
                output_format="json",
                max_turns=max_turns,
                project_context_paths=project_root_paths,
            )

            # Log LLM request details
            self.logger.debug(
                "Claude Code APIリクエスト送信",
                extra={"extra_data": {
                    "max_turns": max_turns,
                    "output_format": "json",
                    "request_id": session_id,
                }}
            )

            claude_response = await self.claude_code_service.execute_prompt(claude_request)

            # Calculate execution time and tokens used
            execution_time = (time.time() - start_time) * 1000

            if claude_response.is_success():
                # Log detailed LLM response metrics
                response_metrics = {
                    "success": True,
                    "execution_time_ms": claude_response.execution_time_ms,
                    "total_time_ms": execution_time,
                    "session_id": session_id,
                }

                # Try to extract token usage if available in response
                if hasattr(claude_response, 'metadata') and claude_response.metadata:
                    if 'token_usage' in claude_response.metadata:
                        response_metrics.update({
                            "tokens_input": claude_response.metadata['token_usage'].get('input_tokens', 0),
                            "tokens_output": claude_response.metadata['token_usage'].get('output_tokens', 0),
                            "tokens_total": claude_response.metadata['token_usage'].get('total_tokens', 0),
                        })
                    if 'model' in claude_response.metadata:
                        response_metrics["model"] = claude_response.metadata['model']

                self.logger.info(
                    "✅ Claude Code実行成功",
                    extra={"extra_data": response_metrics}
                )
                self.console_service.print_success(
                    f"✅ Claude Code実行成功 ({claude_response.execution_time_ms:.0f}ms)"
                )
                return claude_response

            # max_turnsエラーの場合は自動回復を試行
            if self._is_max_turns_error(claude_response):
                self.logger.warning(
                    "max_turns制限エラー検出 - 自動回復試行",
                    extra={"extra_data": {
                        "error_type": "max_turns_exceeded",
                        "original_max_turns": max_turns,
                        "session_id": session_id,
                    }}
                )
                self.console_service.print_warning("max_turnsエラー - 自動回復を試行します")

                recovery_response = await self.attempt_max_turns_recovery(
                    prompt_content, project_root_paths, session_id, max_turns
                )

                if recovery_response:
                    return recovery_response

            # その他のエラーまたは回復失敗
            error_metrics = {
                "success": False,
                "error_message": claude_response.error_message,
                "execution_time_ms": execution_time,
                "session_id": session_id,
            }

            if hasattr(claude_response, 'json_data') and claude_response.json_data:
                error_metrics["error_type"] = claude_response.json_data.get("error_type", "unknown")
                error_metrics["error_details"] = claude_response.json_data.get("error_details")

            self.logger.warning(
                "Claude Code実行失敗",
                extra={"extra_data": error_metrics}
            )
            return claude_response

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.error(
                "Claude Code実行エラー",
                exc_info=True,
                extra={"extra_data": {
                    "error_type": "execution_error",
                    "error_message": str(e),
                    "execution_time_ms": execution_time,
                    "session_id": session_id,
                }}
            )
            # エラー応答を作成して返す
            return ClaudeCodeExecutionResponse(
                success=False, error_message=f"実行エラー: {e}", execution_time_ms=execution_time, response_content=""
            )

    async def attempt_max_turns_recovery(
        self, original_prompt: str, project_root_paths: list, session_id: str, original_max_turns: int
    ) -> ClaudeCodeExecutionResponse | None:
        """max_turnsエラー自動回復機能

        Args:
            original_prompt: 元のプロンプト
            project_root_paths: プロジェクトルートパス一覧
            session_id: セッションID
            original_max_turns: 元のmax_turns設定

        Returns:
            成功時は回復されたレスポンス、失敗時はNone
        """
        # 設定サービスから自動回復パラメータを取得（ドメインインターフェース経由）
        auto_retry_enabled = True  # デフォルト値
        fallback_increment = 5  # デフォルト値
        max_total_turns = self.configuration_service.get_retry_setting()

        if not auto_retry_enabled:
            self.logger.info("自動回復機能は無効になっています")
            self.console_service.print_debug("処理中...")
            return None

        # プロンプト最適化を試行
        self.logger.info("ステップ1: プロンプト最適化実行")
        self.console_service.print_info("処理中...")
        optimized_prompt = await self._optimize_prompt_for_recovery(original_prompt)

        # 段階的にmax_turnsを増加して再試行
        retry_attempts = [
            (original_max_turns + fallback_increment, "基本増加"),
            (original_max_turns + fallback_increment * 2, "追加増加"),
        ]

        for retry_turns, description in retry_attempts:
            if retry_turns > max_total_turns:
                self.logger.warning("制限超過のためスキップ: %s", retry_turns)
                self.console_service.print_warning("警告メッセージ")
                continue

            self.logger.info("ステップ2: %sで再試行 (max_turns: %s)", description, retry_turns)
            self.console_service.print_info("情報メッセージ")

            try:
                claude_request = ClaudeCodeExecutionRequest(
                    prompt_content=optimized_prompt,
                    output_format="json",
                    max_turns=retry_turns,
                    project_context_paths=project_root_paths,
                )

                claude_response = await self.claude_code_service.execute_prompt(claude_request)

                if claude_response.is_success():
                    recovery_metrics = {
                        "success": True,
                        "recovery_attempted": True,
                        "recovery_max_turns_used": retry_turns,
                        "execution_time_ms": claude_response.execution_time_ms,
                        "session_id": session_id,
                        "recovery_description": description,
                    }

                    self.logger.info(
                        "✅ 自動回復成功",
                        extra={"extra_data": recovery_metrics}
                    )
                    self.console_service.print_success(
                        f"✅ 自動回復成功 (max_turns: {retry_turns}, {claude_response.execution_time_ms:.0f}ms)"
                    )

                    # 回復情報をメタデータに追加
                    if not hasattr(claude_response, "metadata"):
                        claude_response.metadata = {}
                    claude_response.metadata["recovery_attempted"] = True
                    claude_response.metadata["recovery_max_turns_used"] = retry_turns

                    return claude_response

                self.logger.warning(
                    "再試行失敗",
                    extra={"extra_data": {
                        "recovery_description": description,
                        "retry_turns": retry_turns,
                        "error_message": claude_response.error_message,
                        "session_id": session_id,
                    }}
                )
                self.console_service.print_warning(f"再試行失敗 ({description}): {claude_response.error_message}")

            except Exception as e:
                self.logger.error(
                    "回復試行中エラー",
                    exc_info=True,
                    extra={"extra_data": {
                        "recovery_description": description,
                        "retry_turns": retry_turns,
                        "error_message": str(e),
                        "session_id": session_id,
                    }}
                )
                self.console_service.print_error(f"回復試行中にエラーが発生しました: {e}")

        self.logger.error(
            "全ての自動回復試行が失敗しました",
            extra={"extra_data": {
                "session_id": session_id,
                "total_attempts": len(retry_attempts),
                "max_total_turns": max_total_turns,
            }}
        )
        self.console_service.print_error("自動回復に失敗しました")
        return None

    async def _optimize_prompt_for_recovery(self, original_prompt: str) -> str:
        """回復用プロンプト最適化

        Args:
            original_prompt: 元のプロンプト

        Returns:
            最適化されたプロンプト
        """
        try:
            # DDD準拠: プロンプト最適化ツールは依存性注入で提供されるべき
            if hasattr(self, "_prompt_optimizer") and self._prompt_optimizer:
                from noveler.domain.entities.prompt_generation import OptimizationTarget

                optimized = self._prompt_optimizer.optimize_for_target(original_prompt, OptimizationTarget.CLAUDE_CODE)
            else:
                # フォールバック: 基本的な最適化のみ
                return original_prompt.strip()

            # 最適化統計を表示
            original_tokens = self._estimate_token_count(original_prompt)
            optimized_tokens = self._estimate_token_count(optimized)
            reduction = original_tokens - optimized_tokens

            if reduction > 0:
                self.logger.info(
                    "プロンプト最適化完了: %s → %s tokens (-%s)", original_tokens, optimized_tokens, reduction
                )
                self.console_service.print_success("成功メッセージ")
            else:
                self.logger.debug("最適化結果: %s → %s tokens", original_tokens, optimized_tokens)
                self.console_service.print_debug(f"最適化結果: {original_tokens} → {optimized_tokens} tokens")

            return optimized

        except ImportError:
            self.logger.info("プロンプト最適化ツール未利用 - 元のプロンプトを使用")
            self.console_service.print_warning("処理中...")
            return original_prompt
        except Exception as e:
            self.logger.error(f"プロンプト最適化エラー: {e}", exc_info=True)
            self.console_service.print_error("エラーが発生しました")
            return original_prompt

    def _is_max_turns_error(self, claude_response: ClaudeCodeExecutionResponse) -> bool:
        """max_turnsエラー判定"""
        return claude_response.json_data and claude_response.json_data.get("error_type") == "error_max_turns"

    def _estimate_token_count(self, text: str) -> int:
        """トークン数概算（簡易版）"""
        # 簡易的な推定: 1トークン ≈ 4文字
        return len(text) // 4
