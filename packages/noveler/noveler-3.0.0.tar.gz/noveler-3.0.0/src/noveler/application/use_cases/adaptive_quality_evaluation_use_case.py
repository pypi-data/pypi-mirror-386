"""適応的品質評価システム - アプリケーション層

執筆者のレベルとジャンルに応じて品質評価を動的に調整する
"""

from typing import Any, ClassVar, Protocol

from noveler.domain.exceptions.base import DomainException
from noveler.domain.interfaces.settings_repository import (
    ISettingsRepositoryFactory,
)
from noveler.domain.services.quality_standard_factory import QualityStandardFactory
from noveler.domain.services.writer_level_service import WriterLevelService
from noveler.domain.value_objects.quality_standards import Genre, QualityStandard, WriterLevel


class ThresholdProtocol(Protocol):
    """閾値オブジェクトのプロトコル"""

    excellent_score: int
    target_score: int
    minimum_score: int


class AdaptiveQualityEvaluationError(DomainException):
    """適応的品質評価のエラー"""


class AdaptiveQualityEvaluator:
    """適応的品質評価を行うオーケストレーター"""

    # 品質チェック項目の定数
    CHECK_TYPES: ClassVar[list[str]] = ["overall", "readability", "composition", "style", "dialogue", "narrative_depth"]

    # 改善提案の閾値定数
    URGENT_THRESHOLD: ClassVar[int] = 50  # この値未満は緊急改善が必要
    MAX_SUGGESTIONS: ClassVar[int] = 3  # 最大提案数

    # ジャンルマッピング定数
    GENRE_MAPPING: ClassVar[dict[str, Genre]] = {
        "ファンタジー": Genre.FANTASY,
        "恋愛": Genre.ROMANCE,
        "ミステリー": Genre.MYSTERY,
        "SF": Genre.SF,
        "純文学": Genre.LITERARY,
        "ライトノベル": Genre.LIGHT_NOVEL,
        "サスペンス": Genre.MYSTERY,  # エイリアス
        "ホラー": Genre.OTHER,
        "青春": Genre.ROMANCE,  # エイリアス
        "学園": Genre.LIGHT_NOVEL,  # エイリアス
    }

    def __init__(self, project_root: str, settings_factory: ISettingsRepositoryFactory | None = None) -> None:
        """Args:
        project_root: プロジェクトのルートディレクトリ
        """
        if not project_root:
            msg = "プロジェクトルートが指定されていません"
            raise AdaptiveQualityEvaluationError(msg)

        self.project_root = project_root
        try:
            # DDD準拠: インフラ層への直接依存を排除
            if settings_factory is None:
                from noveler.infrastructure.adapters.settings_repository_adapter import get_settings_repository_factory

                settings_factory = get_settings_repository_factory(project_root)

            self.progress_repo = settings_factory.create_writer_progress_repository()
            self.settings_repo = settings_factory.create_project_settings_repository()
            self.level_service = WriterLevelService()
            self.standard_factory = QualityStandardFactory()
        except Exception as e:
            msg = f"初期化に失敗しました: {e}"
            raise AdaptiveQualityEvaluationError(msg) from e

    def evaluate_with_adaptive_standards(
        self,
        quality_scores: dict[str, float],
    ) -> dict[str, Any]:
        """適応的基準で品質を評価

        Args:
            quality_scores: 各品質チェック項目のスコア(0-100)

        Returns:
            評価結果(調整後スコア、レベル、メッセージ等を含む)
        """
        if not quality_scores:
            msg = "品質スコアが提供されていません"
            raise AdaptiveQualityEvaluationError(msg)

        # スコア値の検証
        for key, score in quality_scores.items():
            if not isinstance(score, int | float) or not 0 <= score <= 100:
                msg = f"無効なスコア値: {key}={score} (0-100の範囲で指定してください)"
                raise AdaptiveQualityEvaluationError(msg)

        try:
            # 執筆者レベルの判定
            writer_level = self._determine_writer_level()

            # ジャンルの取得
            genre = self._get_project_genre()

            # 品質基準の生成
            standard = self.standard_factory.create_standard(writer_level, genre)

            # スコアの調整と評価
            adjusted_scores = self._adjust_scores(quality_scores, standard)
            evaluation = self._evaluate_against_standard(adjusted_scores, standard)

            # 総合スコアを一度だけ計算
            overall_score = self._calculate_overall_score(adjusted_scores, standard)

            # 結果の構築
            return {
                "writer_level": writer_level.value,
                "writer_level_description": self.level_service.get_level_description(writer_level),
                "genre": genre.value,
                "original_scores": quality_scores,
                "adjusted_scores": adjusted_scores,
                "overall_score": overall_score,
                "evaluation": evaluation,
                "encouragement": self.level_service.get_encouragement_message(
                    writer_level,
                    overall_score,
                ),
                "thresholds": self._get_current_thresholds(standard),
                "improvement_suggestions": self._generate_improvement_suggestions(
                    adjusted_scores,
                    standard,
                ),
            }
        except Exception as e:
            msg = f"品質評価処理に失敗しました: {e}"
            raise AdaptiveQualityEvaluationError(msg) from e

    def _determine_writer_level(self) -> WriterLevel:
        """執筆者レベルを判定"""
        project_name = self.project_root.split("/")[-1]  # プロジェクト名を抽出
        progress = self.progress_repo.get_writer_progress(project_name)

        completed_episodes = progress.get("completed_episodes", 0)
        quality_history = progress.get("quality_history", [])
        average_score = progress.get("recent_average_quality", 0.0) if quality_history else 0.0

        return self.level_service.determine_level(completed_episodes, average_score)

    def _get_project_genre(self) -> Genre:
        """プロジェクトのジャンルを取得"""
        try:
            project_name = self.project_root.split("/")[-1]  # プロジェクト名を抽出
            genre = self.settings_repo.get_project_genre(project_name)
            if genre:
                return genre

            # 後方互換性のため文字列でも取得を試行
            settings = self.settings_repo.get_project_settings(project_name)
            genre_str = settings.get("genre")
            if not genre_str:
                return Genre.OTHER

            # 大文字小文字を統一して検索
            normalized_genre = genre_str.strip()
            genre = self.GENRE_MAPPING.get(normalized_genre)

            if genre is None:
                # 部分一致で検索
                for key, value in self.GENRE_MAPPING.items():
                    if key in normalized_genre or normalized_genre in key:
                        return value
                return Genre.OTHER

            return genre
        except Exception as e:
            msg = f"ジャンル取得に失敗しました: {e}"
            raise AdaptiveQualityEvaluationError(msg) from e

    def _adjust_scores(
        self,
        scores: dict[str, float],
        standard: QualityStandard,
    ) -> dict[str, float]:
        """重み係数に基づいてスコアを調整"""
        adjusted = {}

        for check_type, score in scores.items():
            weight = standard.get_weight(check_type)
            # 重みが1以下の場合は基準を緩和(スコアを上げる)
            # 重みが1以上の場合は基準を厳格化(スコアを下げる)
            if weight < 1.0:
                # 緩和: スコアを100に近づける
                adjusted[check_type] = score + (100 - score) * (1 - weight)
            else:
                # 厳格化: スコアを減少させる
                adjusted[check_type] = score / weight

        return adjusted

    def _calculate_overall_score(
        self,
        scores: dict[str, float],
        standard: QualityStandard,
    ) -> float:
        """総合スコアを計算"""
        if not scores:
            return 0.0

        # 重み付き平均を計算
        total_weight = 0.0
        weighted_sum = 0.0

        for check_type, score in scores.items():
            weight = standard.get_weight(check_type)
            weighted_sum += score * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _evaluate_against_standard(
        self,
        scores: dict[str, float],
        standard: QualityStandard,
    ) -> dict[str, str]:
        """基準に対する評価を行う"""
        evaluation = {}

        # 各項目の評価
        for check_type, score in scores.items():
            threshold = standard.get_threshold(check_type)
            evaluation[check_type] = self._get_evaluation_label(score, threshold)

        # 総合評価 - 事前に計算済みのスコアを使用
        overall_score = self._calculate_overall_score(scores, standard)
        overall_threshold = standard.get_threshold("overall")
        evaluation["overall"] = self._get_evaluation_label(overall_score, overall_threshold)

        return evaluation

    def _get_evaluation_label(self, score: float, threshold: ThresholdProtocol) -> str:
        """スコアと閾値から評価ラベルを取得"""
        if score >= threshold.excellent_score:
            return "優秀"
        if score >= threshold.target_score:
            return "良好"
        if score >= threshold.minimum_score:
            return "合格"
        return "要改善"

    def _get_current_thresholds(self, standard: QualityStandard) -> dict[str, dict[str, int]]:
        """現在の閾値を取得"""
        thresholds = {}

        for check_type in self.CHECK_TYPES:
            threshold = standard.get_threshold(check_type)
            thresholds[check_type] = {
                "minimum": threshold.minimum_score,
                "target": threshold.target_score,
                "excellent": threshold.excellent_score,
            }

        return thresholds

    def _generate_improvement_suggestions(
        self,
        scores: dict[str, float],
        standard: QualityStandard,
    ) -> list[dict[str, Any]]:
        """改善提案を生成"""
        suggestions = []

        # スコアが低い項目から改善提案
        for check_type, score in sorted(scores.items(), key=lambda x: x[1]):
            threshold = standard.get_threshold(check_type)

            if score < threshold.target_score:
                suggestion = self._get_improvement_suggestion(check_type, score)
                if suggestion:
                    suggestions.append({"area": check_type, "current_score": score, "suggestion": suggestion})

        # 最大提案数に限定
        return suggestions[: self.MAX_SUGGESTIONS]

    def _get_improvement_suggestion(self, check_type: str, score: float) -> str | None:
        """具体的な改善提案を取得"""
        base_suggestions = {
            "readability": "短い文と長い文を交互に配置し、リズムを作りましょう。",
            "composition": "段落の長さを調整し、場面転換を明確にしましょう。",
            "style": "文末の変化を増やし、体言止めや疑問形も活用しましょう。",
            "dialogue": "地の文と会話のバランスを見直し、キャラクターの個性を出しましょう。",
            "narrative_depth": "五感を使った描写や、登場人物の内面を深く掘り下げましょう。",
        }

        suggestion = base_suggestions.get(check_type, "品質向上のため、基礎を見直しましょう。")

        # スコアが特に低い場合は緊急度を追加
        if score < self.URGENT_THRESHOLD:
            suggestion = f"[緊急] {suggestion}"

        return suggestion
