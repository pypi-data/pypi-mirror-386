# File: src/noveler/domain/services/section_analysis/optimization_engine.py
# Purpose: Provide section optimization logic extracted from legacy optimizer service.
# Context: Consumed by writing step orchestrators to adjust pacing, balance, and intensity.

"""最適化エンジンサービス

巨大なSectionBalanceOptimizerServiceから最適化機能を抽出。
セクション最適化アルゴリズムとバランス調整を担当。
"""

import time
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
from typing import Any

from noveler.domain.interfaces.logger_service_protocol import ILoggerService


@dataclass
class OptimizationRequest:
    """最適化リクエスト"""

    sections: list[dict[str, Any]]
    balance_requirements: dict[str, Any]
    target_metrics: dict[str, Any]
    constraints: dict[str, Any]


@dataclass
class OptimizationResult:
    """最適化結果"""

    optimized_sections: list[dict[str, Any]]
    optimization_score: float
    improvements: list[dict[str, Any]]
    warnings: list[str]
    execution_time: float


class OptimizationEngine:
    """最適化エンジンサービス

    責任:
    - セクション最適化アルゴリズム実行
    - バランス調整と改善提案
    - 最適化スコア計算
    - 制約条件の適用
    """

    def __init__(self, logger_service: ILoggerService | None = None) -> None:
        """最適化エンジン初期化

        Args:
            logger_service: ロガーサービス
        """
        self._logger = logger_service

    def optimize_sections(
        self,
        request: OptimizationRequest,
        *,
        log: Callable[[str, str], None] | None = None,
    ) -> OptimizationResult:
        """セクション最適化実行

        Args:
            request: 最適化リクエスト
            log: ログ収集用コールバック

        Returns:
            最適化結果
        """
        self._emit_log("info", "🔧 セクション最適化処理を開始...", log)
        start_time = time.time()

        # 最適化実行
        optimized_sections = self._execute_optimization(request)

        # 最適化スコア計算
        optimization_score = self._calculate_optimization_score(
            request.sections, optimized_sections, request.target_metrics
        )

        # 改善点の特定
        improvements = self._identify_improvements(request.sections, optimized_sections)

        # 警告の生成
        warnings = self._generate_warnings(optimized_sections, request.constraints)

        execution_time = time.time() - start_time

        return OptimizationResult(
            optimized_sections=optimized_sections,
            optimization_score=optimization_score,
            improvements=improvements,
            warnings=warnings,
            execution_time=execution_time,
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

    def _execute_optimization(self, request: OptimizationRequest) -> list[dict[str, Any]]:
        """最適化アルゴリズム実行

        Args:
            request: 最適化リクエスト

        Returns:
            最適化されたセクション
        """
        sections = request.sections.copy()

        # 長さ最適化
        sections = self._optimize_length_balance(sections, request.balance_requirements)

        # 強度最適化
        sections = self._optimize_intensity_curve(sections, request.balance_requirements)

        # ペーシング最適化
        sections = self._optimize_pacing_flow(sections, request.balance_requirements)

        # コンテンツバランス最適化
        return self._optimize_content_balance(sections, request.balance_requirements)

    def _optimize_length_balance(
        self, sections: list[dict[str, Any]], requirements: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """長さバランス最適化

        Args:
            sections: セクション情報
            requirements: バランス要件

        Returns:
            長さ最適化されたセクション
        """
        length_balance = requirements.get("length_balance", {})
        target_lengths = length_balance.get("target_lengths", [])

        if not target_lengths or len(target_lengths) != len(sections):
            return sections

        optimized_sections = []
        for i, section in enumerate(sections):
            optimized_section = section.copy()
            target_length = target_lengths[i]
            current_length = section.get("estimated_length", 1000)

            # 長さ調整の計算
            length_ratio = target_length / current_length if current_length > 0 else 1.0

            # 長さ調整をセクション情報に反映
            optimized_section["target_length"] = target_length
            optimized_section["length_adjustment_ratio"] = length_ratio
            optimized_section["estimated_length"] = target_length

            # 長さ変更による他要素への影響を計算
            if length_ratio != 1.0:
                optimized_section["requires_length_adjustment"] = True
                optimized_section["adjustment_suggestions"] = self._generate_length_adjustment_suggestions(
                    section, target_length, current_length
                )

            optimized_sections.append(optimized_section)

        return optimized_sections

    def _optimize_intensity_curve(
        self, sections: list[dict[str, Any]], requirements: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """強度カーブ最適化

        Args:
            sections: セクション情報
            requirements: バランス要件

        Returns:
            強度最適化されたセクション
        """
        intensity_balance = requirements.get("intensity_balance", {})
        ideal_curve = intensity_balance.get("ideal_intensity_curve", [])

        if not ideal_curve or len(ideal_curve) != len(sections):
            return sections

        optimized_sections = []
        for i, section in enumerate(sections):
            optimized_section = section.copy()
            target_intensity = ideal_curve[i]
            current_intensity = section.get("emotional_intensity", 0.5)

            # 強度調整
            optimized_section["target_emotional_intensity"] = target_intensity
            optimized_section["emotional_intensity"] = target_intensity

            # 強度変更による調整提案
            intensity_diff = abs(target_intensity - current_intensity)
            if intensity_diff > 0.1:  # 閾値を超える変更の場合
                optimized_section["requires_intensity_adjustment"] = True
                optimized_section["intensity_adjustment_suggestions"] = self._generate_intensity_adjustment_suggestions(
                    section, target_intensity, current_intensity
                )

            optimized_sections.append(optimized_section)

        return optimized_sections

    def _optimize_pacing_flow(
        self, sections: list[dict[str, Any]], requirements: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """ペーシングフロー最適化

        Args:
            sections: セクション情報
            requirements: バランス要件

        Returns:
            ペーシング最適化されたセクション
        """
        pacing_balance = requirements.get("pacing_balance", {})
        tempo_changes = pacing_balance.get("tempo_changes", {})

        optimized_sections = []
        for section in sections:
            optimized_section = section.copy()
            section_type = section.get("type", "narrative")

            # セクションタイプに基づくペーシング調整
            if section_type in tempo_changes:
                target_pace = tempo_changes[section_type]
                current_pacing = section.get("pacing_requirements", {})
                current_speed = current_pacing.get("speed", "medium")

                if current_speed != target_pace:
                    optimized_section["pacing_requirements"] = current_pacing.copy()
                    optimized_section["pacing_requirements"]["speed"] = target_pace
                    optimized_section["requires_pacing_adjustment"] = True
                    optimized_section["pacing_adjustment_suggestions"] = self._generate_pacing_adjustment_suggestions(
                        section, target_pace, current_speed
                    )

            optimized_sections.append(optimized_section)

        return optimized_sections

    def _optimize_content_balance(
        self, sections: list[dict[str, Any]], requirements: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """コンテンツバランス最適化

        Args:
            sections: セクション情報
            requirements: バランス要件

        Returns:
            コンテンツ最適化されたセクション
        """
        content_balance = requirements.get("content_balance", {})
        dialogue_range = content_balance.get("dialogue_target_range", (0.3, 0.6))
        action_range = content_balance.get("action_target_range", (0.2, 0.4))

        optimized_sections = []
        for section in sections:
            optimized_section = section.copy()
            characteristics = section.get("characteristics", {})

            # 会話比率の調整
            current_dialogue = characteristics.get("dialogue_ratio", 0.4)
            if not (dialogue_range[0] <= current_dialogue <= dialogue_range[1]):
                target_dialogue = max(dialogue_range[0], min(dialogue_range[1], current_dialogue))
                optimized_section.setdefault("characteristics", {})
                optimized_section["characteristics"]["dialogue_ratio"] = target_dialogue
                optimized_section["requires_content_adjustment"] = True

            # アクション比率の調整
            current_action = characteristics.get("action_ratio", 0.3)
            if not (action_range[0] <= current_action <= action_range[1]):
                target_action = max(action_range[0], min(action_range[1], current_action))
                optimized_section.setdefault("characteristics", {})
                optimized_section["characteristics"]["action_ratio"] = target_action
                optimized_section["requires_content_adjustment"] = True

            optimized_sections.append(optimized_section)

        return optimized_sections

    def _calculate_optimization_score(
        self,
        original_sections: list[dict[str, Any]],
        optimized_sections: list[dict[str, Any]],
        target_metrics: dict[str, Any],
    ) -> float:
        """最適化スコア計算

        Args:
            original_sections: 元のセクション
            optimized_sections: 最適化後のセクション
            target_metrics: 目標メトリクス

        Returns:
            最適化スコア（0.0-1.0）
        """
        scores = []

        # 長さバランススコア
        length_score = self._calculate_length_balance_score(optimized_sections)
        scores.append(length_score)

        # 強度バランススコア
        intensity_score = self._calculate_intensity_balance_score(optimized_sections)
        scores.append(intensity_score)

        # ペーシングスコア
        pacing_score = self._calculate_pacing_score(optimized_sections)
        scores.append(pacing_score)

        # コンテンツバランススコア
        content_score = self._calculate_content_balance_score(optimized_sections)
        scores.append(content_score)

        return sum(scores) / len(scores) if scores else 0.0

    def _identify_improvements(
        self, original_sections: list[dict[str, Any]], optimized_sections: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """改善点の特定

        Args:
            original_sections: 元のセクション
            optimized_sections: 最適化後のセクション

        Returns:
            改善点のリスト
        """
        improvements = []

        for i, (_original, optimized) in enumerate(zip(original_sections, optimized_sections, strict=False)):
            section_improvements = []

            # 長さ調整の改善
            if optimized.get("requires_length_adjustment"):
                section_improvements.append(
                    {
                        "type": "length_adjustment",
                        "description": "セクション長の調整が必要",
                        "suggestions": optimized.get("adjustment_suggestions", []),
                    }
                )

            # 強度調整の改善
            if optimized.get("requires_intensity_adjustment"):
                section_improvements.append(
                    {
                        "type": "intensity_adjustment",
                        "description": "感情強度の調整が必要",
                        "suggestions": optimized.get("intensity_adjustment_suggestions", []),
                    }
                )

            # ペーシング調整の改善
            if optimized.get("requires_pacing_adjustment"):
                section_improvements.append(
                    {
                        "type": "pacing_adjustment",
                        "description": "ペーシングの調整が必要",
                        "suggestions": optimized.get("pacing_adjustment_suggestions", []),
                    }
                )

            # コンテンツ調整の改善
            if optimized.get("requires_content_adjustment"):
                section_improvements.append(
                    {"type": "content_adjustment", "description": "コンテンツバランスの調整が必要"}
                )

            if section_improvements:
                improvements.append(
                    {
                        "section_index": i,
                        "section_title": optimized.get("title", f"セクション{i + 1}"),
                        "improvements": section_improvements,
                    }
                )

        return improvements

    def _generate_warnings(self, sections: list[dict[str, Any]], constraints: dict[str, Any]) -> list[str]:
        """警告の生成

        Args:
            sections: セクション情報
            constraints: 制約条件

        Returns:
            警告メッセージのリスト
        """
        warnings = []

        # 長さ制約チェック
        max_length = constraints.get("max_section_length")
        min_length = constraints.get("min_section_length")

        for i, section in enumerate(sections):
            length = section.get("estimated_length", 0)

            if max_length and length > max_length:
                warnings.append(f"セクション{i + 1}: 最大長制約違反 ({length} > {max_length})")

            if min_length and length < min_length:
                warnings.append(f"セクション{i + 1}: 最小長制約違反 ({length} < {min_length})")

        # バランス制約チェック
        total_length = sum(section.get("estimated_length", 0) for section in sections)
        target_total = constraints.get("target_total_length")

        if target_total and abs(total_length - target_total) > target_total * 0.1:
            warnings.append(f"総文字数が目標から大きく逸脱 ({total_length} vs {target_total})")

        return warnings

    def _generate_length_adjustment_suggestions(
        self, section: dict[str, Any], target_length: int, current_length: int
    ) -> list[str]:
        """長さ調整提案生成"""
        suggestions = []
        ratio = target_length / current_length if current_length > 0 else 1.0

        if ratio > 1.1:
            suggestions.extend(["詳細な描写を追加", "キャラクターの内面描写を充実", "場面の背景情報を補強"])
        elif ratio < 0.9:
            suggestions.extend(["冗長な表現を簡潔に", "重複する描写を統合", "核心的な要素に焦点を絞る"])

        return suggestions

    def _generate_intensity_adjustment_suggestions(
        self, section: dict[str, Any], target_intensity: float, current_intensity: float
    ) -> list[str]:
        """強度調整提案生成"""
        suggestions = []

        if target_intensity > current_intensity:
            suggestions.extend(["感情的な対立を強化", "緊張感のある展開を追加", "キャラクターの心理的葛藤を深化"])
        else:
            suggestions.extend(["穏やかな場面転換を挿入", "リフレクションの時間を設ける", "緊張を和らげる要素を追加"])

        return suggestions

    def _generate_pacing_adjustment_suggestions(
        self, section: dict[str, Any], target_pace: str, current_pace: str
    ) -> list[str]:
        """ペーシング調整提案生成"""
        suggestions = []

        pace_map = {"slow": 1, "medium": 2, "fast": 3}
        target_val = pace_map.get(target_pace, 2)
        current_val = pace_map.get(current_pace, 2)

        if target_val > current_val:
            suggestions.extend(["短い文章でテンポアップ", "アクション要素を追加", "会話のやり取りを活発に"])
        elif target_val < current_val:
            suggestions.extend(
                ["描写的な文章で間を作る", "キャラクターの思考時間を設ける", "情景描写でペースをゆっくりに"]
            )

        return suggestions

    def _calculate_length_balance_score(self, sections: list[dict[str, Any]]) -> float:
        """長さバランススコア計算"""
        lengths = [section.get("estimated_length", 1000) for section in sections]
        if not lengths:
            return 0.5

        mean_length = sum(lengths) / len(lengths)
        variance = sum((length - mean_length) ** 2 for length in lengths) / len(lengths)
        cv = (variance**0.5) / mean_length if mean_length > 0 else 1.0

        # 変動係数が小さいほど高スコア
        return max(0.0, 1.0 - cv)

    def _calculate_intensity_balance_score(self, sections: list[dict[str, Any]]) -> float:
        """強度バランススコア計算"""
        intensities = [section.get("emotional_intensity", 0.5) for section in sections]
        if not intensities:
            return 0.5

        # 理想的な上昇カーブとの適合度
        ideal_curve = self._create_ideal_intensity_curve(len(intensities))
        score = 0.0

        for actual, ideal in zip(intensities, ideal_curve, strict=False):
            diff = abs(actual - ideal)
            score += max(0.0, 1.0 - diff)

        return score / len(intensities) if intensities else 0.5

    def _calculate_pacing_score(self, sections: list[dict[str, Any]]) -> float:
        """ペーシングスコア計算"""
        # ペーシングの適切な変化があるかチェック
        pace_values = []
        pace_map = {"slow": 0.3, "medium": 0.6, "fast": 0.9}

        for section in sections:
            pacing = section.get("pacing_requirements", {})
            speed = pacing.get("speed", "medium")
            pace_values.append(pace_map.get(speed, 0.6))

        if len(pace_values) < 2:
            return 0.5

        # ペーシングの変化の適切性を評価
        total_variation = sum(abs(pace_values[i + 1] - pace_values[i]) for i in range(len(pace_values) - 1))
        optimal_variation = len(pace_values) * 0.2  # 理想的な変化量

        variation_score = 1.0 - abs(total_variation - optimal_variation) / optimal_variation
        return max(0.0, min(1.0, variation_score))

    def _calculate_content_balance_score(self, sections: list[dict[str, Any]]) -> float:
        """コンテンツバランススコア計算"""
        dialogue_ratios = []
        action_ratios = []

        for section in sections:
            characteristics = section.get("characteristics", {})
            dialogue_ratios.append(characteristics.get("dialogue_ratio", 0.4))
            action_ratios.append(characteristics.get("action_ratio", 0.3))

        # 各比率の適切性を評価
        dialogue_score = self._evaluate_ratio_balance(dialogue_ratios, (0.3, 0.6))
        action_score = self._evaluate_ratio_balance(action_ratios, (0.2, 0.4))

        return (dialogue_score + action_score) / 2

    def _evaluate_ratio_balance(self, ratios: list[float], target_range: tuple[float, float]) -> float:
        """比率バランスの評価"""
        if not ratios:
            return 0.5

        in_range_count = sum(1 for ratio in ratios if target_range[0] <= ratio <= target_range[1])
        return in_range_count / len(ratios)

    def _create_ideal_intensity_curve(self, section_count: int) -> list[float]:
        """理想的な強度カーブ作成"""
        curve = []
        for i in range(section_count):
            position = i / (section_count - 1) if section_count > 1 else 0
            # 3次関数的な上昇カーブ
            if position <= 0.75:
                intensity = 0.3 + (0.6 * (position / 0.75) ** 2)
            else:
                decay = (position - 0.75) / 0.25
                intensity = 0.9 - (0.2 * decay)
            curve.append(intensity)
        return curve
