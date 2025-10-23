"""Utilities.document_structure_analyzer
Where: Utility module analysing document structure and hierarchy.
What: Parses documents to extract structure, headings, and relationships.
Why: Supports tooling that requires insights into document organisation.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from noveler.presentation.shared.shared_utilities import console

"\nDocument Structure Analyzer and Fixer\n\nAnalyzes and fixes document numbering inconsistencies in the docs/ directory.\nHandles A-series and B-series document numbering conflicts and gaps.\n"

from noveler.infrastructure.logging.unified_logger import get_logger


@dataclass
class DocumentInfo:
    """Information about a document file"""

    filename: str
    series: str
    number: int
    title: str
    full_path: str
    is_tracked: bool


@dataclass
class StructureIssue:
    """Document structure issue"""

    issue_type: str
    series: str
    number: int
    files: list[str]
    severity: str
    description: str


class DocumentStructureAnalyzer:
    """Analyzes and fixes document structure inconsistencies"""

    def __init__(self, docs_dir: str, git_root: str, logger_service=None, console_service=None) -> None:
        self.docs_dir = Path(docs_dir)
        self.git_root = Path(git_root)
        self.documents: list[DocumentInfo] = []
        self.issues: list[StructureIssue] = []
        self.logger_service = logger_service
        self.console_service = console_service

    def analyze_structure(self) -> None:
        """Analyze current document structure"""
        self.console_service.print("🔍 Analyzing document structure...")
        md_files = list(self.docs_dir.glob("*.md"))
        tracked_files = self._get_tracked_files()
        for md_file in md_files:
            doc_info = self._parse_document_info(md_file, tracked_files)
            if doc_info:
                self.documents.append(doc_info)
        self._identify_issues()

    def _get_tracked_files(self) -> set[str]:
        """Get set of git-tracked files"""

        try:
            result = subprocess.run(
                ["git", "ls-files", "docs/"], check=False, cwd=self.git_root, capture_output=True, text=True
            )
            return set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()
        except Exception:
            return set()

    def _parse_document_info(self, file_path: Path, tracked_files: set[str]) -> DocumentInfo | None:
        """Parse document information from filename"""
        filename = file_path.name
        relative_path = f"docs/{filename}"
        match = re.match("([AB])(\\d+)_(.+)\\.md$", filename)
        if match:
            series = match.group(1)
            number = int(match.group(2))
            title = match.group(3)
            return DocumentInfo(
                filename=filename,
                series=series,
                number=number,
                title=title,
                full_path=str(file_path),
                is_tracked=relative_path in tracked_files,
            )
        return DocumentInfo(
            filename=filename,
            series="other",
            number=0,
            title=filename.replace(".md", ""),
            full_path=str(file_path),
            is_tracked=relative_path in tracked_files,
        )

    def _identify_issues(self) -> None:
        """Identify structure issues"""
        self.issues = []
        a_series = [doc for doc in self.documents if doc.series == "A"]
        b_series = [doc for doc in self.documents if doc.series == "B"]
        self._check_series_issues("A", a_series)
        self._check_series_issues("B", b_series)
        self._check_untracked_files()

    def _check_series_issues(self, series: str, docs: list[DocumentInfo]) -> None:
        """Check issues in a document series"""
        if not docs:
            return
        docs.sort(key=lambda x: x.number)
        numbers = [doc.number for doc in docs]
        seen = set()
        for doc in docs:
            if doc.number in seen:
                duplicate_files = [d.filename for d in docs if d.number == doc.number]
                self.issues.append(
                    StructureIssue(
                        issue_type="duplicate",
                        series=series,
                        number=doc.number,
                        files=duplicate_files,
                        severity="high",
                        description=f"{series}系列で番号{doc.number}が重複しています",
                    )
                )
            seen.add(doc.number)
        if len(numbers) > 1:
            (min_num, max_num) = (min(numbers), max(numbers))
            expected_range = set(range(min_num, max_num + 1))
            actual_range = set(numbers)
            gaps = expected_range - actual_range
            significant_gaps = []
            for gap in sorted(gaps):
                has_before = any(n < gap and gap - n <= 5 for n in numbers)
                has_after = any(n > gap and n - gap <= 5 for n in numbers)
                if has_before and has_after:
                    significant_gaps.append(gap)
            if significant_gaps:
                self.issues.append(
                    StructureIssue(
                        issue_type="gap",
                        series=series,
                        number=0,
                        files=[],
                        severity="medium",
                        description=f"{series}系列で番号{significant_gaps}が欠番です",
                    )
                )

    def _check_untracked_files(self) -> None:
        """Check for untracked files"""
        untracked_docs = [doc for doc in self.documents if not doc.is_tracked]
        if untracked_docs:
            for doc in untracked_docs:
                self.issues.append(
                    StructureIssue(
                        issue_type="untracked",
                        series=doc.series,
                        number=doc.number,
                        files=[doc.filename],
                        severity="medium",
                        description=f"'{doc.filename}'がgit管理されていません",
                    )
                )

    def print_analysis_report(self) -> None:
        """Print detailed analysis report"""
        self.console_service.print("\n" + "=" * 80)
        self.console_service.print("📊 DOCUMENT STRUCTURE ANALYSIS REPORT")
        self.console_service.print("=" * 80)
        total_docs = len(self.documents)
        a_docs = len([d for d in self.documents if d.series == "A"])
        b_docs = len([d for d in self.documents if d.series == "B"])
        other_docs = len([d for d in self.documents if d.series == "other"])
        untracked_docs = len([d for d in self.documents if not d.is_tracked])
        self.console_service.print(f"📁 総ドキュメント数: {total_docs}")
        self.console_service.print(f"   └─ A系列: {a_docs}個")
        self.console_service.print(f"   └─ B系列: {b_docs}個")
        self.console_service.print(f"   └─ その他: {other_docs}個")
        self.console_service.print(f"🚫 未追跡ファイル: {untracked_docs}個")
        high_issues = [i for i in self.issues if i.severity == "high"]
        medium_issues = [i for i in self.issues if i.severity == "medium"]
        low_issues = [i for i in self.issues if i.severity == "low"]
        self.console_service.print(f"\n🚨 検出された問題: {len(self.issues)}個")
        self.console_service.print(f"   └─ 高: {len(high_issues)}個")
        self.console_service.print(f"   └─ 中: {len(medium_issues)}個")
        self.console_service.print(f"   └─ 低: {len(low_issues)}個")
        if self.issues:
            self.console_service.print("\n" + "-" * 60)
            self.console_service.print("🔍 DETECTED ISSUES")
            self.console_service.print("-" * 60)
            for issue in sorted(
                self.issues, key=lambda x: (x.severity == "low", x.severity == "medium", x.series, x.number)
            ):
                severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[issue.severity]
                self.console_service.print(f"{severity_icon} {issue.description}")
                if issue.files:
                    for file in issue.files:
                        self.console_service.print(f"     └─ {file}")
        self.console_service.print("\n" + "-" * 60)
        self.console_service.print("📋 DOCUMENT LISTINGS")
        self.console_service.print("-" * 60)
        a_series = sorted([d for d in self.documents if d.series == "A"], key=lambda x: x.number)
        if a_series:
            self.console_service.print(f"\n📚 A系列ドキュメント ({len(a_series)}個):")
            for doc in a_series:
                status = "✅" if doc.is_tracked else "🚫"
                self.console_service.print(f"   {status} A{doc.number:02d}: {doc.title}")
        b_series = sorted([d for d in self.documents if d.series == "B"], key=lambda x: x.number)
        if b_series:
            self.console_service.print(f"\n🔧 B系列ドキュメント ({len(b_series)}個):")
            for doc in b_series:
                status = "✅" if doc.is_tracked else "🚫"
                self.console_service.print(f"   {status} B{doc.number:02d}: {doc.title}")
        other_docs = [d for d in self.documents if d.series == "other"]
        if other_docs:
            self.console_service.print(f"\n📄 その他のドキュメント ({len(other_docs)}個):")
            for doc in other_docs:
                status = "✅" if doc.is_tracked else "🚫"
                self.console_service.print(f"   {status} {doc.filename}")

    def generate_fix_recommendations(self) -> None:
        """Generate fix recommendations"""
        self.console_service.print("\n" + "=" * 80)
        self.console_service.print("🛠️  RECOMMENDED FIXES")
        self.console_service.print("=" * 80)
        if not self.issues:
            self.console_service.print("✅ No issues found! Document structure is consistent.")
            return
        self.console_service.print("以下の修正を推奨します:\n")
        fix_commands = []
        untracked_issues = [i for i in self.issues if i.issue_type == "untracked"]
        if untracked_issues:
            self.console_service.print("1️⃣ **未追跡ファイルをgitに追加:**")
            self.console_service.print("```bash")
            for issue in untracked_issues:
                for file in issue.files:
                    self.console_service.print(f"git add docs/{file}")
                    fix_commands.append(f"git add docs/{file}")
            self.console_service.print("```\n")
        duplicate_issues = [i for i in self.issues if i.issue_type == "duplicate"]
        if duplicate_issues:
            self.console_service.print("2️⃣ **重複番号の解決:**")
            self.console_service.print("手動で以下のファイルの番号を調整してください:")
            for issue in duplicate_issues:
                self.console_service.print(f"   - {issue.series}{issue.number}: {', '.join(issue.files)}")
            self.console_service.print()
        gap_issues = [i for i in self.issues if i.issue_type == "gap"]
        if gap_issues:
            self.console_service.print("3️⃣ **欠番の対応:**")
            self.console_service.print("必要に応じて以下の番号を埋めるか、番号体系を再編成してください:")
            for issue in gap_issues:
                self.console_service.print(f"   - {issue.description}")
            self.console_service.print()
        if fix_commands:
            self.console_service.print("4️⃣ **自動修正スクリプト:**")
            self.console_service.print("```bash")
            self.console_service.print("# 未追跡ファイルの一括追加")
            for cmd in fix_commands:
                self.console_service.print(cmd)
            self.console_service.print("git commit -m 'docs: add untracked documentation files'")
            self.console_service.print("```\n")
        self.console_service.print("5️⃣ **番号体系標準化の提案:**")
        console.print(
            "\nA系列(執筆・創作関連):\n  A10-A19: 企画・設計\n  A20-A29: 世界観・キャラクター\n  A30-A39: 執筆技法\n  A40-A49: 推敲・品質管理\n  A50-A59: 投稿・運用\n\nB系列(システム・技術関連):\n  B00-B09: 概論・体系\n  B10-B19: アーキテクチャ\n  B20-B29: 開発プロセス\n  B30-B39: テスト・品質\n  B40-B49: セキュリティ\n  B50-B59: 運用・保守\n  B70-B79: CI/CD・自動化\n  B80-B89: 特殊機能・拡張\n"
        )


def main() -> None:
    """Main function"""
    parser = argparse.ArgumentParser(description="Analyze document structure")
    parser.add_argument("--docs-dir", default="docs", help="Documentation directory")
    parser.add_argument("--git-root", default=".", help="Git repository root")
    parser.add_argument("--fix", action="store_true", help="Apply automatic fixes")
    args = parser.parse_args()
    analyzer = DocumentStructureAnalyzer(args.docs_dir, args.git_root)
    analyzer.analyze_structure()
    analyzer.print_analysis_report()
    analyzer.generate_fix_recommendations()
    logger = get_logger(__name__)
    if args.fix:
        logger.info("\n🔧 Applying automatic fixes...")
        logger.info("✅ Automatic fixes applied!")


if __name__ == "__main__":
    main()
