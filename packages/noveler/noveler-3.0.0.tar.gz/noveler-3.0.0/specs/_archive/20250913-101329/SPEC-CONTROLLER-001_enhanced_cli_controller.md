# EnhancedCLIController 仕様書

## 概要

EnhancedCLIControllerは、高度なユーザーインタラクションを実現するCLIコントローラーです。コマンドの動的補完、インタラクティブモード、進捗表示、バッチ処理など、ユーザビリティを向上させる機能を提供します。

## クラス設計

```python
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum
import asyncio
from datetime import datetime
from pathlib import Path

class InteractionMode(Enum):
    """インタラクションモード"""
    STANDARD = "standard"
    INTERACTIVE = "interactive"
    BATCH = "batch"
    WIZARD = "wizard"

class ProgressStyle(Enum):
    """進捗表示スタイル"""
    BAR = "bar"
    SPINNER = "spinner"
    PERCENTAGE = "percentage"
    DETAILED = "detailed"

@dataclass
class CommandContext:
    """コマンド実行コンテキスト"""
    command: str
    args: List[str]
    options: Dict[str, Any]
    mode: InteractionMode
    user_profile: Optional['UserProfile'] = None
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class UserProfile:
    """ユーザープロファイル"""
    preference_level: str  # "beginner", "intermediate", "advanced"
    preferred_output_format: str  # "simple", "detailed", "json"
    command_history: List[str] = field(default_factory=list)
    shortcuts: Dict[str, str] = field(default_factory=dict)
    color_scheme: str = "default"

@dataclass
class CommandSuggestion:
    """コマンドサジェスチョン"""
    command: str
    description: str
    confidence: float
    category: str
    usage_example: str

@dataclass
class ProgressUpdate:
    """進捗更新情報"""
    current: int
    total: int
    message: str
    sub_tasks: List['SubTask'] = field(default_factory=list)
    eta: Optional[datetime] = None
    style: ProgressStyle = ProgressStyle.BAR

@dataclass
class SubTask:
    """サブタスク情報"""
    name: str
    status: str  # "pending", "running", "completed", "failed"
    progress: Optional[float] = None
    message: Optional[str] = None

class EnhancedCLIController:
    """高度なCLIコントローラー"""

    def __init__(
        self,
        command_registry: 'CommandRegistry',
        ui_renderer: 'UIRenderer',
        completion_engine: 'CompletionEngine',
        user_profile_manager: 'UserProfileManager'
    ):
        self.command_registry = command_registry
        self.ui_renderer = ui_renderer
        self.completion_engine = completion_engine
        self.user_profile_manager = user_profile_manager
        self._active_sessions: Dict[str, CommandContext] = {}
        self._progress_trackers: Dict[str, ProgressTracker] = {}
```

## データ構造

### リクエストモデル

```python
@dataclass
class CommandRequest:
    """コマンドリクエスト"""
    raw_input: str
    interaction_mode: InteractionMode = InteractionMode.STANDARD
    async_execution: bool = False
    batch_commands: Optional[List[str]] = None
    wizard_config: Optional['WizardConfig'] = None

@dataclass
class WizardConfig:
    """ウィザード設定"""
    steps: List['WizardStep']
    allow_back: bool = True
    show_progress: bool = True
    validation_mode: str = "immediate"  # "immediate", "on_submit"

@dataclass
class WizardStep:
    """ウィザードステップ"""
    name: str
    prompt: str
    input_type: str  # "text", "choice", "multiline", "file", "confirm"
    choices: Optional[List[str]] = None
    default: Optional[Any] = None
    validator: Optional[Callable] = None
    help_text: Optional[str] = None

@dataclass
class BatchRequest:
    """バッチ実行リクエスト"""
    commands: List[str]
    parallel: bool = False
    stop_on_error: bool = True
    progress_reporting: bool = True
    output_file: Optional[Path] = None
```

### レスポンスモデル

```python
@dataclass
class CommandResponse:
    """コマンドレスポンス"""
    success: bool
    result: Any
    execution_time: float
    suggestions: List[CommandSuggestion] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)

@dataclass
class InteractiveResponse:
    """インタラクティブレスポンス"""
    prompt: str
    choices: Optional[List[str]] = None
    default_value: Optional[str] = None
    input_type: str = "text"
    validation_rules: List[str] = field(default_factory=list)

@dataclass
class WizardResponse:
    """ウィザードレスポンス"""
    current_step: int
    total_steps: int
    step_data: Dict[str, Any]
    can_proceed: bool
    validation_errors: List[str] = field(default_factory=list)
    completed: bool = False

@dataclass
class BatchResponse:
    """バッチ実行レスポンス"""
    total_commands: int
    executed: int
    succeeded: int
    failed: int
    results: List[CommandResponse]
    execution_log: List[str]
    total_time: float
```

## パブリックメソッド

```python
class EnhancedCLIController:

    async def execute_command(
        self,
        request: CommandRequest
    ) -> CommandResponse:
        """
        コマンドを実行

        Args:
            request: コマンドリクエスト

        Returns:
            コマンド実行結果
        """
        pass

    async def start_interactive_session(
        self,
        command: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        インタラクティブセッションを開始

        Args:
            command: コマンド名
            context: 初期コンテキスト

        Returns:
            セッションID
        """
        pass

    async def handle_interactive_input(
        self,
        session_id: str,
        user_input: str
    ) -> InteractiveResponse:
        """
        インタラクティブ入力を処理

        Args:
            session_id: セッションID
            user_input: ユーザー入力

        Returns:
            インタラクティブレスポンス
        """
        pass

    async def start_wizard(
        self,
        wizard_config: WizardConfig
    ) -> str:
        """
        ウィザードを開始

        Args:
            wizard_config: ウィザード設定

        Returns:
            ウィザードセッションID
        """
        pass

    async def process_wizard_step(
        self,
        wizard_id: str,
        step_input: Any
    ) -> WizardResponse:
        """
        ウィザードステップを処理

        Args:
            wizard_id: ウィザードID
            step_input: ステップ入力

        Returns:
            ウィザードレスポンス
        """
        pass

    async def execute_batch(
        self,
        batch_request: BatchRequest
    ) -> BatchResponse:
        """
        バッチコマンドを実行

        Args:
            batch_request: バッチリクエスト

        Returns:
            バッチ実行結果
        """
        pass

    def get_command_suggestions(
        self,
        partial_input: str,
        context: Optional[CommandContext] = None
    ) -> List[CommandSuggestion]:
        """
        コマンドサジェスチョンを取得

        Args:
            partial_input: 部分入力
            context: コマンドコンテキスト

        Returns:
            サジェスチョンリスト
        """
        pass

    def track_progress(
        self,
        task_id: str,
        progress_update: ProgressUpdate
    ) -> None:
        """
        進捗を追跡

        Args:
            task_id: タスクID
            progress_update: 進捗更新情報
        """
        pass

    def customize_output(
        self,
        response: Any,
        format_type: str,
        user_profile: Optional[UserProfile] = None
    ) -> str:
        """
        出力をカスタマイズ

        Args:
            response: レスポンスデータ
            format_type: フォーマットタイプ
            user_profile: ユーザープロファイル

        Returns:
            フォーマット済み出力
        """
        pass
```

## プライベートメソッド

```python
class EnhancedCLIController:

    def _parse_command(
        self,
        raw_input: str
    ) -> Tuple[str, List[str], Dict[str, Any]]:
        """コマンドを解析"""
        pass

    def _validate_command(
        self,
        command: str,
        args: List[str],
        options: Dict[str, Any]
    ) -> List[str]:
        """コマンドを検証"""
        pass

    async def _execute_single_command(
        self,
        context: CommandContext
    ) -> CommandResponse:
        """単一コマンドを実行"""
        pass

    def _build_suggestions(
        self,
        command: str,
        error: Optional[Exception] = None
    ) -> List[CommandSuggestion]:
        """サジェスチョンを構築"""
        pass

    def _update_user_history(
        self,
        user_profile: UserProfile,
        command: str,
        success: bool
    ) -> None:
        """ユーザー履歴を更新"""
        pass

    async def _render_progress(
        self,
        progress: ProgressUpdate
    ) -> None:
        """進捗を表示"""
        pass

    def _apply_user_preferences(
        self,
        output: Any,
        user_profile: UserProfile
    ) -> Any:
        """ユーザー設定を適用"""
        pass

    async def _handle_async_execution(
        self,
        command_func: Callable,
        args: tuple,
        kwargs: dict
    ) -> Any:
        """非同期実行を処理"""
        pass
```

## ユーザーインターフェース

### コマンド構文

```bash
# 標準モード
novel [command] [args] [options]

# インタラクティブモード
novel --interactive [command]
novel -i write new

# バッチモード
novel --batch commands.txt
novel -b "write new; check; publish"

# ウィザードモード
novel --wizard project-setup
novel -w episode-creation

# 進捗表示オプション
novel --progress detailed [command]
novel -p spinner analyze --all

# 出力フォーマット指定
novel --output json status
novel -o table list episodes
```

### ヘルプシステム

```bash
# コンテキスト依存ヘルプ
novel help write        # writeコマンドの詳細ヘルプ
novel help --examples   # 使用例付きヘルプ
novel help --video      # ビデオチュートリアルリンク

# インタラクティブヘルプ
novel help --interactive
> What would you like to do?
> 1. Create new episode
> 2. Check quality
> 3. Publish content

# スマートサジェスチョン
novel writ[TAB]         # -> write
novel check --fix[TAB]  # -> --auto-fix
```

### エラーメッセージ

```python
ERROR_MESSAGES = {
    "command_not_found": """
コマンド '{command}' が見つかりません。

もしかして:
  {suggestions}

すべてのコマンドを見るには 'novel help' を実行してください。
""",

    "invalid_arguments": """
引数が正しくありません: {error}

正しい使用方法:
  {usage}

例:
  {example}
""",

    "interactive_cancelled": """
インタラクティブセッションがキャンセルされました。
入力された内容は保存されていません。
""",

    "batch_execution_failed": """
バッチ実行中にエラーが発生しました。

実行済み: {executed}/{total}
成功: {succeeded}
失敗: {failed}

詳細はログファイルを確認してください: {log_file}
"""
}
```

## 依存関係

```python
from application.services.command_registry import CommandRegistry
from presentation.renderers.ui_renderer import UIRenderer
from infrastructure.completion.completion_engine import CompletionEngine
from domain.services.user_profile_manager import UserProfileManager
from infrastructure.logging.progress_tracker import ProgressTracker
from domain.services.validation_service import ValidationService
```

## 設計原則遵守

### Clean Architecture準拠
- プレゼンテーション層の責務に専念
- ビジネスロジックは含まない
- アプリケーション層のユースケースを呼び出す

### MVC原則
- Controller: コマンド処理とフロー制御
- View: UIRendererへの委譲
- Model: ドメイン層エンティティの利用

### ユーザビリティ原則
- 直感的なコマンド構造
- 豊富なフィードバック
- エラーからの回復支援
- 段階的な学習曲線

## 使用例

### 基本的な使用例

```python
# コントローラーの初期化
controller = EnhancedCLIController(
    command_registry=registry,
    ui_renderer=renderer,
    completion_engine=completion,
    user_profile_manager=profile_manager
)

# 標準コマンド実行
request = CommandRequest(
    raw_input="write new --title '転生した件について'",
    interaction_mode=InteractionMode.STANDARD
)
response = await controller.execute_command(request)
```

### インタラクティブモード

```python
# インタラクティブセッション開始
session_id = await controller.start_interactive_session("write")

# ユーザー入力処理
response = await controller.handle_interactive_input(
    session_id,
    "第1話 異世界転生"
)
print(response.prompt)  # "エピソードの概要を入力してください:"
```

### ウィザードモード

```python
# プロジェクト設定ウィザード
wizard_config = WizardConfig(
    steps=[
        WizardStep(
            name="project_name",
            prompt="プロジェクト名を入力してください",
            input_type="text",
            validator=validate_project_name
        ),
        WizardStep(
            name="genre",
            prompt="ジャンルを選択してください",
            input_type="choice",
            choices=["ファンタジー", "SF", "恋愛", "その他"]
        ),
        WizardStep(
            name="target_readers",
            prompt="ターゲット読者層を入力してください",
            input_type="multiline"
        )
    ]
)

wizard_id = await controller.start_wizard(wizard_config)
```

### バッチ実行

```python
# バッチリクエスト作成
batch_request = BatchRequest(
    commands=[
        "write new --episode 1",
        "write new --episode 2",
        "write new --episode 3",
        "check --all --auto-fix",
        "analyze dropout"
    ],
    parallel=False,
    stop_on_error=False,
    progress_reporting=True
)

# バッチ実行
batch_response = await controller.execute_batch(batch_request)
print(f"成功: {batch_response.succeeded}/{batch_response.total_commands}")
```

### 進捗表示

```python
# 進捗追跡
progress = ProgressUpdate(
    current=5,
    total=10,
    message="エピソードを処理中...",
    sub_tasks=[
        SubTask("品質チェック", "completed", 1.0),
        SubTask("文体統一", "running", 0.6),
        SubTask("誤字脱字修正", "pending")
    ],
    style=ProgressStyle.DETAILED
)

controller.track_progress("quality_check_task", progress)
```

## エラーハンドリング

```python
class CommandExecutionError(Exception):
    """コマンド実行エラー"""
    def __init__(self, message: str, suggestions: List[str] = None):
        super().__init__(message)
        self.suggestions = suggestions or []

class InteractiveSessionError(Exception):
    """インタラクティブセッションエラー"""
    pass

class WizardValidationError(Exception):
    """ウィザード検証エラー"""
    def __init__(self, step: str, errors: List[str]):
        super().__init__(f"Step '{step}' validation failed")
        self.step = step
        self.errors = errors

class BatchExecutionError(Exception):
    """バッチ実行エラー"""
    def __init__(self, failed_commands: List[Tuple[str, Exception]]):
        super().__init__(f"{len(failed_commands)} commands failed")
        self.failed_commands = failed_commands

# エラーハンドリング例
try:
    response = await controller.execute_command(request)
except CommandExecutionError as e:
    print(f"エラー: {e}")
    if e.suggestions:
        print("提案:")
        for suggestion in e.suggestions:
            print(f"  - {suggestion}")
```

## テスト観点

### ユニットテスト
- コマンド解析の正確性
- サジェスチョン生成ロジック
- 進捗計算の正確性
- エラーメッセージの妥当性

### 統合テスト
- コマンド実行フロー全体
- インタラクティブセッション管理
- ウィザードステップ遷移
- バッチ実行と並列処理

### E2Eテスト
```gherkin
Feature: 高度なCLI操作

  Scenario: インタラクティブモードでエピソード作成
    Given ユーザーがインタラクティブモードを起動
    When "write"コマンドを選択
    And タイトルとして"新章開幕"を入力
    Then エピソードが作成される
    And 次のステップが提示される

  Scenario: バッチモードで複数タスク実行
    Given 5つのコマンドを含むバッチファイル
    When バッチ実行を開始
    Then 進捗バーが表示される
    And 各コマンドの結果が記録される
```

## 品質基準

### パフォーマンス基準
- コマンド解析: < 10ms
- サジェスチョン生成: < 50ms
- インタラクティブ応答: < 100ms
- バッチ実行オーバーヘッド: < 5%

### ユーザビリティ基準
- コマンド補完精度: > 95%
- エラーメッセージ理解度: > 90%
- ウィザード完了率: > 80%
- ヘルプ利用後の成功率: > 95%

### 信頼性基準
- セッション管理の安定性: 99.9%
- バッチ実行の完了率: > 98%
- 進捗表示の正確性: 100%
- エラーリカバリー成功率: > 95%
