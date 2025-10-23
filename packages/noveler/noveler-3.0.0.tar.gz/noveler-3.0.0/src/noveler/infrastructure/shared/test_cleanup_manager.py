#!/usr/bin/env python3
"""テスト実行後の自動クリーンアップマネージャー.

pytest 実行時に生成されるキャッシュやテンポラリファイルを安全に削除する。
"""

from __future__ import annotations

import os
import re
import shutil
import time
from pathlib import Path
from typing import ClassVar, Iterable

from noveler.infrastructure.logging.unified_logger import get_logger

logger = get_logger(__name__)

_PROTECTED_FILENAMES = {".gitignore", ".gitkeep", ".keep"}


def _parse_timeout(value: str | None) -> float:
    if not value:
        return 0.0
    try:
        timeout = float(value)
        return timeout if timeout > 0 else 0.0
    except (TypeError, ValueError):
        return 0.0


class TestCleanupManager:
    """テスト後クリーンアップの管理クラス."""

    __test__ = False

    CLEANUP_PATTERNS: ClassVar[list[str]] = [
        r".*_サンプル\.yaml$",
        r".*_テスト.*\.yaml$",
        r".*_test_.*\.yaml$",
        r".*_sample\.yaml$",
        r".*test_project.*\.yaml$",
        r"^第\d+話_テスト.*\.md$",
        r"^episode_\d+_test.*\.md$",
        r"品質テスト結果_\d{8}_\d{6}\.yaml$",
        r"test_quality_report_.*\.yaml$",
        r".*_test\.log$",
        r".*_pytest\.log$",
    ]

    EXCLUDE_PATTERNS: ClassVar[list[str]] = [
        r".*テンプレート\.yaml$",
        r".*template\.yaml$",
        r"requirements.*\.txt$",
        r"pyproject\.toml$",
        r"CLAUDE\.md$",
        r"README\.md$",
    ]

    SAFE_CLEANUP_DIRS: ClassVar[list[str]] = [
        "temp",
        "logs",
        "cache",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
    ]

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.cleanup_patterns = [re.compile(pattern) for pattern in self.CLEANUP_PATTERNS]
        self.exclude_patterns = [re.compile(pattern) for pattern in self.EXCLUDE_PATTERNS]

    def cleanup_test_artifacts(self, dry_run: bool) -> dict:
        result = {
            "files_deleted": [],
            "dirs_deleted": [],
            "files_protected": [],
            "errors": [],
            "total_size_freed": 0,
            "aborted": False,
        }

        # Default to "fast" to avoid scanning the entire workspace unless explicit.
        mode = os.getenv("NOVELER_TEST_CLEANUP_MODE", "fast").lower()
        timeout_value = _parse_timeout(os.getenv("NOVELER_TEST_CLEANUP_TIMEOUT"))
        deadline = time.monotonic() + timeout_value if timeout_value > 0 else None

        def timed_out() -> bool:
            return deadline is not None and time.monotonic() >= deadline

        logger.info("Starting test cleanup (dry_run=%s, mode=%s)", dry_run, mode)

        if self._cleanup_files(result, dry_run, mode, timed_out):
            result["aborted"] = True
            result["errors"].append("Cleanup aborted due to timeout during file processing")
            self._log_cleanup_summary(result, dry_run)
            return result

        if self._cleanup_directories(result, dry_run, mode, timed_out):
            result["aborted"] = True
            result["errors"].append("Cleanup aborted due to timeout during directory processing")

        self._log_cleanup_summary(result, dry_run)
        return result

    def _iter_candidate_files(self, mode: str) -> Iterable[Path]:
        if mode == "fast":
            for directory in self.SAFE_CLEANUP_DIRS:
                target = self.project_root / directory
                if target.exists() and target.is_dir():
                    yield from (p for p in target.rglob("*") if p.is_file())
            return
        yield from (p for p in self.project_root.rglob("*") if p.is_file())

    def _iter_candidate_directories(self, mode: str) -> Iterable[Path]:
        if mode == "fast":
            for directory in self.SAFE_CLEANUP_DIRS:
                target = self.project_root / directory
                if target.exists() and target.is_dir():
                    yield target
            return
        yield from (p for p in self.project_root.rglob("*") if p.is_dir())

    def _cleanup_files(self, result: dict, dry_run: bool, mode: str, timed_out) -> bool:
        for file_path in self._iter_candidate_files(mode):
            if timed_out():
                return True

            file_name = file_path.name
            if self._is_protected_file(file_name):
                result["files_protected"].append(str(file_path.relative_to(self.project_root)))
                continue

            if not self._should_cleanup_file(file_name):
                continue

            try:
                file_size = file_path.stat().st_size
                if not dry_run:
                    file_path.unlink()
                result["files_deleted"].append(str(file_path.relative_to(self.project_root)))
                result["total_size_freed"] += file_size
                logger.debug("Deleted file: %s", file_path)
            except Exception as exc:  # pragma: no cover - safety fallback
                error_msg = f"Failed to delete {file_path}: {exc}"
                result["errors"].append(error_msg)
                logger.exception(error_msg)
        return False

    def _cleanup_directories(self, result: dict, dry_run: bool, mode: str, timed_out) -> bool:
        for dir_path in self._iter_candidate_directories(mode):
            if timed_out():
                return True

            dir_name = dir_path.name
            if dir_name not in self.SAFE_CLEANUP_DIRS:
                continue

            has_protected = any((dir_path / name).exists() for name in _PROTECTED_FILENAMES)
            if has_protected:
                if self._cleanup_directory_contents(dir_path, dry_run, timed_out):
                    return True
                continue

            if self._is_safe_to_delete_dir(dir_path):
                try:
                    if not dry_run:
                        shutil.rmtree(dir_path)
                    result["dirs_deleted"].append(str(dir_path.relative_to(self.project_root)))
                    logger.debug("Deleted directory: %s", dir_path)
                except Exception as exc:  # pragma: no cover - safety fallback
                    error_msg = f"Failed to delete directory {dir_path}: {exc}"
                    result["errors"].append(error_msg)
                    logger.exception(error_msg)
        return False

    def _cleanup_directory_contents(self, dir_path: Path, dry_run: bool, timed_out) -> bool:
        for child in dir_path.iterdir():
            if timed_out():
                return True
            if child.name in _PROTECTED_FILENAMES:
                continue
            try:
                if child.is_dir():
                    if not dry_run:
                        shutil.rmtree(child)
                else:
                    if not dry_run:
                        child.unlink()
                logger.debug("Removed path inside directory %s: %s", dir_path, child)
            except Exception as exc:  # pragma: no cover - safety fallback
                error_msg = f"Failed to clean {child}: {exc}"
                logger.exception(error_msg)
        return False

    def _is_protected_file(self, file_name: str) -> bool:
        return any(pattern.match(file_name) for pattern in self.exclude_patterns)

    def _should_cleanup_file(self, file_name: str) -> bool:
        return any(pattern.match(file_name) for pattern in self.cleanup_patterns)

    def _is_safe_to_delete_dir(self, dir_path: Path) -> bool:
        try:
            entries = list(dir_path.iterdir())
        except PermissionError:
            return False
        if not entries:
            return True
        if dir_path.name.startswith(".") and "cache" in dir_path.name:
            # キャッシュディレクトリは中身を確認して安全なら削除
            return all(entry.name not in _PROTECTED_FILENAMES for entry in entries)
        return False

    def _log_cleanup_summary(self, result: dict, dry_run: bool) -> None:
        mode_text = "[DRY RUN] " if dry_run else ""
        logger.info("%sCleanup completed", mode_text)
        logger.info("  Files deleted: %s", len(result["files_deleted"]))
        logger.info("  Directories deleted: %s", len(result["dirs_deleted"]))
        logger.info("  Files protected: %s", len(result["files_protected"]))
        logger.info("  Errors: %s", len(result["errors"]))
        logger.info("  Total size freed: %s bytes", result["total_size_freed"])
        if result["aborted"]:
            logger.warning("Cleanup aborted prior to completion")


def cleanup_after_tests(project_root: Path | None = None, dry_run: bool = False) -> dict:
    if project_root is None:
        project_root = Path(__file__).resolve().parent.parent.parent
    manager = TestCleanupManager(project_root)
    return manager.cleanup_test_artifacts(dry_run=dry_run)


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    import argparse

    parser = argparse.ArgumentParser(description="Test cleanup manager")
    parser.add_argument("--dry-run", action="store_true", help="Show only what would be deleted")
    parser.add_argument("--project-root", type=Path, help="Project root directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    result = cleanup_after_tests(project_root=args.project_root, dry_run=args.dry_run)
    if result["errors"]:
        for err in result["errors"]:
            logger.error("%s", err)
