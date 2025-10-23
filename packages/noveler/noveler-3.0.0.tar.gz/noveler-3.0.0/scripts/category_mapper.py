# File: scripts/category_mapper.py
# Purpose: Infer CHANGELOG category from task title and commit messages.
# Context: Used by task_table_sync.py to automate category classification.

"""Automatic category classification for CHANGELOG entries.

This module implements pattern-based and commit-analysis strategies to infer
the appropriate CHANGELOG category for completed tasks. It consumes rules from
``.task_categories.yaml`` and falls back to commit message analysis when needed.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


class CategoryInferenceError(RuntimeError):
    """Raised when category inference fails unexpectedly."""


@dataclass
class CategoryRule:
    """A single pattern-based category mapping rule."""

    pattern: re.Pattern
    category: str
    description: str


@dataclass
class CategoryConfig:
    """Configuration loaded from .task_categories.yaml"""

    rules: List[CategoryRule]
    default_category: str
    fallback_strategy: str
    conventional_commits: Dict[str, str]
    options: Dict[str, any]


class CategoryMapper:
    """Infer CHANGELOG category from task metadata."""

    def __init__(self, config_path: Path = Path("config/task_categories.yaml")):
        """Initialize the mapper with configuration from YAML file.

        Args:
            config_path: Path to the category mapping rules YAML file.

        Raises:
            CategoryInferenceError: If configuration file is missing or invalid.
        """
        if not config_path.exists():
            raise CategoryInferenceError(
                f"{config_path} が見つかりません。カテゴリルールファイルを作成してください。"
            )

        if yaml is None:
            raise CategoryInferenceError(
                "PyYAML がインストールされていません。`pip install pyyaml` を実行してください。"
            )

        self.config = self._load_config(config_path)

    def _load_config(self, path: Path) -> CategoryConfig:
        """Load and parse category configuration from YAML."""
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Parse rules
        rules = []
        for rule_data in data.get("rules", []):
            pattern_str = rule_data["pattern"]
            flags = 0 if data.get("options", {}).get("case_sensitive", False) else re.IGNORECASE
            pattern = re.compile(pattern_str, flags)
            rules.append(
                CategoryRule(
                    pattern=pattern,
                    category=rule_data["category"],
                    description=rule_data.get("description", ""),
                )
            )

        return CategoryConfig(
            rules=rules,
            default_category=data.get("default_category", "Refactoring"),
            fallback_strategy=data.get("fallback_strategy", "default"),
            conventional_commits=data.get("conventional_commits", {}),
            options=data.get("options", {}),
        )

    def infer_category(
        self,
        task_id: str,
        title: str,
        commits: Optional[List[str]] = None,
    ) -> str:
        """Infer CHANGELOG category from task title and commits.

        Args:
            task_id: Task identifier (for logging purposes).
            title: Task title (primary source for category inference).
            commits: Optional list of commit hashes to analyze.

        Returns:
            Inferred category string (e.g., "Features", "Fixes").
        """
        # Strategy 1: Pattern matching on title
        category = self._match_title_pattern(title)
        if category:
            return category

        # Strategy 2: Check commit messages (if enabled)
        if self.config.options.get("check_commit_messages", True) and commits:
            category = self._analyze_commit_messages(commits)
            if category:
                return category

        # Strategy 3: Fallback
        return self._apply_fallback_strategy(task_id, title)

    def _match_title_pattern(self, title: str) -> Optional[str]:
        """Match title against configured rules.

        Args:
            title: Task title to match.

        Returns:
            Category if match found, None otherwise.
        """
        for rule in self.config.rules:
            if rule.pattern.search(title):
                return rule.category
        return None

    def _analyze_commit_messages(self, commits: List[str]) -> Optional[str]:
        """Analyze commit messages for category hints.

        Args:
            commits: List of commit hashes to analyze.

        Returns:
            Inferred category if found, None otherwise.
        """
        max_commits = self.config.options.get("max_commits_to_analyze", 3)
        commits_to_check = commits[:max_commits]

        for commit_hash in commits_to_check:
            message = self._get_commit_message(commit_hash)
            if not message:
                continue

            # Check Conventional Commits prefix
            for prefix, category in self.config.conventional_commits.items():
                if message.lower().startswith(f"{prefix}:") or message.lower().startswith(f"{prefix}("):
                    return category

            # Check rules against commit message
            category = self._match_title_pattern(message)
            if category:
                return category

        return None

    def _get_commit_message(self, commit_hash: str) -> str:
        """Retrieve commit message from git history.

        Args:
            commit_hash: Git commit hash (short or full).

        Returns:
            Commit message subject line, or empty string if not found.
        """
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%s", commit_hash],
                capture_output=True,
                text=True,
                check=False,
                encoding="utf-8",
                errors="ignore",
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (FileNotFoundError, OSError):
            # Git not available or command failed
            pass
        return ""

    def _apply_fallback_strategy(self, task_id: str, title: str) -> str:
        """Apply fallback strategy when no rules match.

        Args:
            task_id: Task identifier (for logging).
            title: Task title (for context).

        Returns:
            Category based on fallback strategy.
        """
        strategy = self.config.fallback_strategy

        if strategy == "default":
            return self.config.default_category

        if strategy == "commit_analysis":
            # Already attempted in infer_category; use default
            return self.config.default_category

        if strategy == "prompt":
            # CLI mode: prompt user for category
            # (Not implemented in this version; fallback to default)
            return self.config.default_category

        # Unknown strategy; use default
        return self.config.default_category


def main() -> None:
    """CLI entry point for testing category inference."""
    import argparse

    parser = argparse.ArgumentParser(description="Test category inference for tasks.")
    parser.add_argument("title", help="Task title to classify")
    parser.add_argument("--commits", nargs="*", help="Commit hashes to analyze")
    parser.add_argument(
        "--config",
        default="config/task_categories.yaml",
        help="Path to category config (default: %(default)s)",
    )
    args = parser.parse_args()

    try:
        mapper = CategoryMapper(Path(args.config))
        category = mapper.infer_category(
            task_id="TEST-001",
            title=args.title,
            commits=args.commits or [],
        )
        print(f"Inferred category: {category}")
    except CategoryInferenceError as exc:
        print(f"[ERROR] {exc}")
        return


if __name__ == "__main__":
    main()
