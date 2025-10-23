"""Domain.entities.contextual_plot_generation
Where: Domain entity modelling contextual plot generation data.
What: Combines prompts, context, and generated plot structures.
Why: Provides traceability for AI-assisted plot generation.
"""

from __future__ import annotations

"""ContextualPlotGeneration ドメインエンティティ

SPEC-PLOT-004: Enhanced Claude Code Integration Phase 2
コンテキスト駆動プロット生成のドメインエンティティ
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.project_time import project_now


@dataclass(frozen=True)
class PlotGenerationConfig:
    """プロット生成設定の値オブジェクト"""

    target_word_count: int = 5000
    technical_accuracy_required: bool = True
    character_consistency_check: bool = True
    scene_structure_enhanced: bool = False

    def is_valid(self) -> bool:
        """設定の妥当性検証"""
        return 3000 <= self.target_word_count <= 8000

    def to_dict(self) -> dict[str, Any]:
        """辞書形式への変換"""
        return {
            "target_word_count": self.target_word_count,
            "technical_accuracy_required": self.technical_accuracy_required,
            "character_consistency_check": self.character_consistency_check,
            "scene_structure_enhanced": self.scene_structure_enhanced,
        }


@dataclass(frozen=True)
class QualityIndicators:
    """品質指標の値オブジェクト"""

    technical_accuracy: float
    character_consistency: float
    plot_coherence: float
    overall_score: float | None = None

    def __post_init__(self) -> None:
        """初期化後処理: overall_scoreの自動計算"""
        if self.overall_score is None:
            # frozenなので、object.__setattr__を使用
            object.__setattr__(self, "overall_score", self.calculate_overall_score())

    def calculate_overall_score(self) -> float:
        """総合スコアの計算"""
        return (self.technical_accuracy + self.character_consistency + self.plot_coherence) / 3

    def meets_threshold(self, threshold: float) -> bool:
        """閾値チェック"""
        return self.calculate_overall_score() >= threshold

    def to_dict(self) -> dict[str, float]:
        """辞書形式への変換"""
        return {
            "technical_accuracy": self.technical_accuracy,
            "character_consistency": self.character_consistency,
            "plot_coherence": self.plot_coherence,
            "overall_score": self.overall_score or self.calculate_overall_score(),
        }


@dataclass
class ContextualPlotResult:
    """コンテキスト駆動プロット生成結果"""

    episode_number: EpisodeNumber
    content: dict[str, Any] | str  # YAML統合対応: 辞書も受け入れ可能
    quality_indicators: QualityIndicators
    generation_timestamp: datetime = field(default_factory=lambda: project_now().datetime)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """辞書形式への変換(YAML出力用)"""
        return {
            "episode_number": self.episode_number.value,
            "content": self.content,
            "quality_indicators": self.quality_indicators.to_dict(),
            "generation_timestamp": self.generation_timestamp.isoformat(),
            "metadata": self.metadata,
        }

    def meets_quality_threshold(self, threshold: float = 80.0) -> bool:
        """品質閾値の確認"""
        return self.quality_indicators.meets_threshold(threshold)


class ContextualPlotGeneration:
    """コンテキスト駆動プロット生成エンティティ

    DDD Entity として、以下の責務を持つ:
    - プロット生成のライフサイクル管理
    - コンテキスト情報の統合
    - 生成結果の品質管理
    """

    def __init__(
        self, episode_number: EpisodeNumber, config: PlotGenerationConfig, generation_id: str | None = None
    ) -> None:
        self._generation_id = generation_id or str(uuid.uuid4())
        self._episode_number = episode_number
        self._config = config
        self._status = "pending"
        self._context_data: dict[str, Any] = {}
        self._chapter_context: dict[str, Any] = {}
        self._creation_timestamp = project_now().datetime

    @property
    def generation_id(self) -> str:
        """生成ID(エンティティ識別子)"""
        return self._generation_id

    @property
    def episode_number(self) -> EpisodeNumber:
        """エピソード番号"""
        return self._episode_number

    @property
    def config(self) -> PlotGenerationConfig:
        """生成設定"""
        return self._config

    @property
    def status(self) -> str:
        """生成状態"""
        return self._status

    @property
    def context_data(self) -> dict[str, Any]:
        """コンテキストデータ"""
        return self._context_data.copy()

    @property
    def chapter_context(self) -> dict[str, Any]:
        """章コンテキスト"""
        return self._chapter_context.copy()

    @property
    def has_context_data(self) -> bool:
        """コンテキストデータの有無"""
        return bool(self._context_data)

    def update_context(self, context_data: dict[str, Any]) -> None:
        """コンテキストデータの更新"""
        self._context_data.update(context_data)
        self._status = "context_updated"

    def set_chapter_context(self, chapter_context: dict[str, Any]) -> None:
        """章コンテキストの設定"""
        self._chapter_context = chapter_context

    def get_technical_focus(self) -> list[str]:
        """技術要素フォーカスの取得"""
        return self._chapter_context.get("technical_focus", [])

    def start_generation(self) -> None:
        """生成開始"""
        if not self._config.is_valid():
            msg = "Invalid generation configuration"
            raise ValueError(msg)
        self._status = "generating"

    def complete_generation(self, result: ContextualPlotResult) -> None:
        """生成完了"""
        if result.episode_number != self._episode_number:
            msg = "Episode number mismatch in result"
            raise ValueError(msg)
        self._status = "completed"

    def fail_generation(self, error_message: str) -> None:
        """生成失敗"""
        self._status = "failed"

    def create_result(
        self, generated_content: str, quality_indicators: QualityIndicators, metadata: dict[str, Any] | None = None
    ) -> ContextualPlotResult:
        """生成結果の作成"""
        return ContextualPlotResult(
            episode_number=self._episode_number,
            content=generated_content,
            quality_indicators=quality_indicators,
            metadata=metadata or {},
        )

    def can_generate(self) -> bool:
        """生成可能かの判定"""
        return self._status in ["pending", "context_updated"] and self._config.is_valid()

    def to_dict(self) -> dict[str, Any]:
        """辞書形式への変換(永続化用)"""
        return {
            "generation_id": self._generation_id,
            "episode_number": self._episode_number.value,
            "config": self._config.to_dict(),
            "status": self._status,
            "context_data": self._context_data,
            "chapter_context": self._chapter_context,
            "creation_timestamp": self._creation_timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContextualPlotGeneration:
        """辞書からの復元"""
        instance = cls(
            episode_number=EpisodeNumber(data["episode_number"]),
            config=PlotGenerationConfig(**data["config"]),
            generation_id=data["generation_id"],
        )

        instance._status = data["status"]
        instance._context_data = data["context_data"]
        instance._chapter_context = data["chapter_context"]
        instance._creation_timestamp = datetime.fromisoformat(data["creation_timestamp"])
        return instance

    def __eq__(self, other: object) -> bool:
        """等価性比較(エンティティのID基準)"""
        if not isinstance(other, ContextualPlotGeneration):
            return False
        return self._generation_id == other._generation_id

    def __hash__(self) -> int:
        """ハッシュ値(エンティティのID基準)"""
        return hash(self._generation_id)
