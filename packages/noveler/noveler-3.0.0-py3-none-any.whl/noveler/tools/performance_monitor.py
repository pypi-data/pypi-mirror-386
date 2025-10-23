"""Tools.performance_monitor
Where: Tool monitoring performance metrics.
What: Captures and reports performance data for key operations.
Why: Helps identify regressions and optimise runtime behaviour.
"""

from noveler.presentation.shared.shared_utilities import console

"パフォーマンス監視システム\n\n仕様書: SPEC-PERFORMANCE-MONITOR-001\n品質チェック実行時間とリソース消費の監視\n\n設計原則:\n    - 軽量な監視オーバーヘッド\n- リアルタイム性能測定\n- ボトルネック特定支援\n"
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
import json
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from noveler.infrastructure.logging.unified_logger import get_logger


@dataclass
class PerformanceSnapshot:
    """パフォーマンススナップショット"""

    timestamp: datetime
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    disk_read_mb: float
    disk_write_mb: float
    duration_seconds: float


@dataclass
class PerformanceProfile:
    """パフォーマンスプロファイル"""

    operation_name: str
    start_time: datetime
    end_time: datetime
    total_duration: float
    snapshots: list[PerformanceSnapshot]
    avg_cpu_percent: float
    peak_cpu_percent: float
    avg_memory_mb: float
    peak_memory_mb: float
    total_disk_io_mb: float
    bottleneck_phases: list[str]
    performance_grade: str


class PerformanceMonitor:
    """パフォーマンス監視システム

    責務:
        - リアルタイム性能測定
        - リソース消費監視
        - ボトルネック特定
        - 最適化提案
    """

    def __init__(self, monitoring_interval: float = 0.1, reports_dir: Path | None = None) -> None:
        """初期化

        Args:
            monitoring_interval: 監視間隔（秒）
            reports_dir: レポート出力ディレクトリ
        """
        self.monitoring_interval = monitoring_interval
        self.reports_dir = reports_dir or Path("reports/performance")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger(__name__)
        self._monitoring = False
        self._monitor_thread = None
        self._snapshots = []
        if PSUTIL_AVAILABLE:
            self._process = psutil.Process()
            self._initial_disk_io = self._get_disk_io()
        else:
            self._process = None
            self._initial_disk_io = None
            console.print("psutil未インストール - 基本的な時間測定のみ実行します")

    def start_monitoring(self, operation_name: str) -> None:
        """監視開始

        Args:
            operation_name: 操作名
        """
        self.operation_name = operation_name
        self.start_time = datetime.now(timezone.utc)
        self._snapshots = []
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitor_thread.start()
        console.print(f"パフォーマンス監視開始: {operation_name}")

    def stop_monitoring(self) -> PerformanceProfile:
        """監視停止とプロファイル生成

        Returns:
            パフォーマンスプロファイル
        """
        self._monitoring = False
        self.end_time = datetime.now(timezone.utc)
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1.0)
        profile = self._generate_profile()
        self._save_performance_report(profile)
        console.print(f"パフォーマンス監視完了: {self.operation_name}")
        return profile

    def _monitoring_loop(self) -> None:
        """監視ループ"""
        while self._monitoring:
            try:
                snapshot = self._take_snapshot()
                self._snapshots.append(snapshot)
                time.sleep(self.monitoring_interval)
            except Exception as e:
                console.print(f"監視エラー: {e}")
                break

    def _take_snapshot(self) -> PerformanceSnapshot:
        """パフォーマンススナップショット取得

        Returns:
            パフォーマンススナップショット
        """
        if not PSUTIL_AVAILABLE or not self._process:
            duration = (datetime.now(timezone.utc) - self.start_time).total_seconds()
            return PerformanceSnapshot(
                timestamp=datetime.now(timezone.utc),
                cpu_percent=0.0,
                memory_mb=0.0,
                memory_percent=0.0,
                disk_read_mb=0.0,
                disk_write_mb=0.0,
                duration_seconds=duration,
            )
        try:
            cpu_percent = self._process.cpu_percent()
            memory_info = self._process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            memory_percent = self._process.memory_percent()
            current_disk_io = self._get_disk_io()
            if current_disk_io and self._initial_disk_io:
                disk_read_mb = (current_disk_io.read_bytes - self._initial_disk_io.read_bytes) / (1024 * 1024)
                disk_write_mb = (current_disk_io.write_bytes - self._initial_disk_io.write_bytes) / (1024 * 1024)
            else:
                disk_read_mb = 0.0
                disk_write_mb = 0.0
        except Exception as e:
            console.print(f"リソース取得エラー: {e}")
            cpu_percent = 0.0
            memory_mb = 0.0
            memory_percent = 0.0
            disk_read_mb = 0.0
            disk_write_mb = 0.0
        duration = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        return PerformanceSnapshot(
            timestamp=datetime.now(timezone.utc),
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            memory_percent=memory_percent,
            disk_read_mb=disk_read_mb,
            disk_write_mb=disk_write_mb,
            duration_seconds=duration,
        )

    def _get_disk_io(self) -> Any:
        """ディスクI/O情報取得"""
        if not PSUTIL_AVAILABLE or not self._process:
            return None
        try:
            return self._process.io_counters()
        except Exception:
            try:
                return psutil.disk_io_counters() if PSUTIL_AVAILABLE else None
            except Exception:
                return None

    def _generate_profile(self) -> PerformanceProfile:
        """パフォーマンスプロファイル生成

        Returns:
            パフォーマンスプロファイル
        """
        if not self._snapshots:
            return self._create_empty_profile()
        total_duration = (self.end_time - self.start_time).total_seconds()
        avg_cpu = sum(s.cpu_percent for s in self._snapshots) / len(self._snapshots)
        peak_cpu = max(s.cpu_percent for s in self._snapshots)
        avg_memory = sum(s.memory_mb for s in self._snapshots) / len(self._snapshots)
        peak_memory = max(s.memory_mb for s in self._snapshots)
        last_snapshot = self._snapshots[-1]
        total_disk_io = last_snapshot.disk_read_mb + last_snapshot.disk_write_mb
        bottleneck_phases = self._analyze_bottlenecks()
        performance_grade = self._calculate_performance_grade(total_duration, peak_cpu, peak_memory)
        return PerformanceProfile(
            operation_name=self.operation_name,
            start_time=self.start_time,
            end_time=self.end_time,
            total_duration=total_duration,
            snapshots=self._snapshots,
            avg_cpu_percent=avg_cpu,
            peak_cpu_percent=peak_cpu,
            avg_memory_mb=avg_memory,
            peak_memory_mb=peak_memory,
            total_disk_io_mb=total_disk_io,
            bottleneck_phases=bottleneck_phases,
            performance_grade=performance_grade,
        )

    def _analyze_bottlenecks(self) -> list[str]:
        """ボトルネック分析

        Returns:
            ボトルネック要因リスト
        """
        if not self._snapshots:
            return []
        bottlenecks = []
        high_cpu_snapshots = [s for s in self._snapshots if s.cpu_percent > 80.0]
        if len(high_cpu_snapshots) > len(self._snapshots) * 0.3:
            bottlenecks.append("CPU集約的処理")
        high_memory_snapshots = [s for s in self._snapshots if s.memory_percent > 70.0]
        if len(high_memory_snapshots) > len(self._snapshots) * 0.3:
            bottlenecks.append("メモリ使用量過多")
        final_io = self._snapshots[-1].disk_read_mb + self._snapshots[-1].disk_write_mb
        if final_io > 50.0:
            bottlenecks.append("ディスクI/O集約的処理")
        total_duration = (self.end_time - self.start_time).total_seconds()
        if total_duration > 10.0:
            bottlenecks.append("長時間実行")
        return bottlenecks

    def _calculate_performance_grade(self, duration: float, peak_cpu: float, peak_memory: float) -> str:
        """パフォーマンスグレード算出

        Args:
            duration: 実行時間
            peak_cpu: ピークCPU使用率
            peak_memory: ピークメモリ使用量

        Returns:
            パフォーマンスグレード
        """
        score = 100
        if duration > 30:
            score -= 40
        elif duration > 15:
            score -= 25
        elif duration > 5:
            score -= 10
        if peak_cpu > 90:
            score -= 20
        elif peak_cpu > 70:
            score -= 10
        if peak_memory > 500:
            score -= 15
        elif peak_memory > 200:
            score -= 8
        if score >= 90:
            return "Excellent"
        if score >= 80:
            return "Good"
        if score >= 70:
            return "Average"
        if score >= 60:
            return "Below Average"
        return "Poor"

    def _create_empty_profile(self) -> PerformanceProfile:
        """空のプロファイル生成"""
        return PerformanceProfile(
            operation_name=getattr(self, "operation_name", "Unknown"),
            start_time=getattr(self, "start_time", datetime.now(timezone.utc)),
            end_time=getattr(self, "end_time", datetime.now(timezone.utc)),
            total_duration=0.0,
            snapshots=[],
            avg_cpu_percent=0.0,
            peak_cpu_percent=0.0,
            avg_memory_mb=0.0,
            peak_memory_mb=0.0,
            total_disk_io_mb=0.0,
            bottleneck_phases=[],
            performance_grade="Unknown",
        )

    def _save_performance_report(self, profile: PerformanceProfile) -> None:
        """パフォーマンスレポート保存

        Args:
            profile: パフォーマンスプロファイル
        """
        try:
            timestamp = profile.start_time.strftime("%Y%m%d_%H%M%S")
            report_file = self.reports_dir / f"perf_{profile.operation_name}_{timestamp}.json"
            report_data = {
                "operation_name": profile.operation_name,
                "start_time": profile.start_time.isoformat(),
                "end_time": profile.end_time.isoformat(),
                "total_duration": profile.total_duration,
                "statistics": {
                    "avg_cpu_percent": profile.avg_cpu_percent,
                    "peak_cpu_percent": profile.peak_cpu_percent,
                    "avg_memory_mb": profile.avg_memory_mb,
                    "peak_memory_mb": profile.peak_memory_mb,
                    "total_disk_io_mb": profile.total_disk_io_mb,
                },
                "analysis": {
                    "bottleneck_phases": profile.bottleneck_phases,
                    "performance_grade": profile.performance_grade,
                },
                "snapshots_count": len(profile.snapshots),
                "monitoring_interval": self.monitoring_interval,
            }
            with Path(report_file).open("w", encoding="utf-8") as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            console.print(f"パフォーマンスレポート保存: {report_file}")
        except (OSError, json.JSONEncodeError) as e:
            self.logger.exception("パフォーマンスレポート保存エラー: %s", e)


class PerformanceMonitorContext:
    """パフォーマンス監視コンテキストマネージャー"""

    def __init__(self, operation_name: str, **kwargs) -> None:
        self.operation_name = operation_name
        self.monitor = PerformanceMonitor(**kwargs)
        self.profile = None

    def __enter__(self) -> "PerformanceMonitorContext":
        self.monitor.start_monitoring(self.operation_name)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
        self.profile = self.monitor.stop_monitoring()

    def get_profile(self) -> PerformanceProfile | None:
        """パフォーマンスプロファイル取得"""
        return self.profile


def monitor_performance(operation_name: str, **kwargs) -> PerformanceMonitorContext:
    """パフォーマンス監視コンテキストマネージャー作成

    Args:
        operation_name: 操作名
        **kwargs: PerformanceMonitorの引数

    Returns:
        パフォーマンス監視コンテキストマネージャー

    Example:
        with monitor_performance("ddd_compliance_check") as monitor:
            # 監視対象処理
            pass

        profile = monitor.get_profile()
    """
    return PerformanceMonitorContext(operation_name, **kwargs)
