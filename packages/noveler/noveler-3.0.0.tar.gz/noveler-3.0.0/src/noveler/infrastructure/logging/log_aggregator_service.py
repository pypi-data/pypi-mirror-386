# File: src/noveler/infrastructure/logging/log_aggregator_service.py
# Purpose: Aggregate and analyze logs from multiple sources for insights
# Context: Phase 3 implementation for log aggregation and analysis infrastructure

"""ログ集約・分析サービス

分散されたログを収集し、分析可能な形式に集約する。
メトリクスの計算、異常検出、レポート生成を担当。
"""

import json
import sqlite3
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from noveler.infrastructure.logging.structured_logger import get_structured_logger


@dataclass
class LogEntry:
    """ログエントリのデータクラス"""
    timestamp: float
    level: str
    message: str
    logger_name: str
    extra_data: Dict[str, Any] = field(default_factory=dict)
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    operation: Optional[str] = None
    execution_time_ms: Optional[float] = None
    error_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "message": self.message,
            "logger_name": self.logger_name,
            "extra_data": self.extra_data,
            "request_id": self.request_id,
            "session_id": self.session_id,
            "operation": self.operation,
            "execution_time_ms": self.execution_time_ms,
            "error_type": self.error_type,
        }


@dataclass
class AggregatedMetrics:
    """集約されたメトリクス"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_execution_time_ms: float = 0
    avg_execution_time_ms: float = 0
    max_execution_time_ms: float = 0
    min_execution_time_ms: float = float('inf')
    error_rate: float = 0
    operations: Dict[str, int] = field(default_factory=dict)
    errors_by_type: Dict[str, int] = field(default_factory=dict)
    requests_per_minute: List[int] = field(default_factory=list)


class LogAggregatorService:
    """ログ集約サービス

    複数のログソースから情報を収集し、分析可能な形式で保存。
    SQLiteを使用した永続化とクエリ機能を提供。
    """

    def __init__(self, db_path: Optional[Path] = None):
        """初期化

        Args:
            db_path: SQLiteデータベースのパス（省略時はメモリDB）
        """
        self.logger = get_structured_logger(__name__)
        self.db_path = db_path or ":memory:"
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._initialize_database()

    def _initialize_database(self) -> None:
        """データベース初期化"""
        cursor = self.conn.cursor()

        # ログエントリテーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS log_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                logger_name TEXT NOT NULL,
                request_id TEXT,
                session_id TEXT,
                operation TEXT,
                execution_time_ms REAL,
                error_type TEXT,
                extra_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # インデックス作成
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON log_entries(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_request_id ON log_entries(request_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON log_entries(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_operation ON log_entries(operation)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_level ON log_entries(level)")

        # 集約メトリクステーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS aggregated_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                period_start TIMESTAMP NOT NULL,
                period_end TIMESTAMP NOT NULL,
                total_requests INTEGER DEFAULT 0,
                successful_requests INTEGER DEFAULT 0,
                failed_requests INTEGER DEFAULT 0,
                total_execution_time_ms REAL DEFAULT 0,
                avg_execution_time_ms REAL DEFAULT 0,
                max_execution_time_ms REAL DEFAULT 0,
                min_execution_time_ms REAL DEFAULT 0,
                error_rate REAL DEFAULT 0,
                operations TEXT,
                errors_by_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.commit()

    def add_log_entry(self, entry: LogEntry) -> None:
        """ログエントリを追加

        Args:
            entry: 追加するログエントリ
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO log_entries (
                timestamp, level, message, logger_name,
                request_id, session_id, operation,
                execution_time_ms, error_type, extra_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.timestamp,
            entry.level,
            entry.message,
            entry.logger_name,
            entry.request_id,
            entry.session_id,
            entry.operation,
            entry.execution_time_ms,
            entry.error_type,
            json.dumps(entry.extra_data) if entry.extra_data else None
        ))
        self.conn.commit()

    def bulk_add_log_entries(self, entries: List[LogEntry]) -> None:
        """複数のログエントリを一括追加

        Args:
            entries: 追加するログエントリのリスト
        """
        cursor = self.conn.cursor()
        data = [
            (
                entry.timestamp,
                entry.level,
                entry.message,
                entry.logger_name,
                entry.request_id,
                entry.session_id,
                entry.operation,
                entry.execution_time_ms,
                entry.error_type,
                json.dumps(entry.extra_data) if entry.extra_data else None
            )
            for entry in entries
        ]

        cursor.executemany("""
            INSERT INTO log_entries (
                timestamp, level, message, logger_name,
                request_id, session_id, operation,
                execution_time_ms, error_type, extra_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        self.conn.commit()

        self.logger.info(
            f"一括追加完了: {len(entries)}件のログエントリ",
            extra_data={"count": len(entries)}
        )

    def query_logs(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        level: Optional[str] = None,
        operation: Optional[str] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 100
    ) -> List[LogEntry]:
        """ログをクエリ

        Args:
            start_time: 開始時刻（Unix timestamp）
            end_time: 終了時刻（Unix timestamp）
            level: ログレベル
            operation: 操作名
            request_id: リクエストID
            session_id: セッションID
            limit: 取得件数上限

        Returns:
            条件に一致するログエントリのリスト
        """
        query = "SELECT * FROM log_entries WHERE 1=1"
        params = []

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)

        if level:
            query += " AND level = ?"
            params.append(level)

        if operation:
            query += " AND operation = ?"
            params.append(operation)

        if request_id:
            query += " AND request_id = ?"
            params.append(request_id)

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor = self.conn.cursor()
        cursor.execute(query, params)

        entries = []
        for row in cursor.fetchall():
            extra_data = {}
            if row["extra_data"]:
                try:
                    extra_data = json.loads(row["extra_data"])
                except json.JSONDecodeError:
                    pass

            entries.append(LogEntry(
                timestamp=row["timestamp"],
                level=row["level"],
                message=row["message"],
                logger_name=row["logger_name"],
                extra_data=extra_data,
                request_id=row["request_id"],
                session_id=row["session_id"],
                operation=row["operation"],
                execution_time_ms=row["execution_time_ms"],
                error_type=row["error_type"]
            ))

        return entries

    def calculate_metrics(
        self,
        start_time: float,
        end_time: float
    ) -> AggregatedMetrics:
        """指定期間のメトリクスを計算

        Args:
            start_time: 開始時刻（Unix timestamp）
            end_time: 終了時刻（Unix timestamp）

        Returns:
            集約されたメトリクス
        """
        metrics = AggregatedMetrics()

        cursor = self.conn.cursor()

        # 基本統計
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN error_type IS NULL THEN 1 END) as successful,
                COUNT(CASE WHEN error_type IS NOT NULL THEN 1 END) as failed,
                SUM(execution_time_ms) as total_time,
                AVG(execution_time_ms) as avg_time,
                MAX(execution_time_ms) as max_time,
                MIN(execution_time_ms) as min_time
            FROM log_entries
            WHERE timestamp >= ? AND timestamp <= ?
              AND execution_time_ms IS NOT NULL
        """, (start_time, end_time))

        row = cursor.fetchone()
        if row:
            metrics.total_requests = row["total"] or 0
            metrics.successful_requests = row["successful"] or 0
            metrics.failed_requests = row["failed"] or 0
            metrics.total_execution_time_ms = row["total_time"] or 0
            metrics.avg_execution_time_ms = row["avg_time"] or 0
            metrics.max_execution_time_ms = row["max_time"] or 0
            metrics.min_execution_time_ms = row["min_time"] or float('inf')

            if metrics.total_requests > 0:
                metrics.error_rate = metrics.failed_requests / metrics.total_requests

        # 操作別の集計
        cursor.execute("""
            SELECT operation, COUNT(*) as count
            FROM log_entries
            WHERE timestamp >= ? AND timestamp <= ?
              AND operation IS NOT NULL
            GROUP BY operation
        """, (start_time, end_time))

        for row in cursor.fetchall():
            metrics.operations[row["operation"]] = row["count"]

        # エラータイプ別の集計
        cursor.execute("""
            SELECT error_type, COUNT(*) as count
            FROM log_entries
            WHERE timestamp >= ? AND timestamp <= ?
              AND error_type IS NOT NULL
            GROUP BY error_type
        """, (start_time, end_time))

        for row in cursor.fetchall():
            metrics.errors_by_type[row["error_type"]] = row["count"]

        return metrics

    def generate_report(
        self,
        start_time: float,
        end_time: float,
        format: str = "markdown"
    ) -> str:
        """レポート生成

        Args:
            start_time: 開始時刻（Unix timestamp）
            end_time: 終了時刻（Unix timestamp）
            format: 出力形式（markdown, json）

        Returns:
            レポート文字列
        """
        metrics = self.calculate_metrics(start_time, end_time)

        if format == "json":
            return json.dumps({
                "period": {
                    "start": datetime.fromtimestamp(start_time).isoformat(),
                    "end": datetime.fromtimestamp(end_time).isoformat()
                },
                "metrics": {
                    "total_requests": metrics.total_requests,
                    "successful_requests": metrics.successful_requests,
                    "failed_requests": metrics.failed_requests,
                    "error_rate": metrics.error_rate,
                    "performance": {
                        "avg_time_ms": metrics.avg_execution_time_ms,
                        "max_time_ms": metrics.max_execution_time_ms,
                        "min_time_ms": metrics.min_execution_time_ms,
                        "total_time_ms": metrics.total_execution_time_ms
                    },
                    "operations": metrics.operations,
                    "errors": metrics.errors_by_type
                }
            }, indent=2)

        # Markdown形式
        start_dt = datetime.fromtimestamp(start_time)
        end_dt = datetime.fromtimestamp(end_time)

        report = f"""# ログ分析レポート

## 期間
- 開始: {start_dt.isoformat()}
- 終了: {end_dt.isoformat()}

## サマリー
- 総リクエスト数: {metrics.total_requests:,}
- 成功: {metrics.successful_requests:,}
- 失敗: {metrics.failed_requests:,}
- エラー率: {metrics.error_rate:.1%}

## パフォーマンス
- 平均実行時間: {metrics.avg_execution_time_ms:.2f}ms
- 最大実行時間: {metrics.max_execution_time_ms:.2f}ms
- 最小実行時間: {metrics.min_execution_time_ms:.2f}ms

## 操作別統計
"""
        for operation, count in sorted(metrics.operations.items(), key=lambda x: x[1], reverse=True):
            report += f"- {operation}: {count:,}\n"

        if metrics.errors_by_type:
            report += "\n## エラー分析\n"
            for error_type, count in sorted(metrics.errors_by_type.items(), key=lambda x: x[1], reverse=True):
                report += f"- {error_type}: {count:,}\n"

        return report

    def detect_anomalies(
        self,
        window_minutes: int = 5,
        threshold_factor: float = 2.0
    ) -> List[Dict[str, Any]]:
        """異常検出

        Args:
            window_minutes: 分析ウィンドウ（分）
            threshold_factor: 異常判定の閾値係数

        Returns:
            検出された異常のリスト
        """
        anomalies = []
        current_time = time.time()
        window_seconds = window_minutes * 60

        # 直近のウィンドウと過去のウィンドウを比較
        recent_metrics = self.calculate_metrics(
            current_time - window_seconds,
            current_time
        )

        historical_metrics = self.calculate_metrics(
            current_time - (window_seconds * 7),  # 1週間前の同時間帯
            current_time - (window_seconds * 6)
        )

        # エラー率の異常
        if historical_metrics.error_rate > 0:
            if recent_metrics.error_rate > historical_metrics.error_rate * threshold_factor:
                anomalies.append({
                    "type": "high_error_rate",
                    "severity": "critical",
                    "current_value": recent_metrics.error_rate,
                    "historical_value": historical_metrics.error_rate,
                    "message": f"エラー率が通常の{threshold_factor}倍を超えています"
                })

        # レスポンスタイムの異常
        if historical_metrics.avg_execution_time_ms > 0:
            if recent_metrics.avg_execution_time_ms > historical_metrics.avg_execution_time_ms * threshold_factor:
                anomalies.append({
                    "type": "slow_response",
                    "severity": "warning",
                    "current_value": recent_metrics.avg_execution_time_ms,
                    "historical_value": historical_metrics.avg_execution_time_ms,
                    "message": f"平均実行時間が通常の{threshold_factor}倍を超えています"
                })

        # トラフィックの異常
        if historical_metrics.total_requests > 0:
            traffic_ratio = recent_metrics.total_requests / historical_metrics.total_requests
            if traffic_ratio > threshold_factor:
                anomalies.append({
                    "type": "traffic_spike",
                    "severity": "info",
                    "current_value": recent_metrics.total_requests,
                    "historical_value": historical_metrics.total_requests,
                    "message": f"トラフィックが通常の{traffic_ratio:.1f}倍です"
                })
            elif traffic_ratio < (1 / threshold_factor):
                anomalies.append({
                    "type": "traffic_drop",
                    "severity": "warning",
                    "current_value": recent_metrics.total_requests,
                    "historical_value": historical_metrics.total_requests,
                    "message": f"トラフィックが通常の{traffic_ratio:.1%}まで減少しています"
                })

        return anomalies

    def cleanup_old_logs(self, retention_days: int = 30) -> int:
        """古いログをクリーンアップ

        Args:
            retention_days: 保持期間（日数）

        Returns:
            削除されたログ数
        """
        cutoff_time = time.time() - (retention_days * 24 * 3600)

        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM log_entries WHERE timestamp < ?", (cutoff_time,))
        count = cursor.fetchone()["count"]

        if count > 0:
            cursor.execute("DELETE FROM log_entries WHERE timestamp < ?", (cutoff_time,))
            self.conn.commit()

            self.logger.info(
                f"古いログを削除しました",
                extra_data={
                    "deleted_count": count,
                    "retention_days": retention_days,
                    "cutoff_date": datetime.fromtimestamp(cutoff_time).isoformat()
                }
            )

        return count

    def close(self) -> None:
        """リソースをクリーンアップ"""
        if self.conn:
            self.conn.close()