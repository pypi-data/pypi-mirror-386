#!/usr/bin/env python3

"""Domain.entities.similarity_analyzer
Where: Domain entity modelling similarity analysis sessions.
What: Stores comparison parameters and results for similarity checks.
Why: Supports reuse of similarity analysis data across workflows.
"""

from __future__ import annotations

from datetime import timezone

"""類似度分析エンティティ

仕様書: SPEC-NIH-PREVENTION-CODEMAP-001
"""


import math
from dataclasses import dataclass, field

# B30品質作業指示書遵守: Domain純粋性回復
# DDD準拠: Domain層はInfrastructure依存を排除
from typing import TYPE_CHECKING, Any, Protocol

from noveler.domain.value_objects.function_signature import FunctionSignature, FunctionSimilarityMatch

if TYPE_CHECKING:
    from noveler.domain.interfaces.logger_service import ILoggerService
from noveler.domain.interfaces.logger_service import NullLoggerService

# Domain層での適切なパターン（依存性注入により外部から提供）
# 未注入時はNullLoggerで安全に動作させる
logger: "ILoggerService" = NullLoggerService()


@dataclass(frozen=True)
class SyntacticSimilarity:
    """構文的類似度Value Object"""

    score: float  # 0.0 - 1.0
    structure_similarity: float
    pattern_similarity: float
    control_flow_similarity: float
    breakdown: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """事後検証"""
        if not 0.0 <= self.score <= 1.0:
            msg = f"構文的類似度は0.0-1.0の範囲である必要があります: {self.score}"
            raise ValueError(msg)


@dataclass(frozen=True)
class SemanticSimilarity:
    """意味的類似度Value Object"""

    score: float  # 0.0 - 1.0
    lexical_similarity: float
    conceptual_similarity: float
    domain_similarity: float
    common_tokens: set[str] = field(default_factory=set)
    breakdown: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """事後検証"""
        if not 0.0 <= self.score <= 1.0:
            msg = f"意味的類似度は0.0-1.0の範囲である必要があります: {self.score}"
            raise ValueError(msg)


@dataclass(frozen=True)
class FunctionalSimilarity:
    """機能的類似度Value Object"""

    score: float  # 0.0 - 1.0
    io_pattern_similarity: float
    behavior_similarity: float
    responsibility_similarity: float
    side_effects_similarity: float
    breakdown: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """事後検証"""
        if not 0.0 <= self.score <= 1.0:
            msg = f"機能的類似度は0.0-1.0の範囲である必要があります: {self.score}"
            raise ValueError(msg)


@dataclass(frozen=True)
class ArchitecturalSimilarity:
    """アーキテクチャ類似度Value Object"""

    score: float  # 0.0 - 1.0
    layer_similarity: float
    pattern_similarity: float
    dependency_similarity: float
    breakdown: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """事後検証"""
        if not 0.0 <= self.score <= 1.0:
            msg = f"アーキテクチャ類似度は0.0-1.0の範囲である必要があります: {self.score}"
            raise ValueError(msg)


class SimilarityCalculationPort(Protocol):
    """類似度計算アダプタープロトコル"""

    def calculate_vector_similarity(self, vector1: dict[str, float], vector2: dict[str, float]) -> float:
        """ベクトル類似度計算"""
        ...

    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """テキスト類似度計算"""
        ...

    def calculate_tfidf_similarity(self, tokens1: list[str], tokens2: list[str], corpus: list[list[str]]) -> float:
        """TF-IDF類似度計算"""
        ...


@dataclass
class SimilarityAnalysisResult:
    """類似度分析結果"""

    source_function: FunctionSignature
    target_function: FunctionSignature
    syntactic_similarity: SyntacticSimilarity
    semantic_similarity: SemanticSimilarity
    functional_similarity: FunctionalSimilarity
    architectural_similarity: ArchitecturalSimilarity
    overall_similarity: float
    confidence_score: float
    analysis_timestamp: str = field(
        default_factory=lambda: __import__("datetime").datetime.now(timezone.utc).isoformat()
    )

    def get_similarity_breakdown(self) -> dict[str, float]:
        """類似度詳細内訳"""
        return {
            "syntactic": self.syntactic_similarity.score,
            "semantic": self.semantic_similarity.score,
            "functional": self.functional_similarity.score,
            "architectural": self.architectural_similarity.score,
            "overall": self.overall_similarity,
        }

    def is_significant_similarity(self, threshold: float = 0.7) -> bool:
        """有意な類似度の判定"""
        return self.overall_similarity >= threshold and self.confidence_score >= 0.6


class SimilarityAnalyzer:
    """類似度分析エンティティ

    責務:
        - 関数間の多次元的類似度計算
        - NIHシンドローム防止のための重複検出
        - 構文/意味/機能/アーキテクチャ各次元の分析

    設計原則:
        - SPEC-NIH-PREVENTION-CODEMAP-001準拠
        - ポートアダプターパターンによる柔軟な計算方式
        - 重み付けによる総合スコア算出

    依存:
        - SimilarityCalculationPort: 類似度計算アダプター
    """

    def __init__(
        self,
        similarity_calculator: SimilarityCalculationPort,
        # 重み設定（SPEC準拠）
        syntactic_weight: float = 0.25,
        semantic_weight: float = 0.35,
        functional_weight: float = 0.30,
        architectural_weight: float = 0.10,
    ) -> None:
        """初期化

        Args:
            similarity_calculator: 類似度計算アダプター
            syntactic_weight: 構文的類似度の重み（デフォルト0.25）
            semantic_weight: 意味的類似度の重み（デフォルト0.35）
            functional_weight: 機能的類似度の重み（デフォルト0.30）
            architectural_weight: アーキテクチャ類似度の重み（デフォルト0.10）

        Raises:
            ValueError: 重みの合計が1.0でない場合
        """
        self.similarity_calculator = similarity_calculator
        self.weights = {
            "syntactic": syntactic_weight,
            "semantic": semantic_weight,
            "functional": functional_weight,
            "architectural": architectural_weight,
        }

        # 重みの合計は1.0である必要がある
        total_weight = sum(self.weights.values())
        if abs(total_weight - 1.0) > 0.001:
            msg = f"重みの合計は1.0である必要があります: {total_weight}"
            raise ValueError(msg)

    def analyze_similarity(
        self,
        source_function: FunctionSignature,
        target_function: FunctionSignature,
        corpus: list[FunctionSignature] | None = None,
    ) -> SimilarityAnalysisResult:
        """包括的類似度分析

        4つの次元から関数の類似度を分析し、
        総合スコアと信頼度を算出。

        Args:
            source_function: 比較元関数シグネチャ
            target_function: 比較先関数シグネチャ
            corpus: TF-IDF計算用のコーパス（オプション）

        Returns:
            SimilarityAnalysisResult: 分析結果
        """
        logger.info("類似度分析開始: %s vs %s", (source_function.name), (target_function.name))

        # 各次元の類似度計算
        syntactic = self._calculate_syntactic_similarity(source_function, target_function)
        semantic = self._calculate_semantic_similarity(source_function, target_function, corpus)
        functional = self._calculate_functional_similarity(source_function, target_function)
        architectural = self._calculate_architectural_similarity(source_function, target_function)

        # 総合類似度計算
        overall_similarity = self._calculate_overall_similarity(syntactic, semantic, functional, architectural)

        # 信頼度スコア計算
        confidence_score = self._calculate_confidence_score(syntactic, semantic, functional, architectural)

        result = SimilarityAnalysisResult(
            source_function=source_function,
            target_function=target_function,
            syntactic_similarity=syntactic,
            semantic_similarity=semantic,
            functional_similarity=functional,
            architectural_similarity=architectural,
            overall_similarity=overall_similarity,
            confidence_score=confidence_score,
        )

        logger.info("類似度分析完了: 総合%.3f, 信頼度%.3f", overall_similarity, confidence_score)
        return result

    def batch_analyze_similarities(
        self,
        source_function: FunctionSignature,
        target_functions: list[FunctionSignature],
        similarity_threshold: float = 0.5,
    ) -> list[SimilarityAnalysisResult]:
        """バッチ類似度分析"""
        logger.info("バッチ類似度分析開始: %s vs %s関数", (source_function.name), (len(target_functions)))

        results: list[Any] = []
        corpus = target_functions  # コーパスとして利用

        for target_function in target_functions:
            try:
                result = self.analyze_similarity(source_function, target_function, corpus)
                if result.overall_similarity >= similarity_threshold:
                    results.append(result)
            except Exception as e:
                logger.warning("類似度分析エラー: %s - %s", (target_function.name), e)

        # 類似度でソート
        results.sort(key=lambda x: x.overall_similarity, reverse=True)

        logger.info("バッチ分析完了: %s件の類似関数を検出", (len(results)))
        return results

    def find_top_matches(
        self, source_function: FunctionSignature, candidate_functions: list[FunctionSignature], top_k: int = 5
    ) -> list[FunctionSimilarityMatch]:
        """トップマッチ検索"""
        results: Any = self.batch_analyze_similarities(source_function, candidate_functions, 0.3)

        matches = []
        for result in results[:top_k]:
            similarity_breakdown = result.get_similarity_breakdown()
            match_reason = self._generate_match_reason(result)

            match = FunctionSimilarityMatch(
                source_function=source_function,
                target_function=result.target_function,
                overall_similarity=result.overall_similarity,
                similarity_breakdown=similarity_breakdown,
                confidence_level=result.confidence_score,
                match_reason=match_reason,
            )

            matches.append(match)

        return matches

    def _calculate_syntactic_similarity(
        self, func1: FunctionSignature, func2: FunctionSignature
    ) -> SyntacticSimilarity:
        """構文的類似度計算"""

        # 構造的特徴の比較
        features1 = func1.get_structural_features()
        features2 = func2.get_structural_features()

        structure_similarity = self._calculate_feature_similarity(features1, features2)

        # パターン類似度（制御フロー）
        patterns1 = set(func1.control_flow_patterns)
        patterns2 = set(func2.control_flow_patterns)
        pattern_similarity = self._calculate_set_similarity(patterns1, patterns2)

        # 制御フロー複雑度の類似性
        complexity1 = len(func1.control_flow_patterns)
        complexity2 = len(func2.control_flow_patterns)
        max_complexity = max(complexity1, complexity2, 1)
        control_flow_similarity = 1.0 - abs(complexity1 - complexity2) / max_complexity

        # 総合構文的類似度
        score = structure_similarity * 0.4 + pattern_similarity * 0.4 + control_flow_similarity * 0.2

        return SyntacticSimilarity(
            score=score,
            structure_similarity=structure_similarity,
            pattern_similarity=pattern_similarity,
            control_flow_similarity=control_flow_similarity,
            breakdown={
                "structure": structure_similarity,
                "patterns": pattern_similarity,
                "control_flow": control_flow_similarity,
            },
        )

    def _calculate_semantic_similarity(
        self, func1: FunctionSignature, func2: FunctionSignature, corpus: list[FunctionSignature] | None = None
    ) -> SemanticSimilarity:
        """意味的類似度計算"""

        # 語彙的類似度
        tokens1 = func1.get_semantic_tokens()
        tokens2 = func2.get_semantic_tokens()

        if corpus:
            # TF-IDF を使用した類似度計算
            corpus_tokens = [func.get_semantic_tokens() for func in corpus]
            lexical_similarity = self.similarity_calculator.calculate_tfidf_similarity(tokens1, tokens2, corpus_tokens)

        else:
            # 基本的なJaccard類似度
            lexical_similarity = self._calculate_jaccard_similarity(set(tokens1), set(tokens2))

        # 概念的類似度（docstring比較）
        text1 = func1.docstring or ""
        text2 = func2.docstring or ""
        conceptual_similarity = self.similarity_calculator.calculate_text_similarity(text1, text2)

        # ドメイン類似度（DDD層とモジュールパス）
        domain_similarity = self._calculate_domain_similarity(func1, func2)

        # 共通トークン
        common_tokens = set(tokens1) & set(tokens2)

        # 総合意味的類似度
        score = lexical_similarity * 0.5 + conceptual_similarity * 0.3 + domain_similarity * 0.2

        return SemanticSimilarity(
            score=score,
            lexical_similarity=lexical_similarity,
            conceptual_similarity=conceptual_similarity,
            domain_similarity=domain_similarity,
            common_tokens=common_tokens,
            breakdown={"lexical": lexical_similarity, "conceptual": conceptual_similarity, "domain": domain_similarity},
        )

    def _calculate_functional_similarity(
        self, func1: FunctionSignature, func2: FunctionSignature
    ) -> FunctionalSimilarity:
        """機能的類似度計算"""

        # 入出力パターン類似度
        io_similarity = self._calculate_io_pattern_similarity(func1, func2)

        # 行動類似度（機能的特性の比較）
        chars1 = func1.get_functional_characteristics()
        chars2 = func2.get_functional_characteristics()
        behavior_similarity = self._calculate_binary_feature_similarity(chars1, chars2)

        # 責務類似度
        responsibility_similarity = self._calculate_responsibility_similarity(func1, func2)

        # 副作用類似度
        side_effects_similarity = self._calculate_side_effects_similarity(func1, func2)

        # 総合機能的類似度
        score = (
            io_similarity * 0.3
            + behavior_similarity * 0.3
            + responsibility_similarity * 0.2
            + side_effects_similarity * 0.2
        )

        return FunctionalSimilarity(
            score=score,
            io_pattern_similarity=io_similarity,
            behavior_similarity=behavior_similarity,
            responsibility_similarity=responsibility_similarity,
            side_effects_similarity=side_effects_similarity,
            breakdown={
                "io_patterns": io_similarity,
                "behavior": behavior_similarity,
                "responsibility": responsibility_similarity,
                "side_effects": side_effects_similarity,
            },
        )

    def _calculate_architectural_similarity(
        self, func1: FunctionSignature, func2: FunctionSignature
    ) -> ArchitecturalSimilarity:
        """アーキテクチャ類似度計算"""

        # DDD層類似度
        layer_similarity = 1.0 if func1.ddd_layer == func2.ddd_layer else 0.0

        # デザインパターン類似度
        decorators1 = set(func1.decorators)
        decorators2 = set(func2.decorators)
        pattern_similarity = self._calculate_set_similarity(decorators1, decorators2)

        # 依存関係類似度
        deps1 = func1.get_dependency_fingerprint()
        deps2 = func2.get_dependency_fingerprint()
        dependency_similarity = 1.0 if deps1 == deps2 else 0.5

        # 総合アーキテクチャ類似度
        score = layer_similarity * 0.5 + pattern_similarity * 0.3 + dependency_similarity * 0.2

        return ArchitecturalSimilarity(
            score=score,
            layer_similarity=layer_similarity,
            pattern_similarity=pattern_similarity,
            dependency_similarity=dependency_similarity,
            breakdown={
                "layer": layer_similarity,
                "patterns": pattern_similarity,
                "dependencies": dependency_similarity,
            },
        )

    def _calculate_overall_similarity(
        self,
        syntactic: SyntacticSimilarity,
        semantic: SemanticSimilarity,
        functional: FunctionalSimilarity,
        architectural: ArchitecturalSimilarity,
    ) -> float:
        """総合類似度計算（重み付け）"""
        return (
            syntactic.score * self.weights["syntactic"]
            + semantic.score * self.weights["semantic"]
            + functional.score * self.weights["functional"]
            + architectural.score * self.weights["architectural"]
        )

    def _calculate_confidence_score(
        self,
        syntactic: SyntacticSimilarity,
        semantic: SemanticSimilarity,
        functional: FunctionalSimilarity,
        architectural: ArchitecturalSimilarity,
    ) -> float:
        """信頼度スコア計算"""

        # 各次元のスコアの分散を考慮
        scores = [syntactic.score, semantic.score, functional.score, architectural.score]

        mean_score = sum(scores) / len(scores)
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
        std_dev = math.sqrt(variance)

        # 分散が小さいほど信頼度が高い
        consistency_factor = max(0.0, 1.0 - std_dev)

        # 絶対的なスコアレベルも考慮
        absolute_factor = mean_score

        return consistency_factor * 0.6 + absolute_factor * 0.4

    def _calculate_feature_similarity(self, features1: dict[str, int], features2: dict[str, int]) -> float:
        """特徴量類似度計算"""
        if not features1 or not features2:
            return 0.0

        # コサイン類似度を計算
        all_features = set(features1.keys()) | set(features2.keys())

        dot_product = sum(features1.get(feature, 0) * features2.get(feature, 0) for feature in all_features)

        norm1 = math.sqrt(sum(value**2 for value in features1.values()))
        norm2 = math.sqrt(sum(value**2 for value in features2.values()))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _calculate_set_similarity(self, set1: set, set2: set) -> float:
        """集合類似度計算（Jaccard係数）"""
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def _calculate_jaccard_similarity(self, set1: set, set2: set) -> float:
        """Jaccard類似度計算"""
        return self._calculate_set_similarity(set1, set2)

    def _calculate_binary_feature_similarity(self, features1: dict[str, bool], features2: dict[str, bool]) -> float:
        """バイナリ特徴量類似度"""
        if not features1 or not features2:
            return 0.0

        all_features = set(features1.keys()) | set(features2.keys())
        matches = sum(1 for feature in all_features if features1.get(feature, False) == features2.get(feature, False))

        return matches / len(all_features)

    def _calculate_io_pattern_similarity(self, func1: FunctionSignature, func2: FunctionSignature) -> float:
        """入出力パターン類似度"""

        # パラメータ数の類似性
        param_count_similarity = 1.0 - abs(len(func1.parameters) - len(func2.parameters)) / max(
            len(func1.parameters), len(func2.parameters), 1
        )

        # 戻り値型の類似性
        return_type_similarity = 1.0 if func1.return_type == func2.return_type else 0.0

        return param_count_similarity * 0.7 + return_type_similarity * 0.3

    def _calculate_responsibility_similarity(self, func1: FunctionSignature, func2: FunctionSignature) -> float:
        """責務類似度計算"""
        if func1.responsibility_category and func2.responsibility_category:
            return 1.0 if func1.responsibility_category == func2.responsibility_category else 0.0
        return 0.5  # 不明な場合は中間値

    def _calculate_side_effects_similarity(self, func1: FunctionSignature, func2: FunctionSignature) -> float:
        """副作用類似度計算"""
        chars1 = func1.get_functional_characteristics()
        chars2 = func2.get_functional_characteristics()

        is_pure1 = chars1.get("is_pure_function", False)
        is_pure2 = chars2.get("is_pure_function", False)

        return 1.0 if is_pure1 == is_pure2 else 0.0

    def _calculate_domain_similarity(self, func1: FunctionSignature, func2: FunctionSignature) -> float:
        """ドメイン類似度計算"""

        # DDD層の類似性
        layer_match = 1.0 if func1.ddd_layer == func2.ddd_layer else 0.0

        # モジュールパスの類似性
        path1_parts = func1.module_path.split(".")
        path2_parts = func2.module_path.split(".")

        common_parts = 0
        for p1, p2 in zip(path1_parts, path2_parts, strict=False):
            if p1 == p2:
                common_parts += 1
            else:
                break

        max_parts = max(len(path1_parts), len(path2_parts))
        path_similarity = common_parts / max_parts if max_parts > 0 else 0.0

        return layer_match * 0.6 + path_similarity * 0.4

    def _generate_match_reason(self, result: SimilarityAnalysisResult) -> str:
        """マッチ理由の生成"""
        breakdown = result.get_similarity_breakdown()

        # 最も高いスコアの次元を特定
        max_dimension = max(["syntactic", "semantic", "functional", "architectural"], key=lambda d: breakdown[d])

        reasons = {
            "syntactic": "構造的類似性が高い",
            "semantic": "意味的類似性が高い",
            "functional": "機能的類似性が高い",
            "architectural": "アーキテクチャ類似性が高い",
        }

        primary_reason = reasons[max_dimension]

        # 共通トークンがある場合は追加
        if hasattr(result.semantic_similarity, "common_tokens") and result.semantic_similarity.common_tokens:
            common_token_str = ", ".join(list(result.semantic_similarity.common_tokens)[:3])
            primary_reason += f" (共通要素: {common_token_str})"

        return primary_reason
