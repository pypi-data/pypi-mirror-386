# SPEC-GENERAL-005: 強化Gitサービス仕様書

## 概要
強化GitサービスはGitリポジトリ操作の高度な機能を提供するアダプターサービスです。基本的なGit操作に加えて、自動コミット、インテリジェントなマージ、ブランチ管理戦略、品質ゲートとの統合を担当します。

## クラス設計

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Set, Union, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import subprocess
import re

class GitOperationType(Enum):
    """Git操作タイプ"""
    COMMIT = "commit"
    MERGE = "merge"
    REBASE = "rebase"
    CHERRY_PICK = "cherry_pick"
    RESET = "reset"
    STASH = "stash"

class BranchStrategy(Enum):
    """ブランチ戦略"""
    GIT_FLOW = "git_flow"
    GITHUB_FLOW = "github_flow"
    FEATURE_BRANCH = "feature_branch"
    TRUNK_BASED = "trunk_based"

@dataclass
class CommitTemplate:
    """コミットテンプレート"""
    type: str  # feat, fix, docs, style, refactor, test, chore
    scope: Optional[str] = None
    subject: str = ""
    body: Optional[str] = None
    footer: Optional[str] = None
    breaking_change: bool = False

@dataclass
class GitContext:
    """Git実行コンテキスト"""
    repository_path: str
    current_branch: str
    working_directory: str
    user_name: Optional[str] = None
    user_email: Optional[str] = None

@dataclass
class QualityGateResult:
    """品質ゲート結果"""
    passed: bool
    score: float
    checks: Dict[str, bool]
    warnings: List[str]
    errors: List[str]

class IEnhancedGitService(ABC):
    """強化Gitサービスインターフェース"""

    @abstractmethod
    def intelligent_commit(
        self,
        template: CommitTemplate,
        files: Optional[List[str]] = None,
        run_quality_gate: bool = True
    ) -> GitOperationResult:
        """インテリジェントコミット"""
        pass

    @abstractmethod
    def auto_merge_with_strategy(
        self,
        source_branch: str,
        target_branch: str,
        strategy: str = "smart"
    ) -> GitOperationResult:
        """戦略的自動マージ"""
        pass

    @abstractmethod
    def create_feature_branch(
        self,
        feature_name: str,
        base_branch: Optional[str] = None
    ) -> GitOperationResult:
        """フィーチャーブランチ作成"""
        pass

@dataclass
class GitOperationResult:
    """Git操作結果"""
    success: bool
    operation: GitOperationType
    commit_hash: Optional[str] = None
    branch_name: Optional[str] = None
    message: str = ""
    warnings: List[str] = None
    quality_gate_result: Optional[QualityGateResult] = None

class EnhancedGitService(IEnhancedGitService):
    """強化Gitサービス実装"""

    def __init__(
        self,
        git_adapter: IGitAdapter,
        quality_gate_service: IQualityGateService,
        commit_analyzer: ICommitAnalyzer,
        branch_manager: IBranchManager,
        conflict_resolver: IConflictResolver
    ):
        self._git = git_adapter
        self._quality_gate = quality_gate_service
        self._analyzer = commit_analyzer
        self._branch_manager = branch_manager
        self._conflict_resolver = conflict_resolver
```

## データ構造

### インターフェース定義

```python
class IGitAdapter(ABC):
    """Git基底アダプターインターフェース"""

    @abstractmethod
    def execute_command(self, command: List[str], cwd: Optional[str] = None) -> subprocess.CompletedProcess:
        """Gitコマンドを実行"""
        pass

    @abstractmethod
    def get_status(self) -> GitStatus:
        """Gitステータスを取得"""
        pass

    @abstractmethod
    def get_current_branch(self) -> str:
        """現在のブランチを取得"""
        pass

class IQualityGateService(ABC):
    """品質ゲートサービスインターフェース"""

    @abstractmethod
    def run_pre_commit_checks(self, files: List[str]) -> QualityGateResult:
        """コミット前品質チェック"""
        pass

    @abstractmethod
    def run_pre_merge_checks(self, source: str, target: str) -> QualityGateResult:
        """マージ前品質チェック"""
        pass

class ICommitAnalyzer(ABC):
    """コミット分析サービスインターフェース"""

    @abstractmethod
    def analyze_changes(self, files: List[str]) -> ChangeAnalysis:
        """変更内容を分析"""
        pass

    @abstractmethod
    def suggest_commit_message(self, changes: ChangeAnalysis) -> CommitTemplate:
        """コミットメッセージを提案"""
        pass

    @abstractmethod
    def detect_breaking_changes(self, changes: ChangeAnalysis) -> bool:
        """破壊的変更を検出"""
        pass

class IBranchManager(ABC):
    """ブランチ管理インターフェース"""

    @abstractmethod
    def create_branch(self, name: str, base: Optional[str] = None) -> bool:
        """ブランチを作成"""
        pass

    @abstractmethod
    def get_branch_strategy(self) -> BranchStrategy:
        """ブランチ戦略を取得"""
        pass

    @abstractmethod
    def validate_branch_name(self, name: str) -> ValidationResult:
        """ブランチ名を検証"""
        pass

class IConflictResolver(ABC):
    """競合解決インターフェース"""

    @abstractmethod
    def detect_conflicts(self, source: str, target: str) -> List[ConflictInfo]:
        """競合を検出"""
        pass

    @abstractmethod
    def suggest_resolution(self, conflict: ConflictInfo) -> ResolutionSuggestion:
        """解決案を提案"""
        pass
```

### データ型定義

```python
@dataclass
class GitStatus:
    """Gitステータス"""
    modified: List[str]
    added: List[str]
    deleted: List[str]
    renamed: List[str]
    untracked: List[str]
    staged: List[str]

@dataclass
class ChangeAnalysis:
    """変更分析結果"""
    change_type: str  # feature, bugfix, refactor, docs, etc.
    affected_components: List[str]
    complexity_score: float
    risk_level: str  # low, medium, high
    test_coverage_impact: float

@dataclass
class ConflictInfo:
    """競合情報"""
    file_path: str
    conflict_type: str  # content, binary, rename, etc.
    source_content: str
    target_content: str
    line_numbers: List[int]

@dataclass
class ResolutionSuggestion:
    """解決提案"""
    strategy: str  # auto, manual, skip
    resolved_content: Optional[str]
    confidence: float
    explanation: str
```

## パブリックメソッド

### EnhancedGitService

```python
def intelligent_commit(
    self,
    template: CommitTemplate,
    files: Optional[List[str]] = None,
    run_quality_gate: bool = True
) -> GitOperationResult:
    """
    インテリジェントコミット実行

    Args:
        template: コミットテンプレート
        files: コミット対象ファイル（Noneの場合は全変更ファイル）
        run_quality_gate: 品質ゲート実行有無

    Returns:
        GitOperationResult: 実行結果
    """
    try:
        # ファイル選択
        if files is None:
            status = self._git.get_status()
            files = status.modified + status.added + status.deleted

        if not files:
            return GitOperationResult(
                success=False,
                operation=GitOperationType.COMMIT,
                message="コミット対象のファイルがありません"
            )

        # 品質ゲート実行
        quality_result = None
        if run_quality_gate:
            quality_result = self._quality_gate.run_pre_commit_checks(files)
            if not quality_result.passed:
                return GitOperationResult(
                    success=False,
                    operation=GitOperationType.COMMIT,
                    message="品質ゲートを通過しませんでした",
                    quality_gate_result=quality_result
                )

        # 変更分析
        changes = self._analyzer.analyze_changes(files)

        # コミットメッセージ生成
        if not template.subject:
            suggested = self._analyzer.suggest_commit_message(changes)
            template = self._merge_templates(template, suggested)

        # 破壊的変更検出
        if self._analyzer.detect_breaking_changes(changes):
            template.breaking_change = True

        # コミット実行
        commit_message = self._format_commit_message(template)

        # ファイルをステージング
        for file in files:
            self._git.execute_command(['add', file])

        # コミット実行
        result = self._git.execute_command(['commit', '-m', commit_message])

        if result.returncode == 0:
            # コミットハッシュを取得
            hash_result = self._git.execute_command(['rev-parse', 'HEAD'])
            commit_hash = hash_result.stdout.decode().strip()

            return GitOperationResult(
                success=True,
                operation=GitOperationType.COMMIT,
                commit_hash=commit_hash,
                message=f"コミットが完了しました: {commit_hash[:8]}",
                quality_gate_result=quality_result
            )
        else:
            return GitOperationResult(
                success=False,
                operation=GitOperationType.COMMIT,
                message=f"コミットに失敗しました: {result.stderr.decode()}"
            )

    except Exception as e:
        return GitOperationResult(
            success=False,
            operation=GitOperationType.COMMIT,
            message=f"コミット処理中にエラーが発生しました: {str(e)}"
        )

def auto_merge_with_strategy(
    self,
    source_branch: str,
    target_branch: str,
    strategy: str = "smart"
) -> GitOperationResult:
    """
    戦略的自動マージ実行

    Args:
        source_branch: マージ元ブランチ
        target_branch: マージ先ブランチ
        strategy: マージ戦略 (smart, fast-forward, no-ff, rebase)

    Returns:
        GitOperationResult: 実行結果
    """
    try:
        # 現在のブランチを保存
        current_branch = self._git.get_current_branch()

        # 品質ゲート実行
        quality_result = self._quality_gate.run_pre_merge_checks(source_branch, target_branch)
        if not quality_result.passed:
            return GitOperationResult(
                success=False,
                operation=GitOperationType.MERGE,
                message="マージ前品質チェックに失敗しました",
                quality_gate_result=quality_result
            )

        # 競合検出
        conflicts = self._conflict_resolver.detect_conflicts(source_branch, target_branch)

        # ターゲットブランチに切り替え
        self._git.execute_command(['checkout', target_branch])

        # マージ戦略に応じた処理
        if strategy == "smart":
            merge_result = self._execute_smart_merge(source_branch, conflicts)
        elif strategy == "fast-forward":
            merge_result = self._execute_ff_merge(source_branch)
        elif strategy == "no-ff":
            merge_result = self._execute_no_ff_merge(source_branch)
        elif strategy == "rebase":
            merge_result = self._execute_rebase_merge(source_branch)
        else:
            raise ValueError(f"Unknown merge strategy: {strategy}")

        # 元のブランチに戻る
        if current_branch != target_branch:
            self._git.execute_command(['checkout', current_branch])

        return merge_result

    except Exception as e:
        # 元のブランチに戻る（エラー時）
        try:
            self._git.execute_command(['checkout', current_branch])
        except:
            pass

        return GitOperationResult(
            success=False,
            operation=GitOperationType.MERGE,
            message=f"マージ処理中にエラーが発生しました: {str(e)}"
        )

def create_feature_branch(
    self,
    feature_name: str,
    base_branch: Optional[str] = None
) -> GitOperationResult:
    """
    フィーチャーブランチ作成

    Args:
        feature_name: フィーチャー名
        base_branch: ベースブランチ（Noneの場合は現在のブランチ）

    Returns:
        GitOperationResult: 実行結果
    """
    try:
        # ブランチ名を検証・正規化
        normalized_name = self._normalize_branch_name(feature_name)
        validation = self._branch_manager.validate_branch_name(normalized_name)

        if not validation.is_valid:
            return GitOperationResult(
                success=False,
                operation=GitOperationType.COMMIT,  # ブランチ作成用の操作タイプがないため
                message=f"ブランチ名が無効です: {', '.join(validation.errors)}"
            )

        # ベースブランチの決定
        if base_branch is None:
            base_branch = self._git.get_current_branch()

        # ブランチ作成
        branch_created = self._branch_manager.create_branch(normalized_name, base_branch)

        if branch_created:
            # ブランチに切り替え
            self._git.execute_command(['checkout', normalized_name])

            return GitOperationResult(
                success=True,
                operation=GitOperationType.COMMIT,
                branch_name=normalized_name,
                message=f"フィーチャーブランチ '{normalized_name}' を作成しました"
            )
        else:
            return GitOperationResult(
                success=False,
                operation=GitOperationType.COMMIT,
                message=f"ブランチ '{normalized_name}' の作成に失敗しました"
            )

    except Exception as e:
        return GitOperationResult(
            success=False,
            operation=GitOperationType.COMMIT,
            message=f"フィーチャーブランチ作成中にエラーが発生しました: {str(e)}"
        )
```

## プライベートメソッド

```python
def _format_commit_message(self, template: CommitTemplate) -> str:
    """コミットメッセージをフォーマット"""
    parts = []

    # タイプとスコープ
    if template.scope:
        header = f"{template.type}({template.scope}): {template.subject}"
    else:
        header = f"{template.type}: {template.subject}"

    # 破壊的変更の場合は!を追加
    if template.breaking_change:
        if template.scope:
            header = f"{template.type}({template.scope})!: {template.subject}"
        else:
            header = f"{template.type}!: {template.subject}"

    parts.append(header)

    # ボディ
    if template.body:
        parts.append("")  # 空行
        parts.append(template.body)

    # フッター
    if template.footer:
        parts.append("")  # 空行
        parts.append(template.footer)

    return "\n".join(parts)

def _execute_smart_merge(self, source_branch: str, conflicts: List[ConflictInfo]) -> GitOperationResult:
    """スマートマージを実行"""
    if not conflicts:
        # 競合なし：fast-forwardを試行
        result = self._git.execute_command(['merge', '--ff-only', source_branch])
        if result.returncode == 0:
            return GitOperationResult(
                success=True,
                operation=GitOperationType.MERGE,
                message=f"Fast-forward マージが完了しました"
            )

    # 通常のマージ
    result = self._git.execute_command(['merge', '--no-ff', source_branch])

    if result.returncode == 0:
        return GitOperationResult(
            success=True,
            operation=GitOperationType.MERGE,
            message=f"マージが完了しました"
        )
    else:
        # 競合解決の試行
        return self._attempt_conflict_resolution(conflicts)

def _attempt_conflict_resolution(self, conflicts: List[ConflictInfo]) -> GitOperationResult:
    """競合解決を試行"""
    resolved_count = 0

    for conflict in conflicts:
        suggestion = self._conflict_resolver.suggest_resolution(conflict)

        if suggestion.strategy == "auto" and suggestion.confidence > 0.8:
            # 自動解決可能
            self._apply_resolution(conflict, suggestion)
            resolved_count += 1

    if resolved_count == len(conflicts):
        # 全競合を自動解決
        result = self._git.execute_command(['commit', '--no-edit'])
        if result.returncode == 0:
            return GitOperationResult(
                success=True,
                operation=GitOperationType.MERGE,
                message=f"自動競合解決によりマージが完了しました ({resolved_count}件の競合を解決)"
            )

    # 手動解決が必要
    return GitOperationResult(
        success=False,
        operation=GitOperationType.MERGE,
        message=f"手動解決が必要な競合があります ({len(conflicts) - resolved_count}件)",
        warnings=[f"競合ファイル: {c.file_path}" for c in conflicts[resolved_count:]]
    )

def _normalize_branch_name(self, name: str) -> str:
    """ブランチ名を正規化"""
    # 小文字に変換
    normalized = name.lower()

    # スペースをハイフンに変換
    normalized = re.sub(r'\s+', '-', normalized)

    # 不正な文字を除去
    normalized = re.sub(r'[^a-z0-9\-_/]', '', normalized)

    # 連続するハイフンを単一に
    normalized = re.sub(r'-+', '-', normalized)

    # 先頭・末尾のハイフンを除去
    normalized = normalized.strip('-')

    # ブランチ戦略に応じたプレフィックス追加
    strategy = self._branch_manager.get_branch_strategy()
    if strategy == BranchStrategy.GIT_FLOW:
        if not normalized.startswith(('feature/', 'hotfix/', 'release/')):
            normalized = f"feature/{normalized}"

    return normalized
```

## アダプターパターン実装

### Git低レベル操作アダプター

```python
class GitCommandAdapter(IGitAdapter):
    """Gitコマンドアダプター"""

    def __init__(self, repository_path: str):
        self._repo_path = repository_path

    def execute_command(self, command: List[str], cwd: Optional[str] = None) -> subprocess.CompletedProcess:
        """Gitコマンドを実行"""
        full_command = ['git'] + command
        work_dir = cwd or self._repo_path

        return subprocess.run(
            full_command,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

    def get_status(self) -> GitStatus:
        """Gitステータスを取得"""
        result = self.execute_command(['status', '--porcelain'])

        if result.returncode != 0:
            raise GitError(f"Failed to get git status: {result.stderr}")

        return self._parse_status_output(result.stdout)

    def _parse_status_output(self, output: str) -> GitStatus:
        """git statusの出力を解析"""
        modified = []
        added = []
        deleted = []
        renamed = []
        untracked = []
        staged = []

        for line in output.strip().split('\n'):
            if not line:
                continue

            status_code = line[:2]
            file_path = line[3:]

            if status_code[0] in ['A', 'M', 'D', 'R', 'C']:
                staged.append(file_path)

            if status_code[1] == 'M':
                modified.append(file_path)
            elif status_code[1] == 'A' or status_code[0] == 'A':
                added.append(file_path)
            elif status_code[1] == 'D' or status_code[0] == 'D':
                deleted.append(file_path)
            elif status_code[0] == 'R':
                renamed.append(file_path)
            elif status_code == '??':
                untracked.append(file_path)

        return GitStatus(
            modified=modified,
            added=added,
            deleted=deleted,
            renamed=renamed,
            untracked=untracked,
            staged=staged
        )

class LibGit2Adapter(IGitAdapter):
    """libgit2ベースのアダプター"""

    def __init__(self, repository_path: str):
        import pygit2
        self._repo = pygit2.Repository(repository_path)

    def get_status(self) -> GitStatus:
        """pygit2を使ってステータス取得"""
        status_flags = self._repo.status()

        modified = []
        added = []
        deleted = []
        untracked = []
        staged = []

        for filepath, flags in status_flags.items():
            if flags & pygit2.GIT_STATUS_INDEX_MODIFIED:
                staged.append(filepath)
                modified.append(filepath)
            elif flags & pygit2.GIT_STATUS_INDEX_NEW:
                staged.append(filepath)
                added.append(filepath)
            elif flags & pygit2.GIT_STATUS_INDEX_DELETED:
                staged.append(filepath)
                deleted.append(filepath)
            elif flags & pygit2.GIT_STATUS_WT_NEW:
                untracked.append(filepath)

        return GitStatus(
            modified=modified,
            added=added,
            deleted=deleted,
            renamed=[],
            untracked=untracked,
            staged=staged
        )
```

### 品質ゲート統合アダプター

```python
class QualityGateAdapter(IQualityGateService):
    """品質ゲート統合アダプター"""

    def __init__(
        self,
        quality_checkers: List[IQualityChecker],
        test_runner: ITestRunner,
        linter: ILinter
    ):
        self._checkers = quality_checkers
        self._test_runner = test_runner
        self._linter = linter

    def run_pre_commit_checks(self, files: List[str]) -> QualityGateResult:
        """コミット前品質チェック"""
        checks = {}
        warnings = []
        errors = []
        total_score = 0.0

        # Lint チェック
        lint_result = self._linter.check_files(files)
        checks['lint'] = lint_result.passed
        if not lint_result.passed:
            errors.extend(lint_result.errors)
        warnings.extend(lint_result.warnings)
        total_score += lint_result.score * 0.3

        # 品質チェッカー実行
        for checker in self._checkers:
            result = checker.check_files(files)
            checks[checker.name] = result.passed
            if not result.passed:
                errors.extend(result.errors)
            warnings.extend(result.warnings)
            total_score += result.score * (0.7 / len(self._checkers))

        # テスト実行（変更されたファイルに関連するテストのみ）
        if self._should_run_tests(files):
            test_result = self._test_runner.run_affected_tests(files)
            checks['tests'] = test_result.passed
            if not test_result.passed:
                errors.extend([f"Test failed: {failure}" for failure in test_result.failures])

        passed = all(checks.values()) and len(errors) == 0

        return QualityGateResult(
            passed=passed,
            score=total_score,
            checks=checks,
            warnings=warnings,
            errors=errors
        )

    def _should_run_tests(self, files: List[str]) -> bool:
        """テスト実行が必要かを判定"""
        # Python ファイルが変更された場合はテスト実行
        return any(f.endswith('.py') for f in files)
```

## 依存関係

```python
from domain.services import IQualityService
from domain.value_objects import CommitInfo, BranchInfo
from infrastructure.services import IGitService, IFileSystemService
from application.use_cases import QualityCheckUseCase
```

## 設計原則遵守

### アダプターパターン
- **外部システム分離**: Git操作は複数のアダプター実装で抽象化
- **戦略パターン統合**: マージ戦略、ブランチ戦略を動的選択
- **複合パターン**: 複数のサービスを協調動作

### 依存性逆転原則
- **抽象化への依存**: 具体的なGit実装に依存しない
- **注入可能性**: 全ての依存関係は外部から注入
- **テスタビリティ**: モックオブジェクトでテスト可能

## 使用例

### 基本的な使用

```python
# サービス設定
git_adapter = GitCommandAdapter("/path/to/repo")
quality_gate = QualityGateAdapter(checkers, test_runner, linter)
analyzer = CommitAnalyzer()
branch_manager = BranchManager(BranchStrategy.GIT_FLOW)
conflict_resolver = ConflictResolver()

enhanced_git = EnhancedGitService(
    git_adapter,
    quality_gate,
    analyzer,
    branch_manager,
    conflict_resolver
)

# インテリジェントコミット
template = CommitTemplate(
    type="feat",
    scope="episode",
    subject="新エピソード作成機能を追加"
)

result = enhanced_git.intelligent_commit(template, run_quality_gate=True)

if result.success:
    print(f"コミット完了: {result.commit_hash}")
else:
    print(f"コミット失敗: {result.message}")
```

### フィーチャー開発ワークフロー

```python
# フィーチャーブランチ作成
branch_result = enhanced_git.create_feature_branch("ユーザー認証機能")

if branch_result.success:
    print(f"ブランチ作成: {branch_result.branch_name}")

    # 開発作業...

    # 定期的なコミット
    for i in range(3):
        commit_result = enhanced_git.intelligent_commit(
            CommitTemplate(
                type="feat",
                scope="auth",
                subject=f"認証機能実装 Part {i+1}"
            )
        )

        if not commit_result.success:
            print(f"品質チェック失敗: {commit_result.quality_gate_result.errors}")
            break

    # 開発完了後のマージ
    merge_result = enhanced_git.auto_merge_with_strategy(
        branch_result.branch_name,
        "develop",
        "smart"
    )

    if merge_result.success:
        print("フィーチャーマージ完了")
    else:
        print(f"マージ失敗: {merge_result.message}")
```

## エラーハンドリング

```python
class GitError(Exception):
    """Git関連エラーのベースクラス"""
    pass

class GitCommandError(GitError):
    """Gitコマンド実行エラー"""

    def __init__(self, command: List[str], return_code: int, stderr: str):
        self.command = command
        self.return_code = return_code
        self.stderr = stderr
        super().__init__(f"Git command failed: {' '.join(command)} (exit: {return_code})")

class ConflictResolutionError(GitError):
    """競合解決エラー"""

    def __init__(self, conflicts: List[ConflictInfo]):
        self.conflicts = conflicts
        super().__init__(f"Cannot resolve {len(conflicts)} conflicts automatically")

class QualityGateError(GitError):
    """品質ゲートエラー"""

    def __init__(self, result: QualityGateResult):
        self.result = result
        super().__init__(f"Quality gate failed: score {result.score:.1f}")

def handle_git_error(error: GitError) -> GitOperationResult:
    """Git エラーを適切にハンドリング"""
    if isinstance(error, ConflictResolutionError):
        return GitOperationResult(
            success=False,
            operation=GitOperationType.MERGE,
            message="競合の手動解決が必要です",
            warnings=[f"競合ファイル: {c.file_path}" for c in error.conflicts]
        )
    elif isinstance(error, QualityGateError):
        return GitOperationResult(
            success=False,
            operation=GitOperationType.COMMIT,
            message="品質基準を満たしていません",
            quality_gate_result=error.result
        )
    else:
        return GitOperationResult(
            success=False,
            operation=GitOperationType.COMMIT,
            message=str(error)
        )
```

## テスト観点

### ユニットテスト
- Git コマンド実行の正確性
- 品質ゲート連携
- 競合解決ロジック
- ブランチ管理戦略

### 統合テスト
- 実際のGitリポジトリでの動作
- 品質チェックシステムとの連携
- エラー状況での復旧処理
- パフォーマンス測定

### E2Eテスト
- 完全な開発ワークフロー
- 複数開発者での協調動作
- 大規模リポジトリでの動作
- CI/CD パイプライン統合

## 品質基準

### コード品質
- 循環的複雑度: 12以下
- テストカバレッジ: 85%以上
- 型安全性: 100%

### パフォーマンス
- Git コマンド実行: 5秒以内
- 品質チェック: 30秒以内
- 競合検出: 1秒以内

### 信頼性
- 操作のアトミック性保証
- 失敗時の状態復旧
- データ損失防止
