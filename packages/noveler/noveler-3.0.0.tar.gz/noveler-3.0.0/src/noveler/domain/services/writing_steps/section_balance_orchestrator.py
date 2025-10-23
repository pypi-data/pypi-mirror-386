# File: src/noveler/domain/services/writing_steps/section_balance_orchestrator.py
# Purpose: Coordinate section analysis, optimization, and experience services for balanced episodes.
# Context: Orchestrates domain services; requires careful dependency handling during PLC0415 cleanup.

"""セクションバランス統合オーケストレーター

巨大なSectionBalanceOptimizerServiceを複数のサービスに分離した後の統合層。
各専門サービスを協調させてセクションバランス最適化を実行。
"""

import time
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
from typing import Any

from noveler.domain.interfaces.logger_service_protocol import ILoggerService
from noveler.domain.services.section_analysis.balance_calculator import (
    BalanceCalculator,
    BalanceMetrics,
    BalanceRequirements,
)
from noveler.domain.services.section_analysis.experience_optimizer import (
    ExperienceMetrics,
    ExperienceOptimizationResult,
    ExperienceOptimizer,
)
from noveler.domain.services.section_analysis.optimization_engine import (
    OptimizationEngine,
    OptimizationRequest,
    OptimizationResult,
)
from noveler.domain.services.section_analysis.section_analyzer import SectionAnalysisResult, SectionAnalyzer


@dataclass
class SectionBalanceRequest:
    """セクションバランス最適化リクエスト"""

    plot_data: dict[str, Any]
    phase_structure: dict[str, Any]
    target_episode_length: int = 10000
    optimization_level: str = "moderate"  # basic, moderate, aggressive
    reader_preferences: dict[str, Any] | None = None
    genre_constraints: dict[str, Any] | None = None


@dataclass
class SectionBalanceLogEntry:
    """オーケストレーション過程で発生したメッセージ"""

    level: str
    message: str


@dataclass
class SectionBalanceResult:
    """セクションバランス最適化結果"""

    analysis_result: SectionAnalysisResult
    balance_requirements: BalanceRequirements
    balance_metrics: BalanceMetrics
    optimization_result: OptimizationResult
    experience_result: ExperienceOptimizationResult
    final_sections: list[dict[str, Any]]
    overall_success: bool
    execution_summary: dict[str, Any]
    execution_log: list[SectionBalanceLogEntry]


class SectionBalanceOrchestrator:
    """セクションバランス統合オーケストレーター

    責任:
    - 各専門サービスの協調実行
    - 最適化プロセス全体の管理
    - 結果の統合と品質保証
    - パフォーマンス監視
    """

    def __init__(
        self,
        logger_service: ILoggerService | None = None,
        di_container: object | None = None,
    ) -> None:
        """オーケストレーター初期化

        Args:
            logger_service: ロガーサービス
            di_container: DIコンテナ（依存性注入用）
        """
        self._logger = logger_service
        self._di_container = di_container

        # 各専門サービスの初期化
        self._section_analyzer = SectionAnalyzer(logger_service)
        self._balance_calculator = BalanceCalculator(logger_service)
        self._optimization_engine = OptimizationEngine(logger_service)
        self._experience_optimizer = ExperienceOptimizer(logger_service)

    def _invoke_with_optional_log(
        self, func: Callable[..., Any], *args: Any, log: Callable[[str, str], None] | None = None, **kwargs: Any
    ) -> Any:
        """ログコールバックを受け付けないスタブにも対応して安全に呼び出す"""

        if log is not None:
            try:
                return func(*args, log=log, **kwargs)
            except TypeError as exc:
                if "log" not in str(exc):
                    raise
        return func(*args, **kwargs)

    def execute_section_balance_optimization(self, request: SectionBalanceRequest) -> SectionBalanceResult:
        """セクションバランス最適化の統合実行

        Args:
            request: 最適化リクエスト

        Returns:
            統合最適化結果
        """
        log_entries: list[SectionBalanceLogEntry] = []

        def _log(level: str, message: str) -> None:
            entry = SectionBalanceLogEntry(level=level, message=message)
            log_entries.append(entry)
            if self._logger is not None:
                log_method = getattr(self._logger, level, None)
                if callable(log_method):
                    with suppress(Exception):  # pragma: no cover - logger misconfiguration
                        log_method(message)

        _log("info", "🎭 セクションバランス最適化を開始...")
        _log("info", f"📊 最適化レベル: {request.optimization_level}")
        _log("info", f"📏 目標エピソード長: {request.target_episode_length:,}文字")

        start_time = time.time()

        try:
            # ステップ1: セクション構造分析
            _log("info", "\n🔍 ステップ1: セクション構造分析")
            analysis_result = self._invoke_with_optional_log(
                self._section_analyzer.analyze_section_structure,
                request.plot_data,
                request.phase_structure,
                log=_log,
            )
            _log("info", f"✅ {len(analysis_result.natural_sections)}個のセクションを特定")

            # ステップ2: バランス要件計算
            _log("info", "\n⚖️ ステップ2: バランス要件計算")
            balance_requirements = self._invoke_with_optional_log(
                self._balance_calculator.calculate_balance_requirements,
                analysis_result.natural_sections,
                request.phase_structure,
                request.target_episode_length,
                log=_log,
            )
            _log("info", "✅ バランス要件計算完了")

            # ステップ3: 現在のバランス評価
            _log("info", "\n📊 ステップ3: 現在のバランス評価")
            balance_metrics = self._invoke_with_optional_log(
                self._balance_calculator.assess_current_balance,
                analysis_result.natural_sections,
                balance_requirements,
                log=_log,
            )
            _log("info", f"📈 全体バランススコア: {balance_metrics.overall_balance_score:.2f}")

            # ステップ4: 最適化エンジン実行
            _log("info", "\n🔧 ステップ4: セクション最適化実行")
            optimization_request = self._create_optimization_request(
                analysis_result.natural_sections, balance_requirements, request.optimization_level
            )
            optimization_result = self._invoke_with_optional_log(
                self._optimization_engine.optimize_sections,
                optimization_request,
                log=_log,
            )
            _log("info", f"🚀 最適化スコア: {optimization_result.optimization_score:.2f}")

            # ステップ5: 読者体験最適化
            _log("info", "\n👥 ステップ5: 読者体験最適化")
            experience_result = self._invoke_with_optional_log(
                self._experience_optimizer.optimize_reader_experience,
                optimization_result.optimized_sections,
                request.reader_preferences,
                request.genre_constraints,
                log=_log,
            )
            _log(
                "info",
                f"🎯 体験スコア: {experience_result.experience_metrics.overall_experience_score:.2f}",
            )

            # ステップ6: 最終統合と品質チェック
            _log("info", "\n🔍 ステップ6: 最終統合と品質チェック")
            final_sections = self._integrate_and_validate_results(
                analysis_result, optimization_result, experience_result
            )
            self._validate_final_sections(
                final_sections,
                warn=lambda message: _log("warning", message),
            )

            execution_time = time.time() - start_time

            # 実行サマリー生成
            execution_summary = self._generate_execution_summary(
                analysis_result, balance_metrics, optimization_result, experience_result, execution_time
            )

            # 成功判定
            overall_success = self._evaluate_optimization_success(
                balance_metrics, optimization_result, experience_result
            )

            _log("info", f"\n✅ セクションバランス最適化完了 ({execution_time:.2f}秒)")
            _log("info", f"🎯 最適化成功: {'はい' if overall_success else 'いいえ'}")

            return SectionBalanceResult(
                analysis_result=analysis_result,
                balance_requirements=balance_requirements,
                balance_metrics=balance_metrics,
                optimization_result=optimization_result,
                experience_result=experience_result,
                final_sections=final_sections,
                overall_success=overall_success,
                execution_summary=execution_summary,
                execution_log=list(log_entries),
            )

        except Exception as e:
            _log("error", f"❌ セクションバランス最適化エラー: {e}")
            if self._logger:
                self._logger.exception("SectionBalanceOrchestrator実行エラー")

            # エラー時のフォールバック結果
            return self._create_fallback_result(request, str(e), log_entries)

    def _create_optimization_request(
        self, sections: list[dict[str, Any]], balance_requirements: BalanceRequirements, optimization_level: str
    ) -> OptimizationRequest:
        """最適化リクエスト作成

        Args:
            sections: セクション情報
            balance_requirements: バランス要件
            optimization_level: 最適化レベル

        Returns:
            最適化リクエスト
        """
        # 最適化レベルに応じた目標メトリクス
        target_metrics = {
            "basic": {"balance_score_target": 0.7, "engagement_target": 0.6, "consistency_target": 0.7},
            "moderate": {"balance_score_target": 0.8, "engagement_target": 0.7, "consistency_target": 0.8},
            "aggressive": {"balance_score_target": 0.9, "engagement_target": 0.8, "consistency_target": 0.9},
        }.get(optimization_level, {"balance_score_target": 0.8, "engagement_target": 0.7, "consistency_target": 0.8})

        # 制約条件の設定
        constraints = {
            "max_section_length": max(balance_requirements.length_balance.get("target_lengths", [2000])) * 1.2,
            "min_section_length": min(balance_requirements.length_balance.get("target_lengths", [500])) * 0.8,
            "target_total_length": balance_requirements.length_balance.get("total_target", 10000),
            "preserve_story_structure": True,
        }

        return OptimizationRequest(
            sections=sections,
            balance_requirements={
                "length_balance": balance_requirements.length_balance,
                "intensity_balance": balance_requirements.intensity_balance,
                "pacing_balance": balance_requirements.pacing_balance,
                "content_balance": balance_requirements.content_balance,
            },
            target_metrics=target_metrics,
            constraints=constraints,
        )

    def _integrate_and_validate_results(
        self,
        analysis_result: SectionAnalysisResult,
        optimization_result: OptimizationResult,
        experience_result: ExperienceOptimizationResult,
    ) -> list[dict[str, Any]]:
        """結果統合と検証

        Args:
            analysis_result: 分析結果
            optimization_result: 最適化結果
            experience_result: 体験最適化結果

        Returns:
            統合された最終セクション
        """
        final_sections = []

        # 各結果を統合
        base_sections = experience_result.optimized_sections

        for i, section in enumerate(base_sections):
            integrated_section = section.copy()

            # 分析結果からの情報統合
            if i < len(analysis_result.narrative_weights):
                integrated_section["narrative_weight"] = analysis_result.narrative_weights[i]

            if i < len(analysis_result.emotional_intensities):
                integrated_section["emotional_intensity"] = analysis_result.emotional_intensities[i]

            if i < len(analysis_result.pacing_requirements):
                integrated_section["pacing_requirements"] = analysis_result.pacing_requirements[i]

            # 最適化結果からの追加情報
            if optimization_result.warnings:
                integrated_section["optimization_warnings"] = [
                    warning for warning in optimization_result.warnings if f"セクション{i + 1}" in warning
                ]

            # 品質スコアの統合
            integrated_section["quality_metrics"] = {
                "analysis_completeness": 1.0 if analysis_result.natural_sections else 0.5,
                "optimization_score": optimization_result.optimization_score,
                "experience_score": experience_result.experience_metrics.overall_experience_score,
                "integrated_score": self._calculate_integrated_quality_score(
                    optimization_result.optimization_score,
                    experience_result.experience_metrics.overall_experience_score,
                ),
            }

            final_sections.append(integrated_section)

        return final_sections

    def _generate_execution_summary(
        self,
        analysis_result: SectionAnalysisResult,
        balance_metrics: BalanceMetrics,
        optimization_result: OptimizationResult,
        experience_result: ExperienceOptimizationResult,
        execution_time: float,
    ) -> dict[str, Any]:
        """実行サマリー生成

        Args:
            analysis_result: 分析結果
            balance_metrics: バランスメトリクス
            optimization_result: 最適化結果
            experience_result: 体験最適化結果
            execution_time: 実行時間

        Returns:
            実行サマリー
        """
        return {
            "execution_time": execution_time,
            "sections_processed": len(analysis_result.natural_sections),
            "improvements_identified": len(optimization_result.improvements),
            "warnings_generated": len(optimization_result.warnings),
            "experience_issues": len(experience_result.experience_issues),
            "overall_balance_score": balance_metrics.overall_balance_score,
            "optimization_score": optimization_result.optimization_score,
            "experience_score": experience_result.experience_metrics.overall_experience_score,
            "recommendations_count": len(experience_result.recommendations),
            "performance_metrics": {
                "sections_per_second": len(analysis_result.natural_sections) / execution_time
                if execution_time > 0
                else 0,
                "optimization_efficiency": optimization_result.optimization_score / execution_time
                if execution_time > 0
                else 0,
            },
        }

    def _evaluate_optimization_success(
        self,
        balance_metrics: BalanceMetrics,
        optimization_result: OptimizationResult,
        experience_result: ExperienceOptimizationResult,
    ) -> bool:
        """最適化成功判定

        Args:
            balance_metrics: バランスメトリクス
            optimization_result: 最適化結果
            experience_result: 体験最適化結果

        Returns:
            最適化成功フラグ
        """
        # 成功基準の定義
        success_criteria = {
            "min_balance_score": 0.7,
            "min_optimization_score": 0.7,
            "min_experience_score": 0.6,
            "max_critical_warnings": 0,
            "max_experience_issues": 2,
        }

        # 各基準をチェック
        checks = {
            "balance_score": balance_metrics.overall_balance_score >= success_criteria["min_balance_score"],
            "optimization_score": optimization_result.optimization_score >= success_criteria["min_optimization_score"],
            "experience_score": experience_result.experience_metrics.overall_experience_score
            >= success_criteria["min_experience_score"],
            "critical_warnings": len(optimization_result.warnings) <= success_criteria["max_critical_warnings"],
            "experience_issues": len(experience_result.experience_issues) <= success_criteria["max_experience_issues"],
        }

        # すべての基準を満たした場合に成功
        return all(checks.values())

    def _create_fallback_result(
        self,
        request: SectionBalanceRequest,
        error_message: str,
        log_entries: list[SectionBalanceLogEntry],
    ) -> SectionBalanceResult:
        """エラー時のフォールバック結果作成

        Args:
            request: 元のリクエスト
            error_message: エラーメッセージ
            log_entries: これまでに蓄積したログエントリ

        Returns:
            フォールバック結果
        """
        # エラー状態の結果を作成
        fallback_analysis = SectionAnalysisResult(
            structure_assessment={"error": error_message},
            natural_sections=[],
            section_characteristics=[],
            narrative_weights=[],
            emotional_intensities=[],
            pacing_requirements=[],
            engagement_levels=[],
        )

        fallback_requirements = BalanceRequirements(
            length_balance={},
            intensity_balance={},
            pacing_balance={},
            content_balance={},
            reader_experience_requirements={},
        )

        fallback_metrics = BalanceMetrics(
            overall_balance_score=0.0,
            length_distribution=[],
            intensity_curve=[],
            pacing_variation=[],
            content_ratios=[],
            engagement_consistency=0.0,
        )

        fallback_optimization = OptimizationResult(
            optimized_sections=[],
            optimization_score=0.0,
            improvements=[],
            warnings=[f"最適化実行エラー: {error_message}"],
            execution_time=0.0,
        )

        fallback_experience_metrics = ExperienceMetrics(
            engagement_levels=[],
            satisfaction_points=[],
            cognitive_load=[],
            emotional_journey=[],
            immersion_consistency=0.0,
            overall_experience_score=0.0,
        )

        fallback_experience = ExperienceOptimizationResult(
            optimized_sections=[],
            experience_metrics=fallback_experience_metrics,
            recommendations=[],
            experience_issues=[f"体験最適化実行エラー: {error_message}"],
            improvement_score=0.0,
        )

        return SectionBalanceResult(
            analysis_result=fallback_analysis,
            balance_requirements=fallback_requirements,
            balance_metrics=fallback_metrics,
            optimization_result=fallback_optimization,
            experience_result=fallback_experience,
            final_sections=[],
            overall_success=False,
            execution_summary={
                "execution_time": 0.0,
                "error": error_message,
                "fallback_result": True,
                "request_info": {
                    "target_length": request.target_episode_length,
                    "optimization_level": request.optimization_level,
                },
            },
            execution_log=list(log_entries),
        )

    def _calculate_integrated_quality_score(self, optimization_score: float, experience_score: float) -> float:
        """統合品質スコア計算

        Args:
            optimization_score: 最適化スコア
            experience_score: 体験スコア

        Returns:
            統合品質スコア
        """
        # 重み付き平均で統合スコアを計算
        return optimization_score * 0.6 + experience_score * 0.4

    def _validate_final_sections(
        self,
        sections: list[dict[str, Any]],
        warn: Callable[[str], None] | None = None,
    ) -> None:
        """最終セクションの検証

        Args:
            sections: 検証対象のセクション
            warn: 警告メッセージを通知するコールバック

        Raises:
            ValueError: 検証エラー時
        """
        if not sections:
            msg = "最終セクションが空です"
            raise ValueError(msg)

        # 各セクションの必須フィールドチェック
        required_fields = ["id", "title", "estimated_length"]

        for i, section in enumerate(sections):
            for field in required_fields:
                if field not in section:
                    message = f"⚠️ セクション{i + 1}に必須フィールド'{field}'がありません"
                    if warn:
                        warn(message)

            # 長さの妥当性チェック
            length = section.get("estimated_length", 0)
            if length <= 0:
                message = f"⚠️ セクション{i + 1}の推定長が無効です: {length}"
                if warn:
                    warn(message)

    # 後方互換性のためのレガシーメソッド（元の巨大ファイルからの移行用）
    def optimize_section_balance(
        self,
        plot_data: dict[str, Any],
        phase_structure: dict[str, Any],
        target_episode_length: int = 10000,
        **kwargs: object,
    ) -> dict[str, Any]:
        """レガシー互換メソッド

        元のSectionBalanceOptimizerService.optimize_section_balanceとの互換性維持
        """
        request = SectionBalanceRequest(
            plot_data=plot_data,
            phase_structure=phase_structure,
            target_episode_length=target_episode_length,
            optimization_level=kwargs.get("optimization_level", "moderate"),
            reader_preferences=kwargs.get("reader_preferences"),
            genre_constraints=kwargs.get("genre_constraints"),
        )

        result = self.execute_section_balance_optimization(request)

        # レガシー形式での結果返却
        return {
            "optimized_sections": result.final_sections,
            "balance_score": result.balance_metrics.overall_balance_score,
            "optimization_success": result.overall_success,
            "execution_summary": result.execution_summary,
            "warnings": result.optimization_result.warnings,
            "recommendations": result.experience_result.recommendations,
        }
