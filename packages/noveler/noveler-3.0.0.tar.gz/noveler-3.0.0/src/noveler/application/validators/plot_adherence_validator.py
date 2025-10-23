#!/usr/bin/env python3

"""Application.validators.plot_adherence_validator
Where: Application validator verifying plot adherence rules.
What: Evaluates manuscripts against expected plot beats and constraints.
Why: Helps authors avoid deviations from planned plot structure.
"""

from __future__ import annotations

"""プロット準拠検証バリデーター

執筆原稿とプロットの準拠性を検証するアプリケーション層バリデーター
SPEC-PLOT-ADHERENCE-001準拠実装
"""


from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

# 既存実装活用（B20準拠）
# B20準拠: 共有コンポーネント必須使用
from noveler.presentation.shared.shared_utilities import get_logger

if TYPE_CHECKING:
    from pathlib import Path

logger = get_logger(__name__)


class AdherenceElementType(Enum):
    """プロット要素タイプ"""

    KEY_EVENT = "key_event"
    CHARACTER_DEVELOPMENT = "character_development"
    WORLD_BUILDING = "world_building"
    FORESHADOWING = "foreshadowing"


@dataclass
class PlotElement:
    """プロット要素値オブジェクト"""

    element_type: AdherenceElementType
    description: str
    required: bool = True
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AdherenceScore:
    """準拠率値オブジェクト"""

    total_score: float  # 0-100
    element_scores: dict[AdherenceElementType, float] = field(default_factory=dict)
    implemented_count: int = 0
    total_count: int = 0

    @property
    def is_excellent(self) -> bool:
        """優秀評価判定（95%以上）"""
        return self.total_score >= 95.0

    @property
    def is_acceptable(self) -> bool:
        """許容評価判定（80%以上）"""
        return self.total_score >= 80.0


@dataclass
class PlotAdherenceResult:
    """プロット準拠検証結果"""

    episode_number: int
    adherence_score: AdherenceScore
    missing_elements: list[PlotElement] = field(default_factory=list)
    extra_elements: list[PlotElement] = field(default_factory=list)
    improvement_suggestions: list[str] = field(default_factory=list)
    validation_timestamp: str | None = None


class PlotAdherenceValidator:
    """プロット準拠検証バリデーター

    執筆完了後の原稿がプロット要件を満たしているかを検証する。
    SPEC-PLOT-ADHERENCE-001の中核コンポーネント。
    """

    def __init__(self) -> None:
        """初期化"""
        self.logger = logger
        # 要素別重み設定（仕様書準拠）
        self._element_weights = {
            AdherenceElementType.KEY_EVENT: 0.4,
            AdherenceElementType.CHARACTER_DEVELOPMENT: 0.3,
            AdherenceElementType.WORLD_BUILDING: 0.2,
            AdherenceElementType.FORESHADOWING: 0.1,
        }

    async def validate_adherence(
        self, episode_number: int, manuscript_content: str, plot_data: dict[str, Any], project_root: Path | None = None
    ) -> PlotAdherenceResult:
        """プロット準拠性検証メイン処理

        Args:
            episode_number: エピソード番号
            manuscript_content: 執筆完了原稿
            plot_data: プロットデータ（YAML形式）
            project_root: プロジェクトルートパス

        Returns:
            PlotAdherenceResult: 検証結果
        """
        self.logger.info(f"プロット準拠検証開始: 第{episode_number:03d}話")

        try:
            # プロット要素抽出
            plot_elements = await self._extract_plot_elements(plot_data)

            # 原稿内容分析
            manuscript_elements = await self._analyze_manuscript_content(manuscript_content)

            # 準拠性評価
            adherence_score = await self._calculate_adherence_score(plot_elements, manuscript_elements)

            # 不足・過剰要素検出
            missing_elements = await self._detect_missing_elements(plot_elements, manuscript_elements)
            extra_elements = await self._detect_extra_elements(plot_elements, manuscript_elements)

            # 改善提案生成
            improvement_suggestions = await self._generate_improvement_suggestions(
                missing_elements, extra_elements, adherence_score
            )

            result = PlotAdherenceResult(
                episode_number=episode_number,
                adherence_score=adherence_score,
                missing_elements=missing_elements,
                extra_elements=extra_elements,
                improvement_suggestions=improvement_suggestions,
            )

            self.logger.info(f"プロット準拠検証完了: 第{episode_number:03d}話 準拠率{adherence_score.total_score:.1f}%")

            return result

        except Exception as e:
            self.logger.exception(f"プロット準拠検証エラー: {e}")
            # フォールバック結果を返す
            return PlotAdherenceResult(
                episode_number=episode_number,
                adherence_score=AdherenceScore(total_score=0.0),
                improvement_suggestions=[f"検証エラー: {e!s}"],
            )

    async def _extract_plot_elements(self, plot_data: dict[str, Any]) -> list[PlotElement]:
        """プロットデータから検証要素を抽出

        Args:
            plot_data: プロットYAMLデータ

        Returns:
            List[PlotElement]: プロット要素リスト
        """
        elements = []

        # キーイベント抽出
        key_events = plot_data.get("key_events", [])
        for event in key_events:
            elements.append(
                PlotElement(element_type=AdherenceElementType.KEY_EVENT, description=str(event), required=True)
            )

        # キャラクター要素抽出
        character_elements = plot_data.get("character_development", [])
        for char_element in character_elements:
            elements.append(
                PlotElement(
                    element_type=AdherenceElementType.CHARACTER_DEVELOPMENT,
                    description=str(char_element),
                    required=True,
                )
            )

        # 世界観要素抽出
        world_elements = plot_data.get("world_building", [])
        for world_element in world_elements:
            elements.append(
                PlotElement(
                    element_type=AdherenceElementType.WORLD_BUILDING, description=str(world_element), required=True
                )
            )

        # 伏線要素抽出
        foreshadowing_elements = plot_data.get("foreshadowing", [])
        for foreshadow_element in foreshadowing_elements:
            elements.append(
                PlotElement(
                    element_type=AdherenceElementType.FORESHADOWING, description=str(foreshadow_element), required=True
                )
            )

        self.logger.debug(f"抽出されたプロット要素: {len(elements)}個")
        return elements

    async def _analyze_manuscript_content(self, manuscript: str) -> list[PlotElement]:
        """原稿内容を分析して実装要素を検出

        Args:
            manuscript: 原稿テキスト

        Returns:
            List[PlotElement]: 実装されている要素リスト
        """
        # TODO: NLP分析による要素検出実装
        # 現在はプレースホルダー実装
        elements = []

        # キーワードベースの簡易分析
        if "ギルド" in manuscript:
            elements.append(
                PlotElement(element_type=AdherenceElementType.WORLD_BUILDING, description="ギルドの描写", required=True)
            )

        if "主人公" in manuscript or "彼" in manuscript:
            elements.append(
                PlotElement(
                    element_type=AdherenceElementType.CHARACTER_DEVELOPMENT, description="主人公の描写", required=True
                )
            )

        self.logger.debug(f"分析された原稿要素: {len(elements)}個")
        return elements

    async def _calculate_adherence_score(
        self, plot_elements: list[PlotElement], manuscript_elements: list[PlotElement]
    ) -> AdherenceScore:
        """準拠率を計算

        Args:
            plot_elements: プロット要素
            manuscript_elements: 原稿実装要素

        Returns:
            AdherenceScore: 算出された準拠率
        """
        element_scores = {}
        total_weighted_score = 0.0

        for element_type in AdherenceElementType:
            plot_count = len([e for e in plot_elements if e.element_type == element_type])
            impl_count = len([e for e in manuscript_elements if e.element_type == element_type])

            if plot_count > 0:
                type_score = min(impl_count / plot_count, 1.0) * 100
            else:
                type_score = 100.0  # 要求されていない要素は満点

            element_scores[element_type] = type_score
            weight = self._element_weights.get(element_type, 0.0)
            total_weighted_score += type_score * weight

        return AdherenceScore(
            total_score=total_weighted_score,
            element_scores=element_scores,
            implemented_count=len(manuscript_elements),
            total_count=len(plot_elements),
        )

    async def _detect_missing_elements(
        self, plot_elements: list[PlotElement], manuscript_elements: list[PlotElement]
    ) -> list[PlotElement]:
        """不足要素を検出

        Args:
            plot_elements: プロット要素
            manuscript_elements: 原稿実装要素

        Returns:
            List[PlotElement]: 不足している要素
        """
        # TODO: より精密な要素マッチング実装
        # 現在は簡易実装
        missing = []

        for plot_element in plot_elements:
            # 原稿に対応する要素があるかチェック（簡易版）
            has_matching = any(m.element_type == plot_element.element_type for m in manuscript_elements)

            if not has_matching:
                missing.append(plot_element)

        return missing

    async def _detect_extra_elements(
        self, plot_elements: list[PlotElement], manuscript_elements: list[PlotElement]
    ) -> list[PlotElement]:
        """過剰要素を検出

        Args:
            plot_elements: プロット要素
            manuscript_elements: 原稿実装要素

        Returns:
            List[PlotElement]: 過剰な要素
        """
        # TODO: 過剰要素の検出実装
        # 現在は空リストを返す
        return []

    async def _generate_improvement_suggestions(
        self, missing_elements: list[PlotElement], extra_elements: list[PlotElement], adherence_score: AdherenceScore
    ) -> list[str]:
        """改善提案を生成

        Args:
            missing_elements: 不足要素
            extra_elements: 過剰要素
            adherence_score: 準拠率

        Returns:
            List[str]: 改善提案リスト
        """
        suggestions = []

        # 不足要素に基づく提案
        for missing in missing_elements:
            if missing.element_type == AdherenceElementType.KEY_EVENT:
                suggestions.append(f"重要イベントの描写を追加: {missing.description}")
            elif missing.element_type == AdherenceElementType.CHARACTER_DEVELOPMENT:
                suggestions.append(f"キャラクター描写を強化: {missing.description}")
            elif missing.element_type == AdherenceElementType.WORLD_BUILDING:
                suggestions.append(f"世界観描写を追加: {missing.description}")
            elif missing.element_type == AdherenceElementType.FORESHADOWING:
                suggestions.append(f"伏線の設置を検討: {missing.description}")

        # 準拠率に基づく全体提案
        if adherence_score.total_score < 80.0:
            suggestions.append("プロットの見直しと原稿の大幅な改善が推奨されます")
        elif adherence_score.total_score < 95.0:
            suggestions.append("細部の調整でより高品質な原稿になります")
        else:
            suggestions.append("優秀な準拠率です。このまま公開品質を維持してください")

        return suggestions
