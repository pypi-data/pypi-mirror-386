#!/usr/bin/env python3

"""Domain.ai_integration.value_objects.genre_configuration
Where: Domain value object describing genre configuration parameters.
What: Defines weights, aliases, and thresholds used in genre benchmarking.
Why: Provides reusable configuration for genre-aware AI analysis.
"""

from __future__ import annotations

"""ジャンル設定値オブジェクト

プロジェクト設定.yamlから読み込まれるジャンル情報を表現
"""


from dataclasses import dataclass
from enum import Enum


class MainGenre(Enum):
    """メインジャンル"""

    FANTASY = "ファンタジー"
    ROMANCE = "恋愛"
    MYSTERY = "ミステリー"
    SCIENCE_FICTION = "SF"
    HORROR = "ホラー"
    SLICE_OF_LIFE = "日常"
    HISTORICAL = "歴史"
    CONTEMPORARY = "現代"


class SubGenre(Enum):
    """サブジャンル"""

    ISEKAI = "異世界"
    SCHOOL = "学園"
    MAGIC = "魔法"
    ROMANCE = "恋愛"
    COMEDY = "コメディ"
    ACTION = "アクション"
    REINCARNATION = "転生"
    GAME_WORLD = "ゲーム世界"
    OFFICE = "社会人"
    FAMILY = "家族"


class TargetFormat(Enum):
    """ターゲットフォーマット"""

    LIGHT_NOVEL = "ライトノベル"
    WEB_NOVEL = "Web小説"
    LITERARY_FICTION = "純文学"
    YOUNG_ADULT = "ヤングアダルト"


@dataclass(frozen=True)
class GenreConfiguration:
    """ジャンル設定

    プロジェクト設定.yamlから読み込まれるジャンル情報を表現
    """

    main_genre: MainGenre
    sub_genres: list[SubGenre]
    target_format: TargetFormat

    def __post_init__(self) -> None:
        """設定の妥当性検証"""
        if not self.sub_genres:
            msg = "サブジャンルは1つ以上指定する必要があります"
            raise ValueError(msg)

        if len(self.sub_genres) > 5:
            msg = f"サブジャンルは5つまでです: {len(self.sub_genres)}"
            raise ValueError(msg)

        # sub_genresをタプルに変換して不変性を保証
        object.__setattr__(self, "sub_genres", tuple(self.sub_genres))

    def get_genre_combination(self) -> str:
        """ジャンル組み合わせ文字列を取得"""
        sub_genre_names = [sg.value for sg in self.sub_genres]
        return f"{self.main_genre.value}×{'×'.join(sub_genre_names)}"

    def matches_genre(self, main: MainGenre, subs: list[SubGenre]) -> bool:
        """指定されたジャンルと一致するか"""
        return self.main_genre == main and set(self.sub_genres) == set(subs)

    def has_sub_genre(self, sub_genre: SubGenre) -> bool:
        """特定のサブジャンルを含むか"""
        return sub_genre in self.sub_genres

    def similarity_score(self, other: GenreConfiguration) -> float:
        """他のジャンル設定との類似度(0.0-1.0)"""
        if self.main_genre != other.main_genre:
            return 0.0

        # サブジャンルの重複率を計算
        self_subs = set(self.sub_genres)
        other_subs = set(other.sub_genres)

        if not self_subs and not other_subs:
            return 1.0

        intersection = self_subs.intersection(other_subs)
        union = self_subs.union(other_subs)

        return len(intersection) / len(union)
