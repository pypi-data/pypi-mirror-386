#!/usr/bin/env python3
# File: scripts/comment_header_audit.py
# Purpose: Audit Python modules for header comment and docstring compliance.
# Context: Supports AGENTS.md standards by verifying comment coverage before commits.

"""Command-line tool to validate comment and docstring standards across src/ modules."""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


@dataclass
class Finding:
    """Represents a single compliance issue discovered during auditing."""

    file: Path
    lineno: int
    message: str

    def format(self) -> str:
        """Format the finding for human-readable output."""

        return f"{self.file}:{self.lineno}: {self.message}"


HEADER_PREFIX = "# File:"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"


def main(argv: List[str] | None = None) -> int:
    """Entry point for the audit command."""

    args = argv or sys.argv[1:]
    targets = [SRC_ROOT]
    if args:
        targets = [Path(arg) for arg in args]

    findings: list[Finding] = []
    for path in iter_python_files(targets):
        findings.extend(audit_file(path))

    if not findings:
        print("✅ Comment audit: all files meet header and docstring standards.")
        return 0

    print("❌ Comment audit: issues detected. See details below:\n")
    for finding in findings:
        print(finding.format())

    print(f"\nTotal findings: {len(findings)}")
    return 1


def iter_python_files(paths: Iterable[Path]) -> Iterable[Path]:
    """Yield Python files under the given paths."""

    for path in paths:
        if path.is_file() and path.suffix == ".py":
            yield path
        elif path.is_dir():
            for candidate in path.rglob("*.py"):
                yield candidate


def audit_file(path: Path) -> list[Finding]:
    """Inspect a single file and return any compliance findings."""

    findings: list[Finding] = []
    text = path.read_text(encoding="utf-8")
    header_finding = check_header_comment(path, text)
    if header_finding:
        findings.append(header_finding)

    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        findings.append(Finding(file=path, lineno=exc.lineno or 1, message=f"Syntax error prevents audit: {exc}"))
        return findings

    module_docstring = ast.get_docstring(tree)
    if not module_docstring:
        findings.append(Finding(file=path, lineno=1, message="Missing module docstring that documents Purpose."))
    else:
        findings.extend(validate_docstring(path, 1, module_docstring, has_returns=False, has_args=False, has_raises=False))

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            doc = ast.get_docstring(node)
            if not doc:
                findings.append(Finding(file=path, lineno=node.lineno, message=f"Class '{node.name}' lacks docstring."))
                continue
            findings.extend(validate_docstring(path, node.lineno, doc, has_returns=False, has_args=False, has_raises=False))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node)
            if not doc:
                findings.append(Finding(file=path, lineno=node.lineno, message=f"Function '{node.name}' lacks docstring."))
                continue
            has_returns = function_has_return(node)
            has_raises = function_has_raise(node)
            arg_names = [arg.arg for arg in node.args.args]
            filtered_args = [name for name in arg_names if name not in {"self", "cls"}]
            findings.extend(
                validate_docstring(
                    path,
                    node.lineno,
                    doc,
                    has_returns=has_returns,
                    has_args=bool(filtered_args or node.args.kwonlyargs or node.args.vararg or node.args.kwarg),
                    has_raises=has_raises,
                )
            )
    return findings


def check_header_comment(path: Path, text: str) -> Finding | None:
    """Validate that the first meaningful line is the required header comment."""

    lines = text.splitlines()
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#!"):
            continue
        if not stripped.startswith("#"):
            return Finding(file=path, lineno=lineno, message="Missing header comment (expected '# File: ...').")
        if not stripped.startswith(HEADER_PREFIX):
            return Finding(file=path, lineno=lineno, message="Header comment must start with '# File:'")
        return None
    return Finding(file=path, lineno=1, message="File is empty or missing header comment.")


def validate_docstring(
    path: Path,
    lineno: int,
    docstring: str,
    *,
    has_returns: bool,
    has_args: bool,
    has_raises: bool,
) -> list[Finding]:
    """Check that a docstring contains required specification fields."""

    findings: list[Finding] = []
    normalized = "\n" + docstring.lower()
    if "purpose:" not in normalized:
        findings.append(Finding(file=path, lineno=lineno, message="Docstring must include 'Purpose:' section."))
    if has_args and "args:" not in normalized:
        findings.append(Finding(file=path, lineno=lineno, message="Docstring must include 'Args:' section for parameters."))
    if has_returns and "returns:" not in normalized:
        findings.append(Finding(file=path, lineno=lineno, message="Docstring must include 'Returns:' section when values are returned."))
    if has_raises and "raises:" not in normalized:
        findings.append(Finding(file=path, lineno=lineno, message="Docstring must include 'Raises:' section when exceptions are raised."))
    if "side effects" not in normalized and "side-effects" not in normalized:
        findings.append(Finding(file=path, lineno=lineno, message="Docstring must describe side effects using 'Side Effects:' section."))
    return findings


def function_has_return(node: ast.AST) -> bool:
    """Detect whether a function returns a value."""

    for child in ast.walk(node):
        if isinstance(child, ast.Return) and child.value is not None:
            return True
    return False


def function_has_raise(node: ast.AST) -> bool:
    """Detect whether a function raises an exception."""

    for child in ast.walk(node):
        if isinstance(child, ast.Raise):
            return True
    return False


if __name__ == "__main__":
    sys.exit(main())
