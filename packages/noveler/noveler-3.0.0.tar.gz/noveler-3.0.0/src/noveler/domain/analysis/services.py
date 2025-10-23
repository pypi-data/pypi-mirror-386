"""Domain.analysis.services
Where: Domain services implementing text and quality analyses.
What: Offers analysis algorithms reusable by application workflows.
Why: Isolates analysis logic for easier maintenance and reuse.
"""

from __future__ import annotations

"""分析ドメインのサービスインターフェース"""


from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date
    from typing import Any, Protocol

    from noveler.domain.analysis.entities import EpisodeAccess
    from noveler.domain.writing.value_objects import EpisodeNumber

    class MetricsProtocol(Protocol):
        """メトリクス用プロトコル"""

        dropout_analyses: Any


class AccessDataService(ABC):
    """アクセスデータ取得サービスのインターフェース"""

    @abstractmethod
    def fetch_episode_access(self, ncode: str, date_range: tuple[date, date]) -> list[EpisodeAccess]:
        """エピソードのアクセスデータを取得"""

    @abstractmethod
    def fetch_daily_access(self, ncode: str, target_date: date) -> dict[int, EpisodeAccess]:
        """特定日のアクセスデータを取得"""

    @abstractmethod
    def is_data_available(self, ncode: str) -> bool:
        """データが利用可能かチェック"""


class DropoutAnalyzer:
    """離脱率分析サービス"""

    def analyze_dropout_patterns(
        self,
        episode_accesses: list[EpisodeAccess],
    ) -> dict[str, Any]:
        """離脱パターンを分析"""
        if len(episode_accesses) < 2:
            return {"error": "分析には2話以上のデータが必要です"}

        patterns: dict[str, list[dict[str, Any]]] = {
            "sudden_drops": [],  # 急激な離脱
            "gradual_decline": [],  # 段階的な減少
            "recovery_points": [],  # 回復ポイント
            "stable_sections": [],  # 安定区間
        }

        for i in range(1, len(episode_accesses)):
            current = episode_accesses[i]
            previous = episode_accesses[i - 1]

            if not (current.unique_users and previous.unique_users):
                continue

            dropout_rate = current.unique_users.calculate_dropout_rate(previous.unique_users)
            if not dropout_rate:
                continue

            # 急激な離脱(20%以上)
            if dropout_rate.to_percentage() > 20:
                users_lost = previous.unique_users.value - current.unique_users.value
                patterns["sudden_drops"].append(
                    {"episode": current.episode_number, "dropout_rate": dropout_rate, "users_lost": users_lost}
                )

            # 回復ポイント(前話より増加)
            if current.unique_users.value > previous.unique_users.value:
                patterns["recovery_points"].append(
                    {
                        "episode": current.episode_number,
                        "users_gained": current.unique_users.value - previous.unique_users.value,
                    }
                )

            # 安定区間(離脱率5%未満)
            if dropout_rate.to_percentage() < 5:
                patterns["stable_sections"].append({"episode": current.episode_number, "dropout_rate": dropout_rate})

        return patterns

    def identify_critical_episodes(self, metrics: MetricsProtocol, threshold: float) -> list[EpisodeNumber]:
        """改善が必要な重要エピソードを特定"""
        critical_episodes: list[EpisodeNumber] = []

        for analysis in metrics.dropout_analyses:
            if analysis.dropout_rate and analysis.dropout_rate.value > threshold:
                if analysis.episode_number:
                    critical_episodes.append(analysis.episode_number)

        # 離脱率の高い順にソート
        critical_episodes.sort(
            key=lambda ep: next(
                (a.dropout_rate.value for a in metrics.dropout_analyses if a.episode_number == ep),
                0,
            ),
            reverse=True,
        )

        return critical_episodes
