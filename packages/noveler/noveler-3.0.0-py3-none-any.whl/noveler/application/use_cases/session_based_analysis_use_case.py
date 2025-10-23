#!/usr/bin/env python3
"""セッションベース分析ユースケース

Claude Codeセッション内でA31重点項目分析を実行し、
結果をリアルタイムでチェックリストに統合するユースケース。
"""

import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from noveler.domain.entities.a31_priority_item import A31PriorityItem
from noveler.domain.entities.session_analysis_result import SessionAnalysisResult
from noveler.domain.services.a31_priority_extractor_service import (
    A31PriorityExtractorService,
    PriorityExtractionCriteria,
)
from noveler.domain.services.in_session_claude_analyzer import AnalysisContext, InSessionClaudeAnalyzer
from noveler.domain.value_objects.a31_checklist_data import A31ChecklistData


@dataclass(frozen=True)
class SessionAnalysisRequest:
    """セッション分析リクエスト"""

    checklist_file_path: str
    manuscript_file_path: str
    episode_number: int
    project_name: str = "Fランク魔法使いはDEBUGログを読む"
    max_priority_items: int = 20
    extraction_strategy: str = "hybrid"
    focus_categories: list[str] | None = None
    enable_parallel_analysis: bool = True
    enable_real_time_integration: bool = True
    analysis_timeout: float = 10.0

    def __post_init__(self) -> None:
        """リクエスト妥当性検証"""
        if self.episode_number <= 0:
            msg = "エピソード番号は正の値である必要があります"
            raise ValueError(msg)

        if not Path(self.checklist_file_path).exists():
            msg = f"チェックリストファイルが見つかりません: {self.checklist_file_path}"
            raise ValueError(msg)

        if not Path(self.manuscript_file_path).exists():
            msg = f"原稿ファイルが見つかりません: {self.manuscript_file_path}"
            raise ValueError(msg)


@dataclass
class SessionAnalysisResponse:
    """セッション分析レスポンス"""

    success: bool
    analysis_result: SessionAnalysisResult | None
    execution_time: float
    extracted_items_count: int = 0
    analyzed_items_count: int = 0
    integrated_results_count: int = 0
    error_message: str | None = None
    performance_metrics: dict[str, Any] | None = None

    def get_completion_status(self) -> str:
        """完了ステータス取得"""
        if not self.success:
            return "FAILED"

        if not self.analysis_result:
            return "NO_RESULTS"

        completion_rate = self.analysis_result.get_completion_rate()
        if completion_rate >= 1.0:
            return "COMPLETED"
        if completion_rate >= 0.8:
            return "MOSTLY_COMPLETED"
        if completion_rate >= 0.5:
            return "PARTIALLY_COMPLETED"
        return "BARELY_STARTED"

    def get_quality_assessment(self) -> str:
        """品質評価取得"""
        if not self.analysis_result:
            return "UNKNOWN"

        avg_score = self.analysis_result.get_average_analysis_score()
        if avg_score >= 8.0:
            return "EXCELLENT"
        if avg_score >= 7.0:
            return "GOOD"
        if avg_score >= 6.0:
            return "FAIR"
        if avg_score >= 5.0:
            return "POOR"
        return "CRITICAL"


class SessionBasedAnalysisUseCase:
    """セッションベース分析ユースケース

    Claude Codeセッション環境において、A31重点項目分析から
    結果統合までの完全自動化されたワークフローを提供する。
    """

    def __init__(
        self,
        priority_extractor: A31PriorityExtractorService | None = None,
        session_analyzer: InSessionClaudeAnalyzer | None = None,
        logger_service=None,
        unit_of_work=None,
        **kwargs
    ) -> None:
        """ユースケース初期化

        Args:
            priority_extractor: A31重点項目抽出サービス
            session_analyzer: セッション内Claude分析エンジン
            logger_service: ロガーサービス
            unit_of_work: Unit of Work
            **kwargs: AbstractUseCaseの引数
        """
        super().__init__(**kwargs)
        self._priority_extractor = priority_extractor
        self._session_analyzer = session_analyzer
        self._logger_service = logger_service
        self._unit_of_work = unit_of_work

        # 実行統計
        self._execution_history: list[SessionAnalysisResponse] = []

    async def execute(
        self,
        request: SessionAnalysisRequest,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> SessionAnalysisResponse:
        """セッションベース分析実行

        Args:
            request: 分析リクエスト
            progress_callback: プログレス表示コールバック

        Returns:
            SessionAnalysisResponse: 分析結果レスポンス
        """
        start_time = time.time()

        try:
            # Phase 1: A31チェックリスト読み込み
            if progress_callback:
                progress_callback("A31チェックリスト読み込み中...", 0, 5)

            checklist_data: dict[str, Any] = self._load_checklist_data(request.checklist_file_path)

            # Phase 2: 重点項目抽出
            if progress_callback:
                progress_callback("重点項目抽出中...", 1, 5)

            priority_items = self._extract_priority_items(checklist_data, request)

            # Phase 3: 原稿コンテキスト準備
            if progress_callback:
                progress_callback("原稿分析コンテキスト準備中...", 2, 5)

            analysis_context = self._prepare_analysis_context(request.manuscript_file_path, request)

            # Phase 4: セッション内分析実行
            if progress_callback:
                progress_callback("Claude分析実行中...", 3, 5)

            session_result = await self._session_analyzer.analyze_priority_items(
                priority_items=priority_items,
                analysis_context=analysis_context,
                progress_callback=self._create_nested_progress_callback(progress_callback),
            )

            # Phase 5: 結果統合（将来実装）
            if progress_callback:
                progress_callback("結果統合処理中...", 4, 5)

            integration_count = 0
            if request.enable_real_time_integration:
                integration_count = self._integrate_analysis_results(session_result, request)

            # Phase 6: 完了処理
            if progress_callback:
                progress_callback("分析完了", 5, 5)

            execution_time = time.time() - start_time

            # レスポンス構築
            response = SessionAnalysisResponse(
                success=True,
                analysis_result=session_result,
                execution_time=execution_time,
                extracted_items_count=len(priority_items),
                analyzed_items_count=len(session_result.item_results),
                integrated_results_count=integration_count,
                performance_metrics=self._generate_performance_metrics(session_result, execution_time),
            )

            # 実行履歴記録
            self._execution_history.append(response)

            return response

        except Exception as e:
            execution_time = time.time() - start_time

            error_response = SessionAnalysisResponse(
                success=False, analysis_result=None, execution_time=execution_time, error_message=str(e)
            )

            self._execution_history.append(error_response)
            return error_response

    def _load_checklist_data(self, checklist_file_path: str) -> A31ChecklistData:
        """A31チェックリストデータ読み込み"""
        from pathlib import Path

        import yaml

        with Path(checklist_file_path).open(encoding="utf-8") as f:
            raw_data: dict[str, Any] = yaml.safe_load(f)

        checklist_data: dict[str, Any] = A31ChecklistData.from_yaml_data(raw_data)

        # パステンプレート変数を実際のパスに解決
        checklist_file_path_obj = Path(checklist_file_path)
        project_root = checklist_file_path_obj.parent.parent.parent  # A31チェックリストから3階層上がプロジェクトルート

        return checklist_data.resolve_path_templates(project_root)

    def _extract_priority_items(
        self,
        checklist_data: A31ChecklistData,
        request: SessionAnalysisRequest,
    ) -> list[A31PriorityItem]:
        """重点項目抽出（具体的改善提案付き）"""
        from noveler.domain.services.a31_priority_extractor_service import ExtractionStrategy
        from noveler.domain.value_objects.a31_evaluation_category import A31EvaluationCategory

        # focus_categoriesを適切な型に変換
        focus_categories = None
        if request.focus_categories:
            focus_categories = []
            category_mapping = {
                "content_balance": A31EvaluationCategory.CONTENT_BALANCE,
                "sensory_description": A31EvaluationCategory.SENSORY_DESCRIPTION,
                "basic_writing_style": A31EvaluationCategory.BASIC_WRITING_STYLE,
                "character_consistency": A31EvaluationCategory.CHARACTER_CONSISTENCY,
                "format_check": A31EvaluationCategory.FORMAT_CHECK,
                "style_consistency": A31EvaluationCategory.STYLE_CONSISTENCY,
            }
            for category_str in request.focus_categories:
                if category_str in category_mapping:
                    focus_categories.append(category_mapping[category_str])

        # A31PriorityExtractorServiceを使用して高品質な抽出を実行
        criteria = PriorityExtractionCriteria(
            max_items=request.max_priority_items,
            strategy=ExtractionStrategy.HYBRID,  # ハイブリッド戦略で最適な項目を抽出
            focus_categories=focus_categories,
            priority_threshold=0.6,  # 閾値を下げて抽出されやすくする
        )

        priority_items = self._priority_extractor.extract_priority_items(checklist_data, criteria)

        # 具体的改善提案を生成してメタデータに保存
        with Path(request.manuscript_file_path).open(encoding="utf-8") as f:
            manuscript_content = f.read()

        episode_context = {"episode_number": request.episode_number, "project_name": request.project_name}

        concrete_suggestions = self._priority_extractor.generate_concrete_improvement_suggestions(
            priority_items=priority_items, manuscript_content=manuscript_content, episode_context=episode_context
        )

        # 各重点項目に具体的改善提案を関連付け
        for item in priority_items:
            item_id = item.item_id.value
            if item_id in concrete_suggestions:
                # メタデータとして具体的提案を保存
                item._metadata = getattr(item, "_metadata", {})
                item._metadata["concrete_suggestions"] = concrete_suggestions[item_id]

        return priority_items

    def _is_claude_analysis_suitable(self, content: str, item_type: str) -> bool:
        """Claude分析適性判定（A31チェックリスト実構造対応）"""
        # A31チェックリスト実構造に基づく内容キーワード
        suitable_content_keywords = [
            # 基本チェック
            "確認",
            "チェック",
            "検証",
            "調整",
            "評価",
            # 品質関連
            "バランス",
            "品質",
            "読みやすさ",
            "リズム",
            "自然",
            # 描写・表現関連
            "描写",
            "表現",
            "工夫",
            "配置",
            "処理",
            # 文章・文体関連
            "文章",
            "文体",
            "文末",
            "単調",
            "一貫性",
            # 感覚・体験関連
            "五感",
            "引き込む",
            "離脱",
            "過不足",
            # 会話・地の文
            "会話",
            "地の文",
            "口調",
            "転換",
            # その他重要要素
            "伏線",
            "キャラクター",
            "シーン",
            "誤字脱字",
        ]

        # 内容ベースの判定（より柔軟なマッチング）
        for keyword in suitable_content_keywords:
            if keyword in content:
                return True

        # A31チェックリスト実構造に基づくタイプ判定
        claude_suitable_types = [
            # 内容品質関連
            "content_quality",
            "content_balance",
            "content_review",
            "content_planning",
            # 文章品質関連
            "readability_check",
            "style_variety",
            "character_consistency",
            # 描写・表現関連
            "sensory_check",
            "transition_quality",
            "scene_design",
            # 基本品質関連
            "basic_proofread",
            "risk_assessment",
        ]

        return item_type in claude_suitable_types

    def _prepare_analysis_context(
        self,
        manuscript_file_path: str,
        request: SessionAnalysisRequest,
    ) -> AnalysisContext:
        """分析コンテキスト準備"""
        # 原稿内容読み込み
        manuscript_content = Path(manuscript_file_path).read_text(encoding="utf-8")

        return AnalysisContext(
            manuscript_content=manuscript_content,
            episode_number=request.episode_number,
            project_name=request.project_name,
            word_count=len(manuscript_content),
        )

    def _create_nested_progress_callback(
        self,
        parent_callback: Callable[[str, int, int], None] | None,
    ) -> Callable[[int, int, str], None] | None:
        """ネストしたプログレスコールバック作成"""
        if not parent_callback:
            return None

        def nested_callback(current: int, total: int, message: str) -> None:
            # 親コールバックに詳細プログレスを通知
            parent_callback(f"Claude分析: {message} ({current}/{total})", 3, 5)

        return nested_callback

    def _integrate_analysis_results(
        self,
        session_result: SessionAnalysisResult,
        request: SessionAnalysisRequest,
    ) -> int:
        """分析結果統合処理（模擬実装）

        実際の実装では、A31チェックリストファイルを更新し、
        分析結果をコメントとして追加する。
        """
        # 高信頼度改善提案のみを統合対象とする
        high_confidence_improvements = session_result.get_high_confidence_improvements()

        # TODO: 実際のファイル更新処理を実装
        # - チェックリストファイルの読み込み
        # - 改善提案のコメント形式での追加
        # - ファイルの保存

        return len(high_confidence_improvements)

    def _generate_performance_metrics(
        self,
        session_result: SessionAnalysisResult,
        execution_time: float,
    ) -> dict[str, Any]:
        """パフォーマンスメトリクス生成"""
        analyzer_stats = self._session_analyzer.get_execution_statistics()

        return {
            "total_execution_time": execution_time,
            "analysis_throughput": len(session_result.item_results) / execution_time,
            "success_rate": session_result.get_success_rate(),
            "average_analysis_time": analyzer_stats.get("total_execution_time", 0)
            / max(1, analyzer_stats.get("total_analyses", 1)),
            "memory_efficiency": "N/A",  # 将来実装
            "error_rate": analyzer_stats.get("failed_analyses", 0) / max(1, analyzer_stats.get("total_analyses", 1)),
        }

    def get_execution_history(self) -> list[SessionAnalysisResponse]:
        """実行履歴取得"""
        return self._execution_history.copy()

    def get_performance_summary(self) -> dict[str, Any]:
        """パフォーマンスサマリー取得"""
        if not self._execution_history:
            return {"status": "no_executions"}

        successful_executions = [response for response in self._execution_history if response.success]

        if not successful_executions:
            return {"status": "no_successful_executions"}

        return {
            "total_executions": len(self._execution_history),
            "successful_executions": len(successful_executions),
            "success_rate": len(successful_executions) / len(self._execution_history),
            "average_execution_time": sum(r.execution_time for r in successful_executions) / len(successful_executions),
            "average_items_analyzed": sum(r.analyzed_items_count for r in successful_executions)
            / len(successful_executions),
            "total_improvements_generated": sum(
                r.analysis_result.get_total_improvements() for r in successful_executions if r.analysis_result
            ),
        }
