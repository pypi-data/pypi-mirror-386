#!/usr/bin/env python3

"""Domain.entities.dropout_analysis_session
Where: Domain entity tracking dropout analysis sessions.
What: Stores reader engagement metrics and analysis insights.
Why: Helps teams understand and address dropout trends.
"""

from __future__ import annotations

"""離脱率分析セッションエンティティ(DDD実装)

離脱率分析のドメインモデル。
KASASAGI APIから取得したデータを分析し、離脱率と改善提案を生成する。
"""


from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

if TYPE_CHECKING:
    from datetime import date, datetime

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class AnalysisStatus(Enum):
    """分析ステータス"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class DropoutRate:
    """離脱率値オブジェクト(0-100%)"""

    value: float

    def __post_init__(self) -> None:
        """バリデーション"""
        if not 0 <= self.value <= 100:
            msg = "離脱率は0-100の範囲内である必要があります"
            raise ValueError(msg)

    def is_critical(self, threshold: float) -> bool:
        """重要な離脱率かを判定"""
        return self.value >= threshold

    def __hash__(self) -> int:
        """ハッシュ値を生成"""
        return hash(self.value)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, DropoutRate):
            return NotImplemented
        return self.value < other.value

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, DropoutRate):
            return NotImplemented
        return self.value > other.value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DropoutRate):
            return NotImplemented
        return self.value == other.value


@dataclass(frozen=True)
class DropoutInfo:
    """離脱情報値オブジェクト"""

    episode_number: int
    episode_title: str
    dropout_rate: DropoutRate
    current_pv: int
    previous_pv: int


@dataclass(frozen=True)
class EpisodeMetrics:
    """エピソードメトリクス値オブジェクト"""

    episode_number: int
    episode_title: str
    page_views: int
    unique_users: int
    access_date: date

    @property
    def pv_per_user(self) -> float:
        """ユーザーあたりPVを計算"""
        if self.unique_users == 0:
            return 0.0
        return self.page_views / self.unique_users

    def is_incomplete(self) -> bool:
        """不完全なデータかを判定(集計中データの可能性)"""
        return self.page_views == 0 or self.unique_users == 0


@dataclass(frozen=True)
class AnalysisPeriod:
    """分析期間値オブジェクト"""

    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        """バリデーション"""
        if self.start_date > self.end_date:
            msg = "開始日は終了日以前である必要があります"
            raise ValueError(msg)

    @property
    def days(self) -> int:
        """期間の日数を取得(両端を含む)"""
        return (self.end_date - self.start_date).days + 1


@dataclass(frozen=True)
class EpisodeDropout:
    """エピソード離脱情報"""

    episode_number: int
    episode_title: str
    dropout_rate: DropoutRate
    current_pv: int
    previous_pv: int

    @property
    def pv_loss(self) -> int:
        """PV損失数"""
        return self.previous_pv - self.current_pv


@dataclass(frozen=True)
class CriticalEpisode:
    """要改善エピソード"""

    episode_number: int
    episode_title: str
    dropout_rate: DropoutRate
    current_pv: int
    previous_pv: int
    priority: str  # high, medium, low

    @classmethod
    def from_dropout(cls, dropout: EpisodeDropout) -> CriticalEpisode:
        """離脱情報から生成"""
        priority = "high" if dropout.dropout_rate.value >= 30 else "medium"
        return cls(
            episode_number=dropout.episode_number,
            episode_title=dropout.episode_title,
            dropout_rate=dropout.dropout_rate,
            current_pv=dropout.current_pv,
            previous_pv=dropout.previous_pv,
            priority=priority,
        )


class DropoutAnalysisSession:
    """離脱率分析セッション(ルートアグリゲート)

    エピソードアクセスデータから離脱率を分析し、
    改善が必要なエピソードを特定する。
    """

    def __init__(
        self,
        session_id: str,
        project_id: str,
        ncode: str | None = None,
        analysis_period: str | None = None,
        config: dict | None = None,
    ) -> None:
        """初期化

        Args:
            session_id: セッションID
            project_id: プロジェクトID
            ncode: 小説コード
            analysis_period: 分析期間
            config: 設定
        """
        self.session_id = session_id
        self.project_id = project_id
        self.ncode = ncode
        self.analysis_period = analysis_period
        self.config = config or {}
        self.created_at = project_now().datetime
        self.completed_at: datetime | None = None
        self.status = AnalysisStatus.PENDING
        self.episode_metrics: list[EpisodeMetrics] = []
        self._dropout_rates_cache: list[EpisodeDropout] | None = None
        self._average_rate_cache: DropoutRate | None = None

    def add_episode_metrics(self, metrics: EpisodeMetrics) -> None:
        """エピソードメトリクスを追加

        Args:
            metrics: エピソードメトリクス
        """
        if self.status == AnalysisStatus.COMPLETED:
            msg = "完了した分析セッションにはデータを追加できません"
            raise ValueError(msg)

        # エピソード番号順にソートして保持
        self.episode_metrics.append(metrics)
        self.episode_metrics.sort(key=lambda m: m.episode_number)

        # キャッシュをクリア
        self._dropout_rates_cache = None
        self._average_rate_cache = None

        # ステータス更新
        if self.status == AnalysisStatus.PENDING:
            self.status = AnalysisStatus.IN_PROGRESS

    def filter_incomplete_data(self) -> None:
        """不完全なデータを除外

        KASASAGIの制約により、PV=0のデータは集計中の可能性があるため除外。
        """
        self.episode_metrics = [m for m in self.episode_metrics if not m.is_incomplete()]
        # キャッシュをクリア
        self._dropout_rates_cache = None
        self._average_rate_cache = None

    def analyze_dropout_rates(self, access_data) -> list[EpisodeDropout]:
        """離脱率を計算

        Returns:
            エピソード離脱情報のリスト
        """
        return self.calculate_dropout_rates()

    def calculate_dropout_rates(self) -> list[EpisodeDropout]:
        """離脱率を計算(内部メソッド)

        Returns:
            エピソード離脱情報のリスト
        """
        if self._dropout_rates_cache is not None:
            return self._dropout_rates_cache

        dropout_rates = []
        for i in range(1, len(self.episode_metrics)):
            current = self.episode_metrics[i]
            previous = self.episode_metrics[i - 1]

            if previous.page_views > 0:
                rate = (previous.page_views - current.page_views) / previous.page_views * 100
                dropout = EpisodeDropout(
                    episode_number=current.episode_number,
                    episode_title=current.episode_title,
                    dropout_rate=DropoutRate(rate),
                    current_pv=current.page_views,
                    previous_pv=previous.page_views,
                )

                dropout_rates.append(dropout)

        self._dropout_rates_cache = dropout_rates
        return dropout_rates

    def calculate_average_dropout_rate(self) -> DropoutRate:
        """平均離脱率を計算

        Returns:
            平均離脱率
        """
        if self._average_rate_cache is not None:
            return self._average_rate_cache

        dropout_rates = self.calculate_dropout_rates()
        if not dropout_rates:
            return DropoutRate(0.0)

        avg_rate = sum(d.dropout_rate.value for d in dropout_rates) / len(dropout_rates)
        self._average_rate_cache = DropoutRate(avg_rate)
        return self._average_rate_cache

    def identify_critical_episodes(self, threshold: float) -> list[CriticalEpisode]:
        """要改善エピソードを特定

        Args:
            threshold: 離脱率の閾値(デフォルト20%)

        Returns:
            要改善エピソードのリスト
        """
        dropout_rates = self.calculate_dropout_rates()
        critical_episodes = []

        for dropout in dropout_rates:
            if dropout.dropout_rate.value >= threshold:
                critical = CriticalEpisode.from_dropout(dropout)
                critical_episodes.append(critical)

        # 離脱率の高い順にソート
        critical_episodes.sort(key=lambda e: e.dropout_rate.value, reverse=True)
        return critical_episodes

    def generate_recommendations(self) -> list[str]:
        """改善推奨事項を生成

        Returns:
            改善推奨事項のリスト
        """
        recommendations = []

        # 平均離脱率に基づく推奨
        avg_rate = self.calculate_average_dropout_rate()
        if avg_rate.value > 25:
            recommendations.append(f"平均離脱率が{avg_rate.value}%と高いです。内容の見直しを推奨します")

        # 要改善エピソードに基づく推奨
        critical_episodes = self.identify_critical_episodes(25.0)
        if critical_episodes:
            high_priority = [e for e in critical_episodes if e.priority == "high"]
            if high_priority:
                recommendations.append(
                    f"離脱率30%以上の話が{len(high_priority)}話あります。これらの話を最優先で修正することを推奨します。"
                )

            recommendations.extend(
                [
                    "各話の締めに次話への強い引きを追加",
                    "読者コメントから具体的な問題点を抽出",
                    "情報過多による読者の混乱がないか確認",
                    "展開の遅さによる退屈感がないか検証",
                ]
            )

        # データ精度に関する注意
        recommendations.append(
            "KASASAGIの制約により、直近2日間のデータは除外済みです。最新話の分析は2-3日後に再実行することを推奨します。"
        )

        return recommendations

    def complete(self) -> None:
        """分析を完了"""
        self.status = AnalysisStatus.COMPLETED
        self.completed_at = project_now().datetime

    def fail(self, error_message: str) -> None:
        """分析を失敗として記録"""
        self.status = AnalysisStatus.FAILED
        self.completed_at = project_now().datetime
        self.config["error_message"] = error_message

    def export_summary(self) -> dict[str, Any]:
        """サマリーをエクスポート

        Returns:
            分析サマリー
        """
        avg_rate = self.calculate_average_dropout_rate()
        critical_episodes = self.identify_critical_episodes(25.0)

        return {
            "session_id": self.session_id,
            "project_id": self.project_id,
            "ncode": self.ncode,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "analysis_period": {
                "start_date": self.analysis_period.start_date.isoformat(),
                "end_date": self.analysis_period.end_date.isoformat(),
                "days": self.analysis_period.days,
            },
            "total_episodes": len(self.episode_metrics),
            "average_dropout_rate": avg_rate.value,
            "critical_episodes": [
                {
                    "episode": e.episode_title,
                    "dropout_rate": e.dropout_rate.value,
                    "current_pv": e.current_pv,
                    "previous_pv": e.previous_pv,
                    "pv_loss": e.previous_pv - e.current_pv,
                    "priority": e.priority,
                }
                for e in critical_episodes
            ],
            "recommendations": self.generate_recommendations(),
            "data_accuracy_notes": [
                "KASASAGIの制約により、直近2日間のデータは除外済み",
                "PV=0 または極端な離脱率(90%以上)のエピソードは集計中データとして除外",
            ],
        }

    def get_episode_by_number(self, episode_number: int) -> EpisodeMetrics | None:
        """エピソード番号でメトリクスを取得"""
        for metrics in self.episode_metrics:
            if metrics.episode_number == episode_number:
                return metrics
        return None


@dataclass(frozen=True)
class DropoutAnalysisResult:
    """離脱率分析結果エンティティ"""

    session_id: str
    project_id: str
    ncode: str | None
    status: AnalysisStatus
    created_at: datetime
    completed_at: datetime | None
    total_episodes: int
    average_dropout_rate: DropoutRate
    critical_episodes: list[CriticalEpisode]
    recommendations: list[str]

    @classmethod
    def from_session(cls, session: DropoutAnalysisSession) -> DropoutAnalysisResult:
        """セッションから結果を生成"""
        avg_rate = session.calculate_average_dropout_rate()
        critical_episodes = session.identify_critical_episodes(25.0)
        recommendations = session.generate_recommendations()

        return cls(
            session_id=session.session_id,
            project_id=session.project_id,
            ncode=session.ncode,
            status=session.status,
            created_at=session.created_at,
            completed_at=session.completed_at,
            total_episodes=len(session.episode_metrics),
            average_dropout_rate=avg_rate,
            critical_episodes=critical_episodes,
            recommendations=recommendations,
        )
