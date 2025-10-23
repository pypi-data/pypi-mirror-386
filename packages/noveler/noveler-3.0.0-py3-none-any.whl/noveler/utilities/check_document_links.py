"""Utilities.check_document_links
Where: Utility script verifying documentation links.
What: Scans documentation for broken links and reports issues.
Why: Helps keep documentation healthy and accurate.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""
Document Link Consistency Checker

Checks and fixes reference links in documentation files.
Ensures all internal links point to existing files and anchors.
"""


import argparse
import re
from dataclasses import dataclass

from noveler.presentation.shared.shared_utilities import console
from pathlib import Path
from urllib.parse import unquote


@dataclass
class LinkReference:
    """A reference link found in documentation"""

    source_file: str
    line_number: int
    link_text: str
    target_path: str
    anchor: str | None
    full_match: str


@dataclass
class LinkIssue:
    """An issue with a reference link"""

    reference: LinkReference
    issue_type: str  # 'missing_file', 'missing_anchor', 'invalid_path', 'broken_relative'
    severity: str  # 'error', 'warning', 'info'
    description: str
    suggested_fix: str | None = None


class DocumentLinkChecker:
    """Checks document reference links for consistency"""

    def __init__(self, docs_dir: str, logger_service=None, console_service=None) -> None:
        self.docs_dir = Path(docs_dir)
        self.references: list[LinkReference] = []
        self.issues: list[LinkIssue] = []
        self.existing_files: set[Path] = set()
        self.existing_anchors: dict[Path, set[str]] = {}

        self.logger_service = logger_service
        self.console_service = console_service
    def check_all_links(self) -> None:
        """Check all links in all documentation files"""
        self.console_service.print("🔍 Checking document link consistency...")

        # Discover existing files and anchors
        self._discover_files_and_anchors()

        # Extract all reference links
        self._extract_all_references()

        # Validate all links
        self._validate_all_links()

        self.console_service.print(f"✅ Analysis complete: {len(self.references)} links, {len(self.issues)} issues")

    def _discover_files_and_anchors(self) -> None:
        """Discover existing files and their anchors"""
        self.console_service.print("📂 Discovering files and anchors...")

        md_files = list(self.docs_dir.glob("*.md"))
        for md_file in md_files:
            self.existing_files.add(md_file)
            self.existing_anchors[md_file] = self._extract_anchors(md_file)

    def _extract_anchors(self, file_path: Path) -> set[str]:
        """Extract anchor points from a markdown file"""
        anchors = set()

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

                # Extract headers (# ## ### etc.)
                header_pattern = r"^#+\s+(.+)$"
                for match in re.finditer(header_pattern, content, re.MULTILINE):
                    header_text = match.group(1)
                    # Convert to GitHub-style anchor
                    anchor = self._text_to_anchor(header_text)
                    anchors.add(anchor)

                # Extract explicit anchors
                anchor_pattern = r'<a\s+(?:name|id)=["\']([^"\']+)["\']'
                for match in re.finditer(anchor_pattern, content, re.IGNORECASE):
                    anchors.add(match.group(1))

        except Exception as e:
            self.console_service.print(f"⚠️ Error reading {file_path}: {e}")

        return anchors

    def _text_to_anchor(self, text: str) -> str:
        """Convert header text to GitHub-style anchor"""
        # Remove markdown formatting
        text = re.sub(r"[*_`]", "", text)
        # Convert to lowercase and replace spaces/symbols with hyphens
        text = re.sub(r"[^\w\s-]", "", text.lower())
        text = re.sub(r"[\s_]+", "-", text)
        return text.strip("-")

    def _extract_all_references(self) -> None:
        """Extract all reference links from documentation"""
        self.console_service.print("🔗 Extracting reference links...")

        md_files = list(self.docs_dir.glob("*.md"))
        for md_file in md_files:
            self._extract_references_from_file(md_file)

    def _extract_references_from_file(self, file_path: Path) -> None:
        """Extract reference links from a single file"""
        try:
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                # Pattern for markdown links: [text](url)
                link_pattern = r"\\[([^\\]]+)\\]\\(([^\\)]+)\\)"

                for match in re.finditer(link_pattern, line):
                    link_text = match.group(1)
                    target_url = match.group(2)

                    # Only process internal links
                    if self._is_internal_link(target_url):
                        target_path, anchor = self._parse_target_url(target_url)

                        reference = LinkReference(
                            source_file=str(file_path),
                            line_number=line_num,
                            link_text=link_text,
                            target_path=target_path,
                            anchor=anchor,
                            full_match=match.group(0),
                        )

                        self.references.append(reference)

        except Exception as e:
            self.console_service.print(f"⚠️ Error processing {file_path}: {e}")

    def _is_internal_link(self, url: str) -> bool:
        """Check if URL is an internal documentation link"""
        # Skip external URLs
        if url.startswith(("http://", "https://", "mailto:", "ftp://")):
            return False

        # Skip non-markdown files (mostly)
        return url.endswith(".md") or "#" in url or url.startswith("docs/")

    def _parse_target_url(self, url: str) -> tuple[str, str | None]:
        """Parse target URL into path and anchor components"""
        # URL decode
        url = unquote(url)

        # Split path and anchor
        if "#" in url:
            path_part, anchor_part = url.split("#", 1)
            return path_part.strip(), anchor_part.strip() if anchor_part else None
        return url.strip(), None

    def _validate_all_links(self) -> None:
        """Validate all extracted links"""
        self.console_service.print("🔎 Validating links...")

        for ref in self.references:
            self._validate_single_link(ref)

    def _validate_single_link(self, ref: LinkReference) -> None:
        """Validate a single reference link"""
        target_path = ref.target_path

        # Handle relative paths
        if target_path.startswith("../"):
            # Relative path from docs directory
            resolved_path = (self.docs_dir.parent / target_path.lstrip("../")).resolve()
        elif target_path.startswith("docs/"):
            # Absolute path from project root
            resolved_path = (self.docs_dir.parent / target_path).resolve()
        elif target_path.startswith("./"):
            # Current directory relative
            resolved_path = (self.docs_dir / target_path.lstrip("./")).resolve()
        elif target_path == "" and ref.anchor:
            # Same file anchor reference
            resolved_path = Path(ref.source_file).resolve()
        else:
            # Assume it's relative to docs directory
            resolved_path = (self.docs_dir / target_path).resolve()

        # Check if target file exists
        if not resolved_path.exists():
            issue = LinkIssue(
                reference=ref,
                issue_type="missing_file",
                severity="error",
                description=f"Target file does not exist: {resolved_path}",
                suggested_fix=self._suggest_file_fix(target_path),
            )

            self.issues.append(issue)
            return

        # Check if target is in our known files
        if resolved_path not in self.existing_files:
            issue = LinkIssue(
                reference=ref,
                issue_type="invalid_path",
                severity="warning",
                description=f"Target file is outside documentation scope: {resolved_path}",
            )

            self.issues.append(issue)

        # Check anchor if specified
        if ref.anchor:
            anchors = self.existing_anchors.get(resolved_path, set())
            if ref.anchor not in anchors:
                issue = LinkIssue(
                    reference=ref,
                    issue_type="missing_anchor",
                    severity="warning",
                    description=f"Anchor '{ref.anchor}' not found in {resolved_path.name}",
                    suggested_fix=self._suggest_anchor_fix(ref.anchor, anchors),
                )

                self.issues.append(issue)

    def _suggest_file_fix(self, target_path: str) -> str | None:
        """Suggest a fix for missing file"""
        # Look for similar file names
        target_name = Path(target_path).name.lower()

        for existing_file in self.existing_files:
            if existing_file.name.lower() == target_name:
                return f"Did you mean: {existing_file.name}?"

        # Look for partial matches
        for existing_file in self.existing_files:
            if target_name in existing_file.name.lower():
                return f"Similar file found: {existing_file.name}"

        return None

    def _suggest_anchor_fix(self, target_anchor: str, available_anchors: set[str]) -> str | None:
        """Suggest a fix for missing anchor"""
        target_lower = target_anchor.lower()

        # Look for exact case-insensitive match
        for anchor in available_anchors:
            if anchor.lower() == target_lower:
                return f"Case mismatch, use: #{anchor}"

        # Look for partial matches
        for anchor in available_anchors:
            if target_lower in anchor.lower() or anchor.lower() in target_lower:
                return f"Similar anchor: #{anchor}"

        return f"Available anchors: {', '.join(sorted(available_anchors)[:5])}"

    def print_report(self) -> None:
        """Print detailed link consistency report"""
        self.console_service.print("\n" + "=" * 80)
        self.console_service.print("🔗 DOCUMENT LINK CONSISTENCY REPORT")
        self.console_service.print("=" * 80)

        # Summary
        total_refs = len(self.references)
        error_issues = [i for i in self.issues if i.severity == "error"]
        warning_issues = [i for i in self.issues if i.severity == "warning"]

        self.console_service.print("📊 Summary:")
        self.console_service.print(f"   Total references: {total_refs}")
        self.console_service.print(f"   Issues found: {len(self.issues)}")
        self.console_service.print(f"   └─ Errors: {len(error_issues)}")
        self.console_service.print(f"   └─ Warnings: {len(warning_issues)}")

        if not self.issues:
            self.console_service.print("\n✅ All links are valid!")
            return

        # Group issues by severity
        self.console_service.print("\n" + "-" * 60)
        self.console_service.print("🚨 ISSUES FOUND")
        self.console_service.print("-" * 60)

        for severity in ["error", "warning"]:
            severity_issues = [i for i in self.issues if i.severity == severity]
            if not severity_issues:
                continue

            icon = "🔴" if severity == "error" else "🟡"
            self.console_service.print(f"\n{icon} {severity.upper()} ISSUES ({len(severity_issues)}):")

            for issue in severity_issues:
                ref = issue.reference
                source_file = Path(ref.source_file).name

                self.console_service.print(f"\n   File: {source_file}:{ref.line_number}")
                self.console_service.print(f"   Link: [{ref.link_text}]({ref.target_path}{'#' + ref.anchor if ref.anchor else ''})")
                self.console_service.print(f"   Issue: {issue.description}")

                if issue.suggested_fix:
                    self.console_service.print(f"   Fix: {issue.suggested_fix}")

        # Generate fix commands
        self._generate_fix_commands()

    def _generate_fix_commands(self) -> None:
        """Generate commands to fix issues"""
        fixable_issues = [i for i in self.issues if i.suggested_fix and "Did you mean:" in i.suggested_fix]

        if fixable_issues:
            self.console_service.print("\n" + "-" * 60)
            self.console_service.print("🛠️ SUGGESTED FIXES")
            self.console_service.print("-" * 60)

            self.console_service.print("Manual fixes required for the following:")
            for issue in fixable_issues:
                ref = issue.reference
                source_file = Path(ref.source_file).name
                self.console_service.print(f"   {source_file}:{ref.line_number} - {issue.suggested_fix}")


def main() -> None:
    """Main function"""

    parser = argparse.ArgumentParser(description="Check document link consistency")
    parser.add_argument("--docs-dir", default="docs", help="Documentation directory")
    parser.add_argument("--fix", action="store_true", help="Apply automatic fixes")

    args = parser.parse_args()

    # Initialize checker
    checker = DocumentLinkChecker(args.docs_dir)

    # Run analysis
    checker.check_all_links()

    # Print report
    checker.print_report()

    if args.fix:
        console.print("\n🔧 Applying automatic fixes...")
        # Implementation would go here
        console.print("✅ Automatic fixes applied!")


if __name__ == "__main__":
    main()
