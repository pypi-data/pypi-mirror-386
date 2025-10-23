#!/usr/bin/env python3
"""プロンプト記録リポジトリ

品質チェックプロンプト記録の永続化・検索・管理を行うリポジトリ。
YAML形式での構造化保存とトレーサビリティ機能を提供。
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any

from noveler.domain.entities.quality_check_prompt_record import QualityCheckPromptRecord
from noveler.domain.value_objects.a31_evaluation_category import A31EvaluationCategory


class PromptRecordRepository(ABC):
    """プロンプト記録リポジトリ抽象基底クラス

    品質チェックプロンプト記録の永続化・検索・管理機能を定義。
    """

    @abstractmethod
    def save_record(self, record: QualityCheckPromptRecord) -> bool:
        """プロンプト記録保存

        Args:
            record: 保存する記録

        Returns:
            bool: 保存成功の場合True
        """

    @abstractmethod
    def find_by_id(self, record_id: str) -> QualityCheckPromptRecord | None:
        """ID指定記録検索

        Args:
            record_id: 記録ID

        Returns:
            Optional[QualityCheckPromptRecord]: 記録（見つからない場合None）
        """

    @abstractmethod
    def find_by_project_and_episode(self, project_name: str, episode_number: int) -> list[QualityCheckPromptRecord]:
        """プロジェクト・エピソード指定記録検索

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号

        Returns:
            list[QualityCheckPromptRecord]: 該当記録リスト
        """

    @abstractmethod
    def find_by_category(
        self, category: A31EvaluationCategory, project_name: str | None = None
    ) -> list[QualityCheckPromptRecord]:
        """カテゴリ指定記録検索

        Args:
            category: チェックカテゴリ
            project_name: プロジェクト名（オプション）

        Returns:
            list[QualityCheckPromptRecord]: 該当記録リスト
        """

    @abstractmethod
    def find_by_date_range(
        self, start_date: datetime, end_date: datetime, project_name: str | None = None
    ) -> list[QualityCheckPromptRecord]:
        """日付範囲指定記録検索

        Args:
            start_date: 開始日時
            end_date: 終了日時
            project_name: プロジェクト名（オプション）

        Returns:
            list[QualityCheckPromptRecord]: 該当記録リスト
        """

    @abstractmethod
    def find_successful_records(
        self, project_name: str | None = None, limit: int | None = None
    ) -> list[QualityCheckPromptRecord]:
        """成功記録検索

        Args:
            project_name: プロジェクト名（オプション）
            limit: 取得件数制限（オプション）

        Returns:
            list[QualityCheckPromptRecord]: 成功記録リスト
        """

    @abstractmethod
    def find_high_impact_records(
        self, min_impact_score: float = 80.0, project_name: str | None = None
    ) -> list[QualityCheckPromptRecord]:
        """高インパクト記録検索

        Args:
            min_impact_score: 最小インパクトスコア
            project_name: プロジェクト名（オプション）

        Returns:
            list[QualityCheckPromptRecord]: 高インパクト記録リスト
        """

    @abstractmethod
    def get_records_statistics(self, project_name: str | None = None, days_back: int = 30) -> dict[str, Any]:
        """記録統計情報取得

        Args:
            project_name: プロジェクト名（オプション）
            days_back: 過去何日分を対象とするか

        Returns:
            dict[str, Any]: 統計情報辞書
        """

    @abstractmethod
    def delete_record(self, record_id: str) -> bool:
        """記録削除

        Args:
            record_id: 削除する記録ID

        Returns:
            bool: 削除成功の場合True
        """

    @abstractmethod
    def cleanup_old_records(self, days_to_keep: int = 90) -> int:
        """古い記録のクリーンアップ

        Args:
            days_to_keep: 保持日数

        Returns:
            int: 削除した記録数
        """


class PromptRecordQueryService:
    """プロンプト記録クエリサービス

    プロンプト記録リポジトリを使用した高度な検索・分析機能を提供。
    """

    def __init__(self, repository: PromptRecordRepository) -> None:
        """初期化

        Args:
            repository: プロンプト記録リポジトリ
        """
        self._repository = repository

    def find_most_effective_prompts(
        self, category: A31EvaluationCategory, project_name: str | None = None, limit: int = 10
    ) -> list[QualityCheckPromptRecord]:
        """最も効果的なプロンプト検索

        Args:
            category: チェックカテゴリ
            project_name: プロジェクト名（オプション）
            limit: 取得件数制限

        Returns:
            list[QualityCheckPromptRecord]: 効果的なプロンプト記録リスト
        """
        records = self._repository.find_by_category(category, project_name)
        successful_records = [r for r in records if r.is_successful_execution()]

        # 効果性スコアでソート
        sorted_records = sorted(successful_records, key=lambda r: r.get_effectiveness_score(), reverse=True)

        return sorted_records[:limit]

    def find_problematic_patterns(
        self, project_name: str | None = None, min_failure_rate: float = 0.3
    ) -> dict[str, Any]:
        """問題パターン検索

        Args:
            project_name: プロジェクト名（オプション）
            min_failure_rate: 最小失敗率

        Returns:
            dict[str, Any]: 問題パターン分析結果
        """
        # 過去30日間の記録を取得
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=30)
        records = self._repository.find_by_date_range(start_date, end_date, project_name)

        if not records:
            return {"patterns": [], "summary": "分析対象記録なし"}

        # カテゴリ別失敗率分析
        category_stats = {}
        for record in records:
            category = record.check_category.value
            if category not in category_stats:
                category_stats[category] = {"total": 0, "failures": 0}

            category_stats[category]["total"] += 1
            if not record.is_successful_execution():
                category_stats[category]["failures"] += 1

        # 問題パターン抽出
        problematic_patterns = []
        for category, stats in category_stats.items():
            failure_rate = stats["failures"] / stats["total"] if stats["total"] > 0 else 0
            if failure_rate >= min_failure_rate:
                problematic_patterns.append(
                    {
                        "category": category,
                        "failure_rate": failure_rate,
                        "total_attempts": stats["total"],
                        "failed_attempts": stats["failures"],
                    }
                )

        # 失敗率でソート
        problematic_patterns.sort(key=lambda p: p["failure_rate"], reverse=True)

        return {
            "patterns": problematic_patterns,
            "total_records": len(records),
            "overall_success_rate": sum(1 for r in records if r.is_successful_execution()) / len(records),
            "analysis_period": f"{start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}",
        }

    def generate_improvement_report(self, project_name: str, days_back: int = 30) -> dict[str, Any]:
        """改善レポート生成

        Args:
            project_name: プロジェクト名
            days_back: 過去何日分を対象とするか

        Returns:
            dict[str, Any]: 改善レポート
        """
        # 統計情報取得
        stats = self._repository.get_records_statistics(project_name, days_back)

        # 最も効果的なプロンプトを各カテゴリごとに取得
        effective_prompts = {}
        for category in A31EvaluationCategory:
            prompts = self.find_most_effective_prompts(category, project_name, 3)
            if prompts:
                effective_prompts[category.value] = [
                    {
                        "record_id": p.record_id,
                        "effectiveness_score": p.get_effectiveness_score(),
                        "template_id": p.prompt_content.template_id,
                        "created_at": p.created_at.isoformat(),
                    }
                    for p in prompts
                ]

        # 問題パターン分析
        problematic_patterns = self.find_problematic_patterns(project_name)

        # 改善提案生成
        improvement_suggestions = self._generate_improvement_suggestions(stats, effective_prompts, problematic_patterns)

        return {
            "project_name": project_name,
            "analysis_period_days": days_back,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "statistics": stats,
            "effective_prompts": effective_prompts,
            "problematic_patterns": problematic_patterns,
            "improvement_suggestions": improvement_suggestions,
        }

    def _generate_improvement_suggestions(
        self,
        stats: dict[str, Any],
        effective_prompts: dict[str, list[dict[str, Any]]],
        problematic_patterns: dict[str, Any],
    ) -> list[str]:
        """改善提案生成

        Args:
            stats: 統計情報
            effective_prompts: 効果的プロンプト情報
            problematic_patterns: 問題パターン情報

        Returns:
            list[str]: 改善提案リスト
        """
        suggestions = []

        # 成功率に基づく提案
        success_rate = stats.get("overall_success_rate", 0)
        if success_rate < 0.8:
            suggestions.append(
                f"全体成功率が{success_rate:.1%}と低めです。効果的なプロンプトテンプレートの活用を推奨します。"
            )

        # 効果的プロンプトの活用提案
        if effective_prompts:
            best_categories = [cat for cat, prompts in effective_prompts.items() if prompts]
            if best_categories:
                suggestions.append(
                    f"高効果プロンプトが確認されたカテゴリ（{', '.join(best_categories[:3])}）の"
                    f"テンプレートを他の分析にも活用してください。"
                )

        # 問題パターンに基づく提案
        if problematic_patterns.get("patterns"):
            problematic_categories = [p["category"] for p in problematic_patterns["patterns"][:2]]
            suggestions.append(
                f"失敗率の高いカテゴリ（{', '.join(problematic_categories)}）について、"
                f"プロンプト設計の見直しを推奨します。"
            )

        # 記録数に基づく提案
        total_records = stats.get("total_records", 0)
        if total_records < 10:
            suggestions.append("記録数が少ないため、より多くの品質チェックを実行して分析精度を向上させてください。")

        return suggestions

    def find_template_usage_stats(self, project_name: str | None = None) -> dict[str, Any]:
        """テンプレート使用統計取得

        Args:
            project_name: プロジェクト名（オプション）

        Returns:
            dict[str, Any]: テンプレート使用統計
        """
        # 過去30日間の記録を取得
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=30)
        records = self._repository.find_by_date_range(start_date, end_date, project_name)

        if not records:
            return {"templates": [], "total_usage": 0}

        # テンプレート別使用統計
        template_stats = {}
        for record in records:
            template_id = record.prompt_content.template_id
            if template_id not in template_stats:
                template_stats[template_id] = {
                    "usage_count": 0,
                    "success_count": 0,
                    "total_effectiveness": 0.0,
                    "categories": set(),
                }

            stats = template_stats[template_id]
            stats["usage_count"] += 1
            stats["categories"].add(record.check_category.value)

            if record.is_successful_execution():
                stats["success_count"] += 1
                stats["total_effectiveness"] += record.get_effectiveness_score()

        # 統計データ整形
        template_usage = []
        for template_id, stats in template_stats.items():
            success_rate = stats["success_count"] / stats["usage_count"] if stats["usage_count"] > 0 else 0
            avg_effectiveness = (
                stats["total_effectiveness"] / stats["success_count"] if stats["success_count"] > 0 else 0
            )

            template_usage.append(
                {
                    "template_id": template_id,
                    "usage_count": stats["usage_count"],
                    "success_rate": success_rate,
                    "average_effectiveness": avg_effectiveness,
                    "categories_used": sorted(stats["categories"]),
                }
            )

        # 使用回数でソート
        template_usage.sort(key=lambda t: t["usage_count"], reverse=True)

        return {
            "templates": template_usage,
            "total_usage": len(records),
            "unique_templates": len(template_stats),
            "analysis_period": f"{start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}",
        }
