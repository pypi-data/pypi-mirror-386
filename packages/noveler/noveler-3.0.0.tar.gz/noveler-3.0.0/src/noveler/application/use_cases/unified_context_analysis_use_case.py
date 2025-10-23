#!/usr/bin/env python3

"""Application.use_cases.unified_context_analysis_use_case
Where: Application use case running unified context analysis.
What: Aggregates story data, performs analysis, and produces insights for downstream tools.
Why: Keeps context analysis accessible without duplicating analytical orchestration.
"""

from __future__ import annotations



from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psutil
import yaml

from noveler.application.base.abstract_use_case import AbstractUseCase
from noveler.domain.entities.holistic_analysis_result import HolisticAnalysisResult
from noveler.domain.entities.unified_analysis_context import ProjectContext, UnifiedAnalysisContext
from noveler.domain.interfaces.console_service_protocol import IConsoleService

# 実行時に使用するため、TYPE_CHECKINGブロック外でインポート
from noveler.domain.interfaces.logger_service_protocol import ILoggerService
from noveler.domain.interfaces.path_service_protocol import IPathService
from noveler.domain.services.unified_context_analyzer import UnifiedContextAnalyzer
from noveler.domain.value_objects.analysis_scope import AnalysisScope
from noveler.infrastructure.adapters.path_service_adapter import create_path_service
from noveler.infrastructure.caching.file_cache_service import get_file_cache_service
from noveler.infrastructure.unit_of_work import IUnitOfWork

# DDD準拠: Infrastructure層への直接依存を除去（遅延初期化で対応）
# from noveler.infrastructure.factories.configuration_service_factory import get_configuration_manager


@dataclass
class UnifiedAnalysisRequest:
    """統合分析リクエスト"""

    project_name: str
    episode_number: int
    manuscript_path: Path | None = None
    a31_yaml_path: Path | None = None
    include_cross_phase_analysis: bool = True
    include_comprehensive_improvements: bool = True
    analysis_scope: AnalysisScope = AnalysisScope.COMPREHENSIVE
    performance_budget_seconds: float = 30.0
    memory_budget_mb: float = 500.0

    def validate(self) -> dict[str, Any]:
        """リクエスト妥当性検証

        Returns:
            Dict[str, Any]: 検証結果
        """
        issues = []
        warnings = []

        if not self.project_name:
            issues.append("プロジェクト名が指定されていません")

        if self.episode_number <= 0:
            issues.append("エピソード番号は1以上である必要があります")

        if self.manuscript_path and not self.manuscript_path.exists():
            issues.append(f"原稿ファイルが見つかりません: {self.manuscript_path}")

        if self.a31_yaml_path and not self.a31_yaml_path.exists():
            issues.append(f"A31チェックリストファイルが見つかりません: {self.a31_yaml_path}")

        if self.performance_budget_seconds > 60.0:
            warnings.append("パフォーマンス予算が60秒を超えています")

        return {"is_valid": len(issues) == 0, "issues": issues, "warnings": warnings}


@dataclass
class UnifiedAnalysisResponse:
    """統合分析レスポンス"""

    success: bool
    analysis_result: HolisticAnalysisResult | None = None
    error_message: str | None = None
    execution_time_seconds: float = 0.0
    memory_usage_mb: float = 0.0
    performance_metrics: dict[str, Any] = field(default_factory=dict)

    # 詳細統計
    items_analyzed: int = 0
    phases_processed: int = 0
    insights_generated: int = 0
    improvements_suggested: int = 0

    def get_summary(self) -> dict[str, Any]:
        """結果サマリーの取得

        Returns:
            Dict[str, Any]: サマリー情報
        """
        if not self.success or not self.analysis_result:
            return {"status": "failed", "error": self.error_message, "execution_time": self.execution_time_seconds}

        return {
            "status": "success",
            "overall_score": self.analysis_result.overall_score.value,
            "grade": self.analysis_result.overall_score.get_grade(),
            "items_analyzed": self.items_analyzed,
            "phases_processed": self.phases_processed,
            "insights_generated": self.insights_generated,
            "improvements_suggested": self.improvements_suggested,
            "execution_time": self.execution_time_seconds,
            "memory_usage": self.memory_usage_mb,
            "context_preservation_rate": self.analysis_result.context_preservation_metrics.preservation_rate,
        }


class UnifiedContextAnalysisUseCase(AbstractUseCase[UnifiedAnalysisRequest, dict]):
    """統合コンテキスト分析ユースケース

    統合コンテキスト分析システムのメインエントリポイント。
    ドメインサービスを協調させて包括的な品質分析を実行。
    """

    def __init__(self,
        logger_service: ILoggerService | None = None,
        unit_of_work: IUnitOfWork | None = None,
        console_service: IConsoleService | None = None,
        path_service: IPathService | None = None,
        **kwargs) -> None:
        """初期化

        Args:
            logger_service: ロガーサービス（DI注入）
            unit_of_work: 作業単位（DI注入）
            console_service: コンソールサービス（DI注入）
            path_service: パスサービス（DI注入）
        """
        # 基底クラス初期化（共通サービス）
        analyzer_override = kwargs.pop("unified_analyzer", None)
        context_builder_override = kwargs.pop("context_builder", None)
        result_formatter_override = kwargs.pop("result_formatter", None)
        memory_tracker_override = kwargs.pop("memory_tracker", None)

        super().__init__(console_service=console_service, path_service=path_service, **kwargs)
        # B20準拠: 標準DIサービス
        self._logger_service = logger_service
        self._unit_of_work = unit_of_work

        # ドメインサービスの遅延初期化
        self.unified_analyzer = analyzer_override or UnifiedContextAnalyzer()
        self.context_builder = context_builder_override or UnifiedContextBuilder(
            logger_service=logger_service,
            unit_of_work=unit_of_work,
        )
        self.result_formatter = result_formatter_override or ResultFormatter(
            logger_service=logger_service,
            unit_of_work=unit_of_work,
        )

        # パフォーマンス監視
        self.execution_start_time: datetime | None = None
        self.memory_tracker = memory_tracker_override or MemoryTracker(
            logger_service=logger_service,
            unit_of_work=unit_of_work,
        )

    async def execute(self, request: UnifiedAnalysisRequest) -> UnifiedAnalysisResponse:
        """統合分析の実行

        Args:
            request: 分析リクエスト

        Returns:
            UnifiedAnalysisResponse: 分析結果
        """
        self.execution_start_time = datetime.now(timezone.utc)
        tracker = self.memory_tracker
        if tracker:
            tracker.start_tracking()

        try:
            # リクエスト妥当性検証
            validation_result = request.validate()
            if not validation_result["is_valid"]:
                return UnifiedAnalysisResponse(
                    success=False,
                    error_message=f"リクエスト検証エラー: {', '.join(validation_result['issues'])}",
                    execution_time_seconds=self._get_execution_time(),
                )

            # コンテキスト構築
            self.logger.info("統合分析開始: %s エピソード%s", (request.project_name), (request.episode_number))

            context = await self.context_builder.build_context(request)
            if not context:
                return UnifiedAnalysisResponse(
                    success=False,
                    error_message="分析コンテキストの構築に失敗しました",
                    execution_time_seconds=self._get_execution_time(),
                )

            # コンテキスト整合性検証
            integrity_result = context.validate_context_integrity()
            if not integrity_result["is_valid"]:
                self.logger.warning(f"コンテキスト整合性の問題: {integrity_result['issues']}")

            # パフォーマンス制約チェック
            if self._should_abort_for_performance(request):
                return UnifiedAnalysisResponse(
                    success=False,
                    error_message="パフォーマンス制約により分析を中止しました",
                    execution_time_seconds=self._get_execution_time(),
                )

            # 統合分析実行
            self.logger.info("統合分析を実行中...")
            analysis_result = await self.unified_analyzer.analyze_holistically(context)

            # 結果の後処理
            formatted_result = await self.result_formatter.format_result(analysis_result, request)

            # パフォーマンスメトリクス収集
            performance_metrics = self._collect_performance_metrics(context, analysis_result)

            execution_time = self._get_execution_time()
            memory_usage = tracker.get_peak_usage_mb() if tracker else 0.0

            self.logger.info(
                f"統合分析完了: {execution_time:.2f}秒, "
                f"メモリ使用量: {memory_usage:.1f}MB, "
                f"総合スコア: {analysis_result.overall_score.value:.1f}"
            )

            return UnifiedAnalysisResponse(
                success=True,
                analysis_result=formatted_result,
                execution_time_seconds=execution_time,
                memory_usage_mb=memory_usage,
                performance_metrics=performance_metrics,
                items_analyzed=analysis_result.total_items_analyzed,
                phases_processed=len(analysis_result.phase_analyses),
                insights_generated=len(analysis_result.cross_phase_insights),
                improvements_suggested=len(analysis_result.comprehensive_improvements),
            )

        except Exception as e:
            self.logger.error(f"統合分析中にエラーが発生: {e!s}", exc_info=True)
            return UnifiedAnalysisResponse(
                success=False,
                error_message=f"分析実行エラー: {e!s}",
                execution_time_seconds=self._get_execution_time(),
                memory_usage_mb=tracker.get_peak_usage_mb() if tracker else 0.0,
            )

        finally:
            if tracker:
                tracker.stop_tracking()

    async def execute_with_progress_callback(
        self, request: UnifiedAnalysisRequest, progress_callback: callable | None = None
    ) -> UnifiedAnalysisResponse:
        """進捗コールバック付き実行

        Args:
            request: 分析リクエスト
            progress_callback: 進捗通知コールバック

        Returns:
            UnifiedAnalysisResponse: 分析結果
        """
        if progress_callback:
            progress_callback("分析準備中...", 0.0)

        # 基本実行をラップしてプログレス通知
        response = await self.execute(request)

        if progress_callback:
            if response.success:
                progress_callback("分析完了", 1.0)
            else:
                progress_callback(f"分析失敗: {response.error_message}", -1.0)

        return response

    def _get_execution_time(self) -> float:
        """実行時間の取得"""
        if self.execution_start_time:
            return (datetime.now(timezone.utc) - self.execution_start_time).total_seconds()
        return 0.0

    def _should_abort_for_performance(self, request: UnifiedAnalysisRequest) -> bool:
        """パフォーマンス制約による中止判定"""
        current_time = self._get_execution_time()
        current_memory = self.memory_tracker.get_current_usage_mb()

        return (
            current_time > request.performance_budget_seconds * 0.8 or current_memory > request.memory_budget_mb * 0.8
        )

    def _collect_performance_metrics(
        self, context: UnifiedAnalysisContext, result: HolisticAnalysisResult
    ) -> dict[str, Any]:
        """パフォーマンスメトリクス収集"""
        return {
            "context_build_time": context.build_duration.total_seconds() if hasattr(context, "build_duration") else 0.0,
            "analysis_time": result.execution_time.total_seconds(),
            "items_per_second": result.total_items_analyzed / result.execution_time.total_seconds(),
            "memory_efficiency": self.memory_tracker.get_peak_usage_mb() / context.get_total_items_count(),
            "context_preservation_efficiency": result.context_preservation_metrics.preservation_rate / 100.0,
        }


class UnifiedContextBuilder:
    """統合コンテキストビルダー

    分析に必要なコンテキスト情報の構築を担当。
    """

    def __init__(self,
        logger_service: ILoggerService | None = None,
        unit_of_work: IUnitOfWork | None = None,
        **kwargs) -> None:
        """初期化"""
        # DDD準拠: Infrastructure依存を避ける
        if logger_service:
            self.logger = logger_service
        else:
            # 遅延importで統一ロガーへ委譲（フォールバックなし）
            from noveler.infrastructure.logging.unified_logger import get_logger  # type: ignore
            self.logger = get_logger(__name__)

    async def build_context(self, request: UnifiedAnalysisRequest) -> UnifiedAnalysisContext | None:
        """コンテキスト構築

        Args:
            request: 分析リクエスト

        Returns:
            Optional[UnifiedAnalysisContext]: 構築されたコンテキスト
        """
        try:
            # 原稿内容の読み込み
            manuscript_content = await self._load_manuscript_content(request)
            if not manuscript_content:
                self.logger.error("原稿内容の読み込みに失敗")
                return None

            # A31チェックリストの読み込み
            a31_content = await self._load_a31_checklist(request)
            if not a31_content:
                self.logger.error("A31チェックリストの読み込みに失敗")
                return None

            # プロジェクトコンテキストの構築
            project_context = await self._build_project_context(request)

            # 統合コンテキスト生成
            context = UnifiedAnalysisContext.from_a31_yaml(
                a31_yaml_content=a31_content,
                manuscript_content=manuscript_content,
                project_context=project_context,
                preservation_scope=request.analysis_scope,
            )

            self.logger.info("コンテキスト構築完了: %s項目", (context.get_total_items_count()))
            return context

        except Exception as e:
            self.logger.exception("コンテキスト構築エラー: %s", e)
            return None

    async def _load_manuscript_content(self, request: UnifiedAnalysisRequest) -> str | None:
        """原稿内容の読み込み"""
        if request.manuscript_path and request.manuscript_path.exists():
            try:
                return request.manuscript_path.read_text(encoding="utf-8")
            except Exception as e:
                self.logger.exception("原稿読み込みエラー: %s", e)
                return None

        # デフォルトパス推定
        default_path = self._estimate_manuscript_path(request)
        if default_path and default_path.exists():
            try:
                return default_path.read_text(encoding="utf-8")
            except Exception as e:
                self.logger.exception("デフォルト原稿読み込みエラー: %s", e)
                return None

        return None

    async def _load_a31_checklist(self, request: UnifiedAnalysisRequest) -> dict[str, Any] | None:
        """A31チェックリストの読み込み"""
        if request.a31_yaml_path and request.a31_yaml_path.exists():
            try:
                with request.a31_yaml_path.open(encoding="utf-8") as f:
                    return yaml.safe_load(f)
            except Exception as e:
                self.logger.exception("A31チェックリスト読み込みエラー: %s", e)
                return None

        # デフォルトパス推定
        default_path = self._estimate_a31_path(request)
        if default_path and default_path.exists():
            try:
                with default_path.open(encoding="utf-8") as f:
                    return yaml.safe_load(f)
            except Exception as e:
                self.logger.exception("デフォルトA31読み込みエラー: %s", e)
                return None

        return None

    async def _build_project_context(self, request: UnifiedAnalysisRequest) -> ProjectContext:
        """プロジェクトコンテキストの構築"""
        # 設定から基本パスを取得
        # DDD準拠: AbstractUseCaseのconfig_serviceを使用（Infrastructure依存排除）
        config_manager = self.config_service
        project_root_str = config_manager.get_configuration().get_platform_path("default_project_root")
        project_root = (
            Path(project_root_str) if project_root_str else Path("/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説")
        )
        manuscript_path = self._estimate_manuscript_path(request) or Path("dummy.md")

        return ProjectContext(
            project_name=request.project_name,
            project_root=project_root,
            episode_number=request.episode_number,
            manuscript_path=manuscript_path,
        )

    def _estimate_manuscript_path(self, request: UnifiedAnalysisRequest) -> Path | None:
        """原稿パスの推定（PathService優先、旧方式フォールバック）"""
        try:
            # 設定からプロジェクトルートを構築
            config_manager = self.config_service
            base_path_str = config_manager.get_configuration().get_platform_path("default_project_root")
            base_path = Path(base_path_str) if base_path_str else Path("/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説")
            project_root = base_path / request.project_name

            # PathServiceで統一パスを取得
            path_service = self.get_path_service(project_root)
            candidate = path_service.get_manuscript_path(request.episode_number)
            if candidate.exists():
                return candidate

            # フォールバック: 旧data/manuscripts配下を探索
            project_path = project_root / "data" / "manuscripts"
            if project_path.exists():
                episode_str = f"{request.episode_number:03d}"
                pattern = f"第{episode_str}話_*.md"
                cache_service = get_file_cache_service()
                matching_files = cache_service.get_matching_files(project_path, pattern, ttl_seconds=300)
                if matching_files:
                    return matching_files[0]
        except Exception:
            return None
        return None

    def _estimate_a31_path(self, request: UnifiedAnalysisRequest) -> Path | None:
        """A31チェックリストパスの推定"""
        # DDD準拠: AbstractUseCaseのconfig_serviceを使用（Infrastructure依存排除）
        config_manager = self.config_service
        base_path_str = config_manager.get_configuration().get_platform_path("default_project_root")
        base_path = Path(base_path_str) if base_path_str else Path("/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説")
        project_root = base_path / request.project_name
        # DDD準拠: ApplicationからInfrastructureのIPathService経由でパスを取得

        path_service = create_path_service(project_root)
        a31_path = path_service.get_quality_data_dir() / "a31_checklists"

        episode_str = f"{request.episode_number:03d}"
        pattern = f"A31_チェックリスト_第{episode_str}話_*.yaml"

        if a31_path.exists():
            # 高速化: ファイルキャッシュサービス使用でglob操作を最適化
            cache_service = get_file_cache_service()
            matching_files = cache_service.get_matching_files(
                a31_path, pattern, ttl_seconds=300
            )
            if matching_files:
                return matching_files[0]

        return None


class ResultFormatter:
    """結果フォーマッター

    分析結果の表示形式を整理・最適化。
    """

    def __init__(self,
        logger_service: ILoggerService | None = None,
        unit_of_work: IUnitOfWork | None = None,
        **kwargs) -> None:
        """初期化"""
        self._logger_service = logger_service
        self._unit_of_work = unit_of_work

    async def format_result(
        self, result: HolisticAnalysisResult, request: UnifiedAnalysisRequest
    ) -> HolisticAnalysisResult:
        """結果フォーマット

        Args:
            result: 分析結果
            request: 元のリクエスト

        Returns:
            HolisticAnalysisResult: フォーマット済み結果
        """
        # 基本的には元の結果をそのまま返す
        # 将来的に表示最適化や情報整理を実装
        return result


class MemoryTracker:
    """メモリ使用量トラッカー"""

    def __init__(self,
        logger_service: ILoggerService | None = None,
        unit_of_work: IUnitOfWork | None = None,
        **kwargs) -> None:
        """初期化"""
        self._logger_service = logger_service
        self._unit_of_work = unit_of_work
        self.peak_usage_mb = 0.0
        self.is_tracking = False

    def start_tracking(self) -> None:
        """トラッキング開始"""
        self.is_tracking = True
        self.peak_usage_mb = self.get_current_usage_mb()

    def stop_tracking(self) -> None:
        """トラッキング停止"""
        self.is_tracking = False

    def get_current_usage_mb(self) -> float:
        """現在のメモリ使用量取得"""
        try:

            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0

    def get_peak_usage_mb(self) -> float:
        """ピークメモリ使用量取得"""
        if self.is_tracking:
            current = self.get_current_usage_mb()
            self.peak_usage_mb = max(self.peak_usage_mb, current)
        return self.peak_usage_mb
