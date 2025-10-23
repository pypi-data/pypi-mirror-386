#!/usr/bin/env python3

"""Application.use_cases.nih_prevention_use_case
Where: Application use case focused on preventing NIH (Not Invented Here) pitfalls.
What: Runs analyses and generates recommendations to reuse existing assets effectively.
Why: Encourages teams to leverage internal knowledge instead of duplicating functionality.
"""

from __future__ import annotations



import asyncio
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from noveler.domain.interfaces.console_service_protocol import IConsoleService
    from noveler.domain.interfaces.logger_service_protocol import ILoggerService
    from noveler.domain.interfaces.path_service_protocol import IPathService
    from noveler.infrastructure.unit_of_work import IUnitOfWork

from noveler.application.base.abstract_use_case import AbstractUseCase
from noveler.domain.services.similar_function_detection_service import (
    NIHPreventionResult,
    SimilarFunctionDetectionRequest,
)
from noveler.domain.value_objects.function_signature import FunctionSignature


class CodeAnalysisPort(Protocol):
    """コード分析アダプタープロトコル"""

    def extract_function_signatures(self, file_path: Path) -> list[FunctionSignature]:
        """ファイルから関数シグネチャを抽出"""
        ...

    def extract_function_signatures_from_content(self, content: str, file_path: Path) -> list[FunctionSignature]:
        """文字列コンテンツから関数シグネチャを抽出"""
        ...

    def analyze_project_structure(self, project_root: Path) -> dict[str, list[FunctionSignature]]:
        """プロジェクト構造の分析"""
        ...


class ReportGenerationPort(Protocol):
    """レポート生成アダプタープロトコル"""

    def generate_prevention_report(self, result: NIHPreventionResult, format_type: str = "markdown") -> str:
        """NIH防止レポートの生成"""
        ...

    def save_report(self, report_content: str, file_path: Path) -> bool:
        """レポートの保存"""
        ...


@dataclass
class NIHPreventionRequest:
    """NIH症候群防止リクエスト"""

    # 分析対象
    analysis_type: str  # "single_function", "implementation_plan", "full_project"

    # 単一関数分析用
    target_function: FunctionSignature | None = None

    # 実装計画分析用
    implementation_files: dict[str, str] | None = None  # ファイルパス -> コード内容
    target_layer: str = "domain"

    # プロジェクト全体分析用
    project_root: Path | None = None

    # 分析オプション
    similarity_threshold: float = 0.7
    max_results_per_function: int = 5
    enable_deep_analysis: bool = True
    include_reuse_suggestions: bool = True

    # レポート設定
    generate_report: bool = True
    report_format: str = "markdown"  # "markdown", "json", "html"
    save_report_to_file: bool = True
    report_output_path: Path | None = None

    # 実行制御
    max_execution_time_seconds: int = 300
    enable_parallel_processing: bool = True
    batch_size: int = 10


@dataclass
class NIHPreventionResponse:
    """NIH症候群防止レスポンス"""

    # 分析結果
    prevention_results: list[NIHPreventionResult]

    # サマリー情報
    total_functions_analyzed: int
    total_similar_functions_found: int
    high_similarity_matches_count: int

    # 実装推奨事項
    overall_implementation_recommendations: list[dict[str, str]]
    critical_duplications: list[dict[str, str]]

    # パフォーマンス情報
    execution_time_ms: int
    analysis_efficiency_score: float

    # レポート情報
    report_generated: bool = False
    report_file_path: Path | None = None
    report_content: str | None = None

    def get_executive_summary(self) -> str:
        """エグゼクティブサマリーの取得"""
        if not self.prevention_results:
            return "❌ 分析対象の関数が見つかりませんでした"

        duplication_risk = (
            "高" if self.high_similarity_matches_count > 0 else "中" if self.total_similar_functions_found > 0 else "低"
        )

        return (
            f"🔍 NIH症候群防止分析完了\n"
            f"📊 分析関数: {self.total_functions_analyzed}件\n"
            f"🔗 類似関数: {self.total_similar_functions_found}件\n"
            f"⚠️ 重複リスク: {duplication_risk}\n"
            f"⏱️ 実行時間: {self.execution_time_ms}ms"
        )

    def has_implementation_risks(self) -> bool:
        """実装リスクの有無"""
        return self.high_similarity_matches_count > 0 or len(self.critical_duplications) > 0


class NIHPreventionUseCase(AbstractUseCase[NIHPreventionRequest, NIHPreventionResponse]):
    """NIH症候群防止ユースケース

    注意: 互換性のためにコンストラクタは(検出サービス, コードアナライザ, レポート生成器)
    の順で位置引数を受け付けます。
    """

    def __init__(
        self,
        detection_service,
        code_analyzer,
        report_generator,
        *,
        logger_service: ILoggerService | None = None,
        unit_of_work: IUnitOfWork | None = None,
        console_service: IConsoleService | None = None,
        path_service: IPathService | None = None,
        **kwargs,
    ) -> None:
        """初期化"""
        # 基底クラス初期化（共通サービス）
        super().__init__(
            logger_service=logger_service,
            unit_of_work=unit_of_work,
            console_service=console_service,
            path_service=path_service,
            **kwargs,
        )

        # 依存サービス
        self.detection_service = detection_service
        self.code_analyzer = code_analyzer
        self.report_generator = report_generator

    def execute(self, request: NIHPreventionRequest) -> NIHPreventionResponse:
        """同期API互換の実行メソッド

        内部で非同期分析メソッドをブリッジします。
        """
        try:
            # 通常の同期コンテキスト
            return asyncio.run(self.execute_nih_prevention_analysis(request))
        except RuntimeError as exc:
            if "asyncio.run()" not in str(exc):
                raise
            new_loop = asyncio.new_event_loop()
            try:
                return new_loop.run_until_complete(self.execute_nih_prevention_analysis(request))
            finally:
                new_loop.close()

    async def execute_nih_prevention_analysis(self, request: NIHPreventionRequest) -> NIHPreventionResponse:
        """NIH症候群防止分析の実行"""
        self.logger.info("NIH症候群防止分析開始: %s", (request.analysis_type))
        start_time = time.time()

        try:
            # タイムアウト設定
            analysis_task = asyncio.create_task(self._execute_analysis_by_type(request))

            prevention_results = await asyncio.wait_for(analysis_task, timeout=request.max_execution_time_seconds)

            # 分析結果の統合
            response = await self._create_comprehensive_response(prevention_results, request, start_time)

            # レポート生成
            if request.generate_report:
                await self._generate_and_save_report(response, request)

            self.logger.info("NIH症候群防止分析完了: %s件の結果", (len(prevention_results)))
            return response

        except asyncio.TimeoutError:
            self.logger.exception("NIH症候群防止分析タイムアウト: %s秒", (request.max_execution_time_seconds))
            raise
        except Exception as e:
            self.logger.exception("NIH症候群防止分析エラー: %s", e)
            raise

    async def analyze_single_function(
        self, target_function: FunctionSignature, analysis_options: dict[str, any] | None = None
    ) -> NIHPreventionResult:
        """単一関数の分析"""
        self.logger.info("単一関数分析: %s", (target_function.name))

        options = analysis_options or {}
        detection_request = SimilarFunctionDetectionRequest(
            target_function=target_function,
            similarity_threshold=options.get("similarity_threshold", 0.7),
            max_results=options.get("max_results", 5),
            enable_deep_analysis=options.get("enable_deep_analysis", True),
        )

        return self.detection_service.detect_similar_functions(detection_request)

    async def analyze_implementation_plan(
        self, implementation_files: dict[str, str], target_layer: str = "domain"
    ) -> list[NIHPreventionResult]:
        """実装計画の分析"""
        self.logger.info("実装計画分析: %sファイル, %s層", (len(implementation_files)), target_layer)

        results: list[Any] = []

        for file_path, content in implementation_files.items():
            try:
                # コンテンツから関数シグネチャを抽出
                function_signatures = self.code_analyzer.extract_function_signatures_from_content(
                    content, Path(file_path)
                )

                # 各関数に対してNIH分析実行
                for func_signature in function_signatures:
                    detection_request = SimilarFunctionDetectionRequest(
                        target_function=func_signature, search_scope="all", similarity_threshold=0.7, max_results=5
                    )

                    result = self.detection_service.detect_similar_functions(detection_request)
                    results.append(result)

            except Exception as e:
                self.logger.warning("ファイル分析エラー: %s - %s", file_path, e)

        return results

    async def generate_reuse_recommendations(
        self, prevention_results: list[NIHPreventionResult]
    ) -> list[dict[str, str]]:
        """再利用推奨事項の生成"""
        self.logger.info("再利用推奨事項生成: %s件の分析結果", (len(prevention_results)))

        recommendations = []

        # 高類似度マッチの統合推奨
        for result in prevention_results:
            high_similarity_matches = [match for match in result.similar_functions if match.overall_similarity >= 0.8]

            if high_similarity_matches:
                top_match = high_similarity_matches[0]

                recommendation = {
                    "type": "high_similarity_reuse",
                    "source_function": result.query_function.name,
                    "target_function": top_match.target_function.name,
                    "similarity_score": top_match.overall_similarity,
                    "recommendation": "既存機能を直接利用またはわずかな拡張で対応",
                    "effort_estimate": "low",
                    "risk_level": "low",
                    "implementation_steps": [
                        f"{top_match.target_function.name}を確認",
                        "必要に応じてWrapper関数作成",
                        "統合テスト実行",
                    ],
                }
                recommendations.append(recommendation)

        # 中程度類似度の統合機会
        medium_similarity_functions = []
        for result in prevention_results:
            medium_matches = [match for match in result.similar_functions if 0.5 <= match.overall_similarity < 0.8]
            medium_similarity_functions.extend(medium_matches)

        # 類似関数群の統合提案
        if len(medium_similarity_functions) >= 2:
            recommendation = {
                "type": "consolidation_opportunity",
                "functions_count": len(medium_similarity_functions),
                "recommendation": "類似機能群の統合による共通化",
                "effort_estimate": "high",
                "risk_level": "medium",
                "benefits": ["コード重複削減", "保守効率向上", "バグ修正の一元化"],
            }
            recommendations.append(recommendation)

        return recommendations

    async def validate_implementation_decisions(
        self, prevention_results: list[NIHPreventionResult], necessity_threshold: float = 0.7
    ) -> list[dict[str, any]]:
        """実装判断の検証"""
        self.logger.info("実装判断検証: %s件", (len(prevention_results)))

        validation_results = []

        for result in prevention_results:
            # 実装必要性の評価
            is_necessary = result.implementation_necessity_score >= necessity_threshold

            validation = {
                "function_name": result.query_function.name,
                "implementation_necessary": is_necessary,
                "necessity_score": result.implementation_necessity_score,
                "similar_functions_found": len(result.similar_functions),
                "recommendation": result.get_implementation_recommendation(),
                "validation_status": "approved" if is_necessary else "requires_review",
            }

            # 具体的な懸念事項
            concerns = []
            if result.has_high_similarity_matches(0.8):
                concerns.append("高類似度関数が存在 - 重複実装の可能性")

            if result.implementation_necessity_score < 0.5:
                concerns.append("実装必要性が低い - 既存機能で対応可能")

            validation["concerns"] = concerns
            validation_results.append(validation)

        return validation_results

    async def _execute_analysis_by_type(self, request: NIHPreventionRequest) -> list[NIHPreventionResult]:
        """分析タイプ別の実行"""

        if request.analysis_type == "single_function":
            if not request.target_function:
                msg = "single_function分析にはtarget_functionが必要です"
                raise ValueError(msg)

            result = await self.analyze_single_function(request.target_function)
            return [result]

        if request.analysis_type == "implementation_plan":
            if not request.implementation_files:
                msg = "implementation_plan分析にはimplementation_filesが必要です"
                raise ValueError(msg)

            return await self.analyze_implementation_plan(request.implementation_files, request.target_layer)

        if request.analysis_type == "full_project":
            if not request.project_root:
                msg = "full_project分析にはproject_rootが必要です"
                raise ValueError(msg)

            return await self._analyze_full_project(request)

        msg = f"無効な分析タイプ: {request.analysis_type}"
        raise ValueError(msg)

    async def _analyze_full_project(self, request: NIHPreventionRequest) -> list[NIHPreventionResult]:
        """プロジェクト全体分析"""
        self.logger.info("プロジェクト全体分析: %s", (request.project_root))

        # プロジェクト構造の分析
        project_functions = self.code_analyzer.analyze_project_structure(request.project_root)

        results: list[Any] = []
        all_functions = []
        for module_functions in project_functions.values():
            all_functions.extend(module_functions)

        self.logger.info("プロジェクト関数総数: %s", (len(all_functions)))

        # バッチ処理で効率的に分析
        if request.enable_parallel_processing:
            results: Any = await self._parallel_batch_analysis(all_functions, request)
        else:
            results: Any = await self._sequential_analysis(all_functions, request)

        return results

    async def _parallel_batch_analysis(
        self, functions: list[FunctionSignature], request: NIHPreventionRequest
    ) -> list[NIHPreventionResult]:
        """並列バッチ分析"""

        # 関数をバッチに分割
        batches = [functions[i : i + request.batch_size] for i in range(0, len(functions), request.batch_size)]

        results: list[Any] = []

        # 並列実行
        for batch in batches:
            batch_tasks = []
            for func in batch:
                detection_request = SimilarFunctionDetectionRequest(
                    target_function=func,
                    similarity_threshold=request.similarity_threshold,
                    max_results=request.max_results_per_function,
                )

                task = asyncio.create_task(
                    asyncio.to_thread(self.detection_service.detect_similar_functions, detection_request)
                )

                batch_tasks.append(task)

            # バッチ結果の収集
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, Exception):
                    self.logger.warning("バッチ分析エラー: %s", result)
                else:
                    results.append(result)

        return results

    async def _sequential_analysis(
        self, functions: list[FunctionSignature], request: NIHPreventionRequest
    ) -> list[NIHPreventionResult]:
        """シーケンシャル分析"""

        results: list[Any] = []

        for func in functions:
            try:
                detection_request = SimilarFunctionDetectionRequest(
                    target_function=func,
                    similarity_threshold=request.similarity_threshold,
                    max_results=request.max_results_per_function,
                )

                result = self.detection_service.detect_similar_functions(detection_request)
                results.append(result)

            except Exception as e:
                self.logger.warning("関数分析エラー: %s - %s", (func.name), e)

        return results

    async def _create_comprehensive_response(
        self, prevention_results: list[NIHPreventionResult], request: NIHPreventionRequest, start_time: float
    ) -> NIHPreventionResponse:
        """包括的レスポンスの作成"""

        # 統計情報の計算
        total_functions = len(prevention_results)
        total_similar_functions = sum(len(r.similar_functions) for r in prevention_results)
        high_similarity_count = sum(
            len([m for m in r.similar_functions if m.overall_similarity >= 0.8]) for r in prevention_results
        )

        # 実装推奨事項の生成
        overall_recommendations = await self.generate_reuse_recommendations(prevention_results)

        # 重要な重複の特定
        critical_duplications = []
        for result in prevention_results:
            if result.has_high_similarity_matches(0.9):
                top_match = result.get_top_match()
                critical_duplications.append(
                    {
                        "source_function": result.query_function.name,
                        "duplicate_function": top_match.target_function.name,
                        "similarity_score": top_match.overall_similarity,
                        "risk_level": "critical",
                    }
                )

        # パフォーマンス計算
        execution_time = max(1, int((time.time() - start_time) * 1000))
        efficiency_score = min(1.0, total_functions / max(execution_time / 1000, 1)) * 100

        return NIHPreventionResponse(
            prevention_results=prevention_results,
            total_functions_analyzed=total_functions,
            total_similar_functions_found=total_similar_functions,
            high_similarity_matches_count=high_similarity_count,
            overall_implementation_recommendations=overall_recommendations,
            critical_duplications=critical_duplications,
            execution_time_ms=execution_time,
            analysis_efficiency_score=efficiency_score,
        )

    async def _generate_and_save_report(self, response: NIHPreventionResponse, request: NIHPreventionRequest) -> None:
        """レポートの生成と保存"""

        try:
            # レポートコンテンツ生成
            report_content = ""
            for result in response.prevention_results:
                result_report = self.report_generator.generate_prevention_report(result, request.report_format)

                report_content += result_report + "\n\n"

            response.report_content = report_content
            response.report_generated = True

            # ファイル保存
            if request.save_report_to_file:
                output_path = request.report_output_path or Path(
                    f"nih_prevention_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.md"
                )

                success = self.report_generator.save_report(report_content, output_path)
                if success:
                    response.report_file_path = output_path
                    self.logger.info("レポート保存完了: %s", output_path)
                else:
                    self.logger.warning("レポート保存失敗: %s", output_path)

        except Exception as e:
            self.logger.exception("レポート生成エラー: %s", e)
            response.report_generated = False
