#!/usr/bin/env python3

"""Domain.services.similar_function_detection_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""類似機能検出ドメインサービス

仕様書: SPEC-NIH-PREVENTION-CODEMAP-001
"""


# DDD準拠: Domain層はInfrastructure層に依存しない
# ロガーは依存性注入で受け取る
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Protocol

from noveler.domain.entities.similarity_analyzer import SimilarityAnalysisResult, SimilarityAnalyzer
from noveler.domain.value_objects.function_signature import FunctionSignature, FunctionSimilarityMatch
from noveler.domain.value_objects.project_time import project_now

if TYPE_CHECKING:

    from pathlib import Path

    from noveler.domain.interfaces.logger_service import ILoggerService


class FunctionIndexRepository(Protocol):
    """関数インデックスリポジトリプロトコル"""

    def save_function_signature(self, signature: FunctionSignature) -> bool:
        """関数シグネチャの保存"""
        ...

    def load_all_function_signatures(self) -> list[FunctionSignature]:
        """全関数シグネチャの読み込み"""
        ...

    def find_functions_by_layer(self, layer: str) -> list[FunctionSignature]:
        """層別関数検索"""
        ...

    def find_functions_by_pattern(self, pattern: str) -> list[FunctionSignature]:
        """パターン別関数検索"""
        ...


class SimilarityIndexRepository(Protocol):
    """類似度インデックスリポジトリプロトコル"""

    def save_similarity_result(self, source_id: str, target_id: str, result: SimilarityAnalysisResult) -> bool:
        """類似度結果の保存"""
        ...

    def load_similarity_result(self, source_id: str, target_id: str) -> SimilarityAnalysisResult | None:
        """類似度結果の読み込み"""
        ...

    def find_similar_functions(self, source_id: str, threshold: float = 0.7) -> list[tuple[str, float]]:
        """類似関数の検索"""
        ...


@dataclass(frozen=True)
class NIHPreventionResult:
    """NIH症候群防止結果Value Object"""

    # 検索対象
    query_function: FunctionSignature

    # 検索結果
    similar_functions: list[FunctionSimilarityMatch]
    total_candidates_analyzed: int
    analysis_duration_ms: int

    # 推奨事項
    reuse_recommendations: list[dict[str, str]]
    implementation_necessity_score: float  # 0.0(不要) - 1.0(必要)

    # メタ情報
    analysis_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    analysis_timestamp: datetime = field(default_factory=datetime.now)
    analyzer_version: str = "1.0.0"

    def get_top_match(self) -> FunctionSimilarityMatch | None:
        """最高類似度マッチの取得"""
        return self.similar_functions[0] if self.similar_functions else None

    def has_high_similarity_matches(self, threshold: float = 0.8) -> bool:
        """高類似度マッチの有無"""
        return any(match.overall_similarity >= threshold for match in self.similar_functions)

    def get_implementation_recommendation(self) -> str:
        """実装推奨事項の取得"""
        if self.implementation_necessity_score < 0.3:
            return "既存機能で十分対応可能 - 新規実装不要"
        if self.implementation_necessity_score < 0.7:
            return "既存機能の拡張で対応 - 部分的な新規実装"
        return "新規実装が適切 - 独自性が高い"


@dataclass
class SimilarFunctionDetectionRequest:
    """類似機能検出リクエスト"""

    # 検索対象
    target_function: FunctionSignature

    # 検索オプション
    search_scope: str = "all"  # "all", "same_layer", "related_modules"
    similarity_threshold: float = 0.5
    max_results: int = 10

    # 分析オプション
    enable_deep_analysis: bool = True
    include_architectural_check: bool = True
    generate_reuse_suggestions: bool = True

    # フィルタリング
    exclude_same_module: bool = True
    layer_filters: list[str] | None = None

    # キャッシュ利用
    use_cached_results: bool = True
    cache_expiry_hours: int = 24


class SimilarFunctionDetectionService:
    """類似機能検出ドメインサービス"""

    def __init__(
        self,
        similarity_analyzer: SimilarityAnalyzer,
        function_index_repo: FunctionIndexRepository,
        similarity_index_repo: SimilarityIndexRepository,
        project_root: Path,
        logger: ILoggerService | None = None,
    ) -> None:
        """初期化

        Args:
            similarity_analyzer: 類似度分析器
            function_index_repo: 関数インデックスリポジトリ
            similarity_index_repo: 類似度インデックスリポジトリ
            project_root: プロジェクトルートパス
            logger: ロガーインスタンス（依存性注入）
        """
        self.similarity_analyzer = similarity_analyzer
        self.function_index_repo = function_index_repo
        self.similarity_index_repo = similarity_index_repo
        self.project_root = project_root
        self.logger = logger

    def detect_similar_functions(self, request: SimilarFunctionDetectionRequest) -> NIHPreventionResult:
        """類似機能検出の実行"""
        if self.logger:
            self.logger.info("類似機能検出開始: %s", request.target_function.name)
        start_time = project_now().datetime

        # 検索候補の取得
        candidate_functions = self._get_candidate_functions(request)
        if self.logger:
            self.logger.info("検索候補: %s関数", len(candidate_functions))

        # 類似度分析の実行
        similar_matches = self._analyze_similarities(request.target_function, candidate_functions, request)

        # 再利用推奨事項の生成
        reuse_recommendations = []
        if request.generate_reuse_suggestions:
            reuse_recommendations = self._generate_reuse_recommendations(similar_matches)

        # 実装必要性スコアの計算
        necessity_score = self._calculate_implementation_necessity_score(similar_matches)

        # 実行時間計算
        end_time = project_now().datetime
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        result = NIHPreventionResult(
            query_function=request.target_function,
            similar_functions=similar_matches[: request.max_results],
            total_candidates_analyzed=len(candidate_functions),
            analysis_duration_ms=duration_ms,
            reuse_recommendations=reuse_recommendations,
            implementation_necessity_score=necessity_score,
        )

        if self.logger:
            self.logger.info("類似機能検出完了: %s件検出, 必要性スコア%s", len(similar_matches), necessity_score)
        return result

    def calculate_overall_similarity(self, func1: FunctionSignature, func2: FunctionSignature) -> float:
        """総合類似度計算"""
        analysis_result = self.similarity_analyzer.analyze_similarity(func1, func2)
        return analysis_result.overall_similarity

    def suggest_reuse_strategies(self, similar_matches: list[FunctionSimilarityMatch]) -> list[dict[str, str]]:
        """再利用戦略提案"""
        strategies = []

        for match in similar_matches:
            if match.is_high_confidence_match():
                strategy = match.get_reuse_recommendation()

                # より詳細な戦略を追加
                enhanced_strategy = self._enhance_reuse_strategy(match, strategy)
                strategies.append(enhanced_strategy)

        return strategies

    def validate_implementation_necessity(
        self,
        target_function: FunctionSignature,
        similar_functions: list[FunctionSimilarityMatch],
        necessity_threshold: float = 0.7,
    ) -> tuple[bool, list[str]]:
        """実装必要性の検証"""

        # 高類似度マッチの存在確認
        high_similarity_matches = [match for match in similar_functions if match.overall_similarity >= 0.8]

        validation_messages = []

        if high_similarity_matches:
            top_match = high_similarity_matches[0]
            validation_messages.append(
                f"⚠️ 高類似度関数発見: {top_match.target_function.name} (類似度: {top_match.overall_similarity:.3f})"
            )

            # 具体的な類似点を指摘
            breakdown = top_match.similarity_breakdown
            for dimension, score in breakdown.items():
                if score >= 0.7:
                    validation_messages.append(f"  - {dimension}: {score:.3f}")

            validation_messages.append("💡 既存機能の拡張を検討してください")

        # 中程度の類似度マッチの場合
        medium_similarity_matches = [match for match in similar_functions if 0.5 <= match.overall_similarity < 0.8]

        if medium_similarity_matches and not high_similarity_matches:
            validation_messages.append(f"📋 類似機能候補: {len(medium_similarity_matches)}件 - 部分的な機能統合を検討")

        # 実装必要性判定
        necessity_score = self._calculate_implementation_necessity_score(similar_functions)
        is_implementation_necessary = necessity_score >= necessity_threshold

        if not is_implementation_necessary:
            validation_messages.append(f"❌ 新規実装の必要性が低い (スコア: {necessity_score:.3f})")

        else:
            validation_messages.append(f"✅ 新規実装が適切 (スコア: {necessity_score:.3f})")

        return is_implementation_necessary, validation_messages

    def update_function_index(self, new_function: FunctionSignature) -> bool:
        """関数インデックスの更新"""
        if self.logger:
            self.logger.info("関数インデックス更新: %s", new_function.name)

        try:
            success = self.function_index_repo.save_function_signature(new_function)

            if success:
                # 既存関数との類似度を事前計算
                self._precompute_similarities_for_new_function(new_function)

            return success
        except Exception as e:
            if self.logger:
                self.logger.exception("関数インデックス更新エラー: %s", e)
            return False

    def _get_candidate_functions(self, request: SimilarFunctionDetectionRequest) -> list[FunctionSignature]:
        """検索候補関数の取得"""

        if request.search_scope == "same_layer":
            candidates = self.function_index_repo.find_functions_by_layer(
                request.target_function.ddd_layer or "unknown"
            )

        elif request.search_scope == "related_modules":
            # 関連モジュールから検索
            module_pattern = ".".join(request.target_function.module_path.split(".")[:-1])
            candidates = self.function_index_repo.find_functions_by_pattern(module_pattern)
        else:
            # 全体検索
            candidates = self.function_index_repo.load_all_function_signatures()

        # フィルタリング適用
        return self._apply_candidate_filters(candidates, request)


    def _apply_candidate_filters(
        self, candidates: list[FunctionSignature], request: SimilarFunctionDetectionRequest
    ) -> list[FunctionSignature]:
        """候補関数のフィルタリング"""

        filtered = candidates[:]

        # 同じモジュールを除外
        if request.exclude_same_module:
            filtered = [func for func in filtered if func.module_path != request.target_function.module_path]

        # 層フィルタ適用
        if request.layer_filters:
            filtered = [func for func in filtered if func.ddd_layer in request.layer_filters]

        # 自分自身を除外
        return [
            func
            for func in filtered
            if func.calculate_signature_hash() != request.target_function.calculate_signature_hash()
        ]


    def _analyze_similarities(
        self,
        target_function: FunctionSignature,
        candidates: list[FunctionSignature],
        request: SimilarFunctionDetectionRequest,
    ) -> list[FunctionSimilarityMatch]:
        """類似度分析の実行"""

        matches = []

        # キャッシュ利用の場合
        if request.use_cached_results:
            matches = self._try_load_cached_similarities(target_function, candidates, request.cache_expiry_hours)

        # キャッシュにない場合は新規計算
        if not matches:
            matches = self.similarity_analyzer.find_top_matches(
                target_function,
                candidates,
                top_k=request.max_results * 2,  # 余裕を持って多めに取得
            )

            # 結果をキャッシュに保存
            if request.use_cached_results:
                self._cache_similarity_results(target_function, matches)

        # しきい値フィルタリング（B30: テスト環境のMock値を安全に取り扱う）
        filtered: list[FunctionSimilarityMatch] = []
        for match in matches:
            sim = match.overall_similarity
            try:
                sim_val = float(sim)
            except Exception:
                # 非数値（Mock等）は除外
                continue
            if sim_val >= request.similarity_threshold:
                filtered.append(match)
        return filtered


    def _generate_reuse_recommendations(self, similar_matches: list[FunctionSimilarityMatch]) -> list[dict[str, str]]:
        """再利用推奨事項の生成"""
        recommendations = []

        for match in similar_matches[:3]:  # トップ3のみ
            base_recommendation = match.get_reuse_recommendation()

            # 詳細な推奨事項を追加
            detailed_recommendation = {
                "target_function": match.target_function.name,
                "similarity_score": match.overall_similarity,
                "action": base_recommendation["action"],
                "description": base_recommendation["description"],
                "effort": base_recommendation["effort"],
                "file_location": str(match.target_function.file_path),
                "match_reason": match.match_reason,
                "confidence": match.confidence_level,
            }

            # 具体的な統合方法を提案
            if match.overall_similarity >= 0.9:
                detailed_recommendation["integration_method"] = "関数呼び出しによる直接利用"
            elif match.overall_similarity >= 0.7:
                detailed_recommendation["integration_method"] = "パラメータ追加による機能拡張"
            else:
                detailed_recommendation["integration_method"] = "共通インターフェースの抽出"

            recommendations.append(detailed_recommendation)

        return recommendations

    def _calculate_implementation_necessity_score(self, similar_matches: list[FunctionSimilarityMatch]) -> float:
        """実装必要性スコアの計算"""

        if not similar_matches:
            return 1.0  # 類似関数がなければ実装が必要

        # 最高類似度マッチを基準に計算
        top_match = similar_matches[0]
        top_similarity = top_match.overall_similarity

        # 類似度が高いほど実装必要性は低い
        base_necessity = 1.0 - top_similarity

        # 信頼度を考慮
        confidence_factor = top_match.confidence_level
        adjusted_necessity = base_necessity * (1.0 + (1.0 - confidence_factor) * 0.3)

        # 複数の中程度類似関数がある場合は必要性を下げる
        medium_similarity_count = sum(1 for match in similar_matches if 0.5 <= match.overall_similarity < 0.8)

        if medium_similarity_count >= 2:
            adjusted_necessity *= 0.8

        return min(1.0, max(0.0, adjusted_necessity))

    def _enhance_reuse_strategy(self, match: FunctionSimilarityMatch, base_strategy: dict[str, str]) -> dict[str, str]:
        """再利用戦略の拡張"""

        enhanced = base_strategy.copy()
        enhanced.update(
            {
                "target_function": match.target_function.name,
                "similarity_score": match.overall_similarity,
                "confidence": match.confidence_level,
                "file_location": str(match.target_function.file_path),
                "module_path": match.target_function.module_path,
                "ddd_layer": match.target_function.ddd_layer or "unknown",
            }
        )

        # 類似度の詳細分析結果を追加
        breakdown = match.similarity_breakdown
        enhanced["similarity_details"] = {
            "syntactic": breakdown.get("syntactic", 0.0),
            "semantic": breakdown.get("semantic", 0.0),
            "functional": breakdown.get("functional", 0.0),
            "architectural": breakdown.get("architectural", 0.0),
        }

        # 具体的な統合手順を提案
        if match.overall_similarity >= 0.9:
            enhanced["integration_steps"] = [
                "既存関数を直接インポート",
                "必要に応じてWrapper関数作成",
                "単体テストの実行",
            ]
        elif match.overall_similarity >= 0.7:
            enhanced["integration_steps"] = [
                "既存関数の引数仕様確認",
                "拡張パラメータの設計",
                "下位互換性の確保",
                "統合テストの実装",
            ]
        else:
            enhanced["integration_steps"] = [
                "共通インターフェースの設計",
                "既存機能の抽象化",
                "新機能との統合ポイント特定",
                "リファクタリング計画の策定",
            ]

        return enhanced

    def _precompute_similarities_for_new_function(self, new_function: FunctionSignature) -> None:
        """新関数の類似度事前計算"""
        if self.logger:
            self.logger.info("類似度事前計算開始: %s", new_function.name)

        try:
            # 既存の全関数を取得
            existing_functions = self.function_index_repo.load_all_function_signatures()

            # バッチ類似度分析実行
            similar_matches = self.similarity_analyzer.batch_analyze_similarities(
                new_function,
                existing_functions,
                similarity_threshold=0.3,  # 低めのしきい値で多くの結果を保存
            )

            # 結果をキャッシュに保存
            for match in similar_matches:
                analysis_result = SimilarityAnalysisResult(
                    source_function=new_function,
                    target_function=match.target_function,
                    syntactic_similarity=None,  # 実際の実装では適切な値を設定
                    semantic_similarity=None,
                    functional_similarity=None,
                    architectural_similarity=None,
                    overall_similarity=match.overall_similarity,
                    confidence_score=match.confidence_level,
                )

                self.similarity_index_repo.save_similarity_result(
                    new_function.calculate_signature_hash(),
                    match.target_function.calculate_signature_hash(),
                    analysis_result,
                )

            if self.logger:
                self.logger.info("事前計算完了: %s件の類似度を保存", len(similar_matches))

        except Exception as e:
            if self.logger:
                self.logger.exception("類似度事前計算エラー: %s", e)

    def _try_load_cached_similarities(
        self, target_function: FunctionSignature, candidates: list[FunctionSignature], expiry_hours: int
    ) -> list[FunctionSimilarityMatch]:
        """キャッシュされた類似度の読み込み試行"""

        cached_matches = []
        target_id = target_function.calculate_signature_hash()

        for candidate in candidates:
            candidate_id = candidate.calculate_signature_hash()

            cached_result = self.similarity_index_repo.load_similarity_result(target_id, candidate_id)

            if cached_result:
                # 数値型でない場合（Mockなど）はキャッシュを無視
                try:
                    sim_val = float(getattr(cached_result, "overall_similarity", 0.0))
                    conf_val = float(getattr(cached_result, "confidence_score", 0.0))
                except Exception:
                    continue

                # 有効期限チェック（実装省略）
                match = FunctionSimilarityMatch(
                    source_function=target_function,
                    target_function=candidate,
                    overall_similarity=sim_val,
                    similarity_breakdown={"overall": sim_val},
                    confidence_level=conf_val,
                    match_reason="キャッシュから取得",
                )

                cached_matches.append(match)

        return cached_matches

    def _cache_similarity_results(
        self, target_function: FunctionSignature, matches: list[FunctionSimilarityMatch]
    ) -> None:
        """類似度結果のキャッシュ保存"""

        target_id = target_function.calculate_signature_hash()

        for match in matches:
            candidate_id = match.target_function.calculate_signature_hash()

            # 簡易的なSimilarityAnalysisResult作成
            result = SimilarityAnalysisResult(
                source_function=target_function,
                target_function=match.target_function,
                syntactic_similarity=None,
                semantic_similarity=None,
                functional_similarity=None,
                architectural_similarity=None,
                overall_similarity=match.overall_similarity,
                confidence_score=match.confidence_level,
            )

            self.similarity_index_repo.save_similarity_result(target_id, candidate_id, result)
