#!/usr/bin/env python3
# File: scripts/hooks/check_root_structure.py
# Purpose: Phase 2 - Root directory structure policy enforcement
# Context: docs/proposals/root-structure-policy-v2.md に基づく実装

"""Root directory structure policy checker.

This hook ensures that:
1. Only Tier 1-4 items are allowed in the repository root
2. Tier 5 items (temporary/cache) must be in .gitignore
3. New file/directory creation in root requires justification
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Set

# ============================================================================
# Tier Definitions (契約: root-structure-policy-v2.md)
# ============================================================================

# Tier 1: Core Project Files (Never Remove)
TIER1_CORE: Set[str] = {
    "README.md",
    "LICENSE",
    "CHANGELOG.md",
    "CLAUDE.md",
    "AGENTS.md",
    "TODO.md",
    "pyproject.toml",
    "uv.lock",
    ".git",
    ".gitignore",
    ".gitattributes",
    ".gitmessage",
    "src",
    "tests",
    "docs",
    "specs",
    "bin",
    "scripts",
    # Phase A additions (2025-10-03)
    "CODEMAP.yaml",
    "CODEMAP_dependencies.yaml",
    "ARCHITECTURE.md",
    "templates",
    # Phase B20 additions (2025-10-05): User data directories & deliverables
    "40_原稿",
    "50_管理資料",
    "b20-outputs",  # B20 workflow deliverables
}

# Tier 2: Tools (Review Periodically)
TIER2_TOOLS: Set[str] = {
    "Makefile",
    "requirements.txt",
    "setup.py",
    "setup.cfg",
}

# Tier 3: Project-specific Configs
TIER3_CONFIGS: Set[str] = {
    ".pre-commit-config.yaml",
    ".python-version",
    ".editorconfig",
    ".mailmap",
    "pytest.ini",
    "mypy.ini",
    "ruff.toml",
    ".importlinter",
    ".novelerrc.yaml",
    ".b20rc.yaml",
    "codex.mcp.json",
    ".codex",
    ".mcp",
    # Phase A additions (2025-10-03)
    "config",
    "package.json",
    "package-lock.json",
    "bootstrap_stdio.py",  # MCP server dependency (importlib.import_module)
    "sitecustomize.py",    # Python startup customization
    "usercustomize.py",    # Python startup customization
    # Phase C additions (2025-10-03)
    "claude_code_config.json",  # Claude Code hooks configuration
    # Phase B20 additions (2025-10-05): Config files
    ".coveragerc",
    ".ruff.toml",
    ".ruffignore",
    "app_config.yaml",
    # Phase P3 additions (2025-10-12): Anemic Domain Detection config
    ".anemic-domain.yaml",  # Anemic Domain Model detection configuration
}

# Tier 4: Development/CI
TIER4_DEVCI: Set[str] = {
    ".github",
    ".gitlab-ci.yml",
    ".travis.yml",
    "Dockerfile",
    "docker-compose.yml",
    ".dockerignore",
}

# Tier 5: Temporary/Cache (Must be in .gitignore)
TIER5_TEMPORARY: Set[str] = {
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".hypothesis",
    "build",
    "dist",
    "node_modules",
    "reports",
    "logs",
    "temp",
    ".tmp",
    ".cache",
    "workspace",
    ".serena",
    ".claude",
    # Phase A additions (2025-10-03)
    "management",  # Runtime-generated data
    "backups",     # Already in .gitignore
    # Phase B20 additions (2025-10-05): Temporary/generated directories
    ".benchmarks",
    ".dev",
    ".migration",
    ".noveler",
    ".novel_aliases",
    ".venv.win",
    "archive",
    # "b20-outputs",  # Moved to Tier 1 (deliverables should be committed)
    "plots",
    "prompts",
}

# Tier 6: Legacy (Investigate and Remove)
# Currently empty - all legacy items have been cleaned up
TIER6_LEGACY: Set[str] = set()

# Combined allowed items
ALLOWED_ITEMS: Set[str] = (
    TIER1_CORE
    | TIER2_TOOLS
    | TIER3_CONFIGS
    | TIER4_DEVCI
    | TIER5_TEMPORARY
    | TIER6_LEGACY
)


def load_gitignore(root: Path) -> Set[str]:
    """Load patterns from .gitignore.

    Args:
        root: Project root directory

    Returns:
        Set of gitignore patterns (directory names only)
    """
    gitignore_path = root / ".gitignore"
    if not gitignore_path.exists():
        return set()

    patterns = set()
    with open(gitignore_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue
            # Extract directory name (strip leading /, trailing /)
            pattern = line.strip("/")
            if pattern:
                patterns.add(pattern)

    return patterns


def check_root_structure(root: Path) -> tuple[bool, list[str]]:
    """Check if root directory structure complies with policy.

    Args:
        root: Project root directory

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors: list[str] = []
    gitignore_patterns = load_gitignore(root)

    # Check all items in root
    for item in root.iterdir():
        item_name = item.name

        # Skip .git directory
        if item_name == ".git":
            continue

        # Skip items that are in .gitignore (they won't be committed)
        if item_name in gitignore_patterns:
            continue

        # Check if item is allowed
        if item_name not in ALLOWED_ITEMS:
            errors.append(
                f"[ERROR] Forbidden item in root: {item_name}\n"
                f"        Root directory must only contain Tier 1-6 items.\n"
                f"        See: docs/proposals/root-structure-policy-v2.md"
            )
            continue

        # Check Tier 5 items are in .gitignore
        if item_name in TIER5_TEMPORARY:
            if item_name not in gitignore_patterns:
                errors.append(
                    f"[WARN] Tier 5 item not in .gitignore: {item_name}\n"
                    f"       Temporary/cache directories must be in .gitignore"
                )

    return (len(errors) == 0, errors)


def main() -> int:
    """Main entry point for pre-commit hook.

    Returns:
        0 if check passed, 1 if failed
    """
    # Find repository root
    current = Path.cwd()
    root = current
    while root.parent != root:
        if (root / ".git").exists():
            break
        root = root.parent
    else:
        print("[ERROR] Not in a Git repository", file=sys.stderr)
        return 1

    # Run check
    is_valid, errors = check_root_structure(root)

    if not is_valid:
        print("\n" + "=" * 70, file=sys.stderr)
        print("Root Structure Policy Violation", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        for error in errors:
            print(f"\n{error}", file=sys.stderr)
        print("\n" + "=" * 70, file=sys.stderr)
        print(
            "\nPolicy: docs/proposals/root-structure-policy-v2.md",
            file=sys.stderr,
        )
        print("Guideline: CLAUDE.md - Root Directory Policy", file=sys.stderr)
        print("=" * 70 + "\n", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
