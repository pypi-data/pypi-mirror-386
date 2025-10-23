#!/usr/bin/env python3

"""Domain.ai_integration.entities.published_work
Where: Domain entity representing published works used for AI benchmarks.
What: Encapsulates metadata and evaluation helpers for published references.
Why: Supports AI comparison workflows with structured published work data.
"""

from __future__ import annotations

"""書籍化作品エンティティ

書籍化された作品の情報とその成功パターンを表現
"""


from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

if TYPE_CHECKING:
    from noveler.domain.ai_integration.value_objects.genre_configuration import GenreConfiguration

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class SuccessLevel(Enum):
    """成功レベル"""

    S_TIER = "S級"  # 書籍化 + アニメ化
    A_TIER = "A級"  # 書籍化 + 10巻以上
    B_TIER = "B級"  # 書籍化 + 5巻以上
    C_TIER = "C級"  # 書籍化 (基本成功ライン)


@dataclass(frozen=True)
class PublicationMetrics:
    """出版メトリクス"""

    publication_year: int
    volumes_published: int
    total_pv: int
    bookmarks: int
    ratings: float
    reviews_count: int

    def __post_init__(self) -> None:
        """メトリクスの妥当性検証"""
        current_year = project_now().datetime.year
        if not 2010 <= self.publication_year <= current_year:
            msg = f"出版年は2010年以降{current_year}年以前である必要があります: {self.publication_year}"
            raise ValueError(msg)

        if self.volumes_published < 1:
            msg = f"出版巻数は1巻以上である必要があります: {self.volumes_published}"
            raise ValueError(msg)

        if not 0 <= self.ratings <= 5.0:
            msg = f"評価は0.0以上5.0以下である必要があります: {self.ratings}"
            raise ValueError(msg)

    def get_success_level(self) -> SuccessLevel:
        """成功レベルを判定"""
        # アニメ化判定のための簡易ロジック(実際は外部データが必要)
        if self.volumes_published >= 10 and self.ratings >= 4.5:
            return SuccessLevel.S_TIER
        if self.volumes_published >= 10:
            return SuccessLevel.A_TIER
        if self.volumes_published >= 5:
            return SuccessLevel.B_TIER
        return SuccessLevel.C_TIER


@dataclass(frozen=True)
class StoryStructure:
    """物語構造"""

    first_turning_point: int  # 第1転換点(話数)
    romance_introduction: int  # 恋愛要素導入(話数)
    mid_boss_battle: int  # 中ボス戦(話数)
    climax_point: int  # クライマックス(話数)
    total_episodes: int  # 総話数

    def __post_init__(self) -> None:
        """構造の妥当性検証"""
        if self.first_turning_point < 1:
            msg = f"第1転換点は1話以降である必要があります: {self.first_turning_point}"
            raise ValueError(msg)

        if self.climax_point <= self.first_turning_point:
            msg = "クライマックスは第1転換点より後である必要があります"
            raise ValueError(msg)

        if self.total_episodes <= 0:
            msg = f"総話数は1話以上である必要があります: {self.total_episodes}"
            raise ValueError(msg)

    def get_pacing_ratio(self) -> float:
        """ペーシング比率(転換点の位置 / 全体)"""
        return self.first_turning_point / self.total_episodes

    def has_early_romance(self) -> bool:
        """早期恋愛導入かどうか(全体の30%以内)"""
        return self.romance_introduction <= self.total_episodes * 0.3


@dataclass
class PublishedWork:
    """書籍化作品エンティティ

    書籍化された作品とその成功パターンを表現
    """

    work_id: str
    title: str
    author: str
    genre_config: GenreConfiguration
    publication_metrics: PublicationMetrics
    story_structure: StoryStructure
    success_factors: list[str]

    def __post_init__(self) -> None:
        """作品の妥当性検証"""
        if not self.work_id:
            msg = "作品IDは必須です"
            raise ValueError(msg)

        if not self.title:
            msg = "タイトルは必須です"
            raise ValueError(msg)

        if not self.success_factors:
            msg = "成功要因は1つ以上必要です"
            raise ValueError(msg)

        # success_factorsをタプルに変換して不変性を保証
        object.__setattr__(self, "success_factors", tuple(self.success_factors))

    def get_success_level(self) -> SuccessLevel:
        """成功レベルを取得"""
        return self.publication_metrics.get_success_level()

    def is_similar_genre(self, other_config: GenreConfiguration) -> bool:
        """ジャンルが類似しているか"""
        return self.genre_config.similarity_score(other_config) >= 0.5

    def get_structural_pattern(self) -> dict[str, float]:
        """構造パターンを取得"""
        return {
            "first_turning_point_ratio": self.story_structure.get_pacing_ratio(),
            "early_romance": self.story_structure.has_early_romance(),
            "total_episodes": self.story_structure.total_episodes,
            "success_rating": self.publication_metrics.ratings,
        }

    def matches_criteria(self, genre_config: GenreConfiguration, min_success_level: SuccessLevel) -> bool:
        """分析対象の条件に一致するか"""
        # ジャンル類似性チェック
        if not self.is_similar_genre(genre_config):
            return False

        # 成功レベルチェック
        current_level = self.get_success_level()
        success_levels = [SuccessLevel.S_TIER, SuccessLevel.A_TIER, SuccessLevel.B_TIER, SuccessLevel.C_TIER]

        current_index = success_levels.index(current_level)
        min_index = success_levels.index(min_success_level)

        return current_index <= min_index

    def get_key_insights(self) -> list[str]:
        """重要な洞察を取得"""
        insights = []

        # 構造的洞察
        if self.story_structure.get_pacing_ratio() <= 0.2:
            insights.append("早期転換点で読者を引き込む")

        if self.story_structure.has_early_romance():
            insights.append("早期恋愛要素で感情移入を促進")

        # 成功要因から洞察
        if "独自世界観" in self.success_factors:
            insights.append("独自の世界観設定が差別化要因")

        if "キャラクター魅力" in self.success_factors:
            insights.append("魅力的なキャラクターが読者定着の鍵")

        return insights
