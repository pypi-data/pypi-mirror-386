#!/usr/bin/env python3
"""コミット情報バリューオブジェクト

仕様書: SPEC-CODEMAP-AUTO-UPDATE-001
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CommitInformation:
    """Git コミット情報のバリューオブジェクト

    不変オブジェクトとして、コミットに関する情報を保持
    """

    full_hash: str
    short_hash: str
    commit_date: datetime
    author_name: str
    author_email: str
    commit_message: str
    changed_files: list[str]
    branch_name: str

    @classmethod
    def from_git_log(
        cls,
        commit_hash: str,
        commit_date: datetime,
        author_name: str,
        author_email: str,
        commit_message: str,
        changed_files: list[str],
        branch_name: str = "master",
    ) -> "CommitInformation":
        """Git ログ情報から CommitInformation を作成

        Args:
            commit_hash: 完全なコミットハッシュ
            commit_date: コミット日時
            author_name: 作者名
            author_email: 作者メールアドレス
            commit_message: コミットメッセージ
            changed_files: 変更されたファイル一覧
            branch_name: ブランチ名

        Returns:
            CommitInformation: コミット情報オブジェクト
        """
        return cls(
            full_hash=commit_hash,
            short_hash=commit_hash[:8] if len(commit_hash) >= 8 else commit_hash,
            commit_date=commit_date,
            author_name=author_name,
            author_email=author_email,
            commit_message=commit_message,
            changed_files=changed_files,
            branch_name=branch_name,
        )

    def is_merge_commit(self) -> bool:
        """マージコミットかどうかを判定"""
        return "Merge" in self.commit_message or "merge" in self.commit_message.lower()

    def has_changed_files_in_layer(self, layer_path: str) -> bool:
        """指定されたレイヤーのファイルが変更されているかチェック

        Args:
            layer_path: レイヤーのパス (例: "noveler/domain/")

        Returns:
            bool: 該当レイヤーのファイルが変更されている場合True
        """
        return any(layer_path in file_path for file_path in self.changed_files)

    def get_changed_files_by_extension(self, extension: str) -> list[str]:
        """指定された拡張子の変更ファイル一覧を取得

        Args:
            extension: ファイル拡張子 (例: ".py", ".yaml")

        Returns:
            List[str]: 該当拡張子のファイル一覧
        """
        return [f for f in self.changed_files if f.endswith(extension)]

    def get_affected_architecture_layers(self) -> list[str]:
        """影響を受けるアーキテクチャ層を特定

        Returns:
            List[str]: 影響を受けるレイヤー名一覧
        """
        affected_layers = []

        layer_mappings = {
            "noveler/domain/": "domain",
            "noveler/application/": "application",
            "noveler/infrastructure/": "infrastructure",
            "noveler/presentation/": "presentation",
            "docs/": "documentation",
            "specs/": "specification",
        }

        for file_path in self.changed_files:
            for layer_path, layer_name in layer_mappings.items():
                if layer_path in file_path and layer_name not in affected_layers:
                    affected_layers.append(layer_name)

        return affected_layers

    def is_documentation_update(self) -> bool:
        """ドキュメント更新コミットかどうかを判定"""
        doc_patterns = [".md", ".yaml", ".yml", "README", "CHANGELOG"]
        return any(any(pattern in file_path for pattern in doc_patterns) for file_path in self.changed_files)

    def is_implementation_commit(self) -> bool:
        """実装コミットかどうかを判定（コード変更を含む）"""
        code_extensions = [".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs"]
        return any(any(file_path.endswith(ext) for ext in code_extensions) for file_path in self.changed_files)

    def get_commit_category(self) -> str:
        """コミットカテゴリを推定

        Returns:
            str: コミットカテゴリ ("feat", "fix", "docs", "test", "refactor", etc.)
        """
        message = self.commit_message.lower()

        # コミットメッセージパターンマッチング
        if message.startswith("feat"):
            return "feat"
        if message.startswith("fix"):
            return "fix"
        if message.startswith("docs"):
            return "docs"
        if message.startswith("test"):
            return "test"
        if message.startswith("refactor"):
            return "refactor"
        if message.startswith("style"):
            return "style"
        if message.startswith("chore"):
            return "chore"

        # ファイル変更パターンから推定
        if self.is_documentation_update() and not self.is_implementation_commit():
            return "docs"
        if any("test" in f for f in self.changed_files):
            return "test"
        if self.is_implementation_commit():
            return "feat"  # デフォルトで新機能として扱う

        return "chore"

    def summarize(self) -> str:
        """コミット情報の要約を生成"""
        return (
            f"Commit {self.short_hash} by {self.author_name} "
            f"on {self.commit_date.strftime('%Y-%m-%d %H:%M')} "
            f"({len(self.changed_files)} files changed)"
        )
