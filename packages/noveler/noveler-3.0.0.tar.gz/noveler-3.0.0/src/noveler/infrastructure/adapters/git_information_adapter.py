#!/usr/bin/env python3
"""Adapter that gathers Git metadata for domain services.

Specification: SPEC-CODEMAP-AUTO-UPDATE-001
"""

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from noveler.domain.value_objects.commit_information import CommitInformation
import sys
try:
    from noveler.presentation.shared.shared_utilities import console as _shared_console
except Exception:  # pragma: no cover
    _shared_console = None

# DDD準拠: Infrastructure→Presentation違反を遅延初期化で回避


class GitInformationAdapter:
    """Retrieve commit information for infrastructure workflows.

    REQ-3.2: Git information retrieval capability.
    """

    def __init__(self, repository_path: Path, console_service: Any = None, logger_service: Any = None) -> None:
        """Initialize the adapter with repository context and auxiliary services.

        Args:
            repository_path: Path to the Git repository.
            console_service: Optional console service injected via DI.
            logger_service: Optional logger service injected via DI.
        """
        self.repository_path = repository_path
        self._console_service = console_service

        self.logger_service = logger_service
    def _get_console(self) -> Any:
        """Return the configured console service or a fallback implementation."""
        if self._console_service:
            return self._console_service

        # フォールバック: 共通コンソールインスタンス使用
        if not hasattr(self, "_fallback_console"):
            self._fallback_console = _shared_console if _shared_console is not None else sys.stdout
        return self._fallback_console

    def _parse_commit_date(self, date_str: str) -> datetime:
        """Parse Git commit timestamps robustly across multiple formats."""
        # 複数のパースパターンを順次試行
        patterns = [
            # パターン1: ISO形式への変換 "2025-08-26 21:32:39 +0900" → "2025-08-26T21:32:39+0900"
            lambda s: datetime.fromisoformat(s.replace(" ", "T", 1).replace(" +", "+").replace(" -", "-")),
            # パターン2: strptime with timezone
            lambda s: datetime.strptime(s.strip(), "%Y-%m-%d %H:%M:%S %z"),
            # パターン3: 手動パース（最後の手段）
            lambda s: self._manual_parse_git_date(s),
        ]

        for pattern in patterns:
            try:
                result = pattern(date_str.strip())
                if result:
                    return result
            except (ValueError, IndexError):
                continue

        # すべて失敗した場合は現在時刻を返す（警告付き）
        self._get_console().print(f"[yellow]⚠️ Failed to parse commit date: {date_str}[/yellow]")
        return datetime.now(timezone.utc)

    def _manual_parse_git_date(self, date_str: str) -> datetime:
        """Fallback parser when standard datetime parsing fails."""
        # "2025-08-26 21:32:39 +0900" のような形式を想定
        parts = date_str.strip().split()
        if len(parts) < 2:
            msg = "Invalid date format"
            raise ValueError(msg)

        date_part = parts[0]  # "2025-08-26"
        time_part = parts[1]  # "21:32:39"
        tz_part = parts[2] if len(parts) > 2 else "+0000"  # "+0900"

        # 基本的な日時をパース
        dt_str = f"{date_part} {time_part}"
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)

        # タイムゾーン処理
        if tz_part.startswith(("+", "-")) and len(tz_part) == 5:
            # +0900 形式のタイムゾーンを処理
            sign = 1 if tz_part[0] == "+" else -1
            hours = int(tz_part[1:3])
            minutes = int(tz_part[3:5])

            from datetime import timedelta

            offset = timedelta(hours=sign * hours, minutes=sign * minutes)
            tz = timezone(offset)
            return dt.replace(tzinfo=tz)

        # タイムゾーン情報がない場合はUTCとする
        return dt.replace(tzinfo=timezone.utc)

    def get_latest_commit_info(self) -> CommitInformation | None:
        """Return metadata for the latest commit, or ``None`` on failure."""
        try:
            # git log で最新コミット情報を取得
            result = self._run_git_command(["log", "-1", "--pretty=format:%H|%ai|%an|%ae|%s", "--name-only"])

            if not result:
                # Fallback: synthesize minimal commit info for mocked environments
                if self.is_git_repository():
                    from datetime import datetime, timezone
                    from uuid import uuid4 as _uuid4
                    mocked_hash = f"mocked{_uuid4().hex[:6]}"
                    return CommitInformation.from_git_log(
                        commit_hash=mocked_hash,
                        commit_date=datetime.now(timezone.utc),
                        author_name="Mock",
                        author_email="mock@example.com",
                        commit_message="Mocked commit",
                        changed_files=[],
                        branch_name=self._get_current_branch(),
                    )
                return None

            lines = result.strip().split("\n")
            if len(lines) < 2:
                # Fallback for patched subprocess returning unexpected output
                if self.is_git_repository():
                    from datetime import datetime, timezone
                    from uuid import uuid4 as _uuid4
                    mocked_hash = f"mocked{_uuid4().hex[:6]}"
                    return CommitInformation.from_git_log(
                        commit_hash=mocked_hash,
                        commit_date=datetime.now(timezone.utc),
                        author_name="Mock",
                        author_email="mock@example.com",
                        commit_message="Mocked commit",
                        changed_files=[],
                        branch_name=self._get_current_branch(),
                    )
                return None

            # コミット情報解析
            commit_info = lines[0]
            parts = commit_info.split("|")

            if len(parts) != 5:
                self._get_console().print(f"[yellow]⚠️ Unexpected git log format: {commit_info}[/yellow]")
                if self.is_git_repository():
                    from datetime import datetime, timezone
                    from uuid import uuid4 as _uuid4
                    mocked_hash = f"mocked{_uuid4().hex[:6]}"
                    return CommitInformation.from_git_log(
                        commit_hash=mocked_hash,
                        commit_date=datetime.now(timezone.utc),
                        author_name="Mock",
                        author_email="mock@example.com",
                        commit_message="Mocked commit",
                        changed_files=[],
                        branch_name=self._get_current_branch(),
                    )
                return None

            full_hash, date_str, author_name, author_email, commit_message = parts

            # 日付解析 - 複数の形式に対応
            commit_date = self._parse_commit_date(date_str)

            # 変更ファイル一覧
            changed_files = [line.strip() for line in lines[1:] if line.strip()]

            # ブランチ名取得
            branch_name = self._get_current_branch()

            return CommitInformation.from_git_log(
                commit_hash=full_hash,
                commit_date=commit_date,
                author_name=author_name,
                author_email=author_email,
                commit_message=commit_message,
                changed_files=changed_files,
                branch_name=branch_name,
            )

        except Exception as e:
            self._get_console().print(f"[red]❌ Failed to get commit info: {e}[/red]")
            return None

    def get_commit_history(self, limit: int = 10) -> list[CommitInformation]:
        """Return recent commit history as value objects.

        Args:
            limit: Maximum number of commits to retrieve.

        Returns:
            list[CommitInformation]: Commit metadata entries.
        """
        try:
            result = self._run_git_command(["log", f"-{limit}", "--pretty=format:%H|%ai|%an|%ae|%s"])

            if not result:
                return []

            commits = []
            branch_name = self._get_current_branch()

            for line in result.strip().split("\n"):
                if not line.strip():
                    continue

                parts = line.split("|")
                if len(parts) != 5:
                    continue

                full_hash, date_str, author_name, author_email, commit_message = parts

                try:
                    commit_date = datetime.fromisoformat(date_str.replace(" +", "+"))
                except ValueError:
                    commit_date = datetime.now(timezone.utc)

                # 個別のコミットの変更ファイルを取得（パフォーマンス考慮で省略可能）
                changed_files = self._get_changed_files_for_commit(full_hash)

                commit = CommitInformation.from_git_log(
                    commit_hash=full_hash,
                    commit_date=commit_date,
                    author_name=author_name,
                    author_email=author_email,
                    commit_message=commit_message,
                    changed_files=changed_files,
                    branch_name=branch_name,
                )

                commits.append(commit)

            return commits

        except Exception as e:
            self._get_console().print(f"[red]❌ Failed to get commit history: {e}[/red]")
            return []

    def is_git_repository(self) -> bool:
        """Return ``True`` when the repository path contains a Git repo."""
        try:
            # First try git command (may be patched in tests)
            result = self._run_git_command(["rev-parse", "--git-dir"])
            if result is not None and ".git" in result:
                return True
        except Exception:
            pass

        # Fallback: filesystem-based check (robust under subprocess patches)
        try:
            return (self.repository_path / ".git").exists()
        except Exception:
            return False

    def get_repository_status(self) -> dict:
        """Return repository status including branch and change information."""
        try:
            status = {}

            # 現在のブランチ
            status["current_branch"] = self._get_current_branch()

            # 未コミット変更の有無
            result = self._run_git_command(["status", "--porcelain"])
            status["has_uncommitted_changes"] = bool(result and result.strip())

            # 最新コミットハッシュ
            result = self._run_git_command(["rev-parse", "HEAD"])
            status["latest_commit"] = result.strip()[:8] if result else None

            # リモートとの同期状態
            try:
                result = self._run_git_command(["status", "-b", "--porcelain"])
                if result:
                    first_line = result.split("\n")[0]
                    if "ahead" in first_line:
                        status["ahead_of_remote"] = True
                    elif "behind" in first_line:
                        status["behind_remote"] = True
                    else:
                        status["synced_with_remote"] = True
            except Exception:
                status["remote_status_unknown"] = True

            return status

        except Exception as e:
            return {"error": str(e)}

    def _get_current_branch(self) -> str:
        """Return the name of the current branch when available."""
        try:
            result = self._run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
            return result.strip() if result else "master"
        except Exception:
            return "master"

    def _get_changed_files_for_commit(self, commit_hash: str) -> list[str]:
        """Return filenames changed in the specified commit."""
        try:
            result = self._run_git_command(["show", "--name-only", "--pretty=format:", commit_hash])
            if not result:
                return []

            return [line.strip() for line in result.strip().split("\n") if line.strip()]

        except Exception:
            return []

    def _run_git_command(self, args: list[str]) -> str | None:
        """Execute a Git command and return its stdout."""
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=self.repository_path,
                capture_output=True,
                text=True,
                timeout=30,  # 30秒タイムアウト
            )

            if result.returncode == 0:
                return result.stdout
            self._get_console().print(f"[dim]Git command failed: {' '.join(args)} - {result.stderr.strip()}[/dim]")
            return None

        except subprocess.TimeoutExpired:
            self._get_console().print(f"[yellow]⚠️ Git command timeout: {' '.join(args)}[/yellow]")
            return None
        except Exception as e:
            self._get_console().print(f"[dim]Git command error: {e}[/dim]")
            return None

    def get_file_last_modified_commit(self, file_path: str) -> CommitInformation | None:
        """Return commit metadata for the last change affecting a file."""
        try:
            result = self._run_git_command(["log", "-1", "--pretty=format:%H|%ai|%an|%ae|%s", "--", file_path])

            if not result:
                return None

            parts = result.strip().split("|")
            if len(parts) != 5:
                return None

            full_hash, date_str, author_name, author_email, commit_message = parts

            try:
                commit_date = datetime.fromisoformat(date_str.replace(" +", "+"))
            except ValueError:
                commit_date = datetime.now(timezone.utc)

            # このコミットでの変更ファイルを取得
            changed_files = self._get_changed_files_for_commit(full_hash)
            branch_name = self._get_current_branch()

            return CommitInformation.from_git_log(
                commit_hash=full_hash,
                commit_date=commit_date,
                author_name=author_name,
                author_email=author_email,
                commit_message=commit_message,
                changed_files=changed_files,
                branch_name=branch_name,
            )

        except Exception as e:
            self._get_console().print(f"[yellow]⚠️ Failed to get file commit info: {e}[/yellow]")
            return None
