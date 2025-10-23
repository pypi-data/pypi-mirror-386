"""
バッチ処理システム

複数エピソードの一括処理機能を提供。
並列実行、進捗監視、エラーハンドリングを統合したバッチ執筆システム。
"""

import asyncio
import json
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from noveler.infrastructure.factories.progressive_write_llm_executor_factory import (
    create_progressive_write_llm_executor,
)
from noveler.infrastructure.factories.progressive_write_manager_factory import (
    create_progressive_write_manager,
)
from noveler.infrastructure.logging.unified_logger import get_logger
from noveler.presentation.shared.shared_utilities import _get_console
from noveler.infrastructure.performance.comprehensive_performance_optimizer import performance_monitor
from noveler.presentation.ui.feedback_system import InteractiveFeedbackSystem
from noveler.presentation.ui.progress_display import ProgressDisplaySystem


def get_console():
    return _get_console()


@dataclass
class BatchJob:
    """バッチジョブ定義"""
    job_id: str
    episode_numbers: list[int]
    step_ids: list[int]
    priority: int = 0
    max_concurrent: int = 3
    timeout_minutes: int = 120
    retry_count: int = 3
    created_at: datetime | None = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class BatchResult:
    """バッチ実行結果"""
    job_id: str
    total_episodes: int
    successful_episodes: int
    failed_episodes: int
    total_steps: int
    successful_steps: int
    failed_steps: int
    execution_time: float
    start_time: datetime
    end_time: datetime
    detailed_results: dict[int, dict[str, Any]]
    errors: list[dict[str, Any]]


class BatchProcessingSystem:
    """バッチ処理システム

    複数エピソードの18ステップ執筆システムを効率的に並列実行し、
    統合された進捗監視とエラーハンドリングを提供する。
    """

    def __init__(self, project_root: str) -> None:
        self.project_root = Path(project_root)
        self.console = get_console()
        self.logger = get_logger(__name__)

        # 実行中のジョブ管理
        self.active_jobs: dict[str, BatchJob] = {}
        self.job_results: dict[str, BatchResult] = {}

        # 並列実行制御
        self.max_global_concurrent = 5
        self.executor = ThreadPoolExecutor(max_workers=self.max_global_concurrent)

        # 統計情報
        self.stats = {
            "total_jobs_executed": 0,
            "total_episodes_processed": 0,
            "total_execution_time": 0.0,
            "average_episode_time": 0.0,
            "success_rate": 0.0
        }

    @performance_monitor
    def create_batch_job(
        self,
        episode_numbers: list[int],
        step_ids: list[int] | None = None,
        job_name: str | None = None,
        max_concurrent: int = 3,
        priority: int = 0
    ) -> str:
        """バッチジョブを作成

        Args:
            episode_numbers: 処理するエピソード番号のリスト
            step_ids: 実行するステップID（None の場合は全ステップ）
            job_name: ジョブ名（自動生成される場合はNone）
            max_concurrent: 最大同時実行数
            priority: 優先度（高いほど先に実行）

        Returns:
            作成されたジョブID
        """
        # ジョブIDとステップIDの設定
        job_id = job_name or f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(episode_numbers)}eps"
        step_ids = step_ids or list(range(1, 19))  # 全18ステップ

        # バッチジョブの作成
        batch_job = BatchJob(
            job_id=job_id,
            episode_numbers=episode_numbers,
            step_ids=step_ids,
            priority=priority,
            max_concurrent=max_concurrent,
            created_at=datetime.now()
        )

        self.active_jobs[job_id] = batch_job

        self.console.print("[bold green]バッチジョブ作成完了[/bold green]")
        self.console.print(f"ジョブID: {job_id}")
        self.console.print(f"対象エピソード: {len(episode_numbers)}件 ({min(episode_numbers)}-{max(episode_numbers)})")
        self.console.print(f"実行ステップ: {len(step_ids)}ステップ")
        self.console.print(f"最大同時実行: {max_concurrent}")

        return job_id

    @performance_monitor
    async def execute_batch_job(self, job_id: str, callback: Callable | None = None) -> BatchResult:
        """バッチジョブを実行

        Args:
            job_id: 実行するジョブID
            callback: 進捗コールバック関数

        Returns:
            バッチ実行結果

        Raises:
            ValueError: 存在しないジョブIDの場合
        """
        if job_id not in self.active_jobs:
            msg = f"バッチジョブが見つかりません: {job_id}"
            raise ValueError(msg)

        batch_job = self.active_jobs[job_id]
        start_time = datetime.now()

        self.console.print(f"\n[bold blue]バッチジョブ実行開始: {job_id}[/bold blue]")

        # 全体進捗表示システム
        len(batch_job.episode_numbers) * len(batch_job.step_ids)

        # 実行結果の初期化
        detailed_results = {}
        errors = []
        successful_episodes = 0
        failed_episodes = 0
        successful_steps = 0
        failed_steps = 0

        try:
            # 並列実行用セマフォ
            semaphore = asyncio.Semaphore(batch_job.max_concurrent)

            async def process_episode(episode_number: int) -> dict[str, Any]:
                """単一エピソードの処理"""
                async with semaphore:
                    return await self._process_single_episode(
                        episode_number,
                        batch_job.step_ids,
                        job_id,
                        callback
                    )

            # 全エピソードを並列実行
            tasks = [process_episode(ep) for ep in batch_job.episode_numbers]

            # 進捗監視付きで実行
            completed_tasks = 0
            for coroutine in asyncio.as_completed(tasks):
                try:
                    episode_result = await coroutine
                    episode_number = episode_result["episode_number"]

                    detailed_results[episode_number] = episode_result

                    if episode_result["success"]:
                        successful_episodes += 1
                        successful_steps += episode_result["successful_steps"]
                    else:
                        failed_episodes += 1
                        errors.extend(episode_result.get("errors", []))

                    failed_steps += episode_result.get("failed_steps", 0)
                    completed_tasks += 1

                    # 進捗報告
                    progress = (completed_tasks / len(batch_job.episode_numbers)) * 100
                    self.console.print(f"[cyan]進捗: {completed_tasks}/{len(batch_job.episode_numbers)} ({progress:.1f}%) - Episode {episode_number}[/cyan]")

                    if callback:
                        callback({
                            "type": "episode_completed",
                            "episode_number": episode_number,
                            "progress": progress,
                            "successful_episodes": successful_episodes,
                            "failed_episodes": failed_episodes
                        })

                except Exception as e:
                    self.logger.exception(f"エピソード処理中にエラー: {e}")
                    errors.append({
                        "type": "episode_error",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })

        except Exception as e:
            self.logger.exception(f"バッチジョブ実行中にエラー: {e}")
            errors.append({
                "type": "batch_error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

        # 実行時間計算
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        # 結果の作成
        batch_result = BatchResult(
            job_id=job_id,
            total_episodes=len(batch_job.episode_numbers),
            successful_episodes=successful_episodes,
            failed_episodes=failed_episodes,
            total_steps=len(batch_job.episode_numbers) * len(batch_job.step_ids),
            successful_steps=successful_steps,
            failed_steps=failed_steps,
            execution_time=execution_time,
            start_time=start_time,
            end_time=end_time,
            detailed_results=detailed_results,
            errors=errors
        )

        # 結果の保存
        self.job_results[job_id] = batch_result
        self._update_statistics(batch_result)

        # 結果表示
        self._display_batch_result(batch_result)

        # ジョブ完了
        self.active_jobs.pop(job_id, None)

        return batch_result

    async def _process_single_episode(
        self,
        episode_number: int,
        step_ids: list[int],
        job_id: str,
        callback: Callable | None = None
    ) -> dict[str, Any]:
        """単一エピソードの処理"""
        start_time = time.time()

        try:
            # ProgressiveWriteManagerの初期化
            write_manager = create_progressive_write_manager(
                self.project_root,
                episode_number,
                llm_executor=create_progressive_write_llm_executor(),
            )

            # 進捗表示（エピソード単位）
            progress_display = ProgressDisplaySystem(episode_number, total_steps=len(step_ids))
            feedback_system = InteractiveFeedbackSystem(episode_number)

            # バッチモード設定（自動確認無効）
            feedback_system.set_user_preferences({
                "interactive_mode": False,
                "auto_confirm_low_risk": True
            })

            successful_steps = 0
            failed_steps = 0
            step_results = {}
            step_errors = []

            # 各ステップを順次実行
            for step_id in step_ids:
                try:
                    progress_display.start_step(step_id)

                    # ステップ実行（ドライランなし）
                    result = await write_manager.execute_writing_step_async(step_id, dry_run=False)

                    if result.get("success", False):
                        successful_steps += 1
                        progress_display.complete_step(step_id, success=True)
                        step_results[step_id] = result
                    else:
                        failed_steps += 1
                        error_msg = result.get("error", "不明なエラー")
                        progress_display.fail_step(step_id, error_msg)
                        step_errors.append({
                            "step_id": step_id,
                            "error": error_msg,
                            "episode_number": episode_number
                        })

                    if callback:
                        callback({
                            "type": "step_completed",
                            "episode_number": episode_number,
                            "step_id": step_id,
                            "success": result.get("success", False)
                        })

                except Exception as e:
                    failed_steps += 1
                    error_msg = f"ステップ{step_id}実行エラー: {e!s}"
                    progress_display.fail_step(step_id, error_msg)
                    step_errors.append({
                        "step_id": step_id,
                        "error": error_msg,
                        "episode_number": episode_number
                    })

                    self.logger.warning(f"Episode {episode_number}, Step {step_id} failed: {e}")

            execution_time = time.time() - start_time
            success = failed_steps == 0

            return {
                "episode_number": episode_number,
                "success": success,
                "successful_steps": successful_steps,
                "failed_steps": failed_steps,
                "execution_time": execution_time,
                "step_results": step_results,
                "errors": step_errors,
                "progress_report": progress_display.export_progress_report(),
                "feedback_report": feedback_system.export_feedback_report()
            }

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Episode {episode_number} processing error: {e!s}"
            self.logger.exception(error_msg)

            return {
                "episode_number": episode_number,
                "success": False,
                "successful_steps": 0,
                "failed_steps": len(step_ids),
                "execution_time": execution_time,
                "step_results": {},
                "errors": [{
                    "step_id": None,
                    "error": error_msg,
                    "episode_number": episode_number
                }]
            }

    def _display_batch_result(self, result: BatchResult) -> None:
        """バッチ実行結果の表示"""
        self.console.print(f"\n[bold green]バッチジョブ完了: {result.job_id}[/bold green]")
        self.console.print("=" * 60)

        # サマリー
        success_rate = (result.successful_episodes / result.total_episodes) * 100
        step_success_rate = (result.successful_steps / result.total_steps) * 100

        self.console.print("[bold]実行サマリー[/bold]")
        self.console.print(f"  エピソード: {result.successful_episodes}/{result.total_episodes} 成功 ({success_rate:.1f}%)")
        self.console.print(f"  ステップ: {result.successful_steps}/{result.total_steps} 成功 ({step_success_rate:.1f}%)")
        self.console.print(f"  実行時間: {result.execution_time:.1f}秒 ({result.execution_time/60:.1f}分)")

        # 平均時間
        avg_episode_time = result.execution_time / result.total_episodes
        self.console.print(f"  平均エピソード時間: {avg_episode_time:.1f}秒")

        # エラー詳細
        if result.errors:
            self.console.print(f"\n[red]エラー詳細 ({len(result.errors)}件)[/red]")
            for error in result.errors[:5]:  # 最初の5件のみ表示
                self.console.print(f"  • {error.get('error', '不明なエラー')}")
            if len(result.errors) > 5:
                self.console.print(f"  ... 他 {len(result.errors)-5} 件のエラー")

        # パフォーマンス統計
        self.console.print("\n[blue]パフォーマンス統計[/blue]")
        time_saved = self._estimate_time_saved(result)
        if time_saved > 0:
            self.console.print(f"  推定時間短縮: {time_saved:.1f}分 (並列処理効果)")

        self.console.print(f"  並列処理効率: {self._calculate_parallel_efficiency(result):.1f}%")

    def _estimate_time_saved(self, result: BatchResult) -> float:
        """並列処理による推定時間短縮を計算"""
        # 単純な推定：シーケンシャル実行時間 - 実際の実行時間
        estimated_sequential_time = result.total_episodes * 15 * 60  # 15分/エピソード想定
        time_saved_seconds = estimated_sequential_time - result.execution_time
        return max(0, time_saved_seconds / 60)  # 分で返す

    def _calculate_parallel_efficiency(self, result: BatchResult) -> float:
        """並列処理効率を計算"""
        if result.total_episodes <= 1:
            return 100.0

        ideal_time = result.execution_time / result.total_episodes
        actual_avg_time = result.execution_time / max(1, result.successful_episodes)

        return min(100.0, (ideal_time / actual_avg_time) * 100)

    def _update_statistics(self, result: BatchResult) -> None:
        """統計情報の更新"""
        self.stats["total_jobs_executed"] += 1
        self.stats["total_episodes_processed"] += result.total_episodes
        self.stats["total_execution_time"] += result.execution_time

        # 平均時間の更新
        if self.stats["total_episodes_processed"] > 0:
            self.stats["average_episode_time"] = (
                self.stats["total_execution_time"] / self.stats["total_episodes_processed"]
            )

        # 成功率の更新
        total_successful = sum(r.successful_episodes for r in self.job_results.values())
        total_episodes = sum(r.total_episodes for r in self.job_results.values())

        if total_episodes > 0:
            self.stats["success_rate"] = (total_successful / total_episodes) * 100

    @performance_monitor
    def get_batch_status(self, job_id: str | None = None) -> dict[str, Any]:
        """バッチ処理状況の取得"""
        if job_id:
            # 特定ジョブの状況
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
                return {
                    "job_id": job_id,
                    "status": "active",
                    "episode_count": len(job.episode_numbers),
                    "step_count": len(job.step_ids),
                    "created_at": job.created_at.isoformat(),
                    "max_concurrent": job.max_concurrent
                }
            if job_id in self.job_results:
                result = self.job_results[job_id]
                return {
                    "job_id": job_id,
                    "status": "completed",
                    "result": {
                        "total_episodes": result.total_episodes,
                        "successful_episodes": result.successful_episodes,
                        "execution_time": result.execution_time,
                        "success_rate": (result.successful_episodes / result.total_episodes) * 100
                    }
                }
            return {"error": f"ジョブが見つかりません: {job_id}"}

        # 全体状況
        return {
            "active_jobs": len(self.active_jobs),
            "completed_jobs": len(self.job_results),
            "statistics": self.stats,
            "active_job_list": list(self.active_jobs.keys()),
            "completed_job_list": list(self.job_results.keys())
        }

    @performance_monitor
    def cancel_batch_job(self, job_id: str) -> bool:
        """バッチジョブのキャンセル"""
        if job_id in self.active_jobs:
            self.active_jobs.pop(job_id)
            self.console.print(f"[yellow]バッチジョブをキャンセルしました: {job_id}[/yellow]")
            return True
        return False

    def export_batch_report(self, job_id: str, format: str = "json") -> str | None:
        """バッチ実行レポートのエクスポート"""
        if job_id not in self.job_results:
            return None

        result = self.job_results[job_id]

        if format == "json":
            report = {
                "job_id": job_id,
                "summary": {
                    "total_episodes": result.total_episodes,
                    "successful_episodes": result.successful_episodes,
                    "success_rate": (result.successful_episodes / result.total_episodes) * 100,
                    "execution_time": result.execution_time,
                    "start_time": result.start_time.isoformat(),
                    "end_time": result.end_time.isoformat()
                },
                "detailed_results": result.detailed_results,
                "errors": result.errors
            }
            return json.dumps(report, indent=2, ensure_ascii=False)

        return None

    def cleanup(self) -> None:
        """リソースのクリーンアップ"""
        self.executor.shutdown(wait=True)
        self.console.print("[dim]バッチ処理システムをクリーンアップしました[/dim]")
