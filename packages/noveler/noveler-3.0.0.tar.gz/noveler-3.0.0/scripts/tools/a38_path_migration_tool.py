"""
A38パス移行ツール

既存のパス実装からA38準拠パスシステムへの移行を支援するツール。

機能:
1. 既存パス使用箇所の検出
2. A38準拠パスへの自動変換
3. 移行プラン生成
4. 後方互換性チェック
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from noveler.presentation.shared.shared_utilities import get_a38_path_service


@dataclass
class PathMigrationItem:
    """パス移行項目"""
    file_path: Path
    line_number: int
    old_pattern: str
    new_pattern: str
    migration_type: str
    confidence: float


@dataclass
class MigrationReport:
    """移行レポート"""
    total_files_scanned: int
    files_with_changes: int
    migration_items: list[PathMigrationItem]
    conflicts: list[dict[str, Any]]
    estimated_effort_hours: float


class A38PathMigrationTool:
    """A38パス移行ツール"""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()
        self.a38_path_service = get_a38_path_service(project_root)
        self.migration_patterns = self._load_migration_patterns()

    def _load_migration_patterns(self) -> dict[str, dict[str, Any]]:
        """移行パターン定義読み込み"""
        return {
            # ハードコードパス移行
            "hardcoded_plots_dir": {
                "pattern": r'["\']20_プロット["\']',
                "replacement": "path_service.get_plots_dir()",
                "type": "hardcoded_path",
                "confidence": 0.95
            },
            "hardcoded_work_files_dir": {
                "pattern": r'["\']60_作業ファイル["\']',
                "replacement": "path_service.get_work_files_dir()",
                "type": "hardcoded_path",
                "confidence": 0.95
            },
            "hardcoded_manuscripts_dir": {
                "pattern": r'["\']40_原稿["\']',
                "replacement": "path_service.get_manuscripts_dir()",
                "type": "hardcoded_path",
                "confidence": 0.95
            },
            "hardcoded_settings_dir": {
                "pattern": r'["\']30_設定集["\']',
                "replacement": "path_service.get_settings_dir()",
                "type": "hardcoded_path",
                "confidence": 0.95
            },

            # 旧式パス生成パターン移行
            "old_episode_path_pattern": {
                "pattern": r'f["\']第{.*?}話.*?\.md["\']',
                "replacement": "path_service.get_episode_plot_path(episode_number)",
                "type": "path_generation",
                "confidence": 0.85
            },
            "old_work_file_pattern": {
                "pattern": r'f["\']episode{.*?}_step{.*?}\.yaml["\']',
                "replacement": "path_service.get_work_file_path(episode_number, step_number)",
                "type": "path_generation",
                "confidence": 0.90
            },

            # A38非準拠パターン移行
            "non_a38_episode_pattern": {
                "pattern": r'["\']第\d{3}話.*?\.md["\']',
                "replacement": "path_service.get_episode_plot_path(episode_number)",
                "type": "a38_compliance",
                "confidence": 0.80
            },

            # レガシーパスサービス使用パターン
            "legacy_path_service": {
                "pattern": r"get_test_path_service\(",
                "replacement": "get_a38_path_service(",
                "type": "service_migration",
                "confidence": 0.98
            },
            "legacy_plots_method": {
                "pattern": r"\.get_plots_dir\(\)",
                "replacement": ".get_episode_plots_dir()",
                "type": "method_migration",
                "confidence": 0.85
            }
        }

    def scan_codebase(self, target_dirs: list[Path] | None = None) -> MigrationReport:
        """コードベース全体スキャン"""
        if target_dirs is None:
            target_dirs = [
                self.project_root / "scripts",
                self.project_root / "tests",
            ]

        migration_items = []
        files_scanned = 0
        files_with_changes = 0
        conflicts = []

        for target_dir in target_dirs:
            if not target_dir.exists():
                continue

            for py_file in target_dir.rglob("*.py"):
                # アーカイブ・バックアップファイルをスキップ
                if any(part in str(py_file) for part in ["archive", "backup", "__pycache__", ".git"]):
                    continue

                files_scanned += 1
                file_items = self._scan_file(py_file)

                if file_items:
                    files_with_changes += 1
                    migration_items.extend(file_items)

                # 競合チェック
                file_conflicts = self._detect_conflicts(py_file, file_items)
                conflicts.extend(file_conflicts)

        # 推定作業時間計算
        estimated_hours = self._estimate_migration_effort(migration_items)

        return MigrationReport(
            total_files_scanned=files_scanned,
            files_with_changes=files_with_changes,
            migration_items=migration_items,
            conflicts=conflicts,
            estimated_effort_hours=estimated_hours
        )

    def _scan_file(self, file_path: Path) -> list[PathMigrationItem]:
        """単一ファイルスキャン"""
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return []

        migration_items = []
        lines = content.split("\n")

        for line_no, line in enumerate(lines, 1):
            for pattern_name, pattern_config in self.migration_patterns.items():
                pattern = pattern_config["pattern"]
                matches = re.finditer(pattern, line)

                for match in matches:
                    migration_item = PathMigrationItem(
                        file_path=file_path,
                        line_number=line_no,
                        old_pattern=match.group(),
                        new_pattern=pattern_config["replacement"],
                        migration_type=pattern_config["type"],
                        confidence=pattern_config["confidence"]
                    )
                    migration_items.append(migration_item)

        return migration_items

    def _detect_conflicts(self, file_path: Path, migration_items: list[PathMigrationItem]) -> list[dict[str, Any]]:
        """競合検出"""
        conflicts = []

        # 同一行に複数のパターンマッチがある場合
        line_counts = {}
        for item in migration_items:
            line_key = (file_path, item.line_number)
            line_counts[line_key] = line_counts.get(line_key, 0) + 1

        for (file_path, line_no), count in line_counts.items():
            if count > 1:
                conflicts.append({
                    "type": "multiple_patterns_same_line",
                    "file_path": str(file_path),
                    "line_number": line_no,
                    "pattern_count": count,
                    "severity": "medium"
                })

        return conflicts

    def _estimate_migration_effort(self, migration_items: list[PathMigrationItem]) -> float:
        """移行作業時間推定（時間単位）"""
        # 基本時間（分）
        time_estimates = {
            "hardcoded_path": 2,      # ハードコードパス修正
            "path_generation": 5,     # パス生成ロジック修正
            "a38_compliance": 8,      # A38準拠化修正
            "service_migration": 3,   # サービス移行
            "method_migration": 3     # メソッド移行
        }

        total_minutes = 0
        for item in migration_items:
            base_time = time_estimates.get(item.migration_type, 5)
            # 信頼度が低い場合は時間増加
            confidence_multiplier = 1.0 + (1.0 - item.confidence)
            total_minutes += base_time * confidence_multiplier

        # テスト・検証時間を加算（50%）
        total_minutes *= 1.5

        return total_minutes / 60.0  # 時間単位に変換

    def generate_migration_plan(self, migration_report: MigrationReport) -> dict[str, Any]:
        """移行プラン生成"""
        # 優先度別グループ化
        priority_groups = {
            "high": [],      # ハードコードパス、重大な非準拠
            "medium": [],    # パス生成ロジック、サービス移行
            "low": []        # メソッド移行、軽微な修正
        }

        for item in migration_report.migration_items:
            if item.migration_type in ["hardcoded_path", "a38_compliance"] or item.confidence > 0.9:
                priority_groups["high"].append(item)
            elif item.migration_type in ["path_generation", "service_migration"]:
                priority_groups["medium"].append(item)
            else:
                priority_groups["low"].append(item)

        # フェーズ分割
        phases = [
            {
                "phase": 1,
                "name": "緊急修正",
                "description": "ハードコードパス解消とA38準拠化",
                "items": priority_groups["high"],
                "estimated_hours": sum(
                    2 * (1.0 + (1.0 - item.confidence)) / 60.0
                    for item in priority_groups["high"]
                ) * 1.5
            },
            {
                "phase": 2,
                "name": "システム統合",
                "description": "パス生成ロジックとサービス移行",
                "items": priority_groups["medium"],
                "estimated_hours": sum(
                    4 * (1.0 + (1.0 - item.confidence)) / 60.0
                    for item in priority_groups["medium"]
                ) * 1.5
            },
            {
                "phase": 3,
                "name": "最適化",
                "description": "メソッド移行と品質向上",
                "items": priority_groups["low"],
                "estimated_hours": sum(
                    3 * (1.0 + (1.0 - item.confidence)) / 60.0
                    for item in priority_groups["low"]
                ) * 1.5
            }
        ]

        return {
            "migration_summary": {
                "total_items": len(migration_report.migration_items),
                "total_estimated_hours": migration_report.estimated_effort_hours,
                "conflicts_count": len(migration_report.conflicts)
            },
            "phases": phases,
            "risks": self._identify_risks(migration_report),
            "recommendations": self._generate_recommendations(migration_report)
        }

    def _identify_risks(self, migration_report: MigrationReport) -> list[dict[str, Any]]:
        """リスク識別"""
        risks = []

        # 信頼度が低い項目が多い
        low_confidence_items = [
            item for item in migration_report.migration_items
            if item.confidence < 0.8
        ]
        if len(low_confidence_items) > 10:
            risks.append({
                "type": "low_confidence_migrations",
                "severity": "high",
                "count": len(low_confidence_items),
                "description": "信頼度が低い移行項目が多数存在"
            })

        # 競合が多い
        if len(migration_report.conflicts) > 5:
            risks.append({
                "type": "many_conflicts",
                "severity": "medium",
                "count": len(migration_report.conflicts),
                "description": "移行時競合が多数発生予想"
            })

        # 大規模変更
        if migration_report.files_with_changes > 20:
            risks.append({
                "type": "large_scale_changes",
                "severity": "medium",
                "file_count": migration_report.files_with_changes,
                "description": "大規模なファイル変更が必要"
            })

        return risks

    def _generate_recommendations(self, migration_report: MigrationReport) -> list[str]:
        """推奨事項生成"""
        recommendations = []

        recommendations.append("移行前に完全なバックアップを作成")
        recommendations.append("フェーズ別の段階的移行を実施")

        if len(migration_report.conflicts) > 0:
            recommendations.append("競合項目は手動レビューと修正を実施")

        if migration_report.estimated_effort_hours > 8:
            recommendations.append("複数人での分担作業を検討")

        recommendations.append("移行後は統合テストで動作確認")
        recommendations.append("A38準拠チェックツールで品質検証")

        return recommendations

    def apply_migrations(self, migration_items: list[PathMigrationItem], dry_run: bool = True) -> dict[str, Any]:
        """移行適用"""
        results = {
            "applied_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "dry_run": dry_run,
            "details": []
        }

        # ファイル別にグループ化
        file_groups = {}
        for item in migration_items:
            file_path = item.file_path
            if file_path not in file_groups:
                file_groups[file_path] = []
            file_groups[file_path].append(item)

        for file_path, file_items in file_groups.items():
            try:
                if dry_run:
                    # ドライランでは変更をシミュレート
                    results["applied_count"] += len(file_items)
                    results["details"].append({
                        "file": str(file_path),
                        "action": "simulated",
                        "changes": len(file_items)
                    })
                else:
                    # 実際の変更適用
                    applied = self._apply_file_migrations(file_path, file_items)
                    results["applied_count"] += applied
                    results["details"].append({
                        "file": str(file_path),
                        "action": "applied",
                        "changes": applied
                    })
            except Exception as e:
                results["failed_count"] += len(file_items)
                results["details"].append({
                    "file": str(file_path),
                    "action": "failed",
                    "error": str(e)
                })

        return results

    def _apply_file_migrations(self, file_path: Path, migration_items: list[PathMigrationItem]) -> int:
        """単一ファイルへの移行適用"""
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")
        applied_count = 0

        # 行番号の降順で処理（行番号ずれを防ぐため）
        sorted_items = sorted(migration_items, key=lambda x: x.line_number, reverse=True)

        for item in sorted_items:
            try:
                line_idx = item.line_number - 1
                if 0 <= line_idx < len(lines):
                    old_line = lines[line_idx]
                    new_line = re.sub(
                        re.escape(item.old_pattern),
                        item.new_pattern,
                        old_line
                    )
                    lines[line_idx] = new_line
                    applied_count += 1
            except Exception:
                continue

        # ファイル書き戻し
        new_content = "\n".join(lines)
        file_path.write_text(new_content, encoding="utf-8")

        return applied_count


def main():
    """メイン実行"""
    project_root = Path.cwd()
    migration_tool = A38PathMigrationTool(project_root)

    print("A38パス移行ツール実行開始...")

    # コードベーススキャン
    migration_report = migration_tool.scan_codebase()

    print("スキャン完了:")
    print(f"  - 対象ファイル数: {migration_report.total_files_scanned}")
    print(f"  - 変更が必要なファイル数: {migration_report.files_with_changes}")
    print(f"  - 移行項目数: {len(migration_report.migration_items)}")
    print(f"  - 競合数: {len(migration_report.conflicts)}")
    print(f"  - 推定作業時間: {migration_report.estimated_effort_hours:.2f}時間")

    # 移行プラン生成
    migration_plan = migration_tool.generate_migration_plan(migration_report)

    print("\n移行プラン:")
    for phase in migration_plan["phases"]:
        print(f"  フェーズ{phase['phase']}: {phase['name']} ({len(phase['items'])}項目, {phase['estimated_hours']:.2f}時間)")

    if migration_plan["risks"]:
        print("\n特定されたリスク:")
        for risk in migration_plan["risks"]:
            print(f"  - {risk['description']} (重要度: {risk['severity']})")

    print("\n推奨事項:")
    for rec in migration_plan["recommendations"]:
        print(f"  - {rec}")


if __name__ == "__main__":
    main()
