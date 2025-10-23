# File: src/noveler/infrastructure/logging/log_analyzer.py
# Purpose: Analyze aggregated logs for patterns, performance issues, and insights
# Context: Phase 3 log analysis utilities for debugging and optimization

"""ログ分析ユーティリティ

集約されたログデータを分析し、パターン認識、
パフォーマンス問題の特定、最適化提案を行う。
"""

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from noveler.infrastructure.logging.log_aggregator_service import LogEntry


@dataclass
class PerformanceBottleneck:
    """パフォーマンスボトルネック情報"""
    operation: str
    avg_time_ms: float
    p95_time_ms: float
    p99_time_ms: float
    frequency: int
    impact_score: float  # 頻度 × 平均時間
    recommendations: List[str]


@dataclass
class ErrorPattern:
    """エラーパターン情報"""
    error_type: str
    frequency: int
    affected_operations: List[str]
    sample_messages: List[str]
    first_occurrence: float
    last_occurrence: float
    trend: str  # increasing, decreasing, stable


@dataclass
class UserSessionAnalysis:
    """ユーザーセッション分析"""
    session_id: str
    duration_seconds: float
    request_count: int
    error_count: int
    operations_performed: List[str]
    avg_response_time_ms: float
    successful: bool


class LogAnalyzer:
    """ログ分析クラス

    ログデータから有用な洞察を抽出し、
    パフォーマンス改善と問題解決の提案を行う。
    """

    def __init__(self):
        """初期化"""
        self.performance_thresholds = {
            "fast": 100,      # 100ms以下
            "normal": 500,    # 500ms以下
            "slow": 1000,     # 1000ms以下
            "very_slow": 3000 # 3000ms以上
        }

    def analyze_performance_bottlenecks(
        self,
        logs: List[LogEntry],
        min_frequency: int = 10
    ) -> List[PerformanceBottleneck]:
        """パフォーマンスボトルネックを分析

        Args:
            logs: ログエントリのリスト
            min_frequency: 分析対象とする最小頻度

        Returns:
            ボトルネックのリスト（影響度順）
        """
        operation_times = defaultdict(list)

        for log in logs:
            if log.operation and log.execution_time_ms is not None:
                operation_times[log.operation].append(log.execution_time_ms)

        bottlenecks = []

        for operation, times in operation_times.items():
            if len(times) < min_frequency:
                continue

            times_array = np.array(times)
            avg_time = np.mean(times_array)
            p95_time = np.percentile(times_array, 95)
            p99_time = np.percentile(times_array, 99)
            frequency = len(times)
            impact_score = frequency * avg_time

            recommendations = self._generate_performance_recommendations(
                operation, avg_time, p95_time, p99_time
            )

            bottlenecks.append(PerformanceBottleneck(
                operation=operation,
                avg_time_ms=avg_time,
                p95_time_ms=p95_time,
                p99_time_ms=p99_time,
                frequency=frequency,
                impact_score=impact_score,
                recommendations=recommendations
            ))

        # 影響度スコアで降順ソート
        bottlenecks.sort(key=lambda x: x.impact_score, reverse=True)
        return bottlenecks

    def _generate_performance_recommendations(
        self,
        operation: str,
        avg_time: float,
        p95_time: float,
        p99_time: float
    ) -> List[str]:
        """パフォーマンス改善の提案を生成

        Args:
            operation: 操作名
            avg_time: 平均実行時間
            p95_time: 95パーセンタイル
            p99_time: 99パーセンタイル

        Returns:
            改善提案のリスト
        """
        recommendations = []

        # 絶対的な遅さ
        if avg_time > self.performance_thresholds["very_slow"]:
            recommendations.append("⚠️ 非常に遅い処理です。アーキテクチャの見直しを検討してください")
        elif avg_time > self.performance_thresholds["slow"]:
            recommendations.append("処理時間が長いです。非同期処理やキャッシュの導入を検討してください")

        # ばらつきが大きい
        if p99_time > avg_time * 3:
            recommendations.append("実行時間のばらつきが大きいです。外部依存やI/Oを確認してください")

        # 特定パターンの検出
        if "llm" in operation.lower() or "claude" in operation.lower():
            recommendations.append("LLM呼び出しです。プロンプト最適化やレスポンスキャッシュを検討してください")

        if "database" in operation.lower() or "query" in operation.lower():
            recommendations.append("データベース操作です。インデックスやクエリ最適化を確認してください")

        if "file" in operation.lower() or "io" in operation.lower():
            recommendations.append("ファイルI/O操作です。バッファリングやバッチ処理を検討してください")

        return recommendations

    def analyze_error_patterns(
        self,
        logs: List[LogEntry],
        time_window_seconds: float = 3600
    ) -> List[ErrorPattern]:
        """エラーパターンを分析

        Args:
            logs: ログエントリのリスト
            time_window_seconds: トレンド分析の時間窓（秒）

        Returns:
            エラーパターンのリスト
        """
        error_groups = defaultdict(lambda: {
            "logs": [],
            "operations": set(),
            "messages": []
        })

        for log in logs:
            if log.error_type:
                error_groups[log.error_type]["logs"].append(log)
                if log.operation:
                    error_groups[log.error_type]["operations"].add(log.operation)
                error_groups[log.error_type]["messages"].append(log.message)

        patterns = []

        for error_type, data in error_groups.items():
            if not data["logs"]:
                continue

            timestamps = [log.timestamp for log in data["logs"]]
            first_occurrence = min(timestamps)
            last_occurrence = max(timestamps)

            # トレンド分析
            trend = self._analyze_error_trend(timestamps, time_window_seconds)

            # サンプルメッセージ（最大5件、重複排除）
            unique_messages = list(set(data["messages"]))[:5]

            patterns.append(ErrorPattern(
                error_type=error_type,
                frequency=len(data["logs"]),
                affected_operations=list(data["operations"]),
                sample_messages=unique_messages,
                first_occurrence=first_occurrence,
                last_occurrence=last_occurrence,
                trend=trend
            ))

        # 頻度で降順ソート
        patterns.sort(key=lambda x: x.frequency, reverse=True)
        return patterns

    def _analyze_error_trend(
        self,
        timestamps: List[float],
        window_seconds: float
    ) -> str:
        """エラーのトレンドを分析

        Args:
            timestamps: エラー発生時刻のリスト
            window_seconds: 分析窓の秒数

        Returns:
            トレンド（increasing, decreasing, stable）
        """
        if len(timestamps) < 2:
            return "stable"

        timestamps.sort()
        mid_point = timestamps[len(timestamps) // 2]

        recent_count = sum(1 for t in timestamps if t > mid_point)
        older_count = sum(1 for t in timestamps if t <= mid_point)

        if recent_count > older_count * 1.5:
            return "increasing"
        elif recent_count < older_count * 0.67:
            return "decreasing"
        else:
            return "stable"

    def analyze_user_sessions(
        self,
        logs: List[LogEntry]
    ) -> List[UserSessionAnalysis]:
        """ユーザーセッション分析

        Args:
            logs: ログエントリのリスト

        Returns:
            セッション分析結果のリスト
        """
        sessions = defaultdict(lambda: {
            "logs": [],
            "operations": [],
            "errors": 0,
            "total_time": 0,
            "request_count": 0
        })

        for log in logs:
            if log.session_id:
                session_data = sessions[log.session_id]
                session_data["logs"].append(log)

                if log.operation:
                    session_data["operations"].append(log.operation)

                if log.error_type:
                    session_data["errors"] += 1

                if log.execution_time_ms:
                    session_data["total_time"] += log.execution_time_ms
                    session_data["request_count"] += 1

        analyses = []

        for session_id, data in sessions.items():
            if not data["logs"]:
                continue

            timestamps = [log.timestamp for log in data["logs"]]
            duration_seconds = max(timestamps) - min(timestamps) if len(timestamps) > 1 else 0

            avg_response_time = (
                data["total_time"] / data["request_count"]
                if data["request_count"] > 0 else 0
            )

            analyses.append(UserSessionAnalysis(
                session_id=session_id,
                duration_seconds=duration_seconds,
                request_count=len(data["logs"]),
                error_count=data["errors"],
                operations_performed=data["operations"],
                avg_response_time_ms=avg_response_time,
                successful=data["errors"] == 0
            ))

        # セッション時間で降順ソート
        analyses.sort(key=lambda x: x.duration_seconds, reverse=True)
        return analyses

    def find_correlated_events(
        self,
        logs: List[LogEntry],
        time_threshold_seconds: float = 1.0
    ) -> List[Tuple[str, str, int]]:
        """相関のあるイベントを検出

        Args:
            logs: ログエントリのリスト
            time_threshold_seconds: 相関と見なす時間閾値

        Returns:
            (イベント1, イベント2, 共起回数)のタプルのリスト
        """
        # タイムスタンプでソート
        sorted_logs = sorted(logs, key=lambda x: x.timestamp)

        event_pairs = []

        for i in range(len(sorted_logs) - 1):
            log1 = sorted_logs[i]
            log2 = sorted_logs[i + 1]

            # 時間閾値内のイベントペアを記録
            if log2.timestamp - log1.timestamp <= time_threshold_seconds:
                if log1.operation and log2.operation:
                    event_pairs.append((log1.operation, log2.operation))

        # 頻度カウント
        pair_counts = Counter(event_pairs)

        # 頻度順にソート
        correlated = [
            (pair[0], pair[1], count)
            for pair, count in pair_counts.items()
            if count >= 3  # 最低3回以上の共起
        ]

        correlated.sort(key=lambda x: x[2], reverse=True)
        return correlated

    def generate_optimization_report(
        self,
        logs: List[LogEntry]
    ) -> str:
        """最適化レポートを生成

        Args:
            logs: ログエントリのリスト

        Returns:
            Markdown形式のレポート
        """
        # 各種分析を実行
        bottlenecks = self.analyze_performance_bottlenecks(logs)
        error_patterns = self.analyze_error_patterns(logs)
        sessions = self.analyze_user_sessions(logs)
        correlations = self.find_correlated_events(logs)

        report = """# ログ分析・最適化レポート

## 📊 概要統計
"""
        # 基本統計
        total_logs = len(logs)
        error_logs = sum(1 for log in logs if log.error_type)
        error_rate = (error_logs / total_logs * 100) if total_logs > 0 else 0

        report += f"""- 総ログ数: {total_logs:,}
- エラー数: {error_logs:,}
- エラー率: {error_rate:.1f}%

## ⚡ パフォーマンスボトルネック

"""
        if bottlenecks:
            report += "| 操作 | 平均時間 | P95 | P99 | 頻度 | 影響度 |\n"
            report += "|------|----------|-----|-----|------|--------|\n"

            for b in bottlenecks[:10]:  # 上位10件
                report += (
                    f"| {b.operation} | "
                    f"{b.avg_time_ms:.1f}ms | "
                    f"{b.p95_time_ms:.1f}ms | "
                    f"{b.p99_time_ms:.1f}ms | "
                    f"{b.frequency} | "
                    f"{b.impact_score:.0f} |\n"
                )

                if b.recommendations:
                    report += f"\n**推奨事項:**\n"
                    for rec in b.recommendations:
                        report += f"- {rec}\n"
                    report += "\n"
        else:
            report += "パフォーマンスボトルネックは検出されませんでした。\n\n"

        report += """## 🔥 エラーパターン

"""
        if error_patterns:
            for pattern in error_patterns[:5]:  # 上位5件
                trend_icon = {
                    "increasing": "📈",
                    "decreasing": "📉",
                    "stable": "➡️"
                }.get(pattern.trend, "")

                report += f"""### {pattern.error_type} {trend_icon}
- 発生回数: {pattern.frequency}
- トレンド: {pattern.trend}
- 影響を受ける操作: {', '.join(pattern.affected_operations[:5])}

"""
        else:
            report += "エラーパターンは検出されませんでした。\n\n"

        report += """## 👥 セッション分析

"""
        if sessions:
            successful_sessions = sum(1 for s in sessions if s.successful)
            success_rate = (successful_sessions / len(sessions) * 100) if sessions else 0

            report += f"""- 総セッション数: {len(sessions)}
- 成功率: {success_rate:.1f}%
- 平均セッション時間: {np.mean([s.duration_seconds for s in sessions]):.1f}秒

"""

        report += """## 🔗 相関イベント

"""
        if correlations:
            report += "頻繁に連続して発生するイベントペア:\n\n"
            for event1, event2, count in correlations[:5]:
                report += f"- {event1} → {event2} ({count}回)\n"
        else:
            report += "相関イベントは検出されませんでした。\n"

        return report