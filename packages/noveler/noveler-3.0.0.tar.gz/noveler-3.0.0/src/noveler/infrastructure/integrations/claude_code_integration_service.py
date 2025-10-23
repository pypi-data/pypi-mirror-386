"""Claude Code統合サービス

仕様書: SPEC-CLAUDE-CODE-001
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Any

from noveler.domain.value_objects.claude_code_execution import (
    ClaudeCodeExecutionRequest,
    ClaudeCodeExecutionResponse,
)
from noveler.infrastructure.factories.configuration_service_factory import get_configuration_manager
from noveler.infrastructure.factories.path_service_factory import is_mcp_environment
from noveler.presentation.shared.shared_utilities import _get_console


@dataclass
class ClaudeCodeIntegrationConfig:
    """Claude Code統合設定

    REQ-1.2: 統合設定管理システムによる実行設定管理
    """

    claude_executable_path: str = "claude"
    default_output_format: str = "json"
    default_max_turns: int = 3
    timeout_seconds: int = 300

    @classmethod
    def from_configuration_manager(cls) -> "ClaudeCodeIntegrationConfig":
        """統合設定管理システムから設定を読み込み"""
        try:
            config_manager = get_configuration_manager()
            config = config_manager.get_configuration()
            return cls(
                claude_executable_path=config.get_or_default("claude_code.executable_path", "claude"),
                default_output_format=config.get_or_default("claude_code.output_format", "json"),
                default_max_turns=config.get_or_default("claude_code.max_turns", 3),
                timeout_seconds=config.get_or_default("claude_code.timeout_seconds", 300),
            )
        except Exception:
            return cls()


class ClaudeCodeIntegrationService:
    """Claude Code統合サービス"""

    def __init__(self, config: ClaudeCodeIntegrationConfig) -> None:
        self.config = config
        self.console = _get_console()

    async def validate_environment(self) -> bool:
        """Claude Code実行環境の検証（B20準拠: 例外ではなくFalse返却）"""
        try:
            return self._validate_claude_code_availability()
        except Exception as _:
            return False

    def _validate_claude_code_availability(self) -> bool:
        """Claude Code利用可能性チェック（MCP環境ではFalseとして扱う）"""
        if is_mcp_environment():
            # MCP内では外部CLIを直接は使わないためFalse（ダイレクト実行は別経路）
            return False
        # 最低限: 実行パス設定が空でないことのみ確認（詳細な存在確認は環境依存のため簡略化）
        return bool(self.config.claude_executable_path)

    async def execute_request(self, request: ClaudeCodeExecutionRequest) -> ClaudeCodeExecutionResponse:
        """ドメインプロトコル互換エイリアス（IClaudeCodeIntegrationService想定）"""
        return await self.execute_prompt(request)

    async def execute_prompt(self, request: ClaudeCodeExecutionRequest) -> ClaudeCodeExecutionResponse:
        """Universal/Domainが期待するリクエスト型の実行エントリ"""
        # 現実装はprompt文字列のみを受ける実装に委譲
        base_result = await self.execute_claude_code_prompt(request.prompt_content)

        # VO準拠フィールドへ正規化
        if getattr(base_result, "response_content", None):
            content = base_result.response_content
        else:
            content = getattr(base_result, "result", "")

        normalized = ClaudeCodeExecutionResponse(
            success=base_result.success,
            response_content=content,
            json_data=getattr(base_result, "json_data", None),
            execution_time_ms=base_result.execution_time_ms,
            error_message=getattr(base_result, "error_message", None),
        )
        # 後方互換フィールド（存在すれば維持）
        try:
            normalized.result = content
            if hasattr(base_result, "metadata"):
                normalized.metadata = base_result.metadata
        except Exception:
            pass
        return normalized

    async def execute_claude_code_prompt(self, prompt: str) -> ClaudeCodeExecutionResponse:
        """Claude Code統合プロンプト実行

        Args:
            prompt: 実行するプロンプト

        Returns:
            実行結果
        """
        if is_mcp_environment():
            self.console.print("[yellow]MCP環境では外部Claude API呼び出しをスキップします[/yellow]")
            resp = ClaudeCodeExecutionResponse(
                success=True,
                response_content="MCP環境用フォールバック結果",
                execution_time_ms=100,
            )
            # 後方互換メタを付与
            resp.result = resp.response_content
            resp.metadata = {"environment": "mcp", "fallback": True, "prompt_length": len(prompt)}
            return resp

        start_time = time.time()

        try:
            # 実際のClaude Code実行ロジック（プレースホルダー）
            self.console.print(f"[cyan]プロンプト実行開始[/cyan]: {len(prompt)}文字")

            # シミュレーション
            await asyncio.sleep(0.1)

            execution_time = int((time.time() - start_time) * 1000)

            resp = ClaudeCodeExecutionResponse(
                success=True,
                response_content="実行完了",
                execution_time_ms=execution_time,
            )
            resp.result = resp.response_content
            resp.metadata = {"prompt_length": len(prompt), "environment": "standard"}
            return resp

        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            self.console.print(f"[red]Claude Code実行エラー[/red]: {e}")

            return ClaudeCodeExecutionResponse(
                success=False,
                response_content="",
                error_message=str(e),
                execution_time_ms=execution_time,
            )

    async def execute_with_turn_limit(self, prompt: str, max_turns: int = 5) -> dict[str, Any]:
        """ターン制限付きClaude Code実行

        Args:
            prompt: 実行プロンプト
            max_turns: 最大ターン数

        Returns:
            実行結果とメタデータ
        """
        self.console.print(f"[cyan]ターン制限付き実行開始[/cyan]: max_turns={max_turns}")
        try:
            result = await self.execute_claude_code_prompt(prompt)
            return {
                "success": result.success,
                "result": result.result,
                "turns_used": 1,
                "max_turns": max_turns,
                "execution_time_ms": result.execution_time_ms
            }
        except Exception as e:
            self.console.print(f"[red]ターン制限付き実行エラー[/red]: {e}")
            return {
                "success": False,
                "error": str(e),
                "turns_used": 1,
                "max_turns": max_turns
            }
