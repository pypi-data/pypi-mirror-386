# Gitサービス仕様書

## 概要
Gitサービスは基本的なGitリポジトリ操作を提供するアダプターサービスです。コミット、ブランチ操作、ファイル管理、リモートリポジトリ連携などの基本的なGit機能をドメイン層に抽象化して提供します。

## クラス設計

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import subprocess
from datetime import datetime

class GitStatus(Enum):
    """Gitステータス"""
    CLEAN = "clean"
    MODIFIED = "modified"
    STAGED = "staged"
    CONFLICTED = "conflicted"
    UNTRACKED = "untracked"

class RemoteOperation(Enum):
    """リモート操作"""
    PUSH = "push"
    PULL = "pull"
    FETCH = "fetch"
    CLONE = "clone"

@dataclass
class FileStatus:
    """ファイル状態"""
    path: str
    status: GitStatus
    staged: bool = False

@dataclass
class CommitInfo:
    """コミット情報"""
    hash: str
    author: str
    email: str
    timestamp: datetime
    message: str
    files_changed: List[str]

@dataclass
class BranchInfo:
    """ブランチ情報"""
    name: str
    current: bool
    remote: Optional[str] = None
    last_commit: Optional[CommitInfo] = None

class IGitService(ABC):
    """Gitサービスインターフェース"""

    @abstractmethod
    def init_repository(self, path: str) -> bool:
        """リポジトリを初期化"""
        pass

    @abstractmethod
    def add_files(self, files: List[str]) -> bool:
        """ファイルをステージング"""
        pass

    @abstractmethod
    def commit(self, message: str, author: Optional[str] = None) -> Optional[str]:
        """変更をコミット"""
        pass

    @abstractmethod
    def get_status(self) -> List[FileStatus]:
        """リポジトリ状態を取得"""
        pass

    @abstractmethod
    def get_branches(self) -> List[BranchInfo]:
        """ブランチリストを取得"""
        pass

    @abstractmethod
    def create_branch(self, name: str, base: Optional[str] = None) -> bool:
        """ブランチを作成"""
        pass

    @abstractmethod
    def switch_branch(self, name: str) -> bool:
        """ブランチを切り替え"""
        pass

@dataclass
class GitConfig:
    """Git設定"""
    repository_path: str
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    remote_url: Optional[str] = None
    default_branch: str = "main"

class GitService(IGitService):
    """Gitサービス実装"""

    def __init__(
        self,
        config: GitConfig,
        command_executor: ICommandExecutor,
        file_system: IFileSystemAdapter,
        logger: Optional[ILogger] = None
    ):
        self._config = config
        self._executor = command_executor
        self._fs = file_system
        self._logger = logger or NullLogger()
```

## データ構造

### インターフェース定義

```python
class ICommandExecutor(ABC):
    """コマンド実行インターフェース"""

    @abstractmethod
    def execute(
        self,
        command: List[str],
        cwd: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> CommandResult:
        """コマンドを実行"""
        pass

class IFileSystemAdapter(ABC):
    """ファイルシステムアダプターインターフェース"""

    @abstractmethod
    def exists(self, path: str) -> bool:
        """パスが存在するかチェック"""
        pass

    @abstractmethod
    def is_directory(self, path: str) -> bool:
        """ディレクトリかチェック"""
        pass

    @abstractmethod
    def get_files(self, pattern: str, recursive: bool = True) -> List[str]:
        """ファイルリストを取得"""
        pass

class ILogger(ABC):
    """ロガーインターフェース"""

    @abstractmethod
    def info(self, message: str) -> None:
        """情報ログ"""
        pass

    @abstractmethod
    def error(self, message: str, exception: Optional[Exception] = None) -> None:
        """エラーログ"""
        pass

@dataclass
class CommandResult:
    """コマンド実行結果"""
    return_code: int
    stdout: str
    stderr: str
    success: bool
    execution_time: float

@dataclass
class GitOperationContext:
    """Git操作コンテキスト"""
    repository_path: str
    current_branch: Optional[str]
    working_directory_clean: bool
    remote_connected: bool
```

### アダプター実装

```python
class SubprocessCommandExecutor(ICommandExecutor):
    """subprocess を使ったコマンド実行"""

    def execute(
        self,
        command: List[str],
        cwd: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> CommandResult:
        import time
        start_time = time.time()

        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout or 30,
                check=False
            )

            execution_time = time.time() - start_time

            return CommandResult(
                return_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                success=result.returncode == 0,
                execution_time=execution_time
            )

        except subprocess.TimeoutExpired:
            return CommandResult(
                return_code=-1,
                stdout="",
                stderr="Command timed out",
                success=False,
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return CommandResult(
                return_code=-1,
                stdout="",
                stderr=str(e),
                success=False,
                execution_time=time.time() - start_time
            )

class PathFileSystemAdapter(IFileSystemAdapter):
    """pathlib を使ったファイルシステム操作"""

    def exists(self, path: str) -> bool:
        return Path(path).exists()

    def is_directory(self, path: str) -> bool:
        return Path(path).is_dir()

    def get_files(self, pattern: str, recursive: bool = True) -> List[str]:
        base_path = Path(self._config.repository_path)

        if recursive:
            files = base_path.rglob(pattern)
        else:
            files = base_path.glob(pattern)

        return [str(f.relative_to(base_path)) for f in files if f.is_file()]
```

## パブリックメソッド

### GitService

```python
def init_repository(self, path: str) -> bool:
    """
    リポジトリを初期化

    Args:
        path: リポジトリパス

    Returns:
        bool: 初期化成功可否
    """
    try:
        # ディレクトリが存在しない場合は作成
        if not self._fs.exists(path):
            Path(path).mkdir(parents=True, exist_ok=True)

        # git init 実行
        result = self._executor.execute(['git', 'init'], cwd=path)

        if not result.success:
            self._logger.error(f"Git init failed: {result.stderr}")
            return False

        # 設定適用
        self._apply_initial_config(path)

        self._logger.info(f"Git repository initialized at {path}")
        return True

    except Exception as e:
        self._logger.error(f"Failed to initialize repository: {str(e)}", e)
        return False

def add_files(self, files: List[str]) -> bool:
    """
    ファイルをステージング

    Args:
        files: ステージングするファイルのリスト

    Returns:
        bool: 操作成功可否
    """
    try:
        if not files:
            return True

        # ファイル存在チェック
        existing_files = []
        for file in files:
            file_path = Path(self._config.repository_path) / file
            if file_path.exists():
                existing_files.append(file)
            else:
                self._logger.error(f"File not found: {file}")

        if not existing_files:
            return False

        # git add 実行
        command = ['git', 'add'] + existing_files
        result = self._executor.execute(command, cwd=self._config.repository_path)

        if result.success:
            self._logger.info(f"Added {len(existing_files)} files to staging area")
            return True
        else:
            self._logger.error(f"Git add failed: {result.stderr}")
            return False

    except Exception as e:
        self._logger.error(f"Failed to add files: {str(e)}", e)
        return False

def commit(self, message: str, author: Optional[str] = None) -> Optional[str]:
    """
    変更をコミット

    Args:
        message: コミットメッセージ
        author: 作成者（指定されない場合は設定を使用）

    Returns:
        Optional[str]: コミットハッシュ（失敗時はNone）
    """
    try:
        if not message.strip():
            self._logger.error("Commit message cannot be empty")
            return None

        # ステージングエリアに変更があるかチェック
        status_result = self._executor.execute(['git', 'status', '--porcelain'],
                                               cwd=self._config.repository_path)

        if not status_result.success:
            self._logger.error(f"Failed to check git status: {status_result.stderr}")
            return None

        staged_files = [line for line in status_result.stdout.split('\n')
                       if line and line[0] in ['A', 'M', 'D', 'R', 'C']]

        if not staged_files:
            self._logger.info("No staged changes to commit")
            return None

        # コミット実行
        command = ['git', 'commit', '-m', message]

        if author:
            command.extend(['--author', author])

        result = self._executor.execute(command, cwd=self._config.repository_path)

        if result.success:
            # コミットハッシュを取得
            hash_result = self._executor.execute(['git', 'rev-parse', 'HEAD'],
                                                cwd=self._config.repository_path)

            if hash_result.success:
                commit_hash = hash_result.stdout.strip()
                self._logger.info(f"Committed changes: {commit_hash[:8]}")
                return commit_hash

        self._logger.error(f"Git commit failed: {result.stderr}")
        return None

    except Exception as e:
        self._logger.error(f"Failed to commit changes: {str(e)}", e)
        return None

def get_status(self) -> List[FileStatus]:
    """
    リポジトリ状態を取得

    Returns:
        List[FileStatus]: ファイル状態のリスト
    """
    try:
        result = self._executor.execute(['git', 'status', '--porcelain'],
                                       cwd=self._config.repository_path)

        if not result.success:
            self._logger.error(f"Failed to get git status: {result.stderr}")
            return []

        return self._parse_status_output(result.stdout)

    except Exception as e:
        self._logger.error(f"Failed to get repository status: {str(e)}", e)
        return []

def get_branches(self) -> List[BranchInfo]:
    """
    ブランチリストを取得

    Returns:
        List[BranchInfo]: ブランチ情報のリスト
    """
    try:
        result = self._executor.execute(['git', 'branch', '-v'],
                                       cwd=self._config.repository_path)

        if not result.success:
            self._logger.error(f"Failed to get branches: {result.stderr}")
            return []

        return self._parse_branch_output(result.stdout)

    except Exception as e:
        self._logger.error(f"Failed to get branches: {str(e)}", e)
        return []

def create_branch(self, name: str, base: Optional[str] = None) -> bool:
    """
    ブランチを作成

    Args:
        name: ブランチ名
        base: ベースブランチ（指定されない場合は現在のブランチ）

    Returns:
        bool: 作成成功可否
    """
    try:
        if not self._validate_branch_name(name):
            self._logger.error(f"Invalid branch name: {name}")
            return False

        # ブランチ作成コマンド
        command = ['git', 'checkout', '-b', name]
        if base:
            command.append(base)

        result = self._executor.execute(command, cwd=self._config.repository_path)

        if result.success:
            self._logger.info(f"Created and switched to branch: {name}")
            return True
        else:
            self._logger.error(f"Failed to create branch: {result.stderr}")
            return False

    except Exception as e:
        self._logger.error(f"Failed to create branch: {str(e)}", e)
        return False

def switch_branch(self, name: str) -> bool:
    """
    ブランチを切り替え

    Args:
        name: 切り替え先ブランチ名

    Returns:
        bool: 切り替え成功可否
    """
    try:
        result = self._executor.execute(['git', 'checkout', name],
                                       cwd=self._config.repository_path)

        if result.success:
            self._logger.info(f"Switched to branch: {name}")
            return True
        else:
            self._logger.error(f"Failed to switch branch: {result.stderr}")
            return False

    except Exception as e:
        self._logger.error(f"Failed to switch branch: {str(e)}", e)
        return False
```

## プライベートメソッド

```python
def _apply_initial_config(self, path: str) -> None:
    """初期設定を適用"""
    if self._config.user_name:
        self._executor.execute(['git', 'config', 'user.name', self._config.user_name], cwd=path)

    if self._config.user_email:
        self._executor.execute(['git', 'config', 'user.email', self._config.user_email], cwd=path)

    # デフォルトブランチ設定
    if self._config.default_branch != "master":
        self._executor.execute(['git', 'branch', '-m', self._config.default_branch], cwd=path)

def _parse_status_output(self, output: str) -> List[FileStatus]:
    """git statusの出力を解析"""
    status_list = []

    for line in output.strip().split('\n'):
        if not line:
            continue

        index_status = line[0] if len(line) > 0 else ' '
        worktree_status = line[1] if len(line) > 1 else ' '
        file_path = line[3:] if len(line) > 3 else ''

        # ステータス判定
        if index_status in ['A', 'M', 'D', 'R', 'C']:
            staged = True
            if worktree_status == 'M':
                status = GitStatus.MODIFIED
            elif index_status == 'A':
                status = GitStatus.STAGED
            elif index_status == 'D':
                status = GitStatus.STAGED
            else:
                status = GitStatus.STAGED
        elif worktree_status == 'M':
            staged = False
            status = GitStatus.MODIFIED
        elif line.startswith('??'):
            staged = False
            status = GitStatus.UNTRACKED
        elif line.startswith('UU'):
            staged = False
            status = GitStatus.CONFLICTED
        else:
            staged = False
            status = GitStatus.CLEAN

        status_list.append(FileStatus(
            path=file_path,
            status=status,
            staged=staged
        ))

    return status_list

def _parse_branch_output(self, output: str) -> List[BranchInfo]:
    """git branchの出力を解析"""
    branches = []

    for line in output.strip().split('\n'):
        if not line:
            continue

        # 現在のブランチは * で始まる
        is_current = line.startswith('*')
        line = line.lstrip('* ').strip()

        # ブランチ名と最新コミット情報を分離
        parts = line.split()
        if len(parts) >= 2:
            branch_name = parts[0]
            commit_hash = parts[1]

            # コミット情報を取得
            commit_info = self._get_commit_info(commit_hash)

            branches.append(BranchInfo(
                name=branch_name,
                current=is_current,
                last_commit=commit_info
            ))

    return branches

def _get_commit_info(self, commit_hash: str) -> Optional[CommitInfo]:
    """コミット情報を取得"""
    try:
        # コミット情報取得コマンド
        result = self._executor.execute([
            'git', 'show', '--format=%H|%an|%ae|%at|%s', '--name-only', commit_hash
        ], cwd=self._config.repository_path)

        if not result.success:
            return None

        lines = result.stdout.strip().split('\n')
        if not lines:
            return None

        # 最初の行はコミット情報
        commit_line = lines[0]
        parts = commit_line.split('|')

        if len(parts) < 5:
            return None

        # ファイル変更リスト
        files_changed = [line for line in lines[2:] if line and not line.startswith('commit')]

        return CommitInfo(
            hash=parts[0],
            author=parts[1],
            email=parts[2],
            timestamp=datetime.fromtimestamp(int(parts[3])),
            message=parts[4],
            files_changed=files_changed
        )

    except Exception:
        return None

def _validate_branch_name(self, name: str) -> bool:
    """ブランチ名の妥当性を検証"""
    if not name or not name.strip():
        return False

    # Git で無効な文字をチェック
    invalid_chars = [' ', '~', '^', ':', '?', '*', '[', '\\', '..', '@{', '/']

    for char in invalid_chars:
        if char in name:
            return False

    # 先頭・末尾の制限
    if name.startswith('/') or name.endswith('/'):
        return False
    if name.startswith('.') or name.endswith('.'):
        return False
    if name.startswith('-') or name.endswith('-'):
        return False

    return True

def _ensure_git_repository(self) -> bool:
    """Gitリポジトリが存在することを確認"""
    git_dir = Path(self._config.repository_path) / '.git'
    return git_dir.exists()
```

## アダプターパターン実装

### リモートリポジトリ操作

```python
class RemoteGitAdapter:
    """リモートGit操作アダプター"""

    def __init__(self, git_service: IGitService, config: GitConfig):
        self._git = git_service
        self._config = config

    def push_to_remote(self, branch: str, remote: str = "origin") -> bool:
        """リモートにプッシュ"""
        try:
            result = self._git._executor.execute([
                'git', 'push', remote, branch
            ], cwd=self._config.repository_path)

            return result.success

        except Exception:
            return False

    def pull_from_remote(self, branch: str, remote: str = "origin") -> bool:
        """リモートからプル"""
        try:
            result = self._git._executor.execute([
                'git', 'pull', remote, branch
            ], cwd=self._config.repository_path)

            return result.success

        except Exception:
            return False

    def fetch_from_remote(self, remote: str = "origin") -> bool:
        """リモートからフェッチ"""
        try:
            result = self._git._executor.execute([
                'git', 'fetch', remote
            ], cwd=self._config.repository_path)

            return result.success

        except Exception:
            return False

class GitHooksAdapter:
    """Gitフック統合アダプター"""

    def __init__(self, git_service: IGitService):
        self._git = git_service

    def install_pre_commit_hook(self, hook_script: str) -> bool:
        """pre-commitフックをインストール"""
        try:
            hooks_dir = Path(self._git._config.repository_path) / '.git' / 'hooks'
            hooks_dir.mkdir(exist_ok=True)

            hook_file = hooks_dir / 'pre-commit'

            with open(hook_file, 'w') as f:
                f.write('#!/bin/sh\n')
                f.write(hook_script)

            # 実行権限を付与
            hook_file.chmod(0o755)

            return True

        except Exception:
            return False

    def install_commit_msg_hook(self, hook_script: str) -> bool:
        """commit-msgフックをインストール"""
        try:
            hooks_dir = Path(self._git._config.repository_path) / '.git' / 'hooks'
            hooks_dir.mkdir(exist_ok=True)

            hook_file = hooks_dir / 'commit-msg'

            with open(hook_file, 'w') as f:
                f.write('#!/bin/sh\n')
                f.write(hook_script)

            # 実行権限を付与
            hook_file.chmod(0o755)

            return True

        except Exception:
            return False
```

### 履歴操作アダプター

```python
class GitHistoryAdapter:
    """Git履歴操作アダプター"""

    def __init__(self, git_service: IGitService):
        self._git = git_service

    def get_commit_history(self, limit: int = 100, branch: Optional[str] = None) -> List[CommitInfo]:
        """コミット履歴を取得"""
        try:
            command = ['git', 'log', f'--max-count={limit}', '--format=%H|%an|%ae|%at|%s']
            if branch:
                command.append(branch)

            result = self._git._executor.execute(command, cwd=self._git._config.repository_path)

            if not result.success:
                return []

            commits = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                parts = line.split('|')
                if len(parts) >= 5:
                    commits.append(CommitInfo(
                        hash=parts[0],
                        author=parts[1],
                        email=parts[2],
                        timestamp=datetime.fromtimestamp(int(parts[3])),
                        message=parts[4],
                        files_changed=[]
                    ))

            return commits

        except Exception:
            return []

    def get_file_history(self, file_path: str, limit: int = 50) -> List[CommitInfo]:
        """ファイルの変更履歴を取得"""
        try:
            result = self._git._executor.execute([
                'git', 'log', f'--max-count={limit}', '--format=%H|%an|%ae|%at|%s', '--', file_path
            ], cwd=self._git._config.repository_path)

            if not result.success:
                return []

            commits = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                parts = line.split('|')
                if len(parts) >= 5:
                    commits.append(CommitInfo(
                        hash=parts[0],
                        author=parts[1],
                        email=parts[2],
                        timestamp=datetime.fromtimestamp(int(parts[3])),
                        message=parts[4],
                        files_changed=[file_path]
                    ))

            return commits

        except Exception:
            return []
```

## 依存関係

```python
from domain.entities import Project, Episode
from domain.value_objects import FileName, CommitMessage
from domain.services import IFileService
from application.use_cases import CreateCommitUseCase
```

## 設計原則遵守

### アダプターパターン
- **外部システム分離**: Git操作を抽象インターフェースで隠蔽
- **複数実装**: SubprocessとLibGit2の両方に対応可能
- **統一インターフェース**: ドメイン層は具体的なGit実装を知らない

### 単一責任原則
- **コマンド実行**: CommandExecutorが担当
- **ファイル操作**: FileSystemAdapterが担当
- **ログ出力**: Loggerが担当

## 使用例

### 基本的な使用

```python
# 設定
config = GitConfig(
    repository_path="/path/to/project",
    user_name="Author Name",
    user_email="author@example.com"
)

# アダプター設定
executor = SubprocessCommandExecutor()
fs_adapter = PathFileSystemAdapter()
logger = ConsoleLogger()

# サービス作成
git_service = GitService(config, executor, fs_adapter, logger)

# リポジトリ初期化
git_service.init_repository("/path/to/project")

# ファイル追加とコミット
git_service.add_files(["README.md", "main.py"])
commit_hash = git_service.commit("Initial commit")

if commit_hash:
    print(f"Committed: {commit_hash}")
```

### ブランチ操作

```python
# ブランチ作成・切り替え
git_service.create_branch("feature/new-functionality")

# 作業...
git_service.add_files(["new_feature.py"])
git_service.commit("Add new functionality")

# メインブランチに戻る
git_service.switch_branch("main")

# ブランチリスト確認
branches = git_service.get_branches()
for branch in branches:
    marker = " * " if branch.current else "   "
    print(f"{marker}{branch.name}")
```

### リモート操作との組み合わせ

```python
# リモートアダプター
remote_adapter = RemoteGitAdapter(git_service, config)

# 開発ワークフロー
git_service.create_branch("feature/authentication")
git_service.add_files(["auth.py", "tests/test_auth.py"])
git_service.commit("Implement user authentication")

# リモートにプッシュ
success = remote_adapter.push_to_remote("feature/authentication")
if success:
    print("Changes pushed to remote")
```

## エラーハンドリング

```python
class GitError(Exception):
    """Git操作エラーのベースクラス"""
    pass

class GitCommandError(GitError):
    """Gitコマンドエラー"""

    def __init__(self, command: str, return_code: int, stderr: str):
        self.command = command
        self.return_code = return_code
        self.stderr = stderr
        super().__init__(f"Git command '{command}' failed with code {return_code}: {stderr}")

class GitRepositoryError(GitError):
    """リポジトリエラー"""
    pass

class GitConfigurationError(GitError):
    """設定エラー"""
    pass

def handle_git_operation(operation: Callable) -> Any:
    """Git操作のエラーハンドリング装飾子"""
    def wrapper(*args, **kwargs):
        try:
            return operation(*args, **kwargs)
        except subprocess.CalledProcessError as e:
            raise GitCommandError(
                command=' '.join(e.cmd) if e.cmd else 'unknown',
                return_code=e.returncode,
                stderr=e.stderr or str(e)
            )
        except FileNotFoundError as e:
            raise GitRepositoryError(f"Repository not found: {e}")
        except PermissionError as e:
            raise GitRepositoryError(f"Permission denied: {e}")
        except Exception as e:
            raise GitError(f"Unexpected error: {e}")

    return wrapper
```

## テスト観点

### ユニットテスト
- 各Git操作の正確性
- コマンド生成の正確性
- エラーハンドリングの網羅性
- ステータス解析の精度

### 統合テスト
- 実際のGitリポジトリでの動作
- ファイルシステムとの連携
- リモートリポジトリとの連携
- 複雑なワークフローのテスト

### モックテスト
- CommandExecutorのモック化
- FileSystemAdapterのモック化
- エラー状況の再現

## 品質基準

### コード品質
- 循環的複雑度: 10以下
- テストカバレッジ: 90%以上
- 型安全性: 100%

### パフォーマンス
- Git コマンド実行: 3秒以内
- ステータス取得: 1秒以内
- ブランチリスト取得: 1秒以内

### 信頼性
- 操作失敗時の状態保持
- 部分失敗時の適切なロールバック
- 同時操作の競合回避
