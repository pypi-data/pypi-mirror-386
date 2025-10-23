#!/usr/bin/env python3
"""AI協創技法効果分析モジュール
執筆記録から各種技法の効果を分析
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TechniqueStats:
    """技法統計のデータクラス"""

    total_attempts: int = 0
    successful_attempts: int = 0
    improvements: list[float] = field(default_factory=list)
    best_examples: list[dict] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """成功率を計算"""
        if self.total_attempts == 0:
            return 0.0
        return (self.successful_attempts / self.total_attempts) * 100

    @property
    def average_improvement(self) -> float:
        """平均改善率を計算"""
        if not self.improvements:
            return 0.0
        return sum(self.improvements) / len(self.improvements)


class TechniqueAnalyzer:
    """AI協創技法分析専門クラス"""

    def analyze_all_records(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        """すべての記録から技法の効果を分析"""
        emotion_stats = TechniqueStats()
        narou_stats = TechniqueStats()

        for record in records:
            self._analyze_emotion_conversion(record, emotion_stats)
            self._analyze_narou_optimization(record, narou_stats)

        return {
            "emotion_conversion": self._format_emotion_stats(emotion_stats),
            "narou_optimization": self._format_narou_stats(narou_stats),
            "total_records": len(records),
        }

    def _analyze_emotion_conversion(self, record: dict[str, Any], stats: object) -> None:
        """感情変換技法を分析"""
        wr = record.get("writing_record", {})
        phase2 = wr.get("phase2_ai_writing", {})
        step2b = phase2.get("step2b_emotional_optimization", {})
        emotion_conv = step2b.get("emotion_conversion", {})

        if not emotion_conv:
            return

        # 試行回数と成功回数を集計
        total = emotion_conv.get("total_attempts", 0)
        successful = emotion_conv.get("successful_conversions", 0)

        stats.total_attempts += total
        stats.successful_attempts += successful

        # 成功率を記録
        if total > 0:
            success_rate = (successful / total) * 100
            stats.improvements.append(success_rate)

        # 優秀な変換例を収集
        for example in emotion_conv.get("conversion_examples", []):
            if example.get("effectiveness") in ["high", "very_high"]:
                stats.best_examples.append(
                    {
                        "episode": wr.get("metadata", {}).get("episode_number"),
                        "original": example.get("original"),
                        "converted": example.get("converted"),
                        "effectiveness": example.get("effectiveness"),
                    },
                )

    def _analyze_narou_optimization(self, record: dict[str, Any], stats: object) -> None:
        """なろう最適化技法を分析"""
        wr = record.get("writing_record", {})
        phase2 = wr.get("phase2_ai_writing", {})
        step2b = phase2.get("step2b_emotional_optimization", {})
        narou_opt = step2b.get("narou_optimization", {})

        if not narou_opt:
            return

        # 会話文率の改善を分析
        dialogue_adj = narou_opt.get("dialogue_adjustment", {})
        if dialogue_adj:
            initial = dialogue_adj.get("initial_ratio", 0)
            final = dialogue_adj.get("final_ratio", 0)

            if initial > 0:
                improvement = ((final - initial) / initial) * 100
                stats.improvements.append(improvement)
                stats.total_attempts += 1

                # 目標範囲(30-40%)に収まったら成功
                if 30 <= final <= 40:
                    stats.successful_attempts += 1

        # 優秀な最適化例を収集
        if narou_opt.get("effectiveness_rating") in ["high", "very_high"]:
            stats.best_examples.append(
                {
                    "episode": wr.get("metadata", {}).get("episode_number"),
                    "technique": "dialogue_adjustment",
                    "before": initial,
                    "after": final,
                    "improvement": improvement,
                },
            )

    def _format_emotion_stats(self, stats: object) -> dict[str, Any]:
        """感情変換統計をフォーマット"""
        return {
            "total_attempts": stats.total_attempts,
            "total_successful": stats.successful_attempts,
            "avg_success_rate": stats.success_rate,
            "best_examples": stats.best_examples[:5],  # 上位5件
        }

    def _format_narou_stats(self, stats: object) -> dict[str, Any]:
        """なろう最適化統計をフォーマット"""
        return {
            "total_optimizations": stats.total_attempts,
            "successful_optimizations": stats.successful_attempts,
            "avg_improvement": stats.average_improvement,
            "dialogue_improvements": stats.improvements,
            "best_examples": stats.best_examples[:5],  # 上位5件
        }

    def get_technique_recommendations(
        self,
        analysis: dict[str, Any],
    ) -> list[str]:
        """分析結果から推奨事項を生成"""
        recommendations = []

        # 感情変換の推奨事項
        emotion_conv = analysis.get("emotion_conversion", {})
        if emotion_conv.get("avg_success_rate", 0) < 50:
            recommendations.append(
                "感情変換の成功率が低いです。変換例を増やすか、プロンプトを調整することを推奨します。",
            )

        # なろう最適化の推奨事項
        narou_opt = analysis.get("narou_optimization", {})
        if narou_opt.get("avg_improvement", 0) < 10:
            recommendations.append(
                "なろう最適化の改善率が低いです。会話文の配置や展開を見直すことを推奨します。",
            )

        return recommendations
