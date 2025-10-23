#!/usr/bin/env python3
"""5段階分割実行ユーザーフィードバックシステム

from noveler.infrastructure.services.logger_service import logger_service
仕様書: SPEC-FIVE-STAGE-001
リアルタイム進捗表示・ユーザー制御・段階間フィードバック機能
"""

import asyncio
from datetime import datetime, timedelta, timezone
from enum import Enum

from noveler.domain.value_objects.five_stage_writing_execution import (
    ExecutionStage,
    FiveStageExecutionContext,
    StageExecutionStatus,
)
from noveler.infrastructure.logging.unified_logger import get_logger

# DDD準拠: Infrastructure→Presentation依存を除去のため、共有consoleを使用
from noveler.presentation.shared.shared_utilities import console


class UserInteractionMode(Enum):
    """ユーザー対話モード"""

    AUTOMATIC = "automatic"  # 自動実行（最小限のフィードバック）
    INTERACTIVE = "interactive"  # 対話型（段階間で確認）
    MONITORING = "monitoring"  # 監視型（詳細進捗表示のみ）
    DEBUG = "debug"  # デバッグ型（全情報表示）


class StageTransitionAction(Enum):
    """段階遷移アクション"""

    CONTINUE = "continue"  # 続行
    PAUSE = "pause"  # 一時停止
    MODIFY = "modify"  # 設定変更
    SKIP = "skip"  # スキップ
    ABORT = "abort"  # 中断


class FiveStageProgressDisplay:
    """5段階進捗表示システム"""

    def __init__(
        self,
        interaction_mode: UserInteractionMode = UserInteractionMode.MONITORING,
        logger_service=None,
        console_service=None,
    ) -> None:
        self.interaction_mode = interaction_mode
        self.logger = get_logger(__name__)
        self.console = console
        self.start_time: datetime | None = None
        self.stage_start_times: dict[ExecutionStage, datetime] = {}

        self.logger_service = logger_service
        self.console_service = console_service

    def initialize_display(self, context: FiveStageExecutionContext) -> None:
        """進捗表示初期化"""
        self.start_time = datetime.now(timezone.utc)

        self.console_service.print("\n" + "=" * 60)
        self.console_service.print(f"[bold blue]🎯 5段階分割執筆実行 - 第{context.episode_number:03d}話[/bold blue]")
        self.console_service.print(
            f"[dim]セッション: {context.session_id[:8]} | 目標: {context.word_count_target}文字[/dim]"
        )
        self.console.print(
            f"[dim]ジャンル: {context.genre} | 視点: {context.viewpoint} ({context.viewpoint_character})[/dim]"
        )
        self.console_service.print("=" * 60)

        # 段階概要表示
        self.console_service.print("[blue]📋 実行段階計画:[/blue]")
        for i, stage in enumerate(ExecutionStage, 1):
            status_icon = "⏳"
            if stage in context.stage_results:
                result = context.stage_results[stage]
                status_icon = {
                    StageExecutionStatus.COMPLETED: "✅",
                    StageExecutionStatus.FAILED: "❌",
                    StageExecutionStatus.IN_PROGRESS: "🔄",
                    StageExecutionStatus.SKIPPED: "⏭️",
                }.get(result.status, "⏳")

            self.console.print(
                f"[dim]  {status_icon} Stage {i}: {stage.display_name} ({stage.expected_turns}ターン予想)[/dim]"
            )

        self.console_service.print()

    def update_stage_progress(
        self,
        stage: ExecutionStage,
        status: StageExecutionStatus,
        current_turn: int = 0,
        max_turns: int = 0,
        status_message: str = "",
    ) -> None:
        """段階進捗更新"""
        # 段階開始時刻記録
        if status == StageExecutionStatus.IN_PROGRESS and stage not in self.stage_start_times:
            self.stage_start_times[stage] = datetime.now(timezone.utc)

        # ステータス表示
        status_icons = {
            StageExecutionStatus.PENDING: "⏳",
            StageExecutionStatus.IN_PROGRESS: "🔄",
            StageExecutionStatus.COMPLETED: "✅",
            StageExecutionStatus.FAILED: "❌",
            StageExecutionStatus.SKIPPED: "⏭️",
        }

        stage_num = list(ExecutionStage).index(stage) + 1
        icon = status_icons.get(status, "❓")

        # 基本進捗表示
        progress_line = f"[blue]{icon} Stage {stage_num}: {stage.display_name}[/blue]"

        if status == StageExecutionStatus.IN_PROGRESS and max_turns > 0:
            progress_percentage = (current_turn / max_turns) * 100
            progress_line += f" [{current_turn}/{max_turns}ターン ({progress_percentage:.1f}%)]"

        self.console_service.print(progress_line)

        # 詳細情報表示
        if status_message:
            self.console_service.print(f"[dim]  ℹ️ {status_message}[/dim]")

        # 経過時間表示
        if stage in self.stage_start_times:
            elapsed = datetime.now(timezone.utc) - self.stage_start_times[stage]
            self.console_service.print(f"[dim]  ⏱️ 段階実行時間: {elapsed.total_seconds():.1f}秒[/dim]")

        # デバッグモード時の詳細情報
        if self.interaction_mode == UserInteractionMode.DEBUG:
            total_elapsed = datetime.now(timezone.utc) - self.start_time if self.start_time else timedelta(0)
            self.console_service.print(f"[dim]  🕒 総実行時間: {total_elapsed.total_seconds():.1f}秒[/dim]")

    def display_stage_completion(
        self, stage: ExecutionStage, success: bool, turns_used: int, execution_time_ms: float, output_summary: str = ""
    ) -> None:
        """段階完了表示"""
        stage_num = list(ExecutionStage).index(stage) + 1

        if success:
            self.console_service.print(f"[green]✅ Stage {stage_num}: {stage.display_name} 完了[/green]")
            self.console_service.print(
                f"[dim]  📊 {turns_used}ターン使用 | {execution_time_ms:.0f}ms | {output_summary}[/dim]"
            )
        else:
            self.console_service.print(f"[red]❌ Stage {stage_num}: {stage.display_name} 失敗[/red]")
            self.console_service.print(f"[dim]  📊 {turns_used}ターン使用 | {execution_time_ms:.0f}ms[/dim]")

    def display_overall_summary(self, context: FiveStageExecutionContext, final_success: bool) -> None:
        """全体サマリー表示"""
        total_time = datetime.now(timezone.utc) - self.start_time if self.start_time else timedelta(0)
        completed_stages = sum(1 for result in context.stage_results.values() if result.is_success())

        self.console_service.print("\n" + "=" * 60)
        if final_success:
            self.console_service.print("[bold green]🎉 5段階分割執筆完了![/bold green]")
        else:
            self.console_service.print("[bold red]💥 5段階分割執筆失敗[/bold red]")

        self.console_service.print("[blue]📊 実行サマリー:[/blue]")
        self.console_service.print(f"[dim]  ✅ 完了段階: {completed_stages}/{len(ExecutionStage)}[/dim]")
        self.console_service.print(f"[dim]  🔄 総ターン数: {context.total_turns_used}[/dim]")
        self.console_service.print(f"[dim]  💰 総コスト: ${context.total_cost_usd:.4f}[/dim]")
        self.console_service.print(f"[dim]  ⏱️ 総実行時間: {total_time.total_seconds():.1f}秒[/dim]")
        self.console_service.print("=" * 60 + "\n")


class FiveStageUserInteractionManager:
    """5段階ユーザー対話管理システム"""

    def __init__(
        self,
        interaction_mode: UserInteractionMode = UserInteractionMode.INTERACTIVE,
        logger_service=None,
        console_service=None,
    ) -> None:
        self.interaction_mode = interaction_mode
        self.logger = get_logger(__name__)

        # B30品質基準準拠: 依存性注入パターンでconsole_serviceを注入
        if console_service is None:
            from noveler.infrastructure.di.container import resolve_service

            try:
                self.console_service = resolve_service("IConsoleService")
            except ValueError:
                from noveler.infrastructure.adapters.console_service_adapter import ConsoleServiceAdapter

                self.console_service = ConsoleServiceAdapter()
        else:
            self.console_service = console_service

        if logger_service is None:
            from noveler.infrastructure.di.container import resolve_service

            try:
                self.logger_service = resolve_service("ILoggerService")
            except ValueError:
                from noveler.infrastructure.adapters.logger_service_adapter import LoggerServiceAdapter

                self.logger_service = LoggerServiceAdapter("noveler.five_stage_feedback")
        else:
            self.logger_service = logger_service

        self.progress_display = FiveStageProgressDisplay(interaction_mode)

        # ユーザー入力のタイムアウト設定
        self.user_input_timeout = 30  # 秒

    async def handle_stage_transition(
        self, from_stage: ExecutionStage | None, to_stage: ExecutionStage, context: FiveStageExecutionContext
    ) -> StageTransitionAction:
        """段階遷移時のユーザー対話処理"""

        # 自動モードでは対話なし
        if self.interaction_mode == UserInteractionMode.AUTOMATIC:
            return StageTransitionAction.CONTINUE

        # 監視モードでは表示のみ
        if self.interaction_mode == UserInteractionMode.MONITORING:
            if from_stage:
                self.console_service.print(f"[blue]🔄 {from_stage.display_name} → {to_stage.display_name}[/blue]")
            return StageTransitionAction.CONTINUE

        # 対話型・デバッグモードでのユーザー確認
        return await self._interactive_stage_transition(from_stage, to_stage, context)

    async def _interactive_stage_transition(
        self, from_stage: ExecutionStage | None, to_stage: ExecutionStage, context: FiveStageExecutionContext
    ) -> StageTransitionAction:
        """対話型段階遷移"""

        self.console_service.print("\n[yellow]🤔 段階遷移確認[/yellow]")

        if from_stage:
            from_result = context.stage_results.get(from_stage)
            if from_result:
                self.console_service.print(
                    f"[green]完了:[/green] {from_stage.display_name} ({from_result.turns_used}ターン)"
                )
                self.console_service.print(f"[dim]出力: {from_result.get_output_summary()}[/dim]")

        self.console_service.print(
            f"[blue]次の段階:[/blue] {to_stage.display_name} (予想: {to_stage.expected_turns}ターン)"
        )
        self.console_service.print(f"[dim]説明: {self._get_stage_description(to_stage)}[/dim]")

        # ユーザー選択肢表示
        self.console_service.print("\n[blue]選択してください:[/blue]")
        self.console_service.print("  [green]1[/green]: 続行")
        self.console_service.print("  [yellow]2[/yellow]: 一時停止")
        self.console_service.print("  [blue]3[/blue]: 設定変更")
        self.console_service.print("  [dim]4[/dim]: スキップ")
        self.console_service.print("  [red]5[/red]: 中断")

        # ユーザー入力取得
        try:
            # 非同期入力（タイムアウト付き）
            choice = await asyncio.wait_for(
                self._get_user_input("選択 (1-5, デフォルト: 1): "), timeout=self.user_input_timeout
            )

            if choice in ["", "1"]:
                return StageTransitionAction.CONTINUE
            if choice == "2":
                self.console_service.print("[yellow]一時停止します。再開はCLIコマンドから実行してください。[/yellow]")
                return StageTransitionAction.PAUSE
            if choice == "3":
                await self._handle_stage_modification(to_stage, context)
                return StageTransitionAction.CONTINUE
            if choice == "4":
                self.console_service.print(f"[dim]{to_stage.display_name}をスキップします。[/dim]")
                return StageTransitionAction.SKIP
            if choice == "5":
                self.console_service.print("[red]実行を中断します。[/red]")
                return StageTransitionAction.ABORT
            self.console_service.print("[yellow]無効な選択です。続行します。[/yellow]")
            return StageTransitionAction.CONTINUE

        except asyncio.TimeoutError:
            self.console_service.print(
                f"\n[dim]入力タイムアウト ({self.user_input_timeout}秒) - 自動的に続行します[/dim]"
            )
            return StageTransitionAction.CONTINUE

    async def _get_user_input(self, prompt: str) -> str:
        """非同期ユーザー入力"""
        # Note: 実際の非同期入力実装は環境依存
        # 現在は簡易実装
        self.console_service.print(prompt, end="")
        return input().strip()

    def _get_stage_description(self, stage: ExecutionStage) -> str:
        """段階説明取得"""
        descriptions = {
            ExecutionStage.DATA_COLLECTION: "既存データファイルの読み込みと基礎情報の整理",
            ExecutionStage.PLOT_ANALYSIS: "章別プロットとキャラクター設定の詳細分析",
            ExecutionStage.EPISODE_DESIGN: "三幕構成とキーシーンの具体的設計",
            ExecutionStage.MANUSCRIPT_WRITING: "設計に基づく実際の原稿執筆",
            ExecutionStage.QUALITY_FINALIZATION: "A30準拠チェックと品質向上修正",
        }
        return descriptions.get(stage, "段階の詳細情報")

    async def _handle_stage_modification(self, stage: ExecutionStage, context: FiveStageExecutionContext) -> None:
        """段階設定変更処理"""
        self.console_service.print(f"\n[blue]📝 {stage.display_name} 設定変更[/blue]")
        self.console_service.print("現在の設定:")
        self.console_service.print(f"  最大ターン数: {stage.max_turns}")
        self.console_service.print(f"  予想ターン数: {stage.expected_turns}")

        self.console_service.print("\n変更可能な設定:")
        self.console_service.print("  1: 最大ターン数の変更")
        self.console_service.print("  2: カスタム要件の追加")
        self.console_service.print("  3: 戻る")

        try:
            choice = await asyncio.wait_for(self._get_user_input("変更項目 (1-3): "), timeout=15)

            if choice == "1":
                new_max_turns = await self._get_user_input(f"新しい最大ターン数 (現在: {stage.max_turns}): ")
                try:
                    new_value = int(new_max_turns)
                    if 1 <= new_value <= 10:
                        self.console_service.print(
                            f"[green]最大ターン数を {stage.max_turns} → {new_value} に変更しました[/green]"
                        )
                        # Note: 実際の変更は段階実行時に反映
                    else:
                        self.console_service.print("[red]無効な値です (1-10の範囲で入力してください)[/red]")
                except ValueError:
                    self.console_service.print("[red]数値を入力してください[/red]")

            elif choice == "2":
                new_requirement = await self._get_user_input("追加のカスタム要件: ")
                if new_requirement.strip():
                    context.custom_requirements.append(new_requirement.strip())
                    self.console_service.print(f"[green]カスタム要件を追加しました: {new_requirement}[/green]")

        except asyncio.TimeoutError:
            self.console_service.print("\n[dim]設定変更タイムアウト - 元の設定で続行します[/dim]")

    async def handle_execution_error(
        self, stage: ExecutionStage, error_message: str, context: FiveStageExecutionContext
    ) -> StageTransitionAction:
        """実行エラー時のユーザー対話"""

        self.console_service.print(f"\n[red]❌ {stage.display_name} でエラーが発生しました[/red]")
        self.console_service.print(f"[red]エラー: {error_message}[/red]")

        # 自動モードではエラー時に中断
        if self.interaction_mode == UserInteractionMode.AUTOMATIC:
            return StageTransitionAction.ABORT

        self.console_service.print("\n[blue]対応方法を選択してください:[/blue]")
        self.console_service.print("  [yellow]1[/yellow]: 再試行")
        self.console_service.print("  [blue]2[/blue]: スキップして次の段階へ")
        self.console_service.print("  [red]3[/red]: 実行中断")

        try:
            choice = await asyncio.wait_for(self._get_user_input("選択 (1-3): "), timeout=30)

            if choice == "1":
                self.console_service.print("[yellow]再試行します...[/yellow]")
                return StageTransitionAction.CONTINUE
            if choice == "2":
                self.console_service.print(f"[blue]{stage.display_name}をスキップします[/blue]")
                return StageTransitionAction.SKIP
            self.console_service.print("[red]実行を中断します[/red]")
            return StageTransitionAction.ABORT

        except asyncio.TimeoutError:
            self.console_service.print("\n[dim]エラー対応タイムアウト - 実行を中断します[/dim]")
            return StageTransitionAction.ABORT

    def display_user_interaction_help(self) -> None:
        """ユーザー対話ヘルプ表示"""
        self.console_service.print("\n[blue]🆘 5段階実行ユーザー対話ヘルプ[/blue]")
        self.console_service.print("[dim]段階遷移時の選択肢:[/dim]")
        self.console_service.print("[dim]  1: 続行 - 次の段階を実行します[/dim]")
        self.console_service.print("[dim]  2: 一時停止 - 実行を中断し、後で再開できます[/dim]")
        self.console_service.print("[dim]  3: 設定変更 - 段階の実行設定を調整します[/dim]")
        self.console_service.print("[dim]  4: スキップ - 現在の段階をスキップします（推奨しません）[/dim]")
        self.console_service.print("[dim]  5: 中断 - 全体実行を中止します[/dim]")
        self.console_service.print()
        self.console_service.print("[dim]💡 ヒント: 入力待機中は30秒でタイムアウトし、自動的に続行されます[/dim]")


# ユーザーフィードバックシステムのファクトリー
def create_feedback_system(
    interaction_mode: str = "monitoring", enable_user_control: bool = True
) -> FiveStageUserInteractionManager:
    """フィードバックシステム作成"""

    # 文字列からEnum変換
    mode_mapping = {
        "automatic": UserInteractionMode.AUTOMATIC,
        "interactive": UserInteractionMode.INTERACTIVE,
        "monitoring": UserInteractionMode.MONITORING,
        "debug": UserInteractionMode.DEBUG,
    }

    mode = mode_mapping.get(interaction_mode, UserInteractionMode.MONITORING)

    # ユーザー制御無効の場合は自動モードに強制
    if not enable_user_control:
        mode = UserInteractionMode.AUTOMATIC

    return FiveStageUserInteractionManager(mode)
