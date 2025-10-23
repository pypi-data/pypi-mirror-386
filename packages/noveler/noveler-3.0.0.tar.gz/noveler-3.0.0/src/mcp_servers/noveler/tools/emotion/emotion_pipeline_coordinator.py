"""感情表現パイプライン統合コーディネーター

6個のMCPツールを統合し、A38 STEP 8の感情曲線設計を
総合的に支援する統合パイプラインを提供する。
"""

import asyncio
import hashlib
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .base_emotion_tool import BaseEmotionTool, EmotionToolInput, EmotionToolOutput
from .cliche_detector_tool import CliqueDetectorTool
from .contextual_cue_retriever_tool import ContextualCueRetrieverTool
from .metaphor_diversity_scorer_tool import MetaphorDiversityScorerTool
from .micro_ab_emotion_test_tool import MicroABEmotionTestTool
from .physiology_checker_tool import PhysiologyCheckerTool
from .register_verifier_tool import RegisterVerifierTool


class PipelineMode(Enum):
    """パイプライン実行モード"""
    SEQUENTIAL = "sequential"    # 順次実行
    PARALLEL = "parallel"       # 並列実行
    SELECTIVE = "selective"     # 選択的実行


@dataclass
class PipelineConfig:
    """パイプライン設定"""
    mode: PipelineMode = PipelineMode.PARALLEL  # 並列実行をデフォルト
    enabled_tools: list[str] | None = None  # Noneの場合は全ツール有効
    context_metadata: dict[str, Any] | None = None
    quality_threshold: float = 70.0
    max_iterations: int = 3
    enable_caching: bool = True  # キャッシュ有効化
    cache_ttl_seconds: int = 300  # キャッシュTTL（5分）
    parallel_chunk_size: int = 3  # 並列実行時のチャンクサイズ


@dataclass
class PipelineResult:
    """パイプライン実行結果"""
    success: bool
    overall_score: float
    tool_results: dict[str, EmotionToolOutput]
    integrated_analysis: dict[str, Any]
    recommendations: list[str]
    final_text_suggestions: list[str]
    execution_metadata: dict[str, Any]


class EmotionPipelineCoordinator(BaseEmotionTool):
    """感情表現パイプライン統合コーディネーター

    6個の専門ツールを統合し、A38 STEP 8の感情曲線設計を
    包括的にサポートする統合システム。
    """

    def __init__(self) -> None:
        super().__init__("emotion_pipeline_coordinator")
        self._initialize_tools()
        self._initialize_integration_rules()
        self._initialize_performance_optimizations()

    def _initialize_tool(self) -> None:
        """ツール初期化"""
        self.logger.info("感情表現統合パイプライン初期化")

    def _initialize_tools(self) -> None:
        """個別ツールの初期化"""
        self.tools = {
            "cliche_detector": CliqueDetectorTool(),
            "contextual_cue_retriever": ContextualCueRetrieverTool(),
            "physiology_checker": PhysiologyCheckerTool(),
            "metaphor_diversity_scorer": MetaphorDiversityScorerTool(),
            "register_verifier": RegisterVerifierTool(),
            "micro_ab_emotion_test": MicroABEmotionTestTool()
        }

    def _initialize_integration_rules(self) -> None:
        """統合ルールの初期化"""
        # ツール間の依存関係定義
        self.tool_dependencies = {
            "contextual_cue_retriever": [],  # 最初に実行
            "cliche_detector": [],
            "physiology_checker": ["contextual_cue_retriever"],
            "metaphor_diversity_scorer": ["cliche_detector"],
            "register_verifier": ["contextual_cue_retriever"],
            "micro_ab_emotion_test": ["cliche_detector", "metaphor_diversity_scorer"]
        }

        # 統合重み（最終スコア計算用）
        self.integration_weights = {
            "cliche_detector": 0.20,
            "contextual_cue_retriever": 0.15,
            "physiology_checker": 0.20,
            "metaphor_diversity_scorer": 0.15,
            "register_verifier": 0.15,
            "micro_ab_emotion_test": 0.15
        }

    def _initialize_performance_optimizations(self) -> None:
        """パフォーマンス最適化の初期化"""
        # 結果キャッシュ（メモリベース、TTL付き）
        self.result_cache: dict[str, dict[str, EmotionToolOutput | float]] = {}
        self.cache_timestamps: dict[str, float] = {}

        # 並列実行用セマフォ（同時実行数制限）
        self.execution_semaphore = asyncio.Semaphore(6)  # 最大6ツール同時実行

        # パフォーマンスメトリクス
        self.performance_metrics = {
            "total_executions": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "average_execution_time": 0.0,
            "parallel_execution_count": 0
        }

        # 品質基準
        self.quality_thresholds = {
            "minimum_acceptable": 60.0,
            "good_quality": 75.0,
            "excellent_quality": 85.0
        }

    async def execute(self, input_data: EmotionToolInput) -> EmotionToolOutput:
        """最適化された統合パイプラインの実行

        Args:
            input_data: 入力データ（設定含む）

        Returns:
            統合結果
        """
        start_time = time.time()

        try:
            # パフォーマンスメトリクス更新
            self.performance_metrics["total_executions"] += 1

            # キャッシュキー生成
            cache_key = self._generate_cache_key(input_data)

            # キャッシュチェック
            if cached_result := self._get_cached_result(cache_key):
                self.performance_metrics["cache_hits"] += 1
                self.logger.info(f"キャッシュヒット: {cache_key[:16]}...")
                return cached_result

            self.performance_metrics["cache_misses"] += 1

            # パイプライン設定の抽出
            config = self._extract_pipeline_config(input_data.metadata or {})

            # 最適化されたパイプライン実行
            pipeline_result = await self._execute_optimized_pipeline(input_data, config)

            if not pipeline_result.success:
                return self.create_error_output(
                    "パイプライン実行エラー",
                    ["統合処理中にエラーが発生しました"]
                )

            # 統合分析結果の構築
            integrated_analysis = self._build_integrated_analysis(pipeline_result)

            # 最終推奨事項の生成
            final_recommendations = self._generate_final_recommendations(pipeline_result)

            # 実行時間計算
            execution_time = (time.time() - start_time) * 1000
            pipeline_result.execution_metadata["execution_time_ms"] = execution_time

            # 結果作成
            result = self.create_success_output(
                score=pipeline_result.overall_score,
                analysis=integrated_analysis,
                suggestions=final_recommendations,
                metadata=pipeline_result.execution_metadata
            )

            # 結果キャッシュ
            if config.enable_caching:
                self._cache_result(cache_key, result)

            # パフォーマンス統計更新
            self._update_performance_stats(execution_time)

            self.logger.info(f"パイプライン実行完了: {execution_time:.2f}ms, スコア: {pipeline_result.overall_score:.2f}")
            return result

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.exception(f"パイプライン実行エラー: {e!s}, 時間: {execution_time:.2f}ms")
            return self.create_error_output(
                f"パイプライン実行エラー: {e!s}",
                ["統合処理中にエラーが発生しました"]
            )

    async def execute_pipeline(self, text: str, config: PipelineConfig | None = None) -> PipelineResult:
        """外部向けパイプライン実行インターフェース

        Args:
            text: 分析対象テキスト
            config: パイプライン設定

        Returns:
            パイプライン実行結果
        """
        input_data = EmotionToolInput(
            text=text,
            metadata={"pipeline_config": config.__dict__ if config else {}}
        )

        config = config or PipelineConfig()
        return await self._execute_pipeline(input_data, config)

    def _extract_pipeline_config(self, metadata: dict[str, Any]) -> PipelineConfig:
        """メタデータからパイプライン設定を抽出

        Args:
            metadata: 入力メタデータ

        Returns:
            パイプライン設定
        """
        config_data = metadata.get("pipeline_config", {})

        return PipelineConfig(
            mode=PipelineMode(config_data.get("mode", "sequential")),
            enabled_tools=config_data.get("enabled_tools"),
            context_metadata=config_data.get("context_metadata", {}),
            quality_threshold=config_data.get("quality_threshold", 70.0),
            max_iterations=config_data.get("max_iterations", 3)
        )

    async def _execute_pipeline(self, input_data: EmotionToolInput,
                              config: PipelineConfig) -> PipelineResult:
        """パイプラインの実行

        Args:
            input_data: 入力データ
            config: パイプライン設定

        Returns:
            実行結果
        """
        self.logger.info(f"パイプライン実行開始: モード={config.mode.value}")

        try:
            if config.mode == PipelineMode.PARALLEL:
                tool_results = await self._execute_parallel(input_data, config)
            elif config.mode == PipelineMode.SELECTIVE:
                tool_results = await self._execute_selective(input_data, config)
            else:  # SEQUENTIAL
                tool_results = await self._execute_sequential(input_data, config)

            # 統合スコア計算
            overall_score = self._calculate_overall_score(tool_results)

            # 推奨事項統合
            recommendations = self._integrate_recommendations(tool_results)

            # テキスト改善提案
            text_suggestions = self._generate_text_suggestions(tool_results, input_data.text)

            return PipelineResult(
                success=True,
                overall_score=overall_score,
                tool_results=tool_results,
                integrated_analysis={},  # 後で構築
                recommendations=recommendations,
                final_text_suggestions=text_suggestions,
                execution_metadata={
                    "mode": config.mode.value,
                    "tools_executed": list(tool_results.keys()),
                    "execution_time": 0  # 実際の実行時間を記録する場合
                }
            )

        except Exception as e:
            self.logger.exception(f"パイプライン実行エラー: {e}")
            return PipelineResult(
                success=False,
                overall_score=0,
                tool_results={},
                integrated_analysis={},
                recommendations=[f"エラー: {e!s}"],
                final_text_suggestions=[],
                execution_metadata={}
            )

    async def _execute_sequential(self, input_data: EmotionToolInput,
                                config: PipelineConfig) -> dict[str, EmotionToolOutput]:
        """順次実行

        Args:
            input_data: 入力データ
            config: 設定

        Returns:
            ツール別結果
        """
        results = {}
        enabled_tools = config.enabled_tools or list(self.tools.keys())

        # 依存関係順序でツールを実行
        execution_order = self._resolve_execution_order(enabled_tools)

        for tool_name in execution_order:
            if tool_name in self.tools:
                self.logger.info(f"ツール実行: {tool_name}")

                # 前の結果を考慮した入力データ調整
                adjusted_input = self._adjust_input_for_tool(
                    input_data, tool_name, results, config.context_metadata
                )

                # ツール実行
                result = await self.tools[tool_name].safe_execute(adjusted_input)
                results[tool_name] = result

                self.logger.info(f"ツール完了: {tool_name}, スコア: {result.score}")

        return results

    async def _execute_parallel(self, input_data: EmotionToolInput,
                              config: PipelineConfig) -> dict[str, EmotionToolOutput]:
        """並列実行

        Args:
            input_data: 入力データ
            config: 設定

        Returns:
            ツール別結果
        """
        enabled_tools = config.enabled_tools or list(self.tools.keys())

        # 依存関係のないツールを並列実行
        tasks = []
        for tool_name in enabled_tools:
            if tool_name in self.tools:
                adjusted_input = self._adjust_input_for_tool(
                    input_data, tool_name, {}, config.context_metadata
                )
                task = self.tools[tool_name].safe_execute(adjusted_input)
                tasks.append((tool_name, task))

        # 並列実行
        results = {}
        completed_tasks = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)

        for i, (tool_name, _) in enumerate(tasks):
            result = completed_tasks[i]
            if isinstance(result, Exception):
                self.logger.error(f"ツール実行エラー: {tool_name}, {result}")
                results[tool_name] = self.tools[tool_name].create_error_output(str(result))
            else:
                results[tool_name] = result

        return results

    async def _execute_selective(self, input_data: EmotionToolInput,
                                config: PipelineConfig) -> dict[str, EmotionToolOutput]:
        """選択的実行

        Args:
            input_data: 入力データ
            config: 設定

        Returns:
            ツール別結果
        """
        # テキストの特徴に基づいてツールを選択
        selected_tools = self._select_tools_by_content(input_data.text, config)

        # 選択されたツールで順次実行
        temp_config = PipelineConfig(
            mode=PipelineMode.SEQUENTIAL,
            enabled_tools=selected_tools,
            context_metadata=config.context_metadata,
            quality_threshold=config.quality_threshold
        )

        return await self._execute_sequential(input_data, temp_config)

    def _resolve_execution_order(self, enabled_tools: list[str]) -> list[str]:
        """ツールの実行順序を依存関係に基づいて決定

        Args:
            enabled_tools: 有効なツールリスト

        Returns:
            実行順序リスト
        """
        # 簡化したトポロジカルソート
        ordered = []
        remaining = enabled_tools.copy()

        while remaining:
            # 依存関係がない、または依存先が既に実行済みのツールを探す
            ready_tools = []
            for tool in remaining:
                dependencies = self.tool_dependencies.get(tool, [])
                if all(dep in ordered or dep not in enabled_tools for dep in dependencies):
                    ready_tools.append(tool)

            if not ready_tools:
                # デッドロックを避けるため、残りのツールを追加
                ordered.extend(remaining)
                break

            # 最初の準備完了ツールを実行順序に追加
            ordered.extend(ready_tools)
            for tool in ready_tools:
                remaining.remove(tool)

        return ordered

    def _adjust_input_for_tool(self, base_input: EmotionToolInput, tool_name: str,
                             previous_results: dict[str, EmotionToolOutput],
                             context_metadata: dict[str, Any]) -> EmotionToolInput:
        """ツール向けの入力データ調整

        Args:
            base_input: 基本入力データ
            tool_name: 対象ツール名
            previous_results: 前の結果
            context_metadata: 追加コンテキスト

        Returns:
            調整済み入力データ
        """
        metadata = (base_input.metadata or {}).copy()
        metadata.update(context_metadata or {})

        # ツール固有の調整
        if tool_name == "micro_ab_emotion_test" and previous_results:
            # A/Bテストには複数の候補が必要（簡化実装）
            metadata["variant_a"] = base_input.text
            metadata["variant_b"] = base_input.text + "（改良版）"  # 実際には他の結果から生成

        return EmotionToolInput(
            text=base_input.text,
            emotion_layer=base_input.emotion_layer,
            intensity=base_input.intensity,
            context=base_input.context,
            metadata=metadata
        )

    def _select_tools_by_content(self, text: str, config: PipelineConfig) -> list[str]:
        """テキスト内容に基づくツール選択

        Args:
            text: 分析対象テキスト
            config: 設定

        Returns:
            選択されたツールリスト
        """
        selected = []

        # 基本チェック系は常に実行
        selected.extend(["cliche_detector", "contextual_cue_retriever"])

        # 生理学的記述があれば PhysiologyChecker を追加
        if any(word in text for word in ["心臓", "脈", "息", "血", "汗", "震え"]):
            selected.append("physiology_checker")

        # 比喩表現があれば MetaphorDiversityScorer を追加
        if any(word in text for word in ["のような", "のように", "まるで", "あたかも"]):
            selected.append("metaphor_diversity_scorer")

        # 長いテキストなら文体チェック
        if len(text) > 200:
            selected.append("register_verifier")

        return selected

    def _calculate_overall_score(self, tool_results: dict[str, EmotionToolOutput]) -> float:
        """全体スコアの計算

        Args:
            tool_results: ツール実行結果

        Returns:
            統合スコア（0-100）
        """
        total_weighted_score = 0
        total_weight = 0

        for tool_name, result in tool_results.items():
            if result.success and result.score is not None:
                weight = self.integration_weights.get(tool_name, 0.1)
                total_weighted_score += result.score * weight
                total_weight += weight

        if total_weight == 0:
            return 0

        return total_weighted_score / total_weight

    def _integrate_recommendations(self, tool_results: dict[str, EmotionToolOutput]) -> list[str]:
        """推奨事項の統合

        Args:
            tool_results: ツール実行結果

        Returns:
            統合された推奨事項
        """
        all_recommendations = []

        for tool_name, result in tool_results.items():
            if result.success and result.suggestions:
                # ツール名プレフィックス付きで追加
                prefixed = [f"[{tool_name}] {suggestion}" for suggestion in result.suggestions[:2]]
                all_recommendations.extend(prefixed)

        return all_recommendations[:10]  # 最大10個の推奨事項

    def _generate_text_suggestions(self, tool_results: dict[str, EmotionToolOutput],
                                 original_text: str) -> list[str]:
        """テキスト改善提案の生成

        Args:
            tool_results: ツール実行結果
            original_text: 元のテキスト

        Returns:
            テキスト改善提案
        """
        suggestions = []

        # 陳腐表現チェック結果に基づく改善提案
        if "cliche_detector" in tool_results:
            cliche_result = tool_results["cliche_detector"]
            if cliche_result.success and cliche_result.analysis:
                flagged = cliche_result.analysis.get("flagged_phrases", [])
                if flagged:
                    suggestions.append(f"「{flagged[0]}」をより独創的な表現に変更")

        # 生理反応チェック結果に基づく提案
        if "physiology_checker" in tool_results:
            physio_result = tool_results["physiology_checker"]
            if physio_result.success and physio_result.score and physio_result.score < 70:
                suggestions.append("生理学的描写をより正確で詳細な表現に改良")

        # 比喩多様性に基づく提案
        if "metaphor_diversity_scorer" in tool_results:
            metaphor_result = tool_results["metaphor_diversity_scorer"]
            if metaphor_result.success and metaphor_result.score and metaphor_result.score < 60:
                suggestions.append("比喩表現の多様性を高めて独創性を向上")

        return suggestions[:5]  # 最大5個の提案

    def _build_integrated_analysis(self, pipeline_result: PipelineResult) -> dict[str, Any]:
        """統合分析結果の構築

        Args:
            pipeline_result: パイプライン実行結果

        Returns:
            統合分析データ
        """
        analysis = {
            "overall_assessment": {
                "score": pipeline_result.overall_score,
                "quality_level": self._get_quality_level(pipeline_result.overall_score),
                "tools_executed": len(pipeline_result.tool_results)
            },
            "tool_summary": {},
            "cross_tool_insights": []
        }

        # ツール別サマリー
        for tool_name, result in pipeline_result.tool_results.items():
            analysis["tool_summary"][tool_name] = {
                "success": result.success,
                "score": result.score,
                "key_findings": result.suggestions[:2] if result.suggestions else []
            }

        # クロスツール洞察（簡化実装）
        if len(pipeline_result.tool_results) >= 3:
            analysis["cross_tool_insights"].append(
                "複数のツールを通じた包括的分析により、バランスの取れた改善提案を提供"
            )

        return analysis

    def _get_quality_level(self, score: float) -> str:
        """スコアに基づく品質レベル判定

        Args:
            score: 統合スコア

        Returns:
            品質レベル
        """
        if score >= self.quality_thresholds["excellent_quality"]:
            return "excellent"
        if score >= self.quality_thresholds["good_quality"]:
            return "good"
        if score >= self.quality_thresholds["minimum_acceptable"]:
            return "acceptable"
        return "needs_improvement"

    def _generate_final_recommendations(self, pipeline_result: PipelineResult) -> list[str]:
        """最終推奨事項の生成

        Args:
            pipeline_result: パイプライン実行結果

        Returns:
            最終推奨事項リスト
        """
        recommendations = []

        # 品質レベルに基づく総合提案
        quality_level = self._get_quality_level(pipeline_result.overall_score)

        if quality_level == "needs_improvement":
            recommendations.append("感情表現の全体的な改善が必要です。特に独創性と生理学的正確性を重視してください")
        elif quality_level == "acceptable":
            recommendations.append("基本的な品質は確保されています。比喩の多様性と文体の一貫性を向上させてください")
        elif quality_level == "good":
            recommendations.append("良好な品質です。微細な調整で更なる向上が期待できます")
        else:
            recommendations.append("優秀な感情表現です。現在の水準を維持しつつ、さらなる独創性を追求してください")

        # ツール横断的な提案
        recommendations.extend(pipeline_result.recommendations[:3])

        # テキスト改善提案
        recommendations.extend(pipeline_result.final_text_suggestions[:2])

        return recommendations[:8]  # 最大8個の最終提案

    # ========================================
    # パフォーマンス最適化メソッド群
    # ========================================

    def _generate_cache_key(self, input_data: EmotionToolInput) -> str:
        """キャッシュキーの生成

        Args:
            input_data: 入力データ

        Returns:
            ハッシュ化されたキャッシュキー
        """
        # テキストとメタデータからハッシュ生成
        content = f"{input_data.text}_{input_data.emotion_layer}_{input_data.intensity}"
        if input_data.metadata:
            metadata_str = str(sorted(input_data.metadata.items()))
            content += f"_{metadata_str}"

        return hashlib.sha256(content.encode()).hexdigest()

    def _get_cached_result(self, cache_key: str) -> EmotionToolOutput | None:
        """キャッシュからの結果取得

        Args:
            cache_key: キャッシュキー

        Returns:
            キャッシュされた結果またはNone
        """
        if cache_key not in self.result_cache:
            return None

        # TTLチェック
        current_time = time.time()
        cache_time = self.cache_timestamps.get(cache_key, 0)

        if current_time - cache_time > 300:  # 5分でキャッシュ期限切れ
            del self.result_cache[cache_key]
            del self.cache_timestamps[cache_key]
            return None

        return self.result_cache[cache_key]

    def _cache_result(self, cache_key: str, result: EmotionToolOutput) -> None:
        """結果のキャッシュ

        Args:
            cache_key: キャッシュキー
            result: キャッシュする結果
        """
        # メモリ使用量制限（最大100エントリ）
        if len(self.result_cache) >= 100:
            # 最も古いエントリを削除
            oldest_key = min(self.cache_timestamps.keys(),
                           key=self.cache_timestamps.get)
            del self.result_cache[oldest_key]
            del self.cache_timestamps[oldest_key]

        self.result_cache[cache_key] = result
        self.cache_timestamps[cache_key] = time.time()

    def _update_performance_stats(self, execution_time: float) -> None:
        """パフォーマンス統計の更新

        Args:
            execution_time: 実行時間（ミリ秒）
        """
        total_executions = self.performance_metrics["total_executions"]
        current_avg = self.performance_metrics["average_execution_time"]

        # 移動平均計算
        new_avg = ((current_avg * (total_executions - 1)) + execution_time) / total_executions
        self.performance_metrics["average_execution_time"] = new_avg

    async def _execute_optimized_pipeline(
        self,
        input_data: EmotionToolInput,
        config: PipelineConfig
    ) -> PipelineResult:
        """最適化されたパイプライン実行

        Args:
            input_data: 入力データ
            config: パイプライン設定

        Returns:
            パイプライン実行結果
        """
        if config.mode == PipelineMode.PARALLEL:
            return await self._execute_parallel_pipeline(input_data, config)
        if config.mode == PipelineMode.SELECTIVE:
            return await self._execute_selective_pipeline(input_data, config)
        return await self._execute_sequential_pipeline(input_data, config)

    async def _execute_parallel_pipeline(
        self,
        input_data: EmotionToolInput,
        config: PipelineConfig
    ) -> PipelineResult:
        """並列パイプライン実行（最適化版）

        Args:
            input_data: 入力データ
            config: パイプライン設定

        Returns:
            並列実行結果
        """
        self.performance_metrics["parallel_execution_count"] += 1
        start_time = time.time()

        # 有効ツール取得
        enabled_tools = config.enabled_tools or list(self.tools.keys())
        tool_results = {}

        try:
            # 並列実行（セマフォで同時実行数制御）
            async def execute_tool_with_semaphore(tool_name: str):
                async with self.execution_semaphore:
                    tool = self.tools[tool_name]
                    tool_start = time.time()
                    result = await tool.execute(input_data)
                    tool_time = (time.time() - tool_start) * 1000
                    self.logger.debug(f"{tool_name}実行時間: {tool_time:.2f}ms")
                    return tool_name, result

            # 並列タスク作成・実行
            tasks = [
                execute_tool_with_semaphore(tool_name)
                for tool_name in enabled_tools
            ]

            # 全タスクを並列実行
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 結果処理
            for result in results:
                if isinstance(result, Exception):
                    self.logger.error(f"ツール実行エラー: {result!s}")
                    continue

                tool_name, tool_output = result
                tool_results[tool_name] = tool_output

            # 統合スコア計算
            overall_score = self._calculate_weighted_score(tool_results)

            # 実行メタデータ
            execution_time = (time.time() - start_time) * 1000
            metadata = {
                "execution_mode": "parallel",
                "tools_executed": len(tool_results),
                "successful_tools": len([r for r in tool_results.values() if r.success]),
                "total_execution_time": execution_time,
                "parallel_efficiency": len(enabled_tools) / execution_time * 1000
            }

            return PipelineResult(
                success=len(tool_results) > 0,
                overall_score=overall_score,
                tool_results=tool_results,
                integrated_analysis=self._create_integrated_analysis(tool_results),
                recommendations=self._extract_cross_tool_recommendations(tool_results),
                final_text_suggestions=self._generate_text_improvements(tool_results),
                execution_metadata=metadata
            )

        except Exception as e:
            self.logger.exception(f"並列パイプライン実行エラー: {e!s}")
            return PipelineResult(
                success=False,
                overall_score=0.0,
                tool_results={},
                integrated_analysis={},
                recommendations=[f"実行エラー: {e!s}"],
                final_text_suggestions=[],
                execution_metadata={"error": str(e)}
            )

    def _calculate_weighted_score(self, tool_results: dict[str, EmotionToolOutput]) -> float:
        """重み付きスコア計算

        Args:
            tool_results: ツール実行結果

        Returns:
            重み付き総合スコア
        """
        total_weighted_score = 0.0
        total_weight = 0.0

        for tool_name, result in tool_results.items():
            if result.success and tool_name in self.integration_weights:
                weight = self.integration_weights[tool_name]
                total_weighted_score += result.score * weight
                total_weight += weight

        return total_weighted_score / total_weight if total_weight > 0 else 0.0

    def get_performance_metrics(self) -> dict[str, int | float]:
        """パフォーマンスメトリクスの取得

        Returns:
            パフォーマンス統計
        """
        cache_hit_rate = (
            self.performance_metrics["cache_hits"] /
            max(self.performance_metrics["total_executions"], 1)
        ) * 100

        return {
            **self.performance_metrics,
            "cache_hit_rate_percent": cache_hit_rate,
            "cached_entries": len(self.result_cache)
        }
