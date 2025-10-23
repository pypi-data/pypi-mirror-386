#!/usr/bin/env python3

"""Application.use_cases.a31_batch_auto_fix_use_case
Where: Application use case driving batch A31 checklist remediation.
What: Validates episodes, coordinates sequential/parallel fixes, and aggregates results.
Why: Automates large-scale A31 quality enforcement while providing run metrics.
"""

from __future__ import annotations


import time
from dataclasses import dataclass

from noveler.application.base.abstract_use_case import AbstractUseCase
from noveler.domain.entities.a31_complete_evaluation_engine import (
    A31CompleteCheckRequest,
    A31CompleteCheckResponse,
    A31EvaluationCategory,
)
from noveler.infrastructure.logging.unified_logger import get_logger


@dataclass
class A31BatchRequest:
    """Request payload for batch A31 auto-fix operations."""

    project_name: str
    episode_numbers: list[int]
    target_categories: list[A31EvaluationCategory] = None
    include_auto_fix: bool = True
    fix_level: str = "safe"
    max_parallel_jobs: int = 3
    stop_on_error: bool = False

    def __post_init__(self) -> None:
        if self.target_categories is None:
            self.target_categories = list(A31EvaluationCategory)

        if not self.episode_numbers:
            msg = "エピソード番号リストが空です"
            raise ValueError(msg)

@dataclass
class A31BatchResponse:
    """Response payload returned after completing batch processing."""

    success: bool
    project_name: str
    total_episodes: int
    processed_episodes: int
    successful_episodes: int
    failed_episodes: int
    episode_responses: dict[int, A31CompleteCheckResponse]
    execution_time_ms: float
    error_message: str | None = None

    def get_overall_success_rate(self) -> float:
        """Return the success ratio across all requested episodes."""
        if self.total_episodes == 0:
            return 0.0
        return self.successful_episodes / self.total_episodes

    def get_failed_episode_numbers(self) -> list[int]:
        """Return the list of episodes whose processing failed."""
        return [episode_num for episode_num, response in self.episode_responses.items() if not response.success]

    def get_total_items_checked(self) -> int:
        """Return the number of checklist items processed across episodes."""
        return sum(response.total_items_checked for response in self.episode_responses.values() if response.success)

    def get_overall_pass_rate(self) -> float:
        """Return the average pass rate of successful episode runs."""
        successful_responses = [response for response in self.episode_responses.values() if response.success]

        if not successful_responses:
            return 0.0

        total_pass_rate = sum(response.get_pass_rate() for response in successful_responses)
        return total_pass_rate / len(successful_responses)

class A31BatchAutoFixUseCase(AbstractUseCase[A31BatchRequest, A31BatchResponse]):
    """Coordinate A31 auto-fix execution across multiple episodes."""

    def __init__(
        self,
        logger_service,
        unit_of_work,
        **kwargs,
    ) -> None:
        """Initialise the use case with logging and Unit of Work services.

        Args:
            logger_service: Logger service used for diagnostics.
            unit_of_work: Unit of Work coordinating repositories and
                transactions.
            **kwargs: Additional keyword arguments forwarded to the base class.
        """
        # 基底クラス初期化
        super().__init__(**kwargs)

        self._logger_service = logger_service
        self._unit_of_work = unit_of_work

    async def execute(self, request: A31BatchRequest) -> A31BatchResponse:
        """Execute the batch auto-fix workflow for the requested episodes.

        Args:
            request (A31BatchRequest): Batch execution parameters.

        Returns:
            A31BatchResponse: Aggregated result summarising the batch run.
        """
        start_time = time.time()

        try:
            # 1. エピソード存在確認
            available_episodes = self._validate_episodes(request.project_name, request.episode_numbers)

            if not available_episodes:
                return A31BatchResponse(
                    success=False,
                    project_name=request.project_name,
                    total_episodes=len(request.episode_numbers),
                    processed_episodes=0,
                    successful_episodes=0,
                    failed_episodes=0,
                    episode_responses={},
                    execution_time_ms=0.0,
                    error_message="処理可能なエピソードが見つかりません",
                )

            # 2. バッチ処理の実行
            episode_responses = self._process_episodes_batch(request, available_episodes)

            # 3. 結果の集計
            successful_count = sum(1 for response in episode_responses.values() if response.success)

            failed_count = len(episode_responses) - successful_count

            execution_time = (time.time() - start_time) * 1000

            return A31BatchResponse(
                success=True,
                project_name=request.project_name,
                total_episodes=len(request.episode_numbers),
                processed_episodes=len(episode_responses),
                successful_episodes=successful_count,
                failed_episodes=failed_count,
                episode_responses=episode_responses,
                execution_time_ms=execution_time,
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return A31BatchResponse(
                success=False,
                project_name=request.project_name,
                total_episodes=len(request.episode_numbers),
                processed_episodes=0,
                successful_episodes=0,
                failed_episodes=0,
                episode_responses={},
                execution_time_ms=execution_time,
                error_message=f"バッチ処理中にエラーが発生しました: {e!s}",
            )

    def execute_sequential(self, request: A31BatchRequest) -> A31BatchResponse:
        """Execute the batch flow sequentially (debug helper).

        Args:
            request (A31BatchRequest): Batch execution parameters.

        Returns:
            A31BatchResponse: Aggregated result summarising the batch run.
        """
        # 並列処理を無効化して順次実行
        sequential_request = A31BatchRequest(
            project_name=request.project_name,
            episode_numbers=request.episode_numbers,
            target_categories=request.target_categories,
            include_auto_fix=request.include_auto_fix,
            fix_level=request.fix_level,
            max_parallel_jobs=1,  # 並列度を1に設定
            stop_on_error=request.stop_on_error,
        )

        return self.execute(sequential_request)

    def get_batch_summary(self, response: A31BatchResponse) -> dict[str, any]:
        """Return a lightweight summary dictionary for reporting."""
        if not response.success:
            return {"success": False, "error": response.error_message}

        return {
            "success": True,
            "project_name": response.project_name,
            "total_episodes": response.total_episodes,
            "processed_episodes": response.processed_episodes,
            "success_rate": response.get_overall_success_rate(),
            "overall_pass_rate": response.get_overall_pass_rate(),
            "total_items_checked": response.get_total_items_checked(),
            "failed_episodes": response.get_failed_episode_numbers(),
            "execution_time_ms": response.execution_time_ms,
            "performance_metrics": {
                "episodes_per_second": response.processed_episodes / (response.execution_time_ms / 1000),
                "average_time_per_episode": response.execution_time_ms / response.processed_episodes
                if response.processed_episodes > 0
                else 0,
            },
        }

    def _validate_episodes(self, project_name: str, episode_numbers: list[int]) -> list[int]:
        """Validate that the requested episodes exist for the project."""
        available_episodes = []

        for episode_num in episode_numbers:
            try:
                # エピソード内容を取得してみることで存在確認
                self._episode_repository.get_episode_content(project_name, episode_num)
                available_episodes.append(episode_num)
            except FileNotFoundError:
                # 存在しないエピソードはスキップ
                self._logger_service.warning(f"エピソード {episode_num} が見つかりません")
                continue

        return available_episodes

    def _process_episodes_batch(
        self, request: A31BatchRequest, episode_numbers: list[int]
    ) -> dict[int, A31CompleteCheckResponse]:
        """Dispatch execution either sequentially or via the parallel stub."""
        responses = {}

        # 並列処理または順次処理の選択
        if request.max_parallel_jobs > 1 and len(episode_numbers) > 1:
            responses = self._process_episodes_parallel(request, episode_numbers)
        else:
            responses = self._process_episodes_sequential(request, episode_numbers)

        return responses

    def _process_episodes_sequential(
        self, request: A31BatchRequest, episode_numbers: list[int]
    ) -> dict[int, A31CompleteCheckResponse]:
        """Process each episode sequentially and collect responses."""
        responses = {}

        for episode_num in episode_numbers:
            try:
                # 個別エピソードのチェック実行
                check_request = A31CompleteCheckRequest(
                    project_name=request.project_name,
                    episode_number=episode_num,
                    target_categories=request.target_categories,
                    include_auto_fix=request.include_auto_fix,
                    fix_level=request.fix_level,
                )

                response = self._complete_check_use_case.execute(check_request)
                responses[episode_num] = response

                # エラー時の停止判定
                if not response.success and request.stop_on_error:
                    self._logger_service.error(f"エピソード {episode_num} の処理が失敗したため停止します")
                    break

                # 進捗表示
                if request.show_progress:
                    status = "✅ 成功" if response.success else "❌ 失敗"
                    console = self._get_console()
                    console.print(f"エピソード {episode_num}: {status}")

            except Exception as e:
                # 個別エピソード処理のエラーハンドリング
                error_response = A31CompleteCheckResponse(
                    success=False,
                    project_name=request.project_name,
                    episode_number=episode_num,
                    target_categories=request.target_categories,
                    check_results=[],
                    error_message=f"エピソード {episode_num} の処理中にエラーが発生: {e!s}",
                    execution_time_ms=0.0,
                )
                responses[episode_num] = error_response

                if request.stop_on_error:
                    self._logger_service.error(
                        f"エピソード {episode_num} でエラーが発生したため停止します: {e}"
                    )
                    break

        return responses

    def _process_episodes_parallel(
        self, request: A31BatchRequest, episode_numbers: list[int]
    ) -> dict[int, A31CompleteCheckResponse]:
        """Placeholder for future parallel execution support."""
        # 現在は順次処理で代替(将来的にconcurrent.futuresで並列化)
        # B20準拠: print文削除、ロガー使用
        if hasattr(self, "_logger_service") and self._logger_service:
            self._logger_service.info("Info: 並列処理は将来の実装予定です。順次処理で実行します。")
        else:
            logger = get_logger(__name__)
            logger.info("Info: 並列処理は将来の実装予定です。順次処理で実行します。")
        return self._process_episodes_sequential(request, episode_numbers)

class A31BatchAutoFixUseCaseError(Exception):
    """Base exception raised by the batch auto-fix use case."""

class EpisodesNotFoundError(A31BatchAutoFixUseCaseError):
    """Raised when requested episodes do not exist or cannot be loaded."""

class BatchProcessingError(A31BatchAutoFixUseCaseError):
    """Generic error raised during batch auto-fix execution."""
