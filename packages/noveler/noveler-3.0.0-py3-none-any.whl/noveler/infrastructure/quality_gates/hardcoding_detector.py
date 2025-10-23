"""Infrastructure.quality_gates.hardcoding_detector
Where: Infrastructure quality gate detecting hardcoded values.
What: Scans code for hardcoded literals and produces remediation guidance.
Why: Encourages configuration-driven code and consistent practices.
"""

from __future__ import annotations

from noveler.presentation.shared.shared_utilities import console

"\nハードコーディング検出器: 品質ゲート拡張機能\n\nCommonPathService使用義務化とハードコーディングパターンを自動検出する\n品質ゲート拡張システム。\n"
import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar

import yaml


class HardcodingType(Enum):
    """ハードコーディングの種類"""

    DIRECTORY_PATH = "directory_path"
    FILE_PATH = "file_path"
    CONFIGURATION = "configuration"
    MAGIC_NUMBER = "magic_number"
    URL_ENDPOINT = "url_endpoint"
    DATABASE_CONNECTION = "database"


class Severity(Enum):
    """問題の重要度"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class HardcodingViolation:
    """ハードコーディング違反の詳細"""

    file_path: Path
    line_number: int
    hardcoding_type: HardcodingType
    severity: Severity
    detected_value: str
    violation_message: str
    recommended_solution: str
    rule_id: str


class HardcodingDetector:
    """
    ハードコーディング違反検出システム

    検出対象:
    - ディレクトリパスのハードコーディング（CommonPathService違反）
    - 設定値のハードコーディング
    - マジックナンバー
    - URLエンドポイントの埋め込み
    - データベース接続文字列
    """

    DETECTION_RULES: ClassVar[list[dict[str, Any]]] = [
        {
            "type": HardcodingType.DIRECTORY_PATH,
            "pattern": "Path\\(['\\\"].*?/(40_原稿|30_設定集|20_プロット|50_管理資料)['\\\"]",
            "severity": Severity.HIGH,
            "rule_id": "HARD-001",
            "message": "プロジェクトディレクトリのハードコーディングは禁止です",
            "solution": "CommonPathServiceのget_*_dir()メソッドを使用してください",
        },
        {
            "type": HardcodingType.FILE_PATH,
            "pattern": "['\\\"][^'\\\"]*\\.(yaml|yml|md|json)['\\\"]",
            "severity": Severity.MEDIUM,
            "rule_id": "HARD-002",
            "message": "設定ファイルパスのハードコーディングは推奨されません",
            "solution": "設定ファイルパスは外部設定化を検討してください",
        },
        {
            "type": HardcodingType.CONFIGURATION,
            "pattern": "['\\\"][^'\\\"]*localhost[^'\\\"]*['\\\"]",
            "severity": Severity.HIGH,
            "rule_id": "HARD-003",
            "message": "localhostのハードコーディングは本番環境で問題になります",
            "solution": "環境変数またはconfigファイルで設定してください",
        },
        {
            "type": HardcodingType.MAGIC_NUMBER,
            "pattern": "\\b(4000|6000|3000)\\b",
            "severity": Severity.LOW,
            "rule_id": "HARD-004",
            "message": "文字数制限などの定数はマジックナンバーです",
            "solution": "定数として定義するか設定ファイルに移動してください",
        },
        {
            "type": HardcodingType.URL_ENDPOINT,
            "pattern": "['\\\"]https?://[^'\\\"]+['\\\"]",
            "severity": Severity.MEDIUM,
            "rule_id": "HARD-005",
            "message": "APIエンドポイントのハードコーディングは環境依存の問題を起こします",
            "solution": "環境変数またはconfigファイルで管理してください",
        },
        {
            "type": HardcodingType.DATABASE_CONNECTION,
            "pattern": "['\\\"].*?(sqlite|mysql|postgresql)://[^'\\\"]*['\\\"]",
            "severity": Severity.CRITICAL,
            "rule_id": "HARD-006",
            "message": "データベース接続文字列のハードコーディングはセキュリティリスクです",
            "solution": "環境変数で接続情報を管理してください",
        },
    ]
    PATH_SERVICE_PATTERNS: ClassVar[list[dict[str, Any]]] = [
        {
            "description": "原稿ディレクトリ",
            "hardcoded_patterns": ["40_原稿", "manuscript"],
            "recommended_method": "path_service.get_manuscript_dir()",
            "severity": Severity.HIGH,
        },
        {
            "description": "設定ディレクトリ",
            "hardcoded_patterns": ["30_設定集", "settings", "config"],
            "recommended_method": "path_service.get_settings_dir()",
            "severity": Severity.HIGH,
        },
        {
            "description": "プロットディレクトリ",
            "hardcoded_patterns": ["20_プロット", "plot"],
            "recommended_method": "path_service.get_plot_dir()",
            "severity": Severity.HIGH,
        },
        {
            "description": "管理資料ディレクトリ",
            "hardcoded_patterns": ["50_管理資料", "management"],
            "recommended_method": "path_service.get_management_dir()",
            "severity": Severity.MEDIUM,
        },
    ]
    EXCLUSION_PATTERNS: ClassVar[list[str]] = [
        "#.*",
        "['\\\"]https://github\\.com[^'\\\"]*['\\\"]",
        "['\\\"]https://docs\\.[^'\\\"]*['\\\"]",
    ]

    def __init__(self, project_root: Path, logger_service=None, console_service=None) -> None:
        """
        Args:
            project_root: プロジェクトルートディレクトリ
        """
        self.project_root = project_root
        self.scripts_root = project_root / "scripts"
        self.violations: list[HardcodingViolation] = []
        self.logger_service = logger_service
        self.console_service = console_service

    def detect_violations(self) -> list[HardcodingViolation]:
        """
        プロジェクト全体のハードコーディング違反を検出

        Returns:
            検出された違反のリスト
        """
        self.violations.clear()
        python_files = list(self.scripts_root.rglob("*.py"))
        for python_file in python_files:
            self._detect_file_violations(python_file)
        return self.violations

    def _detect_file_violations(self, file_path: Path) -> None:
        """単一ファイルの違反検出"""
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                if self._is_excluded_line(line):
                    continue
                for rule in self.DETECTION_RULES:
                    matches = re.finditer(rule["pattern"], line)
                    for match in matches:
                        self.violations.append(
                            HardcodingViolation(
                                file_path=file_path,
                                line_number=i,
                                hardcoding_type=rule["type"],
                                severity=rule["severity"],
                                detected_value=match.group(),
                                violation_message=rule["message"],
                                recommended_solution=rule["solution"],
                                rule_id=rule["rule_id"],
                            )
                        )
                self._check_path_service_usage(file_path, i, line)
        except Exception as e:
            self.violations.append(
                HardcodingViolation(
                    file_path=file_path,
                    line_number=1,
                    hardcoding_type=HardcodingType.CONFIGURATION,
                    severity=Severity.LOW,
                    detected_value="",
                    violation_message=f"ファイル読み込みエラー: {e}",
                    recommended_solution="ファイルのエンコーディングを確認してください",
                    rule_id="HARD-FILE",
                )
            )

    def _is_excluded_line(self, line: str) -> bool:
        """除外パターンに一致するかチェック"""
        line_stripped = line.strip()
        return any(re.search(pattern, line_stripped) for pattern in self.EXCLUSION_PATTERNS)

    def _check_path_service_usage(self, file_path: Path, line_number: int, line: str) -> None:
        """CommonPathService使用推奨チェック"""
        line_lower = line.lower()
        for path_pattern in self.PATH_SERVICE_PATTERNS:
            for hardcoded_pattern in path_pattern["hardcoded_patterns"]:
                if re.search(hardcoded_pattern, line_lower):
                    if "path_service" in line_lower or "get_common_path_service" in line_lower:
                        continue
                    self.violations.append(
                        HardcodingViolation(
                            file_path=file_path,
                            line_number=line_number,
                            hardcoding_type=HardcodingType.DIRECTORY_PATH,
                            severity=path_pattern["severity"],
                            detected_value=hardcoded_pattern,
                            violation_message=f"{path_pattern['description']}のハードコーディングです",
                            recommended_solution=path_pattern["recommended_method"],
                            rule_id="PATH-SERVICE",
                        )
                    )

    def generate_quality_report(self) -> dict[str, Any]:
        """品質レポートの生成"""
        severity_counts = {
            "critical": len([v for v in self.violations if v.severity == Severity.CRITICAL]),
            "high": len([v for v in self.violations if v.severity == Severity.HIGH]),
            "medium": len([v for v in self.violations if v.severity == Severity.MEDIUM]),
            "low": len([v for v in self.violations if v.severity == Severity.LOW]),
        }
        type_counts = {}
        for violation in self.violations:
            type_name = violation.hardcoding_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        quality_score = 100
        quality_score -= severity_counts["critical"] * 25
        quality_score -= severity_counts["high"] * 10
        quality_score -= severity_counts["medium"] * 5
        quality_score -= severity_counts["low"] * 1
        quality_score = max(0, quality_score)
        return {
            "total_violations": len(self.violations),
            "severity_distribution": severity_counts,
            "type_distribution": type_counts,
            "quality_score": quality_score,
            "quality_grade": self._calculate_quality_grade(quality_score),
            "recommendations": self._generate_recommendations(),
        }

    def _calculate_quality_grade(self, score: int) -> str:
        """品質スコアからグレードを計算"""
        if score >= 90:
            return "A (優秀)"
        if score >= 80:
            return "B (良好)"
        if score >= 70:
            return "C (普通)"
        if score >= 60:
            return "D (要改善)"
        return "F (要大幅改善)"

    def _generate_recommendations(self) -> list[str]:
        """改善推奨事項の生成"""
        recommendations = []
        critical_count = len([v for v in self.violations if v.severity == Severity.CRITICAL])
        if critical_count > 0:
            recommendations.append(
                f"🔴 {critical_count}件のクリティカル違反があります。セキュリティリスクのため即座に修正してください"
            )
        high_count = len([v for v in self.violations if v.severity == Severity.HIGH])
        if high_count > 0:
            recommendations.append(f"🟡 {high_count}件の高重要度違反があります。本番運用前に修正してください")
        path_violations = [v for v in self.violations if v.hardcoding_type == HardcodingType.DIRECTORY_PATH]
        if path_violations:
            recommendations.append(
                "📂 ディレクトリパスのハードコーディングが検出されました。CommonPathServiceの使用を強く推奨します"
            )
        config_violations = [v for v in self.violations if v.hardcoding_type == HardcodingType.CONFIGURATION]
        if config_violations:
            recommendations.append(
                "⚙️ 設定値のハードコーディングが検出されました。設定ファイルまたは環境変数での管理を検討してください"
            )
        return recommendations

    def export_results(self, output_path: Path) -> None:
        """検出結果をYAMLでエクスポート"""
        report = self.generate_quality_report()
        export_data: dict[str, Any] = {
            "metadata": {"project_root": str(self.project_root), "scan_date": "2025-08-08", "quality_report": report},
            "violations": [
                {
                    "file_path": str(v.file_path.relative_to(self.project_root)),
                    "line_number": v.line_number,
                    "type": v.hardcoding_type.value,
                    "severity": v.severity.value,
                    "detected_value": v.detected_value,
                    "message": v.violation_message,
                    "solution": v.recommended_solution,
                    "rule_id": v.rule_id,
                }
                for v in self.violations
            ],
        }
        with output_path.Path("w").open(encoding="utf-8") as f:
            yaml.dump(export_data, f, allow_unicode=True, sort_keys=False)

    def create_auto_fix_suggestions(self) -> dict[Path, list[dict[str, Any]]]:
        """自動修正提案の生成"""
        fix_suggestions = {}
        for violation in self.violations:
            if violation.file_path not in fix_suggestions:
                fix_suggestions[violation.file_path] = []
            if violation.hardcoding_type == HardcodingType.DIRECTORY_PATH:
                suggestion = self._generate_path_service_fix(violation)
                if suggestion:
                    fix_suggestions[violation.file_path].append(suggestion)
        return fix_suggestions

    def _generate_path_service_fix(self, violation: HardcodingViolation) -> dict[str, Any] | None:
        """CommonPathService置換提案の生成"""
        for pattern in self.PATH_SERVICE_PATTERNS:
            for hardcoded_pattern in pattern["hardcoded_patterns"]:
                if hardcoded_pattern in violation.detected_value.lower():
                    return {
                        "line_number": violation.line_number,
                        "original": violation.detected_value,
                        "suggested_replacement": pattern["recommended_method"],
                        "import_required": "from noveler.infrastructure.adapters.path_service_adapter import create_path_service",
                        "setup_code": "path_service = create_path_service(project_root)",
                    }
        return None


def main() -> None:
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description="ハードコーディング検出・品質ゲート拡張ツール")
    parser.add_argument("--project-root", type=Path, default=Path(), help="プロジェクトルートディレクトリ")
    parser.add_argument("--output", type=Path, default=Path("hardcoding_violations.yaml"), help="出力ファイルパス")
    parser.add_argument("--quality-threshold", type=int, default=70, help="品質スコアの最低閾値")
    parser.add_argument("--fail-on-critical", action="store_true", help="クリティカル違反がある場合に終了コード1で終了")
    parser.add_argument("--report-only", action="store_true", help="レポート表示のみ（ファイル出力なし）")
    args = parser.parse_args()
    detector = HardcodingDetector(args.project_root)
    console.print("🔍 ハードコーディング違反をスキャン中...")
    detector.detect_violations()
    report = detector.generate_quality_report()
    console.print("\n📊 品質レポート:")
    console.print(f"   📈 品質スコア: {report['quality_score']}/100 ({report['quality_grade']})")
    console.print(f"   🔍 総違反件数: {report['total_violations']}件")
    if report["severity_distribution"]:
        console.print("   📋 重要度別:")
        for severity, count in report["severity_distribution"].items():
            if count > 0:
                icon = {"critical": "🔴", "high": "🟡", "medium": "🟠", "low": "🔵"}[severity]
                console.print(f"      {icon} {severity.upper()}: {count}件")
    if report["recommendations"]:
        console.print("\n💡 推奨事項:")
        for rec in report["recommendations"]:
            console.print(f"   {rec}")
    if not args.report_only:
        detector.export_results(args.output)
        console.print(f"\n📄 詳細結果をエクスポート: {args.output}")
    if args.fail_on_critical and report["severity_distribution"]["critical"] > 0:
        console.print("❌ クリティカル違反のため終了コード1で終了")
        sys.exit(1)
    elif report["quality_score"] < args.quality_threshold:
        console.print(f"⚠️ 品質スコア({report['quality_score']})が閾値({args.quality_threshold})を下回っています")
        sys.exit(1)
    else:
        console.print("✅ 品質基準をクリア")


if __name__ == "__main__":
    main()
