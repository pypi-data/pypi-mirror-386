# SPEC-GENERAL-013: GitHookRepository 仕様書

## 概要

`GitHookRepository`は、Git hooksの設定と管理を担当するリポジトリです。pre-commit、post-commit、pre-pushなどのGitフックを統合的に管理し、品質保証プロセスを自動化します。

## クラス設計

```python
class GitHookRepository:
    """Gitフック管理リポジトリ"""

    def __init__(self, project_root: Path, hooks_dir: Path):
        """
        Args:
            project_root: プロジェクトルートパス
            hooks_dir: Gitフックスクリプト格納ディレクトリ
        """
        self._project_root = project_root
        self._hooks_dir = hooks_dir
        self._git_hooks_path = project_root / ".git" / "hooks"
        self._config_cache: Dict[str, HookConfiguration] = {}
```

## データ構造

### インターフェース

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Callable
from pathlib import Path
from datetime import datetime

class GitHookRepositoryInterface(ABC):
    """Gitフックリポジトリインターフェース"""

    @abstractmethod
    def find_hook_config(self, hook_type: HookType) -> Optional[HookConfiguration]:
        """フック設定を取得"""
        pass

    @abstractmethod
    def find_all_hook_configs(self) -> List[HookConfiguration]:
        """すべてのフック設定を取得"""
        pass

    @abstractmethod
    def install_hook(self, hook_type: HookType, config: HookConfiguration) -> None:
        """フックをインストール"""
        pass

    @abstractmethod
    def uninstall_hook(self, hook_type: HookType) -> None:
        """フックをアンインストール"""
        pass

    @abstractmethod
    def execute_hook(self, hook_type: HookType, context: HookContext) -> HookResult:
        """フックを実行"""
        pass

    @abstractmethod
    def validate_hook_script(self, script_path: Path) -> List[str]:
        """フックスクリプトを検証"""
        pass

    @abstractmethod
    def get_hook_history(self, hook_type: HookType) -> List[HookExecutionRecord]:
        """フック実行履歴を取得"""
        pass
```

### データモデル

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class HookType(Enum):
    """Gitフックタイプ"""
    PRE_COMMIT = "pre-commit"
    POST_COMMIT = "post-commit"
    PRE_PUSH = "pre-push"
    COMMIT_MSG = "commit-msg"
    PRE_REBASE = "pre-rebase"
    POST_MERGE = "post-merge"

class HookStatus(Enum):
    """フック実行ステータス"""
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SKIPPED = "skipped"

@dataclass
class HookConfiguration:
    """フック設定"""
    hook_type: HookType
    enabled: bool
    script_path: Path
    description: str
    required_tools: List[str]
    environment_vars: Dict[str, str]
    timeout_seconds: int = 300
    fail_fast: bool = True
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    actions: List[HookAction] = field(default_factory=list)

@dataclass
class HookAction:
    """フックアクション"""
    name: str
    command: str
    args: List[str]
    working_dir: Optional[Path] = None
    continue_on_error: bool = False
    output_format: str = "console"

@dataclass
class HookContext:
    """フック実行コンテキスト"""
    hook_type: HookType
    triggered_at: datetime
    git_branch: str
    git_commit: Optional[str]
    changed_files: List[Path]
    environment: Dict[str, str]
    user_name: str
    user_email: str

@dataclass
class HookResult:
    """フック実行結果"""
    hook_type: HookType
    status: HookStatus
    executed_at: datetime
    duration_seconds: float
    actions_results: List[ActionResult]
    messages: List[str]
    modified_files: List[Path] = field(default_factory=list)

@dataclass
class ActionResult:
    """アクション実行結果"""
    action_name: str
    status: HookStatus
    output: str
    error: Optional[str] = None
    duration_seconds: float = 0.0

@dataclass
class HookExecutionRecord:
    """フック実行記録"""
    hook_type: HookType
    executed_at: datetime
    status: HookStatus
    context: HookContext
    result: HookResult
    log_file: Optional[Path] = None
```

## パブリックメソッド

### フック設定管理

```python
def find_hook_config(self, hook_type: HookType) -> Optional[HookConfiguration]:
    """フック設定を取得"""
    if hook_type.value in self._config_cache:
        return self._config_cache[hook_type.value]

    config_path = self._hooks_dir / f"{hook_type.value}.yaml"
    if not config_path.exists():
        return None

    data = self._load_yaml(config_path)
    config = self._create_hook_config(hook_type, data)
    self._config_cache[hook_type.value] = config
    return config

def find_all_hook_configs(self) -> List[HookConfiguration]:
    """すべてのフック設定を取得"""
    configs = []
    for hook_type in HookType:
        config = self.find_hook_config(hook_type)
        if config:
            configs.append(config)
    return configs
```

### フックのインストール・アンインストール

```python
def install_hook(self, hook_type: HookType, config: HookConfiguration) -> None:
    """フックをインストール"""
    # スクリプトの検証
    errors = self.validate_hook_script(config.script_path)
    if errors:
        raise HookInstallationError(f"スクリプト検証エラー: {errors}")

    # 必要なツールの確認
    missing_tools = self._check_required_tools(config.required_tools)
    if missing_tools:
        raise HookInstallationError(f"必要なツールが不足: {missing_tools}")

    # フックスクリプトの生成
    hook_script = self._generate_hook_script(config)
    hook_path = self._git_hooks_path / hook_type.value

    # バックアップ作成
    if hook_path.exists():
        self._backup_existing_hook(hook_path)

    # フックのインストール
    hook_path.write_text(hook_script)
    hook_path.chmod(0o755)

    # 設定の保存
    self._save_hook_config(hook_type, config)

def uninstall_hook(self, hook_type: HookType) -> None:
    """フックをアンインストール"""
    hook_path = self._git_hooks_path / hook_type.value

    if hook_path.exists():
        # バックアップ作成
        self._backup_existing_hook(hook_path)
        # フック削除
        hook_path.unlink()

    # キャッシュクリア
    if hook_type.value in self._config_cache:
        del self._config_cache[hook_type.value]
```

### フック実行

```python
def execute_hook(self, hook_type: HookType, context: HookContext) -> HookResult:
    """フックを実行"""
    config = self.find_hook_config(hook_type)
    if not config or not config.enabled:
        return HookResult(
            hook_type=hook_type,
            status=HookStatus.SKIPPED,
            executed_at=datetime.now(),
            duration_seconds=0,
            actions_results=[],
            messages=["フックが無効化されています"]
        )

    # 実行条件の確認
    if not self._check_conditions(config.conditions, context):
        return HookResult(
            hook_type=hook_type,
            status=HookStatus.SKIPPED,
            executed_at=datetime.now(),
            duration_seconds=0,
            actions_results=[],
            messages=["実行条件を満たしていません"]
        )

    # アクションの実行
    start_time = datetime.now()
    action_results = []
    overall_status = HookStatus.SUCCESS

    for action in config.actions:
        result = self._execute_action(action, context)
        action_results.append(result)

        if result.status == HookStatus.ERROR and config.fail_fast:
            overall_status = HookStatus.ERROR
            break
        elif result.status == HookStatus.WARNING:
            overall_status = HookStatus.WARNING

    # 結果の作成
    duration = (datetime.now() - start_time).total_seconds()
    hook_result = HookResult(
        hook_type=hook_type,
        status=overall_status,
        executed_at=start_time,
        duration_seconds=duration,
        actions_results=action_results,
        messages=self._collect_messages(action_results)
    )

    # 実行記録の保存
    self._save_execution_record(hook_type, context, hook_result)

    return hook_result
```

### 検証と履歴

```python
def validate_hook_script(self, script_path: Path) -> List[str]:
    """フックスクリプトを検証"""
    errors = []

    if not script_path.exists():
        errors.append(f"スクリプトが存在しません: {script_path}")
        return errors

    # 実行権限の確認
    if not os.access(script_path, os.X_OK):
        errors.append("スクリプトに実行権限がありません")

    # シンタックスチェック（Pythonスクリプトの場合）
    if script_path.suffix == '.py':
        try:
            compile(script_path.read_text(), script_path, 'exec')
        except SyntaxError as e:
            errors.append(f"Pythonシンタックスエラー: {e}")

    # セキュリティチェック
    content = script_path.read_text()
    dangerous_patterns = ['rm -rf', 'eval(', 'exec(', '__import__']
    for pattern in dangerous_patterns:
        if pattern in content:
            errors.append(f"危険なパターンが検出されました: {pattern}")

    return errors

def get_hook_history(self, hook_type: HookType) -> List[HookExecutionRecord]:
    """フック実行履歴を取得"""
    history_file = self._hooks_dir / "history" / f"{hook_type.value}_history.yaml"

    if not history_file.exists():
        return []

    data = self._load_yaml(history_file)
    records = []

    for record_data in data.get('records', []):
        record = self._create_execution_record(record_data)
        records.append(record)

    # 新しい順にソート
    records.sort(key=lambda r: r.executed_at, reverse=True)
    return records
```

## プライベートメソッド

### フックスクリプト生成

```python
def _generate_hook_script(self, config: HookConfiguration) -> str:
    """フックスクリプトを生成"""
    template = '''#!/usr/bin/env python3
# Auto-generated Git hook script
# Hook type: {hook_type}
# Generated at: {timestamp}

import sys
import os
import subprocess
from pathlib import Path

# Add project scripts to path
sys.path.insert(0, '{scripts_path}')

from infrastructure.repositories.git_hook_repository import GitHookRepository, HookContext, HookType
from datetime import datetime

# Initialize repository
repo = GitHookRepository(
    project_root=Path('{project_root}'),
    hooks_dir=Path('{hooks_dir}')
)

# Create context
context = HookContext(
    hook_type=HookType.{hook_type_enum},
    triggered_at=datetime.now(),
    git_branch=subprocess.check_output(['git', 'branch', '--show-current']).decode().strip(),
    git_commit=os.environ.get('GIT_COMMIT'),
    changed_files=[Path(f) for f in subprocess.check_output(['git', 'diff', '--cached', '--name-only']).decode().strip().split('\\n') if f],
    environment=dict(os.environ),
    user_name=subprocess.check_output(['git', 'config', 'user.name']).decode().strip(),
    user_email=subprocess.check_output(['git', 'config', 'user.email']).decode().strip()
)

# Execute hook
result = repo.execute_hook(HookType.{hook_type_enum}, context)

# Exit with appropriate code
if result.status.value == 'error':
    sys.exit(1)
elif result.status.value == 'warning':
    sys.exit(0)  # Allow commit with warnings
else:
    sys.exit(0)
'''

    return template.format(
        hook_type=config.hook_type.value,
        hook_type_enum=config.hook_type.name,
        timestamp=datetime.now().isoformat(),
        scripts_path=str(self._project_root / "00_ガイド" / "scripts"),
        project_root=str(self._project_root),
        hooks_dir=str(self._hooks_dir)
    )
```

### アクション実行

```python
def _execute_action(self, action: HookAction, context: HookContext) -> ActionResult:
    """アクションを実行"""
    start_time = datetime.now()

    try:
        # コマンドの準備
        cmd = self._prepare_command(action, context)
        env = {**context.environment, **action.environment_vars}

        # 実行
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=action.working_dir or self._project_root,
            env=env,
            timeout=300  # 5分のタイムアウト
        )

        duration = (datetime.now() - start_time).total_seconds()

        if result.returncode == 0:
            status = HookStatus.SUCCESS
        elif action.continue_on_error:
            status = HookStatus.WARNING
        else:
            status = HookStatus.ERROR

        return ActionResult(
            action_name=action.name,
            status=status,
            output=result.stdout,
            error=result.stderr if result.stderr else None,
            duration_seconds=duration
        )

    except subprocess.TimeoutExpired:
        return ActionResult(
            action_name=action.name,
            status=HookStatus.ERROR,
            output="",
            error="アクションがタイムアウトしました",
            duration_seconds=300
        )
    except Exception as e:
        return ActionResult(
            action_name=action.name,
            status=HookStatus.ERROR,
            output="",
            error=str(e),
            duration_seconds=(datetime.now() - start_time).total_seconds()
        )
```

### ユーティリティ

```python
def _check_required_tools(self, tools: List[str]) -> List[str]:
    """必要なツールの存在確認"""
    missing = []
    for tool in tools:
        if not shutil.which(tool):
            missing.append(tool)
    return missing

def _check_conditions(self, conditions: List[Dict[str, Any]], context: HookContext) -> bool:
    """実行条件をチェック"""
    for condition in conditions:
        cond_type = condition.get('type')

        if cond_type == 'branch':
            pattern = condition.get('pattern')
            if not re.match(pattern, context.git_branch):
                return False

        elif cond_type == 'files':
            patterns = condition.get('patterns', [])
            if not any(self._match_file_pattern(f, patterns) for f in context.changed_files):
                return False

        elif cond_type == 'environment':
            var_name = condition.get('variable')
            expected_value = condition.get('value')
            if context.environment.get(var_name) != expected_value:
                return False

    return True

def _save_execution_record(self, hook_type: HookType, context: HookContext, result: HookResult) -> None:
    """実行記録を保存"""
    history_dir = self._hooks_dir / "history"
    history_dir.mkdir(exist_ok=True)

    history_file = history_dir / f"{hook_type.value}_history.yaml"

    # 既存の履歴を読み込み
    if history_file.exists():
        data = self._load_yaml(history_file)
    else:
        data = {'records': []}

    # 新しい記録を追加
    record = {
        'hook_type': hook_type.value,
        'executed_at': result.executed_at.isoformat(),
        'status': result.status.value,
        'duration_seconds': result.duration_seconds,
        'context': self._context_to_dict(context),
        'result': self._result_to_dict(result)
    }

    data['records'].append(record)

    # 最新100件のみ保持
    data['records'] = data['records'][-100:]

    # 保存
    self._save_yaml(history_file, data)
```

## 永続化仕様

### ファイル構造

```
00_ガイド/
├── hooks/
│   ├── configs/
│   │   ├── pre-commit.yaml
│   │   ├── post-commit.yaml
│   │   ├── pre-push.yaml
│   │   └── commit-msg.yaml
│   ├── scripts/
│   │   ├── quality_check.py
│   │   ├── test_runner.py
│   │   └── format_code.py
│   ├── history/
│   │   ├── pre-commit_history.yaml
│   │   └── pre-push_history.yaml
│   └── backups/
│       └── [timestamp]_[hook_type].bak
```

### YAMLフォーマット

#### フック設定
```yaml
hook_type: "pre-commit"
enabled: true
script_path: "hooks/scripts/quality_check.py"
description: "コミット前の品質チェック"

required_tools:
  - python3
  - pytest
  - mypy

environment_vars:
  QUALITY_THRESHOLD: "80"
  AUTO_FIX: "true"

timeout_seconds: 300
fail_fast: true

conditions:
  - type: "branch"
    pattern: "^(main|develop|feature/.*)$"
  - type: "files"
    patterns:
      - "*.py"
      - "*.md"

actions:
  - name: "品質チェック"
    command: "python"
    args:
      - "scripts/quality/integrated_quality_checker.py"
      - "--project"
      - "${PROJECT_NAME}"
    continue_on_error: false
    output_format: "console"

  - name: "テスト実行"
    command: "pytest"
    args:
      - "scripts/tests/"
      - "-v"
    continue_on_error: true
    output_format: "console"
```

## 依存関係

- `pathlib.Path`: ファイルパス操作
- `subprocess`: 外部コマンド実行
- `yaml`: YAML形式の読み書き
- `datetime`: タイムスタンプ管理
- `shutil`: ツールの存在確認
- `re`: パターンマッチング
- Domain層のエラークラス（HookError等）

## 設計原則遵守

### DDDの原則
- **レポジトリパターン**: Gitフックの管理詳細をドメイン層から隠蔽
- **集約**: フック設定と実行履歴の一貫性を保証
- **値オブジェクト**: フック設定を不変オブジェクトとして扱う

### リポジトリパターンの実装
- インターフェースと実装の分離
- フック管理の抽象化
- 実行履歴の永続化

## 使用例

```python
# リポジトリの初期化
hook_repo = GitHookRepository(
    project_root=Path("/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説"),
    hooks_dir=Path("/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド/hooks")
)

# pre-commitフックの設定
pre_commit_config = HookConfiguration(
    hook_type=HookType.PRE_COMMIT,
    enabled=True,
    script_path=Path("hooks/scripts/quality_check.py"),
    description="コミット前の品質チェック",
    required_tools=["python3", "pytest"],
    environment_vars={"QUALITY_THRESHOLD": "80"},
    actions=[
        HookAction(
            name="品質チェック",
            command="python",
            args=["scripts/quality/integrated_quality_checker.py", "--auto-fix"]
        ),
        HookAction(
            name="型チェック",
            command="mypy",
            args=["scripts/"],
            continue_on_error=True
        )
    ]
)

# フックのインストール
try:
    hook_repo.install_hook(HookType.PRE_COMMIT, pre_commit_config)
    print("pre-commitフックをインストールしました")
except HookInstallationError as e:
    print(f"インストールエラー: {e}")

# 手動でフックを実行
context = HookContext(
    hook_type=HookType.PRE_COMMIT,
    triggered_at=datetime.now(),
    git_branch="feature/new-episode",
    git_commit=None,
    changed_files=[
        Path("40_原稿/第001話_タイトル.md"),
        Path("scripts/quality/check_basic_style.py")
    ],
    environment=os.environ.copy(),
    user_name="山田太郎",
    user_email="yamada@example.com"
)

result = hook_repo.execute_hook(HookType.PRE_COMMIT, context)

# 結果の確認
print(f"ステータス: {result.status.value}")
print(f"実行時間: {result.duration_seconds}秒")
for action_result in result.actions_results:
    print(f"- {action_result.action_name}: {action_result.status.value}")
    if action_result.error:
        print(f"  エラー: {action_result.error}")

# 実行履歴の確認
history = hook_repo.get_hook_history(HookType.PRE_COMMIT)
print(f"過去の実行回数: {len(history)}")
for record in history[:5]:  # 最新5件
    print(f"- {record.executed_at}: {record.status.value}")

# フックの無効化
pre_commit_config.enabled = False
hook_repo.install_hook(HookType.PRE_COMMIT, pre_commit_config)

# フックのアンインストール
hook_repo.uninstall_hook(HookType.PRE_COMMIT)
```

## エラーハンドリング

```python
class HookError(Exception):
    """フックエラーの基底クラス"""
    pass

class HookInstallationError(HookError):
    """フックインストールエラー"""
    pass

class HookExecutionError(HookError):
    """フック実行エラー"""
    pass

class HookValidationError(HookError):
    """フック検証エラー"""
    pass

# 使用例
try:
    # フックスクリプトの検証
    errors = hook_repo.validate_hook_script(Path("custom_hook.py"))
    if errors:
        raise HookValidationError(f"スクリプト検証失敗: {errors}")

    # フックの実行
    result = hook_repo.execute_hook(HookType.PRE_PUSH, context)
    if result.status == HookStatus.ERROR:
        # エラー詳細をログに記録
        for action_result in result.actions_results:
            if action_result.status == HookStatus.ERROR:
                logger.error(f"{action_result.action_name}: {action_result.error}")
        raise HookExecutionError("フック実行に失敗しました")

except HookError as e:
    # ユーザーフレンドリーなエラーメッセージを表示
    print(f"Git hook エラー: {e}")
    sys.exit(1)
```

## テスト観点

### ユニットテスト
- フック設定の作成と読み込み
- スクリプト検証ロジック
- 実行条件の評価
- アクション実行のモック

### 統合テスト
- 実際のGitリポジトリでのフック動作
- 複数アクションの連続実行
- タイムアウト処理
- エラーハンドリング

### E2Eテスト
```gherkin
Feature: Gitフック管理
  Scenario: 品質チェックフックの自動実行
    Given pre-commitフックがインストールされている
    When 品質基準を満たさないファイルをコミットしようとする
    Then コミットが拒否される
    And 具体的な改善提案が表示される
```

## 品質基準

- コードカバレッジ: 85%以上
- サイクロマティック複雑度: 10以下
- フックスクリプトのセキュリティ検証
- 実行時間の監視（タイムアウト設定）
- エラーメッセージの具体性と対処法の明示
