"""適応的品質評価ユースケース(TDD + DDD準拠)"""

from pathlib import Path
from typing import Any, Protocol

from noveler.domain.quality.entities import AdaptiveQualityEvaluator
from noveler.domain.quality.services import QualityAdaptationService
from noveler.domain.quality.value_objects import EvaluationContext, QualityScore


class ModelRepository(Protocol):
    """学習モデルリポジトリのプロトコル"""

    def has_trained_model(self, project_id: str) -> bool:
        """訓練されたモデルが存在するかチェック"""
        ...


class AdaptiveQualityEvaluationUseCase:
    """適応的品質評価ユースケース"""

    def __init__(self, model_repository: ModelRepository, path_service=None) -> None:
        """初期化

        Args:
            model_repository: 学習モデルリポジトリ(依存性注入)
            path_service: パスサービス（B20準拠・DI対応）
        """
        self.model_repository = model_repository
        self.adaptation_service = QualityAdaptationService()
        # B20準拠: path_service依存注入
        self._path_service = path_service

    def evaluate_adaptively(
        self, project_id: str, standard_results: dict[str, Any], episode_file_path: str
    ) -> dict[str, Any]:
        """適応的品質評価を実行

        Args:
            project_id: プロジェクトID
            standard_results: 標準品質チェック結果
            episode_file_path: エピソードファイルパス

        Returns:
            適応的評価結果
        """

        # 学習モデルの可用性チェック
        if not self.model_repository:
            return self._fallback_to_standard(standard_results, "no_learning_model")

        has_model = self.model_repository.has_trained_model(project_id)
        if not has_model:
            return self._fallback_to_standard(standard_results, "no_learning_model")

        try:
            # 適応的評価器の作成
            evaluator = AdaptiveQualityEvaluator(
                evaluator_id=f"adaptive_{project_id}",
                project_id=project_id,
                learning_model_path=self._get_model_path(project_id),
                is_trained=True,
            )

            # 評価コンテキストの構築
            context = self._build_evaluation_context(standard_results, episode_file_path)

            # 適応ポリシーの生成
            policy = self.adaptation_service.generate_project_adaptation(
                learned_evaluator=evaluator,
                episode_count=standard_results.get("episode_number", 1),
                genre="body_swap_fantasy",  # プロジェクト設定から取得
            )

            evaluator.apply_adaptation_policy(policy)

            # 標準スコアの変換
            standard_scores = self._convert_to_quality_scores(standard_results["checks"])

            # 適応的評価の実行
            adapted_scores = evaluator.evaluate_adaptively(standard_scores, context)

            return {
                "adaptive_enabled": True,
                "confidence_level": policy.confidence_threshold,
                "adjusted_scores": self._convert_from_quality_scores(adapted_scores),
                "adaptation_summary": {
                    "policy_id": policy.policy_id,
                    "covered_metrics": policy.get_coverage_metrics(),
                    "adaptation_count": len(policy.adaptations),
                },
            }

        except Exception as e:
            # エラー時は標準評価にフォールバック
            return self._fallback_to_standard(standard_results, f"evaluation_error: {e}")

    def _fallback_to_standard(self, standard_results: dict[str, Any], reason: str) -> dict[str, Any]:
        """標準評価にフォールバック"""
        return {
            "adaptive_enabled": False,
            "fallback_reason": reason,
            "adjusted_scores": standard_results.get("checks", {}),
            "confidence_level": 0.0,
        }

    def _build_evaluation_context(self, standard_results: dict[str, Any], _episode_file_path: str) -> EvaluationContext:
        """評価コンテキストを構築"""
        episode_number = standard_results.get("episode_number", 1)
        chapter_number = (episode_number - 1) // 5 + 1  # 仮の計算

        return EvaluationContext(
            episode_number=episode_number,
            chapter_number=chapter_number,
            genre="body_swap_fantasy",
            viewpoint_type="single_introspective",
        )

    def _convert_to_quality_scores(self, checks: dict[str, Any]) -> dict[str, QualityScore]:
        """チェック結果をQualityScoreに変換"""
        quality_scores = {}

        for check_name, check_result in checks.items():
            if isinstance(check_result, dict) and "score" in check_result:
                score_value = check_result["score"]
                quality_scores[check_name] = QualityScore(float(score_value))
            elif isinstance(check_result, int | float):
                quality_scores[check_name] = QualityScore(float(check_result))

        return quality_scores

    def _convert_from_quality_scores(self, adapted_scores: dict[str, Any]) -> dict[str, Any]:
        """QualityScoreを辞書形式に変換"""
        result = {}

        for metric, score in adapted_scores.items():
            if hasattr(score, "value"):
                result[metric] = {"score": score.value}
            else:
                result[metric] = score

        return result

    def _get_model_path(self, project_id: str) -> str:
        """B20準拠: プロジェクトIDからモデルパスを取得

        Args:
            project_id: プロジェクトID

        Returns:
            モデルファイルパス
        """
        if self._path_service:
            # path_serviceからモデルディレクトリを取得
            models_dir = self._path_service.get_models_dir()
            return str(models_dir / f"{project_id}.pkl")
        # フォールバック: デフォルトパス（将来的にはDI必須化予定）
        return str(Path("models") / f"{project_id}.pkl")
