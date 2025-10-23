"""Domain.services.writing_steps.review_integration_service
Where: Domain service module implementing a specific writing workflow step.
What: Provides helper routines and data structures for this writing step.
Why: Allows stepwise writing orchestrators to reuse consistent step logic.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""STEP 12: ReviewIntegrationService

A38執筆プロンプトガイドのSTEP 12に対応するマイクロサービス。
レビュー統合・最終確認・完成度チェックを担当。
"""

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from noveler.domain.interfaces.logger_service_protocol import ILoggerService

from noveler.domain.services.writing_steps.base_writing_step import BaseWritingStep, WritingStepResponse


@dataclass
class ReviewCriteria:
    """レビュー基準"""

    criteria_type: str  # "structural", "content", "technical", "artistic"
    criteria_name: str
    importance_weight: float = 1.0

    # 評価基準
    evaluation_points: list[str] = field(default_factory=list)
    pass_threshold: float = 7.0
    excellence_threshold: float = 8.5

    # チェック方法
    check_method: str = "manual"  # "manual", "automated", "hybrid"
    check_instructions: list[str] = field(default_factory=list)


@dataclass
class ComponentReview:
    """コンポーネントレビュー"""

    component_name: str  # "plot_analysis", "scene_design", "dialogue_design" etc.
    step_number: int

    # レビュー結果
    review_score: float = 0.0
    passed_criteria: list[str] = field(default_factory=list)
    failed_criteria: list[str] = field(default_factory=list)

    # 詳細評価
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    # 統合性チェック
    integration_score: float = 0.0
    dependency_issues: list[str] = field(default_factory=list)


@dataclass
class IntegrationAssessment:
    """統合評価"""

    # 全体統合度
    overall_integration_score: float = 0.0
    component_harmony: float = 0.0
    consistency_level: float = 0.0

    # コンポーネント間連携
    step_dependencies: dict[int, list[int]] = field(default_factory=dict)
    integration_gaps: list[str] = field(default_factory=list)
    synergy_opportunities: list[str] = field(default_factory=list)

    # 完成度評価
    completeness_score: float = 0.0
    readiness_for_writing: bool = False


@dataclass
class ReviewIntegrationResult:
    """レビュー統合結果"""

    episode_number: int
    review_confidence: float = 0.0

    # 個別コンポーネントレビュー
    component_reviews: list[ComponentReview] = field(default_factory=list)

    # 統合評価
    integration_assessment: IntegrationAssessment | None = None

    # 最終判定
    overall_quality_score: float = 0.0
    approval_status: str = "pending"  # "approved", "needs_revision", "rejected"

    # ガイダンス
    final_recommendations: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)
    quality_assurance_notes: list[str] = field(default_factory=list)


@dataclass
class ReviewIntegrationResponse(WritingStepResponse):
    """レビュー統合サービス結果"""

    review_result: ReviewIntegrationResult | None = None

    # パフォーマンス情報
    component_review_time_ms: float = 0.0
    integration_analysis_time_ms: float = 0.0
    final_assessment_time_ms: float = 0.0

    # 統計情報
    components_reviewed: int = 0
    criteria_evaluated: int = 0
    issues_identified: int = 0


class ReviewIntegrationService(BaseWritingStep):
    """STEP 12: レビュー統合マイクロサービス

    全ステップの結果を統合的にレビューし、
    最終的な執筆準備完了判定を行う。
    """

    def __init__(
        self,
        logger_service: ILoggerService = None,
        **kwargs: Any
    ) -> None:
        """レビュー統合サービス初期化"""
        super().__init__(step_number=12, step_name="review_integration", **kwargs)

        self._logger_service = logger_service

    async def execute(
        self,
        episode_number: int,
        previous_results: dict[int, Any] | None = None
    ) -> ReviewIntegrationResponse:
        """レビュー統合実行"""
        start_time = time.time()

        try:
            if self._logger_service:
                self._logger_service.info(f"STEP 12 レビュー統合開始: エピソード={episode_number}")

            # 1. レビュー基準設定
            review_criteria = self._establish_review_criteria()

            # 2. 個別コンポーネントレビュー
            component_start = time.time()
            component_reviews = await self._review_individual_components(
                previous_results, review_criteria
            )
            component_time = (time.time() - component_start) * 1000

            # 3. 統合性分析
            integration_start = time.time()
            integration_assessment = await self._assess_integration(
                component_reviews, previous_results
            )
            integration_time = (time.time() - integration_start) * 1000

            # 4. 最終評価・判定
            assessment_start = time.time()
            review_result = await self._conduct_final_assessment(
                episode_number, component_reviews, integration_assessment
            )
            assessment_time = (time.time() - assessment_start) * 1000

            # 5. 成功応答作成
            execution_time = (time.time() - start_time) * 1000

            return ReviewIntegrationResponse(
                success=True,
                step_number=12,
                step_name="review_integration",
                execution_time_ms=execution_time,
                review_result=review_result,

                # パフォーマンス情報
                component_review_time_ms=component_time,
                integration_analysis_time_ms=integration_time,
                final_assessment_time_ms=assessment_time,

                # 統計情報
                components_reviewed=len(component_reviews),
                criteria_evaluated=len(review_criteria),
                issues_identified=sum(len(review.failed_criteria)
                                    for review in component_reviews)
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_message = f"STEP 12 レビュー統合エラー: {e}"

            if self._logger_service:
                self._logger_service.error(error_message)

            return ReviewIntegrationResponse(
                success=False,
                step_number=12,
                step_name="review_integration",
                execution_time_ms=execution_time,
                error_message=error_message
            )

    def _establish_review_criteria(self) -> list[ReviewCriteria]:
        """レビュー基準設定"""
        return [
            # 構造的基準
            ReviewCriteria(
                criteria_type="structural",
                criteria_name="プロット整合性",
                importance_weight=1.5,
                evaluation_points=[
                    "プロット要素の論理的一貫性",
                    "因果関係の明確性",
                    "構成の適切性"
                ],
                pass_threshold=7.0,
                check_method="hybrid",
                check_instructions=["プロット解析結果の妥当性確認", "構造設計との整合性チェック"]
            ),

            ReviewCriteria(
                criteria_type="structural",
                criteria_name="シーン構成",
                importance_weight=1.3,
                evaluation_points=[
                    "シーン配置の論理性",
                    "遷移の自然性",
                    "文字数配分の適切性"
                ],
                pass_threshold=7.5,
                check_method="manual"
            ),

            # コンテンツ基準
            ReviewCriteria(
                criteria_type="content",
                criteria_name="キャラクター表現",
                importance_weight=1.4,
                evaluation_points=[
                    "キャラクター音声の差別化",
                    "個性の一貫性",
                    "関係性の適切性"
                ],
                pass_threshold=7.0,
                check_method="manual"
            ),

            ReviewCriteria(
                criteria_type="content",
                criteria_name="対話品質",
                importance_weight=1.2,
                evaluation_points=[
                    "対話の自然性",
                    "目的の明確性",
                    "キャラクター性の反映"
                ],
                pass_threshold=7.5
            ),

            # 技術的基準
            ReviewCriteria(
                criteria_type="technical",
                criteria_name="視点一貫性",
                importance_weight=1.1,
                evaluation_points=[
                    "視点設定の維持",
                    "情報制限の遵守",
                    "切り替えの明確性"
                ],
                pass_threshold=8.0,
                check_method="automated"
            ),

            ReviewCriteria(
                criteria_type="technical",
                criteria_name="時系列整合性",
                importance_weight=1.0,
                evaluation_points=[
                    "時間経過の論理性",
                    "前後関係の明確性",
                    "継続性の維持"
                ],
                pass_threshold=7.5
            ),

            # 芸術的基準
            ReviewCriteria(
                criteria_type="artistic",
                criteria_name="エンゲージメント",
                importance_weight=1.3,
                evaluation_points=[
                    "読者の関心維持",
                    "緊張と緩和のバランス",
                    "感情的な訴求力"
                ],
                pass_threshold=7.0,
                excellence_threshold=9.0
            )
        ]


    async def _review_individual_components(
        self,
        previous_results: dict[int, Any] | None,
        review_criteria: list[ReviewCriteria]
    ) -> list[ComponentReview]:
        """個別コンポーネントレビュー"""
        component_reviews = []

        if not previous_results:
            return component_reviews

        # 各ステップの結果をレビュー
        component_mappings = {
            0: ("scope_definition", "スコープ定義"),
            1: ("plot_analysis", "プロット解析"),
            2: ("context_extraction", "コンテキスト抽出"),
            3: ("narrative_structure", "叙述構造"),
            4: ("scene_design", "シーン設計"),
            5: ("dialogue_design", "対話設計"),
            10: ("manuscript_generation", "原稿生成"),
            11: ("content_optimization", "コンテンツ最適化"),
            13: ("quality_gate", "品質ゲート")
        }

        for step_num, step_result in previous_results.items():
            if step_num in component_mappings:
                component_id, component_name = component_mappings[step_num]

                review = await self._review_single_component(
                    component_id, component_name, step_num,
                    step_result, review_criteria
                )

                if review:
                    component_reviews.append(review)

        return component_reviews

    async def _review_single_component(
        self,
        component_id: str,
        component_name: str,
        step_number: int,
        step_result: Any,
        review_criteria: list[ReviewCriteria]
    ) -> ComponentReview | None:
        """単一コンポーネントレビュー"""
        if not step_result or not hasattr(step_result, "success") or not step_result.success:
            return ComponentReview(
                component_name=component_id,
                step_number=step_number,
                review_score=0.0,
                failed_criteria=["基本実行失敗"],
                weaknesses=["ステップ実行が失敗"],
                recommendations=["ステップの再実行が必要"]
            )

        # 基本品質評価
        base_score = self._evaluate_component_quality(component_id, step_result)

        # 適用可能な基準での評価
        applicable_criteria = self._get_applicable_criteria(component_id, review_criteria)

        passed_criteria = []
        failed_criteria = []
        strengths = []
        weaknesses = []
        recommendations = []

        for criteria in applicable_criteria:
            score = self._evaluate_against_criteria(step_result, criteria)

            if score >= criteria.pass_threshold:
                passed_criteria.append(criteria.criteria_name)

                if score >= criteria.excellence_threshold:
                    strengths.append(f"{criteria.criteria_name}: 優秀")
            else:
                failed_criteria.append(criteria.criteria_name)
                weaknesses.append(f"{criteria.criteria_name}: 改善必要")
                recommendations.extend(criteria.check_instructions)

        # 統合性評価
        integration_score = self._evaluate_component_integration(step_result)

        return ComponentReview(
            component_name=component_id,
            step_number=step_number,
            review_score=base_score,
            passed_criteria=passed_criteria,
            failed_criteria=failed_criteria,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            integration_score=integration_score
        )

    def _evaluate_component_quality(self, component_id: str, step_result: Any) -> float:
        """コンポーネント品質評価"""
        base_score = 5.0

        # 実行時間による評価（効率性）
        if hasattr(step_result, "execution_time_ms"):
            exec_time = step_result.execution_time_ms
            if exec_time < 1000:  # 1秒未満
                base_score += 1.0
            elif exec_time > 5000:  # 5秒超
                base_score -= 0.5

        # 結果の充実度
        if hasattr(step_result, "analysis_result"):
            result = step_result.analysis_result
            if result and hasattr(result, "analysis_confidence"):
                base_score += result.analysis_confidence * 3.0
        elif hasattr(step_result, "design_plan"):
            plan = step_result.design_plan
            if plan and hasattr(plan, "scene_count") and plan.scene_count > 0:
                base_score += 2.0
        elif hasattr(step_result, "dialogue_result"):
            dialogue = step_result.dialogue_result
            if dialogue and hasattr(dialogue, "character_voices") and dialogue.character_voices:
                base_score += 2.0

        return min(10.0, base_score)

    def _get_applicable_criteria(
        self,
        component_id: str,
        all_criteria: list[ReviewCriteria]
    ) -> list[ReviewCriteria]:
        """適用可能基準取得"""
        # コンポーネント別適用基準マッピング
        criteria_mapping = {
            "plot_analysis": ["プロット整合性"],
            "scene_design": ["シーン構成", "時系列整合性"],
            "dialogue_design": ["キャラクター表現", "対話品質"],
            "narrative_structure": ["視点一貫性", "時系列整合性"],
            "manuscript_generation": ["エンゲージメント"],
            "quality_gate": ["全基準"]
        }

        applicable_names = criteria_mapping.get(component_id, [])

        if "全基準" in applicable_names:
            return all_criteria

        return [criteria for criteria in all_criteria
                if criteria.criteria_name in applicable_names]

    def _evaluate_against_criteria(
        self,
        step_result: Any,
        criteria: ReviewCriteria
    ) -> float:
        """基準に対する評価"""
        # 基本スコア
        score = 6.0

        # 基準別評価ロジック
        if criteria.criteria_name == "プロット整合性":
            if hasattr(step_result, "analysis_result"):
                result = step_result.analysis_result
                if result and hasattr(result, "plot_exists") and result.plot_exists:
                    score += 2.0
                if result and hasattr(result, "analysis_confidence"):
                    score += result.analysis_confidence * 2.0

        elif criteria.criteria_name == "シーン構成":
            if hasattr(step_result, "design_plan"):
                plan = step_result.design_plan
                if plan and hasattr(plan, "scene_blocks"):
                    scene_count = len(plan.scene_blocks)
                    if 3 <= scene_count <= 7:
                        score += 2.0
                    elif scene_count > 0:
                        score += 1.0

        elif criteria.criteria_name == "対話品質":
            if hasattr(step_result, "dialogue_result"):
                dialogue = step_result.dialogue_result
                if dialogue and hasattr(dialogue, "character_voices"):
                    voice_count = len(dialogue.character_voices)
                    if voice_count >= 2:
                        score += 2.0

        return min(10.0, score)

    def _evaluate_component_integration(self, step_result: Any) -> float:
        """コンポーネント統合性評価"""
        integration_score = 7.0

        # 前ステップ依存度チェック（推定）
        if hasattr(step_result, "success") and step_result.success:
            integration_score += 1.5

        # エラーメッセージによる統合性判定
        if hasattr(step_result, "error_message") and step_result.error_message:
            if "前ステップ" in step_result.error_message or "依存" in step_result.error_message:
                integration_score -= 2.0

        return max(0.0, min(10.0, integration_score))

    async def _assess_integration(
        self,
        component_reviews: list[ComponentReview],
        previous_results: dict[int, Any] | None
    ) -> IntegrationAssessment:
        """統合性評価"""
        # 全体統合度計算
        if component_reviews:
            avg_integration = sum(review.integration_score
                                for review in component_reviews) / len(component_reviews)
        else:
            avg_integration = 0.0

        # コンポーネント間調和度
        successful_components = sum(1 for review in component_reviews
                                  if review.review_score >= 7.0)
        total_components = len(component_reviews)

        harmony = successful_components / total_components if total_components > 0 else 0.0

        # 一貫性レベル
        consistency = self._evaluate_cross_component_consistency(previous_results)

        # 依存関係分析
        dependencies = self._analyze_step_dependencies(previous_results)

        # 統合ギャップ特定
        integration_gaps = []
        for review in component_reviews:
            if review.integration_score < 7.0:
                integration_gaps.append(f"{review.component_name}: 統合性不足")

        # 相乗効果機会
        synergy_opportunities = self._identify_synergy_opportunities(component_reviews)

        # 完成度評価
        completeness = self._evaluate_completeness(component_reviews)
        readiness = completeness >= 0.8 and avg_integration >= 7.0

        return IntegrationAssessment(
            overall_integration_score=avg_integration,
            component_harmony=harmony,
            consistency_level=consistency,
            step_dependencies=dependencies,
            integration_gaps=integration_gaps,
            synergy_opportunities=synergy_opportunities,
            completeness_score=completeness,
            readiness_for_writing=readiness
        )

    def _evaluate_cross_component_consistency(
        self,
        previous_results: dict[int, Any] | None
    ) -> float:
        """クロスコンポーネント一貫性評価"""
        consistency_score = 7.0

        # キャラクター一貫性チェック
        character_names = set()

        # コンテキスト抽出結果からキャラクター取得
        if previous_results and 2 in previous_results:
            step2 = previous_results[2]
            if (hasattr(step2, "context_result") and
                step2.context_result and
                hasattr(step2.context_result, "character_contexts")):
                for char_ctx in step2.context_result.character_contexts:
                    character_names.add(char_ctx.character_name)

        # 対話設計結果と比較
        if previous_results and 5 in previous_results:
            step5 = previous_results[5]
            if (hasattr(step5, "dialogue_result") and
                step5.dialogue_result and
                hasattr(step5.dialogue_result, "character_voices")):
                dialogue_characters = {voice.character_name
                                        for voice in step5.dialogue_result.character_voices}

                # キャラクター一致度
                if character_names and dialogue_characters:
                    intersection = character_names.intersection(dialogue_characters)
                    union = character_names.union(dialogue_characters)
                    consistency_score += 2.0 * (len(intersection) / len(union))

        return min(10.0, consistency_score)

    def _analyze_step_dependencies(
        self,
        previous_results: dict[int, Any] | None
    ) -> dict[int, list[int]]:
        """ステップ依存関係分析"""
        # 設計上の依存関係定義
        return {
            1: [0],      # プロット解析 → スコープ定義
            2: [0, 1],   # コンテキスト抽出 → スコープ・プロット
            3: [1, 2],   # 叙述構造 → プロット・コンテキスト
            4: [2, 3],   # シーン設計 → コンテキスト・構造
            5: [2, 4],   # 対話設計 → コンテキスト・シーン
            10: [0, 1, 2, 3, 4, 5],  # 原稿生成 → 全前段階
            11: [10],    # 最適化 → 原稿生成
            12: [0, 1, 2, 3, 4, 5, 10, 11],  # レビュー → 全体
            13: [10, 11] # 品質ゲート → 原稿・最適化
        }


    def _identify_synergy_opportunities(
        self,
        component_reviews: list[ComponentReview]
    ) -> list[str]:
        """相乗効果機会特定"""
        opportunities = []

        # 高品質コンポーネント特定
        excellent_components = [review for review in component_reviews
                              if review.review_score >= 8.0]

        if len(excellent_components) >= 2:
            opportunities.append("複数の高品質コンポーネントの相乗効果活用可能")

        # 特定コンビネーション
        component_names = [review.component_name for review in excellent_components]

        if "scene_design" in component_names and "dialogue_design" in component_names:
            opportunities.append("シーン設計と対話設計の統合強化")

        if "plot_analysis" in component_names and "narrative_structure" in component_names:
            opportunities.append("プロット解析と叙述構造の深い統合")

        return opportunities

    def _evaluate_completeness(self, component_reviews: list[ComponentReview]) -> float:
        """完成度評価"""
        # 必須コンポーネント
        essential_components = {
            "scope_definition", "plot_analysis", "context_extraction",
            "scene_design", "manuscript_generation"
        }

        reviewed_components = {review.component_name for review in component_reviews}

        # 必須コンポーネントの完成度
        essential_completion = len(essential_components.intersection(reviewed_components)) / len(essential_components)

        # 成功コンポーネントの割合
        successful_reviews = sum(1 for review in component_reviews
                               if review.review_score >= 6.0)
        success_rate = successful_reviews / len(component_reviews) if component_reviews else 0.0

        return (essential_completion * 0.6) + (success_rate * 0.4)

    async def _conduct_final_assessment(
        self,
        episode_number: int,
        component_reviews: list[ComponentReview],
        integration_assessment: IntegrationAssessment
    ) -> ReviewIntegrationResult:
        """最終評価実施"""
        # 総合品質スコア計算
        if component_reviews:
            weighted_scores = []
            for review in component_reviews:
                # 重要度による重み付け
                weight = self._get_component_weight(review.component_name)
                weighted_scores.append(review.review_score * weight)

            overall_score = sum(weighted_scores) / len(weighted_scores)
        else:
            overall_score = 0.0

        # 承認ステータス決定
        approval_status = self._determine_approval_status(
            overall_score, integration_assessment, component_reviews
        )

        # 最終推奨事項
        final_recommendations = self._generate_final_recommendations(
            component_reviews, integration_assessment
        )

        # 次のステップ
        next_steps = self._determine_next_steps(approval_status, component_reviews)

        # 品質保証ノート
        qa_notes = self._generate_qa_notes(overall_score, integration_assessment)

        # 信頼度計算
        confidence = self._calculate_review_confidence(
            component_reviews, integration_assessment
        )

        return ReviewIntegrationResult(
            episode_number=episode_number,
            review_confidence=confidence,
            component_reviews=component_reviews,
            integration_assessment=integration_assessment,
            overall_quality_score=overall_score,
            approval_status=approval_status,
            final_recommendations=final_recommendations,
            next_steps=next_steps,
            quality_assurance_notes=qa_notes
        )

    def _get_component_weight(self, component_name: str) -> float:
        """コンポーネント重要度重み"""
        weights = {
            "scope_definition": 0.8,
            "plot_analysis": 1.2,
            "context_extraction": 1.0,
            "narrative_structure": 1.1,
            "scene_design": 1.3,
            "dialogue_design": 1.2,
            "manuscript_generation": 1.5,
            "content_optimization": 1.1,
            "quality_gate": 1.0
        }

        return weights.get(component_name, 1.0)

    def _determine_approval_status(
        self,
        overall_score: float,
        integration_assessment: IntegrationAssessment,
        component_reviews: list[ComponentReview]
    ) -> str:
        """承認ステータス決定"""
        # 重要な失敗がある場合
        critical_failures = sum(1 for review in component_reviews
                               if review.component_name in ["manuscript_generation", "plot_analysis"]
                               and review.review_score < 5.0)

        if critical_failures > 0:
            return "rejected"

        # 統合準備状況
        if not integration_assessment.readiness_for_writing:
            return "needs_revision"

        # 総合スコア基準
        if overall_score >= 8.0:
            return "approved"
        if overall_score >= 6.5:
            return "needs_revision"
        return "rejected"

    def _generate_final_recommendations(
        self,
        component_reviews: list[ComponentReview],
        integration_assessment: IntegrationAssessment
    ) -> list[str]:
        """最終推奨事項生成"""
        recommendations = []

        # 低品質コンポーネントの改善
        weak_components = [review for review in component_reviews
                          if review.review_score < 7.0]

        for weak in weak_components:
            recommendations.append(
                f"{weak.component_name}の品質向上: {', '.join(weak.recommendations[:2])}"
            )

        # 統合性改善
        if integration_assessment.integration_gaps:
            recommendations.append("統合性改善: " + ", ".join(integration_assessment.integration_gaps[:2]))

        # 相乗効果活用
        if integration_assessment.synergy_opportunities:
            recommendations.extend(integration_assessment.synergy_opportunities[:2])

        return recommendations

    def _determine_next_steps(
        self,
        approval_status: str,
        component_reviews: list[ComponentReview]
    ) -> list[str]:
        """次ステップ決定"""
        if approval_status == "approved":
            return [
                "STEP 13: 品質ゲートによる最終チェック",
                "STEP 14-15: 執筆実行・完成",
                "全体品質モニタリング継続"
            ]
        if approval_status == "needs_revision":
            steps = ["指摘項目の修正・改善"]

            # 具体的な修正ステップ
            for review in component_reviews:
                if review.review_score < 7.0:
                    steps.append(f"STEP {review.step_number}: {review.component_name}の再実行")

            steps.append("修正後の再レビュー実施")
            return steps
        # rejected
        return [
            "基本設計の見直し",
            "重要コンポーネントの再設計",
            "全体アプローチの再検討"
        ]

    def _generate_qa_notes(
        self,
        overall_score: float,
        integration_assessment: IntegrationAssessment
    ) -> list[str]:
        """品質保証ノート生成"""
        notes = []

        notes.append(f"総合品質スコア: {overall_score:.1f}/10.0")
        notes.append(f"統合度: {integration_assessment.overall_integration_score:.1f}/10.0")
        notes.append(f"完成度: {integration_assessment.completeness_score:.1%}")

        if integration_assessment.readiness_for_writing:
            notes.append("✅ 執筆準備完了")
        else:
            notes.append("⚠️ 追加準備必要")

        return notes

    def _calculate_review_confidence(
        self,
        component_reviews: list[ComponentReview],
        integration_assessment: IntegrationAssessment
    ) -> float:
        """レビュー信頼度計算"""
        base_confidence = 0.7

        # レビュー対象数による調整
        if len(component_reviews) >= 5:
            base_confidence += 0.2
        elif len(component_reviews) < 3:
            base_confidence -= 0.1

        # 統合性による調整
        if integration_assessment.overall_integration_score >= 8.0:
            base_confidence += 0.1
        elif integration_assessment.overall_integration_score < 6.0:
            base_confidence -= 0.2

        return max(0.0, min(1.0, base_confidence))
