"""Domain.services.writing_steps.character_consistency_service
Where: Domain service module implementing a specific writing workflow step.
What: Provides helper routines and data structures for this writing step.
Why: Allows stepwise writing orchestrators to reuse consistent step logic.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""キャラクター一貫性検証サービス

A38執筆プロンプトガイド STEP 6: キャラクター一貫性検証の実装。
キャラクター設定の矛盾チェックと一貫性保証。
"""

import time
from typing import Any

from noveler.domain.services.writing_steps.base_writing_step import (
    BaseWritingStep,
    WritingStepResponse,
)


class CharacterConsistencyService(BaseWritingStep):
    """キャラクター一貫性検証サービス

    A38 STEP 6: 設定されたキャラクターの一貫性を検証し、
    矛盾点を特定・修正提案を行う。
    """

    def __init__(self) -> None:
        super().__init__(
            step_number=6,
            step_name="キャラクター一貫性検証"
        )

    async def execute(
        self,
        episode_number: int,
        previous_results: dict[int, Any] | None = None
    ) -> WritingStepResponse:
        """キャラクター一貫性検証を実行

        Args:
            episode_number: エピソード番号
            previous_results: 前のステップの実行結果

        Returns:
            一貫性検証結果
        """
        start_time = time.time()

        try:
            # 前ステップの結果からキャラクター設定を取得
            character_settings = self._extract_character_settings(previous_results)

            # 一貫性検証実行
            consistency_check = self._validate_character_consistency(
                character_settings, episode_number
            )

            # 矛盾点の修正提案
            corrections = self._generate_corrections(consistency_check)

            # 実行時間計算
            execution_time = (time.time() - start_time) * 1000

            return WritingStepResponse(
                success=True,
                step_number=self.step_number,
                step_name=self.step_name,
                execution_time_ms=execution_time,
                data={
                    "character_consistency": consistency_check,
                    "corrections": corrections,
                    "validated_characters": len(character_settings),
                    "inconsistencies_found": len(corrections)
                }
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return WritingStepResponse(
                success=False,
                step_number=self.step_number,
                step_name=self.step_name,
                execution_time_ms=execution_time,
                error_message=str(e)
            )

    def _extract_character_settings(self, previous_results: dict[int, Any] | None) -> dict[str, Any]:
        """前ステップからキャラクター設定を抽出"""
        if not previous_results:
            return {}

        characters = {}

        # STEP 0-5からキャラクター関連情報を収集
        for result in previous_results.values():
            if hasattr(result, "data") and result.data:
                # キャラクター設定データを抽出
                if "characters" in result.data:
                    characters.update(result.data["characters"])
                elif "character_profiles" in result.data:
                    characters.update(result.data["character_profiles"])

        return characters

    def _validate_character_consistency(self, characters: dict[str, Any], episode_number: int) -> dict[str, Any]:
        """キャラクター一貫性を検証"""
        consistency_report = {
            "overall_score": 0.0,
            "character_checks": {},
            "cross_character_consistency": {},
            "timeline_consistency": {}
        }

        if not characters:
            return consistency_report

        total_score = 0.0
        character_count = len(characters)

        for char_name, char_data in characters.items():
            char_consistency = self._check_single_character(char_name, char_data, episode_number)
            consistency_report["character_checks"][char_name] = char_consistency
            total_score += char_consistency["consistency_score"]

        # 全体スコア計算
        if character_count > 0:
            consistency_report["overall_score"] = total_score / character_count

        # キャラクター間の関係性一貫性
        consistency_report["cross_character_consistency"] = self._check_character_relationships(characters)

        # タイムライン一貫性
        consistency_report["timeline_consistency"] = self._check_timeline_consistency(characters, episode_number)

        return consistency_report

    def _check_single_character(self, char_name: str, char_data: dict[str, Any], episode_number: int) -> dict[str, Any]:
        """単一キャラクターの一貫性チェック"""
        checks = {
            "consistency_score": 8.0,  # デフォルト高スコア
            "issues": [],
            "strengths": [],
            "recommendations": []
        }

        # 基本情報の一貫性チェック
        if not char_data.get("name") or not char_data.get("role"):
            checks["issues"].append("基本情報（名前・役割）が不完全")
            checks["consistency_score"] -= 2.0
        else:
            checks["strengths"].append("基本情報が適切に設定済み")

        # 性格設定の一貫性
        personality = char_data.get("personality", {})
        if not personality or len(personality) < 3:
            checks["issues"].append("性格設定が不十分（3つ以上の特徴が必要）")
            checks["consistency_score"] -= 1.5
        else:
            checks["strengths"].append("性格設定が詳細で一貫性がある")

        # 動機・目標の明確性
        if not char_data.get("motivation") and not char_data.get("goal"):
            checks["issues"].append("動機・目標が不明確")
            checks["consistency_score"] -= 1.0
        else:
            checks["strengths"].append("明確な動機・目標設定")

        # 改善提案
        if checks["consistency_score"] < 7.0:
            checks["recommendations"].append("キャラクター設定の詳細化が必要")
        if not char_data.get("backstory"):
            checks["recommendations"].append("背景設定の追加を推奨")

        return checks

    def _check_character_relationships(self, characters: dict[str, Any]) -> dict[str, Any]:
        """キャラクター間関係の一貫性チェック"""
        relationships = {
            "consistency_score": 8.5,
            "relationship_matrix": {},
            "conflicts": [],
            "recommendations": []
        }

        char_names = list(characters.keys())

        # 関係性マトリクス作成
        for i, char1 in enumerate(char_names):
            for _j, char2 in enumerate(char_names[i+1:], i+1):
                rel_key = f"{char1}-{char2}"

                # 相互関係の一貫性確認
                char1_relations = characters[char1].get("relationships", {})
                char2_relations = characters[char2].get("relationships", {})

                char1_view = char1_relations.get(char2, "未設定")
                char2_view = char2_relations.get(char1, "未設定")

                relationships["relationship_matrix"][rel_key] = {
                    "char1_view": char1_view,
                    "char2_view": char2_view,
                    "consistent": self._are_relationships_consistent(char1_view, char2_view)
                }

                if not relationships["relationship_matrix"][rel_key]["consistent"]:
                    relationships["conflicts"].append(f"{char1}と{char2}の関係認識に矛盾")
                    relationships["consistency_score"] -= 0.5

        return relationships

    def _check_timeline_consistency(self, characters: dict[str, Any], episode_number: int) -> dict[str, Any]:
        """タイムライン一貫性チェック"""
        timeline = {
            "consistency_score": 9.0,
            "timeline_issues": [],
            "character_arcs": {},
            "recommendations": []
        }

        for char_name, char_data in characters.items():
            # キャラクター成長弧の確認
            arc_data = char_data.get("character_arc", {})
            current_state = arc_data.get(f"episode_{episode_number}", {})

            timeline["character_arcs"][char_name] = {
                "current_episode": episode_number,
                "development_stage": current_state.get("stage", "初期"),
                "growth_trajectory": arc_data.get("trajectory", "未定義")
            }

            # 成長の一貫性チェック
            if not current_state:
                timeline["timeline_issues"].append(f"{char_name}の第{episode_number}話での状態が未定義")
                timeline["consistency_score"] -= 0.3

        return timeline

    def _generate_corrections(self, consistency_check: dict[str, Any]) -> list[dict[str, Any]]:
        """一貫性チェック結果から修正提案を生成"""
        corrections = []

        # 個別キャラクターの問題
        for char_name, char_check in consistency_check.get("character_checks", {}).items():
            for issue in char_check.get("issues", []):
                corrections.append({
                    "type": "character_issue",
                    "character": char_name,
                    "issue": issue,
                    "priority": "high" if char_check["consistency_score"] < 6.0 else "medium",
                    "suggestion": f"{char_name}の{issue}を詳細化してください"
                })

        # 関係性の矛盾
        rel_check = consistency_check.get("cross_character_consistency", {})
        for conflict in rel_check.get("conflicts", []):
            corrections.append({
                "type": "relationship_conflict",
                "issue": conflict,
                "priority": "high",
                "suggestion": f"相互の関係認識を統一してください: {conflict}"
            })

        # タイムラインの問題
        timeline_check = consistency_check.get("timeline_consistency", {})
        for timeline_issue in timeline_check.get("timeline_issues", []):
            corrections.append({
                "type": "timeline_issue",
                "issue": timeline_issue,
                "priority": "medium",
                "suggestion": f"キャラクター状態の時系列定義が必要: {timeline_issue}"
            })

        return corrections

    def _are_relationships_consistent(self, view1: str, view2: str) -> bool:
        """関係性認識の一貫性判定"""
        if view1 == "未設定" or view2 == "未設定":
            return False

        # 対立関係の組み合わせチェック
        antagonistic_pairs = [
            ("敵対", "敵対"), ("ライバル", "ライバル"),
            ("警戒", "警戒"), ("不信", "不信")
        ]

        positive_pairs = [
            ("友人", "友人"), ("同盟", "同盟"),
            ("信頼", "信頼"), ("協力", "協力")
        ]

        # 非対称な関係も考慮
        asymmetric_valid = [
            ("師匠", "弟子"), ("弟子", "師匠"),
            ("保護者", "被保護者"), ("被保護者", "保護者"),
            ("上司", "部下"), ("部下", "上司")
        ]

        pair = (view1, view2)
        reverse_pair = (view2, view1)

        return (
            pair in antagonistic_pairs or
            pair in positive_pairs or
            pair in asymmetric_valid or
            reverse_pair in asymmetric_valid
        )
