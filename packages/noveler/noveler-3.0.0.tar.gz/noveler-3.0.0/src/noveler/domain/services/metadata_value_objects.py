"""Domain.services.metadata_value_objects
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""
SPEC-EPISODE-004: エピソードメタデータ管理 - 値オブジェクト定義

エピソードメタデータ管理に関する値オブジェクトを定義。
DDD設計に基づく不変オブジェクトとして実装。
"""


from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import datetime, timedelta

    from noveler.domain.value_objects.episode_number import EpisodeNumber
    from noveler.domain.value_objects.episode_title import EpisodeTitle
    from noveler.domain.value_objects.quality_score import QualityScore
    from noveler.domain.value_objects.word_count import WordCount


@dataclass(frozen=True)
class BasicMetadata:
    """基本メタデータ値オブジェクト"""

    author: str
    genre: str
    tags: list[str]
    description: str

    def __post_init__(self) -> None:
        """バリデーション"""
        if not self.author or not self.author.strip():
            msg = "著者名は必須です"
            raise ValueError(msg)
        if not self.genre or not self.genre.strip():
            msg = "ジャンルは必須です"
            raise ValueError(msg)
        if not isinstance(self.tags, list):
            msg = "タグはリスト形式である必要があります"
            raise TypeError(msg)


@dataclass(frozen=True)
class WritingMetadata:
    """執筆メタデータ値オブジェクト"""

    word_count: WordCount
    writing_duration: timedelta
    status: str
    completion_rate: float

    def __post_init__(self) -> None:
        """バリデーション"""
        if not 0.0 <= self.completion_rate <= 1.0:
            msg = "完成度は0.0から1.0の範囲である必要があります"
            raise ValueError(msg)
        if self.writing_duration.total_seconds() < 0:
            msg = "執筆時間は負の値にできません"
            raise ValueError(msg)


@dataclass(frozen=True)
class QualityMetadata:
    """品質メタデータ値オブジェクト"""

    overall_score: QualityScore
    category_scores: dict[str, QualityScore]
    last_check_date: datetime
    improvement_suggestions: list[str]

    def __post_init__(self) -> None:
        """バリデーション"""
        if not isinstance(self.category_scores, dict):
            msg = "カテゴリスコアは辞書形式である必要があります"
            raise TypeError(msg)
        if not isinstance(self.improvement_suggestions, list):
            msg = "改善提案はリスト形式である必要があります"
            raise TypeError(msg)


@dataclass(frozen=True)
class TechnicalMetadata:
    """技術メタデータ値オブジェクト"""

    file_path: str
    file_hash: str
    version: str
    backup_paths: list[str]

    def __post_init__(self) -> None:
        """バリデーション"""
        if not self.file_path or not self.file_path.strip():
            msg = "ファイルパスは必須です"
            raise ValueError(msg)
        if not self.file_hash or not self.file_hash.strip():
            msg = "ファイルハッシュは必須です"
            raise ValueError(msg)
        if not isinstance(self.backup_paths, list):
            msg = "バックアップパスはリスト形式である必要があります"
            raise TypeError(msg)


@dataclass(frozen=True)
class EpisodeMetadata:
    """エピソードメタデータ集約値オブジェクト"""

    episode_number: EpisodeNumber
    title: EpisodeTitle
    basic_info: BasicMetadata
    writing_info: WritingMetadata
    quality_info: QualityMetadata
    technical_info: TechnicalMetadata
    created_at: datetime
    updated_at: datetime

    def get_completion_summary(self) -> dict[str, Any]:
        """完成度サマリーを取得"""
        return {
            "episode_number": self.episode_number.value,
            "title": self.title.value,
            "completion_rate": self.writing_info.completion_rate,
            "quality_score": self.quality_info.overall_score.value,
            "word_count": self.writing_info.word_count.value,
            "status": self.writing_info.status,
        }

    def is_ready_for_publication(self) -> bool:
        """公開準備完了か判定"""
        return (
            self.writing_info.completion_rate >= 1.0
            and self.quality_info.overall_score.value >= 70.0
            and self.writing_info.status in ["completed", "reviewed"]
        )


@dataclass(frozen=True)
class MetadataSearchCriteria:
    """メタデータ検索条件値オブジェクト"""

    date_range: tuple[datetime, datetime] | None = None
    quality_score_range: tuple[float, float] | None = None
    status_filter: list[str] | None = None
    author_filter: str | None = None
    genre_filter: str | None = None

    def __post_init__(self) -> None:
        """バリデーション"""
        if self.date_range:
            start, end = self.date_range
            if start > end:
                msg = "開始日は終了日より前である必要があります"
                raise ValueError(msg)

        if self.quality_score_range:
            min_score, max_score = self.quality_score_range
            if min_score > max_score:
                msg = "最小スコアは最大スコアより小さい必要があります"
                raise ValueError(msg)
            if not (0.0 <= min_score <= 100.0) or not (0.0 <= max_score <= 100.0):
                msg = "スコア範囲は0.0から100.0の範囲である必要があります"
                raise ValueError(msg)


@dataclass(frozen=True)
class MetadataStatistics:
    """メタデータ統計値オブジェクト"""

    total_episodes: int
    average_quality_score: float
    average_completion_rate: float
    average_word_count: float
    total_writing_time: timedelta
    most_active_period: str | None = None
    quality_trend: str | None = None  # "improving", "stable", "declining"

    def get_productivity_metrics(self) -> dict[str, float]:
        """生産性メトリクスを取得"""
        if self.total_episodes == 0:
            return {"episodes_per_day": 0.0, "words_per_hour": 0.0}

        total_hours = self.total_writing_time.total_seconds() / 3600
        return {
            "episodes_per_day": self.total_episodes / max(1, total_hours / 24),
            "words_per_hour": self.average_word_count * self.total_episodes / max(1, total_hours),
        }
