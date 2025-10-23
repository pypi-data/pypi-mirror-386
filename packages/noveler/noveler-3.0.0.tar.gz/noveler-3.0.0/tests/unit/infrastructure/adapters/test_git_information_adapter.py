#!/usr/bin/env python3
"""Git情報取得アダプターの単体テスト

仕様書: SPEC-CODEMAP-AUTO-UPDATE-001
"""

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from noveler.infrastructure.adapters.git_information_adapter import GitInformationAdapter


class TestGitInformationAdapter:
    """Git情報取得アダプターのテストクラス"""

    @pytest.fixture
    def repo_path(self):
        """リポジトリパス"""
        return Path("/test/repo")

    @pytest.fixture
    def adapter(self, repo_path):
        """テスト対象のアダプター"""
        return GitInformationAdapter(repo_path)

    @pytest.fixture
    def sample_git_log_output(self):
        """サンプルGit logコマンド出力"""
        return (
            "abcd1234567890abcdef1234567890abcdef1234|2025-01-15 10:30:00 +0900|John Doe|john@example.com|feat: implement new feature\n"
            "noveler/domain/entities/test_entity.py\n"
            "noveler/application/use_cases/test_use_case.py\n"
            "README.md"
        )

    def test_init(self, repo_path):
        """初期化テスト"""
        # Act
        adapter = GitInformationAdapter(repo_path)

        # Assert
        assert adapter.repository_path == repo_path

    def test_get_latest_commit_info_success(self, adapter, sample_git_log_output):
        """最新コミット情報取得成功テスト"""
        # Arrange
        with patch.object(adapter, "_run_git_command", return_value=sample_git_log_output):
            with patch.object(adapter, "_get_current_branch", return_value="master"):
                # Act
                commit_info = adapter.get_latest_commit_info()

                # Assert
                assert commit_info is not None
                assert commit_info.full_hash == "abcd1234567890abcdef1234567890abcdef1234"
                assert commit_info.short_hash == "abcd1234"
                assert commit_info.author_name == "John Doe"
                assert commit_info.author_email == "john@example.com"
                assert commit_info.commit_message == "feat: implement new feature"
                assert commit_info.branch_name == "master"
                assert len(commit_info.changed_files) == 3
                assert "noveler/domain/entities/test_entity.py" in commit_info.changed_files

    def test_get_latest_commit_info_no_output(self, adapter):
        """Git logコマンドが結果なしの場合のテスト"""
        # Arrange
        with patch.object(adapter, "_run_git_command", return_value=None):
            # Act
            commit_info = adapter.get_latest_commit_info()

            # Assert
            assert commit_info is None

    def test_get_latest_commit_info_insufficient_lines(self, adapter):
        """Git log出力行数不足のテスト"""
        # Arrange
        insufficient_output = (
            "abcd1234567890abcdef1234567890abcdef1234|2025-01-15 10:30:00 +0900|John Doe|john@example.com|feat: test"
        )

        with patch.object(adapter, "_run_git_command", return_value=insufficient_output):
            # Act
            commit_info = adapter.get_latest_commit_info()

            # Assert
            assert commit_info is None

    def test_get_latest_commit_info_malformed_commit_line(self, adapter):
        """不正なコミット情報フォーマットのテスト"""
        # Arrange
        malformed_output = "invalid|format\nfile1.py\nfile2.py"

        with patch.object(adapter, "_run_git_command", return_value=malformed_output):
            # Act
            commit_info = adapter.get_latest_commit_info()

            # Assert
            assert commit_info is None

    def test_get_latest_commit_info_date_parse_error(self, adapter):
        """日付解析エラーのテスト"""
        # Arrange
        invalid_date_output = (
            "abcd1234567890abcdef1234567890abcdef1234|invalid-date|John Doe|john@example.com|feat: test\nfile.py"
        )

        with patch.object(adapter, "_run_git_command", return_value=invalid_date_output):
            with patch.object(adapter, "_get_current_branch", return_value="master"):
                # Act
                commit_info = adapter.get_latest_commit_info()

                # Assert
                assert commit_info is not None
                # 無効な日付の場合、現在時刻が使用される
                assert abs((commit_info.commit_date - datetime.now(timezone.utc)).total_seconds()) < 60

    def test_get_latest_commit_info_exception(self, adapter):
        """例外発生時のテスト"""
        # Arrange
        with patch.object(adapter, "_run_git_command", side_effect=Exception("Git error")):
            # Act
            commit_info = adapter.get_latest_commit_info()

            # Assert
            assert commit_info is None

    def test_get_commit_history_success(self, adapter):
        """コミット履歴取得成功テスト"""
        # Arrange
        history_output = (
            "commit1234567890abcdef1234567890abcdef1234|2025-01-15 10:30:00 +0900|John Doe|john@example.com|feat: feature 1\n"
            "commit5678901234abcdef5678901234abcdef5678|2025-01-14 15:20:00 +0900|Jane Smith|jane@example.com|fix: bug fix"
        )

        with patch.object(adapter, "_run_git_command", return_value=history_output):
            with patch.object(adapter, "_get_current_branch", return_value="develop"):
                with patch.object(adapter, "_get_changed_files_for_commit", return_value=["file.py"]):
                    # Act
                    commits = adapter.get_commit_history(limit=5)

                    # Assert
                    assert len(commits) == 2
                    assert commits[0].full_hash == "commit1234567890abcdef1234567890abcdef1234"
                    assert commits[0].author_name == "John Doe"
                    assert commits[0].branch_name == "develop"
                    assert commits[1].full_hash == "commit5678901234abcdef5678901234abcdef5678"
                    assert commits[1].author_name == "Jane Smith"

    def test_get_commit_history_no_output(self, adapter):
        """コミット履歴が空の場合のテスト"""
        # Arrange
        with patch.object(adapter, "_run_git_command", return_value=None):
            # Act
            commits = adapter.get_commit_history()

            # Assert
            assert commits == []

    def test_get_commit_history_exception(self, adapter):
        """コミット履歴取得例外のテスト"""
        # Arrange
        with patch.object(adapter, "_run_git_command", side_effect=Exception("History error")):
            # Act
            commits = adapter.get_commit_history()

            # Assert
            assert commits == []

    def test_is_git_repository_true(self, adapter):
        """Gitリポジトリ判定 - Trueの場合"""
        # Arrange
        with patch.object(adapter, "_run_git_command", return_value=".git"):
            # Act
            result = adapter.is_git_repository()

            # Assert
            assert result is True

    def test_is_git_repository_false(self, adapter):
        """Gitリポジトリ判定 - Falseの場合"""
        # Arrange
        with patch.object(adapter, "_run_git_command", return_value=None):
            # Act
            result = adapter.is_git_repository()

            # Assert
            assert result is False

    def test_is_git_repository_exception(self, adapter):
        """Gitリポジトリ判定 - 例外の場合"""
        # Arrange
        with patch.object(adapter, "_run_git_command", side_effect=Exception("Git error")):
            # Act
            result = adapter.is_git_repository()

            # Assert
            assert result is False

    def test_get_repository_status_success(self, adapter):
        """リポジトリ状態取得成功テスト"""
        # Arrange
        with patch.object(adapter, "_get_current_branch", return_value="feature-branch"):
            with patch.object(adapter, "_run_git_command") as mock_git:
                # git status --porcelain の結果
                mock_git.side_effect = [
                    " M file1.py\n?? file2.py",  # 未コミット変更あり
                    "abcd1234567890ab",  # HEAD commit hash
                    "## feature-branch...origin/feature-branch [ahead 2]",  # ブランチステータス
                ]

                # Act
                status = adapter.get_repository_status()

                # Assert
                assert status["current_branch"] == "feature-branch"
                assert status["has_uncommitted_changes"] is True
                assert status["latest_commit"] == "abcd1234"
                assert status["ahead_of_remote"] is True

    def test_get_repository_status_clean(self, adapter):
        """クリーンなリポジトリ状態のテスト"""
        # Arrange
        with patch.object(adapter, "_get_current_branch", return_value="main"):
            with patch.object(adapter, "_run_git_command") as mock_git:
                mock_git.side_effect = [
                    "",  # git status --porcelain が空
                    "efgh5678901234ef",  # HEAD commit hash
                    "## main...origin/main",  # ブランチステータス（同期済み）
                ]

                # Act
                status = adapter.get_repository_status()

                # Assert
                assert status["current_branch"] == "main"
                assert status["has_uncommitted_changes"] is False
                assert status["latest_commit"] == "efgh5678"
                assert status["synced_with_remote"] is True

    def test_get_repository_status_behind_remote(self, adapter):
        """リモートより遅れている状態のテスト"""
        # Arrange
        with patch.object(adapter, "_get_current_branch", return_value="main"):
            with patch.object(adapter, "_run_git_command") as mock_git:
                mock_git.side_effect = [
                    "",  # クリーン状態
                    "1234567890123456",  # HEAD
                    "## main...origin/main [behind 3]",  # リモートより遅れ
                ]

                # Act
                status = adapter.get_repository_status()

                # Assert
                assert status["behind_remote"] is True
                assert "ahead_of_remote" not in status
                assert "synced_with_remote" not in status

    def test_get_repository_status_exception(self, adapter):
        """リポジトリ状態取得例外のテスト"""
        # Arrange
        with patch.object(adapter, "_get_current_branch", side_effect=Exception("Status error")):
            # Act
            status = adapter.get_repository_status()

            # Assert
            assert "error" in status
            assert status["error"] == "Status error"

    def test_get_current_branch_success(self, adapter):
        """現在のブランチ名取得成功テスト"""
        # Arrange
        with patch.object(adapter, "_run_git_command", return_value="feature/new-feature\n"):
            # Act
            branch = adapter._get_current_branch()

            # Assert
            assert branch == "feature/new-feature"

    def test_get_current_branch_failure(self, adapter):
        """現在のブランチ名取得失敗時のテスト"""
        # Arrange
        with patch.object(adapter, "_run_git_command", return_value=None):
            # Act
            branch = adapter._get_current_branch()

            # Assert
            assert branch == "master"

    def test_get_changed_files_for_commit_success(self, adapter):
        """特定コミットの変更ファイル取得成功テスト"""
        # Arrange
        files_output = "\nfile1.py\nfile2.js\ndocs/README.md\n"

        with patch.object(adapter, "_run_git_command", return_value=files_output):
            # Act
            files = adapter._get_changed_files_for_commit("abc123")

            # Assert
            assert len(files) == 3
            assert "file1.py" in files
            assert "file2.js" in files
            assert "docs/README.md" in files

    def test_get_changed_files_for_commit_empty(self, adapter):
        """変更ファイルなしの場合のテスト"""
        # Arrange
        with patch.object(adapter, "_run_git_command", return_value=None):
            # Act
            files = adapter._get_changed_files_for_commit("abc123")

            # Assert
            assert files == []

    def test_run_git_command_success(self, adapter, repo_path):
        """Gitコマンド実行成功テスト"""
        # Arrange
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "git output"

        with patch("subprocess.run", return_value=mock_result) as mock_subprocess:
            # Act
            output = adapter._run_git_command(["status", "--porcelain"])

            # Assert
            assert output == "git output"
            mock_subprocess.assert_called_once_with(
                ["git", "status", "--porcelain"], cwd=repo_path, capture_output=True, text=True, timeout=30
            )

    def test_run_git_command_failure(self, adapter):
        """Gitコマンド実行失敗テスト"""
        # Arrange
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "fatal: not a git repository"

        with patch("subprocess.run", return_value=mock_result):
            # Act
            output = adapter._run_git_command(["status"])

            # Assert
            assert output is None

    def test_run_git_command_timeout(self, adapter):
        """Gitコマンドタイムアウトテスト"""
        # Arrange
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("git", 30)):
            # Act
            output = adapter._run_git_command(["log", "--all"])

            # Assert
            assert output is None

    def test_run_git_command_exception(self, adapter):
        """Gitコマンド実行例外テスト"""
        # Arrange
        with patch("subprocess.run", side_effect=Exception("Command error")):
            # Act
            output = adapter._run_git_command(["status"])

            # Assert
            assert output is None

    def test_get_file_last_modified_commit_success(self, adapter):
        """ファイル最終更新コミット取得成功テスト"""
        # Arrange
        commit_output = "file1234567890abcdef1234567890abcdef1234|2025-01-15 10:30:00 +0900|Author|author@example.com|docs: update file"

        with patch.object(adapter, "_run_git_command", return_value=commit_output):
            with patch.object(adapter, "_get_changed_files_for_commit", return_value=["target_file.py"]):
                with patch.object(adapter, "_get_current_branch", return_value="main"):
                    # Act
                    commit_info = adapter.get_file_last_modified_commit("target_file.py")

                    # Assert
                    assert commit_info is not None
                    assert commit_info.full_hash == "file1234567890abcdef1234567890abcdef1234"
                    assert commit_info.author_name == "Author"
                    assert commit_info.commit_message == "docs: update file"

    def test_get_file_last_modified_commit_no_result(self, adapter):
        """ファイル最終更新コミットが見つからない場合のテスト"""
        # Arrange
        with patch.object(adapter, "_run_git_command", return_value=None):
            # Act
            commit_info = adapter.get_file_last_modified_commit("nonexistent.py")

            # Assert
            assert commit_info is None

    def test_get_file_last_modified_commit_malformed(self, adapter):
        """不正なコミット情報フォーマットのテスト"""
        # Arrange
        with patch.object(adapter, "_run_git_command", return_value="malformed|output"):
            # Act
            commit_info = adapter.get_file_last_modified_commit("file.py")

            # Assert
            assert commit_info is None

    def test_get_file_last_modified_commit_exception(self, adapter):
        """ファイル最終更新コミット取得例外のテスト"""
        # Arrange
        with patch.object(adapter, "_run_git_command", side_effect=Exception("File error")):
            # Act
            commit_info = adapter.get_file_last_modified_commit("file.py")

            # Assert
            assert commit_info is None

    @pytest.mark.parametrize(
        ("git_output", "expected_result"),
        [
            (".git", True),
            ("/.git", True),
            ("/path/to/.git", True),
            ("", False),
            (None, False),
            ("not git related", False),
        ],
    )
    def test_is_git_repository_parametrized(self, adapter, git_output, expected_result):
        """Gitリポジトリ判定のパラメータ化テスト"""
        # Arrange
        with patch.object(adapter, "_run_git_command", return_value=git_output):
            # Act
            result = adapter.is_git_repository()

            # Assert
            assert result is expected_result

    @pytest.mark.parametrize(
        ("status_output", "expected_changes"),
        [
            ("", False),
            (" M modified.py", True),
            ("A  added.py", True),
            ("?? untracked.py", True),
            ("R  renamed.py", True),
            ("D  deleted.py", True),
            (" M file1.py\n?? file2.py\nA  file3.py", True),
        ],
    )
    def test_repository_status_uncommitted_changes(self, adapter, status_output, expected_changes):
        """未コミット変更検出のパラメータ化テスト"""
        # Arrange
        with patch.object(adapter, "_get_current_branch", return_value="test"):
            with patch.object(adapter, "_run_git_command") as mock_git:
                mock_git.side_effect = [
                    status_output,  # git status --porcelain
                    "1234567890123456",  # git rev-parse HEAD
                    "## test",  # git status -b --porcelain
                ]

                # Act
                status = adapter.get_repository_status()

                # Assert
                assert status["has_uncommitted_changes"] is expected_changes
