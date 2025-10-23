"""DDD準拠性チェック基本データ構造

品質チェックで使用される基本的なデータ構造とEnumクラス群
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class ViolationSeverity(Enum):
    """違反重要度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ValidationLevel(Enum):
    """検証レベル"""
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"
    COMPREHENSIVE = "comprehensive"


class LayerType(Enum):
    """DDD層種別"""
    DOMAIN = "domain"
    APPLICATION = "application"
    INFRASTRUCTURE = "infrastructure"
    PRESENTATION = "presentation"
    SHARED = "shared"
    TEST = "test"
    UNKNOWN = "unknown"


@dataclass
class DDDViolation:
    """DDD違反情報"""

    file_path: Path
    line_number: int
    severity: ViolationSeverity
    violation_type: str
    description: str
    suggestion: str | None = None
    rule_id: str | None = None
    layer: LayerType | None = None

    def to_dict(self) -> dict[str, Any]:
        """辞書形式変換"""
        return {
            "file_path": str(self.file_path),
            "line_number": self.line_number,
            "severity": self.severity.value,
            "violation_type": self.violation_type,
            "description": self.description,
            "suggestion": self.suggestion,
            "rule_id": self.rule_id,
            "layer": self.layer.value if self.layer else None
        }


@dataclass
class ComplianceReport:
    """準拠性レポート"""

    project_root: Path
    total_files: int
    violations: list[DDDViolation]
    validation_level: ValidationLevel
    timestamp: str

    @property
    def violation_count_by_severity(self) -> dict[str, int]:
        """重要度別違反数"""
        counts = {severity.value: 0 for severity in ViolationSeverity}
        for violation in self.violations:
            counts[violation.severity.value] += 1
        return counts

    @property
    def violation_count_by_type(self) -> dict[str, int]:
        """種別違反数"""
        type_counts: dict[str, int] = {}
        for violation in self.violations:
            type_counts[violation.violation_type] = type_counts.get(violation.violation_type, 0) + 1
        return type_counts

    @property
    def compliance_score(self) -> float:
        """準拠性スコア（0-100）"""
        if self.total_files == 0:
            return 100.0

        # 重要度別重み
        severity_weights = {
            ViolationSeverity.CRITICAL: 10,
            ViolationSeverity.HIGH: 5,
            ViolationSeverity.MEDIUM: 2,
            ViolationSeverity.LOW: 1
        }

        total_penalty = sum(
            severity_weights.get(violation.severity, 1)
            for violation in self.violations
        )

        # スコア計算（ファイル数基準）
        max_penalty_per_file = 20  # 1ファイル当たりの最大ペナルティ
        max_penalty = self.total_files * max_penalty_per_file

        if max_penalty == 0:
            return 100.0

        score = max(0, 100 - (total_penalty / max_penalty) * 100)
        return round(score, 2)

    def to_dict(self) -> dict[str, Any]:
        """辞書形式変換"""
        return {
            "project_root": str(self.project_root),
            "total_files": self.total_files,
            "validation_level": self.validation_level.value,
            "timestamp": self.timestamp,
            "compliance_score": self.compliance_score,
            "violation_summary": {
                "total_count": len(self.violations),
                "by_severity": self.violation_count_by_severity,
                "by_type": self.violation_count_by_type
            },
            "violations": [violation.to_dict() for violation in self.violations]
        }


class ComplianceRuleSet:
    """準拠性ルールセット"""

    # DDD層間依存関係ルール
    LAYER_DEPENDENCIES = {
        LayerType.DOMAIN: set(),  # ドメインは他の層に依存しない
        LayerType.APPLICATION: {LayerType.DOMAIN},  # アプリケーションはドメインのみ
        LayerType.INFRASTRUCTURE: {LayerType.DOMAIN, LayerType.APPLICATION},  # インフラはドメイン・アプリケーション
        LayerType.PRESENTATION: {LayerType.DOMAIN, LayerType.APPLICATION, LayerType.INFRASTRUCTURE},  # プレゼンテーションは全て
        LayerType.SHARED: set(),  # 共有は独立
        LayerType.TEST: {LayerType.DOMAIN, LayerType.APPLICATION, LayerType.INFRASTRUCTURE, LayerType.PRESENTATION}  # テストは全て
    }

    # 禁止パターン
    FORBIDDEN_PATTERNS = {
        "hardcoded_paths": [
            r"Path\([\"']/",  # 絶対パス
            r"[\"']/home/",   # ホームディレクトリ
            r"[\"']/tmp/",    # 一時ディレクトリ
            r"[\"']/var/",    # システムディレクトリ
        ],
        "direct_console_usage": [
            r"Console\(\)",  # Rich Console直接インスタンス化
            r"print\(",     # print文直接使用
        ],
        "legacy_logging": [
            r"import logging",
            r"logging\.getLogger",
            r"logging\.basicConfig",
        ]
    }

    # 推奨パターン
    RECOMMENDED_PATTERNS = {
        "path_service_usage": [
            "path_service.get_",
            "create_path_service",
        ],
        "shared_console_usage": [
            "_get_console()",
            "shared_utilities.console",
        ],
        "unified_logging": [
            "get_logger(__name__)",
            "from noveler.infrastructure.logging.unified_logger import get_logger",
        ]
    }
