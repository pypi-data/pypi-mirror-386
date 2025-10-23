# File: tests/unit/scripts/test_task_table_sync.py
# Purpose: Validate automated movement of TODO entries into the changelog.
# Context: Covers scripts/task_table_sync.py parsing and sync behaviour.

"""Unit tests for scripts.task_table_sync."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts import task_table_sync


def write_file(path: Path, content: str) -> None:
    """Helper to persist UTF-8 text with trailing newline."""
    path.write_text(content.strip() + "\n", encoding="utf-8")


def read_between_markers(path: Path, start_marker: str, end_marker: str) -> list[str]:
    """Return lines located between the marker pair (exclusive)."""
    lines = path.read_text(encoding="utf-8").splitlines()
    start = lines.index(start_marker) + 1
    end = lines.index(end_marker)
    return lines[start:end]


def parse_data_rows(lines: list[str]) -> list[list[str]]:
    """Extract body rows as cell lists, ignoring header and separator."""
    rows: list[list[str]] = []
    for index, line in enumerate(lines):
        if not line.startswith("|"):
            continue
        content = line.strip().strip("|").replace("-", "").replace(" ", "")
        if content == "":
            # Skip separator rows such as | --- |
            continue
        if index == 0:
            # Skip header row
            continue
        cells = task_table_sync._split_table_row(line)
        rows.append(cells)
    return rows


@pytest.fixture()
def sample_files(tmp_path: Path) -> tuple[Path, Path]:
    """Prepare temporary TODO and changelog files for tests."""
    todo_text = """
# TODO

<!-- TASK_TABLE_START -->
| ID | Title | Owner | Status | Created | Due | Completed | Commit | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TODO-2025-001 | Sample task | yamada | done | 2025-10-10 | 2025-10-12 | 2025-10-12 | abc1234 | all good |
| TODO-2025-002 | In-progress task | yamada | active | 2025-10-11 |  |  |  | follow-up needed |
<!-- TASK_TABLE_END -->
"""
    changelog_text = """
# Changelog

<!-- CHANGELOG_TABLE_START -->
| ID | Title | Owner | Completed | Commit | Notes |
| --- | --- | --- | --- | --- | --- |
<!-- CHANGELOG_TABLE_END -->
"""
    todo_path = tmp_path / "TODO.md"
    changelog_path = tmp_path / "CHANGELOG.md"
    write_file(todo_path, todo_text)
    write_file(changelog_path, changelog_text)
    return todo_path, changelog_path


def test_sync_moves_done_rows(sample_files: tuple[Path, Path]) -> None:
    """Rows marked done with commit information should move into changelog."""
    todo_path, changelog_path = sample_files

    summary = task_table_sync.sync_tables(todo_path, changelog_path, dry_run=False)

    assert summary.moved_ids == ["TODO-2025-001"]
    assert not summary.skipped_duplicates
    assert not summary.skipped_missing_fields

    todo_rows = read_between_markers(todo_path, task_table_sync.TODO_TABLE_START, task_table_sync.TODO_TABLE_END)
    changelog_rows = read_between_markers(
        changelog_path,
        task_table_sync.CHANGELOG_TABLE_START,
        task_table_sync.CHANGELOG_TABLE_END,
    )

    todo_cells = parse_data_rows(todo_rows)
    changelog_cells = parse_data_rows(changelog_rows)

    assert not any(row[0] == "TODO-2025-001" for row in todo_cells)
    migrated = next(row for row in changelog_cells if row[0] == "TODO-2025-001")
    assert migrated[1].startswith("Sample")
    assert any(row[0] == "TODO-2025-002" for row in todo_cells)


def test_sync_skips_rows_missing_commit(sample_files: tuple[Path, Path]) -> None:
    """Rows without a commit ID stay in TODO and are reported as skipped."""
    todo_path, changelog_path = sample_files

    # Remove the commit from the done row.
    content = todo_path.read_text(encoding="utf-8").replace("abc1234", "")
    todo_path.write_text(content, encoding="utf-8")

    summary = task_table_sync.sync_tables(todo_path, changelog_path, dry_run=False)

    assert summary.moved_ids == []
    assert summary.skipped_missing_fields == ["TODO-2025-001"]

    todo_rows = read_between_markers(todo_path, task_table_sync.TODO_TABLE_START, task_table_sync.TODO_TABLE_END)
    todo_cells = parse_data_rows(todo_rows)
    assert any(row[0] == "TODO-2025-001" for row in todo_cells)


def test_sync_skips_duplicates(tmp_path: Path, sample_files: tuple[Path, Path]) -> None:
    """Rows whose ID already exists in the changelog are not duplicated."""
    todo_path, changelog_path = sample_files

    changelog_content = changelog_path.read_text(encoding="utf-8").replace(
        "| --- | --- | --- | --- | --- | --- |",
        "| --- | --- | --- | --- | --- | --- |\n| TODO-2025-001 | Older entry | yamada | 2025-10-11 | zyx9876 | checked |",
    )
    changelog_path.write_text(changelog_content, encoding="utf-8")

    summary = task_table_sync.sync_tables(todo_path, changelog_path, dry_run=False)

    assert summary.moved_ids == []
    assert summary.skipped_duplicates == ["TODO-2025-001"]

    changelog_rows = read_between_markers(
        changelog_path,
        task_table_sync.CHANGELOG_TABLE_START,
        task_table_sync.CHANGELOG_TABLE_END,
    )
    data_rows = parse_data_rows(changelog_rows)
    assert sum(row[0] == "TODO-2025-001" for row in data_rows) == 1


def test_sync_handles_missing_markers(tmp_path: Path) -> None:
    """Missing markers should raise helpful error message."""
    todo_path = tmp_path / "TODO.md"
    changelog_path = tmp_path / "CHANGELOG.md"

    write_file(todo_path, "# TODO\n\nNo markers here\n")
    write_file(changelog_path, "# Changelog\n\n")

    with pytest.raises(task_table_sync.TableParseError, match="TASK_TABLE_START"):
        task_table_sync.sync_tables(todo_path, changelog_path, dry_run=True)


def test_sync_handles_empty_table(tmp_path: Path) -> None:
    """Empty table (header only) should not crash."""
    todo_text = """
# TODO

<!-- TASK_TABLE_START -->
| ID | Title | Owner | Status | Created | Due | Completed | Commit | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
<!-- TASK_TABLE_END -->
"""
    changelog_text = """
# Changelog

<!-- CHANGELOG_TABLE_START -->
| ID | Title | Owner | Completed | Commit | Notes |
| --- | --- | --- | --- | --- | --- |
<!-- CHANGELOG_TABLE_END -->
"""
    todo_path = tmp_path / "TODO.md"
    changelog_path = tmp_path / "CHANGELOG.md"
    write_file(todo_path, todo_text)
    write_file(changelog_path, changelog_text)

    summary = task_table_sync.sync_tables(todo_path, changelog_path, dry_run=False)

    assert summary.moved_count == 0
    assert summary.moved_ids == []


def test_sync_handles_malformed_table_row(tmp_path: Path) -> None:
    """Malformed rows (column mismatch) should raise error."""
    todo_text = """
# TODO

<!-- TASK_TABLE_START -->
| ID | Title | Owner | Status | Created | Due | Completed | Commit | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TODO-2025-001 | Missing columns | yamada |
<!-- TASK_TABLE_END -->
"""
    changelog_text = """
# Changelog

<!-- CHANGELOG_TABLE_START -->
| ID | Title | Owner | Completed | Commit | Notes |
| --- | --- | --- | --- | --- | --- |
<!-- CHANGELOG_TABLE_END -->
"""
    todo_path = tmp_path / "TODO.md"
    changelog_path = tmp_path / "CHANGELOG.md"
    write_file(todo_path, todo_text)
    write_file(changelog_path, changelog_text)

    with pytest.raises(task_table_sync.TableParseError, match="列数が一致しません"):
        task_table_sync.sync_tables(todo_path, changelog_path, dry_run=False)


def test_sync_handles_file_not_found(tmp_path: Path) -> None:
    """Missing TODO.md or CHANGELOG.md should raise helpful error."""
    todo_path = tmp_path / "nonexistent_TODO.md"
    changelog_path = tmp_path / "CHANGELOG.md"

    write_file(changelog_path, "# Changelog\n")

    with pytest.raises(task_table_sync.TableParseError, match="が見つかりません"):
        task_table_sync.sync_tables(todo_path, changelog_path, dry_run=True)


def test_format_only_keeps_done_rows(sample_files: tuple[Path, Path]) -> None:
    """Formatting mode should not move completed rows."""
    todo_path, changelog_path = sample_files

    summary = task_table_sync.sync_tables(
        todo_path,
        changelog_path,
        dry_run=False,
        format_only=True,
    )

    assert summary.moved_ids == []

    todo_rows = read_between_markers(todo_path, task_table_sync.TODO_TABLE_START, task_table_sync.TODO_TABLE_END)
    todo_cells = parse_data_rows(todo_rows)
    assert any(row[0] == "TODO-2025-001" for row in todo_cells)


def test_check_only_detects_invalid_status(sample_files: tuple[Path, Path]) -> None:
    """Check-only mode should surface validation errors."""
    todo_path, changelog_path = sample_files
    content = todo_path.read_text(encoding="utf-8").replace("active", "wip")
    todo_path.write_text(content, encoding="utf-8")

    with pytest.raises(task_table_sync.TableParseError, match="許可されていません"):
        task_table_sync.sync_tables(
            todo_path,
            changelog_path,
            dry_run=True,
            check_only=True,
        )


def test_check_only_passes_for_valid_tables(sample_files: tuple[Path, Path]) -> None:
    """Check-only mode should exit cleanly for valid tables."""
    todo_path, changelog_path = sample_files
    todo_before = todo_path.read_text(encoding="utf-8")
    changelog_before = changelog_path.read_text(encoding="utf-8")

    summary = task_table_sync.sync_tables(
        todo_path,
        changelog_path,
        dry_run=True,
        check_only=True,
    )

    assert summary.moved_count == 0
    assert todo_before == todo_path.read_text(encoding="utf-8")
    assert changelog_before == changelog_path.read_text(encoding="utf-8")


def test_sync_dry_run_does_not_modify_files(sample_files: tuple[Path, Path]) -> None:
    """Dry-run mode should not write any changes to disk."""
    todo_path, changelog_path = sample_files

    todo_content_before = todo_path.read_text(encoding="utf-8")
    changelog_content_before = changelog_path.read_text(encoding="utf-8")

    summary = task_table_sync.sync_tables(todo_path, changelog_path, dry_run=True)

    todo_content_after = todo_path.read_text(encoding="utf-8")
    changelog_content_after = changelog_path.read_text(encoding="utf-8")

    # Files should be unchanged
    assert todo_content_before == todo_content_after
    assert changelog_content_before == changelog_content_after

    # But summary should reflect what WOULD be moved
    assert summary.moved_ids == ["TODO-2025-001"]
