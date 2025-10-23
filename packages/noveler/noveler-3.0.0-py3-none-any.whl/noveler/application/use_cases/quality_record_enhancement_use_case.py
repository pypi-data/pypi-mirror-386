#!/usr/bin/env python3
"""品質記録活用ユースケース
品質記録活用システムのアプリケーション層
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from noveler.domain.entities.learning_session import LearningSession
from noveler.domain.entities.quality_record_enhancement import QualityRecordEnhancement
from noveler.domain.exceptions import BusinessRuleViolationError, InsufficientDataError
from noveler.domain.services.improvement_suggestion_service import ImprovementSuggestionService
from noveler.domain.services.learning_data_integration_service import LearningDataIntegrationService
from noveler.domain.services.quality_trend_analysis_service import QualityTrendAnalysisService
from noveler.domain.value_objects.improvement_suggestion import ImprovementSuggestion
from noveler.domain.value_objects.learning_metrics import LearningMetrics
from noveler.domain.value_objects.quality_trend_data import QualityTrendData


@dataclass
class QualityCheckInput:
    """品質チェック入力データ"""

    project_name: str
    episode_number: int
    category_scores: dict[str, float]
    errors: list[str]
    warnings: list[str]
    auto_fixes: list[str]
    improvement_from_previous: float
    time_spent_writing: int
    revision_count: int
    user_feedback: str | None = None
    writing_environment: str | None = None
    target_audience: str | None = None
    writing_goal: str | None = None


@dataclass
class QualityAnalysisOutput:
    """品質分析出力データ"""

    quality_record: QualityRecordEnhancement
    trend_data: QualityTrendData | None = None
    improvement_suggestions: list[ImprovementSuggestion] | None = None
    learning_summary: dict[str, Any] | None = None


class QualityRecordEnhancementUseCase:
    """品質記録活用ユースケース

    品質記録の更新、分析、改善提案の生成を統合的に管理
    """

    def __init__(
        self,
        trend_analysis_service: QualityTrendAnalysisService,
        suggestion_service: ImprovementSuggestionService,
        integration_service: LearningDataIntegrationService,
    ) -> None:
        self.trend_analysis_service = trend_analysis_service
        self.suggestion_service = suggestion_service
        self.integration_service = integration_service

    def record_quality_check_with_learning(
        self, quality_input: QualityCheckInput, existing_record: dict[str, Any] | None
    ) -> QualityAnalysisOutput:
        """品質チェック結果を学習データと共に記録"""

        # 学習メトリクスの作成
        learning_metrics = LearningMetrics(
            improvement_from_previous=quality_input.improvement_from_previous,
            time_spent_writing=quality_input.time_spent_writing,
            revision_count=quality_input.revision_count,
            user_feedback=quality_input.user_feedback,
            writing_context=quality_input.writing_environment,
        )

        # 品質記録の作成または更新
        if existing_record is None:
            quality_record = QualityRecordEnhancement(project_name=quality_input.project_name, version="1.0")
        else:
            quality_record = existing_record

        # 品質チェック結果を追加
        quality_record.add_quality_check_result(
            episode_number=quality_input.episode_number,
            category_scores=quality_input.category_scores,
            errors=quality_input.errors,
            warnings=quality_input.warnings,
            auto_fixes=quality_input.auto_fixes,
            learning_metrics=learning_metrics,
            writing_environment=quality_input.writing_environment,
            target_audience=quality_input.target_audience,
            writing_goal=quality_input.writing_goal,
        )

        # 学習サマリーの生成
        learning_summary = quality_record.get_learning_summary()

        return QualityAnalysisOutput(quality_record=quality_record, learning_summary=learning_summary)

    def analyze_quality_trends(self, quality_record: QualityRecordEnhancement, category: str) -> QualityTrendData:
        """品質トレンドを分析"""

        if not quality_record.can_generate_trend_analysis():
            error_code = "insufficient_quality_records"
            msg = "トレンド分析には最低3つの品質記録が必要です"
            raise BusinessRuleViolationError(error_code, msg)

        # カテゴリ別トレンドデータの取得
        if category == "overall":
            # 全体的なトレンドを分析
            scores = []
            for check in quality_record.quality_checks:
                category_scores = check["results"]["category_scores"]
                if category_scores:
                    overall_score = sum(category_scores.values()) / len(category_scores)
                    scores.append(overall_score)
        else:
            # 特定カテゴリのトレンドを分析
            trend_data: dict[str, Any] = quality_record.get_improvement_trend(category)
            scores = [point["score"] for point in trend_data]

        MIN_DATA_POINTS = 3
        if len(scores) < MIN_DATA_POINTS:
            msg = f"カテゴリ '{category}' のトレンド分析には最低{MIN_DATA_POINTS}つのデータが必要です"
            raise InsufficientDataError(msg)

        return self.trend_analysis_service.analyze_quality_trend(
            category=category, scores=scores, analysis_period_days=30
        )

    def generate_improvement_suggestions(
        self, quality_record: QualityRecordEnhancement, user_profile: dict[str, Any]
    ) -> list[ImprovementSuggestion]:
        """改善提案を生成"""

        return self.suggestion_service.generate_improvement_suggestions(
            quality_record=quality_record, user_profile=user_profile
        )

    def create_learning_session(
        self,
        project_name: str,
        episode_number: int,
        writing_environment: str | None = None,
        target_audience: str | None = None,
        writing_goal: str | None = None,
    ) -> LearningSession:
        """学習セッションを作成"""

        return LearningSession(
            project_name=project_name,
            episode_number=episode_number,
            start_time=datetime.now(tz=timezone.utc),
            writing_environment=writing_environment,
            target_audience=target_audience,
            writing_goal=writing_goal,
        )

    def complete_learning_session(
        self,
        session: LearningSession,
        improvement_from_previous: float,
        end_time: datetime | None = None,
        revision_count: int = 0,
        user_feedback: str | None = None,
    ) -> LearningMetrics:
        """学習セッションを完了して学習メトリクスを作成"""

        # セッションを完了
        if end_time is None:
            end_time = datetime.now(tz=timezone.utc)
        session.complete(end_time)

        # 学習メトリクスを作成
        return session.create_learning_metrics(
            improvement_from_previous=improvement_from_previous,
            revision_count=revision_count,
            user_feedback=user_feedback,
        )

    def generate_comprehensive_analysis(
        self, quality_record: QualityRecordEnhancement, user_profile: dict[str, Any]
    ) -> QualityAnalysisOutput:
        """包括的な品質分析を生成"""

        output = QualityAnalysisOutput(quality_record=quality_record)

        # 学習サマリーの生成
        output.learning_summary = self.integration_service.integrate_learning_data(quality_record)

        # トレンド分析(データが十分にある場合)
        if quality_record.can_generate_trend_analysis():
            try:
                output.trend_data = self.analyze_quality_trends(quality_record, "overall")
            except (BusinessRuleViolationError, InsufficientDataError):
                # データが不十分な場合はトレンド分析をスキップ
                output.trend_data = None

        # 改善提案の生成
        if quality_record.can_generate_improvement_suggestions():
            try:
                output.improvement_suggestions = self.generate_improvement_suggestions(quality_record, user_profile)
            except (BusinessRuleViolationError, InsufficientDataError):
                # データが不十分な場合は改善提案をスキップ
                output.improvement_suggestions = []

        return output

    def get_quality_insights(self, quality_record: QualityRecordEnhancement) -> dict[str, Any]:
        """品質インサイトを取得"""

        insights: dict[str, Any] = {
            "basic_stats": quality_record.get_learning_summary(),
            "patterns": {},
            "recommendations": [],
        }

        # 学習パターンの分析
        if quality_record.has_sufficient_data_for_analysis():
            patterns = self.integration_service.identify_learning_patterns(quality_record)
            insights["patterns"] = patterns

            # パターンに基づく推奨事項
            recommendations = insights["recommendations"]
            if patterns["improving_categories"]:
                recommendations.append(f"強化中のカテゴリ: {', '.join(patterns['improving_categories'])}")

            if patterns["declining_categories"]:
                recommendations.append(f"要注意カテゴリ: {', '.join(patterns['declining_categories'])}")

        return insights

    def validate_quality_input(self, quality_input: QualityCheckInput) -> bool:
        """品質入力データの妥当性を検証"""

        # 定数定義
        MIN_SCORE = 0.0
        MAX_SCORE = 100.0

        # プロジェクト名の検証
        if not quality_input.project_name or len(quality_input.project_name.strip()) == 0:
            msg = "プロジェクト名は必須です"
            raise BusinessRuleViolationError("project_name_required", msg)

        # エピソード番号の検証
        if quality_input.episode_number <= 0:
            msg = "エピソード番号は1以上の正の整数である必要があります"
            raise BusinessRuleViolationError("episode_number_invalid", msg)

        # カテゴリスコアの検証
        if not quality_input.category_scores:
            msg = "カテゴリスコアは必須です"
            raise BusinessRuleViolationError("category_scores_required", msg)

        for category, score in quality_input.category_scores.items():
            if score < MIN_SCORE or score > MAX_SCORE:
                msg = f"カテゴリ '{category}' のスコアは{MIN_SCORE}から{MAX_SCORE}の範囲で指定してください"
                raise BusinessRuleViolationError("score_out_of_range", msg)

        # 執筆時間の検証
        if quality_input.time_spent_writing < 0:
            msg = "執筆時間は0分以上で指定してください"
            raise BusinessRuleViolationError("writing_minutes_invalid", msg)

        # リビジョン数の検証
        if quality_input.revision_count < 0:
            msg = "リビジョン数は0以上で指定してください"
            raise BusinessRuleViolationError("revision_count_invalid", msg)

        return True
