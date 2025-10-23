"""
SPEC-QUALITY-002: 品質履歴リポジトリインターフェース

品質履歴の永続化を抽象化するリポジトリインターフェース。
DDD設計に基づくドメイン層のインターフェース定義。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from noveler.domain.services.quality_history_value_objects import (
    AnalysisPeriod,
    QualityHistory,
    QualityRecord,
)
from noveler.domain.value_objects.episode_number import EpisodeNumber


@dataclass(frozen=True)
class TrendCriteria:
    """トレンド検索条件"""

    period: AnalysisPeriod
    episode_numbers: list[EpisodeNumber] | None = None
    min_score: float | None = None
    max_score: float | None = None


@dataclass(frozen=True)
class QualityTrendStatistics:
    """品質トレンド統計"""

    total_records: int
    average_improvement_rate: float
    best_performing_episodes: list[EpisodeNumber]
    worst_performing_episodes: list[EpisodeNumber]
    period_coverage: AnalysisPeriod


class QualityHistoryRepository(ABC):
    """品質履歴リポジトリインターフェース"""

    @abstractmethod
    def find_by_episode(self, episode_number: EpisodeNumber) -> QualityHistory | None:
        """エピソード番号で品質履歴を検索

        Args:
            episode_number: 検索対象のエピソード番号

        Returns:
            見つかった品質履歴、存在しない場合はNone
        """

    @abstractmethod
    def find_by_period(self, period: object) -> list[QualityRecord]:
        """期間で品質記録を検索

        Args:
            period: 検索期間

        Returns:
            期間内の品質記録のリスト
        """

    @abstractmethod
    def save_record(self, episode_number: EpisodeNumber, record: QualityRecord) -> None:
        """品質記録を保存

        Args:
            episode_number: エピソード番号
            record: 保存する品質記録
        """

    @abstractmethod
    def save_history(self, history: QualityHistory) -> None:
        """品質履歴全体を保存

        Args:
            history: 保存する品質履歴
        """

    @abstractmethod
    def get_trend_statistics(self, criteria: object) -> QualityTrendStatistics:
        """トレンド統計を取得

        Args:
            criteria: 統計取得条件

        Returns:
            トレンド統計情報
        """

    @abstractmethod
    def get_latest_records(self, episode_number: EpisodeNumber, limit: int) -> list[QualityRecord]:
        """最新の品質記録を取得

        Args:
            episode_number: エピソード番号
            limit: 取得件数上限

        Returns:
            最新の品質記録のリスト
        """

    @abstractmethod
    def delete_history(self, episode_number: EpisodeNumber) -> bool:
        """品質履歴を削除

        Args:
            episode_number: 削除対象のエピソード番号

        Returns:
            削除成功の場合True、対象が存在しない場合False
        """

    @abstractmethod
    def get_all_episodes_with_history(self) -> list[EpisodeNumber]:
        """履歴が存在する全エピソード番号を取得

        Returns:
            履歴が存在するエピソード番号のリスト
        """
