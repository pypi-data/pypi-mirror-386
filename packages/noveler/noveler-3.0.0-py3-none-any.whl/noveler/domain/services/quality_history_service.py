"""Domain.services.quality_history_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""
SPEC-QUALITY-002: 品質履歴管理サービス

品質履歴の管理と分析を行うドメインサービス。
DDD設計に基づくビジネスロジックの実装。
"""


from typing import TYPE_CHECKING, Any

from noveler.domain.services.quality_history_value_objects import (
    AnalysisPeriod,
    ImprovementPattern,
    ImprovementRate,
    QualityAnalysisSummary,
    QualityHistory,
    QualityTrendAnalysis,
    TrendDirection,
)
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.value_objects.quality_score import QualityScore

if TYPE_CHECKING:
    from noveler.domain.repositories.quality_history_repository import QualityHistoryRepository
    from noveler.domain.value_objects.episode_number import EpisodeNumber

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class QualityHistoryService:
    """品質履歴管理ドメインサービス"""

    def __init__(self, repository: QualityHistoryRepository, analyzer: object) -> None:
        """初期化

        Args:
            repository: 品質履歴リポジトリ
            analyzer: 品質トレンド分析器
        """
        self._repository = repository
        self._analyzer = analyzer

    def record_quality_check(self, episode_number: EpisodeNumber, record: object) -> None:
        """品質チェック結果を記録

        Args:
            episode_number: エピソード番号
            record: 品質記録
        """
        # 既存履歴を取得または新規作成
        existing_history = self._repository.find_by_episode(episode_number)

        if existing_history:
            # 既存履歴に追加
            updated_records = [*existing_history.history_records, record]
            updated_history = QualityHistory(
                episode_number=episode_number,
                history_records=updated_records,
                analysis_summary=self._generate_analysis_summary(updated_records),
                created_at=existing_history.created_at,
            )

        else:
            # 新規履歴作成
            updated_history = QualityHistory(
                episode_number=episode_number,
                history_records=[record],
                analysis_summary=self._generate_analysis_summary([record]),
                created_at=project_now().datetime,
            )

        self._repository.save_history(updated_history)

    def analyze_improvement_trend(
        self, episode_number: EpisodeNumber, period: AnalysisPeriod
    ) -> QualityTrendAnalysis | None:
        """改善トレンドを分析

        Args:
            episode_number: エピソード番号
            period: 分析期間

        Returns:
            トレンド分析結果、データ不足の場合はNone
        """
        history = self._repository.find_by_episode(episode_number)
        if not history:
            return None

        return history.get_trend_analysis(period)

    def extract_learning_patterns(self, history: QualityHistory, min_occurrences: int = 2) -> list[ImprovementPattern]:
        """学習パターンを抽出

        Args:
            history: 品質履歴
            min_occurrences: 最小出現回数

        Returns:
            改善パターンのリスト
        """
        if not history.history_records:
            return []

        # 改善提案の出現頻度を分析
        suggestion_frequency = {}
        suggestion_effectiveness = {}

        records = sorted(history.history_records, key=self._record_sort_key)

        for i, record in enumerate(records):
            for suggestion in record.improvement_suggestions:
                # 出現頻度をカウント
                suggestion_frequency[suggestion] = suggestion_frequency.get(suggestion, 0) + 1

                # 効果性を評価(その後のスコア改善から)
                if i < len(records) - 1:
                    current_score = record.overall_score.value
                    next_score = records[i + 1].overall_score.value
                    improvement = max(0, next_score - current_score)

                    if suggestion not in suggestion_effectiveness:
                        suggestion_effectiveness[suggestion] = []
                    suggestion_effectiveness[suggestion].append(improvement)

        # パターン生成
        patterns = []
        pattern_id = 1

        for suggestion, frequency in suggestion_frequency.items():
            if frequency >= min_occurrences:
                effectiveness_scores = suggestion_effectiveness.get(suggestion, [0])
                avg_effectiveness = sum(effectiveness_scores) / len(effectiveness_scores)

                # 効果性スコアを0-1範囲に正規化
                effectiveness_score = min(1.0, avg_effectiveness / 10.0)

                pattern = ImprovementPattern(
                    pattern_id=f"pattern_{pattern_id:03d}",
                    problem_type=self._categorize_suggestion(suggestion),
                    successful_solutions=[suggestion],
                    effectiveness_score=effectiveness_score,
                    usage_frequency=frequency,
                )

                patterns.append(pattern)
                pattern_id += 1

        # 効果性スコア順にソート
        patterns.sort(key=lambda p: p.effectiveness_score, reverse=True)

        return patterns

    def generate_personalized_guidance(self, history: QualityHistory, writer_level: str) -> dict[str, Any]:
        """個人化された指導を生成

        Args:
            history: 品質履歴
            writer_level: 執筆者レベル(beginner, intermediate, advanced)

        Returns:
            個人化指導情報
        """
        if not history.history_records:
            return {"guidance": "まずは品質チェックを実行してデータを蓄積しましょう"}

        # 最新のトレンド分析
        trend_analysis = history.get_trend_analysis(AnalysisPeriod.LAST_30_DAYS)

        # 学習パターン抽出
        patterns = self.extract_learning_patterns(history)

        # レベル別指導生成
        guidance = {
            "level": writer_level,
            "current_trend": trend_analysis.get_trend_summary(),
            "focus_areas": [],
            "recommended_actions": [],
            "improvement_patterns": [],
        }

        # 弱点領域の特定
        weak_areas = self._safe_list(self._analyzer, "identify_weak_areas", history.history_records)

        if writer_level == "beginner":
            guidance["focus_areas"] = weak_areas[:2]  # 最も重要な2つに絞る
            guidance["recommended_actions"] = [
                "基本的な文法と表現を重点的に改善",
                "一つずつ着実に改善することを心がける",
            ]
        elif writer_level == "intermediate":
            guidance["focus_areas"] = weak_areas[:3]
            guidance["recommended_actions"] = ["複数の改善点を並行して取り組む", "品質チェックの頻度を上げる"]
        else:  # advanced
            guidance["focus_areas"] = weak_areas
            guidance["recommended_actions"] = ["細かな表現技法の向上", "読者層に合わせた文体の調整"]

        # 効果的なパターンを推奨
        guidance["improvement_patterns"] = [
            {
                "problem": pattern.problem_type,
                "solution": pattern.successful_solutions[0],
                "effectiveness": f"{pattern.effectiveness_score:.1%}",
            }
            for pattern in patterns[:3]  # 上位3つ
        ]

        return guidance

    def get_quality_history(self, episode_number: EpisodeNumber) -> QualityHistory | None:
        """品質履歴を取得

        Args:
            episode_number: エピソード番号

        Returns:
            品質履歴、存在しない場合はNone
        """
        return self._repository.find_by_episode(episode_number)

    def calculate_improvement_rate(self, history: QualityHistory) -> ImprovementRate:
        """改善率を計算

        Args:
            history: 品質履歴

        Returns:
            改善率情報
        """
        return history.get_improvement_rate()

    def _generate_analysis_summary(self, records: list[Any]) -> QualityAnalysisSummary:
        """分析サマリーを生成"""
        if not records:
            return QualityAnalysisSummary(
                total_checks=0,
                average_score=QualityScore(0),
                improvement_trend=TrendDirection.UNKNOWN,
                most_improved_category=None,
                most_problematic_category=None,
                recent_improvement_rate=0.0,
            )

        # 平均スコア計算
        total_score = sum(record.overall_score.value for record in records)
        average_score = QualityScore(int(total_score / len(records)))

        # 改善トレンド判定
        improvement_rate = self._safe_float(self._analyzer, "calculate_improvement_rate", records)
        if improvement_rate > 5.0:
            trend = TrendDirection.IMPROVING
        elif improvement_rate < -5.0:
            trend = TrendDirection.DECLINING
        else:
            trend = TrendDirection.STABLE

        # カテゴリ分析
        weak_areas = self._safe_list(self._analyzer, "identify_weak_areas", records)
        category_trends = self._safe_mapping(self._analyzer, "analyze_category_trends", records)

        most_improved = None
        most_problematic = None

        if category_trends:
            # 最も改善したカテゴリ
            best_category = max(category_trends.keys(), key=lambda k: category_trends[k].improvement_rate)
            if category_trends[best_category].improvement_rate > 0:
                most_improved = best_category

            # 最も問題のあるカテゴリ
            if weak_areas:
                most_problematic = weak_areas[0]

        return QualityAnalysisSummary(
            total_checks=len(records),
            average_score=average_score,
            improvement_trend=trend,
            most_improved_category=most_improved,
            most_problematic_category=most_problematic,
            recent_improvement_rate=improvement_rate,
        )

    def _categorize_suggestion(self, suggestion: str) -> str:
        """改善提案をカテゴリ分類"""
        # 簡単なキーワードベースの分類
        suggestion_lower = suggestion.lower()

        if any(word in suggestion_lower for word in ["文法", "語法", "表記"]):
            return "文法・表記"
        if any(word in suggestion_lower for word in ["描写", "表現", "比喩"]):
            return "表現技法"
        if any(word in suggestion_lower for word in ["構成", "構造", "流れ"]):
            return "文章構成"
        if any(word in suggestion_lower for word in ["読みやすさ", "理解", "明確"]):
            return "読みやすさ"
        return "その他"

    @staticmethod
    def _record_sort_key(record: Any) -> Any:
        """品質記録のソートキーを取得"""
        return getattr(record, "timestamp", getattr(record, "created_at", project_now().datetime))

    def _safe_float(self, analyzer: object, method: str, *args: Any) -> float:
        """分析器呼び出しを安全に実行"""
        func = getattr(analyzer, method, None)
        if callable(func):
            result = func(*args)
            try:
                return float(result)
            except (TypeError, ValueError):
                return 0.0
        return 0.0

    def _safe_list(self, analyzer: object, method: str, *args: Any) -> list[Any]:
        """分析器呼び出しの結果をリスト化"""
        func = getattr(analyzer, method, None)
        if callable(func):
            result = func(*args)
            if result is None:
                return []
            if isinstance(result, list):
                return result
            try:
                return list(result)
            except TypeError:
                return []
        return []

    def _safe_mapping(self, analyzer: object, method: str, *args: Any) -> dict[str, Any]:
        """分析器呼び出しの結果を辞書化"""
        func = getattr(analyzer, method, None)
        if callable(func):
            result = func(*args)
            if isinstance(result, dict):
                return result
            return {}
        return {}
