#!/usr/bin/env python3
"""プロットコミットバージョン提案ユースケース"""

from dataclasses import dataclass
from typing import Protocol

from noveler.domain.versioning.value_objects import VersionCalculator


@dataclass
class CommitAnalysis:
    """コミット分析結果"""

    requires_versioning: bool
    significance: "ChangeSignificance"
    reason: str
    changed_files: list[str]


@dataclass
class ChangeSignificance:
    """変更の重要度"""

    level: str  # "major", "minor", "patch"


class CommitAnalyzer(Protocol):
    """コミット分析器のプロトコル"""

    def analyze_commit(self, changed_files: list[str], git_diff: str) -> CommitAnalysis:
        """コミットを分析"""
        ...


class VersionRepository(Protocol):
    """バージョンリポジトリのプロトコル"""

    def get_current_version(self) -> str:
        """現在のバージョンを取得"""
        ...


class GitService(Protocol):
    """Gitサービスのプロトコル"""

    def get_changed_files(self) -> list[str]:
        """変更されたファイルを取得"""
        ...


@dataclass
class VersionProposal:
    """バージョン提案結果"""

    should_propose: bool
    suggested_version: str | None = None
    change_type: str | None = None
    reason: str = ""
    changed_files: list[str] = None

    def __post_init__(self) -> None:
        if self.changed_files is None:
            self.changed_files = []


class PlotCommitVersionProposer:
    """プロットコミットバージョン提案器ユースケース"""

    def __init__(self, analyzer: CommitAnalyzer, version_repo: VersionRepository, git_service: GitService) -> None:
        self.analyzer = analyzer
        self.version_repo = version_repo
        self.git_service = git_service
        self.calculator = VersionCalculator()

    def propose_version_update(self) -> VersionProposal:
        """バージョン更新を提案"""

        # 最新コミットの変更を取得
        changed_files = self.git_service.get_changed_files()
        git_diff = self._get_git_diff_content()

        # コミット内容を分析
        analysis = self.analyzer.analyze_commit(changed_files, git_diff)

        if not analysis.requires_versioning:
            return VersionProposal(
                should_propose=False,
                reason=f"軽微な変更のため提案をスキップ: {analysis.reason}",
            )

        # 現在のバージョンを取得
        current_version = self.version_repo.get_current_version()

        # 提案するバージョンを計算
        change_type = analysis.significance.level
        suggested_version = self.calculator.calculate_next_version(
            current_version,
            change_type,
        )

        return VersionProposal(
            should_propose=True,
            suggested_version=suggested_version,
            change_type=change_type,
            reason=analysis.reason,
            changed_files=analysis.changed_files,
        )

    def _get_git_diff_content(self) -> str:
        """Git差分内容を取得(簡略版)"""
        # 実際の実装では git diff コマンドを実行
        return ""  # 最小実装
