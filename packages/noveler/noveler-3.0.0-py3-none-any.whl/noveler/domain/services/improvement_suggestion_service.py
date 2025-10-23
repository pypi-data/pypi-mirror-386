#!/usr/bin/env python3

"""Domain.services.improvement_suggestion_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""改善提案サービス
品質記録活用システムのドメインサービス
"""


from typing import Any

from noveler.domain.entities.quality_record_enhancement import QualityRecordEnhancement
from noveler.domain.value_objects.improvement_suggestion import ImprovementSuggestion
from noveler.domain.value_objects.learning_metrics import LearningMetrics


class ImprovementSuggestionService:
    """改善提案サービス

    品質記録データから個人化された改善提案を生成するドメインサービス
    """

    def __init__(self, confidence_threshold: float) -> None:
        self.confidence_threshold = confidence_threshold
        self.category_thresholds = {
            "basic_style": 70.0,
            "composition": 75.0,
            "character_consistency": 80.0,
            "readability": 75.0,
        }

    def generate_improvement_suggestions(
        self, quality_record: QualityRecordEnhancement, user_profile: dict[str, Any]
    ) -> list[ImprovementSuggestion]:
        """改善提案を生成"""

        # 前提条件チェック
        quality_record.generate_improvement_suggestions_precondition_check()

        suggestions = []

        # 弱点領域の特定
        weak_categories = self._identify_weak_categories(quality_record)

        # 各弱点に対する提案生成
        for category in weak_categories:
            suggestion = self._generate_category_suggestion(category, quality_record, user_profile)
            if suggestion:
                suggestions.append(suggestion)

        # ユーザープロファイルに基づく追加提案
        profile_suggestions = self._generate_profile_based_suggestions(quality_record, user_profile)
        suggestions.extend(profile_suggestions)

        # 優先度による並び替え
        return self._sort_suggestions_by_priority(suggestions)

    def _identify_weak_categories(self, quality_record: QualityRecordEnhancement) -> list[str]:
        """弱点カテゴリを特定"""
        latest_scores = quality_record.get_latest_scores()
        weak_categories = []

        for category, score in latest_scores.items():
            threshold = self.category_thresholds.get(category, 75.0)
            if score < threshold:
                weak_categories.append(category)

        return weak_categories

    def _generate_category_suggestion(
        self, category: str, quality_record: QualityRecordEnhancement, user_profile: dict[str, Any]
    ) -> ImprovementSuggestion | None:
        """カテゴリ別改善提案を生成"""

        latest_scores = quality_record.get_latest_scores()
        category_score = latest_scores.get(category, 0.0)

        # カテゴリ別の提案テンプレート
        suggestion_templates = {
            "basic_style": self._generate_basic_style_suggestion,
            "composition": self._generate_composition_suggestion,
            "character_consistency": self._generate_character_suggestion,
            "readability": self._generate_readability_suggestion,
        }

        generator = suggestion_templates.get(category)
        if generator:
            return generator(category_score, user_profile)

        return None

    def _generate_basic_style_suggestion(self, score: float, _user_profile: dict[str, Any]) -> ImprovementSuggestion:
        """基本文体の改善提案を生成"""

        if score < 60.0:
            return ImprovementSuggestion(
                category="basic_style",
                priority="high",
                title="基本的な文体を改善しましょう",
                description="文章の基本的な構造や表現に改善の余地があります",
                specific_actions=[
                    "一文を短く簡潔に書く",
                    "同じ表現の繰り返しを避ける",
                    "適切な句読点を使用する",
                    "冗長な修飾語を削除する",
                ],
                estimated_impact=8.0,
                confidence=0.85,
            )

        if score < 70.0:
            return ImprovementSuggestion(
                category="basic_style",
                priority="medium",
                title="文体の表現力を向上させましょう",
                description="基本的な文体は身についていますが、表現の幅を広げることができます",
                specific_actions=[
                    "同義語を使ったバリエーションを増やす",
                    "感情表現を豊かにする",
                    "リズム感のある文章を心がける",
                ],
                estimated_impact=6.5,
                confidence=0.75,
            )

        return ImprovementSuggestion(
            category="basic_style",
            priority="low",
            title="文体の洗練度を高めましょう",
            description="良い文体が身についています。さらに洗練させることで読者の印象を深めることができます",
            specific_actions=["比喩表現を効果的に使う", "文章のリズムを意識する", "読者の感情に響く表現を選ぶ"],
            estimated_impact=4.0,
            confidence=0.70,
        )

    def _generate_composition_suggestion(self, score: float, _user_profile: dict[str, Any]) -> ImprovementSuggestion:
        """構成の改善提案を生成"""

        if score < 70.0:
            return ImprovementSuggestion(
                category="composition",
                priority="high",
                title="ストーリー構成を見直しましょう",
                description="話の流れや構成に改善の余地があります",
                specific_actions=[
                    "起承転結を明確にする",
                    "段落の区切りを適切に行う",
                    "話の論理的な流れを確認する",
                    "読者が理解しやすい順序で情報を提示する",
                ],
                estimated_impact=7.5,
                confidence=0.80,
            )

        if score < 80.0:
            return ImprovementSuggestion(
                category="composition",
                priority="medium",
                title="構成の完成度を高めましょう",
                description="基本的な構成は良好ですが、より効果的な構成に改善できます",
                specific_actions=[
                    "クライマックスの位置を最適化する",
                    "伏線の配置を工夫する",
                    "読者の興味を引く導入部を作る",
                ],
                estimated_impact=6.0,
                confidence=0.75,
            )

        return ImprovementSuggestion(
            category="composition",
            priority="low",
            title="構成の芸術性を追求しましょう",
            description="優れた構成力があります。さらに芸術的な構成を目指すことができます",
            specific_actions=["独特な構成手法を試す", "読者の予想を裏切る展開を作る", "テーマに沿った構成を意識する"],
            estimated_impact=3.5,
            confidence=0.70,
        )

    def _generate_character_suggestion(self, _score: float, _user_profile: dict[str, Any]) -> ImprovementSuggestion:
        """キャラクター描写の改善提案を生成"""

        return ImprovementSuggestion(
            category="character_consistency",
            priority="medium",
            title="キャラクターの一貫性を保ちましょう",
            description="キャラクターの行動や性格に一貫性を持たせることで、読者の理解が深まります",
            specific_actions=[
                "キャラクターの性格設定を明確にする",
                "行動の動機を明確にする",
                "過去の行動と矛盾しないよう注意する",
            ],
            estimated_impact=7.0,
            confidence=0.75,
        )

    def _generate_readability_suggestion(self, _score: float, _user_profile: dict[str, Any]) -> ImprovementSuggestion:
        """読みやすさの改善提案を生成"""

        return ImprovementSuggestion(
            category="readability",
            priority="high",
            title="読みやすさを改善しましょう",
            description="文章の読みやすさを向上させることで、読者の理解度が高まります",
            specific_actions=["難しい漢字にはひらがなを使う", "文章の長さを適切に調整する", "専門用語は説明を加える"],
            estimated_impact=8.5,
            confidence=0.80,
        )

    def _generate_profile_based_suggestions(
        self, _quality_record: QualityRecordEnhancement, user_profile: dict[str, Any]
    ) -> list[ImprovementSuggestion]:
        """ユーザープロファイルに基づく提案を生成"""

        suggestions = []
        writer_level = user_profile.get("writer_level", "beginner")
        user_profile.get("focus_areas", [])

        # 初心者向けの追加提案
        if writer_level == "beginner":
            suggestions.append(
                ImprovementSuggestion(
                    category="general",
                    priority="medium",
                    title="継続的な執筆習慣を身につけましょう",
                    description="定期的な執筆が上達の鍵です",
                    specific_actions=["毎日決まった時間に執筆する", "短時間でも継続的に書く", "執筆記録をつける"],
                    estimated_impact=6.0,
                    confidence=0.85,
                )
            )

        return suggestions

    def _sort_suggestions_by_priority(self, suggestions: list[ImprovementSuggestion]) -> list[ImprovementSuggestion]:
        """優先度による並び替え"""

        priority_order = {"high": 3, "medium": 2, "low": 1}

        return sorted(suggestions, key=lambda s: (priority_order[s.priority], s.estimated_impact), reverse=True)

    def generate_suggestions(
        self, quality_history: list[Any], user_profile: dict[str, Any]
    ) -> list[ImprovementSuggestion]:
        """品質履歴から改善提案を生成(互換性メソッド)"""

        # 品質記録エンハンスメントオブジェクトを作成
        enhancement = QualityRecordEnhancement(project_name="テンプレート", version="1.0")

        # 履歴データを追加
        for i, record in enumerate(quality_history):
            if hasattr(record, "category_scores"):
                metrics = LearningMetrics(improvement_from_previous=0.0, time_spent_writing=60, revision_count=1)

                enhancement.add_quality_check_result(
                    episode_number=i + 1,
                    category_scores=record.category_scores,
                    errors=[],
                    warnings=[],
                    auto_fixes=[],
                    learning_metrics=metrics,
                )

        # ユーザープロファイルを辞書形式に変換
        profile_dict = {}
        if hasattr(user_profile, "skill_level"):
            profile_dict["writer_level"] = user_profile.skill_level

        return self.generate_improvement_suggestions(enhancement, profile_dict)

    def prioritize_suggestions(self, suggestions: list[Any], current_context: dict[str, Any]) -> list[Any]:
        """提案の優先度付け(互換性メソッド)"""

        # 現在のコンテキストに基づいて優先度を調整
        if hasattr(current_context, "focus_area"):
            focus_area = current_context.focus_area

            # フォーカス領域に関連する提案を優先
            prioritized = []
            other_suggestions = []

            for suggestion in suggestions:
                if hasattr(suggestion, "category") and suggestion.category == focus_area:
                    prioritized.append(suggestion)
                else:
                    other_suggestions.append(suggestion)

            return prioritized + other_suggestions

        return suggestions
