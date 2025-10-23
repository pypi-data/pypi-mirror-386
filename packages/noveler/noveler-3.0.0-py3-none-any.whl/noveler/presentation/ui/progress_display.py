"""
進捗表示システム

18ステップ執筆システムの進捗を視覚的に表示するUI機能。
リアルタイム進捗バー、ステップ状態表示、ETA計算を提供。
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from noveler.infrastructure.performance.comprehensive_performance_optimizer import performance_monitor
from noveler.presentation.shared.shared_utilities import _get_console


def get_console():
    return _get_console()


class ProgressStatus(Enum):
    """ステップの進捗状態"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepProgress:
    """個別ステップの進捗情報"""
    step_id: int
    name: str
    status: ProgressStatus
    start_time: datetime | None = None
    end_time: datetime | None = None
    duration: float | None = None
    progress_percentage: float = 0.0
    sub_tasks: list[str] | None = None
    current_sub_task: str | None = None
    error_message: str | None = None


class ProgressDisplaySystem:
    """進捗表示システム

    18ステップ執筆システムの進捗を視覚的に表示し、
    リアルタイム更新とETA計算を提供する。
    """

    def __init__(self, episode_number: int, total_steps: int = 18) -> None:
        self.episode_number = episode_number
        self.total_steps = total_steps
        self.console = get_console()
        self.steps: dict[int, StepProgress] = {}
        self.overall_start_time = datetime.now()
        self.display_config = {
            "show_eta": True,
            "show_elapsed": True,
            "show_step_details": True,
            "animate_progress": True,
            "color_coding": True
        }

        # ステップ名の定義（18ステップシステム）
        self.step_names = {
            1: "基本情報設定",
            2: "ジャンル・テーマ設定",
            3: "キャラクター設計",
            4: "世界観構築",
            5: "プロット骨子作成",
            6: "シーン構成設計",
            7: "対話設計",
            8: "感情カーブ設計",
            9: "雰囲気・世界観描写",
            10: "伏線配置",
            11: "文章スタイル確立",
            12: "文体調整",
            13: "描写技法適用",
            14: "読みやすさ最適化",
            15: "品質チェック",
            16: "読者体験最適化",
            17: "最終調整",
            18: "完成版出力"
        }

        # 初期化
        self._initialize_steps()

    def _initialize_steps(self) -> None:
        """ステップの初期化"""
        for step_id in range(1, self.total_steps + 1):
            self.steps[step_id] = StepProgress(
                step_id=step_id,
                name=self.step_names.get(step_id, f"ステップ{step_id}"),
                status=ProgressStatus.PENDING
            )

    @performance_monitor
    def start_step(self, step_id: int, sub_tasks: list[str] | None = None) -> None:
        """ステップの開始"""
        if step_id in self.steps:
            step = self.steps[step_id]
            step.status = ProgressStatus.IN_PROGRESS
            step.start_time = datetime.now()
            step.sub_tasks = sub_tasks or []
            step.current_sub_task = sub_tasks[0] if sub_tasks else None
            step.progress_percentage = 0.0

            self._display_step_start(step)

    @performance_monitor
    def update_step_progress(
        self,
        step_id: int,
        progress: float,
        current_sub_task: str | None = None
    ) -> None:
        """ステップの進捗更新"""
        if step_id in self.steps:
            step = self.steps[step_id]
            step.progress_percentage = min(100.0, max(0.0, progress))
            if current_sub_task:
                step.current_sub_task = current_sub_task

            self._display_step_progress(step)

    @performance_monitor
    def complete_step(self, step_id: int, success: bool = True) -> None:
        """ステップの完了"""
        if step_id in self.steps:
            step = self.steps[step_id]
            step.status = ProgressStatus.COMPLETED if success else ProgressStatus.FAILED
            step.end_time = datetime.now()
            step.progress_percentage = 100.0

            if step.start_time:
                step.duration = (step.end_time - step.start_time).total_seconds()

            self._display_step_completion(step, success)

    @performance_monitor
    def fail_step(self, step_id: int, error_message: str) -> None:
        """ステップの失敗"""
        if step_id in self.steps:
            step = self.steps[step_id]
            step.status = ProgressStatus.FAILED
            step.end_time = datetime.now()
            step.error_message = error_message

            if step.start_time:
                step.duration = (step.end_time - step.start_time).total_seconds()

            self._display_step_failure(step)

    @performance_monitor
    def display_overall_progress(self) -> None:
        """全体進捗の表示"""
        completed_steps = len([s for s in self.steps.values() if s.status == ProgressStatus.COMPLETED])
        failed_steps = len([s for s in self.steps.values() if s.status == ProgressStatus.FAILED])
        in_progress_steps = len([s for s in self.steps.values() if s.status == ProgressStatus.IN_PROGRESS])

        overall_progress = (completed_steps / self.total_steps) * 100

        # 全体進捗バー
        progress_bar = self._create_progress_bar(overall_progress, width=50)

        # ETA計算
        eta_str = self._calculate_eta(completed_steps)

        # 経過時間
        elapsed = datetime.now() - self.overall_start_time
        elapsed_str = self._format_duration(elapsed.total_seconds())

        self.console.print(f"\n[bold blue]Episode {self.episode_number} 全体進捗[/bold blue]")
        self.console.print(f"{progress_bar} {overall_progress:.1f}%")
        self.console.print(f"[green]完了: {completed_steps}[/green] | [yellow]実行中: {in_progress_steps}[/yellow] | [red]失敗: {failed_steps}[/red]")
        self.console.print(f"[cyan]経過時間: {elapsed_str}[/cyan] | [magenta]ETA: {eta_str}[/magenta]")

    @performance_monitor
    def display_detailed_status(self) -> dict[str, Any]:
        """詳細ステータスの表示と返却"""
        self.console.print(f"\n[bold]Episode {self.episode_number} - 詳細ステータス[/bold]")
        self.console.print("=" * 60)

        status_data = {
            "episode_number": self.episode_number,
            "total_steps": self.total_steps,
            "steps": {},
            "summary": {
                "completed": 0,
                "failed": 0,
                "in_progress": 0,
                "pending": 0
            },
            "performance": {
                "total_elapsed": (datetime.now() - self.overall_start_time).total_seconds(),
                "average_step_duration": 0.0,
                "estimated_remaining": 0.0
            }
        }

        total_duration = 0.0
        completed_count = 0

        for step_id, step in self.steps.items():
            # ステップ情報の表示
            status_icon = self._get_status_icon(step.status)
            duration_str = f" ({self._format_duration(step.duration)})" if step.duration else ""

            self.console.print(f"{status_icon} ステップ{step_id:2d}: {step.name}{duration_str}")

            if step.current_sub_task:
                self.console.print(f"    └─ {step.current_sub_task}")

            if step.error_message:
                self.console.print(f"    [red]エラー: {step.error_message}[/red]")

            # データ収集
            status_data["steps"][step_id] = {
                "name": step.name,
                "status": step.status.value,
                "progress_percentage": step.progress_percentage,
                "duration": step.duration,
                "error_message": step.error_message
            }

            status_data["summary"][step.status.value] += 1

            if step.duration:
                total_duration += step.duration
                completed_count += 1

        # パフォーマンス統計
        if completed_count > 0:
            status_data["performance"]["average_step_duration"] = total_duration / completed_count
            remaining_steps = self.total_steps - status_data["summary"]["completed"]
            status_data["performance"]["estimated_remaining"] = (
                status_data["performance"]["average_step_duration"] * remaining_steps
            )

        return status_data

    def _display_step_start(self, step: StepProgress) -> None:
        """ステップ開始の表示"""
        self.console.print(f"\n[bold yellow]🚀 ステップ{step.step_id}: {step.name} - 開始[/bold yellow]")
        if step.sub_tasks:
            self.console.print(f"[dim]サブタスク: {', '.join(step.sub_tasks)}[/dim]")

    def _display_step_progress(self, step: StepProgress) -> None:
        """ステップ進捗の表示"""
        progress_bar = self._create_progress_bar(step.progress_percentage, width=30)
        sub_task_info = f" - {step.current_sub_task}" if step.current_sub_task else ""

        self.console.print(f"[blue]ステップ{step.step_id}[/blue] {progress_bar} {step.progress_percentage:.1f}%{sub_task_info}")

    def _display_step_completion(self, step: StepProgress, success: bool) -> None:
        """ステップ完了の表示"""
        if success:
            duration_str = f" ({self._format_duration(step.duration)})" if step.duration else ""
            self.console.print(f"[bold green]✅ ステップ{step.step_id}: {step.name} - 完了{duration_str}[/bold green]")
        else:
            self.console.print(f"[bold red]❌ ステップ{step.step_id}: {step.name} - 失敗[/bold red]")

    def _display_step_failure(self, step: StepProgress) -> None:
        """ステップ失敗の表示"""
        duration_str = f" ({self._format_duration(step.duration)})" if step.duration else ""
        self.console.print(f"[bold red]💥 ステップ{step.step_id}: {step.name} - 失敗{duration_str}[/bold red]")
        if step.error_message:
            self.console.print(f"[red]エラー詳細: {step.error_message}[/red]")

    def _create_progress_bar(self, percentage: float, width: int = 40) -> str:
        """進捗バーの作成"""
        filled = int((percentage / 100) * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}]"

    def _get_status_icon(self, status: ProgressStatus) -> str:
        """ステータスアイコンの取得"""
        icons = {
            ProgressStatus.PENDING: "⏸️ ",
            ProgressStatus.IN_PROGRESS: "⚡",
            ProgressStatus.COMPLETED: "✅",
            ProgressStatus.FAILED: "❌",
            ProgressStatus.SKIPPED: "⏭️ "
        }
        return icons.get(status, "❓")

    def _calculate_eta(self, completed_steps: int) -> str:
        """ETA（完了予定時刻）の計算"""
        if completed_steps == 0:
            return "計算中..."

        elapsed = datetime.now() - self.overall_start_time
        average_time_per_step = elapsed.total_seconds() / completed_steps
        remaining_steps = self.total_steps - completed_steps

        if remaining_steps <= 0:
            return "完了"

        estimated_remaining = timedelta(seconds=average_time_per_step * remaining_steps)
        eta = datetime.now() + estimated_remaining

        return eta.strftime("%H:%M:%S")

    def _format_duration(self, seconds: float | None) -> str:
        """時間のフォーマット"""
        if seconds is None:
            return "N/A"

        if seconds < 60:
            return f"{seconds:.1f}秒"
        if seconds < 3600:
            return f"{seconds/60:.1f}分"
        return f"{seconds/3600:.1f}時間"

    def export_progress_report(self) -> dict[str, Any]:
        """進捗レポートのエクスポート"""
        return {
            "episode_number": self.episode_number,
            "timestamp": datetime.now().isoformat(),
            "overall_progress": (len([s for s in self.steps.values() if s.status == ProgressStatus.COMPLETED]) / self.total_steps) * 100,
            "total_elapsed": (datetime.now() - self.overall_start_time).total_seconds(),
            "steps": {
                step_id: {
                    "name": step.name,
                    "status": step.status.value,
                    "duration": step.duration,
                    "progress_percentage": step.progress_percentage,
                    "error_message": step.error_message
                }
                for step_id, step in self.steps.items()
            },
            "performance_metrics": {
                "completed_steps": len([s for s in self.steps.values() if s.status == ProgressStatus.COMPLETED]),
                "failed_steps": len([s for s in self.steps.values() if s.status == ProgressStatus.FAILED]),
                "average_step_duration": sum(s.duration for s in self.steps.values() if s.duration) / max(1, len([s for s in self.steps.values() if s.duration])),
            }
        }
