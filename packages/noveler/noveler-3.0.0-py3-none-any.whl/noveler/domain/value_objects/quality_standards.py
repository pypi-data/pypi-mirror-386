"""Domain.value_objects.quality_standards
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

from __future__ import annotations

"""品質基準の段階的適用システム - ドメインモデル

執筆者のレベルとジャンルに応じて品質基準を動的に調整する
"""


from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class WriterLevel(Enum):
    """執筆者レベル"""

    BEGINNER = "beginner"  # 初心者(0-5話)
    INTERMEDIATE = "intermediate"  # 中級者(6-20話)
    ADVANCED = "advanced"  # 上級者(21-50話)
    EXPERT = "expert"  # エキスパート(51話以上)


class Genre(Enum):
    """小説ジャンル"""

    FANTASY = "fantasy"  # ファンタジー
    ROMANCE = "romance"  # 恋愛
    MYSTERY = "mystery"  # ミステリー
    SF = "science_fiction"  # SF
    LITERARY = "literary"  # 純文学
    LIGHT_NOVEL = "light_novel"  # ライトノベル
    OTHER = "other"  # その他


@dataclass(frozen=True)
class QualityThreshold:
    """品質基準の閾値"""

    minimum_score: int  # 最低基準スコア
    target_score: int  # 目標スコア
    excellent_score: int  # 優秀スコア

    def __post_init__(self) -> None:
        if not (0 <= self.minimum_score <= self.target_score <= self.excellent_score <= 100):
            msg = "スコアは0-100の範囲で、minimum <= target <= excellentである必要があります"
            raise ValueError(msg)


@dataclass(frozen=True)
class QualityStandard:
    """品質基準"""

    writer_level: WriterLevel
    genre: Genre
    thresholds: dict[str, QualityThreshold]  # チェック項目ごとの閾値
    weight_adjustments: dict[str, float]  # 重み調整係数

    def get_threshold(self, check_type: str) -> QualityThreshold:
        """特定のチェック項目の閾値を取得"""
        return self.thresholds.get(check_type, self._get_default_threshold())

    def get_weight(self, check_type: str) -> float:
        """特定のチェック項目の重み係数を取得"""
        return self.weight_adjustments.get(check_type, 1.0)

    def _get_default_threshold(self) -> QualityThreshold:
        """デフォルトの閾値を返す"""
        base_values = {
            WriterLevel.BEGINNER: (50, 60, 70),
            WriterLevel.INTERMEDIATE: (60, 70, 80),
            WriterLevel.ADVANCED: (70, 80, 90),
            WriterLevel.EXPERT: (75, 85, 95),
        }
        min_score, target, excellent = base_values[self.writer_level]
        return QualityThreshold(min_score, target, excellent)


class QualityStandardRepository(ABC):
    """品質基準の永続化インターフェース"""

    @abstractmethod
    def get_standard(self, writer_level: WriterLevel, genre: Genre) -> QualityStandard:
        """品質基準を取得

        Args:
            writer_level: 執筆者レベル
            genre: ジャンル

        Returns:
            QualityStandard: 品質基準
        """
        msg = "get_standard must be implemented by subclasses"
        raise NotImplementedError(msg)

    @abstractmethod
    def save_standard(self, standard: QualityStandard) -> None:
        """品質基準を保存

        Args:
            standard: 保存する品質基準
        """
        msg = "save_standard must be implemented by subclasses"
        raise NotImplementedError(msg)


class WriterProgressRepository(ABC):
    """執筆者の進捗情報の永続化インターフェース"""

    @abstractmethod
    def get_completed_episodes_count(self, project_id: str) -> int:
        """完了したエピソード数を取得

        Args:
            project_id: プロジェクトID

        Returns:
            int: 完了エピソード数
        """
        msg = "get_completed_episodes_count must be implemented by subclasses"
        raise NotImplementedError(msg)

    @abstractmethod
    def get_average_quality_score(self, project_id: str) -> float:
        """平均品質スコアを取得

        Args:
            project_id: プロジェクトID

        Returns:
            float: 平均品質スコア
        """
        msg = "get_average_quality_score must be implemented by subclasses"
        raise NotImplementedError(msg)
