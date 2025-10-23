"""バランス計算サービス

セクション間のバランス計算と要件決定を担当。
長さ、強度、ペーシング、コンテンツのバランスを計算。
"""

from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
from typing import Any

from noveler.domain.interfaces.logger_service_protocol import ILoggerService


@dataclass
class BalanceRequirements:
    """バランス要件"""

    length_balance: dict[str, Any]
    intensity_balance: dict[str, Any]
    pacing_balance: dict[str, Any]
    content_balance: dict[str, Any]
    reader_experience_requirements: dict[str, Any]


@dataclass
class BalanceMetrics:
    """バランス指標"""

    overall_balance_score: float
    length_distribution: list[float]
    intensity_curve: list[float]
    pacing_variation: list[float]
    content_ratios: list[dict[str, float]]
    engagement_consistency: float


class BalanceCalculator:
    """バランス計算サービス

    責任:
    - セクション間のバランス要件計算
    - 長さ、強度、ペーシング、コンテンツバランスの評価
    - 最適バランスの設計
    """

    def __init__(self, logger_service: ILoggerService | None = None) -> None:
        """バランス計算サービス初期化

        Args:
            logger_service: ロガーサービス
        """
        self._logger = logger_service

    def calculate_balance_requirements(
        self,
        sections: list[dict[str, Any]],
        phase_structure: dict[str, Any],
        target_episode_length: int = 10000,
        *,
        log: Callable[[str, str], None] | None = None,
    ) -> BalanceRequirements:
        """セクションバランス要件を計算

        Args:
            sections: セクション情報リスト
            phase_structure: フェーズ構造
            target_episode_length: 目標エピソード長
            log: ログ収集用コールバック

        Returns:
            計算されたバランス要件
        """
        self._emit_log("info", "⚖️ バランス要件計算を開始...", log)

        # 長さバランス要件
        length_balance = self._determine_length_balance_requirements(sections, target_episode_length)

        # 強度バランス要件
        intensity_balance = self._determine_intensity_balance_requirements(sections, phase_structure)

        # ペーシングバランス要件
        pacing_balance = self._determine_pacing_balance_requirements(sections, phase_structure)

        # コンテンツバランス要件
        content_balance = self._determine_content_balance_requirements(sections)

        # 読者体験要件
        reader_experience_requirements = self._determine_reader_experience_requirements(sections, phase_structure)

        return BalanceRequirements(
            length_balance=length_balance,
            intensity_balance=intensity_balance,
            pacing_balance=pacing_balance,
            content_balance=content_balance,
            reader_experience_requirements=reader_experience_requirements,
        )

    def assess_current_balance(
        self,
        sections: list[dict[str, Any]],
        requirements: BalanceRequirements,
        *,
        log: Callable[[str, str], None] | None = None,
    ) -> BalanceMetrics:
        """現在のバランスを評価

        Args:
            sections: セクション情報
            requirements: バランス要件
            log: ログ収集用コールバック

        Returns:
            バランス評価指標
        """
        self._emit_log("info", "📊 現在のバランス評価を実行...", log)

        # 全体バランススコア計算
        overall_score = self._calculate_overall_balance_score(sections, requirements)

        # 長さ分布計算
        length_distribution = self._calculate_length_distribution(sections)

        # 強度カーブ計算
        intensity_curve = self._calculate_intensity_curve(sections)

        # ペーシング変動計算
        pacing_variation = self._calculate_pacing_variation(sections)

        # コンテンツ比率計算
        content_ratios = self._calculate_content_ratios(sections)

        # エンゲージメント一貫性計算
        engagement_consistency = self._calculate_engagement_consistency(sections)

        return BalanceMetrics(
            overall_balance_score=overall_score,
            length_distribution=length_distribution,
            intensity_curve=intensity_curve,
            pacing_variation=pacing_variation,
            content_ratios=content_ratios,
            engagement_consistency=engagement_consistency,
        )

    def _determine_length_balance_requirements(
        self, sections: list[dict[str, Any]], target_length: int
    ) -> dict[str, Any]:
        """長さバランス要件を決定

        Args:
            sections: セクション情報
            target_length: 目標総文字数

        Returns:
            長さバランス要件
        """
        section_count = len(sections)
        base_length = target_length // section_count

        # セクションタイプ別の長さ調整
        length_multipliers = {
            "introduction": 0.8,
            "development": 1.1,
            "climax": 1.3,
            "resolution": 0.9,
            "narrative": 1.0,
        }

        target_lengths = []
        for section in sections:
            section_type = section.get("type", "narrative")
            multiplier = length_multipliers.get(section_type, 1.0)
            target_lengths.append(int(base_length * multiplier))

        return {
            "target_lengths": target_lengths,
            "total_target": sum(target_lengths),
            "variance_tolerance": 0.15,  # ±15%の許容範囲
            "min_section_length": int(base_length * 0.6),
            "max_section_length": int(base_length * 1.5),
        }

    def _determine_intensity_balance_requirements(
        self, sections: list[dict[str, Any]], phase_structure: dict[str, Any]
    ) -> dict[str, Any]:
        """強度バランス要件を決定

        Args:
            sections: セクション情報
            phase_structure: フェーズ構造

        Returns:
            強度バランス要件
        """
        # 理想的な強度カーブを設計
        section_count = len(sections)
        ideal_curve = self._design_ideal_intensity_curve(section_count)

        return {
            "ideal_intensity_curve": ideal_curve,
            "peak_positions": [int(section_count * 0.75)],  # 3/4地点にピーク
            "valley_positions": [0, section_count - 1],  # 開始と終了で低強度
            "smooth_transitions": True,
            "intensity_variance": 0.2,  # 隣接セクション間の最大変動
            "overall_trend": "ascending",  # 全体的には上昇傾向
        }

    def _determine_pacing_balance_requirements(
        self, sections: list[dict[str, Any]], phase_structure: dict[str, Any]
    ) -> dict[str, Any]:
        """ペーシングバランス要件を決定

        Args:
            sections: セクション情報
            phase_structure: フェーズ構造

        Returns:
            ペーシングバランス要件
        """
        return {
            "pace_variation_pattern": "gradual_acceleration",
            "rhythm_consistency": 0.8,  # リズムの一貫性レベル
            "tempo_changes": {"introduction": "slow", "development": "medium", "climax": "fast", "resolution": "slow"},
            "transition_smoothness": 0.9,
            "reader_fatigue_prevention": True,
        }

    def _determine_content_balance_requirements(self, sections: list[dict[str, Any]]) -> dict[str, Any]:
        """コンテンツバランス要件を決定

        Args:
            sections: セクション情報

        Returns:
            コンテンツバランス要件
        """
        return {
            "dialogue_target_range": (0.3, 0.6),  # 会話比率の目標範囲
            "action_target_range": (0.2, 0.4),  # アクション比率
            "description_target_range": (0.15, 0.3),  # 描写比率
            "internal_thought_target_range": (0.05, 0.2),  # 内的思考比率
            "variety_requirement": True,  # バラエティの確保
            "genre_specific_adjustments": {
                "action": {"action_ratio": 0.5},
                "romance": {"dialogue_ratio": 0.6},
                "mystery": {"internal_thought_ratio": 0.25},
            },
        }

    def _determine_reader_experience_requirements(
        self, sections: list[dict[str, Any]], phase_structure: dict[str, Any]
    ) -> dict[str, Any]:
        """読者体験要件を決定

        Args:
            sections: セクション情報
            phase_structure: フェーズ構造

        Returns:
            読者体験要件
        """
        return {
            "engagement_minimum": 0.6,  # 最低エンゲージメントレベル
            "interest_sustainability": True,
            "cognitive_load_management": True,
            "emotional_journey_smoothness": 0.8,
            "satisfaction_delivery_points": [
                len(sections) // 3,  # 1/3地点
                2 * len(sections) // 3,  # 2/3地点
                len(sections) - 1,  # 最終地点
            ],
            "immersion_consistency": 0.85,
        }

    def _calculate_overall_balance_score(
        self, sections: list[dict[str, Any]], requirements: BalanceRequirements
    ) -> float:
        """全体バランススコアを計算

        Args:
            sections: セクション情報
            requirements: バランス要件

        Returns:
            全体バランススコア（0.0-1.0）
        """
        scores = []

        # 長さバランススコア
        length_score = self._evaluate_length_balance(sections, requirements.length_balance)
        scores.append(length_score)

        # 強度バランススコア
        intensity_score = self._evaluate_intensity_balance(sections, requirements.intensity_balance)
        scores.append(intensity_score)

        # ペーシングバランススコア
        pacing_score = self._evaluate_pacing_balance(sections, requirements.pacing_balance)
        scores.append(pacing_score)

        # コンテンツバランススコア
        content_score = self._evaluate_content_balance(sections, requirements.content_balance)
        scores.append(content_score)

        return sum(scores) / len(scores)

    def _design_ideal_intensity_curve(self, section_count: int) -> list[float]:
        """理想的な強度カーブを設計

        Args:
            section_count: セクション数

        Returns:
            理想的な強度値のリスト
        """
        curve = []
        for i in range(section_count):
            # 3次関数的な上昇カーブ
            position = i / (section_count - 1) if section_count > 1 else 0
            # 0.3で開始し、0.75地点で最高値0.9、最後に0.7で終了
            if position <= 0.75:
                intensity = 0.3 + (0.6 * (position / 0.75) ** 2)
            else:
                # 最後は少し下げる
                decay = (position - 0.75) / 0.25
                intensity = 0.9 - (0.2 * decay)
            curve.append(intensity)
        return curve

    def _calculate_length_distribution(self, sections: list[dict[str, Any]]) -> list[float]:
        """長さ分布を計算

        Args:
            sections: セクション情報

        Returns:
            各セクションの相対的長さ
        """
        lengths = [section.get("estimated_length", 1000) for section in sections]
        total_length = sum(lengths)
        return [length / total_length for length in lengths]

    def _calculate_intensity_curve(self, sections: list[dict[str, Any]]) -> list[float]:
        """強度カーブを計算

        Args:
            sections: セクション情報

        Returns:
            各セクションの強度値
        """
        return [section.get("emotional_intensity", 0.5) for section in sections]

    def _calculate_pacing_variation(self, sections: list[dict[str, Any]]) -> list[float]:
        """ペーシング変動を計算

        Args:
            sections: セクション情報

        Returns:
            各セクションのペーシング値
        """
        pace_values = []
        for section in sections:
            pacing = section.get("pacing_requirements", {})
            speed = pacing.get("speed", "medium")
            speed_map = {"slow": 0.3, "medium": 0.6, "fast": 0.9}
            pace_values.append(speed_map.get(speed, 0.6))
        return pace_values

    def _calculate_content_ratios(self, sections: list[dict[str, Any]]) -> list[dict[str, float]]:
        """コンテンツ比率を計算

        Args:
            sections: セクション情報

        Returns:
            各セクションのコンテンツ比率
        """
        ratios = []
        for section in sections:
            characteristics = section.get("characteristics", {})
            ratio = {
                "dialogue": characteristics.get("dialogue_ratio", 0.4),
                "action": characteristics.get("action_ratio", 0.3),
                "description": characteristics.get("description_ratio", 0.2),
                "internal_thought": characteristics.get("internal_thought_ratio", 0.1),
            }
            ratios.append(ratio)
        return ratios

    def _calculate_engagement_consistency(self, sections: list[dict[str, Any]]) -> float:
        """エンゲージメント一貫性を計算

        Args:
            sections: セクション情報

        Returns:
            エンゲージメント一貫性スコア
        """
        engagement_levels = [section.get("engagement_level", 0.5) for section in sections]
        if not engagement_levels:
            return 0.5

        # 変動係数を使用して一貫性を評価
        mean_engagement = sum(engagement_levels) / len(engagement_levels)
        variance = sum((x - mean_engagement) ** 2 for x in engagement_levels) / len(engagement_levels)
        std_dev = variance**0.5

        # 変動係数が小さいほど一貫性が高い
        cv = std_dev / mean_engagement if mean_engagement > 0 else 1.0
        return max(0.0, 1.0 - cv)

    def _evaluate_length_balance(self, sections: list[dict[str, Any]], requirements: dict[str, Any]) -> float:
        """長さバランスを評価"""
        target_lengths = requirements.get("target_lengths", [])
        if not target_lengths:
            return 0.5

        actual_lengths = [section.get("estimated_length", 1000) for section in sections]
        score = 0.0

        for actual, target in zip(actual_lengths, target_lengths, strict=False):
            ratio = min(actual, target) / max(actual, target)
            score += ratio

        return score / len(target_lengths)

    def _evaluate_intensity_balance(self, sections: list[dict[str, Any]], requirements: dict[str, Any]) -> float:
        """強度バランスを評価"""
        ideal_curve = requirements.get("ideal_intensity_curve", [])
        actual_intensities = [section.get("emotional_intensity", 0.5) for section in sections]

        if not ideal_curve or not actual_intensities:
            return 0.5

        score = 0.0
        for actual, ideal in zip(actual_intensities, ideal_curve, strict=False):
            # 差分の逆数でスコア化
            diff = abs(actual - ideal)
            section_score = max(0.0, 1.0 - diff)
            score += section_score

        return score / len(ideal_curve)

    def _evaluate_pacing_balance(self, sections: list[dict[str, Any]], requirements: dict[str, Any]) -> float:
        """ペーシングバランスを評価"""
        # 簡略化された評価
        return 0.75  # プレースホルダー値

    def _evaluate_content_balance(self, sections: list[dict[str, Any]], requirements: dict[str, Any]) -> float:
        """コンテンツバランスを評価"""
        # 簡略化された評価
        return 0.8  # プレースホルダー値

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
