"""Domain.services.bulk_quality_check_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""全話品質チェック サービス"""


import threading
import time
from concurrent.futures import CancelledError, ThreadPoolExecutor
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

from noveler.domain.entities.bulk_quality_check import QualityHistory
from noveler.domain.exceptions import NoEpisodesFoundError

if TYPE_CHECKING:
    from noveler.domain.entities.episode import Episode
    from noveler.domain.value_objects.quality_check_result import QualityCheckResult


class EpisodeRepository(Protocol):
    """エピソードリポジトリのプロトコル"""

    def find_by_project(self, project_name: str) -> list[Episode]:
        """プロジェクトのエピソードを検索"""
        ...


class QualityRepository(Protocol):
    """品質リポジトリのプロトコル"""

    def save_quality_history(self, history: QualityHistory) -> None:
        """品質履歴を保存"""
        ...


class QualityChecker(Protocol):
    """品質チェッカーのプロトコル"""

    def check_episode_quality(self, episode: Episode) -> QualityCheckResult:
        """エピソードの品質をチェック"""
        ...


@dataclass
class BulkQualityCheckRequest:
    """全話品質チェック要求"""

    project_name: str
    episode_range: tuple[int, int] | None = None
    parallel: bool = False
    include_archived: bool = False
    force_recheck: bool = False


@dataclass
class BulkQualityCheckResult:
    """全話品質チェック結果"""

    project_name: str
    total_episodes: int
    checked_episodes: int
    average_quality_score: float
    quality_trend: str
    problematic_episodes: list[int]
    improvement_suggestions: list[str]
    execution_time: float
    success: bool
    errors: list[str]


class BulkQualityCheckService:
    """全話品質チェック サービス"""

    def __init__(
        self,
        episode_repository: EpisodeRepository,
        quality_repository: QualityRepository,
        quality_checker: QualityChecker | None = None,
    ) -> None:
        self.episode_repository = episode_repository
        self.quality_repository = quality_repository
        self.quality_checker = quality_checker

    def execute_bulk_check(self, request: BulkQualityCheckRequest) -> BulkQualityCheckResult:
        """全話品質チェックを実行"""
        start_time = time.time()

        try:
            # エピソード一覧を取得
            episodes = self.episode_repository.find_by_project(request.project_name)

            if not episodes:
                msg = f"No episodes found for project: {request.project_name}"
                raise NoEpisodesFoundError(msg)

            # 範囲指定がある場合はフィルタリング
            if request.episode_range:
                start_ep, end_ep = request.episode_range
                episodes = [ep for ep in episodes if start_ep <= ep.episode_number <= end_ep]

            # 品質チェック実行
            if request.parallel:
                results: Any = self._execute_parallel_check(episodes)
            else:
                results: Any = self._execute_sequential_check(episodes)

            # 結果を集計
            total_episodes = len(episodes)
            checked_episodes = len(results)
            average_score = sum(r.overall_score.to_float() for r in results) / len(results) if results else 0.0

            # 品質履歴を作成
            history = QualityHistory(request.project_name)
            for episode, result in zip(episodes, results, strict=False):
                history.add_record(episode.episode_number, result)

            # 問題のあるエピソードを特定
            problematic_episodes = history.find_problematic_episodes(threshold=70.0)

            # 改善提案を生成
            suggestions = self._generate_improvement_suggestions(results)

            execution_time = time.time() - start_time

            return BulkQualityCheckResult(
                project_name=request.project_name,
                total_episodes=total_episodes,
                checked_episodes=checked_episodes,
                average_quality_score=average_score,
                quality_trend="stable",  # 簡易実装
                problematic_episodes=problematic_episodes,
                improvement_suggestions=suggestions,
                execution_time=execution_time,
                success=True,
                errors=[],
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return BulkQualityCheckResult(
                project_name=request.project_name,
                total_episodes=0,
                checked_episodes=0,
                average_quality_score=0.0,
                quality_trend="unknown",
                problematic_episodes=[],
                improvement_suggestions=[],
                execution_time=execution_time,
                success=False,
                errors=[str(e)],
            )

    def _execute_sequential_check(self, episodes: list[Any]) -> list[QualityCheckResult]:
        """逐次品質チェック実行"""
        results: list[QualityCheckResult] = []
        for episode in episodes:
            result = self.quality_checker.check_episode(episode)
            results.append(result)
        return results

    def _execute_parallel_check(self, episodes: list[Any]) -> list[QualityCheckResult]:
        """並列品質チェック実行"""
        max_workers = max(1, min(4, len(episodes)))
        try:
            executor = ThreadPoolExecutor(max_workers=max_workers)
        except (RuntimeError, OSError):
            # Fallback when threads cannot be spawned (e.g. resource constrained CI).
            return self._execute_sequential_check(episodes)

        results_map: dict[int, QualityCheckResult] = {}
        lock = threading.Lock()

        def _run_episode(index: int, episode: Any) -> QualityCheckResult:
            result = self.quality_checker.check_episode(episode)
            with lock:
                results_map[index] = result
            return result

        futures: list[Any] = []
        try:
            for index, episode in enumerate(episodes):
                futures.append(executor.submit(_run_episode, index, episode))
        except (RuntimeError, OSError):
            executor.shutdown(wait=False, cancel_futures=True)
            for future in futures:
                try:
                    future.result()
                except CancelledError:
                    continue
            missing_indices = [i for i in range(len(episodes)) if i not in results_map]
            for index in missing_indices:
                episode = episodes[index]
                results_map[index] = self.quality_checker.check_episode(episode)
            executor.shutdown(wait=True)
            return [results_map[i] for i in range(len(episodes))]

        try:
            for future in futures:
                future.result()
        finally:
            executor.shutdown(wait=True)

        return [results_map[i] for i in range(len(episodes))]

    def _generate_improvement_suggestions(self, results: list[QualityCheckResult]) -> list[str]:
        """改善提案を生成"""
        suggestions: list[str] = []

        # 平均スコアが低い場合
        avg_score = sum(r.overall_score.to_float() for r in results) / len(results) if results else 0.0
        if avg_score < 80.0:
            suggestions.append("全体的な品質向上が必要です")

        # 具体的な改善案(簡易実装)
        if avg_score < 90.0:  # 閾値を上げて必ず提案が出るようにする:
            suggestions.append("文体の統一性を確認してください")

        return list(set(suggestions))  # 重複を除去
