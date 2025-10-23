#!/usr/bin/env python3
"""手動分析品質検証サービス

自動分析結果が手動Claude Code分析レベルに達しているかを
定量的に検証・測定するドメインサービス。
"""

from dataclasses import dataclass
from statistics import mean
from typing import Any

from noveler.domain.entities.category_analysis_result import CategoryAnalysisResult
from noveler.domain.value_objects.a31_evaluation_category import A31EvaluationCategory
from noveler.domain.value_objects.line_specific_feedback import LineSpecificFeedback


@dataclass
class ManualAnalysisStandard:
    """手動分析品質基準"""

    category: A31EvaluationCategory
    min_issues_identified: int  # 最低検出すべき問題数
    min_suggestions_quality: float  # 改善提案の最低品質スコア
    min_specificity_score: float  # 具体性の最低スコア
    min_actionability_score: float  # 実行可能性の最低スコア
    expected_feedback_types: list[str]  # 期待されるフィードバック種別
    manual_benchmark_score: float  # 手動分析ベンチマークスコア


@dataclass
class QualityValidationResult:
    """品質検証結果"""

    category: A31EvaluationCategory
    manual_analysis_level_achieved: bool  # 手動分析レベル達成判定
    quality_gap_score: float  # 品質ギャップスコア（0-100、0が完全一致）
    specificity_score: float  # 具体性スコア
    actionability_score: float  # 実行可能性スコア
    coverage_score: float  # 問題カバレッジスコア
    improvement_areas: list[str]  # 改善領域
    detailed_feedback: str  # 詳細フィードバック
    confidence_level: float  # 検証信頼度


class ManualAnalysisQualityValidator:
    """手動分析品質検証サービス

    自動分析結果を手動Claude Code分析の品質基準と照合し、
    到達度を定量評価するサービス。
    """

    def __init__(self) -> None:
        """手動分析品質検証サービス初期化"""
        self._manual_standards = self._initialize_manual_standards()
        self._quality_metrics = self._initialize_quality_metrics()

    def validate_analysis_quality(
        self, category_result: CategoryAnalysisResult, line_feedbacks: list[LineSpecificFeedback], episode_content: str
    ) -> QualityValidationResult:
        """分析品質の検証

        Args:
            category_result: カテゴリ分析結果
            line_feedbacks: 行別フィードバック
            episode_content: エピソード内容

        Returns:
            QualityValidationResult: 品質検証結果
        """
        category = category_result.category
        standard = self._manual_standards.get(category)

        if not standard:
            return self._create_default_validation_result(category)

        # 具体性評価
        specificity_score = self._evaluate_specificity(category_result, line_feedbacks)

        # 実行可能性評価
        actionability_score = self._evaluate_actionability(category_result, line_feedbacks)

        # カバレッジ評価
        coverage_score = self._evaluate_coverage(category_result, line_feedbacks, episode_content, standard)

        # 品質ギャップ計算
        quality_gap = self._calculate_quality_gap(
            category_result, standard, specificity_score, actionability_score, coverage_score
        )

        # 手動分析レベル達成判定
        manual_level_achieved = self._assess_manual_level_achievement(
            quality_gap, specificity_score, actionability_score, coverage_score, standard
        )

        # 改善領域特定
        improvement_areas = self._identify_improvement_areas(
            category_result, line_feedbacks, standard, specificity_score, actionability_score, coverage_score
        )

        # 詳細フィードバック生成
        detailed_feedback = self._generate_detailed_feedback(
            category, quality_gap, improvement_areas, manual_level_achieved
        )

        # 検証信頼度計算
        confidence_level = self._calculate_validation_confidence(category_result, line_feedbacks, episode_content)

        return QualityValidationResult(
            category=category,
            manual_analysis_level_achieved=manual_level_achieved,
            quality_gap_score=quality_gap,
            specificity_score=specificity_score,
            actionability_score=actionability_score,
            coverage_score=coverage_score,
            improvement_areas=improvement_areas,
            detailed_feedback=detailed_feedback,
            confidence_level=confidence_level,
        )

    def validate_overall_quality(
        self,
        category_results: list[CategoryAnalysisResult],
        all_line_feedbacks: list[LineSpecificFeedback],
        episode_content: str,
    ) -> dict[str, Any]:
        """全体品質検証

        Args:
            category_results: 全カテゴリ分析結果
            all_line_feedbacks: 全行別フィードバック
            episode_content: エピソード内容

        Returns:
            dict[str, Any]: 全体検証結果
        """
        category_validations = []

        # カテゴリ別検証実行
        for category_result in category_results:
            category_feedbacks = [
                fb for fb in all_line_feedbacks if self._is_feedback_for_category(fb, category_result.category)
            ]

            validation = self.validate_analysis_quality(category_result, category_feedbacks, episode_content)

            category_validations.append(validation)

        # 全体統計計算
        manual_level_categories = [v for v in category_validations if v.manual_analysis_level_achieved]
        overall_manual_level_rate = (
            len(manual_level_categories) / len(category_validations) if category_validations else 0
        )

        avg_quality_gap = mean([v.quality_gap_score for v in category_validations]) if category_validations else 100.0
        avg_specificity = mean([v.specificity_score for v in category_validations]) if category_validations else 0.0
        avg_actionability = mean([v.actionability_score for v in category_validations]) if category_validations else 0.0
        avg_coverage = mean([v.coverage_score for v in category_validations]) if category_validations else 0.0

        # 全体改善提案
        all_improvement_areas = []
        for validation in category_validations:
            all_improvement_areas.extend(validation.improvement_areas)

        unique_improvements = list(set(all_improvement_areas))

        # 全体評価
        overall_assessment = self._generate_overall_assessment(
            overall_manual_level_rate, avg_quality_gap, unique_improvements
        )

        return {
            "overall_manual_level_achieved": overall_manual_level_rate >= 0.8,
            "manual_level_achievement_rate": overall_manual_level_rate,
            "average_quality_gap": avg_quality_gap,
            "average_specificity_score": avg_specificity,
            "average_actionability_score": avg_actionability,
            "average_coverage_score": avg_coverage,
            "category_validations": [
                {
                    "category": v.category.value,
                    "manual_level_achieved": v.manual_analysis_level_achieved,
                    "quality_gap": v.quality_gap_score,
                    "improvement_areas": v.improvement_areas,
                }
                for v in category_validations
            ],
            "priority_improvements": unique_improvements[:5],
            "overall_assessment": overall_assessment,
            "recommended_actions": self._generate_recommended_actions(category_validations, overall_manual_level_rate),
        }

    def _evaluate_specificity(
        self, category_result: CategoryAnalysisResult, line_feedbacks: list[LineSpecificFeedback]
    ) -> float:
        """具体性評価"""
        specificity_factors = []

        # 問題特定の具体性
        for issue in category_result.issues_found:
            issue_specificity = self._calculate_issue_specificity(issue)
            specificity_factors.append(issue_specificity)

        # 改善提案の具体性
        for suggestion in category_result.suggestions:
            suggestion_specificity = self._calculate_suggestion_specificity(suggestion)
            specificity_factors.append(suggestion_specificity)

        # 行別フィードバックの具体性
        for feedback in line_feedbacks:
            line_specificity = self._calculate_line_feedback_specificity(feedback)
            specificity_factors.append(line_specificity)

        return mean(specificity_factors) if specificity_factors else 0.0

    def _evaluate_actionability(
        self, category_result: CategoryAnalysisResult, line_feedbacks: list[LineSpecificFeedback]
    ) -> float:
        """実行可能性評価"""
        actionability_factors = []

        # 改善提案の実行可能性
        for suggestion in category_result.suggestions:
            actionability = self._calculate_suggestion_actionability(suggestion)
            actionability_factors.append(actionability)

        # 行別フィードバックの実行可能性
        for feedback in line_feedbacks:
            actionability = self._calculate_feedback_actionability(feedback)
            actionability_factors.append(actionability)

        return mean(actionability_factors) if actionability_factors else 0.0

    def _evaluate_coverage(
        self,
        category_result: CategoryAnalysisResult,
        line_feedbacks: list[LineSpecificFeedback],
        episode_content: str,
        standard: ManualAnalysisStandard,
    ) -> float:
        """カバレッジ評価"""
        coverage_factors = []

        # 問題検出カバレッジ
        issues_coverage = len(category_result.issues_found) / max(1, standard.min_issues_identified)
        coverage_factors.append(min(100.0, issues_coverage * 100))

        # フィードバック種別カバレッジ
        detected_types = set()
        for feedback in line_feedbacks:
            detected_types.add(feedback.issue_type.value)

        expected_types = set(standard.expected_feedback_types)
        type_coverage = (
            len(detected_types.intersection(expected_types)) / len(expected_types) if expected_types else 1.0
        )
        coverage_factors.append(type_coverage * 100)

        # 内容網羅性
        content_coverage = self._calculate_content_coverage(line_feedbacks, episode_content)
        coverage_factors.append(content_coverage)

        return mean(coverage_factors)

    def _calculate_quality_gap(
        self,
        category_result: CategoryAnalysisResult,
        standard: ManualAnalysisStandard,
        specificity_score: float,
        actionability_score: float,
        coverage_score: float,
    ) -> float:
        """品質ギャップ計算"""
        # ベンチマークスコアとの差異
        score_gap = abs(category_result.score - standard.manual_benchmark_score)

        # 各品質要素の不足分
        specificity_gap = max(0, standard.min_specificity_score - specificity_score)
        actionability_gap = max(0, standard.min_actionability_score - actionability_score)
        coverage_gap = max(0, 80.0 - coverage_score)  # 80%を基準とする

        # 重み付き平均でギャップスコア計算
        total_gap = score_gap * 0.3 + specificity_gap * 0.25 + actionability_gap * 0.25 + coverage_gap * 0.2

        return min(100.0, total_gap)

    def _assess_manual_level_achievement(
        self,
        quality_gap: float,
        specificity_score: float,
        actionability_score: float,
        coverage_score: float,
        standard: ManualAnalysisStandard,
    ) -> bool:
        """手動分析レベル達成判定"""
        # 全ての基準を満たす必要がある
        criteria = [
            quality_gap < 20.0,  # 品質ギャップが20未満
            specificity_score >= standard.min_specificity_score,
            actionability_score >= standard.min_actionability_score,
            coverage_score >= 70.0,  # カバレッジ70%以上
        ]

        return all(criteria)

    def _calculate_issue_specificity(self, issue: str) -> float:
        """問題記述の具体性計算"""
        specificity_score = 50.0  # 基本スコア

        # 具体的な数値や例を含む
        if any(char.isdigit() for char in issue):
            specificity_score += 15.0

        # 具体的な位置や行番号の言及
        if any(word in issue for word in ["行", "箇所", "部分", "段落"]):
            specificity_score += 10.0

        # 具体的な改善方向の提示
        if any(word in issue for word in ["増やし", "減らし", "調整", "修正"]):
            specificity_score += 10.0

        # 曖昧な表現のペナルティ
        if any(word in issue for word in ["やや", "なんとなく", "もう少し"]):
            specificity_score -= 10.0

        return min(100.0, max(0.0, specificity_score))

    def _calculate_suggestion_specificity(self, suggestion: str) -> float:
        """改善提案の具体性計算"""
        specificity_score = 50.0

        # 具体例の提供
        if "例：" in suggestion or "（例" in suggestion:
            specificity_score += 20.0

        # 具体的な手法の提示
        if any(word in suggestion for word in ["追加", "削除", "変更", "修正", "調整"]):
            specificity_score += 15.0

        # 具体的な文字数や比率の言及
        if any(char.isdigit() for char in suggestion):
            specificity_score += 10.0

        return min(100.0, max(0.0, specificity_score))

    def _calculate_line_feedback_specificity(self, feedback: LineSpecificFeedback) -> float:
        """行別フィードバックの具体性計算"""
        specificity_score = 60.0  # 行番号指定により基本的に具体的

        # 具体的な修正例の提供
        if any(word in feedback.suggestion.content for word in ["例：", "→", "変更"]):
            specificity_score += 15.0

        # 問題の具体的説明
        if len(feedback.suggestion.content) > 30:  # 詳細な説明:
            specificity_score += 10.0

        # 信頼度による調整
        specificity_score *= feedback.confidence

        return min(100.0, max(0.0, specificity_score))

    def _calculate_suggestion_actionability(self, suggestion: str) -> float:
        """改善提案の実行可能性計算"""
        actionability_score = 50.0

        # 明確な動作指示
        action_words = ["追加", "削除", "変更", "修正", "調整", "分割", "統合"]
        if any(word in suggestion for word in action_words):
            actionability_score += 20.0

        # 具体的な場所の指定
        if any(word in suggestion for word in ["箇所", "行", "段落", "文"]):
            actionability_score += 15.0

        # 曖昧な指示のペナルティ
        if any(word in suggestion for word in ["適切に", "うまく", "よく"]):
            actionability_score -= 10.0

        return min(100.0, max(0.0, actionability_score))

    def _calculate_feedback_actionability(self, feedback: LineSpecificFeedback) -> float:
        """フィードバックの実行可能性計算"""
        actionability_score = 70.0  # 行指定により基本的に実行可能

        # 具体的な修正指示
        if any(word in feedback.suggestion.content for word in ["この", "その", "該当"]):
            actionability_score += 10.0

        # 修正例の提供
        if "例：" in feedback.suggestion.content:
            actionability_score += 15.0

        return min(100.0, max(0.0, actionability_score))

    def _calculate_content_coverage(self, line_feedbacks: list[LineSpecificFeedback], episode_content: str) -> float:
        """内容網羅性計算"""
        if not line_feedbacks:
            return 0.0

        content_lines = len([line for line in episode_content.split("\n") if line.strip()])
        if content_lines == 0:
            return 0.0

        # フィードバック対象行の分散度
        feedback_lines = {feedback.line_number for feedback in line_feedbacks}
        coverage_ratio = len(feedback_lines) / content_lines

        # 分散の均一性
        if len(feedback_lines) > 1:
            line_numbers = sorted(feedback_lines)
            gaps = [line_numbers[i + 1] - line_numbers[i] for i in range(len(line_numbers) - 1)]
            avg_gap = sum(gaps) / len(gaps)
            ideal_gap = content_lines / len(feedback_lines)

            # ギャップの均一性ボーナス
            gap_uniformity = max(0, 1 - abs(avg_gap - ideal_gap) / ideal_gap)
            coverage_ratio += gap_uniformity * 0.2

        return min(100.0, coverage_ratio * 100)

    def _identify_improvement_areas(
        self,
        category_result: CategoryAnalysisResult,
        line_feedbacks: list[LineSpecificFeedback],
        standard: ManualAnalysisStandard,
        specificity_score: float,
        actionability_score: float,
        coverage_score: float,
    ) -> list[str]:
        """改善領域特定"""
        improvements = []

        if specificity_score < standard.min_specificity_score:
            improvements.append("具体性向上 - より詳細で明確な問題指摘が必要")

        if actionability_score < standard.min_actionability_score:
            improvements.append("実行可能性向上 - 具体的な修正手順の提示が必要")

        if coverage_score < 70.0:
            improvements.append("カバレッジ拡大 - より多くの問題箇所の検出が必要")

        if len(category_result.issues_found) < standard.min_issues_identified:
            improvements.append("問題検出力向上 - 見落としがちな問題の検出強化が必要")

        if len(line_feedbacks) < 3:
            improvements.append("行別分析強化 - より詳細な行レベルフィードバックが必要")

        return improvements

    def _generate_detailed_feedback(
        self,
        category: A31EvaluationCategory,
        quality_gap: float,
        improvement_areas: list[str],
        manual_level_achieved: bool,
    ) -> str:
        """詳細フィードバック生成"""
        feedback_parts = []

        category_name = category.get_display_name()

        if manual_level_achieved:
            feedback_parts.append(f"{category_name}の分析は手動Claude Code分析レベルに到達しています。")
        else:
            feedback_parts.append(f"{category_name}の分析品質にはまだ改善の余地があります。")
            feedback_parts.append(f"手動分析との品質ギャップ: {quality_gap:.1f}点")

        if improvement_areas:
            feedback_parts.append("主な改善領域:")
            for i, area in enumerate(improvement_areas, 1):
                feedback_parts.append(f"{i}. {area}")

        return "\n".join(feedback_parts)

    def _generate_overall_assessment(
        self, manual_level_rate: float, avg_quality_gap: float, improvements: list[str]
    ) -> str:
        """全体評価生成"""
        if manual_level_rate >= 0.9:
            return "優秀 - 手動分析レベルにほぼ到達しています"
        if manual_level_rate >= 0.7:
            return "良好 - 手動分析レベルに近づいています"
        if manual_level_rate >= 0.5:
            return "改善中 - 基本的な分析は機能していますが向上が必要です"
        return "要改善 - 大幅な品質向上が必要です"

    def _generate_recommended_actions(
        self, validations: list[QualityValidationResult], overall_rate: float
    ) -> list[str]:
        """推奨アクション生成"""
        actions = []

        if overall_rate < 0.5:
            actions.append("基本分析アルゴリズムの見直しが必要です")
            actions.append("問題検出パターンの拡充を実施してください")

        if overall_rate < 0.8:
            actions.append("改善提案の具体性を向上させてください")
            actions.append("行別フィードバックの充実を図ってください")

        # カテゴリ別の改善提案
        low_quality_categories = [v for v in validations if not v.manual_analysis_level_achieved]
        if low_quality_categories:
            category_names = [v.category.get_display_name() for v in low_quality_categories]
            actions.append(f"優先改善カテゴリ: {', '.join(category_names)}")

        return actions

    def _is_feedback_for_category(self, feedback: LineSpecificFeedback, category: A31EvaluationCategory) -> bool:
        """フィードバックがカテゴリに属するか判定"""
        # 簡易的な判定ロジック（実際の実装では詳細な分類が必要）
        category_issue_mapping = {
            A31EvaluationCategory.STYLE_CONSISTENCY: ["style_monotony", "rhythm_variation"],
            A31EvaluationCategory.CONTENT_BALANCE: ["content_balance", "sensory_lack"],
            A31EvaluationCategory.FORMAT_CHECK: ["structure_complexity", "breathing_points"],
            A31EvaluationCategory.READABILITY_CHECK: ["punctuation_overuse", "readability"],
        }

        expected_issues = category_issue_mapping.get(category, [])
        return feedback.issue_type.value in expected_issues

    def _calculate_validation_confidence(
        self, category_result: CategoryAnalysisResult, line_feedbacks: list[LineSpecificFeedback], episode_content: str
    ) -> float:
        """検証信頼度計算"""
        confidence_factors = []

        # 分析結果の信頼度
        confidence_factors.append(category_result.calculate_confidence_score())

        # フィードバック数による信頼度
        feedback_count_factor = min(1.0, len(line_feedbacks) / 5)  # 5個以上で満点
        confidence_factors.append(feedback_count_factor)

        # コンテンツ量による信頼度
        content_length = len(episode_content)
        if content_length > 1000:
            confidence_factors.append(0.9)
        elif content_length > 500:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.7)

        return mean(confidence_factors)

    def _create_default_validation_result(self, category: A31EvaluationCategory) -> QualityValidationResult:
        """デフォルト検証結果作成"""
        return QualityValidationResult(
            category=category,
            manual_analysis_level_achieved=False,
            quality_gap_score=100.0,
            specificity_score=0.0,
            actionability_score=0.0,
            coverage_score=0.0,
            improvement_areas=["品質基準が未定義です"],
            detailed_feedback="このカテゴリの品質基準が定義されていません",
            confidence_level=0.0,
        )

    def _initialize_manual_standards(self) -> dict[A31EvaluationCategory, ManualAnalysisStandard]:
        """手動分析基準初期化"""
        return {
            A31EvaluationCategory.STYLE_CONSISTENCY: ManualAnalysisStandard(
                category=A31EvaluationCategory.STYLE_CONSISTENCY,
                min_issues_identified=3,
                min_suggestions_quality=75.0,
                min_specificity_score=70.0,
                min_actionability_score=75.0,
                expected_feedback_types=["style_monotony", "rhythm_variation"],
                manual_benchmark_score=86.0,  # 手動分析での期待スコア
            ),
            A31EvaluationCategory.CONTENT_BALANCE: ManualAnalysisStandard(
                category=A31EvaluationCategory.CONTENT_BALANCE,
                min_issues_identified=4,
                min_suggestions_quality=80.0,
                min_specificity_score=75.0,
                min_actionability_score=80.0,
                expected_feedback_types=["content_balance", "sensory_lack"],
                manual_benchmark_score=82.0,
            ),
            A31EvaluationCategory.FORMAT_CHECK: ManualAnalysisStandard(
                category=A31EvaluationCategory.FORMAT_CHECK,
                min_issues_identified=2,
                min_suggestions_quality=70.0,
                min_specificity_score=75.0,
                min_actionability_score=85.0,
                expected_feedback_types=["structure_complexity", "breathing_points"],
                manual_benchmark_score=84.0,
            ),
            A31EvaluationCategory.READABILITY_CHECK: ManualAnalysisStandard(
                category=A31EvaluationCategory.READABILITY_CHECK,
                min_issues_identified=3,
                min_suggestions_quality=70.0,
                min_specificity_score=70.0,
                min_actionability_score=80.0,
                expected_feedback_types=["punctuation_overuse", "readability"],
                manual_benchmark_score=79.0,
            ),
        }

    def _initialize_quality_metrics(self) -> dict[str, Any]:
        """品質メトリクス初期化"""
        return {
            "specificity_weights": {
                "concrete_examples": 0.3,
                "numerical_references": 0.2,
                "location_specificity": 0.25,
                "clear_description": 0.25,
            },
            "actionability_weights": {"clear_actions": 0.4, "specific_targets": 0.3, "practical_examples": 0.3},
        }
