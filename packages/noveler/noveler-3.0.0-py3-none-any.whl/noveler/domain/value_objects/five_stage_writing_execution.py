#!/usr/bin/env python3
"""5段階分割執筆実行システム

仕様書: SPEC-FIVE-STAGE-001
max_turnsエラー根本解決のための段階分割実行アーキテクチャ
"""

import importlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from noveler.domain.value_objects.structured_step_output import StructuredStepOutput



class ExecutionStage(Enum):
    """実行段階定義"""

    DATA_COLLECTION = "data_collection"
    PLOT_ANALYSIS = "plot_analysis"
    EPISODE_DESIGN = "episode_design"
    MANUSCRIPT_WRITING = "manuscript_writing"
    INITIAL_WRITING = "initial_writing"
    QUALITY_FINALIZATION = "quality_finalization"

    @property
    def display_name(self) -> str:
        """表示名取得"""
        display_names: dict[ExecutionStage, str] = {
            ExecutionStage.DATA_COLLECTION: "データ収集・準備",
            ExecutionStage.PLOT_ANALYSIS: "プロット分析・設計",
            ExecutionStage.EPISODE_DESIGN: "エピソード設計",
            ExecutionStage.MANUSCRIPT_WRITING: "原稿執筆",
            ExecutionStage.INITIAL_WRITING: "初稿執筆",
            ExecutionStage.QUALITY_FINALIZATION: "品質チェック・仕上げ",
        }
        return display_names[self]

    @property
    def expected_turns(self) -> int:
        """予想ターン数"""
        turn_estimates: dict[ExecutionStage, int] = {
            ExecutionStage.DATA_COLLECTION: 3,
            ExecutionStage.PLOT_ANALYSIS: 3,
            ExecutionStage.EPISODE_DESIGN: 3,
            ExecutionStage.MANUSCRIPT_WRITING: 4,
            ExecutionStage.INITIAL_WRITING: 3,
            ExecutionStage.QUALITY_FINALIZATION: 3,
        }
        return turn_estimates[self]

    @property
    def max_turns(self) -> int:
        """許容される最大ターン数.

        仕様では明確に定義されていないが、ユニットテストおよび
        既存利用箇所では ``expected_turns`` の2倍を安全な上限として
        扱っているため、ここではそれに倣う。
        """

        return self.expected_turns * 2


@dataclass
class StageResult:
    """段階実行結果（簡易版）"""

    stage_name: str
    success: bool
    turns_used: int = 0
    cost_usd: float = 0.0
    output: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_success(self) -> bool:
        """実行成功判定"""
        return self.success

    @property
    def max_turns(self) -> int:
        """最大ターン数制限"""
        # 各段階の最大ターン数を予想の1.5倍に設定（安全マージン）
        return int(self.expected_turns * 1.5)


class StageExecutionStatus(Enum):
    """段階実行状態"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    EMERGENCY_FALLBACK = "emergency_fallback"


@dataclass
class StageExecutionResult:
    """段階実行結果

    SPEC-JSON-001: JSON形式STEP間橋渡しシステム対応
    structured_outputフィールドによる構造化データ連携を追加
    """

    stage: ExecutionStage
    status: StageExecutionStatus
    execution_time_ms: float = 0.0
    turns_used: int = 0
    error_message: str | None = None
    output_data: dict[str, Any] = field(default_factory=dict)
    temporary_files: list[Path] = field(default_factory=list)
    structured_output: Optional["StructuredStepOutput"] = None

    def is_success(self) -> bool:
        """実行成功判定"""
        return self.status == StageExecutionStatus.COMPLETED

    def get_output_summary(self) -> str:
        """出力データサマリー取得

        構造化出力がある場合はそちらを優先して表示
        """
        # 構造化出力がある場合はそちらを優先
        if self.structured_output:
            summary_parts = []
            summary_parts.append(f"STEP: {self.structured_output.step_id}")
            summary_parts.append(f"品質スコア: {self.structured_output.quality_metrics.overall_score:.2f}")
            summary_parts.append(f"ステータス: {self.structured_output.completion_status.value}")

            # 構造化データのサマリー
            if self.structured_output.structured_data:
                summary_parts.append(f"構造化データ: {len(self.structured_output.structured_data)}要素")

            return ", ".join(summary_parts)

        # 従来の出力データサマリー
        if not self.output_data:
            return "出力データなし"

        summary_parts = []
        for key, value in self.output_data.items():
            if isinstance(value, str):
                summary_parts.append(f"{key}: {len(value)}文字")
            elif isinstance(value, list):
                summary_parts.append(f"{key}: {len(value)}項目")
            elif isinstance(value, dict):
                summary_parts.append(f"{key}: {len(value)}要素")
            else:
                summary_parts.append(f"{key}: {type(value).__name__}")

        return ", ".join(summary_parts)

    def create_structured_output(
        self,
        step_name: str,
        structured_data: dict[str, Any],
        quality_score: float = 0.0,
    ) -> "StructuredStepOutput":
        """構造化出力作成ヘルパーメソッド

        Args:
            step_name: STEP名称
            structured_data: 構造化されたデータ
            quality_score: 品質スコア

        Returns:
            StructuredStepOutput: 作成された構造化出力
        """
        # 循環インポート回避: importlib経由で遅延ロード（PLC0415回避）
        mod = importlib.import_module("noveler.domain.value_objects.structured_step_output")
        StepCompletionStatus = mod.StepCompletionStatus
        StructuredStepOutput = mod.StructuredStepOutput

        # ステータスマッピング
        completion_status_map = {
            StageExecutionStatus.COMPLETED: StepCompletionStatus.COMPLETED,
            StageExecutionStatus.FAILED: StepCompletionStatus.FAILED,
            StageExecutionStatus.SKIPPED: StepCompletionStatus.SKIPPED,
            StageExecutionStatus.PENDING: StepCompletionStatus.PARTIAL,
            StageExecutionStatus.IN_PROGRESS: StepCompletionStatus.PARTIAL,
        }

        structured_output = StructuredStepOutput.create_from_execution_stage(
            stage=self.stage,
            structured_data=structured_data,
            quality_score=quality_score,
            completion_status=completion_status_map[self.status],
        )

        # 構造化出力を自動設定
        self.structured_output = structured_output
        return structured_output


@dataclass
class FiveStageExecutionContext:
    """5段階実行コンテキスト"""

    session_id: str
    episode_number: int
    project_root: Path
    word_count_target: int
    genre: str
    viewpoint: str
    viewpoint_character: str
    custom_requirements: list[str]

    # 段階間共有データ
    shared_data: dict[str, Any] = field(default_factory=dict)
    stage_results: dict[ExecutionStage, StageExecutionResult] = field(default_factory=dict)

    # 実行制御設定
    allow_stage_skip: bool = True
    fail_fast_mode: bool = False
    user_feedback_enabled: bool = True

    # パフォーマンス監視
    total_execution_start: datetime | None = None
    total_turns_used: int = 0
    total_cost_usd: float = 0.0

    def get_current_stage(self) -> ExecutionStage | None:
        """現在実行中の段階取得"""
        for stage in ExecutionStage:
            if stage not in self.stage_results:
                return stage

            result = self.stage_results[stage]
            if result.status == StageExecutionStatus.IN_PROGRESS:
                return stage

        return None

    def get_next_stage(self) -> ExecutionStage | None:
        """次に実行すべき段階取得"""
        current = self.get_current_stage()
        if current:
            return current

        # 完了していない最初の段階を探す
        for stage in ExecutionStage:
            if stage not in self.stage_results or not self.stage_results[stage].is_success():
                return stage

        return None

    def is_execution_complete(self) -> bool:
        """実行完了判定"""
        return all(stage in self.stage_results and self.stage_results[stage].is_success() for stage in ExecutionStage)

    def get_progress_percentage(self) -> float:
        """進捗率取得"""
        completed_stages = sum(
            1 for stage in ExecutionStage if stage in self.stage_results and self.stage_results[stage].is_success()
        )

        return (completed_stages / len(ExecutionStage)) * 100

    def add_shared_data(self, key: str, value: object) -> None:
        """共有データ追加"""
        self.shared_data[key] = value

    def get_shared_data(self, key: str, default: object = None) -> object:
        """共有データ取得"""
        return self.shared_data.get(key, default)

    def update_performance_metrics(self, turns: int, cost_usd: float) -> None:
        """パフォーマンス指標更新"""
        self.total_turns_used += turns
        self.total_cost_usd += cost_usd

    # --- 共有データ補助メソッド（executorテスト用に追加） ---

    def get_current_shared_data(self) -> dict[str, Any]:
        """共有データのスナップショットを返す"""
        return dict(self.shared_data)

    def update_shared_data(self, data: dict[str, Any]) -> None:
        """共有データをまとめて更新"""
        self.shared_data.update(data)


@dataclass
class StagePromptTemplate:
    """段階別プロンプトテンプレート"""

    stage: ExecutionStage
    template_content: str
    required_context_keys: list[str]
    output_format: str = "json"
    max_turns_override: int | None = None

    def generate_prompt(self, context: FiveStageExecutionContext) -> str:
        """コンテキストベースプロンプト生成"""
        # テンプレート変数を実際の値で置換
        prompt_vars = {
            "session_id": context.session_id,
            "episode_number": context.episode_number,
            "word_count_target": context.word_count_target,
            "genre": context.genre,
            "viewpoint": context.viewpoint,
            "viewpoint_character": context.viewpoint_character,
            "custom_requirements": "\n".join(f"- {req}" for req in context.custom_requirements),
            "stage_name": self.stage.display_name,
            "expected_turns": self.stage.expected_turns,
        }

        # 共有データからコンテキスト情報を追加
        for key in self.required_context_keys:
            prompt_vars[key] = context.get_shared_data(key, f"[{key}データが利用できません]")

        # 前段階の結果を参照可能にする
        previous_results = {}
        for prev_stage in ExecutionStage:
            if prev_stage == self.stage:
                break
            if prev_stage in context.stage_results:
                result = context.stage_results[prev_stage]
                previous_results[prev_stage.value] = {
                    "status": result.status.value,
                    "output_summary": result.get_output_summary(),
                    "turns_used": result.turns_used,
                }

        prompt_vars["previous_results"] = json.dumps(previous_results, ensure_ascii=False, indent=2)

        try:
            return self.template_content.format(**prompt_vars)
        except KeyError as e:
            message = f"テンプレート変数が不足しています: {e}"
            raise ValueError(message) from e

    def get_effective_max_turns(self) -> int:
        """実効最大ターン数取得"""
        if self.max_turns_override:
            return self.max_turns_override
        return self.stage.max_turns


@dataclass
class FiveStageWritingRequest:
    """5段階分割執筆リクエスト"""

    episode_number: int
    project_root: Path
    word_count_target: int = 3500
    genre: str = "fantasy"
    viewpoint: str = "三人称単元視点"
    viewpoint_character: str = "主人公"
    custom_requirements: list[str] = field(default_factory=list)

    # 実行制御設定
    resume_session_id: str | None = None
    skip_completed_stages: bool = True
    user_interaction_mode: bool = True

    # デバッグ・開発設定
    debug_mode: bool = False
    dry_run: bool = False
    stage_override_settings: dict[ExecutionStage, dict[str, Any]] = field(default_factory=dict)

    def create_execution_context(self) -> FiveStageExecutionContext:
        """実行コンテキスト作成"""
        session_id = self.resume_session_id or str(uuid.uuid4())

        return FiveStageExecutionContext(
            session_id=session_id,
            episode_number=self.episode_number,
            project_root=self.project_root,
            word_count_target=self.word_count_target,
            genre=self.genre,
            viewpoint=self.viewpoint,
            viewpoint_character=self.viewpoint_character,
            custom_requirements=self.custom_requirements,
            user_feedback_enabled=self.user_interaction_mode,
            total_execution_start=datetime.now(timezone.utc),
        )


@dataclass
class FiveStageWritingResponse:
    """5段階分割執筆レスポンス"""

    success: bool
    session_id: str
    stage_results: dict[ExecutionStage, StageExecutionResult]

    # 最終成果物パス
    manuscript_path: Path | None = None
    quality_report_path: Path | None = None

    # パフォーマンス指標
    total_execution_time_ms: float = 0.0
    total_turns_used: int = 0
    total_cost_usd: float = 0.0
    turns_saved_vs_single_execution: int = 0

    # エラー情報
    failed_stage: ExecutionStage | None = None
    error_message: str | None = None
    recovery_suggestions: list[str] = field(default_factory=list)

    def get_success_summary(self) -> str:
        """成功サマリー取得"""
        if not self.success:
            return f"実行失敗: {self.failed_stage.display_name if self.failed_stage else '不明'}"

        completed_stages = len([r for r in self.stage_results.values() if r.is_success()])

        return (
            f"5段階実行完了 ({completed_stages}/{len(ExecutionStage)}段階成功) - "
            f"総ターン数: {self.total_turns_used}, "
            f"実行時間: {self.total_execution_time_ms:.0f}ms, "
            f"コスト: ${self.total_cost_usd:.4f}"
        )

    def get_performance_improvement(self) -> str:
        """パフォーマンス改善メトリクス"""
        if self.turns_saved_vs_single_execution <= 0:
            return "ターン数削減効果: なし"

        reduction_rate = (
            self.turns_saved_vs_single_execution / (self.total_turns_used + self.turns_saved_vs_single_execution)
        ) * 100

        return f"ターン数削減効果: {self.turns_saved_vs_single_execution}ターン削減 ({reduction_rate:.1f}%改善)"

    def generate_execution_report(self) -> str:
        """実行レポート生成"""
        report_lines = [
            "# 5段階分割執筆実行レポート",
            "",
            f"**セッションID**: {self.session_id}",
            f"**実行結果**: {'✅ 成功' if self.success else '❌ 失敗'}",
            f"**総実行時間**: {self.total_execution_time_ms:.0f}ms",
            f"**総ターン数**: {self.total_turns_used}",
            f"**総コスト**: ${self.total_cost_usd:.4f}",
            "",
            "## 段階別実行結果",
            "",
        ]

        for stage in ExecutionStage:
            if stage in self.stage_results:
                result = self.stage_results[stage]
                status_emoji = {
                    StageExecutionStatus.COMPLETED: "✅",
                    StageExecutionStatus.FAILED: "❌",
                    StageExecutionStatus.IN_PROGRESS: "🔄",
                    StageExecutionStatus.PENDING: "⏳",
                    StageExecutionStatus.SKIPPED: "⏭️",
                }[result.status]

                report_lines.extend(
                    [
                        f"### {status_emoji} {stage.display_name}",
                        f"- **ステータス**: {result.status.value}",
                        f"- **使用ターン数**: {result.turns_used}/{stage.max_turns}",
                        f"- **実行時間**: {result.execution_time_ms:.0f}ms",
                        f"- **出力サマリー**: {result.get_output_summary()}",
                    ]
                )

                if result.error_message:
                    report_lines.append(f"- **エラー**: {result.error_message}")

                report_lines.append("")

        if self.manuscript_path:
            report_lines.extend(
                [
                    "## 成果物",
                    f"- **原稿ファイル**: {self.manuscript_path}",
                ]
            )

            if self.quality_report_path:
                report_lines.append(f"- **品質レポート**: {self.quality_report_path}")

        if not self.success and self.recovery_suggestions:
            report_lines.extend(["", "## 回復提案", *[f"- {suggestion}" for suggestion in self.recovery_suggestions]])

        return "\n".join(report_lines)
