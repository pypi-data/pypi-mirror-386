#!/usr/bin/env python3
"""機械学習ベース類似度判定サービス - NIH症候群防止システム Phase2

SPEC: SPEC-NIH-PREVENTION-CODEMAP-001
責務: 高精度類似機能検出のための機械学習ベース判定システム
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from noveler.domain.entities.similarity_analyzer import SimilarityAnalysisResult, SimilarityAnalyzer
from noveler.domain.interfaces.logger_interface import ILogger, NullLogger
from noveler.domain.interfaces.nlp_analysis_interface import INLPAnalysisAdapter
from noveler.domain.value_objects.function_signature import FunctionSignature


@dataclass
class MLSimilarityFeatures:
    """機械学習ベース類似度特徴量"""

    syntactic_score: float
    semantic_score: float
    functional_score: float
    architectural_score: float
    nlp_similarity_score: float
    intent_similarity_score: float
    structural_complexity_score: float
    confidence_score: float

    def get_feature_vector(self) -> list[float]:
        """特徴量ベクトル取得"""
        return [
            self.syntactic_score,
            self.semantic_score,
            self.functional_score,
            self.architectural_score,
            self.nlp_similarity_score,
            self.intent_similarity_score,
            self.structural_complexity_score,
            self.confidence_score,
        ]

    def get_weighted_similarity(self, weights: dict[str, float] | None = None) -> float:
        """重み付け類似度計算"""

        if weights is None:
            # デフォルト重み（Phase2最適化版）
            weights = {
                "syntactic": 0.15,
                "semantic": 0.25,
                "functional": 0.20,
                "architectural": 0.10,
                "nlp_similarity": 0.20,
                "intent_similarity": 0.10,
            }

        return (
            self.syntactic_score * weights.get("syntactic", 0.15)
            + self.semantic_score * weights.get("semantic", 0.25)
            + self.functional_score * weights.get("functional", 0.20)
            + self.architectural_score * weights.get("architectural", 0.10)
            + self.nlp_similarity_score * weights.get("nlp_similarity", 0.20)
            + self.intent_similarity_score * weights.get("intent_similarity", 0.10)
        )


@dataclass
class MLSimilarityResult:
    """機械学習ベース類似度判定結果"""

    source_function: FunctionSignature
    target_function: FunctionSignature
    ml_features: MLSimilarityFeatures
    overall_ml_similarity: float
    confidence_level: str  # 'high', 'medium', 'low'
    recommended_action: str  # 'reuse', 'extend', 'new_implementation'
    reasoning: str
    feature_importance_ranking: list[tuple[str, float]]

    def is_high_similarity(self, threshold: float = 0.8) -> bool:
        """高類似度判定"""
        return self.overall_ml_similarity >= threshold

    def is_reuse_recommended(self) -> bool:
        """再利用推奨判定"""
        return self.recommended_action == "reuse"

    def get_similarity_explanation(self) -> str:
        """類似度説明生成"""

        explanations = []

        # 総合スコア説明
        if self.overall_ml_similarity >= 0.9:
            explanations.append(f"非常に高い類似度 ({self.overall_ml_similarity:.2f})")
        elif self.overall_ml_similarity >= 0.7:
            explanations.append(f"高い類似度 ({self.overall_ml_similarity:.2f})")
        elif self.overall_ml_similarity >= 0.5:
            explanations.append(f"中程度の類似度 ({self.overall_ml_similarity:.2f})")
        else:
            explanations.append(f"低い類似度 ({self.overall_ml_similarity:.2f})")

        # 主要特徴量の説明
        top_features = self.feature_importance_ranking[:3]
        for feature_name, importance in top_features:
            explanations.append(f"{feature_name}: {importance:.2f}")

        return " | ".join(explanations)


class MachineLearningBasedSimilarityService:
    """機械学習ベース類似度判定サービス"""

    def __init__(
        self,
        similarity_analyzer: SimilarityAnalyzer,
        nlp_analyzer: INLPAnalysisAdapter,
        logger: ILogger | None = None,
        project_root: Path | None = None,
        enable_advanced_ml: bool = True,
    ) -> None:
        """初期化"""
        # ロガーは未指定時にNullLoggerを使用
        self._logger: ILogger = logger or NullLogger()
        self.similarity_analyzer = similarity_analyzer
        self.nlp_analyzer = nlp_analyzer
        # project_root は未指定でも動作可能に（推奨: 明示指定）
        self.project_root = Path(project_root) if project_root is not None else Path.cwd()
        self.enable_advanced_ml = enable_advanced_ml

        # しきい値設定（学習により最適化される）
        self.similarity_thresholds = {
            "high_confidence": 0.85,
            "medium_confidence": 0.65,
            "low_confidence": 0.45,
            "reuse_recommendation": 0.75,
        }

        # 特徴量重み（学習により最適化される）
        self.feature_weights = {
            "syntactic": 0.15,
            "semantic": 0.25,
            "functional": 0.20,
            "architectural": 0.10,
            "nlp_similarity": 0.20,
            "intent_similarity": 0.10,
        }

        self._logger.info(
            f"MachineLearningBasedSimilarityService初期化完了 (advanced_ml: {enable_advanced_ml})"
        )

    def analyze_ml_based_similarity(
        self, source_function: FunctionSignature, target_function: FunctionSignature
    ) -> MLSimilarityResult:
        """機械学習ベース類似度分析"""

        try:
            # 基本類似度分析実行
            basic_analysis = self.similarity_analyzer.analyze_similarity(source_function, target_function)

            # NLP特徴量抽出
            nlp_features = self._extract_nlp_features(source_function, target_function)

            # 機械学習特徴量構築
            ml_features = self._build_ml_features(basic_analysis, nlp_features)

            # 総合類似度計算
            overall_similarity = ml_features.get_weighted_similarity(self.feature_weights)

            # 信頼度レベル判定
            confidence_level = self._determine_confidence_level(overall_similarity, ml_features)

            # 推奨アクション決定
            recommended_action = self._determine_recommended_action(overall_similarity, ml_features)

            # 推論理由生成
            reasoning = self._generate_reasoning(ml_features, overall_similarity)

            # 特徴量重要度ランキング
            feature_ranking = self._calculate_feature_importance_ranking(ml_features)

            result = MLSimilarityResult(
                source_function=source_function,
                target_function=target_function,
                ml_features=ml_features,
                overall_ml_similarity=overall_similarity,
                confidence_level=confidence_level,
                recommended_action=recommended_action,
                reasoning=reasoning,
                feature_importance_ranking=feature_ranking,
            )

            self._logger.debug(
                f"ML類似度分析完了: {source_function.name} vs {target_function.name} = {overall_similarity:.3f}"
            )

            return result

        except Exception as e:
            self._logger.exception("ML類似度分析エラー: %s vs %s: %s", (source_function.name), (target_function.name), e)

            # エラー時のデフォルト結果
            return self._create_error_result(source_function, target_function, str(e))

    def batch_analyze_ml_similarities(
        self, source_function: FunctionSignature, candidate_functions: list[FunctionSignature], max_results: int = 10
    ) -> list[MLSimilarityResult]:
        """バッチ機械学習類似度分析"""

        self._logger.info("バッチML類似度分析開始: %s件の候補", (len(candidate_functions)))

        results: list[Any] = []

        for candidate in candidate_functions:
            try:
                result = self.analyze_ml_based_similarity(source_function, candidate)
                results.append(result)

            except Exception as e:
                self._logger.warning("候補関数分析エラー (%s): %s", (candidate.name), e)
                continue

        # 類似度順ソート
        results.sort(key=lambda x: x.overall_ml_similarity, reverse=True)

        # 結果制限
        limited_results = results[:max_results]

        self._logger.info("バッチML類似度分析完了: %s件の結果", (len(limited_results)))
        return limited_results

    def optimize_similarity_thresholds(
        self, training_data: list[tuple[FunctionSignature, FunctionSignature, float]]
    ) -> dict[str, float]:
        """類似度しきい値の最適化（簡易機械学習）"""

        if not training_data:
            self._logger.warning("訓練データが空のため、しきい値最適化をスキップ")
            return self.similarity_thresholds

        self._logger.info("しきい値最適化開始: %s件の訓練データ", (len(training_data)))

        # 訓練データから類似度分布を分析
        similarities = []
        ground_truth_labels = []

        for source_func, target_func, ground_truth in training_data:
            try:
                result = self.analyze_ml_based_similarity(source_func, target_func)
                similarities.append(result.overall_ml_similarity)
                ground_truth_labels.append(ground_truth)
            except Exception as e:
                self._logger.warning("訓練データ分析エラー: %s", e)
                continue

        if not similarities:
            self._logger.error("有効な訓練データがないため、しきい値最適化失敗")
            return self.similarity_thresholds

        # 簡易最適化（分位点ベース）
        similarities.sort()
        n = len(similarities)

        optimized_thresholds = {
            "high_confidence": similarities[int(n * 0.9)] if n > 0 else 0.85,
            "medium_confidence": similarities[int(n * 0.7)] if n > 0 else 0.65,
            "low_confidence": similarities[int(n * 0.5)] if n > 0 else 0.45,
            "reuse_recommendation": similarities[int(n * 0.8)] if n > 0 else 0.75,
        }

        self._logger.info("しきい値最適化完了: %s", optimized_thresholds)

        # しきい値更新
        self.similarity_thresholds.update(optimized_thresholds)

        return optimized_thresholds

    def get_ml_performance_metrics(
        self, test_data: list[tuple[FunctionSignature, FunctionSignature, bool]]
    ) -> dict[str, float]:
        """機械学習性能メトリクス計算"""

        if not test_data:
            return {}

        self._logger.info("性能評価開始: %s件のテストデータ", (len(test_data)))

        true_positives = 0
        true_negatives = 0
        false_positives = 0
        false_negatives = 0

        for source_func, target_func, is_similar in test_data:
            try:
                result = self.analyze_ml_based_similarity(source_func, target_func)
                predicted_similar = result.overall_ml_similarity >= self.similarity_thresholds["reuse_recommendation"]

                if is_similar and predicted_similar:
                    true_positives += 1
                elif not is_similar and not predicted_similar:
                    true_negatives += 1
                elif not is_similar and predicted_similar:
                    false_positives += 1
                elif is_similar and not predicted_similar:
                    false_negatives += 1

            except Exception as e:
                self._logger.warning("テストデータ評価エラー: %s", e)
                continue

        # メトリクス計算
        total = true_positives + true_negatives + false_positives + false_negatives

        if total == 0:
            return {}

        accuracy = (true_positives + true_negatives) / total
        precision = (
            true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        )
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        metrics = {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "true_positives": true_positives,
            "true_negatives": true_negatives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
        }

        self._logger.info("性能評価完了: Accuracy=%.3f, F1=%.3f", accuracy, f1_score)

        return metrics

    def _extract_nlp_features(
        self, source_function: FunctionSignature, target_function: FunctionSignature
    ) -> dict[str, float]:
        """NLP特徴量抽出"""

        # 関数間意味類似度分析
        semantic_analysis = self.nlp_analyzer.analyze_function_semantic_similarity(
            source_function.name,
            source_function.parameters,
            source_function.docstring or "",
            target_function.name,
            target_function.parameters,
            target_function.docstring or "",
        )

        # 意図特徴量抽出
        source_intent = self.nlp_analyzer.extract_programming_intent_features(
            source_function.name, source_function.parameters, source_function.docstring
        )

        target_intent = self.nlp_analyzer.extract_programming_intent_features(
            target_function.name, target_function.parameters, target_function.docstring
        )

        # 意図類似度計算
        intent_similarity = self._calculate_intent_similarity(source_intent, target_intent)

        return {
            "name_similarity": semantic_analysis.get("name_similarity", 0.0),
            "parameter_similarity": semantic_analysis.get("parameter_similarity", 0.0),
            "docstring_similarity": semantic_analysis.get("docstring_similarity", 0.0),
            "overall_semantic": semantic_analysis.get("overall_semantic_similarity", 0.0),
            "intent_similarity": intent_similarity,
        }


    def _calculate_intent_similarity(self, intent1: dict[str, float], intent2: dict[str, float]) -> float:
        """意図類似度計算"""

        if not intent1 or not intent2:
            return 0.0

        # 共通特徴量の類似度
        common_features = set(intent1.keys()) & set(intent2.keys())

        if not common_features:
            return 0.0

        similarities = []

        for feature in common_features:
            val1 = intent1[feature]
            val2 = intent2[feature]

            # バイナリ特徴量の場合
            if val1 in [0.0, 1.0] and val2 in [0.0, 1.0]:
                similarity = 1.0 if val1 == val2 else 0.0
            else:
                # 連続値特徴量の場合
                max_val = max(abs(val1), abs(val2), 1.0)
                similarity = 1.0 - abs(val1 - val2) / max_val

            similarities.append(similarity)

        return sum(similarities) / len(similarities) if similarities else 0.0

    def _build_ml_features(
        self, basic_analysis: SimilarityAnalysisResult, nlp_features: dict[str, float]
    ) -> MLSimilarityFeatures:
        """機械学習特徴量構築"""

        # 基本類似度取得
        similarity_breakdown = basic_analysis.get_similarity_breakdown()

        return MLSimilarityFeatures(
            syntactic_score=similarity_breakdown.get("syntactic", 0.0),
            semantic_score=similarity_breakdown.get("semantic", 0.0),
            functional_score=similarity_breakdown.get("functional", 0.0),
            architectural_score=similarity_breakdown.get("architectural", 0.0),
            nlp_similarity_score=nlp_features.get("overall_semantic", 0.0),
            intent_similarity_score=nlp_features.get("intent_similarity", 0.0),
            structural_complexity_score=self._calculate_structural_complexity(basic_analysis),
            confidence_score=basic_analysis.confidence_score,
        )

    def _calculate_structural_complexity(self, analysis: SimilarityAnalysisResult) -> float:
        """構造的複雑度スコア計算"""

        # パラメータ数の類似性
        source_params = len(analysis.source_function.parameters)
        target_params = len(analysis.target_function.parameters)

        if source_params == 0 and target_params == 0:
            param_similarity = 1.0
        elif source_params == 0 or target_params == 0:
            param_similarity = 0.0
        else:
            param_similarity = 1.0 - abs(source_params - target_params) / max(source_params, target_params)

        # DDD層の一致性
        layer_match = 1.0 if analysis.source_function.ddd_layer == analysis.target_function.ddd_layer else 0.0

        # 複合スコア
        return param_similarity * 0.7 + layer_match * 0.3

    def _determine_confidence_level(self, similarity: float, features: MLSimilarityFeatures) -> str:
        """信頼度レベル判定"""

        if similarity >= self.similarity_thresholds["high_confidence"]:
            return "high"
        if similarity >= self.similarity_thresholds["medium_confidence"]:
            return "medium"
        return "low"

    def _determine_recommended_action(self, similarity: float, features: MLSimilarityFeatures) -> str:
        """推奨アクション決定"""

        if similarity >= self.similarity_thresholds["reuse_recommendation"]:
            return "reuse"
        if similarity >= self.similarity_thresholds["medium_confidence"]:
            return "extend"
        return "new_implementation"

    def _generate_reasoning(self, features: MLSimilarityFeatures, similarity: float) -> str:
        """推論理由生成"""

        reasons = []

        # 高スコア特徴量の特定
        if features.semantic_score >= 0.8:
            reasons.append("意味的類似度が非常に高い")
        if features.nlp_similarity_score >= 0.8:
            reasons.append("自然言語処理による類似度が高い")
        if features.functional_score >= 0.8:
            reasons.append("機能的類似性が高い")

        # 総合判定
        if similarity >= 0.85:
            reasons.append("総合的に非常に類似した機能")
        elif similarity >= 0.65:
            reasons.append("総合的に類似した機能")
        else:
            reasons.append("類似性は限定的")

        return " | ".join(reasons) if reasons else "類似度分析完了"

    def _calculate_feature_importance_ranking(self, features: MLSimilarityFeatures) -> list[tuple[str, float]]:
        """特徴量重要度ランキング計算"""

        feature_scores = {
            "syntactic": features.syntactic_score,
            "semantic": features.semantic_score,
            "functional": features.functional_score,
            "architectural": features.architectural_score,
            "nlp_similarity": features.nlp_similarity_score,
            "intent_similarity": features.intent_similarity_score,
            "structural_complexity": features.structural_complexity_score,
            "confidence": features.confidence_score,
        }

        # スコア順にソート
        return sorted(feature_scores.items(), key=lambda x: x[1], reverse=True)


    def _create_error_result(
        self, source_function: FunctionSignature, target_function: FunctionSignature, error_message: str
    ) -> MLSimilarityResult:
        """エラー時のデフォルト結果作成"""

        error_features = MLSimilarityFeatures(
            syntactic_score=0.0,
            semantic_score=0.0,
            functional_score=0.0,
            architectural_score=0.0,
            nlp_similarity_score=0.0,
            intent_similarity_score=0.0,
            structural_complexity_score=0.0,
            confidence_score=0.0,
        )

        return MLSimilarityResult(
            source_function=source_function,
            target_function=target_function,
            ml_features=error_features,
            overall_ml_similarity=0.0,
            confidence_level="low",
            recommended_action="new_implementation",
            reasoning=f"分析エラー: {error_message}",
            feature_importance_ranking=[],
        )
