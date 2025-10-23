"""層間違反検出器

仕様書: SPEC-DDD-AUTO-COMPLIANCE-001
インフラ層直接依存検出とリアルタイムアラート実装
"""

import ast
import asyncio
import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
from noveler.infrastructure.logging.unified_logger import get_logger
from noveler.infrastructure.services.ddd_compliance_engine import DDDComplianceEngine, DDDViolation, ViolationSeverity
from noveler.presentation.shared.shared_utilities import console

if TYPE_CHECKING:
    from collections.abc import Callable


class AlertLevel(Enum):
    """アラートレベル"""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class NotificationChannel(Enum):
    """通知チャネル"""

    CONSOLE = "console"
    LOG_FILE = "log_file"
    IDE_INTEGRATION = "ide_integration"
    WEBHOOK = "webhook"


@dataclass
class ViolationAlert:
    """違反アラート"""

    timestamp: datetime
    alert_level: AlertLevel
    violation: DDDViolation
    suggested_fix: str
    auto_fixable: bool
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertConfiguration:
    """アラート設定"""

    enabled_channels: list[NotificationChannel]
    min_alert_level: AlertLevel
    immediate_block_levels: list[AlertLevel]
    sound_enabled: bool = True
    color_coding: bool = True
    auto_fix_enabled: bool = False
    debounce_seconds: int = 2


class FileChangeHandler(FileSystemEventHandler):
    """ファイル変更ハンドラー"""

    def __init__(self, violation_detector: "LayerViolationDetector") -> None:
        self.violation_detector = violation_detector
        self.logger = get_logger(__name__)
        self._last_check_time = {}
        self._debounce_delay = 1.0

    def on_modified(self, event) -> None:
        """ファイル変更時の処理"""
        if event.is_directory:
            return
        file_path = Path(event.src_path)
        if file_path.suffix != ".py":
            return
        current_time = time.time()
        last_check = self._last_check_time.get(str(file_path), 0)
        if current_time - last_check < self._debounce_delay:
            return
        self._last_check_time[str(file_path)] = current_time
        asyncio.create_task(self.violation_detector.check_file_real_time(file_path))


class LayerViolationDetector:
    """層間違反検出器

    責務:
        - リアルタイムファイル監視
        - インフラ層直接依存検出
        - 即座のアラート通知
        - 自動修正提案
        - IDE統合サポート

    設計原則:
        - 低レイテンシー検出
        - 開発者フレンドリーな通知
        - 拡張可能なアラート設定
    """

    def __init__(self, project_root: Path, alert_config: AlertConfiguration | None = None) -> None:
        """初期化

        Args:
            project_root: プロジェクトルートパス
            alert_config: アラート設定
        """
        self.project_root = project_root
        self.alert_config = alert_config or AlertConfiguration(
            enabled_channels=[NotificationChannel.CONSOLE, NotificationChannel.LOG_FILE],
            min_alert_level=AlertLevel.MEDIUM,
            immediate_block_levels=[AlertLevel.CRITICAL, AlertLevel.HIGH],
            sound_enabled=True,
            color_coding=True,
        )
        self.logger = get_logger(__name__)
        self.compliance_engine = DDDComplianceEngine(project_root)
        self.observer = None
        self.monitoring_active = False
        self.alert_history: list[ViolationAlert] = []
        self.notification_callbacks: dict[NotificationChannel, Callable] = {}
        self.stats = {"files_checked": 0, "violations_detected": 0, "alerts_sent": 0, "auto_fixes_applied": 0}
        self._initialize_notification_handlers()

    def _initialize_notification_handlers(self) -> None:
        """通知ハンドラーの初期化"""
        self.notification_callbacks = {
            NotificationChannel.CONSOLE: self._send_console_notification,
            NotificationChannel.LOG_FILE: self._send_log_notification,
            NotificationChannel.IDE_INTEGRATION: self._send_ide_notification,
        }

    async def start_real_time_monitoring(self) -> None:
        """リアルタイム監視開始"""
        if not WATCHDOG_AVAILABLE:
            console.print("watchdogパッケージが利用できません。リアルタイム監視は無効です")
            return
        if self.monitoring_active:
            console.print("リアルタイム監視は既に開始されています")
            return
        console.print("リアルタイム層間違反監視を開始します")
        event_handler = FileChangeHandler(self)
        self.observer = Observer()
        scripts_dir = self.project_root / "scripts"
        if scripts_dir.exists():
            self.observer.schedule(event_handler, str(scripts_dir), recursive=True)
        self.observer.start()
        self.monitoring_active = True
        console.print("[green]✅ DDD準拠性リアルタイム監視開始[/green]")

    async def stop_real_time_monitoring(self) -> None:
        """リアルタイム監視停止"""
        if not self.monitoring_active or not self.observer:
            return
        self.observer.stop()
        self.observer.join()
        self.monitoring_active = False
        console.print("[yellow]⏹️  DDD準拠性リアルタイム監視停止[/yellow]")
        console.print("リアルタイム監視を停止しました")

    async def check_file_real_time(self, file_path: Path) -> None:
        """リアルタイムファイルチェック

        Args:
            file_path: チェック対象ファイル
        """
        try:
            self.stats["files_checked"] += 1
            violations: Any = await self._check_single_file_violations(file_path)
            if violations:
                self.stats["violations_detected"] += len(violations)
                for violation in violations:
                    await self._process_violation_alert(violation, file_path)
        except Exception as e:
            self.logger.exception("リアルタイムチェックエラー: %s - %s", file_path, e)

    async def _check_single_file_violations(self, file_path: Path) -> list[DDDViolation]:
        """単一ファイルの違反チェック

        Args:
            file_path: ファイルパス

        Returns:
            違反リスト
        """
        violations: list[Any] = []
        try:
            content = file_path.read_text(encoding="utf-8")
            import ast

            tree = ast.parse(content)
            file_layer = self._determine_file_layer(file_path)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    violation = self._check_import_violation(file_path, node, file_layer)
                    if violation:
                        violations.append(violation)
        except (FileNotFoundError, SyntaxError, UnicodeDecodeError) as e:
            console.print(f"ファイル解析エラー: {file_path} - {e}")
        return violations

    def _determine_file_layer(self, file_path: Path) -> str:
        """ファイルの層判定

        Args:
            file_path: ファイルパス

        Returns:
            層名
        """
        relative_path = str(file_path.relative_to(self.project_root))
        if "noveler/domain" in relative_path:
            return "domain"
        if "noveler/application" in relative_path:
            return "application"
        if "noveler/infrastructure" in relative_path:
            return "infrastructure"
        if "noveler/presentation" in relative_path:
            return "presentation"
        return "unknown"

    def _check_import_violation(
        self, file_path: Path, import_node: ast.ImportFrom, file_layer: str
    ) -> DDDViolation | None:
        """インポート違反チェック

        Args:
            file_path: ファイルパス
            import_node: インポートノード
            file_layer: ファイル層

        Returns:
            違反情報（違反がない場合はNone）
        """
        module_name = import_node.module
        violation_patterns = {
            "domain": [
                ("scripts\\.infrastructure", "ドメイン層からインフラ層への直接依存"),
                ("scripts\\.application", "ドメイン層からアプリケーション層への依存"),
                ("scripts\\.presentation", "ドメイン層からプレゼンテーション層への依存"),
            ],
            "application": [
                ("scripts\\.infrastructure\\.services", "アプリケーション層からインフラサービスへの直接依存"),
                ("scripts\\.presentation", "アプリケーション層からプレゼンテーション層への依存"),
            ],
            "presentation": [
                ("scripts\\.infrastructure\\.services", "プレゼンテーション層からインフラサービスへの直接依存"),
                ("scripts\\.infrastructure\\.adapters", "プレゼンテーション層からアダプターへの直接依存"),
            ],
        }
        patterns = violation_patterns.get(file_layer, [])
        for pattern, description in patterns:
            if re.match(pattern, module_name):
                severity = self._determine_violation_severity(file_layer, module_name)
                return DDDViolation(
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=import_node.lineno,
                    violation_type="INFRASTRUCTURE_DIRECT_DEPENDENCY",
                    severity=severity,
                    description=description,
                    recommendation=self._get_fix_recommendation(file_layer, module_name),
                    rule_id=f"INFRA_{file_layer.upper()}_001",
                    metadata={"imported_module": module_name, "file_layer": file_layer},
                )
        return None

    def _determine_violation_severity(self, file_layer: str, module_name: str) -> ViolationSeverity:
        """違反重要度決定

        Args:
            file_layer: ファイル層
            module_name: モジュール名

        Returns:
            違反重要度
        """
        critical_patterns = [("domain", "scripts\\.infrastructure"), ("domain", "scripts\\.presentation")]
        for pattern_layer, pattern in critical_patterns:
            if file_layer == pattern_layer and re.match(pattern, module_name):
                return ViolationSeverity.CRITICAL
        high_patterns = [
            ("application", "scripts\\.infrastructure\\.services"),
            ("presentation", "scripts\\.infrastructure\\.services"),
        ]
        for pattern_layer, pattern in high_patterns:
            if file_layer == pattern_layer and re.match(pattern, module_name):
                return ViolationSeverity.HIGH
        return ViolationSeverity.MEDIUM

    def _get_fix_recommendation(self, file_layer: str, module_name: str) -> str:
        """修正推奨事項取得

        Args:
            file_layer: ファイル層
            module_name: モジュール名

        Returns:
            修正推奨事項
        """
        fix_recommendations = {
            (
                "domain",
                "noveler.infrastructure",
            ): "ドメインインターフェースを定義し、インフラ層でアダプターパターンを使用してください",
            ("domain", "noveler.application"): "ドメインサービスとして実装するか、アプリケーション層に移動してください",
            (
                "application",
                "noveler.infrastructure.services",
            ): "アプリケーション層でインターフェースを定義し、DIコンテナで注入してください",
            (
                "presentation",
                "noveler.infrastructure.services",
            ): "アプリケーション層経由でアクセスするか、DIファクトリーを使用してください",
        }
        for (layer, pattern), recommendation in fix_recommendations.items():
            if file_layer == layer and pattern in module_name:
                return recommendation
        return f"{file_layer}層から{module_name}への直接依存を避け、適切な抽象化を行ってください"

    async def _process_violation_alert(self, violation: DDDViolation, file_path: Path) -> None:
        """違反アラート処理

        Args:
            violation: 違反情報
            file_path: ファイルパス
        """
        alert_level = self._map_severity_to_alert_level(violation.severity)
        if alert_level.value > self.alert_config.min_alert_level.value:
            return
        auto_fixable = self._is_auto_fixable(violation)
        alert = ViolationAlert(
            timestamp=datetime.now(timezone.utc),
            alert_level=alert_level,
            violation=violation,
            suggested_fix=self._generate_auto_fix_suggestion(violation),
            auto_fixable=auto_fixable,
            context={"file_path": str(file_path), "real_time": True},
        )
        self.alert_history.append(alert)
        await self._send_alert_notifications(alert)
        if alert_level in self.alert_config.immediate_block_levels:
            await self._handle_immediate_block(alert)
        if self.alert_config.auto_fix_enabled and auto_fixable:
            await self._apply_auto_fix(alert, file_path)

    def _map_severity_to_alert_level(self, severity: ViolationSeverity) -> AlertLevel:
        """重要度からアラートレベルへのマッピング"""
        mapping = {
            ViolationSeverity.CRITICAL: AlertLevel.CRITICAL,
            ViolationSeverity.HIGH: AlertLevel.HIGH,
            ViolationSeverity.MEDIUM: AlertLevel.MEDIUM,
            ViolationSeverity.LOW: AlertLevel.LOW,
        }
        return mapping.get(severity, AlertLevel.MEDIUM)

    def _is_auto_fixable(self, violation: DDDViolation) -> bool:
        """自動修正可能性判定

        Args:
            violation: 違反情報

        Returns:
            自動修正可能かどうか
        """
        auto_fixable_patterns = ["INFRASTRUCTURE_DIRECT_DEPENDENCY"]
        return violation.violation_type in auto_fixable_patterns

    def _generate_auto_fix_suggestion(self, violation: DDDViolation) -> str:
        """自動修正提案生成

        Args:
            violation: 違反情報

        Returns:
            修正提案
        """
        if violation.violation_type == "INFRASTRUCTURE_DIRECT_DEPENDENCY":
            imported_module = violation.metadata.get("imported_module", "")
            file_layer = violation.metadata.get("file_layer", "")
            if file_layer == "application" and "services" in imported_module:
                return f"インターフェース経由でアクセス: from noveler.domain.interfaces import I{imported_module.split('.')[-1]}"
            if file_layer == "presentation":
                return "DIファクトリー経由でアクセス: from noveler.infrastructure.factories import get_service_factory"
        return "手動での修正が必要です"

    async def _send_alert_notifications(self, alert: ViolationAlert) -> None:
        """アラート通知送信

        Args:
            alert: アラート情報
        """
        for channel in self.alert_config.enabled_channels:
            try:
                callback = self.notification_callbacks.get(channel)
                if callback:
                    await callback(alert)
                    self.stats["alerts_sent"] += 1
            except Exception as e:
                self.logger.exception("通知送信エラー (%s): %s", channel.value, e)

    async def _send_console_notification(self, alert: ViolationAlert) -> None:
        """コンソール通知送信"""
        level_colors = {
            AlertLevel.CRITICAL: "red",
            AlertLevel.HIGH: "orange3",
            AlertLevel.MEDIUM: "yellow",
            AlertLevel.LOW: "green",
            AlertLevel.INFO: "blue",
        }
        color = level_colors.get(alert.alert_level, "white")
        message = f"\n[{color}]🚨 DDD違反検出 ({alert.alert_level.value})[/{color}]\n📁 ファイル: {alert.violation.file_path}:{alert.violation.line_number}\n🔍 種類: {alert.violation.violation_type}\n📝 説明: {alert.violation.description}\n💡 推奨: {alert.violation.recommendation}\n"
        if alert.auto_fixable:
            message += f"🔧 自動修正提案: {alert.suggested_fix}\n"
        console.print(message)
        if self.alert_config.sound_enabled:
            await self._play_notification_sound(alert.alert_level)

    async def _send_log_notification(self, alert: ViolationAlert) -> None:
        """ログファイル通知送信"""
        log_message = f"DDD_VIOLATION|{alert.timestamp.isoformat()}|{alert.alert_level.value}|{alert.violation.file_path}|{alert.violation.violation_type}|{alert.violation.description}"
        console.print(log_message)

    async def _send_ide_notification(self, alert: ViolationAlert) -> None:
        """IDE統合通知送信"""
        ide_markers_dir = self.project_root / ".ddd_violations"
        ide_markers_dir.mkdir(exist_ok=True)
        marker_file = ide_markers_dir / f"violation_{int(time.time())}.json"
        marker_data: dict[str, Any] = {
            "timestamp": alert.timestamp.isoformat(),
            "file_path": alert.violation.file_path,
            "line_number": alert.violation.line_number,
            "severity": alert.alert_level.value,
            "type": alert.violation.violation_type,
            "description": alert.violation.description,
            "recommendation": alert.violation.recommendation,
            "auto_fixable": alert.auto_fixable,
            "suggested_fix": alert.suggested_fix,
        }
        with marker_file.open("w", encoding="utf-8") as f:
            json.dump(marker_data, f, ensure_ascii=False, indent=2)

    async def _play_notification_sound(self, alert_level: AlertLevel) -> None:
        """通知音再生

        Args:
            alert_level: アラートレベル
        """
        try:
            if alert_level in [AlertLevel.CRITICAL, AlertLevel.HIGH]:
                for _ in range(3):
                    self.console_service.print("\x07", end="", flush=True)
                    await asyncio.sleep(0.1)
            else:
                self.console_service.print("\x07", end="", flush=True)
        except Exception:
            pass

    async def _handle_immediate_block(self, alert: ViolationAlert) -> None:
        """即座ブロック処理

        Args:
            alert: アラート情報
        """
        console.print("[red]🛑 クリティカル違反により開発の一時停止をお勧めします[/red]")
        console.print(f"[red]ファイル: {alert.violation.file_path}[/red]")
        console.print("[red]修正してから作業を継続してください[/red]")
        self.logger.critical(f"IMMEDIATE_BLOCK: {alert.violation.violation_type} in {alert.violation.file_path}")

    async def _apply_auto_fix(self, alert: ViolationAlert, file_path: Path) -> None:
        """自動修正適用

        Args:
            alert: アラート情報
            file_path: ファイルパス
        """
        try:
            if not alert.auto_fixable:
                return
            backup_path = file_path.with_suffix(f".py.backup.{int(time.time())}")
            backup_path.write_text(file_path.read_text(encoding="utf-8"), encoding="utf-8")
            file_path.read_text(encoding="utf-8")
            if alert.violation.violation_type == "INFRASTRUCTURE_DIRECT_DEPENDENCY":
                alert.violation.metadata.get("imported_module", "")
            self.stats["auto_fixes_applied"] += 1
            console.print(f"自動修正適用: {file_path}")
            console.print(f"[green]🔧 自動修正適用: {alert.violation.file_path}[/green]")
        except Exception as e:
            self.logger.exception("自動修正エラー: %s - %s", file_path, e)

    def get_monitoring_statistics(self) -> dict[str, Any]:
        """監視統計取得

        Returns:
            監視統計情報
        """
        return {
            "monitoring_active": self.monitoring_active,
            "files_checked": self.stats["files_checked"],
            "violations_detected": self.stats["violations_detected"],
            "alerts_sent": self.stats["alerts_sent"],
            "auto_fixes_applied": self.stats["auto_fixes_applied"],
            "alert_history_count": len(self.alert_history),
            "recent_alerts": [
                {
                    "timestamp": alert.timestamp.isoformat(),
                    "level": alert.alert_level.value,
                    "type": alert.violation.violation_type,
                    "file": alert.violation.file_path,
                }
                for alert in self.alert_history[-10:]
            ],
        }

    async def export_alert_history(self, output_path: Path, format_type: str = "json") -> None:
        """アラート履歴エクスポート

        Args:
            output_path: 出力パス
            format_type: フォーマット（json/csv）
        """
        if format_type == "json":
            alert_data: dict[str, Any] = [
                {
                    "timestamp": alert.timestamp.isoformat(),
                    "alert_level": alert.alert_level.value,
                    "violation_type": alert.violation.violation_type,
                    "file_path": alert.violation.file_path,
                    "line_number": alert.violation.line_number,
                    "description": alert.violation.description,
                    "recommendation": alert.violation.recommendation,
                    "auto_fixable": alert.auto_fixable,
                    "suggested_fix": alert.suggested_fix,
                }
                for alert in self.alert_history
            ]
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(alert_data, f, ensure_ascii=False, indent=2)
        elif format_type == "csv":
            import csv

            with output_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "Timestamp",
                        "AlertLevel",
                        "ViolationType",
                        "FilePath",
                        "LineNumber",
                        "Description",
                        "Recommendation",
                        "AutoFixable",
                    ]
                )
                for alert in self.alert_history:
                    writer.writerow(
                        [
                            alert.timestamp.isoformat(),
                            alert.alert_level.value,
                            alert.violation.violation_type,
                            alert.violation.file_path,
                            alert.violation.line_number,
                            alert.violation.description,
                            alert.violation.recommendation,
                            alert.auto_fixable,
                        ]
                    )
        console.print(f"アラート履歴をエクスポートしました: {output_path}")
