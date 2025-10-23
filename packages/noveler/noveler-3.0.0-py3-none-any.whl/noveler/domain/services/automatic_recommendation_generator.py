#!/usr/bin/env python3
"""自動提案生成サービス - NIH症候群防止システム Phase2 P2

SPEC: SPEC-NIH-PREVENTION-CODEMAP-001 Phase2
責務: 機械学習分析結果に基づく自動的な再利用・拡張・統合提案の生成
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

# DDD準拠: Infrastructure層への直接依存を排除し、DIでInterface注入
from noveler.domain.services.machine_learning_based_similarity_service import (
    MachineLearningBasedSimilarityService,
    MLSimilarityResult,
)
from noveler.domain.value_objects.function_signature import FunctionSignature
from noveler.domain.value_objects.project_time import project_now

if TYPE_CHECKING:
    from noveler.domain.interfaces.logger_interface import ILogger
else:
    # 実行時はNullLoggerを利用してインフラ依存を避ける
    from noveler.domain.interfaces.logger_interface import NullLogger


class RecommendationCategory(Enum):
    """提案カテゴリ"""

    DIRECT_REUSE = "direct_reuse"
    EXTEND_EXISTING = "extend_existing"
    MERGE_FUNCTIONS = "merge_functions"
    EXTRACT_COMMON = "extract_common"
    REFACTOR_PATTERN = "refactor_pattern"
    ARCHITECTURAL_IMPROVEMENT = "architectural_improvement"


class RecommendationPriority(Enum):
    """提案優先度"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class RecommendationAction:
    """推奨アクション"""

    action_type: str  # "reuse", "extend", "merge", "extract"
    target_functions: list[FunctionSignature]
    description: str
    implementation_steps: list[str]
    expected_benefits: list[str]
    estimated_effort_hours: float
    risk_level: str  # "low", "medium", "high"


@dataclass
class AutomationRecommendation:
    """自動提案"""

    recommendation_id: str
    category: RecommendationCategory
    priority: RecommendationPriority
    title: str
    description: str
    confidence_score: float  # 0.0-1.0

    # 関連機能情報
    target_function: FunctionSignature
    similar_functions: list[tuple[FunctionSignature, float]]
    ml_analysis_results: list[MLSimilarityResult]

    # アクション提案
    recommended_actions: list[RecommendationAction]
    alternative_approaches: list[str]

    # メタデータ
    generated_timestamp: datetime
    reasoning: str
    implementation_complexity: str  # "simple", "medium", "complex"

    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """高信頼度提案判定"""
        return self.confidence_score >= threshold

    def get_effort_estimate(self) -> float:
        """総工数見積り計算"""
        return sum(action.estimated_effort_hours for action in self.recommended_actions)

    def get_primary_action(self) -> RecommendationAction | None:
        """主要アクション取得"""
        if not self.recommended_actions:
            return None

        # 最も工数が少ないアクションを主要とする
        return min(self.recommended_actions, key=lambda x: x.estimated_effort_hours)


class AutomaticRecommendationGenerator:
    """自動提案生成サービス"""

    def __init__(
        self,
        ml_similarity_service: MachineLearningBasedSimilarityService,
        project_root: Path,
        logger: "ILogger | None" = None,
        enable_advanced_analysis: bool = True,
    ) -> None:
        """初期化

        Args:
            ml_similarity_service: 機械学習ベース類似度サービス
            project_root: プロジェクトルートパス
            logger: ロガーインターフェース（DI注入）
            enable_advanced_analysis: 高度分析を有効化
        """
        self.ml_similarity_service = ml_similarity_service
        # ロガー未指定時はNullLoggerを利用
        self._logger = logger if logger is not None else NullLogger()
        self.project_root = project_root
        self.enable_advanced_analysis = enable_advanced_analysis

        # 提案生成設定
        self.recommendation_thresholds = {
            "direct_reuse_similarity": 0.85,
            "extend_similarity": 0.65,
            "merge_similarity": 0.75,
            "extract_common_similarity": 0.6,
            "min_confidence_score": 0.5,
        }

        # パターン認識設定
        self.pattern_keywords = {
            "data_processing": ["process", "handle", "transform", "convert"],
            "validation": ["validate", "verify", "check", "ensure"],
            "calculation": ["calculate", "compute", "sum", "count"],
            "authentication": ["auth", "login", "verify", "credential"],
            "persistence": ["save", "store", "persist", "write"],
            "retrieval": ["get", "fetch", "load", "read", "find"],
        }

        self._logger.info("AutomaticRecommendationGenerator初期化完了 (advanced: %s)", enable_advanced_analysis=enable_advanced_analysis)

    def generate_comprehensive_recommendations(
        self,
        target_function: FunctionSignature,
        candidate_functions: list[FunctionSignature],
        max_recommendations: int = 5,
    ) -> list[AutomationRecommendation]:
        """包括的提案生成"""

        self._logger.info("包括的提案生成開始: %s (候補: %s件)", target_function_name=target_function.name, candidate_count=len(candidate_functions))

        try:
            # Phase 1: 機械学習類似度分析
            ml_results = self.ml_similarity_service.batch_analyze_ml_similarities(
                target_function, candidate_functions, max_results=20
            )

            # Phase 2: パターン分析・カテゴリ分類
            function_patterns = self._analyze_function_patterns(target_function, ml_results)

            # Phase 3: 提案生成戦略決定
            recommendation_strategies = self._determine_recommendation_strategies(
                target_function, ml_results, function_patterns
            )

            # フォールバック: 戦略が見つからない場合でも最低1件は提案
            if not recommendation_strategies and ml_results:
                recommendation_strategies.append("extend_existing")

            # Phase 4: 個別提案生成
            recommendations = []
            for strategy in recommendation_strategies[:max_recommendations]:
                recommendation = self._generate_specific_recommendation(target_function, ml_results, strategy)

                if recommendation:
                    recommendations.append(recommendation)

            # Phase 5: 優先度・信頼度による最適化
            optimized_recommendations = self._optimize_recommendations(recommendations)

            if not optimized_recommendations:
                fallback = self._build_fallback_recommendation(
                    target_function=target_function,
                    ml_results=ml_results,
                    candidate_functions=candidate_functions,
                )
                if fallback:
                    optimized_recommendations = [fallback]

            self._logger.info("包括的提案生成完了: %s件の提案", recommendation_count=len(optimized_recommendations))
            return optimized_recommendations[:max_recommendations]

        except Exception as e:
            self._logger.exception("包括的提案生成エラー: %s: %s", target_function_name=target_function.name, error=str(e))
            return []

    def _build_fallback_recommendation(
        self,
        target_function: FunctionSignature,
        ml_results: list[MLSimilarityResult],
        candidate_functions: list[FunctionSignature],
    ) -> AutomationRecommendation | None:
        """戦略が生成されなかった場合のフォールバック提案を構築。"""

        best_result: MLSimilarityResult | None = ml_results[0] if ml_results else None
        if not best_result and candidate_functions:
            try:
                analysis = self.ml_similarity_service.analyze_ml_based_similarity(
                    target_function, candidate_functions[0]
                )
                best_result = analysis
                ml_results = [analysis]
            except Exception:
                best_result = None

        if not best_result:
            return None

        confidence = max(self.recommendation_thresholds["min_confidence_score"], best_result.overall_ml_similarity)
        fallback_action = RecommendationAction(
            action_type="extend",
            target_functions=[best_result.target_function],
            description=f"{best_result.target_function.name}を基に{target_function.name}の要件を実装",
            implementation_steps=[
                "既存機能の現在の挙動をレビュー",
                "不足している要件を洗い出し",
                "段階的に機能を拡張",
                "リグレッションテストを実行",
            ],
            expected_benefits=["実装コスト削減", "既存資産の活用", "保守性の向上"],
            estimated_effort_hours=2.0,
            risk_level="medium",
        )

        recommendation = AutomationRecommendation(
            recommendation_id=f"fallback_extend_{target_function.name}_{best_result.target_function.name}",
            category=RecommendationCategory.EXTEND_EXISTING,
            priority=RecommendationPriority.MEDIUM,
            title=f"既存機能拡張案: {best_result.target_function.name}",
            description="既存の類似機能を拡張するフォールバック提案",
            confidence_score=confidence,
            target_function=target_function,
            similar_functions=[(best_result.target_function, best_result.overall_ml_similarity)],
            ml_analysis_results=[best_result],
            recommended_actions=[fallback_action],
            alternative_approaches=["直接再利用を再検討", "機能の分割による共通化"],
            generated_timestamp=project_now().datetime,
            reasoning="戦略抽出が行えなかったため、安全な拡張案を提示",
            implementation_complexity="medium",
        )

        return recommendation

    def generate_direct_reuse_recommendations(
        self, target_function: FunctionSignature, ml_results: list[MLSimilarityResult]
    ) -> list[AutomationRecommendation]:
        """直接再利用提案生成"""

        recommendations = []

        for result in ml_results:
            if result.overall_ml_similarity >= self.recommendation_thresholds["direct_reuse_similarity"]:
                # 直接再利用提案作成
                recommendation = AutomationRecommendation(
                    recommendation_id=f"reuse_{target_function.name}_{result.target_function.name}",
                    category=RecommendationCategory.DIRECT_REUSE,
                    priority=RecommendationPriority.HIGH,
                    title=f"既存機能の直接再利用: {result.target_function.name}",
                    description=f"新規実装予定の{target_function.name}は、既存の{result.target_function.name}と{result.overall_ml_similarity:.2f}の高い類似度を示しています。",
                    confidence_score=result.overall_ml_similarity,
                    target_function=target_function,
                    similar_functions=[(result.target_function, result.overall_ml_similarity)],
                    ml_analysis_results=[result],
                    recommended_actions=[
                        RecommendationAction(
                            action_type="reuse",
                            target_functions=[result.target_function],
                            description=f"{result.target_function.name}を直接利用",
                            implementation_steps=[
                                f"{result.target_function.module_path}から{result.target_function.name}をインポート",
                                "既存機能の呼び出しに変更",
                                "パラメータマッピングの調整",
                                "テスト実行・動作確認",
                            ],
                            expected_benefits=[
                                "実装コスト削減",
                                "保守性向上",
                                "重複コード排除",
                                "テスト済み機能の活用",
                            ],
                            estimated_effort_hours=0.5,
                            risk_level="low",
                        )
                    ],
                    alternative_approaches=["既存機能の拡張による対応", "既存機能をベースとした新機能開発"],
                    generated_timestamp=project_now().datetime,
                    reasoning=result.reasoning,
                    implementation_complexity="simple",
                )

                recommendations.append(recommendation)

        return recommendations

    def generate_extension_recommendations(
        self, target_function: FunctionSignature, ml_results: list[MLSimilarityResult]
    ) -> list[AutomationRecommendation]:
        """拡張提案生成"""

        recommendations = []

        extension_candidates = [
            result
            for result in ml_results
            if (
                self.recommendation_thresholds["extend_similarity"]
                <= result.overall_ml_similarity
                < self.recommendation_thresholds["direct_reuse_similarity"]
            )
        ]

        for result in extension_candidates[:3]:  # 上位3件
            recommendation = AutomationRecommendation(
                recommendation_id=f"extend_{target_function.name}_{result.target_function.name}",
                category=RecommendationCategory.EXTEND_EXISTING,
                priority=RecommendationPriority.MEDIUM,
                title=f"既存機能の拡張: {result.target_function.name}",
                description=f"{result.target_function.name}を拡張して{target_function.name}の要件に対応",
                confidence_score=result.overall_ml_similarity * 0.8,  # 拡張の不確実性を考慮
                target_function=target_function,
                similar_functions=[(result.target_function, result.overall_ml_similarity)],
                ml_analysis_results=[result],
                recommended_actions=[
                    RecommendationAction(
                        action_type="extend",
                        target_functions=[result.target_function],
                        description=f"{result.target_function.name}を拡張し、オプション機能を追加",
                        implementation_steps=[
                            f"{result.target_function.name}の現在の実装を分析",
                            "新機能要件との差分特定",
                            "後方互換性を保った拡張実装",
                            "既存テストケース実行確認",
                            "拡張機能のテスト追加",
                        ],
                        expected_benefits=[
                            "既存機能の活用",
                            "実装コスト削減",
                            "一元的な機能管理",
                            "テスト資産の再利用",
                        ],
                        estimated_effort_hours=2.0,
                        risk_level="medium",
                    )
                ],
                alternative_approaches=[
                    "デコレータパターンによる機能追加",
                    "ストラテジーパターンによる処理切り替え",
                    "既存機能のラッパー実装",
                ],
                generated_timestamp=project_now().datetime,
                reasoning=f"類似度{result.overall_ml_similarity:.2f}で拡張による対応が効率的",
                implementation_complexity="medium",
            )

            recommendations.append(recommendation)

        return recommendations

    def generate_architectural_improvement_recommendations(
        self, target_function: FunctionSignature, ml_results: list[MLSimilarityResult]
    ) -> list[AutomationRecommendation]:
        """アーキテクチャ改善提案生成"""

        recommendations = []

        # 同一レイヤーで類似機能が多い場合の統合提案
        same_layer_functions = [
            result
            for result in ml_results
            if (
                result.target_function.ddd_layer == target_function.ddd_layer
                and result.overall_ml_similarity >= self.recommendation_thresholds["merge_similarity"]
            )
        ]

        if len(same_layer_functions) >= 2:
            recommendation = AutomationRecommendation(
                recommendation_id=f"arch_improve_{target_function.name}",
                category=RecommendationCategory.ARCHITECTURAL_IMPROVEMENT,
                priority=RecommendationPriority.HIGH,
                title=f"アーキテクチャ統合改善: {target_function.ddd_layer}層",
                description=f"{target_function.ddd_layer}層で類似機能が分散しています。統合による改善を提案します。",
                confidence_score=0.75,
                target_function=target_function,
                similar_functions=[
                    (result.target_function, result.overall_ml_similarity) for result in same_layer_functions
                ],
                ml_analysis_results=same_layer_functions,
                recommended_actions=[
                    RecommendationAction(
                        action_type="merge",
                        target_functions=[result.target_function for result in same_layer_functions],
                        description="類似機能の統合とアーキテクチャ改善",
                        implementation_steps=[
                            "類似機能の共通インターフェース設計",
                            "統合サービスクラス実装",
                            "戦略パターンによる処理振り分け",
                            "既存コードのリファクタリング",
                            "統合テストスイート作成",
                        ],
                        expected_benefits=[
                            "コードの一元化",
                            "保守性大幅向上",
                            "重複ロジック排除",
                            "アーキテクチャ健全性向上",
                            "将来拡張性確保",
                        ],
                        estimated_effort_hours=8.0,
                        risk_level="high",
                    )
                ],
                alternative_approaches=[
                    "ファクトリーパターンによる統一化",
                    "共通基底クラスによる統合",
                    "コンポジションパターンでの構成",
                ],
                generated_timestamp=project_now().datetime,
                reasoning=f"{len(same_layer_functions)}個の類似機能統合によるアーキテクチャ改善",
                implementation_complexity="complex",
            )

            recommendations.append(recommendation)

        return recommendations

    def _analyze_function_patterns(
        self, target_function: FunctionSignature, ml_results: list[MLSimilarityResult]
    ) -> dict[str, any]:
        """機能パターン分析"""

        patterns = {
            "detected_patterns": [],
            "common_keywords": set(),
            "layer_distribution": {},
            "parameter_patterns": [],
            "return_type_patterns": [],
        }

        # キーワードパターン検出
        target_name_lower = target_function.name.lower()
        for pattern_name, keywords in self.pattern_keywords.items():
            if any(keyword in target_name_lower for keyword in keywords):
                patterns["detected_patterns"].append(pattern_name)

        # 類似機能からの共通パターン抽出
        for result in ml_results:
            func_name_lower = result.target_function.name.lower()

            # 共通キーワード抽出
            for pattern_name, keywords in self.pattern_keywords.items():
                common_words = {keyword for keyword in keywords if keyword in func_name_lower}
                patterns["common_keywords"].update(common_words)

            # レイヤー分布
            layer = result.target_function.ddd_layer
            patterns["layer_distribution"][layer] = patterns["layer_distribution"].get(layer, 0) + 1

            # パラメータパターン
            param_count = len(result.target_function.parameters)
            patterns["parameter_patterns"].append(param_count)

            # 戻り値パターン
            if result.target_function.return_type:
                patterns["return_type_patterns"].append(result.target_function.return_type)

        return patterns

    def _determine_recommendation_strategies(
        self, target_function: FunctionSignature, ml_results: list[MLSimilarityResult], patterns: dict[str, Any]
    ) -> list[str]:
        """提案戦略決定"""

        strategies = []

        # 高類似度による直接再利用戦略
        high_similarity_count = sum(
            1
            for result in ml_results
            if result.overall_ml_similarity >= self.recommendation_thresholds["direct_reuse_similarity"]
        )

        if high_similarity_count > 0:
            strategies.append("direct_reuse")

        # 中程度類似度による拡張戦略
        medium_similarity_count = sum(
            1
            for result in ml_results
            if (
                self.recommendation_thresholds["extend_similarity"]
                <= result.overall_ml_similarity
                < self.recommendation_thresholds["direct_reuse_similarity"]
            )
        )

        if medium_similarity_count > 0:
            strategies.append("extend_existing")

        # 同一レイヤー集中による統合戦略
        same_layer_count = sum(
            1
            for result in ml_results
            if (
                result.target_function.ddd_layer == target_function.ddd_layer
                and result.overall_ml_similarity >= self.recommendation_thresholds["merge_similarity"]
            )
        )

        if same_layer_count >= 1:
            strategies.append("architectural_improvement")

        # パターン別戦略
        if "data_processing" in patterns["detected_patterns"]:
            strategies.append("extract_common")

        return strategies

    def _generate_specific_recommendation(
        self, target_function: FunctionSignature, ml_results: list[MLSimilarityResult], strategy: str
    ) -> AutomationRecommendation | None:
        """特定戦略による提案生成"""

        try:
            if strategy == "direct_reuse":
                recommendations = self.generate_direct_reuse_recommendations(target_function, ml_results)
                return recommendations[0] if recommendations else None

            if strategy == "extend_existing":
                recommendations = self.generate_extension_recommendations(target_function, ml_results)
                return recommendations[0] if recommendations else None

            if strategy == "architectural_improvement":
                recommendations = self.generate_architectural_improvement_recommendations(target_function, ml_results)

                return recommendations[0] if recommendations else None

            if strategy == "extract_common":
                # 共通処理の抽出提案（中程度以上の類似度が複数ある場合に有効）
                candidates = [
                    r for r in ml_results if r.overall_ml_similarity >= self.recommendation_thresholds["extend_similarity"]
                ]
                if not candidates:
                    return None

                similar_pairs = [(r.target_function, r.overall_ml_similarity) for r in candidates[:3]]
                confidence = min(0.8, max((r.overall_ml_similarity for r in candidates), default=0.6))

                recommendation = AutomationRecommendation(
                    recommendation_id=f"extract_common_{target_function.name}",
                    category=RecommendationCategory.EXTRACT_COMMON,
                    priority=RecommendationPriority.MEDIUM,
                    title=f"共通処理の抽出: {target_function.name}",
                    description="複数の類似機能から共通インターフェース/ユーティリティの抽出を提案",
                    confidence_score=confidence,
                    target_function=target_function,
                    similar_functions=similar_pairs,
                    ml_analysis_results=candidates[:3],
                    recommended_actions=[
                        RecommendationAction(
                            action_type="extract_common",
                            target_functions=[p[0] for p in similar_pairs],
                            description="共通処理のユーティリティ化/インターフェース抽出",
                            implementation_steps=[
                                "共通ロジックの特定",
                                "新しいユーティリティ/インターフェースの設計",
                                "既存機能を新インターフェースに適合",
                                "回帰テストの実行",
                            ],
                            expected_benefits=[
                                "重複排除",
                                "保守性向上",
                                "再利用性向上",
                            ],
                            estimated_effort_hours=3.0,
                            risk_level="medium",
                        )
                    ],
                    alternative_approaches=["段階的な抽出によるリスク低減", "アダプターパターンの適用"],
                    generated_timestamp=project_now().datetime,
                    reasoning="共通語彙/処理パターンの重複を検出",
                    implementation_complexity="medium",
                )

                return recommendation

            self._logger.warning("未サポートの戦略: %s", strategy=strategy)
            return None

        except Exception as e:
            self._logger.exception("提案生成エラー (strategy: %s): %s", strategy=strategy, error=str(e))
            return None

    def _optimize_recommendations(
        self, recommendations: list[AutomationRecommendation]
    ) -> list[AutomationRecommendation]:
        """提案最適化"""

        if not recommendations:
            return []

        # 信頼度による最初のフィルタリング
        filtered_recommendations = [
            rec
            for rec in recommendations
            if rec.confidence_score >= self.recommendation_thresholds["min_confidence_score"]
        ]

        # フォールバック: すべてフィルタで落ちた場合は最上位を1件残す
        if not filtered_recommendations and recommendations:
            filtered_recommendations = [recommendations[0]]

        # 優先度・信頼度・工数のバランスによるスコアリング
        def calculate_optimization_score(rec: AutomationRecommendation) -> float:
            priority_weights = {
                RecommendationPriority.CRITICAL: 1.0,
                RecommendationPriority.HIGH: 0.8,
                RecommendationPriority.MEDIUM: 0.6,
                RecommendationPriority.LOW: 0.4,
            }

            priority_score = priority_weights.get(rec.priority, 0.5)
            confidence_score = rec.confidence_score
            effort_penalty = max(0.1, 1.0 - (rec.get_effort_estimate() / 10.0))  # 10時間を基準

            return priority_score * 0.4 + confidence_score * 0.4 + effort_penalty * 0.2

        # スコア順でソート
        optimized_recommendations = sorted(filtered_recommendations, key=calculate_optimization_score, reverse=True)

        self._logger.debug("提案最適化完了: %s件", recommendation_count=len(optimized_recommendations))
        return optimized_recommendations

    def generate_implementation_guide(self, recommendation: AutomationRecommendation) -> dict[str, any]:
        """実装ガイド生成"""

        guide = {
            "recommendation_summary": {
                "title": recommendation.title,
                "category": recommendation.category.value,
                "confidence": f"{recommendation.confidence_score:.2f}",
                "estimated_effort": f"{recommendation.get_effort_estimate():.1f}時間",
            },
            "implementation_plan": [],
            "risk_assessment": [],
            "success_metrics": [],
            "testing_strategy": [],
        }

        # 実装プラン作成
        for action in recommendation.recommended_actions:
            action_plan = {
                "action_type": action.action_type,
                "steps": action.implementation_steps,
                "estimated_hours": action.estimated_effort_hours,
                "risk_level": action.risk_level,
            }
            guide["implementation_plan"].append(action_plan)

        # リスク評価
        if recommendation.implementation_complexity == "complex":
            guide["risk_assessment"].extend(
                ["複雑な実装のため段階的アプローチ推奨", "既存機能への影響範囲事前確認必須", "十分なテスト期間確保"]
            )

        # 成功指標
        guide["success_metrics"] = [
            "機能動作正常性確認",
            "既存テスト全パス",
            "コードカバレッジ維持・向上",
            "パフォーマンス劣化なし",
        ]

        # テスト戦略
        guide["testing_strategy"] = [
            "ユニットテスト作成・実行",
            "統合テスト実施",
            "既存機能回帰テスト",
            "エラーケースハンドリング確認",
        ]

        return guide
