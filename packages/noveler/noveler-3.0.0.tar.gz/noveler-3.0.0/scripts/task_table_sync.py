# File: scripts/task_table_sync.py
# Purpose: Provide a repeatable CLI to validate, format, and move completed TODO items into CHANGELOG.md.
# Context: Follows the structured workflow documented in docs/guides/task_tracking_workflow.md.

"""Synchronise structured TODO entries with the changelog.

The command line interface supports three primary modes:

* Validation (`--check`) verifies that both tables adhere to the agreed schema.
* Formatting (`--format-only`) rewrites the tables into a canonical Markdown layout.
* Synchronisation (default) moves completed tasks from TODO.md into CHANGELOG.md,
  ensuring each migrated row includes a commit ID and completion date.

If `config/task_categories.yaml` is present, category inference is applied so that
the changelog can optionally include a `Category` column. The script tolerates
files that omit this column for backwards compatibility.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence

try:
    from scripts.category_mapper import CategoryInferenceError, CategoryMapper
except ImportError:  # pragma: no cover - optional dependency
    CategoryMapper = None  # type: ignore
    CategoryInferenceError = RuntimeError  # type: ignore

TODO_TABLE_START = "<!-- TASK_TABLE_START -->"
TODO_TABLE_END = "<!-- TASK_TABLE_END -->"
CHANGELOG_TABLE_START = "<!-- CHANGELOG_TABLE_START -->"
CHANGELOG_TABLE_END = "<!-- CHANGELOG_TABLE_END -->"

TODO_HEADERS = [
    "ID",
    "Title",
    "Owner",
    "Status",
    "Created",
    "Due",
    "Completed",
    "Commit",
    "Notes",
]
CHANGELOG_HEADERS = [
    "ID",
    "Category",
    "Title",
    "Owner",
    "Completed",
    "Commit",
    "Notes",
]
CHANGELOG_HEADERS_LEGACY = [
    "ID",
    "Title",
    "Owner",
    "Completed",
    "Commit",
    "Notes",
]
ALLOWED_STATUS = {"active", "blocked", "done"}
ID_PATTERN = re.compile(r"^TODO-\d{4}-\d{3,}$")


class TableParseError(RuntimeError):
    """Raised when the structured Markdown table cannot be parsed safely."""


@dataclass
class TableData:
    """Container for a parsed Markdown table."""

    headers: Sequence[str]
    rows: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class SyncSummary:
    """Holds migration statistics for CLI reporting."""

    moved_ids: List[str] = field(default_factory=list)
    skipped_missing_fields: List[str] = field(default_factory=list)
    skipped_duplicates: List[str] = field(default_factory=list)

    @property
    def moved_count(self) -> int:
        """Return the number of migrated tasks."""
        return len(self.moved_ids)


@dataclass
class TableMeta:
    """Metadata describing where the table resides within the document."""

    start_index: int
    end_index: int


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.check and args.apply:
        parser.error("--check と --apply は同時に指定できません。")
    if args.check and args.format_only:
        parser.error("--check と --format-only は同時に指定できません。")

    todo_path = Path(args.todo_path)
    changelog_path = Path(args.changelog_path)
    dry_run = not args.apply

    category_mapper = _load_category_mapper(Path(args.category_config))

    try:
        summary = sync_tables(
            todo_path,
            changelog_path,
            dry_run=dry_run,
            check_only=args.check,
            format_only=args.format_only,
            category_mapper=category_mapper,
        )
    except TableParseError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    if args.check:
        print("[CHECK] validation passed without issues.")
    else:
        print_summary(summary, dry_run=dry_run, format_only=args.format_only)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Construct the command line parser."""
    parser = argparse.ArgumentParser(
        description="Move completed TODO entries into CHANGELOG.md while keeping tables consistent."
    )
    parser.add_argument(
        "--todo-path",
        default="TODO.md",
        help="Path to TODO.md (default: %(default)s).",
    )
    parser.add_argument(
        "--changelog-path",
        default="CHANGELOG.md",
        help="Path to CHANGELOG.md (default: %(default)s).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes to disk. Without this flag the command runs in dry-run mode.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate tables only. Returns non-zero if problems are detected.",
    )
    parser.add_argument(
        "--format-only",
        action="store_true",
        help="Rewrite tables into canonical Markdown without moving tasks.",
    )
    parser.add_argument(
        "--category-config",
        default="config/task_categories.yaml",
        help="Path to category mapping rules (default: %(default)s).",
    )
    return parser


def sync_tables(
    todo_path: Path,
    changelog_path: Path,
    *,
    dry_run: bool,
    check_only: bool = False,
    format_only: bool = False,
    category_mapper: Optional[CategoryMapper] = None,
) -> SyncSummary:
    """Synchronise TODO and changelog tables and optionally persist the result."""
    todo_lines = _read_lines(todo_path)
    changelog_lines = _read_lines(changelog_path)

    todo_table, todo_meta = _extract_table(todo_lines, TODO_TABLE_START, TODO_TABLE_END)
    changelog_table, changelog_meta = _extract_table(
        changelog_lines, CHANGELOG_TABLE_START, CHANGELOG_TABLE_END
    )

    _validate_tables(todo_table, changelog_table, strict=check_only)

    if check_only:
        # Validation has already run; nothing else to do.
        return SyncSummary()

    summary = SyncSummary()

    if not format_only:
        _migrate_completed_rows(todo_table, changelog_table, summary, category_mapper)

    if not dry_run:
        todo_lines = _replace_table(
            todo_lines, todo_table, todo_meta.start_index, todo_meta.end_index
        )
        changelog_lines = _replace_table(
            changelog_lines,
            changelog_table,
            changelog_meta.start_index,
            changelog_meta.end_index,
        )
        _write_lines(todo_path, todo_lines)
        _write_lines(changelog_path, changelog_lines)

    return summary


def _load_category_mapper(config_path: Path) -> Optional[CategoryMapper]:
    """Return a CategoryMapper if available and configuration exists."""
    if not CategoryMapper or not config_path.exists():
        return None

    try:
        return CategoryMapper(config_path)
    except CategoryInferenceError as exc:  # pragma: no cover - defensive
        print(f"[WARN] カテゴリ推論を無効化しました: {exc}", file=sys.stderr)
        return None


def print_summary(summary: SyncSummary, dry_run: bool, format_only: bool) -> None:
    """Emit a human-readable summary to stdout."""
    operation = "FORMAT" if format_only else "SYNC"
    mode = "DRY-RUN" if dry_run else "APPLY"
    print(f"[{operation}][{mode}] moved={summary.moved_count}")
    if summary.moved_ids:
        print("  moved IDs:", ", ".join(summary.moved_ids))
    if summary.skipped_missing_fields:
        print(
            "  skipped (missing fields):",
            ", ".join(summary.skipped_missing_fields),
        )
    if summary.skipped_duplicates:
        print("  skipped (duplicate IDs):", ", ".join(summary.skipped_duplicates))


def _migrate_completed_rows(
    todo_table: TableData,
    changelog_table: TableData,
    summary: SyncSummary,
    category_mapper: Optional[CategoryMapper],
) -> None:
    """Move completed TODO rows into the changelog table."""
    existing_ids = {row.get("ID", "") for row in changelog_table.rows}
    remaining_rows: List[Dict[str, str]] = []

    for row in todo_table.rows:
        status = row.get("Status", "").strip().lower()
        commit_value = row.get("Commit", "").strip()
        completed_value = row.get("Completed", "").strip()
        task_id = row.get("ID", "").strip()

        if status != "done":
            remaining_rows.append(row)
            continue

        if not task_id or not commit_value or not completed_value:
            remaining_rows.append(row)
            summary.skipped_missing_fields.append(task_id or "<missing-id>")
            continue

        if task_id in existing_ids:
            remaining_rows.append(row)
            summary.skipped_duplicates.append(task_id)
            continue

        category_value = ""
        if category_mapper:
            title = row.get("Title", "").strip()
            commits = [c.strip() for c in commit_value.split(",") if c.strip()]
            try:
                category_value = category_mapper.infer_category(task_id, title, commits)
            except CategoryInferenceError as exc:  # pragma: no cover - defensive
                print(f"[WARN] カテゴリ推論に失敗 (ID={task_id}): {exc}", file=sys.stderr)

        changelog_entry = _build_changelog_entry(
            task_id=task_id,
            title=row.get("Title", "").strip(),
            owner=row.get("Owner", "").strip(),
            completed=completed_value,
            commit=commit_value,
            notes=row.get("Notes", "").strip(),
            category=category_value,
            headers=changelog_table.headers,
        )
        changelog_table.rows.insert(0, changelog_entry)
        existing_ids.add(task_id)
        summary.moved_ids.append(task_id)

    todo_table.rows = remaining_rows


def _build_changelog_entry(
    *,
    task_id: str,
    title: str,
    owner: str,
    completed: str,
    commit: str,
    notes: str,
    category: str,
    headers: Sequence[str],
) -> Dict[str, str]:
    """Return a changelog row aligned to the target header ordering."""
    mapping = {
        "ID": task_id,
        "Category": category,
        "Title": title,
        "Owner": owner,
        "Completed": completed,
        "Commit": commit,
        "Notes": notes,
    }
    return {header: mapping.get(header, "") for header in headers}


def _read_lines(path: Path) -> List[str]:
    """Return file contents split into lines; missing files raise a helpful error."""
    if not path.exists():
        raise TableParseError(f"{path} が見つかりません。構造化テーブルを先に作成してください。")
    return path.read_text(encoding="utf-8").splitlines()


def _write_lines(path: Path, lines: Sequence[str]) -> None:
    """Persist the given lines to disk, ensuring the file ends with a newline."""
    text = "\n".join(lines) + "\n"
    path.write_text(text, encoding="utf-8")


def _extract_table(
    lines: Sequence[str], start_marker: str, end_marker: str
) -> tuple[TableData, TableMeta]:
    """Extract and parse a Markdown table enclosed by markers."""
    try:
        start_index = lines.index(start_marker)
    except ValueError as exc:
        raise TableParseError(f"{start_marker} が見つかりません。") from exc
    try:
        end_index = lines.index(end_marker, start_index + 1)
    except ValueError as exc:
        raise TableParseError(f"{end_marker} が見つかりません。") from exc

    table_lines = [
        line for line in lines[start_index + 1 : end_index] if line.strip()
    ]
    if len(table_lines) < 2:
        raise TableParseError(
            f"{start_marker} と {end_marker} の間に有効なテーブルが存在しません。"
            "ヘッダー行と区切り行を定義してください。"
        )

    header_line = table_lines[0]
    separator_line = table_lines[1]
    headers = _split_table_row(header_line)
    if not headers:
        raise TableParseError(f"{start_marker} と {end_marker} の間にヘッダー行が見つかりません。")
    if not separator_line.startswith("|"):
        raise TableParseError("テーブルの区切り行が不正です。")

    data_rows = [
        line for line in table_lines[2:] if line.strip().startswith("|")
    ]
    parsed_rows = [_row_to_dict(headers, row_line) for row_line in data_rows]
    return (
        TableData(headers=headers, rows=parsed_rows),
        TableMeta(start_index=start_index, end_index=end_index),
    )


def _replace_table(
    original_lines: Sequence[str],
    table: TableData,
    start_index: int,
    end_index: int,
) -> List[str]:
    """Replace the table segment in the original lines with the rendered table."""
    rendered_table = _render_table(table)
    return (
        list(original_lines[: start_index + 1])
        + rendered_table
        + list(original_lines[end_index:])
    )


def _render_table(table: TableData) -> List[str]:
    """Render a table back into Markdown lines with aligned columns."""
    headers = list(table.headers)
    widths = [len(header) for header in headers]
    for row in table.rows:
        for index, header in enumerate(headers):
            widths[index] = max(widths[index], len(row.get(header, "")))

    def format_row(values: Sequence[str]) -> str:
        padded = [
            value + " " * (widths[idx] - len(value))
            for idx, value in enumerate(values)
        ]
        return "| " + " | ".join(padded) + " |"

    separator = "| " + " | ".join("-" * width for width in widths) + " |"
    lines = [format_row(headers), separator]
    for row in table.rows:
        row_values = [row.get(header, "") for header in headers]
        lines.append(format_row(row_values))
    return lines


def _split_table_row(row: str) -> List[str]:
    """Split a Markdown table row into trimmed cell values."""
    return [cell.strip() for cell in row.strip().strip("|").split("|")]


def _row_to_dict(headers: Sequence[str], row_line: str) -> Dict[str, str]:
    """Convert a Markdown table row string into a dictionary keyed by headers."""
    values = _split_table_row(row_line)
    if len(values) != len(headers):
        raise TableParseError(
            "ヘッダーと行の列数が一致しません。行の区切り記法を確認してください。"
        )
    return dict(zip(headers, values))


def _validate_tables(
    todo_table: TableData, changelog_table: TableData, *, strict: bool
) -> None:
    """Validate structure and field values prior to processing."""
    errors: List[str] = []

    if list(todo_table.headers) != TODO_HEADERS:
        errors.append(
            "TODO.md のテーブルヘッダーが期待値と一致しません。"
            f" 現在: {list(todo_table.headers)} / 期待: {TODO_HEADERS}"
        )

    if list(changelog_table.headers) == CHANGELOG_HEADERS_LEGACY:
        changelog_headers = CHANGELOG_HEADERS_LEGACY
    elif list(changelog_table.headers) == CHANGELOG_HEADERS:
        changelog_headers = CHANGELOG_HEADERS
    else:
        errors.append(
            "CHANGELOG.md のテーブルヘッダーが期待値と一致しません。"
            f" 現在: {list(changelog_table.headers)} / 許容: {CHANGELOG_HEADERS} または {CHANGELOG_HEADERS_LEGACY}"
        )
        changelog_headers = list(changelog_table.headers)

    seen_ids = set()
    for row in todo_table.rows:
        task_id = row.get("ID", "").strip()
        status = row.get("Status", "").strip().lower()
        commit_value = row.get("Commit", "").strip()
        completed_value = row.get("Completed", "").strip()

        if not task_id:
            errors.append("TODO.md に ID が空の行があります。")
        elif not ID_PATTERN.match(task_id):
            errors.append(f"ID '{task_id}' は 'TODO-YYYY-NNNN' 形式ではありません。")

        if task_id:
            if task_id in seen_ids:
                errors.append(f"TODO.md に ID '{task_id}' の重複行があります。")
            seen_ids.add(task_id)

        if status not in ALLOWED_STATUS:
            errors.append(f"ID '{task_id}' の Status '{status}' は許可されていません。")
        if status == "done":
            if not completed_value and strict:
                errors.append(f"ID '{task_id}' は Completed が空です。")
            if not commit_value and strict:
                errors.append(f"ID '{task_id}' は Commit が空です。")

    changelog_ids = set()
    for row in changelog_table.rows:
        task_id = row.get("ID", "").strip()
        completed_value = row.get("Completed", "").strip()
        commit_value = row.get("Commit", "").strip()

        if not task_id:
            errors.append("CHANGELOG.md に ID が空の行があります。")
        elif task_id in changelog_ids:
            errors.append(f"CHANGELOG.md に ID '{task_id}' の重複行があります。")
        changelog_ids.add(task_id)

        if not completed_value:
            errors.append(f"CHANGELOG.md の ID '{task_id}' は Completed が空です。")
        if not commit_value:
            errors.append(f"CHANGELOG.md の ID '{task_id}' は Commit が空です。")

    if errors:
        raise TableParseError("\n".join(errors))


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
