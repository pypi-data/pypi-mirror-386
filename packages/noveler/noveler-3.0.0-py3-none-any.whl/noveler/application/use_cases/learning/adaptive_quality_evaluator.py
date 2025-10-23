"""適応的品質評価ユースケース

アプリケーション層:学習機能ドメインサービスの調整・外部システム連携
"""

import uuid
from dataclasses import dataclass
from typing import Any

from noveler.domain.learning.entities import LearningQualityEvaluator
from noveler.domain.learning.repositories import (
    EpisodeAnalysisRepository,
    LearningEvaluatorRepository,
    QualityLearningRepository,
    ReaderFeedbackRepository,
    WritingStyleProfileRepository,
)
from noveler.domain.learning.services import AdaptiveQualityService, CorrelationAnalysisService, StyleLearningService
from noveler.domain.learning.value_objects import EvaluationResult, QualityMetric
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


@dataclass
class LearningRepositoryCollection:
    """学習機能のリポジトリ群"""

    learning_repository: QualityLearningRepository
    episode_repository: EpisodeAnalysisRepository
    feedback_repository: ReaderFeedbackRepository
    profile_repository: WritingStyleProfileRepository
    evaluator_repository: LearningEvaluatorRepository


@dataclass
class LearningServiceCollection:
    """学習機能のサービス群"""

    style_learning_service: StyleLearningService
    adaptive_service: AdaptiveQualityService
    correlation_service: CorrelationAnalysisService


class AdaptiveQualityEvaluatorUseCase:
    """適応的品質評価ユースケース

    責務:
    - 学習データの収集・整理
    - ドメインサービス間の協調
    - 評価結果の保存・履歴管理
    """

    def __init__(self, repositories: LearningRepositoryCollection, services: LearningServiceCollection) -> None:
        # リポジトリ
        self.learning_repository = repositories.learning_repository
        self.episode_repository = repositories.episode_repository
        self.feedback_repository = repositories.feedback_repository
        self.profile_repository = repositories.profile_repository
        self.evaluator_repository = repositories.evaluator_repository
        # サービス
        self.style_learning_service = services.style_learning_service
        self.adaptive_service = services.adaptive_service
        self.correlation_service = services.correlation_service

    def initialize_learning_evaluator(self, project_id: str) -> dict[str, Any]:
        """プロジェクト用学習評価器初期化"""
        try:
            # 既存評価器チェック
            existing_evaluator = self.evaluator_repository.find_evaluator_by_project(project_id)
            if existing_evaluator:
                return {
                    "success": True,
                    "evaluator_id": existing_evaluator.evaluator_id,
                    "status": "already_exists",
                    "is_trained": existing_evaluator.is_trained(),
                }

            # 新規評価器作成
            evaluator = LearningQualityEvaluator(
                evaluator_id=str(uuid.uuid4()),
                project_id=project_id,
            )

            # 過去データから学習
            historical_data: dict[str, Any] = self.episode_repository.find_project_episodes_analysis(project_id)

            if len(historical_data) >= 5:
                # 十分なデータがある場合は学習実行
                evaluator.learn_from_historical_data(historical_data)

                return {
                    "success": True,
                    "evaluator_id": evaluator.evaluator_id,
                    "status": "created_and_trained",
                    "training_data_count": len(historical_data),
                    "learning_quality": evaluator.get_learning_data_quality().value,
                }
            # データ不足の場合は評価器のみ作成
            self.evaluator_repository.save_evaluator(evaluator)

            return {
                "success": True,
                "evaluator_id": evaluator.evaluator_id,
                "status": "created_untrained",
                "message": "学習データが不足しています。5エピソード以上のデータが必要です。",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def evaluate_episode_quality(
        self, project_id: str, episode_text: str, episode_id: str | None = None
    ) -> dict[str, Any]:
        """エピソード品質評価(学習機能付き)"""
        try:
            # 評価器取得
            evaluator = self.evaluator_repository.find_evaluator_by_project(project_id)
            if not evaluator:
                return {"success": False, "error": "プロジェクト用評価器が見つかりません"}

            # 標準評価と学習済み評価の両方実行
            standard_result = evaluator.evaluate_with_standard_criteria(episode_text)

            if evaluator.is_trained():
                adaptive_result = evaluator.evaluate_with_learned_criteria(episode_text)
                primary_result = adaptive_result
                comparison_available = True
            else:
                adaptive_result = None
                primary_result = standard_result
                comparison_available = False

            # 評価結果保存
            if episode_id:
                evaluation_data: dict[str, Any] = {
                    "episode_id": episode_id,
                    "evaluation_timestamp": project_now().datetime.isoformat(),
                    "standard_score": standard_result.total_score,
                    "adaptive_score": adaptive_result.total_score if adaptive_result else None,
                    "confidence_level": primary_result.confidence_level,
                    "personalization_applied": primary_result.has_personalized_adjustments(),
                }
                self.evaluator_repository.save_evaluation_result(
                    evaluator.evaluator_id,
                    episode_id,
                    evaluation_data,
                )

            return {
                "success": True,
                "primary_evaluation": {
                    "total_score": primary_result.total_score,
                    "metric_scores": {k.value: v for k, v in primary_result.metric_scores.items()},
                    "confidence_level": primary_result.confidence_level,
                    "evaluation_type": "adaptive" if evaluator.is_trained() else "standard",
                },
                "comparison": (
                    {
                        "available": comparison_available,
                        "standard_score": standard_result.total_score,
                        "adaptive_score": adaptive_result.total_score if adaptive_result else None,
                        "improvement": (
                            (adaptive_result.total_score - standard_result.total_score) if adaptive_result else 0
                        ),
                    }
                    if comparison_available
                    else None
                ),
                "recommendations": self._generate_recommendations(primary_result, evaluator),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_recommendations(
        self, evaluation_result: EvaluationResult, _evaluator: LearningQualityEvaluator
    ) -> list[str]:
        """評価結果に基づく改善推奨生成"""
        recommendations = []

        # スコア別推奨
        if evaluation_result.total_score < 60:
            recommendations.append("全体的な品質向上が必要です。特に低スコア項目を重点的に改善してください。")
        elif evaluation_result.total_score < 80:
            recommendations.append("品質は良好ですが、さらなる向上の余地があります。")

        # メトリック別推奨
        for metric, score in evaluation_result.metric_scores.items():
            if score < 60:
                if metric == QualityMetric.READABILITY:
                    recommendations.append("文章の読みやすさを改善してください。文長や語彙を見直してみてください。")
                elif metric == QualityMetric.DIALOGUE_RATIO:
                    recommendations.append("会話と地の文のバランスを調整してください。")
                elif metric == QualityMetric.NARRATIVE_DEPTH:
                    recommendations.append("内面描写や情景描写を豊かにしてください。")

        # 個人化調整があるかチェック
        if evaluation_result.has_personalized_adjustments():
            recommendations.append("あなたの執筆スタイルに基づいて評価基準を調整しました。")

        return recommendations

    def trigger_retraining(self, project_id: str) -> dict[str, Any]:
        """学習モデル再学習トリガー"""
        try:
            evaluator = self.evaluator_repository.find_evaluator_by_project(project_id)
            if not evaluator:
                return {"success": False, "error": "評価器が見つかりません"}

            # 新しいデータ収集
            new_episodes = self.episode_repository.find_project_episodes_analysis(project_id)
            recent_feedback = self.feedback_repository.find_feedback_by_project(project_id)

            if len(new_episodes) < 5:
                return {
                    "success": False,
                    "error": "再学習に十分なデータがありません",
                    "current_data_count": len(new_episodes),
                }

            # 再学習実行
            evaluator.learn_from_historical_data(new_episodes)

            # 読者反応データとの相関分析
            if len(recent_feedback) >= 5:
                correlation_data: dict[str, Any] = self._prepare_correlation_data(new_episodes, recent_feedback)
                correlations = evaluator.analyze_quality_feedback_correlation(correlation_data)
                evaluator.apply_correlation_insights(correlations)

            # 更新された評価器保存
            self.evaluator_repository.save_evaluator(evaluator)

            return {
                "success": True,
                "retraining_completed": True,
                "training_data_count": len(new_episodes),
                "correlation_analysis_applied": len(recent_feedback) >= 5,
                "learning_quality": evaluator.get_learning_data_quality().value,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _prepare_correlation_data(
        self, episodes: list[dict[str, Any]], feedback: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """相関分析用データ準備"""
        correlation_data: dict[str, Any] = []

        # エピソードIDをキーとしてデータをマッチング
        feedback_by_episode = {fb["episode_id"]: fb for fb in feedback}

        for episode in episodes:
            episode_id = episode["episode_id"]
            if episode_id in feedback_by_episode:
                fb = feedback_by_episode[episode_id]
                correlation_data.append(
                    {
                        "readability": episode.get("readability", 75),
                        "dialogue_ratio": episode.get("dialogue_ratio", 0.35),
                        "reader_rating": fb.get("rating", 3.0),
                        "retention_rate": fb.get("retention_rate", 0.7),
                    }
                )

        return correlation_data

    def get_learning_status(self, project_id: str) -> dict[str, Any]:
        """学習状況取得"""
        try:
            evaluator = self.evaluator_repository.find_evaluator_by_project(project_id)
            if not evaluator:
                return {"success": False, "error": "評価器が見つかりません"}

            # 基本状況
            status = {
                "evaluator_id": evaluator.evaluator_id,
                "is_trained": evaluator.is_trained(),
                "learning_quality": (
                    evaluator.get_learning_data_quality().value if evaluator.is_trained() else "untrained"
                ),
            }

            if evaluator.is_trained():
                # 学習済みの場合の詳細情報
                status.update(
                    {
                        "learning_info": {
                            "author_style_profile": evaluator.author_style_profile,
                            "sample_count": evaluator.sample_count,
                        },
                        "learned_patterns": list(evaluator.learned_patterns.keys()),
                        "quality_adjustments": list(evaluator.quality_criteria_adjustments.keys()),
                    }
                )

            # 評価履歴統計
            evaluation_history = self.evaluator_repository.find_evaluation_history(evaluator.evaluator_id, 30)
            if evaluation_history:
                recent_scores = [
                    eval_data.get("adaptive_score") or eval_data.get("standard_score")
                    for eval_data in evaluation_history[-10:]
                ]
                recent_scores = [score for score in recent_scores if score is not None]

                if recent_scores:
                    status["recent_performance"] = {
                        "average_score": sum(recent_scores) / len(recent_scores),
                        "score_trend": "improving"
                        if len(recent_scores) > 1 and recent_scores[-1] > recent_scores[0]
                        else "stable",
                        "evaluation_count": len(evaluation_history),
                    }

            return {"success": True, "status": status}

        except Exception as e:
            return {"success": False, "error": str(e)}
