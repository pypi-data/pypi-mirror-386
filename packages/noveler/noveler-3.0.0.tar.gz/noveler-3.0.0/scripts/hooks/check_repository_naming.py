#!/usr/bin/env python3
"""
File: scripts/hooks/check_repository_naming.py
Purpose: Pre-commit hook to enforce Repository naming conventions
Context: Part of DDD compliance - ensures consistent naming across Domain/Infrastructure layers

Usage:
    python scripts/hooks/check_repository_naming.py

Exit codes:
    0 - All checks passed
    1 - Naming violations found
"""

import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set


def get_project_root() -> Path:
    """Get project root directory"""
    return Path(__file__).resolve().parent.parent.parent


def find_repository_files(root: Path) -> Dict[str, List[Path]]:
    """Find all repository-related files categorized by layer

    Args:
        root: Project root directory

    Returns:
        Dictionary mapping layer names to file paths
    """
    categories = {
        "domain": [],
        "infrastructure": [],
        "tests": [],
    }

    # Domain repositories
    domain_repos = root / "src" / "noveler" / "domain" / "repositories"
    if domain_repos.exists():
        categories["domain"].extend(domain_repos.rglob("*repository*.py"))

    # Infrastructure repositories
    infra_repos = root / "src" / "noveler" / "infrastructure"
    if infra_repos.exists():
        categories["infrastructure"].extend(
            [
                f
                for f in infra_repos.rglob("*repository*.py")
                if not f.name.startswith("__")
            ]
        )

    # Test files
    tests_dir = root / "tests"
    if tests_dir.exists():
        categories["tests"].extend(
            [f for f in tests_dir.rglob("*repository*.py") if not f.name.startswith("__")]
        )

    return categories


def check_infrastructure_naming(files: List[Path]) -> List[str]:
    """Check Infrastructure layer files have technology prefix

    Args:
        files: Infrastructure repository files

    Returns:
        List of violation messages
    """
    violations = []
    allowed_prefixes = ["yaml", "file", "json", "markdown"]
    allowed_patterns = [
        r"^(yaml|file|json|markdown)_.*repository\.py$",  # Preferred: {tech}_{entity}_repository.py
        r"^.*_repository_adapter\.py$",  # Allowed: *_repository_adapter.py
        r"^.*_adapter\.py$",  # Allowed: *_adapter.py
        r"^base_.*\.py$",  # Allowed: base classes
        r"^.*_factory\.py$",  # Allowed: factories
    ]

    for file_path in files:
        filename = file_path.name

        # Skip __init__.py and test files
        if filename.startswith("__") or filename.startswith("test_"):
            continue

        # Check if matches any allowed pattern
        matches_pattern = any(re.match(pattern, filename) for pattern in allowed_patterns)

        if not matches_pattern:
            # Check for prohibited *_impl.py pattern
            if filename.endswith("_impl.py"):
                violations.append(
                    f"[ERROR] {file_path.relative_to(get_project_root())}: "
                    f"'*_impl.py' suffix is prohibited (use technology prefix instead)"
                )
            else:
                # General violation
                violations.append(
                    f"[WARN] {file_path.relative_to(get_project_root())}: "
                    f"Missing technology prefix ({', '.join(allowed_prefixes)})"
                )

    return violations


def check_duplicate_filenames(all_files: Dict[str, List[Path]]) -> List[str]:
    """Check for duplicate filenames across directories

    Args:
        all_files: Dictionary of categorized repository files

    Returns:
        List of violation messages
    """
    violations = []
    filename_to_paths: Dict[str, List[Path]] = defaultdict(list)

    # Collect all filenames and their paths
    for category, files in all_files.items():
        for file_path in files:
            filename_to_paths[file_path.name].append(file_path)

    # Check for duplicates
    for filename, paths in filename_to_paths.items():
        if len(paths) <= 1:
            continue

        # Check if duplication is allowed (domain/infrastructure pair)
        if len(paths) == 2:
            path_strs = [str(p) for p in paths]
            has_domain = any("domain/repositories" in p for p in path_strs)
            has_infrastructure = any("infrastructure/repositories" in p for p in path_strs)

            if has_domain and has_infrastructure:
                # This is allowed (interface/implementation pair)
                continue

        # Duplication violation
        root = get_project_root()
        relative_paths = [str(p.relative_to(root)) for p in paths]
        violations.append(
            f"[ERROR] Duplicate filename '{filename}' found in:\n"
            + "\n".join(f"   - {p}" for p in relative_paths)
        )

    return violations


def check_domain_interface_naming(files: List[Path]) -> List[str]:
    """Check Domain layer interfaces follow simple naming pattern

    Args:
        files: Domain repository files

    Returns:
        List of violation messages
    """
    violations = []
    expected_pattern = r"^[a-z_]+_repository\.py$"

    for file_path in files:
        filename = file_path.name

        # Skip __init__.py
        if filename.startswith("__"):
            continue

        if not re.match(expected_pattern, filename):
            violations.append(
                f"[WARN] {file_path.relative_to(get_project_root())}: "
                f"Domain interface should use simple pattern: {{entity}}_repository.py"
            )

    return violations


def main() -> int:
    """Run all naming convention checks

    Returns:
        Exit code (0=success, 1=violations found)
    """
    root = get_project_root()
    print(f"[CHECK] Checking Repository naming conventions in: {root}")
    print()

    # Find all repository files
    categorized_files = find_repository_files(root)

    total_files = sum(len(files) for files in categorized_files.values())
    print(f"[INFO] Found {total_files} repository-related files:")
    for category, files in categorized_files.items():
        print(f"   - {category}: {len(files)} files")
    print()

    # Run checks
    all_violations: List[str] = []

    # 1. Domain interface naming
    domain_violations = check_domain_interface_naming(categorized_files["domain"])
    all_violations.extend(domain_violations)

    # 2. Infrastructure implementation naming
    infra_violations = check_infrastructure_naming(categorized_files["infrastructure"])
    all_violations.extend(infra_violations)

    # 3. Duplicate filenames
    duplicate_violations = check_duplicate_filenames(categorized_files)
    all_violations.extend(duplicate_violations)

    # Report results
    if all_violations:
        print("[FAIL] Repository naming violations found:\n")
        for violation in all_violations:
            print(violation)
        print()
        print("[DOCS] See: docs/architecture/repository_naming_conventions.md")
        return 1
    else:
        print("[PASS] All Repository naming checks passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
