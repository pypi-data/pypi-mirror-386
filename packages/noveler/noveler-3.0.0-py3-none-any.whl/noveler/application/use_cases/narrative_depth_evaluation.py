# application/use_cases/narrative_depth_evaluation.py
"""内面描写深度評価のユースケース"""

from typing import Any

from noveler.domain.repositories.analysis_result_repository import AnalysisResultRepository
from noveler.domain.repositories.manuscript_repository import ManuscriptRepository
from noveler.domain.repositories.plot_repository import PlotRepository
from noveler.domain.services.narrative_depth_analyzer import NarrativeDepthAnalyzer
from noveler.domain.services.viewpoint_evaluator import ViewpointEvaluator
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class EvaluateNarrativeDepthUseCase:
    """内面描写深度評価ユースケース"""

    def __init__(
        self,
        plot_repository: PlotRepository,
        text_repository: ManuscriptRepository,
        result_repository: AnalysisResultRepository,
        analyzer: NarrativeDepthAnalyzer,
        evaluator: ViewpointEvaluator,
    ) -> None:
        self.plot_repository = plot_repository
        self.text_repository = text_repository
        self.result_repository = result_repository
        self.analyzer = analyzer
        self.evaluator = evaluator

    def execute(self, episode_number: int) -> dict[str, Any]:
        """内面描写深度評価を実行"""
        # 1. エピソードテキストを取得
        episode_text = self.text_repository.get_episode_text(episode_number)
        if not episode_text:
            return self._create_error_result(f"Episode {episode_number} not found")

        # 2. 視点情報を取得
        viewpoint_info = self.plot_repository.get_viewpoint_info(episode_number)
        if not viewpoint_info:
            return self._create_error_result(f"Viewpoint info for episode {episode_number} not found")

        # 3. 内面描写深度分析を実行
        depth_score = self.analyzer.analyze_depth(episode_text)

        # 4. 視点情報に基づいて調整
        viewpoint_type = viewpoint_info.get("視点タイプ", "標準")
        complexity_level = viewpoint_info.get("複雑度", "中")

        adjusted_score = self.evaluator.adjust_for_viewpoint(
            depth_score,
            viewpoint_type,
            complexity_level,
        )

        # 5. 結果を構築
        result = self._create_success_result(
            episode_number,
            depth_score,
            adjusted_score,
            viewpoint_info,
        )

        # 6. 結果を保存
        self.result_repository.save_evaluation_result(episode_number, result)

        return result

    def _create_success_result(
        self, episode_number: int, depth_score: float, adjusted_score: float, viewpoint_info: dict[str, Any]
    ) -> dict[str, Any]:
        """成功結果を作成"""
        return {
            "status": "success",
            "episode_number": episode_number,
            "narrative_depth_analysis": {
                "layer_scores": {
                    layer.value: {
                        "score": score.score,
                        "percentage": score.percentage,
                        "max_score": score.max_score,
                    }
                    for layer, score in depth_score.layer_scores.items()
                },
                "base_total_score": depth_score.total_score,
                "adjusted_total_score": adjusted_score,
                "organic_combination_bonus": depth_score._has_organic_combination(),
            },
            "viewpoint_info": viewpoint_info,
            "recommendations": self._generate_recommendations(depth_score, viewpoint_info),
            "evaluation_metadata": {
                "analyzer_version": "1.0.0",
                "evaluation_timestamp": self._get_current_timestamp(),
            },
        }

    def _create_error_result(self, error_message: str) -> dict[str, Any]:
        """エラー結果を作成"""
        return {
            "status": "error",
            "error_message": error_message,
            "evaluation_metadata": {
                "analyzer_version": "1.0.0",
                "evaluation_timestamp": self._get_current_timestamp(),
            },
        }

    def _generate_recommendations(self, depth_score: float, viewpoint_info: dict[str, Any]) -> list[str]:
        """推奨事項を生成"""
        recommendations = []

        # 各層のスコアに基づく推奨事項
        for layer, score in depth_score.layer_scores.items():
            if score.percentage < 30:
                recommendations.append(
                    {
                        "type": "depth_improvement",
                        "layer": layer,
                        "current_score": score.percentage,
                        "message": f"{layer}の描写を深めることをお勧めします",
                    }
                )

        # 総合スコアに基づく推奨事項
        if depth_score.total_score < 50:
            recommendations.append(
                {"type": "overall_improvement", "message": "全体的な内面描写を充実させることをお勧めします"}
            )

        # 視点タイプに基づく推奨事項
        viewpoint_type = viewpoint_info.get("視点タイプ", "")
        if "単一視点" in viewpoint_type and depth_score.total_score < 60:
            recommendations.append({"type": "viewpoint_specific", "message": "単一視点ではより深い内面描写が有効です"})

        return recommendations

    def _get_current_timestamp(self) -> str:
        """現在のタイムスタンプを取得"""

        return project_now().datetime.isoformat()


class ViewpointAwareQualityEvaluationUseCase:
    """視点情報を考慮した品質評価ユースケース"""

    def __init__(self, narrative_evaluation: EvaluateNarrativeDepthUseCase, plot_repository: PlotRepository) -> None:
        self.narrative_evaluation = narrative_evaluation
        self.plot_repository = plot_repository

    def execute(self, episode_number: int, base_scores: dict[str, float]) -> dict[str, Any]:
        """視点情報を考慮した総合品質評価を実行"""
        # 1. 視点情報を取得
        viewpoint_info = self.plot_repository.get_viewpoint_info(episode_number)
        if not viewpoint_info:
            return self._apply_standard_evaluation(base_scores)

        # 2. 内面描写深度評価を実行
        narrative_result = self.narrative_evaluation.execute(episode_number)
        if narrative_result["status"] != "success":
            return self._apply_standard_evaluation(base_scores)

        # 3. 視点タイプに基づいてスコアを調整
        adjusted_scores = self._adjust_scores_by_viewpoint(
            base_scores,
            narrative_result,
            viewpoint_info,
        )

        # 4. 結果を構築
        return {
            "status": "success",
            "episode_number": episode_number,
            "viewpoint_adjusted_scores": adjusted_scores,
            "base_scores": base_scores,
            "narrative_depth_analysis": narrative_result.get("narrative_depth_analysis"),
            "viewpoint_info": viewpoint_info,
            "adjustment_summary": self._create_adjustment_summary(
                base_scores,
                adjusted_scores,
                viewpoint_info,
            ),
        }

    def _adjust_scores_by_viewpoint(
        self, base_scores: dict[str, float], narrative_result: dict[str, Any], viewpoint_info: dict[str, Any]
    ) -> dict[str, float]:
        """視点タイプに基づいてスコアを調整"""
        adjusted_scores = base_scores.copy()
        viewpoint_type = viewpoint_info.get("視点タイプ", "")

        # 内面描写深度スコアを取得
        narrative_score = narrative_result["narrative_depth_analysis"]["adjusted_total_score"]

        if "内省型" in viewpoint_type or "単一視点" in viewpoint_type:
            # 単一視点・内省型:会話比率の重みを下げ、内面描写を重視
            if "dialogue_ratio" in adjusted_scores:
                adjusted_scores["dialogue_ratio"] *= 0.5
            adjusted_scores["narrative_depth"] = narrative_score * 1.5

        elif "身体交換" in viewpoint_type:
            # 身体交換:内面描写を重視
            adjusted_scores["narrative_depth"] = narrative_score * 1.3

        elif "複数視点" in viewpoint_type:
            # 複数視点:視点の明確さを重視
            if "viewpoint_clarity" in adjusted_scores:
                adjusted_scores["viewpoint_clarity"] *= 1.5

        else:
            # 標準的な評価
            adjusted_scores["narrative_depth"] = narrative_score

        return adjusted_scores

    def _create_adjustment_summary(
        self, base_scores: dict[str, float], adjusted_scores: dict[str, float], viewpoint_info: dict[str, Any]
    ) -> dict[str, Any]:
        """調整サマリーを作成"""
        adjustments = {}
        for key, base_val in base_scores.items():
            if key in adjusted_scores:
                adjusted_val = adjusted_scores[key]
                if abs(base_val - adjusted_val) > 0.1:
                    adjustments[key] = {
                        "base": base_val,
                        "adjusted": adjusted_val,
                        "change": adjusted_val - base_val,
                    }

        return {
            "viewpoint_type": viewpoint_info.get("視点タイプ", "不明"),
            "complexity_level": viewpoint_info.get("複雑度", "不明"),
            "score_adjustments": adjustments,
            "adjustment_reason": self._get_adjustment_reason(viewpoint_info),
        }

    def _get_adjustment_reason(self, viewpoint_info: dict[str, Any]) -> str:
        """調整理由を取得"""
        viewpoint_type = viewpoint_info.get("視点タイプ", "")

        if "内省型" in viewpoint_type:
            return "内省型エピソードのため会話比率は参考値、内面描写を重視して評価"
        if "身体交換" in viewpoint_type:
            return "身体交換エピソードのため内面描写を重視して評価"
        if "複数視点" in viewpoint_type:
            return "複数視点エピソードのため視点の明確さを重視して評価"
        return "標準的な評価基準を適用"

    def _apply_standard_evaluation(self, base_scores: dict[str, float]) -> dict[str, Any]:
        """標準評価を適用"""
        return {
            "status": "standard_evaluation",
            "adjusted_scores": base_scores,
            "base_scores": base_scores,
            "adjustment_summary": {
                "viewpoint_type": "不明",
                "adjustment_reason": "視点情報が取得できないため標準評価を適用",
            },
        }
