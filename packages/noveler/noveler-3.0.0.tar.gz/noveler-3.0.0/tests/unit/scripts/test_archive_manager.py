"""Unit tests for archive_manager.py

File: tests/unit/scripts/test_archive_manager.py
Purpose: Test archive candidate detection and management functionality.
Context: Ensures CI/CD archive suggestions work correctly.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestGetFileAge:
    """Test get_file_age function."""

    def test_get_file_age_with_git_history(self, tmp_path):
        """Test file age calculation using git history."""
        from scripts.archive_manager import get_file_age

        # Create a test file
        test_file = tmp_path / "test.md"
        test_file.write_text("test content")

        # Mock git log to return a timestamp from 100 days ago
        timestamp = int((datetime.now() - timedelta(days=100)).timestamp())
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = str(timestamp)

        with patch("subprocess.run", return_value=mock_result):
            age = get_file_age(test_file)

        # Should return approximately 100 days
        assert 99 <= age <= 101

    def test_get_file_age_fallback_to_filesystem(self, tmp_path):
        """Test file age fallback to filesystem mtime when git fails."""
        from scripts.archive_manager import get_file_age

        # Create a test file
        test_file = tmp_path / "test.md"
        test_file.write_text("test content")

        # Set mtime to 50 days ago
        past_time = (datetime.now() - timedelta(days=50)).timestamp()
        test_file.touch()
        import os

        os.utime(test_file, (past_time, past_time))

        # Mock git to fail
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""

        with patch("subprocess.run", return_value=mock_result):
            age = get_file_age(test_file)

        # Should fallback to filesystem mtime (~50 days)
        assert 49 <= age <= 51


class TestIsCompletedFile:
    """Test is_completed_file function."""

    def test_is_completed_file_with_japanese_marker(self, tmp_path):
        """Test completion detection with Japanese marker."""
        from scripts.archive_manager import is_completed_file

        test_file = tmp_path / "proposal.md"
        test_file.write_text("## Proposal\n\n完了\n", encoding="utf-8")

        assert is_completed_file(test_file) is True

    def test_is_completed_file_with_english_marker(self, tmp_path):
        """Test completion detection with English marker."""
        from scripts.archive_manager import is_completed_file

        test_file = tmp_path / "proposal.md"
        test_file.write_text("## Proposal\n\nCompleted\n", encoding="utf-8")

        assert is_completed_file(test_file) is True

    def test_is_completed_file_with_emoji_marker(self, tmp_path):
        """Test completion detection with emoji marker."""
        from scripts.archive_manager import is_completed_file

        test_file = tmp_path / "proposal.md"
        test_file.write_text("## Proposal\n\n✅ Done\n", encoding="utf-8")

        assert is_completed_file(test_file) is True

    def test_is_completed_file_with_bracket_marker(self, tmp_path):
        """Test completion detection with bracket marker."""
        from scripts.archive_manager import is_completed_file

        test_file = tmp_path / "proposal.md"
        test_file.write_text("## Proposal\n\n[COMPLETE]\n", encoding="utf-8")

        assert is_completed_file(test_file) is True

    def test_is_completed_file_without_marker(self, tmp_path):
        """Test completion detection returns False when no marker present."""
        from scripts.archive_manager import is_completed_file

        test_file = tmp_path / "proposal.md"
        test_file.write_text("## Proposal\n\nIn progress\n", encoding="utf-8")

        assert is_completed_file(test_file) is False

    def test_is_completed_file_case_insensitive(self, tmp_path):
        """Test completion detection is case insensitive."""
        from scripts.archive_manager import is_completed_file

        test_file = tmp_path / "proposal.md"
        test_file.write_text("## Proposal\n\nCOMPLETED\n", encoding="utf-8")

        assert is_completed_file(test_file) is True

    def test_is_completed_file_handles_unicode_error(self, tmp_path):
        """Test graceful handling of UnicodeDecodeError."""
        from scripts.archive_manager import is_completed_file

        # Create a binary file that will cause UnicodeDecodeError
        test_file = tmp_path / "binary.dat"
        test_file.write_bytes(b"\xff\xfe\x00\x00")

        # Should return False without raising exception
        assert is_completed_file(test_file) is False


class TestSuggestCandidates:
    """Test suggest_candidates function."""

    def test_suggest_candidates_completed_proposal(self, tmp_path):
        """Test detection of completed old proposal."""
        from scripts.archive_manager import suggest_candidates

        # Setup: Create completed proposal
        proposals_dir = tmp_path / "proposals"
        proposals_dir.mkdir()
        proposal = proposals_dir / "old_proposal.md"
        proposal.write_text("## Proposal\n\n完了\n", encoding="utf-8")

        # Mock get_file_age to return 100 days
        with patch("scripts.archive_manager.get_file_age", return_value=100):
            candidates = suggest_candidates(tmp_path, age_threshold_days=90)

        # Should detect 1 candidate
        assert len(candidates) == 1
        assert candidates[0][0] == proposal
        assert "Completed proposal" in candidates[0][1]
        assert "100 days old" in candidates[0][1]

    def test_suggest_candidates_stale_proposal(self, tmp_path):
        """Test detection of stale proposal without completion marker."""
        from scripts.archive_manager import suggest_candidates

        # Setup: Create stale proposal
        proposals_dir = tmp_path / "proposals"
        proposals_dir.mkdir()
        proposal = proposals_dir / "stale_proposal.md"
        proposal.write_text("## Proposal\n\nDraft\n", encoding="utf-8")

        # Mock get_file_age to return 120 days
        with patch("scripts.archive_manager.get_file_age", return_value=120):
            candidates = suggest_candidates(tmp_path, age_threshold_days=90)

        # Should detect 1 candidate
        assert len(candidates) == 1
        assert "Stale proposal" in candidates[0][1]
        assert "120 days old" in candidates[0][1]

    def test_suggest_candidates_completed_refactoring(self, tmp_path):
        """Test detection of completed refactoring plan."""
        from scripts.archive_manager import suggest_candidates

        # Setup: Create completed refactoring plan
        refactoring_dir = tmp_path / "refactoring"
        refactoring_dir.mkdir()
        plan = refactoring_dir / "refactor_plan.md"
        plan.write_text("## Plan\n\n実装完了\n", encoding="utf-8")

        # Mock get_file_age to return 95 days
        with patch("scripts.archive_manager.get_file_age", return_value=95):
            candidates = suggest_candidates(tmp_path, age_threshold_days=90)

        # Should detect 1 candidate
        assert len(candidates) == 1
        assert "Completed refactoring plan" in candidates[0][1]

    def test_suggest_candidates_recent_proposal_excluded(self, tmp_path):
        """Test recent proposals are not suggested."""
        from scripts.archive_manager import suggest_candidates

        # Setup: Create recent proposal
        proposals_dir = tmp_path / "proposals"
        proposals_dir.mkdir()
        proposal = proposals_dir / "recent_proposal.md"
        proposal.write_text("## Proposal\n\n完了\n", encoding="utf-8")

        # Mock get_file_age to return 30 days
        with patch("scripts.archive_manager.get_file_age", return_value=30):
            candidates = suggest_candidates(tmp_path, age_threshold_days=90)

        # Should not detect any candidates
        assert len(candidates) == 0

    def test_suggest_candidates_check_proposals_false(self, tmp_path):
        """Test proposals are skipped when check_proposals=False."""
        from scripts.archive_manager import suggest_candidates

        # Setup: Create completed proposal
        proposals_dir = tmp_path / "proposals"
        proposals_dir.mkdir()
        proposal = proposals_dir / "old_proposal.md"
        proposal.write_text("## Proposal\n\n完了\n", encoding="utf-8")

        # Mock get_file_age to return 100 days
        with patch("scripts.archive_manager.get_file_age", return_value=100):
            candidates = suggest_candidates(tmp_path, age_threshold_days=90, check_proposals=False)

        # Should not detect any candidates
        assert len(candidates) == 0

    def test_suggest_candidates_nonexistent_directory(self, tmp_path):
        """Test graceful handling of nonexistent directories."""
        from scripts.archive_manager import suggest_candidates

        # No proposals/ directory exists
        candidates = suggest_candidates(tmp_path, age_threshold_days=90)

        # Should return empty list without error
        assert len(candidates) == 0

    def test_suggest_candidates_multiple_files(self, tmp_path):
        """Test detection of multiple candidates."""
        from scripts.archive_manager import suggest_candidates

        # Setup: Create multiple old files
        proposals_dir = tmp_path / "proposals"
        proposals_dir.mkdir()
        refactoring_dir = tmp_path / "refactoring"
        refactoring_dir.mkdir()

        proposal1 = proposals_dir / "proposal1.md"
        proposal1.write_text("## Proposal 1\n\n完了\n", encoding="utf-8")

        proposal2 = proposals_dir / "proposal2.md"
        proposal2.write_text("## Proposal 2\n\nDraft\n", encoding="utf-8")

        refactor = refactoring_dir / "refactor.md"
        refactor.write_text("## Refactor\n\nCompleted\n", encoding="utf-8")

        # Mock get_file_age to return 100 days for all
        with patch("scripts.archive_manager.get_file_age", return_value=100):
            candidates = suggest_candidates(tmp_path, age_threshold_days=90)

        # Should detect 3 candidates
        assert len(candidates) == 3


class TestMainFunction:
    """Test main function (CLI interface)."""

    def test_main_suggest_candidates_command(self, tmp_path, monkeypatch, capsys):
        """Test main function with suggest-candidates command."""
        from scripts.archive_manager import main

        # Setup: Create docs/proposals directory structure
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        proposals_dir = docs_dir / "proposals"
        proposals_dir.mkdir()
        proposal = proposals_dir / "old.md"
        proposal.write_text("## Proposal\n\n完了\n", encoding="utf-8")

        # Change to tmp_path and mock sys.argv
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("sys.argv", ["archive_manager.py", "suggest-candidates"])

        # Mock get_file_age
        with patch("scripts.archive_manager.get_file_age", return_value=100):
            exit_code = main()

        # Should exit with 0 and print candidates
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "old.md" in captured.out
        assert "Completed proposal" in captured.out

    def test_main_no_candidates_found(self, tmp_path, monkeypatch, capsys):
        """Test main function when no candidates found."""
        from scripts.archive_manager import main

        # Change to tmp_path with no old files
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("sys.argv", ["archive_manager.py", "suggest-candidates"])

        exit_code = main()

        # Should exit with 0 and print message
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "No archive candidates found" in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
