# File: tests/unit/infrastructure/repositories/test_file_template_repository.py
# Purpose: Comprehensive tests for FileTemplateRepository
# Context: Contract tests + unit tests + edge cases for template discovery and loading

import pytest
from pathlib import Path
from noveler.infrastructure.repositories.file_template_repository import FileTemplateRepository


# ============================================================================
# Contract Tests - ITemplateRepository Protocol Compliance
# ============================================================================


class TestFileTemplateRepositoryContract:
    """Contract tests for ITemplateRepository protocol compliance."""

    def test_find_template_returns_path_or_none(self, tmp_path: Path) -> None:
        """Contract: find_template() must return Path | None."""
        repo = FileTemplateRepository(tmp_path)
        result = repo.find_template(step_id=1, step_slug="test")
        assert isinstance(result, Path) or result is None, "find_template must return Path or None"

    def test_load_template_content_returns_string(self, tmp_path: Path) -> None:
        """Contract: load_template_content() must return str."""
        template_file = tmp_path / "test.yaml"
        template_file.write_text("content", encoding="utf-8")

        repo = FileTemplateRepository(tmp_path)
        result = repo.load_template_content(template_file)

        assert isinstance(result, str), "load_template_content must return str"

    def test_load_template_content_raises_on_missing_file(self, tmp_path: Path) -> None:
        """Contract: load_template_content() must raise FileNotFoundError if file missing."""
        repo = FileTemplateRepository(tmp_path)
        nonexistent = tmp_path / "missing.yaml"

        with pytest.raises(FileNotFoundError):
            repo.load_template_content(nonexistent)


# ============================================================================
# Unit Tests - FileTemplateRepository Implementation
# ============================================================================


class TestFileTemplateRepositoryUnit:
    """Unit tests for FileTemplateRepository implementation."""

    def test_init_stores_templates_dir(self, tmp_path: Path) -> None:
        """__init__ should store templates_dir for later use."""
        repo = FileTemplateRepository(tmp_path)
        assert repo._templates_dir == tmp_path

    def test_find_template_in_quality_checks(self, tmp_path: Path) -> None:
        """find_template() should find template in quality/checks/ directory."""
        # Arrange: create directory structure
        checks_dir = tmp_path / "quality" / "checks"
        checks_dir.mkdir(parents=True)
        template = checks_dir / "check_step01_typo_check.yaml"
        template.write_text("metadata:\n  title: Typo Check", encoding="utf-8")

        repo = FileTemplateRepository(tmp_path)

        # Act
        result = repo.find_template(step_id=1, step_slug="typo_check")

        # Assert
        assert result == template
        assert result.exists()

    def test_find_template_in_backup_directory(self, tmp_path: Path) -> None:
        """find_template() should fallback to quality/checks/backup/ directory."""
        # Arrange: skip quality/checks, create in backup
        backup_dir = tmp_path / "quality" / "checks" / "backup"
        backup_dir.mkdir(parents=True)
        template = backup_dir / "check_step02_consistency.yaml"
        template.write_text("metadata:\n  title: Consistency", encoding="utf-8")

        repo = FileTemplateRepository(tmp_path)

        # Act
        result = repo.find_template(step_id=2, step_slug="consistency")

        # Assert
        assert result == template

    def test_find_template_in_writing_directory(self, tmp_path: Path) -> None:
        """find_template() should fallback to writing/ directory."""
        # Arrange: skip quality/checks and backup, create in writing
        writing_dir = tmp_path / "writing"
        writing_dir.mkdir(parents=True)
        template = writing_dir / "check_step03_pacing.yaml"
        template.write_text("metadata:\n  title: Pacing", encoding="utf-8")

        repo = FileTemplateRepository(tmp_path)

        # Act
        result = repo.find_template(step_id=3, step_slug="pacing")

        # Assert
        assert result == template

    def test_find_template_returns_none_when_not_found(self, tmp_path: Path) -> None:
        """find_template() should return None if template doesn't exist in any directory."""
        repo = FileTemplateRepository(tmp_path)

        result = repo.find_template(step_id=99, step_slug="nonexistent")

        assert result is None

    def test_find_template_priority_order(self, tmp_path: Path) -> None:
        """find_template() should respect search priority: checks > backup > writing."""
        # Arrange: create same template in all three locations
        checks_dir = tmp_path / "quality" / "checks"
        backup_dir = tmp_path / "quality" / "checks" / "backup"
        writing_dir = tmp_path / "writing"

        checks_dir.mkdir(parents=True)
        backup_dir.mkdir(parents=True)
        writing_dir.mkdir(parents=True)

        template_name = "check_step05_test.yaml"
        checks_template = checks_dir / template_name
        backup_template = backup_dir / template_name
        writing_template = writing_dir / template_name

        checks_template.write_text("source: checks", encoding="utf-8")
        backup_template.write_text("source: backup", encoding="utf-8")
        writing_template.write_text("source: writing", encoding="utf-8")

        repo = FileTemplateRepository(tmp_path)

        # Act
        result = repo.find_template(step_id=5, step_slug="test")

        # Assert: should find checks first
        assert result == checks_template

    def test_find_template_formats_step_id_with_zero_padding(self, tmp_path: Path) -> None:
        """find_template() should format step_id as zero-padded 2-digit number."""
        checks_dir = tmp_path / "quality" / "checks"
        checks_dir.mkdir(parents=True)

        # Create template with properly formatted step_id
        template = checks_dir / "check_step01_test.yaml"
        template.write_text("test", encoding="utf-8")

        repo = FileTemplateRepository(tmp_path)

        # Act: pass step_id=1, expect filename "check_step01_test.yaml"
        result = repo.find_template(step_id=1, step_slug="test")

        assert result is not None
        assert result.name == "check_step01_test.yaml"

    def test_load_template_content_returns_full_content(self, tmp_path: Path) -> None:
        """load_template_content() should return complete file content."""
        template_file = tmp_path / "test.yaml"
        expected_content = """metadata:
  title: "Test Template"
  description: "Multi-line content test"
prompt: |
  This is a test prompt
  with multiple lines
  and special characters: 日本語
"""
        template_file.write_text(expected_content, encoding="utf-8")

        repo = FileTemplateRepository(tmp_path)
        result = repo.load_template_content(template_file)

        assert result == expected_content

    def test_load_template_content_preserves_utf8(self, tmp_path: Path) -> None:
        """load_template_content() should preserve UTF-8 characters (Japanese)."""
        template_file = tmp_path / "japanese.yaml"
        japanese_content = """metadata:
  title: "誤字チェック"
  description: "文章の誤字脱字を確認"
prompt: |
  以下の文章をチェックしてください：
  「こんにちは、世界！」
"""
        template_file.write_text(japanese_content, encoding="utf-8")

        repo = FileTemplateRepository(tmp_path)
        result = repo.load_template_content(template_file)

        assert "誤字チェック" in result
        assert "こんにちは、世界！" in result

    def test_load_template_content_raises_on_unicode_error(self, tmp_path: Path) -> None:
        """load_template_content() should raise UnicodeDecodeError on invalid UTF-8."""
        template_file = tmp_path / "bad_encoding.yaml"
        # Write invalid UTF-8 bytes
        template_file.write_bytes(b"\x80\x81\x82")

        repo = FileTemplateRepository(tmp_path)

        with pytest.raises(UnicodeDecodeError):
            repo.load_template_content(template_file)


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestFileTemplateRepositoryEdgeCases:
    """Edge case tests for FileTemplateRepository."""

    def test_empty_template_file(self, tmp_path: Path) -> None:
        """load_template_content() should handle empty files gracefully."""
        template_file = tmp_path / "empty.yaml"
        template_file.write_text("", encoding="utf-8")

        repo = FileTemplateRepository(tmp_path)
        result = repo.load_template_content(template_file)

        assert result == ""

    def test_very_large_step_id(self, tmp_path: Path) -> None:
        """find_template() should handle large step_id numbers correctly."""
        checks_dir = tmp_path / "quality" / "checks"
        checks_dir.mkdir(parents=True)

        # Create template with step_id=999 (format :02d allows 3+ digits)
        template = checks_dir / "check_step999_large.yaml"
        template.write_text("test", encoding="utf-8")

        repo = FileTemplateRepository(tmp_path)
        result = repo.find_template(step_id=999, step_slug="large")

        # Python f"{999:02d}" → "999" (minimum 2 digits, but allows more)
        assert result == template

    def test_step_slug_with_underscores(self, tmp_path: Path) -> None:
        """find_template() should handle step_slug with multiple underscores."""
        checks_dir = tmp_path / "quality" / "checks"
        checks_dir.mkdir(parents=True)

        template = checks_dir / "check_step10_complex_check_name.yaml"
        template.write_text("test", encoding="utf-8")

        repo = FileTemplateRepository(tmp_path)
        result = repo.find_template(step_id=10, step_slug="complex_check_name")

        assert result == template

    def test_nonexistent_templates_dir(self, tmp_path: Path) -> None:
        """find_template() should handle nonexistent templates_dir gracefully."""
        nonexistent_dir = tmp_path / "does_not_exist"

        repo = FileTemplateRepository(nonexistent_dir)
        result = repo.find_template(step_id=1, step_slug="test")

        assert result is None  # Should not crash, just return None
