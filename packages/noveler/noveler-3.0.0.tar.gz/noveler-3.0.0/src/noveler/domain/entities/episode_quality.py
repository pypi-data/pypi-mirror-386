#!/usr/bin/env python3

"""Domain.entities.episode_quality
Where: Domain entity representing episode quality metrics.
What: Aggregates quality scores, violations, and summaries.
Why: Supports quality reporting and remediation decisions.
"""

from __future__ import annotations

"""エピソード品質管理責務エンティティ

Phase 1 Week 3-4: Episode.py分割 - 品質管理責務の分離実装
責務: 品質スコア管理・品質チェック・課題特定 (40行実装)

仕様書: Episode_Split_Design_Specification.md
"""


from dataclasses import dataclass

from noveler.domain.value_objects.project_time import project_now

# DDD準拠: Domain層はInterface経由でLoggerを取得
# Infrastructure直接依存除去（Phase 4: 契約違反修正）

# Phase 6修正: 完全な循環依存解消のため、全てのEpisode参照を除去
# if TYPE_CHECKING:
    #     from noveler.domain.entities.episode import Episode


"""エピソード品質管理エンティティ

Episode.pyから分離された品質管理責務
DDD原則準拠・Infrastructure依存除去済み
"""

from dataclasses import field
from typing import TYPE_CHECKING

from noveler.domain.interfaces.logger_service import ILoggerService

if TYPE_CHECKING:
    from datetime import datetime

# Phase 6修正: 循環依存解消のため、Episodeの直接参照を除去
# if TYPE_CHECKING:
    #     from noveler.domain.entities.episode import Episode
#     from noveler.domain.value_objects.quality_score import QualityScore


@dataclass
class QualityCheckResult:
    """品質チェック結果"""

    passed: bool
    score: float
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class EpisodeQuality:
    """エピソード品質管理エンティティ（40行・単一責務）"""

    episode_id: str
    logger_service: ILoggerService
    quality_score: float | None = field(default=None)  # Phase 6修正: 循環依存解消のため型をfloatに変更
    last_check_at: datetime | None = field(default=None)

    def is_ready_for_quality_check(self, episode_status: str, episode_content: str) -> bool:
        """品質チェック準備完了か判定

        Phase 6修正: 循環依存解消のため、Episodeオブジェクトではなく必要なプロパティのみ受け取る
        """
        if episode_status not in ["completed", "in_progress"]:
            return False
        if len(episode_content) < 100:  # 最小文字数チェック
            return False
        return True

    def perform_quality_check(
        self, episode_status: str, episode_content: str, episode_title: str, target_words: int
    ) -> QualityCheckResult:
        """品質チェック実行

        Phase 6修正: 循環依存解消のため、Episodeオブジェクトではなく必要なプロパティのみ受け取る
        """
        if not self.is_ready_for_quality_check(episode_status, episode_content):
            return QualityCheckResult(passed=False, score=0.0, issues=["品質チェック準備未完了"])

        # 品質チェックロジック実行
        issues = self._analyze_quality_issues(episode_content, target_words)
        score = self._calculate_quality_score(episode_content, issues)

        self.last_check_at = project_now().datetime
        self.quality_score = score
        self.logger_service.info(f"品質チェック完了: {episode_title}, スコア: {score}")

        return QualityCheckResult(
            passed=score >= 0.7, score=score, issues=issues, recommendations=self._generate_recommendations(issues)
        )

    def _analyze_quality_issues(self, episode_content: str, target_words: int) -> list[str]:
        """品質問題の分析

        Phase 6修正: 循環依存解消のため、Episodeオブジェクトではなく必要なプロパティのみ受け取る
        """
        issues = []
        if len(episode_content) < target_words * 0.8:
            issues.append("文字数不足")
        return issues

    def _calculate_quality_score(self, episode_content: str, issues: list[str]) -> float:
        """品質スコア計算

        Phase 6修正: 循環依存解消のため、Episodeオブジェクトではなく必要なプロパティのみ受け取る
        """
        base_score = 1.0
        penalty = len(issues) * 0.1
        return max(0.0, base_score - penalty)

    def _generate_recommendations(self, issues: list[str]) -> list[str]:
        """改善提案生成"""
        recommendations = []
        for issue in issues:
            if "文字数不足" in issue:
                recommendations.append("コンテンツを追加してください")
        return recommendations

    # Phase 4修正: Infrastructure依存完全除去のため create_with_di() メソッドを削除
    # Application層のDomainEntityFactoryServiceで依存性注入を管理
