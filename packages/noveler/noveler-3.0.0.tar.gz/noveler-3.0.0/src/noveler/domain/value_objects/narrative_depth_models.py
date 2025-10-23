"""Domain.value_objects.narrative_depth_models
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

from __future__ import annotations

"""内面描写深度評価のドメインモデル。

小説における心理描写、感情表現、内面的葛藤などの深度を評価するための
ドメインモデルを定義する。
"""


from dataclasses import dataclass
from enum import Enum


class DepthLayer(Enum):
    """内面描写の層"""

    SENSORY = "感覚層"  # 身体感覚の描写
    EMOTIONAL = "感情層"  # 感情の直接表現
    COGNITIVE = "思考層"  # 内的独白・思考過程
    MEMORIAL = "記憶層"  # 過去との対比・想起
    SYMBOLIC = "象徴層"  # 比喩・暗喩・象徴表現


@dataclass(frozen=True)
class LayerScore:
    """各層のスコア値オブジェクト"""

    layer: DepthLayer
    score: float
    max_score: float = 20.0

    def __post_init__(self) -> None:
        if not 0 <= self.score <= self.max_score:
            msg = f"Score must be between 0 and {self.max_score}"
            raise ValueError(msg)

    @property
    def percentage(self) -> float:
        """パーセンテージ表現"""
        return (self.score / self.max_score) * 100


@dataclass(frozen=True)
class NarrativeDepthScore:
    """内面描写深度の総合スコア"""

    layer_scores: dict[DepthLayer, LayerScore]

    def __post_init__(self) -> None:
        # 全ての層が含まれているか確認
        required_layers = set(DepthLayer)
        actual_layers = set(self.layer_scores.keys())
        if required_layers != actual_layers:
            msg = "All depth layers must be included"
            raise ValueError(msg)

    @property
    def total_score(self) -> float:
        """重み付け総合スコア(0-100)"""
        weights = {
            DepthLayer.SENSORY: 0.15,
            DepthLayer.EMOTIONAL: 0.20,
            DepthLayer.COGNITIVE: 0.30,
            DepthLayer.MEMORIAL: 0.20,
            DepthLayer.SYMBOLIC: 0.15,
        }

        total = sum(self.layer_scores[layer].percentage * weights[layer] for layer in DepthLayer)

        # 複数層の有機的結合ボーナス
        if self._has_organic_combination():
            total *= 1.2
            total = min(total, 100.0)  # 100を超えないように

        return round(total, 1)

    def _has_organic_combination(self) -> bool:
        """複数層が有機的に結合しているか判定"""
        high_scores = sum(1 for score in self.layer_scores.values() if score.percentage >= 60)
        return high_scores >= 3


@dataclass(frozen=True)
class TextSegment:
    """評価対象のテキストセグメント"""

    content: str
    start_position: int
    end_position: int

    def __post_init__(self) -> None:
        if not self.content:
            msg = "Content cannot be empty"
            raise ValueError(msg)
        if self.start_position < 0 or self.end_position < self.start_position:
            msg = "Invalid position range"
            raise ValueError(msg)


@dataclass(frozen=True)
class DepthPattern:
    """深度評価用のパターン"""

    pattern: str
    layer: DepthLayer
    depth_level: int  # 1-3の深度レベル
    weight: float = 1.0

    def __post_init__(self) -> None:
        if not 1 <= self.depth_level <= 3:
            msg = "Depth level must be between 1 and 3"
            raise ValueError(msg)
        if self.weight <= 0:
            msg = "Weight must be positive"
            raise ValueError(msg)
