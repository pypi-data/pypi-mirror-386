#!/usr/bin/env python3
# File: scripts/migration/migrate_legacy_filenames.py
# Purpose: Migrate legacy filename format to unified format
# Context: Automates migration from A41_ep001.md to episode_001_A41.md

"""レガシーファイル名形式から統一形式への移行スクリプト

Usage:
    python scripts/migration/migrate_legacy_filenames.py [--dry-run] [--path PATH]

Legacy Format Examples:
    A41_ep001.md → episode_001_A41.md
    quality_ep042_20251013_124325.json → episode_042_quality_20251013_124325.json

Options:
    --dry-run: Preview changes without applying them
    --path PATH: Target directory (default: current directory)
    --backup: Create backup of original files before migration
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import NamedTuple


class LegacyFilenamePattern(NamedTuple):
    """レガシーファイル名パターンの定義"""

    pattern: re.Pattern
    description: str

    def matches(self, filename: str) -> re.Match | None:
        """ファイル名がこのパターンにマッチするかチェック"""
        return self.pattern.match(filename)


class MigrationResult(NamedTuple):
    """移行結果"""

    success: bool
    old_path: Path
    new_path: Path | None
    error: str | None


class LegacyFilenameMigrator:
    """レガシーファイル名の移行を管理するクラス

    Purpose:
        レガシー形式のファイル名を統一形式に変換し、ファイル名を更新する。

    Supported Legacy Formats:
        1. A41_ep001.md → episode_001_A41.md
        2. quality_ep042.json → episode_042_quality.json
        3. quality_ep042_20251013_124325.json → episode_042_quality_20251013_124325.json
    """

    # レガシーパターン定義
    LEGACY_PATTERNS = [
        LegacyFilenamePattern(
            pattern=re.compile(r"^([A-Za-z0-9]+)_ep(\d+)\.(\w+)$"),
            description="Format 1: {report_type}_ep{episode}.{ext}",
        ),
        LegacyFilenamePattern(
            pattern=re.compile(
                r"^([A-Za-z0-9]+)_ep(\d+)_(\d{8}_\d{6})\.(\w+)$"
            ),
            description="Format 2: {report_type}_ep{episode}_{timestamp}.{ext}",
        ),
    ]

    def __init__(self, dry_run: bool = False, create_backup: bool = False) -> None:
        """初期化

        Args:
            dry_run: True の場合、変更をプレビューのみ
            create_backup: True の場合、移行前にバックアップを作成
        """
        self.dry_run = dry_run
        self.create_backup = create_backup
        self.results: list[MigrationResult] = []

    def migrate_directory(self, target_dir: Path) -> list[MigrationResult]:
        """ディレクトリ内の全レガシーファイル名を移行

        Args:
            target_dir: 対象ディレクトリ

        Returns:
            移行結果のリスト
        """
        if not target_dir.exists():
            raise FileNotFoundError(f"Directory not found: {target_dir}")

        if not target_dir.is_dir():
            raise NotADirectoryError(f"Not a directory: {target_dir}")

        # レガシーファイルを検出
        legacy_files = self._find_legacy_files(target_dir)

        print(f"Found {len(legacy_files)} legacy files in {target_dir}")

        # 各ファイルを移行
        for legacy_file in legacy_files:
            result = self.migrate_file(legacy_file)
            self.results.append(result)

        return self.results

    def migrate_file(self, file_path: Path) -> MigrationResult:
        """単一ファイルの移行

        Args:
            file_path: 移行対象のファイルパス

        Returns:
            移行結果
        """
        try:
            # 統一形式のファイル名を生成
            new_filename = self._convert_to_unified_format(file_path.name)

            if new_filename is None:
                return MigrationResult(
                    success=False,
                    old_path=file_path,
                    new_path=None,
                    error="Not a legacy format filename",
                )

            new_path = file_path.parent / new_filename

            # 既に存在する場合はスキップ
            if new_path.exists():
                return MigrationResult(
                    success=False,
                    old_path=file_path,
                    new_path=new_path,
                    error=f"Target file already exists: {new_path}",
                )

            # Dry-run モード
            if self.dry_run:
                print(f"[DRY-RUN] Would rename: {file_path} → {new_path}")
                return MigrationResult(
                    success=True, old_path=file_path, new_path=new_path, error=None
                )

            # バックアップ作成
            if self.create_backup:
                backup_path = file_path.with_suffix(
                    file_path.suffix + ".backup"
                )
                shutil.copy2(file_path, backup_path)
                print(f"Created backup: {backup_path}")

            # ファイル名変更
            file_path.rename(new_path)
            print(f"Migrated: {file_path} → {new_path}")

            return MigrationResult(
                success=True, old_path=file_path, new_path=new_path, error=None
            )

        except Exception as e:
            return MigrationResult(
                success=False, old_path=file_path, new_path=None, error=str(e)
            )

    def _find_legacy_files(self, directory: Path) -> list[Path]:
        """ディレクトリ内のレガシーファイルを検出

        Args:
            directory: 検索対象ディレクトリ

        Returns:
            レガシーファイルのリスト
        """
        legacy_files = []

        for file_path in directory.rglob("*"):
            if not file_path.is_file():
                continue

            # レガシーパターンにマッチするかチェック
            if self._is_legacy_format(file_path.name):
                legacy_files.append(file_path)

        return legacy_files

    def _is_legacy_format(self, filename: str) -> bool:
        """ファイル名がレガシー形式かチェック

        Args:
            filename: チェック対象のファイル名

        Returns:
            レガシー形式の場合 True
        """
        for pattern_def in self.LEGACY_PATTERNS:
            if pattern_def.matches(filename):
                return True
        return False

    def _convert_to_unified_format(self, legacy_filename: str) -> str | None:
        """レガシーファイル名を統一形式に変換

        Args:
            legacy_filename: レガシー形式のファイル名

        Returns:
            統一形式のファイル名、または変換不可の場合 None

        Examples:
            A41_ep001.md → episode_001_A41.md
            quality_ep042_20251013_124325.json → episode_042_quality_20251013_124325.json
        """
        # Format 1: {report_type}_ep{episode}.{ext}
        match = self.LEGACY_PATTERNS[0].matches(legacy_filename)
        if match:
            report_type = match.group(1)
            episode = int(match.group(2))
            extension = match.group(3)
            return f"episode_{episode:03d}_{report_type}.{extension}"

        # Format 2: {report_type}_ep{episode}_{timestamp}.{ext}
        match = self.LEGACY_PATTERNS[1].matches(legacy_filename)
        if match:
            report_type = match.group(1)
            episode = int(match.group(2))
            timestamp = match.group(3)
            extension = match.group(4)
            return f"episode_{episode:03d}_{report_type}_{timestamp}.{extension}"

        return None

    def print_summary(self) -> None:
        """移行結果のサマリーを出力"""
        total = len(self.results)
        success = sum(1 for r in self.results if r.success)
        failed = total - success

        print("\n" + "=" * 80)
        print("Migration Summary")
        print("=" * 80)
        print(f"Total files processed: {total}")
        print(f"Successfully migrated: {success}")
        print(f"Failed: {failed}")

        if failed > 0:
            print("\nFailed migrations:")
            for result in self.results:
                if not result.success:
                    print(f"  - {result.old_path}: {result.error}")

        if self.dry_run:
            print("\n[DRY-RUN MODE] No files were actually modified.")
        print("=" * 80)


def main() -> int:
    """メインエントリーポイント

    Returns:
        終了コード（0: 成功、1: 失敗）
    """
    parser = argparse.ArgumentParser(
        description="Migrate legacy filename format to unified format"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them",
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=Path.cwd(),
        help="Target directory (default: current directory)",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create backup of original files before migration",
    )

    args = parser.parse_args()

    try:
        migrator = LegacyFilenameMigrator(
            dry_run=args.dry_run, create_backup=args.backup
        )

        print(f"Starting migration in: {args.path}")
        print(f"Dry-run mode: {args.dry_run}")
        print(f"Backup enabled: {args.backup}")
        print()

        results = migrator.migrate_directory(args.path)
        migrator.print_summary()

        # 失敗がある場合は終了コード 1
        failed = sum(1 for r in results if not r.success)
        return 1 if failed > 0 else 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
