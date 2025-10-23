# File: tests/unit/scripts/test_migrate_legacy_filenames.py
# Purpose: Unit tests for legacy filename migration script
# Context: Validates conversion logic and migration behavior

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from scripts.migration.migrate_legacy_filenames import (
    LegacyFilenameMigrator,
    MigrationResult,
)


class TestLegacyFilenameMigrator:
    """LegacyFilenameMigrator のテスト"""

    @pytest.fixture
    def migrator(self) -> LegacyFilenameMigrator:
        """テスト用のマイグレーターインスタンス"""
        return LegacyFilenameMigrator(dry_run=False, create_backup=False)

    @pytest.fixture
    def dry_run_migrator(self) -> LegacyFilenameMigrator:
        """Dry-run モードのマイグレーター"""
        return LegacyFilenameMigrator(dry_run=True, create_backup=False)

    def test_is_legacy_format_type1(self, migrator: LegacyFilenameMigrator) -> None:
        """Format 1 のレガシー形式を検出"""
        assert migrator._is_legacy_format("A41_ep001.md") is True
        assert migrator._is_legacy_format("quality_ep042.json") is True
        assert migrator._is_legacy_format("backup_ep999.yaml") is True

    def test_is_legacy_format_type2(self, migrator: LegacyFilenameMigrator) -> None:
        """Format 2 のレガシー形式を検出"""
        assert (
            migrator._is_legacy_format("quality_ep042_20251013_124325.json") is True
        )
        assert migrator._is_legacy_format("A41_ep001_20250115_103045.md") is True

    def test_is_not_legacy_format(self, migrator: LegacyFilenameMigrator) -> None:
        """統一形式はレガシーとして検出されない"""
        assert migrator._is_legacy_format("episode_001_A41.md") is False
        assert migrator._is_legacy_format("episode_042_quality.json") is False
        assert (
            migrator._is_legacy_format("episode_001_quality_20251013_124325.json")
            is False
        )

    def test_convert_format1_to_unified(
        self, migrator: LegacyFilenameMigrator
    ) -> None:
        """Format 1 から統一形式への変換"""
        result = migrator._convert_to_unified_format("A41_ep001.md")
        assert result == "episode_001_A41.md"

        result = migrator._convert_to_unified_format("quality_ep042.json")
        assert result == "episode_042_quality.json"

        result = migrator._convert_to_unified_format("backup_ep999.yaml")
        assert result == "episode_999_backup.yaml"

    def test_convert_format2_to_unified(
        self, migrator: LegacyFilenameMigrator
    ) -> None:
        """Format 2 から統一形式への変換"""
        result = migrator._convert_to_unified_format(
            "quality_ep042_20251013_124325.json"
        )
        assert result == "episode_042_quality_20251013_124325.json"

        result = migrator._convert_to_unified_format("A41_ep001_20250115_103045.md")
        assert result == "episode_001_A41_20250115_103045.md"

    def test_convert_unified_format_returns_none(
        self, migrator: LegacyFilenameMigrator
    ) -> None:
        """統一形式のファイル名は変換対象外"""
        result = migrator._convert_to_unified_format("episode_001_A41.md")
        assert result is None

        result = migrator._convert_to_unified_format(
            "episode_042_quality_20251013_124325.json"
        )
        assert result is None

    def test_migrate_file_dry_run(
        self, tmp_path: Path, dry_run_migrator: LegacyFilenameMigrator
    ) -> None:
        """Dry-run モードではファイルが変更されない"""
        # レガシーファイルを作成
        legacy_file = tmp_path / "A41_ep001.md"
        legacy_file.write_text("Test content")

        # 移行実行（dry-run）
        result = dry_run_migrator.migrate_file(legacy_file)

        # 結果確認
        assert result.success is True
        assert result.old_path == legacy_file
        assert result.new_path == tmp_path / "episode_001_A41.md"
        assert result.error is None

        # ファイルは変更されていない
        assert legacy_file.exists()
        assert not (tmp_path / "episode_001_A41.md").exists()

    def test_migrate_file_actual(
        self, tmp_path: Path, migrator: LegacyFilenameMigrator
    ) -> None:
        """実際のファイル移行が成功する"""
        # レガシーファイルを作成
        legacy_file = tmp_path / "quality_ep042.json"
        legacy_file.write_text('{"test": "data"}')

        # 移行実行
        result = migrator.migrate_file(legacy_file)

        # 結果確認
        assert result.success is True
        assert result.old_path == legacy_file
        assert result.new_path == tmp_path / "episode_042_quality.json"
        assert result.error is None

        # ファイルが移行されている
        assert not legacy_file.exists()
        assert (tmp_path / "episode_042_quality.json").exists()
        assert (tmp_path / "episode_042_quality.json").read_text() == '{"test": "data"}'

    def test_migrate_file_target_exists(
        self, tmp_path: Path, migrator: LegacyFilenameMigrator
    ) -> None:
        """移行先ファイルが既に存在する場合はエラー"""
        # レガシーファイルと移行先ファイルを作成
        legacy_file = tmp_path / "A41_ep001.md"
        legacy_file.write_text("Old content")

        target_file = tmp_path / "episode_001_A41.md"
        target_file.write_text("New content")

        # 移行実行
        result = migrator.migrate_file(legacy_file)

        # 結果確認
        assert result.success is False
        assert "already exists" in result.error

        # ファイルは変更されていない
        assert legacy_file.exists()
        assert target_file.read_text() == "New content"

    def test_migrate_file_with_backup(self, tmp_path: Path) -> None:
        """バックアップオプションが機能する"""
        migrator = LegacyFilenameMigrator(dry_run=False, create_backup=True)

        # レガシーファイルを作成
        legacy_file = tmp_path / "backup_ep010.yaml"
        legacy_file.write_text("Original data")

        # 移行実行
        result = migrator.migrate_file(legacy_file)

        # 結果確認
        assert result.success is True

        # バックアップが作成されている
        backup_file = tmp_path / "backup_ep010.yaml.backup"
        assert backup_file.exists()
        assert backup_file.read_text() == "Original data"

        # 移行先ファイルが作成されている
        assert (tmp_path / "episode_010_backup.yaml").exists()

    def test_migrate_directory(
        self, tmp_path: Path, migrator: LegacyFilenameMigrator
    ) -> None:
        """ディレクトリ内の複数ファイルを移行"""
        # レガシーファイルを複数作成
        (tmp_path / "A41_ep001.md").write_text("Content 1")
        (tmp_path / "quality_ep002.json").write_text("Content 2")
        (tmp_path / "backup_ep003_20251013_124325.yaml").write_text("Content 3")
        # 統一形式のファイルも作成（移行対象外）
        (tmp_path / "episode_010_A41.md").write_text("Already unified")

        # 移行実行
        results = migrator.migrate_directory(tmp_path)

        # 結果確認
        assert len(results) == 3  # レガシーファイルのみ
        assert all(r.success for r in results)

        # 移行後のファイルを確認
        assert (tmp_path / "episode_001_A41.md").exists()
        assert (tmp_path / "episode_002_quality.json").exists()
        assert (tmp_path / "episode_003_backup_20251013_124325.yaml").exists()
        assert (tmp_path / "episode_010_A41.md").exists()  # 統一形式は変更なし

    def test_migrate_directory_not_found(
        self, migrator: LegacyFilenameMigrator
    ) -> None:
        """存在しないディレクトリでエラー"""
        with pytest.raises(FileNotFoundError):
            migrator.migrate_directory(Path("/nonexistent/directory"))

    def test_migrate_directory_not_a_directory(
        self, tmp_path: Path, migrator: LegacyFilenameMigrator
    ) -> None:
        """ファイルパスを指定した場合エラー"""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Not a directory")

        with pytest.raises(NotADirectoryError):
            migrator.migrate_directory(file_path)
