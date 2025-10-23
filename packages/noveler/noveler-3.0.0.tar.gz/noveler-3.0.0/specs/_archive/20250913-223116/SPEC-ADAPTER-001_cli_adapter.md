# CLIアダプター仕様書

## 概要
CLIアダプターは、外部CLIコマンドシステムとドメイン層のユースケースを接続するアダプターです。コマンドライン引数の解析、ユースケースへの変換、実行結果の表示を担当します。

## クラス設計

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class CommandType(Enum):
    """コマンドタイプ"""
    PROJECT = "project"
    EPISODE = "episode"
    QUALITY = "quality"
    ANALYSIS = "analysis"
    CONFIGURATION = "config"

@dataclass
class CommandContext:
    """コマンドコンテキスト"""
    command_type: CommandType
    command_name: str
    arguments: Dict[str, Any]
    options: Dict[str, Any]
    working_directory: str
    user: Optional[str] = None

class ICommandHandler(ABC):
    """コマンドハンドラーインターフェース"""

    @abstractmethod
    def can_handle(self, context: CommandContext) -> bool:
        """コマンドを処理できるか判定"""
        pass

    @abstractmethod
    def handle(self, context: CommandContext) -> CommandResult:
        """コマンドを実行"""
        pass

@dataclass
class CommandResult:
    """コマンド実行結果"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    exit_code: int = 0

class CLIAdapter:
    """CLIアダプター"""

    def __init__(
        self,
        command_parser: ICommandParser,
        command_registry: ICommandRegistry,
        output_formatter: IOutputFormatter,
        error_handler: IErrorHandler
    ):
        self._parser = command_parser
        self._registry = command_registry
        self._formatter = output_formatter
        self._error_handler = error_handler
```

## データ構造

### インターフェース定義

```python
class ICommandParser(ABC):
    """コマンドパーサーインターフェース"""

    @abstractmethod
    def parse(self, args: List[str]) -> CommandContext:
        """引数を解析してコマンドコンテキストを生成"""
        pass

class ICommandRegistry(ABC):
    """コマンドレジストリインターフェース"""

    @abstractmethod
    def register(self, handler: ICommandHandler) -> None:
        """コマンドハンドラーを登録"""
        pass

    @abstractmethod
    def get_handler(self, context: CommandContext) -> Optional[ICommandHandler]:
        """適切なハンドラーを取得"""
        pass

class IOutputFormatter(ABC):
    """出力フォーマッターインターフェース"""

    @abstractmethod
    def format_success(self, result: CommandResult) -> str:
        """成功結果をフォーマット"""
        pass

    @abstractmethod
    def format_error(self, error: Exception) -> str:
        """エラーをフォーマット"""
        pass

class IErrorHandler(ABC):
    """エラーハンドラーインターフェース"""

    @abstractmethod
    def handle(self, error: Exception, context: CommandContext) -> CommandResult:
        """エラーをハンドリング"""
        pass
```

### アダプター実装

```python
@dataclass
class ParsedCommand:
    """解析済みコマンド"""
    main_command: str
    sub_command: Optional[str]
    positional_args: List[str]
    named_args: Dict[str, Any]
    flags: List[str]

class ArgvCommandParser(ICommandParser):
    """argvベースのコマンドパーサー"""

    def parse(self, args: List[str]) -> CommandContext:
        parsed = self._parse_argv(args)
        command_type = self._determine_command_type(parsed.main_command)

        return CommandContext(
            command_type=command_type,
            command_name=self._build_command_name(parsed),
            arguments=self._build_arguments(parsed),
            options=self._build_options(parsed),
            working_directory=os.getcwd()
        )
```

## パブリックメソッド

### CLIAdapter

```python
def execute(self, args: List[str]) -> int:
    """
    CLIコマンドを実行

    Args:
        args: コマンドライン引数

    Returns:
        int: 終了コード
    """
    try:
        # コマンド解析
        context = self._parser.parse(args)

        # ハンドラー取得
        handler = self._registry.get_handler(context)
        if not handler:
            raise CommandNotFoundError(f"Unknown command: {context.command_name}")

        # コマンド実行
        result = handler.handle(context)

        # 結果出力
        self._display_result(result)

        return result.exit_code

    except Exception as e:
        # エラーハンドリング
        result = self._error_handler.handle(e, context)
        self._display_error(e, result)
        return result.exit_code

def register_handlers(self, handlers: List[ICommandHandler]) -> None:
    """
    コマンドハンドラーを一括登録

    Args:
        handlers: 登録するハンドラーのリスト
    """
    for handler in handlers:
        self._registry.register(handler)

def add_middleware(self, middleware: ICommandMiddleware) -> None:
    """
    ミドルウェアを追加

    Args:
        middleware: 追加するミドルウェア
    """
    self._middlewares.append(middleware)
```

## プライベートメソッド

```python
def _display_result(self, result: CommandResult) -> None:
    """実行結果を表示"""
    output = self._formatter.format_success(result)
    if result.success:
        print(output)
    else:
        print(output, file=sys.stderr)

def _display_error(self, error: Exception, result: CommandResult) -> None:
    """エラーを表示"""
    output = self._formatter.format_error(error)
    print(output, file=sys.stderr)

    if result.data and result.data.get("suggestions"):
        print("\n提案:")
        for suggestion in result.data["suggestions"]:
            print(f"  - {suggestion}")

def _apply_middlewares(
    self,
    context: CommandContext,
    handler: ICommandHandler
) -> CommandResult:
    """ミドルウェアを適用"""
    chain = handler.handle

    for middleware in reversed(self._middlewares):
        chain = middleware.wrap(chain)

    return chain(context)
```

## アダプターパターン実装

### ユースケースアダプター

```python
class CreateEpisodeCommandHandler(ICommandHandler):
    """エピソード作成コマンドハンドラー"""

    def __init__(self, use_case: CreateEpisodeUseCase):
        self._use_case = use_case

    def can_handle(self, context: CommandContext) -> bool:
        return (
            context.command_type == CommandType.EPISODE and
            context.command_name == "episode.create"
        )

    def handle(self, context: CommandContext) -> CommandResult:
        # CLIコンテキストをユースケース入力に変換
        try:
            request = CreateEpisodeRequest(
                project_name=context.arguments["project"],
                episode_number=int(context.arguments.get("number", 0)),
                title=context.arguments.get("title", ""),
                auto_numbering=context.options.get("auto_number", False)
            )

            # ユースケース実行
            response = self._use_case.execute(request)

            # 結果をCLI結果に変換
            return CommandResult(
                success=True,
                message=f"エピソード '{response.episode.title}' を作成しました",
                data={
                    "episode_number": response.episode.number,
                    "file_path": response.file_path
                }
            )

        except DomainError as e:
            return CommandResult(
                success=False,
                message=str(e),
                exit_code=1
            )
```

### 外部ツールアダプター

```python
class GitCommandAdapter:
    """Gitコマンドアダプター"""

    def __init__(self, git_service: IGitService):
        self._git_service = git_service

    def create_handler(self) -> ICommandHandler:
        """Gitコマンドハンドラーを生成"""
        return GitCommandHandler(self._git_service)

class ExternalToolAdapter:
    """外部ツールアダプター"""

    def __init__(self, tool_name: str, tool_path: str):
        self._tool_name = tool_name
        self._tool_path = tool_path

    def adapt_to_command(self, command: str) -> Callable:
        """外部ツールコマンドをPython関数に適応"""
        def execute(**kwargs) -> Dict[str, Any]:
            args = self._build_args(command, kwargs)
            result = subprocess.run(
                [self._tool_path] + args,
                capture_output=True,
                text=True
            )

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }

        return execute
```

## 依存関係

```python
from domain.use_cases import (
    CreateEpisodeUseCase,
    QualityCheckUseCase,
    AnalyzeDropoutUseCase
)
from domain.services import IErrorHandler, IUserGuidanceService
from infrastructure.services import (
    IGitService,
    IFileSystemService,
    IProcessService
)
```

## 設計原則遵守

### アダプターパターン
- **インターフェース分離**: 各アダプターは単一の責務を持つ
- **依存性逆転**: ドメイン層への依存はインターフェース経由
- **Open/Closed原則**: 新しいコマンドハンドラーの追加が容易

### クリーンアーキテクチャ
- **レイヤー分離**: CLI層はドメイン層の詳細を知らない
- **依存方向**: CLI → Application → Domain
- **テスタビリティ**: 全ての依存関係は注入可能

## 使用例

### 基本的な使用

```python
# アダプター設定
parser = ArgvCommandParser()
registry = CommandRegistry()
formatter = ColoredOutputFormatter()
error_handler = SmartErrorHandler()

cli = CLIAdapter(parser, registry, formatter, error_handler)

# ハンドラー登録
cli.register_handlers([
    CreateEpisodeCommandHandler(create_episode_use_case),
    QualityCheckCommandHandler(quality_check_use_case),
    AnalyzeCommandHandler(analyze_use_case)
])

# 実行
exit_code = cli.execute(sys.argv[1:])
sys.exit(exit_code)
```

### カスタムハンドラー

```python
class CustomCommandHandler(ICommandHandler):
    """カスタムコマンドハンドラー"""

    def __init__(self, custom_service: ICustomService):
        self._service = custom_service

    def can_handle(self, context: CommandContext) -> bool:
        return context.command_name == "custom.process"

    def handle(self, context: CommandContext) -> CommandResult:
        # カスタム処理
        data = self._service.process(
            context.arguments["input"],
            context.options
        )

        return CommandResult(
            success=True,
            message="処理が完了しました",
            data=data
        )

# 登録
cli.register_handlers([CustomCommandHandler(custom_service)])
```

## エラーハンドリング

```python
class SmartErrorHandler(IErrorHandler):
    """スマートエラーハンドラー"""

    def handle(self, error: Exception, context: CommandContext) -> CommandResult:
        if isinstance(error, CommandNotFoundError):
            return self._handle_command_not_found(error, context)
        elif isinstance(error, ValidationError):
            return self._handle_validation_error(error, context)
        elif isinstance(error, DomainError):
            return self._handle_domain_error(error, context)
        else:
            return self._handle_unknown_error(error, context)

    def _handle_command_not_found(
        self,
        error: CommandNotFoundError,
        context: CommandContext
    ) -> CommandResult:
        suggestions = self._suggest_commands(context.command_name)

        return CommandResult(
            success=False,
            message=f"コマンド '{context.command_name}' が見つかりません",
            data={"suggestions": suggestions},
            exit_code=127
        )
```

## テスト観点

### ユニットテスト
- コマンド解析の正確性
- ハンドラー選択ロジック
- 結果フォーマットの検証
- エラーハンドリングのカバレッジ

### 統合テスト
- エンドツーエンドのコマンド実行
- ユースケースとの連携
- 外部ツールとの統合
- ミドルウェアチェーン

### パフォーマンステスト
- コマンド解析速度
- ハンドラー検索効率
- 大量オプション処理

## 品質基準

### コード品質
- 循環的複雑度: 10以下
- テストカバレッジ: 90%以上
- 型ヒント: 100%実装

### 設計品質
- 単一責任原則の遵守
- インターフェース分離の徹底
- 依存性注入の活用

### 運用品質
- エラーメッセージの明確性
- ログ出力の適切性
- デバッグ情報の充実
