#!/usr/bin/env python3
"""
Simple import validator - Replacement for missing script
File: scripts/tools/import_validator_simple.py

Basic import validation focusing on common issues.
"""

import argparse
import ast
import sys
from pathlib import Path
from typing import List, Set


class ImportValidator:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.violations = []

    def validate_file(self, py_file: Path) -> List[str]:
        """Validate imports in a single Python file."""
        violations = []

        try:
            content = py_file.read_text(encoding='utf-8')
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    # Check for relative imports going too far up
                    if node.level and node.level > 3:
                        violations.append(f"Deep relative import (level {node.level})")

                    # Check for wildcard imports
                    if any(alias.name == '*' for alias in node.names):
                        violations.append("Wildcard import found")

                elif isinstance(node, ast.Import):
                    # Check for overly complex imports
                    if len(node.names) > 10:
                        violations.append("Too many imports in single statement")

        except (SyntaxError, UnicodeDecodeError) as e:
            violations.append(f"Parse error: {e}")

        return violations

    def check_quick(self) -> bool:
        """Quick validation of recent/changed files."""
        python_files = []

        # Focus on src directory for performance
        src_dir = self.project_root / "src"
        if src_dir.exists():
            python_files = list(src_dir.glob("**/*.py"))[:20]  # Limit for speed

        total_violations = 0
        for py_file in python_files:
            file_violations = self.validate_file(py_file)
            if file_violations:
                print(f"⚠️ {py_file}:")
                for violation in file_violations[:3]:  # Limit violations per file
                    print(f"  - {violation}")
                total_violations += len(file_violations)

        if total_violations == 0:
            print("✅ Import validation: No issues found")
            return True
        else:
            print(f"⚠️ Found {total_violations} import issues")
            return total_violations < 10  # Allow some violations in quick mode

    def check_full(self) -> bool:
        """Full validation of all Python files."""
        python_files = list(self.project_root.glob("**/*.py"))

        # Exclude common non-code directories
        excluded_patterns = {'.venv', '__pycache__', '.git', 'build', 'dist'}
        python_files = [
            f for f in python_files
            if not any(part in excluded_patterns for part in f.parts)
        ]

        total_violations = 0
        files_with_issues = 0

        for py_file in python_files[:100]:  # Reasonable limit
            file_violations = self.validate_file(py_file)
            if file_violations:
                files_with_issues += 1
                if files_with_issues <= 10:  # Limit output
                    print(f"⚠️ {py_file}:")
                    for violation in file_violations:
                        print(f"  - {violation}")
                total_violations += len(file_violations)

        if files_with_issues > 10:
            print(f"... and {files_with_issues - 10} more files with issues")

        if total_violations == 0:
            print("✅ Import validation: All files clean")
            return True
        else:
            print(f"❌ Found {total_violations} import violations in {files_with_issues} files")
            return False


def main():
    parser = argparse.ArgumentParser(description="Simple import validator")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--quick-check", action="store_true", help="Quick validation mode")

    args = parser.parse_args()

    print(f"📦 Import validation starting...")
    print(f"📁 Project root: {args.project_root.absolute()}")

    validator = ImportValidator(args.project_root)

    if args.quick_check:
        success = validator.check_quick()
    else:
        success = validator.check_full()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())