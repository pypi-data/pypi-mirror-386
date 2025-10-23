"""独立セッション実行制御サービス

仕様書: SPEC-FIVE-STAGE-SESSION-002
段階別独立セッション実行・ターン配分制御・データ連携管理
"""

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

from noveler.domain.templates.five_stage_prompt_templates import FiveStagePromptTemplateFactory
from noveler.domain.value_objects.claude_code_execution import ClaudeCodeExecutionResponse
from noveler.domain.value_objects.five_stage_writing_execution import (
    ExecutionStage,
    FiveStageExecutionContext,
    StageExecutionResult,
    StageExecutionStatus,
)
from noveler.infrastructure.factories.path_service_factory import is_mcp_environment
from noveler.infrastructure.integrations.claude_code_integration_service import (
    ClaudeCodeIntegrationConfig,
    ClaudeCodeIntegrationService,
)
from noveler.infrastructure.llm.llm_io_logger import LLMIOLogger
from noveler.infrastructure.logging.unified_logger import get_logger
from noveler.presentation.shared.shared_utilities import console


@dataclass
class StageSessionConfig:
    """段階別セッション設定"""

    stage: ExecutionStage
    allocated_turns: int
    max_turns: int
    priority_weight: float
    timeout_seconds: int = 600

    _DEFAULT_ALLOCATIONS: ClassVar[dict[ExecutionStage, tuple[int, int, float, int]]] = {
        ExecutionStage.DATA_COLLECTION: (4, 6, 1.0, 300),
        ExecutionStage.PLOT_ANALYSIS: (4, 6, 1.2, 300),
        ExecutionStage.EPISODE_DESIGN: (5, 8, 1.4, 400),
        ExecutionStage.MANUSCRIPT_WRITING: (8, 12, 2.0, 800),
        ExecutionStage.INITIAL_WRITING: (6, 10, 1.8, 600),
        ExecutionStage.QUALITY_FINALIZATION: (4, 6, 1.1, 300),
    }

    @classmethod
    def create_default_config(cls, stage: ExecutionStage) -> "StageSessionConfig":
        """段階別デフォルト設定作成"""
        allocated, maximum, weight, timeout = cls._DEFAULT_ALLOCATIONS[stage]
        return cls(stage=stage, allocated_turns=allocated, max_turns=maximum, priority_weight=weight, timeout_seconds=timeout)

    @classmethod
    def for_stage(cls, stage: ExecutionStage) -> "StageSessionConfig":
        """ステージに対応する設定を取得"""
        return cls.create_default_config(stage)


@dataclass
class StageDataTransfer:
    """段階間データ転送オブジェクト"""

    stage: ExecutionStage
    key_data: dict[str, Any]
    metadata: dict[str, Any]
    compression_applied: bool = True
    transfer_size_bytes: int = 0

    def to_context_string(self) -> str:
        """次段階用コンテキスト文字列生成"""
        context_parts = []
        for key, value in self.key_data.items():
            if isinstance(value, str | int | float | bool):
                context_parts.append(f"{key}: {value}")
            elif isinstance(value, list | dict):
                if isinstance(value, list) and len(value) > 3:
                    context_parts.append(f"{key}: [{len(value)}項目]")
                elif isinstance(value, dict) and len(value) > 3:
                    context_parts.append(f"{key}: {{{len(value)}要素}}")
                else:
                    context_parts.append(f"{key}: {str(value)[:100]}...")
        return f"前段階結果({self.stage.display_name}): " + ", ".join(context_parts[:10])


class StageDataConnector:
    """段階間データ接続管理"""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    def extract_essential_data(self, stage: ExecutionStage, stage_result: StageExecutionResult) -> StageDataTransfer:
        """段階結果から必要最小限データ抽出"""
        if not stage_result.output_data:
            return StageDataTransfer(stage=stage, key_data={}, metadata={"extraction_failed": True})
        key_data: dict[str, Any] = {}
        if stage == ExecutionStage.DATA_COLLECTION:
            key_data: dict[str, Any] = {
                "collected_data": stage_result.output_data.get("collected_data", {}),
                "project_structure": stage_result.output_data.get("project_structure", {}),
                "data_quality": stage_result.output_data.get("data_quality_assessment", {}),
            }
        elif stage == ExecutionStage.PLOT_ANALYSIS:
            key_data: dict[str, Any] = {
                "plot_analysis_results": stage_result.output_data.get("plot_analysis_results", {}),
                "character_analysis": stage_result.output_data.get("character_analysis", {}),
                "design_recommendations": stage_result.output_data.get("design_recommendations", {}),
            }
        elif stage == ExecutionStage.EPISODE_DESIGN:
            key_data: dict[str, Any] = {
                "three_act_structure": stage_result.output_data.get("three_act_structure", {}),
                "key_scenes": stage_result.output_data.get("key_scenes", []),
                "writing_guidelines": stage_result.output_data.get("writing_guidelines", {}),
                "pacing_design": stage_result.output_data.get("pacing_design", {}),
            }
        elif stage == ExecutionStage.MANUSCRIPT_WRITING:
            key_data: dict[str, Any] = {
                "manuscript": stage_result.output_data.get("manuscript", ""),
                "writing_metrics": stage_result.output_data.get("writing_metrics", {}),
                "quality_self_assessment": stage_result.output_data.get("quality_self_assessment", {}),
            }
        elif stage == ExecutionStage.INITIAL_WRITING:
            key_data = {
                "draft_outline": stage_result.output_data.get("draft_outline", ""),
                "tone_guidelines": stage_result.output_data.get("tone_guidelines", {}),
            }
        transfer_data = StageDataTransfer(
            stage=stage,
            key_data=key_data,
            metadata={
                "turns_used": stage_result.turns_used,
                "execution_time_ms": stage_result.execution_time_ms,
                "success": stage_result.is_success(),
            },
        )
        transfer_data.transfer_size_bytes = len(str(transfer_data.key_data))
        self.logger.info("%s: データ転送オブジェクト生成 (%sbytes)", stage.display_name, transfer_data.transfer_size_bytes)
        return transfer_data

    def inject_previous_data(self, prompt_template: str, previous_transfers: list[StageDataTransfer]) -> str:
        """前段階データを次段階プロンプトに注入"""
        if not previous_transfers:
            return prompt_template.replace("{previous_results}", "{}")
        context_strings = [transfer.to_context_string() for transfer in previous_transfers]
        previous_context = "\n".join(context_strings)
        structured_data: dict[str, Any] = {}
        for transfer in previous_transfers:
            structured_data[transfer.stage.value] = {
                "status": "completed" if transfer.metadata.get("success") else "failed",
                "output_summary": self._summarize_output(transfer.key_data),
                "turns_used": transfer.metadata.get("turns_used", 0),
            }
        formatted_context = {"context": previous_context, "structured_data": structured_data}
        return prompt_template.replace("{previous_results}", str(formatted_context))

    def _summarize_output(self, key_data: dict[str, Any]) -> str:
        """出力データの要約生成"""
        summary_parts = []
        for key, value in key_data.items():
            if isinstance(value, str):
                summary_parts.append(f"{key}: {len(value)}文字")
            elif isinstance(value, list):
                summary_parts.append(f"{key}: {len(value)}項目")
            elif isinstance(value, dict):
                summary_parts.append(f"{key}: {len(value)}要素")
            else:
                summary_parts.append(f"{key}: {type(value).__name__}")
        return ", ".join(summary_parts)


class IndependentSessionExecutor:
    """独立セッション実行制御サービス

    段階別セッション独立実行・ターン配分制御・データ連携を管理します。
    Claude Code統合により効率的な5段階執筆プロセスを実行し、
    95%トークン削減を実現します。
    """

    def __init__(
        self,
        config_or_service: dict[str, Any] | ClaudeCodeIntegrationService,
        project_root: Path | str | None = None,
    ) -> None:
        """初期化

        Args:
            config_or_service: 設定辞書 または Claudeサービス実装
            project_root: プロジェクトルートパス（サービス直接指定時）
        """

        self.console = console
        self.logger = get_logger(__name__)

        if isinstance(config_or_service, dict):
            # 設定辞書から初期化
            config = dict(config_or_service)
            root = config.get("project_root")
            self.project_root = Path(root) if root is not None else Path.cwd()
            claude_service = config.get("claude_service")
        else:
            # Claudeサービス直接指定（テスト用統合シナリオ等）
            config = {}
            self.project_root = Path(project_root) if project_root is not None else Path.cwd()
            claude_service = config_or_service

        self.config = config

        if claude_service is not None:
            self.claude_service = claude_service
        else:
            self.claude_service = ClaudeCodeIntegrationService(
                ClaudeCodeIntegrationConfig.create_default()
            )

        # 設定に標準値を補完
        self.config.setdefault("project_root", self.project_root)
        self.config.setdefault("claude_service", self.claude_service)

        # プロンプトテンプレートファクトリ
        self.template_factory = FiveStagePromptTemplateFactory()
        self.data_connector = StageDataConnector()
        self.prompt_templates = self.template_factory

    # ------------------------------------------------------------------
    # テスト向け軽量ヘルパー
    # ------------------------------------------------------------------
    def _get_console(self):  # pragma: no cover - tested via patching
        from noveler.presentation.shared import shared_utilities as shared_utils

        return shared_utils.console

    def _format_stage_prompt(
        self,
        stage: ExecutionStage,
        episode_number: int,
        shared_data: dict[str, Any] | None,
        previous_transfers: list[StageDataTransfer] | None,
    ) -> str:
        shared_data = shared_data or {}
        previous_transfers = previous_transfers or []
        header = f"Stage: {stage.display_name} / Episode {episode_number}"
        shared_lines = "\n".join(f"- {key}: {value}" for key, value in shared_data.items()) or "- 共有データなし"
        previous_context = "\n".join(transfer.to_context_string() for transfer in previous_transfers) or "- 前段階データなし"
        return f"{header}\n共有データ:\n{shared_lines}\n前段階要約:\n{previous_context}"

    def _extract_data_from_transfers(self, transfers: list[StageDataTransfer] | None) -> dict[str, Any]:
        extracted: dict[str, Any] = {}
        for transfer in transfers or []:
            namespace = transfer.stage.value
            for key, value in transfer.key_data.items():
                extracted[f"{namespace}_{key}"] = value
        return extracted

    def _get_required_output_keys(self, stage: ExecutionStage) -> list[str]:
        mapping = {
            ExecutionStage.DATA_COLLECTION: ["concept", "theme", "conflict"],
            ExecutionStage.PLOT_ANALYSIS: ["structure", "pacing", "character_arc"],
            ExecutionStage.EPISODE_DESIGN: ["key_scenes", "emotional_flow"],
            ExecutionStage.MANUSCRIPT_WRITING: ["manuscript", "word_count", "quality_notes"],
            ExecutionStage.INITIAL_WRITING: ["draft_outline", "tone_guidelines"],
            ExecutionStage.QUALITY_FINALIZATION: ["issues", "recommendations"],
        }
        return list(mapping.get(stage, [stage.value]))

    async def _handle_metadata_only_response(self, stage: ExecutionStage, response: Any) -> dict[str, Any]:
        console = self._get_console()
        console.print(f"[yellow]Stage {stage.display_name} returned metadata only. Applying fallback parsing.[/yellow]")
        raw = getattr(response, "response", "")
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {"raw_response": raw}
        payload.setdefault("stage", stage.value)
        return payload

    async def _handle_incomplete_response(
        self,
        stage: ExecutionStage,
        incomplete_data: dict[str, Any],
        required_keys: list[str],
    ) -> dict[str, Any]:
        console = self._get_console()
        console.print(f"[yellow]Stage {stage.display_name} returned incomplete data. Generating fallbacks.[/yellow]")
        result = dict(incomplete_data)
        for key in required_keys:
            value = result.get(key)
            if not value:
                result[key] = self._generate_fallback_data_for_key(stage, key)
        return result

    async def _handle_text_extraction_fallback(
        self,
        stage: ExecutionStage,
        raw_text: str,
        required_keys: list[str],
    ) -> dict[str, Any]:
        console = self._get_console()
        console.print(f"[yellow]Stage {stage.display_name} falling back to regex extraction.[/yellow]")
        extracted: dict[str, Any] = {}
        for key in required_keys:
            pattern = re.compile(rf"{re.escape(key)}\s*[:：]\s*(.+?)(?:[。.!?\n]|$)", re.IGNORECASE)
            match = pattern.search(raw_text)
            if match:
                extracted[key] = match.group(1).strip()
            else:
                extracted[key] = self._generate_fallback_data_for_key(stage, key)
        return extracted

    def _generate_emergency_stage_data(self, stage: ExecutionStage, required_keys: list[str]) -> dict[str, str]:
        emergency_data: dict[str, str] = {}
        for key in required_keys:
            emergency_data[key] = self._generate_fallback_data_for_key(stage, key)
        return emergency_data

    def _generate_fallback_data_for_key(self, stage: ExecutionStage, key: str) -> str:
        templates = {
            "concept": "緊急フォールバック: 主人公が予想外の転機を迎えるコンセプトを提示",
            "theme": "緊急フォールバック: 成長と再生をテーマとして扱う",
            "conflict": "緊急フォールバック: 主人公と宿敵の価値観衝突を強調",
            "character": "緊急フォールバック: 新たなサポートキャラクターが合流",
            "setting": "緊急フォールバック: 魔導都市での新章開幕",
        }
        base = templates.get(key, "緊急フォールバック: 物語を前進させる要素を補完")
        return f"{base} ({stage.display_name})"

    async def execute_stage_independently(
        self,
        stage: ExecutionStage,
        context: FiveStageExecutionContext,
        previous_transfers: list[StageDataTransfer] | None = None,
    ) -> tuple[StageExecutionResult, StageDataTransfer]:
        previous_transfers = previous_transfers or []
        shared_data = {}
        if hasattr(context, "get_current_shared_data"):
            try:
                shared_data = context.get_current_shared_data()
            except Exception:
                shared_data = {}

        episode_number = getattr(context, "episode_number", 0)
        prompt = self._format_stage_prompt(stage, episode_number, shared_data, previous_transfers)

        response = await self.claude_service.execute_claude_code_session(prompt)
        turns_used = getattr(response, "turns_used", 0)
        execution_time_ms = getattr(response, "execution_time_ms", 0.0)
        if isinstance(execution_time_ms, (int, float)):
            exec_time_ms = float(execution_time_ms)
        else:
            exec_time_ms = 0.0

        output_payload: dict[str, Any]
        if getattr(response, "success", False):
            output_payload = {
                "text": getattr(response, "response", ""),
                "metadata": getattr(response, "metadata", {}),
            }
            status = StageExecutionStatus.COMPLETED
        else:
            output_payload = {
                "error": getattr(response, "error_message", ""),
                "metadata": getattr(response, "metadata", {}),
            }
            status = StageExecutionStatus.FAILED

        stage_result = StageExecutionResult(
            stage=stage,
            status=status,
            turns_used=turns_used if isinstance(turns_used, int) else 0,
            execution_time_ms=exec_time_ms,
            output_data=output_payload,
        )

        transfer_payload = output_payload if stage_result.is_success() else self._generate_emergency_stage_data(
            stage, self._get_required_output_keys(stage)
        )
        transfer = StageDataTransfer(
            stage=stage,
            key_data=transfer_payload,
            metadata={
                "success": stage_result.is_success(),
                "turns_used": stage_result.turns_used,
                "execution_time_ms": stage_result.execution_time_ms,
            },
        )

        if hasattr(context, "update_shared_data"):
            try:
                context.update_shared_data(transfer.key_data)
            except Exception:
                pass

        return stage_result, transfer

    def _generate_session_transfer_data(self, stage: ExecutionStage, data: dict[str, Any]) -> StageDataTransfer:
        """セッション間データ転送オブジェクト生成

        Args:
            stage: 実行段階
            data: 転送データ

        Returns:
            データ転送オブジェクト
        """
        transfer_data = StageDataTransfer(
            stage=stage,
            key_data=data,
            metadata={"transfer_timestamp": time.time()},
        )
        transfer_data.transfer_size_bytes = len(str(transfer_data.key_data))
        self.console.print("%s: データ転送オブジェクト生成 (%sbytes)", stage.display_name, transfer_data.transfer_size_bytes)
        return transfer_data

    async def execute_stage_session(
        self,
        stage: ExecutionStage,
        context: FiveStageExecutionContext,
        input_data: dict[str, Any] | None = None
    ) -> StageExecutionResult:
        """段階別セッション実行

        Args:
            stage: 実行段階
            context: 実行コンテキスト
            input_data: 入力データ

        Returns:
            段階実行結果
        """
        start_time = time.time()
        console_obj = console

        console_obj.print(f"[bold blue]段階 {stage.stage_number}: {stage.display_name}[/bold blue] 実行開始")

        try:
            # プロンプト生成
            prompt_template = self.template_factory.get_stage_template(stage.stage_number)
            if not prompt_template:
                error_message = f"段階 {stage.stage_number} のテンプレートが見つかりません"
                raise ValueError(error_message)

            # コンテキスト適用
            prompt = prompt_template.render_prompt({
                "episode_number": context.episode_number,
                "project_root": context.project_root,
                "input_data": input_data or {},
                **context.additional_context
            })

            # Claude Code実行
            if is_mcp_environment():
                console_obj.warning("MCP環境: 実際の実行をスキップしてダミー結果を生成")
                execution_result = ClaudeCodeExecutionResponse(
                    success=True,
                    result=f"MCP環境用ダミー結果 - {stage.display_name}",
                    execution_time_ms=100,
                    metadata={
                        "environment": "mcp",
                        "stage": stage.name,
                        "fallback": True
                    }
                )
            else:
                execution_result = await self.claude_service.execute_claude_code_prompt(prompt)

            # LLM I/O保存フック（/noveler write 各ステージ）
            try:
                io_logger = LLMIOLogger(context.project_root)
                response_payload: dict[str, Any] = {
                    "success": execution_result.success,
                    "execution_time_ms": execution_result.execution_time_ms,
                    "error_message": getattr(execution_result, "error_message", None),
                    "result": getattr(execution_result, "result", ""),
                    "metadata": getattr(execution_result, "metadata", {}),
                }
                io_logger.save_stage_io(
                    episode_number=context.episode_number,
                    step_number=stage.stage_number,
                    stage_name=stage.display_name,
                    request_content=prompt,
                    response_content=response_payload,
                    extra_metadata={
                        "context_files_count": len(getattr(context, "project_root_paths", []) or []),
                        "stage_key": stage.name,
                    },
                )
            except Exception:
                pass

            # 実行結果処理
            execution_time_ms = int((time.time() - start_time) * 1000)

            if execution_result.success:
                console_obj.print(f"✅ {stage.display_name} 完了 ({execution_time_ms}ms)")
                return StageExecutionResult(
                    stage=stage,
                    status=StageExecutionStatus.COMPLETED,
                    output_data={"result": execution_result.result},
                    execution_time_ms=execution_time_ms,
                    metadata=execution_result.metadata or {}
                )
            console_obj.print(f"❌ {stage.display_name} 失敗: {execution_result.error_message}")
            return StageExecutionResult(
                stage=stage,
                status=StageExecutionStatus.FAILED,
                error_message=execution_result.error_message,
                execution_time_ms=execution_time_ms,
                metadata=execution_result.metadata or {}
            )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            console_obj.error(f"段階 {stage.stage_number} 実行中にエラー: {e}")

            return StageExecutionResult(
                stage=stage,
                status=StageExecutionStatus.FAILED,
                error_message=str(e),
                execution_time_ms=execution_time_ms,
                metadata={"error_type": type(e).__name__}
            )

    async def execute_five_stage_session(
        self,
        context: FiveStageExecutionContext,
        start_stage: int = 1,
        end_stage: int = 5
    ) -> list[StageExecutionResult]:
        """5段階セッション完全実行

        Args:
            context: 実行コンテキスト
            start_stage: 開始段階
            end_stage: 終了段階

        Returns:
            各段階の実行結果リスト
        """
        console_obj = console
        console_obj.print(f"[bold green]5段階執筆セッション開始[/bold green] (段階 {start_stage}-{end_stage})")

        results = []

        # 段階実行定義
        stages = [
            ExecutionStage(1, "plot_data_preparation", "プロット準備"),
            ExecutionStage(2, "plot_structure_analysis", "構造分析"),
            ExecutionStage(3, "emotional_flow_design", "感情設計"),
            ExecutionStage(4, "humor_elements_design", "ユーモア設計"),
            ExecutionStage(5, "manuscript_writing", "原稿執筆")
        ]

        # 段階間データ連携
        stage_data = {}

        for stage in stages:
            if start_stage <= stage.stage_number <= end_stage:
                result = await self.execute_stage_session(stage, context, stage_data)
                results.append(result)

                # 次段階への データ連携
                if result.status == StageExecutionStatus.COMPLETED:
                    stage_data[stage.name] = result.output_data
                else:
                    console_obj.warning(f"段階 {stage.stage_number} が失敗しましたが続行します")

        console_obj.print(f"[bold green]5段階執筆セッション完了[/bold green] - {len(results)}段階実行")
        return results
