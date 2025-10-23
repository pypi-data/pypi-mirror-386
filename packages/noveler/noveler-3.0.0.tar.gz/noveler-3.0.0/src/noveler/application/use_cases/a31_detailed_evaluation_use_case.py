#!/usr/bin/env python3
"""A31詳細評価ユースケース

手動Claude Code分析と同等の詳細フィードバックを提供するA31評価の
アプリケーション層実装。既存A31システムとの統合も保証する。
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from noveler.domain.entities.detailed_evaluation_session import DetailedEvaluationSession
from noveler.domain.repositories.a31_checklist_repository import A31ChecklistRepository
from noveler.domain.repositories.detailed_evaluation_repository import DetailedEvaluationRepository
from noveler.domain.services.detailed_analysis_engine import (
    AnalysisContext,
    DetailedAnalysisEngine,
    DetailedAnalysisResult,
)
from noveler.domain.value_objects.a31_evaluation_category import A31EvaluationCategory
from noveler.domain.value_objects.episode_number import EpisodeNumber


@dataclass
class A31DetailedEvaluationRequest:
    """A31詳細評価リクエスト"""

    project_name: str
    episode_number: int
    target_categories: list[A31EvaluationCategory] | None = None
    include_line_feedback: bool = True
    include_improvement_suggestions: bool = True
    output_format: str = "comprehensive"  # comprehensive | summary | yaml
    save_results: bool = True


@dataclass
class A31DetailedEvaluationResponse:
    """A31詳細評価レスポンス"""

    success: bool
    session_id: str
    project_name: str
    episode_number: int
    overall_score: float
    category_scores: dict[str, float]
    total_issues_found: int
    total_suggestions: int
    line_feedback_count: int
    confidence_score: float
    execution_time_seconds: float
    detailed_results: DetailedAnalysisResult | None = None
    yaml_output: str | None = None
    error_message: str | None = None

    def get_summary_dict(self) -> dict[str, Any]:
        """サマリー辞書を取得

        Returns:
            dict[str, Any]: 評価結果サマリー
        """
        return {
            "success": self.success,
            "project_name": self.project_name,
            "episode_number": self.episode_number,
            "overall_score": self.overall_score,
            "category_scores": self.category_scores,
            "total_issues": self.total_issues_found,
            "total_suggestions": self.total_suggestions,
            "line_feedback_count": self.line_feedback_count,
            "confidence": self.confidence_score,
            "execution_time": self.execution_time_seconds,
        }

    def is_passing_grade(self, threshold: float = 80.0) -> bool:
        """合格基準判定

        Args:
            threshold: 合格基準スコア

        Returns:
            bool: 合格の場合True
        """
        return self.success and self.overall_score >= threshold


class DetailedEpisodeEvaluationUseCase:
    """A31詳細評価ユースケース

    手動Claude Code分析レベルの詳細評価を実行し、
    既存A31システムとの互換性も保証するユースケース。
    """

    def __init__(
        self,
        a31_checklist_repository: A31ChecklistRepository,
        detailed_evaluation_repository: DetailedEvaluationRepository,
        analysis_engine: DetailedAnalysisEngine | None = None,
        episode_repository: Any | None = None,
        project_repository: Any | None = None,
        **kwargs: Any,
    ) -> None:
        """A31詳細評価ユースケース初期化

        Args:
            a31_checklist_repository: A31チェックリストリポジトリ
            detailed_evaluation_repository: 詳細評価リポジトリ
            analysis_engine: 詳細分析エンジン（オプション）
        """
        self._a31_checklist_repository = a31_checklist_repository
        self._detailed_evaluation_repository = detailed_evaluation_repository
        self._analysis_engine = analysis_engine or DetailedAnalysisEngine()

        # Compatibility shims for repositories expected by tests
        class _FallbackEpisodeRepo:
            def get_episode_content(self, project_name: str, episode_number: int) -> str:
                raise FileNotFoundError(f"Episode not found: {project_name} #{episode_number}")

        class _FallbackProjectRepo:
            def get_project_config(self, project_name: str) -> dict[str, Any]:
                return {}

        self._episode_repository = episode_repository or _FallbackEpisodeRepo()
        self._project_repository = project_repository or _FallbackProjectRepo()

        # absorb legacy kwargs (e.g., episode_repository, project_repository passed in kwargs)
        if not episode_repository and "episode_repository" in kwargs:
            self._episode_repository = kwargs["episode_repository"]
        if not project_repository and "project_repository" in kwargs:
            self._project_repository = kwargs["project_repository"]


    def execute(self, request: A31DetailedEvaluationRequest) -> A31DetailedEvaluationResponse:
        """A31詳細評価を実行

        Args:
            request: 詳細評価リクエスト

        Returns:
            A31DetailedEvaluationResponse: 詳細評価レスポンス
        """
        start_time = datetime.now(timezone.utc)

        try:
            # 1. エピソード内容の取得
            episode_content = self._get_episode_content(request.project_name, request.episode_number)

            # 2. 評価セッションの作成と開始
            session = DetailedEvaluationSession.create(
                project_name=request.project_name,
                episode_number=EpisodeNumber(request.episode_number),
                episode_content=episode_content,
            )

            session.start_evaluation()

            # 3. チェックリスト項目の取得
            checklist_items = self._get_checklist_items(request.project_name, request.target_categories)

            # 4. 分析コンテキストの準備
            analysis_context = self._prepare_analysis_context(
                request.project_name, request.episode_number, request.target_categories
            )

            # 5. 詳細分析の実行
            analysis_result = self._analysis_engine.analyze_episode_detailed(
                session=session, checklist_items=checklist_items, context=analysis_context
            )

            # 6. セッション結果の更新
            self._update_session_with_results(session, analysis_result)
            session.complete_evaluation()

            # 7. 結果の保存（オプション）
            if request.save_results:
                self._detailed_evaluation_repository.save_evaluation_session(session)
                self._detailed_evaluation_repository.save_analysis_result(analysis_result)

            # 8. レスポンスの作成
            execution_time = max((datetime.now(timezone.utc) - start_time).total_seconds(), 0.1)

            response = A31DetailedEvaluationResponse(
                success=True,
                session_id=session.session_id.value,
                project_name=request.project_name,
                episode_number=request.episode_number,
                overall_score=analysis_result.overall_score,
                category_scores=self._extract_category_scores(analysis_result),
                total_issues_found=sum(len(cr.issues_found) for cr in analysis_result.category_results),
                total_suggestions=sum(len(cr.suggestions) for cr in analysis_result.category_results),
                line_feedback_count=len(analysis_result.line_feedbacks),
                confidence_score=analysis_result.confidence_score,
                execution_time_seconds=execution_time,
                detailed_results=analysis_result if request.output_format == "comprehensive" else None,
            )

            # 9. YAML出力生成（必要な場合）
            if request.output_format == "yaml":
                response.yaml_output = self._generate_yaml_output(analysis_result)

            return response

        except Exception as e:
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()

            return A31DetailedEvaluationResponse(
                success=False,
                session_id="",
                project_name=request.project_name,
                episode_number=request.episode_number,
                overall_score=0.0,
                category_scores={},
                total_issues_found=0,
                total_suggestions=0,
                line_feedback_count=0,
                confidence_score=0.0,
                execution_time_seconds=execution_time,
                error_message=f"詳細評価実行中にエラーが発生しました: {e!s}",
            )

    def execute_legacy_a31_compatible(self, request: A31DetailedEvaluationRequest) -> dict[str, Any]:
        """既存A31システム互換形式での実行

        Args:
            request: 詳細評価リクエスト

        Returns:
            dict[str, Any]: 既存A31形式のレスポンス
        """
        response = self.execute(request)

        if not response.success:
            return {
                "success": False,
                "error_message": response.error_message,
                "project_name": request.project_name,
                "episode_number": request.episode_number,
            }

        # 既存A31形式に変換
        return {
            "success": True,
            "project_name": response.project_name,
            "episode_number": response.episode_number,
            "evaluation_batch": {
                "results": self._convert_to_a31_results(response.detailed_results),
                "total_items": len(response.category_scores),
                "evaluated_items": len(response.category_scores),
                "execution_time_ms": response.execution_time_seconds * 1000,
            },
            "total_items_checked": len(response.category_scores),
            "checklist_file_path": f"temp/a31_detailed_episode_{request.episode_number}.yaml",
            "auto_fixes_applied": 0,  # 将来実装
            "overall_score": response.overall_score,
            "pass_rate": len([s for s in response.category_scores.values() if s >= 80.0])
            / len(response.category_scores)
            if response.category_scores
            else 0.0,
        }

    def _get_episode_content(self, project_name: str, episode_number: int) -> str:
        """エピソード内容の取得

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号

        Returns:
            str: エピソード内容

        Raises:
            FileNotFoundError: エピソードが見つからない場合
        """
        try:
            return self._episode_repository.get_episode_content(project_name, episode_number)
        except FileNotFoundError as e:
            msg = f"エピソード {episode_number} が見つかりません: {project_name}"
            raise FileNotFoundError(msg) from e

    def _get_checklist_items(
        self, project_name: str, target_categories: list[A31EvaluationCategory] | None
    ) -> list[Any]:
        """チェックリスト項目の取得

        Args:
            project_name: プロジェクト名
            target_categories: 対象カテゴリリスト

        Returns:
            list[Any]: チェックリスト項目リスト
        """
        all_items = self._a31_checklist_repository.get_all_checklist_items(project_name)

        if target_categories is None:
            return all_items

        # カテゴリでフィルタリング
        filtered_items = []
        for item in all_items:
            if hasattr(item, "category") and item.category in target_categories:
                filtered_items.append(item)
            elif hasattr(item, "item_type"):
                # item_typeからカテゴリを推定
                item_category = self._infer_category_from_item_type(item.item_type)
                if item_category in target_categories:
                    filtered_items.append(item)

        return filtered_items

    def _prepare_analysis_context(
        self, project_name: str, episode_number: int, target_categories: list[A31EvaluationCategory] | None
    ) -> AnalysisContext:
        """分析コンテキストの準備

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号
            target_categories: 対象カテゴリリスト

        Returns:
            AnalysisContext: 分析コンテキスト
        """
        # デフォルトカテゴリ設定
        if target_categories is None:
            target_categories = [
                A31EvaluationCategory.FORMAT_CHECK,
                A31EvaluationCategory.CONTENT_BALANCE,
                A31EvaluationCategory.STYLE_CONSISTENCY,
                A31EvaluationCategory.READABILITY_CHECK,
                A31EvaluationCategory.CHARACTER_CONSISTENCY,
            ]

        # プロジェクト設定の取得
        try:
            project_config: dict[str, Any] = self._project_repository.get_project_config(project_name)
            quality_threshold = project_config.get("quality_threshold", 80.0)
        except Exception:
            quality_threshold = 80.0

        # 前話内容の取得（オプション）
        previous_episode_content = None
        if episode_number > 1:
            try:
                previous_episode_content = self._episode_repository.get_episode_content(
                    project_name, episode_number - 1
                )

            except FileNotFoundError:
                pass  # 前話がない場合は無視

        return AnalysisContext.create(
            project_name=project_name,
            episode_number=episode_number,
            target_categories=target_categories,
            quality_threshold=quality_threshold,
            previous_episode_content=previous_episode_content,
        )

    def _update_session_with_results(
        self, session: DetailedEvaluationSession, analysis_result: DetailedAnalysisResult
    ) -> None:
        """セッションに分析結果を反映

        Args:
            session: 評価セッション
            analysis_result: 分析結果
        """
        # カテゴリ分析結果を追加
        for category_result in analysis_result.category_results:
            session.add_category_analysis(category_result)

        # 行別フィードバックを追加
        for line_feedback in analysis_result.line_feedbacks:
            session.add_line_feedback(line_feedback)

    def _extract_category_scores(self, analysis_result: DetailedAnalysisResult) -> dict[str, float]:
        """カテゴリスコアを抽出

        Args:
            analysis_result: 分析結果

        Returns:
            dict[str, float]: カテゴリ別スコア辞書
        """
        return {result.category.value: result.score for result in analysis_result.category_results}

    def _generate_yaml_output(self, analysis_result: DetailedAnalysisResult) -> str:
        """YAML出力を生成

        Args:
            analysis_result: 分析結果

        Returns:
            str: YAML形式の出力
        """
        import yaml

        output_data: dict[str, Any] = {
            "evaluation_summary": {
                "overall_score": analysis_result.overall_score,
                "confidence_score": analysis_result.confidence_score,
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "category_results": [
                {
                    "category": result.category.value,
                    "score": result.score,
                    "issues_found": result.issues_found,
                    "suggestions": result.suggestions,
                    "confidence": result.calculate_confidence_score(),
                }
                for result in analysis_result.category_results
            ],
            "line_feedback": [
                {
                    "line_number": feedback.line_number,
                    "issue_type": feedback.issue_type.value,
                    "severity": feedback.severity.value,
                    "suggestion": feedback.suggestion.content,
                    "confidence": feedback.confidence,
                }
                for feedback in analysis_result.line_feedbacks
            ],
            "improvement_summary": {
                "total_issues": len(analysis_result.line_feedbacks),
                "critical_issues": len([f for f in analysis_result.line_feedbacks if f.severity.value == "critical"]),
                "actionable_suggestions": sum(len(r.suggestions) for r in analysis_result.category_results),
            },
        }

        return yaml.dump(output_data, default_flow_style=False, allow_unicode=True, sort_keys=False)

    def _convert_to_a31_results(self, analysis_result: DetailedAnalysisResult | None) -> dict[str, Any]:
        """A31形式結果に変換

        Args:
            analysis_result: 詳細分析結果

        Returns:
            dict[str, Any]: A31形式結果辞書
        """
        if not analysis_result:
            return {}

        results: dict[str, Any] = {}
        for i, category_result in enumerate(analysis_result.category_results, 1):
            item_id = f"A31-{i:03d}"
            results[item_id] = {
                "item_id": item_id,
                "category": category_result.category.value,
                "score": category_result.score,
                "passed": category_result.is_passing_grade(),
                "details": " | ".join(category_result.suggestions) if category_result.suggestions else "評価完了",
                "execution_time_ms": 100.0,  # 仮の値
                "auto_fixable": False,  # 将来実装
            }

        return results

    def _infer_category_from_item_type(self, item_type: Any) -> A31EvaluationCategory:
        """アイテムタイプからカテゴリを推定

        Args:
            item_type: アイテムタイプ

        Returns:
            A31EvaluationCategory: 推定されたカテゴリ
        """
        # アイテムタイプとカテゴリのマッピング（簡易版）
        type_to_category = {
            "format_check": A31EvaluationCategory.FORMAT_CHECK,
            "content_balance": A31EvaluationCategory.CONTENT_BALANCE,
            "style_consistency": A31EvaluationCategory.STYLE_CONSISTENCY,
            "readability_check": A31EvaluationCategory.READABILITY_CHECK,
            "character_consistency": A31EvaluationCategory.CHARACTER_CONSISTENCY,
        }

        if hasattr(item_type, "value"):
            return type_to_category.get(item_type.value, A31EvaluationCategory.QUALITY_THRESHOLD)

        return A31EvaluationCategory.QUALITY_THRESHOLD

# Backward-compatible alias (tests may import this name)
A31DetailedEvaluationUseCase = DetailedEpisodeEvaluationUseCase
