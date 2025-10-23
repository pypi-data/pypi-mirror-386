"""Domain.value_objects.dropout_metrics
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

from __future__ import annotations

"""離脱率メトリクス値オブジェクト

離脱率分析で使用される値オブジェクト群。
"""


from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date


@dataclass(frozen=True)
class DropoutRate:
    """離脱率値オブジェクト

    0-100%の範囲で離脱率を表現する。
    """

    value: float

    def __post_init__(self) -> None:
        """初期化後の検証"""
        if not 0 <= self.value <= 100:
            msg = "離脱率は0-100の範囲で指定してください"
            raise ValueError(msg)

    def __str__(self) -> str:
        """文字列表現"""
        return f"{self.value}%"

    def __hash__(self) -> int:
        """ハッシュ値を生成"""
        return hash(self.value)

    def __lt__(self, other: DropoutRate) -> bool:
        """小なり比較"""
        return self.value < other.value

    def __gt__(self, other: DropoutRate) -> bool:
        """大なり比較"""
        return self.value > other.value

    def __eq__(self, other: object) -> bool:
        """等価比較"""
        if not isinstance(other, DropoutRate):
            return NotImplemented
        return self.value == other.value

    def is_critical(self, threshold: float) -> bool:
        """危険な離脱率かどうか判定

        Args:
            threshold: 閾値(%)

        Returns:
            閾値を超えているかどうか
        """
        return self.value > threshold


@dataclass(frozen=True)
class EpisodeAccess:
    """エピソードアクセス情報

    特定のエピソードのアクセス数と日付を保持。
    """

    episode_number: int
    page_views: int
    date: date

    def __post_init__(self) -> None:
        """初期化後の検証"""
        if self.episode_number < 1:
            msg = "エピソード番号は1以上である必要があります"
            raise ValueError(msg)
        if self.page_views < 0:
            msg = "ページビュー数は0以上である必要があります"
            raise ValueError(msg)


@dataclass(frozen=True)
class EpisodeDropoutInfo:
    """エピソード別離脱情報

    特定エピソードの離脱率と関連情報を管理。
    """

    episode_number: int
    dropout_rate: DropoutRate
    page_views: int
    previous_page_views: int

    def __post_init__(self) -> None:
        """初期化後の検証"""
        if self.episode_number < 1:
            msg = "エピソード番号は1以上である必要があります"
            raise ValueError(msg)
        if self.page_views < 0:
            msg = "ページビュー数は0以上である必要があります"
            raise ValueError(msg)
        if self.previous_page_views < 0:
            msg = "前話のページビュー数は0以上である必要があります"
            raise ValueError(msg)


@dataclass
class AccessData:
    """アクセスデータコレクション

    複数のエピソードアクセス情報を管理。
    """

    accesses: list[EpisodeAccess]

    def __len__(self) -> int:
        """アクセスデータ数"""
        return len(self.accesses)

    def get_episode_access(self, episode_number: int) -> EpisodeAccess | None:
        """特定エピソードのアクセス情報を取得

        Args:
            episode_number: エピソード番号

        Returns:
            エピソードアクセス情報、存在しない場合はNone
        """
        for access in self.accesses:
            if access.episode_number == episode_number:
                return access
        return None

    def filter_by_date(self, target_date: date) -> AccessData:
        """特定日付のデータのみフィルタリング

        Args:
            target_date: 対象日付

        Returns:
            フィルタリングされたアクセスデータ
        """
        filtered = [access for access in self.accesses if access.date == target_date]
        return AccessData(filtered)

    def sorted_by_episode(self) -> AccessData:
        """エピソード番号順にソート

        Returns:
            ソートされたアクセスデータ
        """
        sorted_accesses = sorted(self.accesses, key=lambda x: x.episode_number)
        return AccessData(sorted_accesses)


@dataclass
class DropoutMetrics:
    """離脱率メトリクス

    エピソード別の離脱率と平均値を管理。
    """

    def __init__(self) -> None:
        """初期化"""
        self._episode_rates: dict[int, DropoutRate] = {}
        self._average_rate: float = 0.0

    @property
    def episode_rates(self) -> dict[int, DropoutRate]:
        """エピソード別離脱率"""
        return self._episode_rates.copy()

    @property
    def average_dropout_rate(self) -> float:
        """平均離脱率"""
        return self._average_rate

    def add_episode_rate(self, episode_number: int, rate: DropoutRate) -> None:
        """エピソード別離脱率を追加

        Args:
            episode_number: エピソード番号
            rate: 離脱率
        """
        self._episode_rates[episode_number] = rate

    def get_rate_for_episode(self, episode_number: int) -> DropoutRate | None:
        """特定エピソードの離脱率を取得

        Args:
            episode_number: エピソード番号

        Returns:
            離脱率、存在しない場合はNone
        """
        return self._episode_rates.get(episode_number)

    def calculate_average(self) -> None:
        """平均離脱率を計算"""
        if not self._episode_rates:
            self._average_rate = 0.0
            return

        total = sum(rate.value for rate in self._episode_rates.values())
        self._average_rate = total / len(self._episode_rates)

    def get_critical_episodes(self, threshold: float) -> list[int]:
        """危険な離脱率のエピソードを取得

        Args:
            threshold: 閾値(%)

        Returns:
            閾値を超えるエピソード番号のリスト
        """
        critical = []
        for episode_num, rate in self._episode_rates.items():
            if rate.is_critical(threshold):
                critical.append(episode_num)
        return sorted(critical)
