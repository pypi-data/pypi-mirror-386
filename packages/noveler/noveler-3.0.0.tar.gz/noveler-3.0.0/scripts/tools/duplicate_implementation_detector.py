#!/usr/bin/env python3
"""重複実装検出ツール

既存ファイルを無視した新規実装を防ぐため、重複パターンを自動検出する。

使用例:
    python scripts/tools/duplicate_implementation_detector.py
    python scripts/tools/duplicate_implementation_detector.py --fix  # 自動修正
"""

import re
import sys
from dataclasses import dataclass
from pathlib import Path

from rich.panel import Panel
from rich.table import Table

# B20準拠: 共有コンソール使用
from noveler.presentation.shared.shared_utilities import console


@dataclass
class DuplicationViolation:
    """重複実装違反情報"""
    file_path: Path
    line_number: int
    violation_type: str
    content: str
    suggestion: str
    severity: str  # "critical", "high", "medium", "low"

class DuplicateImplementationDetector:
    """重複実装検出器"""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()
        # B20準拠: 共有コンソール使用
        self.console = console
        self.violations: list[DuplicationViolation] = []

        # 検出パターン定義
        self.patterns = {
            "console_duplication": {
                "pattern": r"console\s*=\s*Console\(\)",
                "severity": "critical",
                "message": "Console()の直接インスタンス化は禁止",
                "suggestion": "from noveler.presentation.shared.shared_utilities import console"
            },
            "console_import_duplication": {
                "pattern": r"from\s+rich\.console\s+import\s+Console",
                "severity": "critical",
                "message": "rich.Consoleの直接インポートは禁止",
                "suggestion": "from noveler.presentation.shared.shared_utilities import console"
            },
            "logging_duplication": {
                "pattern": r"import\s+logging(?!\s*#\s*legacy\s+migration)",
                "severity": "high",
                "message": "直接logging使用は禁止",
                "suggestion": "from noveler.infrastructure.logging.unified_logger import get_logger"
            },
            "logging_config_duplication": {
                "pattern": r"logging\.basicConfig\(",
                "severity": "critical",
                "message": "logging設定の重複は禁止",
                "suggestion": "統一loggerシステムを使用"
            },
            "path_hardcoding_manuscript": {
                "pattern": r'["\']40_原稿["\']',
                "severity": "high",
                "message": "原稿パスのハードコーディングは禁止",
                "suggestion": "path_service.get_manuscript_dir()"
            },
            "path_hardcoding_plot": {
                "pattern": r'["\']20_プロット["\']',
                "severity": "high",
                "message": "プロットパスのハードコーディングは禁止",
                "suggestion": "path_service.get_plots_dir()"
            },
            "path_hardcoding_management": {
                "pattern": r'["\']50_管理資料["\']',
                "severity": "high",
                "message": "管理資料パスのハードコーディングは禁止",
                "suggestion": "path_service.get_management_dir()"
            },
            "path_hardcoding_quality": {
                "pattern": r'["\']60_作業ファイル["\']',
                "severity": "medium",
                "message": "作業ファイルパスのハードコーディングは禁止",
                "suggestion": "path_service.get_quality_records_dir()"
            },
            "repository_direct_instantiation": {
                "pattern": r"class\s+\w+Repository(?!.*\(.*Repository\))",
                "severity": "medium",
                "message": "Repository ABCを継承していない可能性",
                "suggestion": "適切なRepository ABCを継承すること"
            },
            "error_handling_duplication": {
                "pattern": r"except\s+\w+Exception.*:\s*print\(",
                "severity": "medium",
                "message": "エラーハンドリングの重複",
                "suggestion": "handle_command_error()を使用"
            }
        }

    def detect_all_violations(self) -> list[DuplicationViolation]:
        """全ての重複実装違反を検出"""
        self.violations.clear()

        # src/ディレクトリのPythonファイルを検索
        src_files = list((self.project_root / "src").rglob("*.py"))

        for file_path in src_files:
            self._detect_violations_in_file(file_path)

        return self.violations

    def _detect_violations_in_file(self, file_path: Path) -> None:
        """単一ファイル内の重複実装違反を検出"""
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            for line_num, line in enumerate(lines, 1):
                for pattern_name, pattern_info in self.patterns.items():
                    if re.search(pattern_info["pattern"], line):
                        violation = DuplicationViolation(
                            file_path=file_path,
                            line_number=line_num,
                            violation_type=pattern_name,
                            content=line.strip(),
                            suggestion=pattern_info["suggestion"],
                            severity=pattern_info["severity"]
                        )
                        self.violations.append(violation)

        except Exception as e:
            self.console.print(f"❌ ファイル読み込みエラー: {file_path} - {e}", style="red")

    def generate_report(self) -> dict[str, int]:
        """検出結果レポートを生成"""
        if not self.violations:
            self.console.print("✅ 重複実装違反は検出されませんでした！", style="green")
            return {"total": 0}

        # 重要度別集計
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        violation_type_counts = {}

        for violation in self.violations:
            severity_counts[violation.severity] += 1
            violation_type_counts[violation.violation_type] = \
                violation_type_counts.get(violation.violation_type, 0) + 1

        # サマリー表示
        self.console.print("\n" + "="*60)
        self.console.print("🔍 重複実装検出結果", style="bold blue")
        self.console.print("="*60)

        # 重要度別表
        severity_table = Table(title="重要度別違反数")
        severity_table.add_column("重要度", style="cyan")
        severity_table.add_column("件数", style="magenta")
        severity_table.add_column("説明", style="white")

        severity_table.add_row("Critical", str(severity_counts["critical"]), "即座修正必須")
        severity_table.add_row("High", str(severity_counts["high"]), "高優先度")
        severity_table.add_row("Medium", str(severity_counts["medium"]), "中優先度")
        severity_table.add_row("Low", str(severity_counts["low"]), "低優先度")

        self.console.print(severity_table)

        # 詳細違反リスト
        if severity_counts["critical"] > 0:
            self._show_critical_violations()

        return {
            "total": len(self.violations),
            **severity_counts,
            "by_type": violation_type_counts
        }

    def _show_critical_violations(self) -> None:
        """Critical重要度の違反詳細を表示"""
        critical_violations = [v for v in self.violations if v.severity == "critical"]

        if not critical_violations:
            return

        self.console.print("\n🚨 Critical違反（即座修正必須）", style="bold red")

        for violation in critical_violations:
            panel_content = f"""
📁 ファイル: {violation.file_path.relative_to(self.project_root)}
📍 行番号: {violation.line_number}
🔍 違反内容: {violation.content}
💡 修正提案: {violation.suggestion}
            """.strip()

            self.console.print(Panel(
                panel_content,
                title=f"[red]❌ {violation.violation_type}[/red]",
                border_style="red"
            ))

    def auto_fix_violations(self) -> int:
        """自動修正可能な違反を修正"""
        fixed_count = 0

        # Console重複の自動修正
        console_fixes = self._fix_console_duplications()
        fixed_count += console_fixes

        # パスハードコーディングの自動修正
        path_fixes = self._fix_path_hardcoding()
        fixed_count += path_fixes

        self.console.print(f"✅ {fixed_count}件の違反を自動修正しました", style="green")
        return fixed_count

    def _fix_console_duplications(self) -> int:
        """Console重複の自動修正"""
        fixed_count = 0

        console_violations = [
            v for v in self.violations
            if v.violation_type in ["console_duplication", "console_import_duplication"]
        ]

        # ファイル別にグループ化
        files_to_fix = {}
        for violation in console_violations:
            if violation.file_path not in files_to_fix:
                files_to_fix[violation.file_path] = []
            files_to_fix[violation.file_path].append(violation)

        for file_path, violations in files_to_fix.items():
            try:
                content = file_path.read_text(encoding="utf-8")

                # Console関連の置換
                content = re.sub(
                    r"from\s+rich\.console\s+import\s+Console",
                    "# Fixed: Use shared console\n# B20準拠: 共有コンソール使用\nfrom noveler.presentation.shared.shared_utilities import console",
                    content
                )
                content = re.sub(
                    r"console\s*=\s*Console\(\)",
                    "# Fixed: Use shared console instead",
                    content
                )

                # shared_utilities importを追加（まだない場合）
                if "from noveler.presentation.shared.shared_utilities import" not in content:
                    import_section = "from noveler.presentation.shared.shared_utilities import console\n"
                    content = import_section + content

                file_path.write_text(content, encoding="utf-8")
                fixed_count += len(violations)

                self.console.print(f"🔧 修正完了: {file_path.name}", style="yellow")

            except Exception as e:
                self.console.print(f"❌ 修正失敗: {file_path} - {e}", style="red")

        return fixed_count

    def _fix_path_hardcoding(self) -> int:
        """パスハードコーディングの自動修正"""
        fixed_count = 0

        path_violations = [
            v for v in self.violations
            if v.violation_type.startswith("path_hardcoding")
        ]

        # 実装は複雑になるため、警告のみ表示
        if path_violations:
            self.console.print("⚠️ パスハードコーディング違反が検出されました", style="yellow")
            self.console.print("手動でCommonPathServiceに移行してください", style="yellow")

        return 0

def main():
    """メイン実行関数"""
    detector = DuplicateImplementationDetector()

    # コマンドライン引数確認
    auto_fix = "--fix" in sys.argv

    print("🔍 重複実装検出を開始...")

    # 違反検出
    violations = detector.detect_all_violations()

    # レポート生成
    report = detector.generate_report()

    # 自動修正実行
    if auto_fix and violations:
        print("\n🔧 自動修正を実行...")
        fixed = detector.auto_fix_violations()

        if fixed > 0:
            # 修正後の再検証
            print("\n🔍 修正後の再検証...")
            detector.detect_all_violations()
            detector.generate_report()

    # 終了コード
    critical_count = report.get("critical", 0)
    if critical_count > 0:
        print(f"\n❌ {critical_count}件のCritical違反があります。修正してください。")
        sys.exit(1)
    else:
        print("\n✅ Critical違反はありません。")
        sys.exit(0)

if __name__ == "__main__":
    main()
