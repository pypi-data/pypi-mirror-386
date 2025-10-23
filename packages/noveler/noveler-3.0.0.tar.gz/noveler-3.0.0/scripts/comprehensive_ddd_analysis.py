#!/usr/bin/env python3
"""包括的DDDコンプライアンス分析スクリプト

全層間の依存関係を分析し、B20準拠性を包括的に評価。
"""

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class LayerType(Enum):
    DOMAIN = "domain"
    APPLICATION = "application"
    INFRASTRUCTURE = "infrastructure"
    PRESENTATION = "presentation"


@dataclass
class DependencyViolation:
    """依存関係違反情報"""
    source_file: str
    source_layer: LayerType
    target_module: str
    target_layer: LayerType
    line_number: int
    line_content: str
    violation_severity: str


class DDDComplianceAnalyzer:
    """DDD準拠性分析器"""

    def __init__(self):
        # DDD層間依存関係ルール
        self.allowed_dependencies = {
            LayerType.DOMAIN: set(),  # Domainは他の層に依存してはいけない
            LayerType.APPLICATION: {LayerType.DOMAIN},
            LayerType.INFRASTRUCTURE: {LayerType.DOMAIN, LayerType.APPLICATION},
            LayerType.PRESENTATION: {LayerType.APPLICATION, LayerType.DOMAIN}
        }

        # 層識別パターン
        self.layer_patterns = {
            LayerType.DOMAIN: [r"noveler\.domain", r"scripts\.domain"],
            LayerType.APPLICATION: [r"noveler\.application", r"scripts\.application"],
            LayerType.INFRASTRUCTURE: [r"noveler\.infrastructure", r"scripts\.infrastructure"],
            LayerType.PRESENTATION: [r"noveler\.presentation", r"scripts\.presentation"]
        }

    def identify_layer(self, file_path: str) -> LayerType:
        """ファイルパスから層を特定"""
        for layer, patterns in self.layer_patterns.items():
            if any(re.search(pattern, file_path) for pattern in patterns):
                return layer
        return LayerType.DOMAIN  # デフォルト

    def identify_target_layer(self, import_statement: str) -> LayerType:
        """インポート文から対象層を特定"""
        for layer, patterns in self.layer_patterns.items():
            if any(re.search(pattern, import_statement) for pattern in patterns):
                return layer
        return LayerType.DOMAIN  # デフォルト

    def analyze_file(self, file_path: Path) -> list[DependencyViolation]:
        """単一ファイルの依存関係分析"""
        violations = []
        source_layer = self.identify_layer(str(file_path))

        try:
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # import文をチェック
                import_match = re.search(
                    r"(?:from\s+(noveler\.[^\s]+|scripts\.[^\s]+))|(?:import\s+(noveler\.[^\s]+|scripts\.[^\s]+))",
                    line
                )

                if import_match:
                    target_module = import_match.group(1) or import_match.group(2)
                    target_layer = self.identify_target_layer(target_module)

                    # 違反チェック
                    if target_layer not in self.allowed_dependencies[source_layer]:
                        severity = self._determine_severity(source_layer, target_layer)
                        violations.append(DependencyViolation(
                            source_file=str(file_path.relative_to(Path.cwd())),
                            source_layer=source_layer,
                            target_module=target_module,
                            target_layer=target_layer,
                            line_number=line_num,
                            line_content=line,
                            violation_severity=severity
                        ))

        except Exception as e:
            print(f"⚠️  ファイル分析エラー: {file_path} - {e}")

        return violations

    def _determine_severity(self, source: LayerType, target: LayerType) -> str:
        """違反重要度の決定"""
        critical_violations = [
            (LayerType.DOMAIN, LayerType.INFRASTRUCTURE),
            (LayerType.DOMAIN, LayerType.APPLICATION),
            (LayerType.DOMAIN, LayerType.PRESENTATION),
        ]

        if (source, target) in critical_violations:
            return "CRITICAL"
        if source == LayerType.APPLICATION and target == LayerType.INFRASTRUCTURE:
            return "HIGH"
        return "MEDIUM"

    def analyze_project(self) -> list[DependencyViolation]:
        """プロジェクト全体の分析"""
        all_violations = []

        # src/noveler配下の全Pythonファイルを分析
        src_path = Path("src/noveler")
        if src_path.exists():
            for py_file in src_path.rglob("*.py"):
                if py_file.name == "__init__.py":
                    continue
                violations = self.analyze_file(py_file)
                all_violations.extend(violations)

        # scripts配下も分析
        scripts_path = Path("scripts")
        if scripts_path.exists():
            for py_file in scripts_path.rglob("*.py"):
                if py_file.name == "__init__.py":
                    continue
                violations = self.analyze_file(py_file)
                all_violations.extend(violations)

        return all_violations

    def generate_report(self, violations: list[DependencyViolation]) -> None:
        """包括的レポート生成"""
        print("=" * 100)
        print("📋 包括的DDD準拠性分析レポート")
        print("=" * 100)

        if not violations:
            print("🎉 DDD違反は発見されませんでした！完全にB20準拠です！")
            return None

        # サマリー統計
        total_violations = len(violations)
        severity_counts = {}
        layer_violations = {}

        for violation in violations:
            # 重要度別集計
            severity = violation.violation_severity
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

            # 層別集計
            layer_key = f"{violation.source_layer.value} → {violation.target_layer.value}"
            layer_violations[layer_key] = layer_violations.get(layer_key, 0) + 1

        print("📊 違反サマリー:")
        print(f"  - 総違反数: {total_violations}")
        print("  - 重要度別:")
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            if severity in severity_counts:
                emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}[severity]
                print(f"    {emoji} {severity}: {severity_counts[severity]}件")

        print("\n🔄 層間依存関係違反:")
        for layer_dep, count in sorted(layer_violations.items(), key=lambda x: -x[1]):
            print(f"  - {layer_dep}: {count}件")

        # 重要度順で詳細表示（上位20件）
        violations_by_severity = sorted(violations, key=lambda x: {
            "CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3
        }.get(x.violation_severity, 3))

        print("\n🚨 重要度順詳細違反 (上位20件):")
        for i, violation in enumerate(violations_by_severity[:20], 1):
            severity_emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}[violation.violation_severity]
            print(f"  {i:2d}. {severity_emoji} [{violation.violation_severity}]")
            print(f"      {violation.source_file}:{violation.line_number}")
            print(f"      {violation.source_layer.value} → {violation.target_layer.value}")
            print(f"      {violation.line_content[:80]}...")
            print()

        # B20準拠性スコア計算
        total_files = len(set(v.source_file for v in violations))
        critical_violations = len([v for v in violations if v.violation_severity == "CRITICAL"])
        high_violations = len([v for v in violations if v.violation_severity == "HIGH"])

        # スコア計算（Critical=-10点、High=-5点、Medium=-2点、Low=-1点）
        penalty_score = critical_violations * 10 + high_violations * 5 + \
                       len([v for v in violations if v.violation_severity == "MEDIUM"]) * 2 + \
                       len([v for v in violations if v.violation_severity == "LOW"])

        max_score = 100
        compliance_score = max(0, max_score - penalty_score)

        print(f"📈 B20準拠性スコア: {compliance_score}/100")
        if compliance_score >= 90:
            print("✅ 優秀！B20準拠性が高いレベルです")
        elif compliance_score >= 70:
            print("⚠️  改善推奨。いくつかの違反が残っています")
        else:
            print("❌ 要改善。多くの違反があります")

        print("=" * 100)

        return violations


def main():
    """メイン実行"""
    print("🚀 包括的DDD準拠性分析開始...")

    analyzer = DDDComplianceAnalyzer()
    violations = analyzer.analyze_project()
    analyzer.generate_report(violations)

    print("✅ 包括的分析完了")


if __name__ == "__main__":
    main()
