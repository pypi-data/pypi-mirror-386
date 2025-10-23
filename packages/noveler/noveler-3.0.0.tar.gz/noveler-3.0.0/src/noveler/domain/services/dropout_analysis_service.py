#!/usr/bin/env python3

"""Domain.services.dropout_analysis_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""離脱率分析ドメインサービス(DDD実装)

離脱率計算とデータ検証のビジネスロジック。
"""


from noveler.domain.entities.dropout_analysis_session import (
    CriticalEpisode,
    DropoutRate,
    EpisodeDropout,
    EpisodeMetrics,
)


class DropoutAnalysisService:
    """離脱率分析サービス

    離脱率計算のビジネスロジックを提供。
    """

    def calculate_dropout_rate(self, previous_pv: int, current_pv: int) -> DropoutRate:
        """離脱率を計算

        Args:
            previous_pv: 前話のPV
            current_pv: 現在話のPV

        Returns:
            離脱率
        """
        if previous_pv == 0:
            return DropoutRate(0.0)

        rate = (previous_pv - current_pv) / previous_pv * 100
        return DropoutRate(max(0.0, min(100.0, rate)))  # 0-100の範囲に制限

    def analyze_episode_sequence(
        self,
        metrics_list: list[EpisodeMetrics],
    ) -> list[EpisodeDropout]:
        """エピソードシーケンスから離脱率を分析

        Args:
            metrics_list: エピソードメトリクスのリスト(順序付き)

        Returns:
            エピソード離脱情報のリスト
        """
        dropout_list = []

        for i in range(1, len(metrics_list)):
            current = metrics_list[i]
            previous = metrics_list[i - 1]

            dropout_rate = self.calculate_dropout_rate(
                previous.page_views,
                current.page_views,
            )

            dropout = EpisodeDropout(
                episode_number=current.episode_number,
                episode_title=current.episode_title,
                dropout_rate=dropout_rate,
                current_pv=current.page_views,
                previous_pv=previous.page_views,
            )

            dropout_list.append(dropout)

        return dropout_list

    def calculate_average_dropout(
        self,
        dropouts: list[EpisodeDropout],
    ) -> DropoutRate:
        """平均離脱率を計算

        Args:
            dropouts: エピソード離脱情報のリスト

        Returns:
            平均離脱率
        """
        if not dropouts:
            return DropoutRate(0.0)

        avg_rate = sum(d.dropout_rate.value for d in dropouts) / len(dropouts)
        return DropoutRate(avg_rate)

    def identify_critical_episodes(self, dropouts: list[EpisodeDropout], threshold: float) -> list[CriticalEpisode]:
        """重要な閾値を超えるエピソードを特定

        Args:
            dropouts: エピソード離脱情報のリスト
            threshold: 閾値(デフォルト30%)

        Returns:
            要改善エピソードのリスト
        """
        critical_episodes = []

        for dropout in dropouts:
            if dropout.dropout_rate.value >= threshold:
                critical = CriticalEpisode.from_dropout(dropout)
                critical_episodes.append(critical)

        return critical_episodes


class DataValidationService:
    """データ検証サービス

    KASASAGIデータの品質と完全性を検証。
    """

    def is_valid_metrics(self, metrics: EpisodeMetrics) -> bool:
        """エピソードメトリクスが有効かを判定

        Args:
            metrics: エピソードメトリクス

        Returns:
            有効性
        """
        # PVまたはUAが0の場合は無効(集計中の可能性)
        if metrics.page_views == 0 or metrics.unique_users == 0:
            return False

        # PVがUAより少ない場合は異常
        return not metrics.page_views < metrics.unique_users

    def filter_incomplete_data(
        self,
        metrics_list: list[EpisodeMetrics],
    ) -> list[EpisodeMetrics]:
        """不完全なデータをフィルタ

        KASASAGIの制約により、以下のデータを除外:
        - PV=0のエピソード(集計中)
        - 極端に低いPVのエピソード(閾値: 前話の10%未満)

        Args:
            metrics_list: エピソードメトリクスのリスト

        Returns:
            フィルタ済みリスト
        """
        if not metrics_list:
            return []

        # まずPV=0のデータを除外
        filtered = [m for m in metrics_list if self.is_valid_metrics(m)]

        # 極端な低下を検出して除外
        result = []
        for i, metrics in enumerate(filtered):
            if i == 0:
                result.append(metrics)
                continue

            previous = result[-1] if result else None
            if previous and previous.page_views > 0:
                dropout_rate = (previous.page_views - metrics.page_views) / previous.page_views * 100
                # 90%以上の離脱は集計中の可能性
                if dropout_rate < 90:
                    result.append(metrics)
            else:
                result.append(metrics)

        return result

    def detect_extreme_dropout(
        self, metrics_list: list[EpisodeMetrics], threshold: float = 80.0
    ) -> tuple[bool, list[EpisodeMetrics]]:
        """極端な離脱率を検出

        Args:
            metrics_list: エピソードメトリクスのリスト
            threshold: 極端とみなす離脱率の閾値

        Returns:
            (極端な離脱があるか, 該当エピソードリスト)
        """
        extreme_episodes = []

        for i in range(1, len(metrics_list)):
            current = metrics_list[i]
            previous = metrics_list[i - 1]

            if previous.page_views > 0:
                dropout_rate = (previous.page_views - current.page_views) / previous.page_views * 100
                if dropout_rate >= threshold:
                    extreme_episodes.append(current)

        return len(extreme_episodes) > 0, extreme_episodes

    def get_data_freshness_warning(self) -> str:
        """データ鮮度に関する警告メッセージを取得"""
        return (
            "KASASAGIでは直近2日間のデータは集計中のため表示されません。"
            "最新話数のデータが不正確になる可能性があります。"
        )
