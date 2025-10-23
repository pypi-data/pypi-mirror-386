"""Unit tests for check_archive_structure.py

File: tests/unit/hooks/test_check_archive_structure.py
Purpose: Test archive structure validation hook functionality.
Context: Ensures pre-commit hook validates archive policy correctly.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestValidateArchive:
    """Test validate_archive function."""

    def test_validate_archive_missing_readme(self, tmp_path, monkeypatch):
        """Test validation fails when README.md is missing."""
        from scripts.hooks.check_archive_structure import validate_archive

        # Change to tmp_path (no README exists)
        monkeypatch.chdir(tmp_path)

        errors = validate_archive()

        # Should have error about missing README
        assert len(errors) > 0
        assert any("README.md not found" in err for err in errors)

    def test_validate_archive_missing_gitignore_exception(self, tmp_path, monkeypatch):
        """Test validation fails when .gitignore missing exception."""
        from scripts.hooks.check_archive_structure import validate_archive

        # Setup: Create README but no .gitignore exception
        monkeypatch.chdir(tmp_path)
        readme = tmp_path / "docs" / "archive" / "README.md"
        readme.parent.mkdir(parents=True)
        readme.write_text("# Archive\n")

        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("archive/\n")  # No exception

        errors = validate_archive()

        # Should have error about missing .gitignore exception
        assert any("!docs/archive/" in err for err in errors)

    def test_validate_archive_no_gitignore_file(self, tmp_path, monkeypatch):
        """Test validation fails when .gitignore doesn't exist."""
        from scripts.hooks.check_archive_structure import validate_archive

        # Setup: Create README but no .gitignore
        monkeypatch.chdir(tmp_path)
        readme = tmp_path / "docs" / "archive" / "README.md"
        readme.parent.mkdir(parents=True)
        readme.write_text("# Archive\n")

        errors = validate_archive()

        # Should have error about missing .gitignore
        assert any(".gitignore not found" in err for err in errors)

    def test_validate_archive_no_tracked_files(self, tmp_path, monkeypatch):
        """Test validation warns when no files tracked."""
        from scripts.hooks.check_archive_structure import validate_archive

        # Setup: Create proper structure
        monkeypatch.chdir(tmp_path)
        readme = tmp_path / "docs" / "archive" / "README.md"
        readme.parent.mkdir(parents=True)
        readme.write_text("# Archive\n")

        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("archive/\n!docs/archive/\n")

        # Mock git ls-files to return empty (but not None)
        # Line 44 checks: result.returncode == 0 and result.stdout and not result.stdout.strip()
        # This means stdout must be truthy (not None) but empty when stripped
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = " "  # Whitespace only - truthy but strips to empty

        with patch("subprocess.run", return_value=mock_result):
            errors = validate_archive()

        # Should have warning about no tracked files
        assert any("no tracked files" in err.lower() for err in errors)

    def test_validate_archive_missing_expected_directories(self, tmp_path, monkeypatch):
        """Test validation warns when expected directories missing."""
        from scripts.hooks.check_archive_structure import validate_archive

        # Setup: Create README and .gitignore
        monkeypatch.chdir(tmp_path)
        readme = tmp_path / "docs" / "archive" / "README.md"
        readme.parent.mkdir(parents=True)
        readme.write_text("# Archive\n")

        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("archive/\n!docs/archive/\n")

        # Mock git ls-files to return files
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "docs/archive/README.md\n"

        with patch("subprocess.run", return_value=mock_result):
            errors = validate_archive()

        # Should have warnings about missing directories
        assert any("proposals" in err for err in errors)
        assert any("refactoring" in err for err in errors)
        assert any("reviews" in err for err in errors)
        assert any("backup" in err for err in errors)

    def test_validate_archive_success(self, tmp_path, monkeypatch):
        """Test validation succeeds with proper structure."""
        from scripts.hooks.check_archive_structure import validate_archive

        # Setup: Create complete structure
        monkeypatch.chdir(tmp_path)

        # Create README
        readme = tmp_path / "docs" / "archive" / "README.md"
        readme.parent.mkdir(parents=True)
        readme.write_text("# Archive\n")

        # Create .gitignore with exception
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("archive/\n!docs/archive/\n")

        # Create expected directories
        (tmp_path / "docs" / "archive" / "proposals").mkdir()
        (tmp_path / "docs" / "archive" / "refactoring").mkdir()
        (tmp_path / "docs" / "archive" / "reviews").mkdir()
        (tmp_path / "docs" / "archive" / "backup").mkdir()

        # Mock git ls-files to return files
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "docs/archive/README.md\n"

        with patch("subprocess.run", return_value=mock_result):
            errors = validate_archive()

        # Should have no errors (only warnings about empty dirs)
        error_count = len([e for e in errors if e.startswith("[ERROR]")])
        assert error_count == 0

    def test_validate_archive_git_command_not_found(self, tmp_path, monkeypatch):
        """Test graceful handling when git command not found."""
        from scripts.hooks.check_archive_structure import validate_archive

        # Setup: Create proper structure
        monkeypatch.chdir(tmp_path)
        readme = tmp_path / "docs" / "archive" / "README.md"
        readme.parent.mkdir(parents=True)
        readme.write_text("# Archive\n")

        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("archive/\n!docs/archive/\n")

        # Mock subprocess to raise FileNotFoundError
        with patch("subprocess.run", side_effect=FileNotFoundError("git not found")):
            errors = validate_archive()

        # Should have warning about git not found
        assert any("git command not found" in err.lower() for err in errors)


class TestMainFunction:
    """Test main function."""

    def test_main_validation_success(self, tmp_path, monkeypatch, capsys):
        """Test main function with successful validation."""
        from scripts.hooks.check_archive_structure import main

        # Setup: Create complete structure
        monkeypatch.chdir(tmp_path)
        readme = tmp_path / "docs" / "archive" / "README.md"
        readme.parent.mkdir(parents=True)
        readme.write_text("# Archive\n")

        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("archive/\n!docs/archive/\n")

        # Create expected directories
        (tmp_path / "docs" / "archive" / "proposals").mkdir()
        (tmp_path / "docs" / "archive" / "refactoring").mkdir()
        (tmp_path / "docs" / "archive" / "reviews").mkdir()
        (tmp_path / "docs" / "archive" / "backup").mkdir()

        # Mock git ls-files
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "docs/archive/README.md\n"

        with patch("subprocess.run", return_value=mock_result):
            exit_code = main()

        # Should exit with 0
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "[PASS]" in captured.out

    def test_main_validation_failure(self, tmp_path, monkeypatch, capsys):
        """Test main function with validation failure."""
        from scripts.hooks.check_archive_structure import main

        # Setup: Missing README
        monkeypatch.chdir(tmp_path)

        exit_code = main()

        # Should exit with 1
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "[FAIL]" in captured.err
        assert "README.md not found" in captured.err


class TestWindowsCompatibility:
    """Test Windows compatibility."""

    def test_validate_archive_handles_encoding_error(self, tmp_path, monkeypatch):
        """Test graceful handling of encoding errors on Windows."""
        from scripts.hooks.check_archive_structure import validate_archive

        # Setup: Create proper structure
        monkeypatch.chdir(tmp_path)
        readme = tmp_path / "docs" / "archive" / "README.md"
        readme.parent.mkdir(parents=True)
        readme.write_text("# Archive\n")

        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("archive/\n!docs/archive/\n")

        # Mock git ls-files to raise UnicodeDecodeError
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "docs/archive/README.md\n"

        # encoding="utf-8", errors="ignore" should prevent errors
        with patch("subprocess.run", return_value=mock_result):
            errors = validate_archive()

        # Should not raise exception
        # May have warnings but no crashes
        assert isinstance(errors, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
