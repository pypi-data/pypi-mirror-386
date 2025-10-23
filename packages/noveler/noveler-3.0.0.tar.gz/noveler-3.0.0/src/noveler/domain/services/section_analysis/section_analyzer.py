"""セクション分析サービス

巨大なSectionBalanceOptimizerServiceから分析機能を抽出。
セクション構造の分析と特性評価を担当。
"""

from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
from typing import Any

from noveler.domain.interfaces.logger_service_protocol import ILoggerService


@dataclass
class SectionAnalysisResult:
    """セクション分析結果"""

    structure_assessment: dict[str, Any]
    natural_sections: list[dict[str, Any]]
    section_characteristics: list[dict[str, Any]]
    narrative_weights: list[float]
    emotional_intensities: list[float]
    pacing_requirements: list[dict[str, Any]]
    engagement_levels: list[float]


class SectionAnalyzer:
    """セクション分析サービス

    責任:
    - セクション構造の評価
    - 自然なセクション境界の特定
    - セクション特性の分析
    - 物語的重み付けの計算
    """

    def __init__(self, logger_service: ILoggerService | None = None) -> None:
        """セクション分析サービス初期化

        Args:
            logger_service: ロガーサービス
        """
        self._logger = logger_service

    def analyze_section_structure(
        self,
        plot_data: dict[str, Any],
        phase_structure: dict[str, Any],
        *,
        log: Callable[[str, str], None] | None = None,
        **_: object,
    ) -> SectionAnalysisResult:
        """セクション構造の包括的分析

        Args:
            plot_data: プロット情報
            phase_structure: フェーズ構造情報
            log: ログ収集用コールバック
            **_: 未使用の追加パラメータ（互換性維持用）

        Returns:
            セクション分析結果
        """
        self._emit_log("info", "📊 セクション構造分析を開始...", log)

        # 現在の構造評価
        structure_assessment = self._assess_current_structure(plot_data, phase_structure)

        # 自然なセクション境界の特定
        natural_sections = self._identify_natural_sections(plot_data, phase_structure)

        # セクション特性の分析
        section_characteristics = []
        narrative_weights = []
        emotional_intensities = []
        pacing_requirements = []
        engagement_levels = []

        for section in natural_sections:
            # 各セクションの分析
            section_type = self._classify_section_type(section)
            characteristics = self._analyze_section_characteristics(section, section_type)
            section_characteristics.append(characteristics)

            # 物語的重み付け計算
            narrative_weight = self._calculate_narrative_weight(section, phase_structure)
            narrative_weights.append(narrative_weight)

            # 感情的強度の推定
            emotional_intensity = self._estimate_emotional_intensity(section)
            emotional_intensities.append(emotional_intensity)

            # ペーシング要件の決定
            pacing_req = self._determine_pacing_requirements(section, section_type)
            pacing_requirements.append(pacing_req)

            # エンゲージメントレベルの推定
            engagement_level = self._estimate_engagement_level(section, characteristics)
            engagement_levels.append(engagement_level)

        return SectionAnalysisResult(
            structure_assessment=structure_assessment,
            natural_sections=natural_sections,
            section_characteristics=section_characteristics,
            narrative_weights=narrative_weights,
            emotional_intensities=emotional_intensities,
            pacing_requirements=pacing_requirements,
            engagement_levels=engagement_levels,
        )

    def _emit_log(
        self,
        level: str,
        message: str,
        log: Callable[[str, str], None] | None = None,
    ) -> None:
        """Emit log messages to callback and optional logger service."""
        if log is not None:
            with suppress(Exception):
                log(level, message)
        if self._logger is None:
            return
        log_method = getattr(self._logger, level, None)
        if callable(log_method):
            with suppress(Exception):  # pragma: no cover - logger misconfiguration
                log_method(message)

    def _assess_current_structure(self, plot_data: dict[str, Any], phase_structure: dict[str, Any]) -> dict[str, Any]:
        """現在の構造を評価

        Args:
            plot_data: プロット情報
            phase_structure: フェーズ構造

        Returns:
            構造評価結果
        """
        return {
            "coherence_score": 0.7,
            "balance_score": 0.6,
            "flow_score": 0.8,
            "structural_issues": [],
            "strengths": ["明確なフェーズ区分", "一貫したテーマ"],
            "weaknesses": ["セクション長のばらつき", "強度変化の急激さ"],
        }

    def _identify_natural_sections(
        self, plot_data: dict[str, Any], phase_structure: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """自然なセクション境界を特定

        Args:
            plot_data: プロット情報
            phase_structure: フェーズ構造

        Returns:
            特定されたセクションのリスト
        """
        sections = []

        # フェーズ情報からセクションを生成
        phases = phase_structure.get("phases", [])
        for i, phase in enumerate(phases):
            section = {
                "id": f"section_{i + 1}",
                "title": phase.get("name", f"セクション{i + 1}"),
                "phase": phase.get("name", ""),
                "start_position": phase.get("start_position", 0),
                "end_position": phase.get("end_position", 100),
                "content_type": phase.get("content_type", "narrative"),
                "themes": phase.get("themes", []),
                "plot_points": phase.get("plot_points", []),
            }
            sections.append(section)

        return sections

    def _classify_section_type(self, section: dict[str, Any]) -> str:
        """セクションタイプを分類

        Args:
            section: セクション情報

        Returns:
            セクションタイプ
        """
        content_type = section.get("content_type", "")
        phase_name = section.get("phase", "")

        if "導入" in phase_name or "beginning" in content_type:
            return "introduction"
        if "展開" in phase_name or "development" in content_type:
            return "development"
        if "クライマックス" in phase_name or "climax" in content_type:
            return "climax"
        if "結末" in phase_name or "resolution" in content_type:
            return "resolution"
        return "narrative"

    def _analyze_section_characteristics(self, section: dict[str, Any], section_type: str) -> dict[str, Any]:
        """セクション特性を分析

        Args:
            section: セクション情報
            section_type: セクションタイプ

        Returns:
            セクション特性
        """
        return {
            "type": section_type,
            "length_estimate": 800,  # 推定文字数
            "complexity": "medium",
            "dialogue_ratio": 0.4,
            "action_ratio": 0.3,
            "description_ratio": 0.2,
            "internal_thought_ratio": 0.1,
            "key_elements": section.get("plot_points", []),
        }

    def _calculate_narrative_weight(self, section: dict[str, Any], phase_structure: dict[str, Any]) -> float:
        """物語的重み付けを計算

        Args:
            section: セクション情報
            phase_structure: フェーズ構造

        Returns:
            物語的重み（0.0-1.0）
        """
        plot_points = len(section.get("plot_points", []))
        themes = len(section.get("themes", []))

        # プロットポイントとテーマ数に基づく重み付け
        weight = min(1.0, (plot_points * 0.3 + themes * 0.2) / 3.0)
        return max(0.1, weight)  # 最小値0.1を保証

    def _estimate_emotional_intensity(self, section: dict[str, Any]) -> float:
        """感情的強度を推定

        Args:
            section: セクション情報

        Returns:
            感情的強度（0.0-1.0）
        """
        section_type = section.get("type", "narrative")

        intensity_map = {"climax": 0.9, "resolution": 0.7, "development": 0.6, "introduction": 0.4, "narrative": 0.5}

        return intensity_map.get(section_type, 0.5)

    def _determine_pacing_requirements(self, section: dict[str, Any], section_type: str) -> dict[str, Any]:
        """ペーシング要件を決定

        Args:
            section: セクション情報
            section_type: セクションタイプ

        Returns:
            ペーシング要件
        """
        pacing_map = {
            "introduction": {"speed": "slow", "rhythm": "steady", "variation": "low"},
            "development": {"speed": "medium", "rhythm": "varied", "variation": "medium"},
            "climax": {"speed": "fast", "rhythm": "intense", "variation": "high"},
            "resolution": {"speed": "slow", "rhythm": "gentle", "variation": "low"},
        }

        return pacing_map.get(section_type, {"speed": "medium", "rhythm": "steady", "variation": "medium"})

    def _estimate_engagement_level(self, section: dict[str, Any], characteristics: dict[str, Any]) -> float:
        """エンゲージメントレベルを推定

        Args:
            section: セクション情報
            characteristics: セクション特性

        Returns:
            エンゲージメントレベル（0.0-1.0）
        """
        base_engagement = 0.5

        # セクションタイプによる調整
        section_type = characteristics.get("type", "narrative")
        type_multiplier = {
            "climax": 1.4,
            "development": 1.1,
            "resolution": 0.9,
            "introduction": 0.8,
            "narrative": 1.0,
        }.get(section_type, 1.0)

        # 会話比率による調整（会話が多いほどエンゲージメント向上）
        dialogue_bonus = characteristics.get("dialogue_ratio", 0.4) * 0.3

        # アクション比率による調整
        action_bonus = characteristics.get("action_ratio", 0.3) * 0.2

        engagement = base_engagement * type_multiplier + dialogue_bonus + action_bonus
        return min(1.0, max(0.1, engagement))
