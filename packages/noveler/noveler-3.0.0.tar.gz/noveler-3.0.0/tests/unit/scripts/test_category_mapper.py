# File: tests/unit/scripts/test_category_mapper.py
# Purpose: Unit tests for scripts/category_mapper.py category inference.
# Context: Validates pattern-based and commit-analysis category classification.

"""Unit tests for scripts.category_mapper."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.category_mapper import CategoryInferenceError, CategoryMapper


@pytest.fixture()
def sample_config(tmp_path: Path) -> Path:
    """Create a sample category configuration file."""
    config_content = """
rules:
  - pattern: "^(fix|bugfix):"
    category: Fixes
    description: "Bug fixes"
  - pattern: "^(feat|feature):"
    category: Features
    description: "New features"
  - pattern: "^refactor:"
    category: Refactoring
    description: "Refactoring"
  - pattern: "\\\\b(test|testing)\\\\b"
    category: Testing
    description: "Testing"

default_category: Refactoring

fallback_strategy: commit_analysis

conventional_commits:
  feat: Features
  fix: Fixes
  refactor: Refactoring
  test: Testing
  docs: Documentation

options:
  case_sensitive: false
  check_commit_messages: true
  max_commits_to_analyze: 3
"""
    config_path = tmp_path / ".task_categories.yaml"
    config_path.write_text(config_content, encoding="utf-8")
    return config_path


def test_category_mapper_initialization(sample_config: Path) -> None:
    """Category mapper should initialize with valid config."""
    mapper = CategoryMapper(sample_config)
    assert mapper.config.default_category == "Refactoring"
    assert len(mapper.config.rules) == 4


def test_category_mapper_missing_config() -> None:
    """Category mapper should raise error if config file is missing."""
    with pytest.raises(CategoryInferenceError, match="が見つかりません"):
        CategoryMapper(Path("nonexistent.yaml"))


def test_infer_category_from_title_fix(sample_config: Path) -> None:
    """Title starting with 'fix:' should infer Fixes category."""
    mapper = CategoryMapper(sample_config)
    category = mapper.infer_category(
        task_id="T001",
        title="fix: authentication bug in JWT validation",
        commits=[],
    )
    assert category == "Fixes"


def test_infer_category_from_title_feature(sample_config: Path) -> None:
    """Title starting with 'feat:' should infer Features category."""
    mapper = CategoryMapper(sample_config)
    category = mapper.infer_category(
        task_id="T002",
        title="feat: add user dashboard with charts",
        commits=[],
    )
    assert category == "Features"


def test_infer_category_from_title_refactor(sample_config: Path) -> None:
    """Title starting with 'refactor:' should infer Refactoring category."""
    mapper = CategoryMapper(sample_config)
    category = mapper.infer_category(
        task_id="T003",
        title="refactor: simplify database query logic",
        commits=[],
    )
    assert category == "Refactoring"


def test_infer_category_from_title_testing_keyword(sample_config: Path) -> None:
    """Title containing 'testing' should infer Testing category."""
    mapper = CategoryMapper(sample_config)
    category = mapper.infer_category(
        task_id="T004",
        title="Add comprehensive testing for API endpoints",
        commits=[],
    )
    assert category == "Testing"


def test_infer_category_fallback_to_default(sample_config: Path) -> None:
    """Title with no matches should fallback to default category."""
    mapper = CategoryMapper(sample_config)
    category = mapper.infer_category(
        task_id="T005",
        title="Update dependencies",
        commits=[],
    )
    assert category == "Refactoring"  # Default category


def test_infer_category_from_commit_message(sample_config: Path) -> None:
    """Should analyze commit messages when title doesn't match."""
    mapper = CategoryMapper(sample_config)

    with patch.object(mapper, "_get_commit_message", return_value="feat: implement caching layer"):
        category = mapper.infer_category(
            task_id="T006",
            title="Implement caching",
            commits=["abc1234"],
        )

    assert category == "Features"


def test_infer_category_from_conventional_commits(sample_config: Path) -> None:
    """Should recognize Conventional Commits format in commit messages."""
    mapper = CategoryMapper(sample_config)

    with patch.object(mapper, "_get_commit_message", return_value="fix(auth): resolve token expiration issue"):
        category = mapper.infer_category(
            task_id="T007",
            title="Token issue",
            commits=["def5678"],
        )

    assert category == "Fixes"


def test_infer_category_multiple_commits(sample_config: Path) -> None:
    """Should analyze multiple commits and use first match."""
    mapper = CategoryMapper(sample_config)

    commit_messages = [
        "chore: update deps",  # No match
        "feat: add feature X",  # Match: Features
        "fix: bug Y",  # Would also match but not reached
    ]

    with patch.object(mapper, "_get_commit_message", side_effect=commit_messages):
        category = mapper.infer_category(
            task_id="T008",
            title="Multiple commits",
            commits=["abc111", "abc222", "abc333"],
        )

    assert category == "Features"


def test_infer_category_max_commits_limit(sample_config: Path) -> None:
    """Should respect max_commits_to_analyze limit."""
    mapper = CategoryMapper(sample_config)

    # Config has max_commits_to_analyze: 3
    commit_messages = ["chore: update"] * 5

    with patch.object(mapper, "_get_commit_message", side_effect=commit_messages) as mock:
        mapper.infer_category(
            task_id="T009",
            title="Many commits",
            commits=["c1", "c2", "c3", "c4", "c5"],
        )

    # Should only call _get_commit_message 3 times
    assert mock.call_count == 3


def test_infer_category_case_insensitive(sample_config: Path) -> None:
    """Pattern matching should be case insensitive by default."""
    mapper = CategoryMapper(sample_config)

    category = mapper.infer_category(
        task_id="T010",
        title="FIX: uppercase fix prefix",
        commits=[],
    )

    assert category == "Fixes"


def test_get_commit_message_success(sample_config: Path) -> None:
    """_get_commit_message should retrieve commit message from git."""
    mapper = CategoryMapper(sample_config)

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="feat: add feature X\n",
        )

        message = mapper._get_commit_message("abc1234")

    assert message == "feat: add feature X"
    mock_run.assert_called_once()


def test_get_commit_message_failure(sample_config: Path) -> None:
    """_get_commit_message should return empty string on failure."""
    mapper = CategoryMapper(sample_config)

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="")

        message = mapper._get_commit_message("invalid")

    assert message == ""


def test_get_commit_message_git_not_available(sample_config: Path) -> None:
    """_get_commit_message should handle git not being available."""
    mapper = CategoryMapper(sample_config)

    with patch("subprocess.run", side_effect=FileNotFoundError):
        message = mapper._get_commit_message("abc1234")

    assert message == ""


def test_match_title_pattern_japanese_prefix(sample_config: Path) -> None:
    """Should match Japanese category prefixes (if configured)."""
    # Extend config with Japanese patterns
    config_with_japanese = sample_config.parent / ".task_categories_ja.yaml"
    config_with_japanese.write_text(
        """
rules:
  - pattern: "^(修正|バグ修正):"
    category: Fixes
    description: "Bug fixes (Japanese)"
  - pattern: "^(実装|追加):"
    category: Features
    description: "Features (Japanese)"

default_category: Refactoring
fallback_strategy: default
conventional_commits: {}
options:
  case_sensitive: false
""",
        encoding="utf-8",
    )

    mapper = CategoryMapper(config_with_japanese)

    category = mapper.infer_category(
        task_id="T011",
        title="修正: JWT認証のバグ",
        commits=[],
    )

    assert category == "Fixes"
