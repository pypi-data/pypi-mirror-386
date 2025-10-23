"""Domain.analysis.entities
Where: Domain entities representing analysis results and contexts.
What: Defines core data structures for text and quality analyses.
Why: Provides reusable analysis entity models across the domain.
"""

from __future__ import annotations

"""分析ドメインのエンティティ"""


from dataclasses import dataclass, field
from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from noveler.domain.analysis.value_objects import (
    AnalysisTimestamp,
    DateRange,
    DropoutRate,
    DropoutSeverity,
    NarouCode,
    PageView,
    UniqueUser,
)
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

if TYPE_CHECKING:
    from noveler.domain.writing.value_objects import EpisodeNumber


# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


@dataclass
class EpisodeAccess:
    """エピソードアクセス情報エンティティ"""

    id: str = field(default_factory=lambda: str(uuid4()))
    episode_number: EpisodeNumber | None = None
    date: date | None = None
    page_views: PageView | None = None
    unique_users: UniqueUser | None = None

    def calculate_average_views_per_user(self) -> float | None:
        """ユーザーあたりの平均閲覧数を計算"""
        if self.unique_users and self.unique_users.value > 0 and self.page_views:
            return self.page_views.value / self.unique_users.value
        return None

    def is_data_available(self) -> bool:
        """データが利用可能かチェック"""
        return self.page_views is not None and self.unique_users is not None and self.page_views.value > 0


@dataclass
class DropoutAnalysis:
    """離脱率分析エンティティ"""

    id: str = field(default_factory=lambda: str(uuid4()))
    project_id: str = ""
    ncode: NarouCode | None = None
    episode_number: EpisodeNumber | None = None
    previous_users: UniqueUser | None = None
    current_users: UniqueUser | None = None
    dropout_rate: DropoutRate | None = None
    severity: DropoutSeverity | None = None
    analyzed_at: AnalysisTimestamp = field(default_factory=lambda: AnalysisTimestamp(project_now().datetime))

    def calculate_dropout_rate(self) -> None:
        """離脱率を計算"""
        if self.current_users and self.previous_users:
            self.dropout_rate = self.current_users.calculate_dropout_rate(self.previous_users)
            if self.dropout_rate:
                self.severity = self.dropout_rate.get_severity()

    def is_critical(self) -> bool:
        """危険な離脱率かチェック"""
        return self.severity == DropoutSeverity.CRITICAL

    def is_significant(self) -> bool:
        """有意な離脱率かチェック(20%以上)"""
        return self.dropout_rate and not self.dropout_rate.is_acceptable(0.2)

    def get_improvement_priority(self) -> int:
        """改善優先度を取得(1-4、1が最優先)"""
        if not self.severity:
            return 4

        priority_map = {
            DropoutSeverity.CRITICAL: 1,
            DropoutSeverity.HIGH: 2,
            DropoutSeverity.MODERATE: 3,
            DropoutSeverity.LOW: 4,
        }
        return priority_map[self.severity]


@dataclass
class AccessMetrics:
    """アクセス統計エンティティ"""

    id: str = field(default_factory=lambda: str(uuid4()))
    project_id: str = ""
    ncode: NarouCode | None = None
    period: DateRange = field(default_factory=lambda: DateRange.current_month())
    episode_accesses: list[EpisodeAccess] = field(default_factory=list)
    dropout_analyses: list[DropoutAnalysis] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def add_episode_access(self, access: EpisodeAccess) -> None:
        """エピソードアクセス情報を追加"""
        self.episode_accesses.append(access)

    def add_dropout_analysis(self, analysis: DropoutAnalysis) -> None:
        """離脱率分析を追加"""
        self.dropout_analyses.append(analysis)

    def get_total_page_views(self) -> int:
        """総ページビュー数を取得"""
        return sum(access.page_views.value for access in self.episode_accesses if access.page_views)

    def get_total_unique_users(self) -> int:
        """総ユニークユーザー数を取得(最初のエピソード基準)"""
        first_episode = min(
            (a for a in self.episode_accesses if a.episode_number),
            key=lambda a: a.episode_number.value,
            default=None,
        )

        if first_episode and first_episode.unique_users:
            return first_episode.unique_users.value
        return 0

    def get_average_dropout_rate(self) -> DropoutRate | None:
        """平均離脱率を取得"""
        valid_analyses = [a for a in self.dropout_analyses if a.dropout_rate is not None]

        if not valid_analyses:
            return None

        avg_rate = sum(a.dropout_rate.value for a in valid_analyses) / len(valid_analyses)
        return DropoutRate(avg_rate)

    def get_critical_episodes(self) -> list[DropoutAnalysis]:
        """危険な離脱率のエピソードを取得"""
        return [analysis for analysis in self.dropout_analyses if analysis.is_critical()]

    def get_episodes_by_severity(self, severity: DropoutSeverity) -> list[DropoutAnalysis]:
        """深刻度別にエピソードを取得"""
        return [analysis for analysis in self.dropout_analyses if analysis.severity == severity]

    def generate_summary(self) -> dict[str, any]:
        """サマリー情報を生成"""
        critical_episodes = self.get_critical_episodes()
        avg_dropout = self.get_average_dropout_rate()

        return {
            "period": {
                "start": self.period.start_date,
                "end": self.period.end_date,
                "days": self.period.days(),
            },
            "total_episodes": len(self.episode_accesses),
            "total_page_views": self.get_total_page_views(),
            "total_unique_users": self.get_total_unique_users(),
            "average_dropout_rate": avg_dropout.to_percentage() if avg_dropout else None,
            "critical_episodes": len(critical_episodes),
            "severity_breakdown": {
                severity.value: len(self.get_episodes_by_severity(severity)) for severity in DropoutSeverity
            },
        }


@dataclass
class AnalysisReport:
    """分析レポート集約"""

    id: str = field(default_factory=lambda: str(uuid4()))
    project_id: str = ""
    title: str = ""
    metrics: AccessMetrics | None = None
    recommendations: list[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)

    def add_recommendation(self, recommendation: str) -> None:
        """推奨事項を追加"""
        self.recommendations.append(recommendation)

    def generate_recommendations(self) -> None:
        """メトリクスに基づいて推奨事項を自動生成"""
        if not self.metrics:
            return

        # 危険なエピソードがある場合
        critical_episodes = self.metrics.get_critical_episodes()
        if critical_episodes:
            for analysis in critical_episodes[:3]:  # 上位3つ
                if analysis.episode_number:
                    self.add_recommendation(
                        f"{analysis.episode_number}の離脱率が{analysis.dropout_rate}と"
                        f"非常に高いです。内容の見直しを推奨します。",
                    )

        # 平均離脱率が高い場合
        avg_dropout = self.metrics.get_average_dropout_rate()
        if avg_dropout and avg_dropout.to_percentage() > 15:
            self.add_recommendation(
                f"全体の平均離脱率が{avg_dropout}と高めです。読者を引き込む要素の強化を検討してください。",
            )

        # 改善の兆候がある場合
        improving_episodes = [a for a in self.metrics.dropout_analyses if a.dropout_rate and a.dropout_rate.value < 0.1]
        if improving_episodes:
            self.add_recommendation(
                f"{len(improving_episodes)}つのエピソードで離脱率が10%未満と良好です。"
                "これらの要素を他のエピソードにも活用することを推奨します。",
            )
