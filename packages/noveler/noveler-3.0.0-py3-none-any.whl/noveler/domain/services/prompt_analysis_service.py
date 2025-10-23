#!/usr/bin/env python3
"""プロンプト効果分析モジュール
執筆記録からプロンプトの効果を分析
"""

from collections import defaultdict
from typing import Any


class PromptAnalyzer:
    """プロンプト効果分析専門クラス"""

    def analyze_all_records(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        """すべての記録からプロンプト効果を分析"""
        analysis = {
            "total_records": len(records),
            "effectiveness_distribution": defaultdict(int),
            "best_prompts": [],
            "categories": defaultdict(list),
        }

        for record in records:
            self._analyze_single_record(record, analysis)

        # 効果の高いプロンプトをソート
        analysis["best_prompts"].sort(
            key=lambda x: x.get("effectiveness", 0),
            reverse=True,
        )

        return dict(analysis)

    def _analyze_single_record(self, record: dict, analysis: dict[str, Any]) -> None:
        """単一記録を分析"""
        wr = record.get("writing_record", {})
        phase2 = wr.get("phase2_ai_writing", {})

        # Step1のプロンプトを分析
        step1 = phase2.get("step1_initial_draft", {})
        self._analyze_step_prompts(step1, "initial_draft", wr, analysis)

        # Step2aのプロンプトを分析
        step2a = phase2.get("step2a_structural_alignment", {})
        self._analyze_step_prompts(step2a, "structural", wr, analysis)

        # Step2bのプロンプトを分析
        step2b = phase2.get("step2b_emotional_optimization", {})
        self._analyze_step_prompts(step2b, "emotional", wr, analysis)

        # Step3のプロンプトを分析
        step3 = phase2.get("step3_final_polish", {})
        self._analyze_step_prompts(step3, "polish", wr, analysis)

    def _analyze_step_prompts(
        self, step_data: dict[str, Any], category: str, wr: dict[str, Any], analysis: dict[str, Any]
    ) -> None:
        """ステップごとのプロンプトを分析"""
        for prompt_data in step_data.get("prompts_used", []):
            effectiveness = prompt_data.get("effectiveness_rating", "medium")

            # 効果分布を記録
            analysis["effectiveness_distribution"][effectiveness] += 1

            # 高効果のプロンプトを保存
            if effectiveness in ["high", "very_high"]:
                prompt_info = {
                    "episode": wr.get("metadata", {}).get("episode_number", "Unknown"),
                    "category": category,
                    "prompt": prompt_data.get("prompt", ""),
                    "effectiveness": effectiveness,
                    "context": prompt_data.get("context", ""),
                }
                analysis["best_prompts"].append(prompt_info)
                analysis["categories"][category].append(prompt_info)

    def _effectiveness_score(self, rating: str) -> int:
        """効果評価をスコアに変換"""
        scores = {
            "very_high": 5,
            "high": 4,
            "medium": 3,
            "low": 2,
            "very_low": 1,
        }
        return scores.get(rating, 0)

    def get_category_statistics(self, records: list[dict[str, Any]]) -> dict[str, dict]:
        """カテゴリ別の統計を取得"""
        analysis = self.analyze_all_records(records)
        stats = {}

        for category, prompts in analysis["categories"].items():
            total = len(prompts)
            if total > 0:
                avg_score = sum(self._effectiveness_score(p["effectiveness"]) for p in prompts) / total

                stats[category] = {
                    "total_prompts": total,
                    "average_score": avg_score,
                    "best_prompt": prompts[0] if prompts else None,
                }

        return stats
