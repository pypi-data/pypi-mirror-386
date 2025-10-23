#!/usr/bin/env python3
"""Forbidden imports quality gate for DDD layering compliance.

This script enforces DDD layering principles by detecting forbidden imports:
- Infrastructure/Application/Domain must not import from Presentation
- Domain must not import from Infrastructure/Application

Violations are reported with file path, line number, and severity.

Exit codes:
    0: No violations found
    1: Violations found (fails CI)
    2: Script execution error

Usage:
    python scripts/quality_gates/forbidden_imports_gate.py
    python scripts/quality_gates/forbidden_imports_gate.py --layer infrastructure
    python scripts/quality_gates/forbidden_imports_gate.py --verbose
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import NamedTuple


class ImportViolation(NamedTuple):
    """Represents a forbidden import violation."""

    file_path: Path
    line_number: int
    line_content: str
    layer: str
    forbidden_layer: str
    severity: str


# Forbidden import patterns by layer
FORBIDDEN_PATTERNS = {
    "domain": [
        (r"from noveler\.presentation\.", "presentation", "critical"),
        (r"from noveler\.infrastructure\.", "infrastructure", "critical"),
        (r"from noveler\.application\.", "application", "critical"),
    ],
    "application": [
        (r"from noveler\.presentation\.(?!__pycache__|tests)", "presentation", "high"),
    ],
    "infrastructure": [
        (r"from noveler\.presentation\.(?!__pycache__|tests)", "presentation", "high"),
    ],
}

# Exceptions - these imports are allowed
ALLOWED_EXCEPTIONS = [
    r"from noveler\.presentation\.cli\.shared_utilities import",  # Legacy - being phased out
    r"from noveler\.infrastructure\.utils\.infra_console import",  # New compliant pattern
    r"from noveler\.domain\.utils\.domain_console import",  # Domain console utilities
]

# Adapter pattern exceptions - Infrastructure may wrap Presentation UI components
# These are intentional architectural decisions where Infrastructure provides
# DDD-compliant adapters that delegate to Presentation layer UI systems.
ADAPTER_PATTERN_EXCEPTIONS = [
    # UI System Adapters (wrap Presentation UI for Application layer)
    r"src/noveler/infrastructure/adapters/analytics_adapter\.py",
    r"src/noveler/infrastructure/adapters/batch_processing_adapter\.py",
    # MCP Handlers (legacy code moved from Presentation, gradual refactoring)
    r"src/noveler/infrastructure/mcp/handlers\.py",
]


def detect_forbidden_imports(
    project_root: Path, layer: str | None = None, verbose: bool = False
) -> list[ImportViolation]:
    """Detect forbidden imports in the specified layer(s).

    Args:
        project_root: Root directory of the project
        layer: Specific layer to check (domain, application, infrastructure)
               If None, checks all layers
        verbose: Print detailed progress information

    Returns:
        List of ImportViolation instances
    """
    violations = []
    src_dir = project_root / "src" / "noveler"

    # Determine which layers to check
    if layer:
        layers_to_check = {layer: FORBIDDEN_PATTERNS[layer]}
    else:
        layers_to_check = FORBIDDEN_PATTERNS

    for layer_name, patterns in layers_to_check.items():
        layer_dir = src_dir / layer_name
        if not layer_dir.exists():
            if verbose:
                print(f"⚠️  Layer directory not found: {layer_dir}")
            continue

        if verbose:
            print(f"🔍 Checking {layer_name} layer...")

        # Scan all Python files in the layer
        for py_file in layer_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            try:
                violations.extend(_check_file(py_file, layer_name, patterns, verbose))
            except Exception as e:
                print(f"[ERROR] Error checking {py_file}: {e}", file=sys.stderr)

    return violations


def _check_file(
    file_path: Path, layer: str, patterns: list[tuple[str, str, str]], verbose: bool
) -> list[ImportViolation]:
    """Check a single file for forbidden imports.

    Args:
        file_path: Path to Python file
        layer: Layer name (domain, application, infrastructure)
        patterns: List of (pattern, forbidden_layer, severity) tuples
        verbose: Print detailed progress information

    Returns:
        List of violations found in this file
    """
    violations = []

    # Check if file is in adapter pattern exception list
    file_path_str = str(file_path).replace("\\", "/")
    is_adapter_exception = any(
        re.search(exc_pattern, file_path_str) for exc_pattern in ADAPTER_PATTERN_EXCEPTIONS
    )

    if is_adapter_exception:
        if verbose:
            print(f"  ✓ Adapter pattern exception: {file_path}")
        return violations

    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    for line_num, line in enumerate(lines, start=1):
        line_stripped = line.strip()

        # Skip comments and empty lines
        if not line_stripped or line_stripped.startswith("#"):
            continue

        # Check each forbidden pattern
        for pattern, forbidden_layer, severity in patterns:
            if re.search(pattern, line):
                # Check if this is an allowed exception
                is_exception = any(re.search(exc, line) for exc in ALLOWED_EXCEPTIONS)
                if is_exception:
                    if verbose:
                        print(f"  ℹ️  Allowed exception: {file_path}:{line_num}")
                    continue

                violations.append(
                    ImportViolation(
                        file_path=file_path,
                        line_number=line_num,
                        line_content=line_stripped,
                        layer=layer,
                        forbidden_layer=forbidden_layer,
                        severity=severity,
                    )
                )

    return violations


def report_violations(violations: list[ImportViolation], verbose: bool = False) -> None:
    """Report detected violations to stdout.

    Args:
        violations: List of violations to report
        verbose: Include additional details in report
    """
    if not violations:
        print("[PASS] No forbidden imports detected")
        return

    print(f"[FAIL] Found {len(violations)} forbidden import violation(s):\n")

    # Group by severity
    by_severity = {}
    for v in violations:
        by_severity.setdefault(v.severity, []).append(v)

    for severity in ["critical", "high", "medium", "low"]:
        if severity not in by_severity:
            continue

        print(f"\n{'=' * 60}")
        print(f"{severity.upper()} SEVERITY ({len(by_severity[severity])} violations)")
        print(f"{'=' * 60}\n")

        for v in by_severity[severity]:
            print(f"File: {v.file_path}")
            print(f"Line: {v.line_number}")
            print(f"Layer: {v.layer} → {v.forbidden_layer} (FORBIDDEN)")
            print(f"Code: {v.line_content}")
            if verbose:
                print(f"Severity: {v.severity}")
            print()


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 = success, 1 = violations found, 2 = error)
    """
    parser = argparse.ArgumentParser(
        description="Detect forbidden imports for DDD layering compliance"
    )
    parser.add_argument(
        "--layer",
        choices=["domain", "application", "infrastructure"],
        help="Check specific layer only",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Print detailed progress information"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).parent.parent.parent,
        help="Project root directory (default: repository root)",
    )
    args = parser.parse_args()

    try:
        violations = detect_forbidden_imports(
            project_root=args.project_root,
            layer=args.layer,
            verbose=args.verbose,
        )

        report_violations(violations, verbose=args.verbose)

        return 0 if not violations else 1

    except Exception as e:
        print(f"[FATAL] Fatal error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
