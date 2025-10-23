# SPEC-API-101: MCP Tool API 仕様書

## 概要

小説執筆支援CLI機能をMCP（Model Context Protocol）ツールとしてラップし、
LLMエージェントとの高精度な連携を実現するAPI仕様書。

## メタデータ

| 項目 | 内容 |
|------|------|
| 仕様ID | SPEC-API-001 |
| E2EテストID | E2E-API-001 |
| test_type | integration |
| バージョン | v1.0.0 |
| 作成日 | 2025-08-27 |
| 最終更新 | 2025-08-28 |
| ステータス | active |
| プロトコル | MCP (Model Context Protocol) |
| 対象CLI | novel, check, plot, quality コマンド群 |

## 1. MCP Server概要

### 1.1 Server基本情報

```json
{
  "name": "novel-writing-cli-wrapper",
  "version": "1.0.0",
  "description": "小説執筆支援CLI MCPラッパーツール",
  "author": "Novel Writing System Team",
  "license": "MIT",
  "homepage": "https://github.com/your-org/novel-writing-system",
  "capabilities": {
    "tools": true,
    "resources": true,
    "prompts": false,
    "logging": true
  }
}
```

### 1.2 サポートされるMCP機能

- **Tools**: CLI機能のツール化（主機能）
- **Resources**: 生成ファイルへのアクセス
- **Logging**: 実行ログ・エラー追跡
- **Prompts**: なし（将来拡張予定）

## 2. Tools定義

### 2.1 Episode Creation Tool

```json
{
  "name": "create_episode",
  "description": "新しいエピソードを作成し、プロット・原稿を生成",
  "inputSchema": {
    "type": "object",
    "properties": {
      "episode_number": {
        "type": "integer",
        "description": "エピソード番号",
        "minimum": 1,
        "maximum": 9999
      },
      "title": {
        "type": "string",
        "description": "エピソードタイトル",
        "minLength": 1,
        "maxLength": 100
      },
      "genre": {
        "type": "string",
        "description": "ジャンル",
        "enum": ["fantasy", "mystery", "romance", "sci-fi", "slice-of-life", "adventure"]
      },
      "word_count_target": {
        "type": "integer",
        "description": "目標文字数",
        "minimum": 100,
        "maximum": 50000,
        "default": 2000
      },
      "viewpoint": {
        "type": "string",
        "description": "視点（一人称/三人称）",
        "enum": ["first_person", "third_person"],
        "default": "third_person"
      },
      "viewpoint_character": {
        "type": "string",
        "description": "視点キャラクター名",
        "maxLength": 50
      },
      "custom_requirements": {
        "type": "array",
        "description": "カスタム要件リスト",
        "items": {
          "type": "string",
          "maxLength": 200
        },
        "maxItems": 10
      },
      "use_ai_generation": {
        "type": "boolean",
        "description": "AI生成使用フラグ",
        "default": true
      }
    },
    "required": ["episode_number", "title", "genre", "viewpoint_character"],
    "additionalProperties": false
  }
}
```

### 2.2 Quality Check Tool

```json
{
  "name": "quality_check",
  "description": "指定ファイルまたはプロジェクト全体の品質チェック実行",
  "inputSchema": {
    "type": "object",
    "properties": {
      "target_files": {
        "type": "array",
        "description": "チェック対象ファイルパス一覧",
        "items": {
          "type": "string",
          "pattern": "^[^/].*\\.(md|yaml|json)$"
        },
        "maxItems": 50
      },
      "check_types": {
        "type": "array",
        "description": "チェック種別",
        "items": {
          "type": "string",
          "enum": [
            "grammar",
            "consistency",
            "plot_coherence",
            "character_development",
            "pacing",
            "style",
            "technical_validation"
          ]
        },
        "minItems": 1,
        "uniqueItems": true
      },
      "severity_threshold": {
        "type": "string",
        "description": "重要度しきい値",
        "enum": ["low", "medium", "high", "critical"],
        "default": "medium"
      },
      "include_suggestions": {
        "type": "boolean",
        "description": "改善提案含む",
        "default": true
      },
      "output_format": {
        "type": "string",
        "description": "出力形式",
        "enum": ["detailed", "summary", "actionable"],
        "default": "detailed"
      }
    },
    "required": ["check_types"],
    "additionalProperties": false
  }
}
```

### 2.3 Plot Generation Tool

```json
{
  "name": "generate_plot",
  "description": "エピソードまたは章のプロット生成",
  "inputSchema": {
    "type": "object",
    "properties": {
      "target_episode": {
        "type": "integer",
        "description": "対象エピソード番号",
        "minimum": 1
      },
      "plot_type": {
        "type": "string",
        "description": "プロットタイプ",
        "enum": ["episode", "chapter", "arc"],
        "default": "episode"
      },
      "plot_structure": {
        "type": "string",
        "description": "プロット構造",
        "enum": ["three_act", "kishōtenketsu", "hero_journey", "custom"],
        "default": "kishōtenketsu"
      },
      "complexity_level": {
        "type": "string",
        "description": "複雑度レベル",
        "enum": ["simple", "moderate", "complex"],
        "default": "moderate"
      },
      "previous_context": {
        "type": "boolean",
        "description": "前エピソード文脈考慮",
        "default": true
      },
      "character_focus": {
        "type": "array",
        "description": "フォーカスキャラクター",
        "items": {
          "type": "string",
          "maxLength": 50
        },
        "maxItems": 5
      },
      "theme_keywords": {
        "type": "array",
        "description": "テーマキーワード",
        "items": {
          "type": "string",
          "maxLength": 30
        },
        "maxItems": 10
      }
    },
    "required": ["target_episode", "plot_type"],
    "additionalProperties": false
  }
}
```

### 2.4 Project Status Tool

```json
{
  "name": "get_project_status",
  "description": "プロジェクト全体の状況確認・統計取得",
  "inputSchema": {
    "type": "object",
    "properties": {
      "include_metrics": {
        "type": "boolean",
        "description": "メトリクス含む",
        "default": true
      },
      "include_file_list": {
        "type": "boolean",
        "description": "ファイル一覧含む",
        "default": true
      },
      "include_quality_summary": {
        "type": "boolean",
        "description": "品質サマリー含む",
        "default": true
      },
      "date_range_days": {
        "type": "integer",
        "description": "統計対象日数",
        "minimum": 1,
        "maximum": 365,
        "default": 30
      }
    },
    "additionalProperties": false
  }
}
```

### 2.5 File Management Tool

```json
{
  "name": "manage_files",
  "description": "プロジェクトファイルの管理・操作",
  "inputSchema": {
    "type": "object",
    "properties": {
      "operation": {
        "type": "string",
        "description": "操作種別",
        "enum": ["list", "backup", "restore", "cleanup", "validate"],
        "default": "list"
      },
      "target_pattern": {
        "type": "string",
        "description": "対象ファイルパターン（glob）",
        "default": "**/*.md"
      },
      "backup_location": {
        "type": "string",
        "description": "バックアップ先（backup操作時）",
        "pattern": "^[^/].*$"
      },
      "max_age_days": {
        "type": "integer",
        "description": "最大保持日数（cleanup操作時）",
        "minimum": 1,
        "default": 30
      },
      "verify_integrity": {
        "type": "boolean",
        "description": "完全性検証実行",
        "default": true
      }
    },
    "required": ["operation"],
    "additionalProperties": false
  }
}
```

## 3. Resources定義

### 3.1 Generated Files Resource

```json
{
  "uri": "file://generated/{path}",
  "name": "Generated File",
  "description": "CLI実行で生成されたファイル",
  "mimeType": "auto-detect"
}
```

### 3.2 Project Configuration Resource

```json
{
  "uri": "config://project",
  "name": "Project Configuration",
  "description": "プロジェクト設定情報",
  "mimeType": "application/json"
}
```

### 3.3 Quality Reports Resource

```json
{
  "uri": "reports://quality/{date}",
  "name": "Quality Report",
  "description": "品質チェックレポート",
  "mimeType": "application/json"
}
```

## 4. Tool実装詳細

### 4.1 Tool Base Class

```python
# scripts/infrastructure/mcp/tools/base_tool.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pathlib import Path
import uuid
import asyncio
import subprocess

from mcp import types
from ..models.tool_response import ToolResponse, FileReference
from ..validators.tool_input_validator import ToolInputValidator

class BaseMCPTool(ABC):
    """MCP Tool基底クラス"""

    def __init__(self,
                 cli_executable: str = "python",
                 cli_script_path: Path = None,
                 output_dir: Path = None,
                 timeout_seconds: int = 300):
        self.cli_executable = cli_executable
        self.cli_script_path = cli_script_path or Path("bin/novel")
        self.output_dir = output_dir or Path("outputs")
        self.timeout_seconds = timeout_seconds
        self.validator = ToolInputValidator()

        # 出力ディレクトリ確保
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> types.TextContent:
        """ツール実行（抽象メソッド）"""
        pass

    async def _execute_cli_command(self,
                                  command_args: List[str],
                                  operation_id: str = None) -> Dict[str, Any]:
        """CLI コマンド実行"""

        operation_id = operation_id or str(uuid.uuid4())

        # 完全なコマンド構築
        full_command = [
            self.cli_executable,
            str(self.cli_script_path)
        ] + command_args + [
            "--json-output",  # JSON出力強制
            "--operation-id", operation_id
        ]

        try:
            # 非同期プロセス実行
            process = await asyncio.create_subprocess_exec(
                *full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=Path.cwd()
            )

            # タイムアウト付きで結果取得
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout_seconds
            )

            # JSON レスポンス解析
            if process.returncode == 0:
                import json
                result = json.loads(stdout.decode('utf-8'))
                result['stderr'] = stderr.decode('utf-8') if stderr else None
                return result
            else:
                # エラー時のフォールバック
                return {
                    'success': False,
                    'error': {
                        'code': 'CLI_EXECUTION_ERROR',
                        'message': f'CLI実行エラー（終了コード: {process.returncode}）',
                        'hint': 'コマンド引数と権限を確認してください',
                        'details': {
                            'return_code': process.returncode,
                            'stderr': stderr.decode('utf-8') if stderr else '',
                            'stdout': stdout.decode('utf-8') if stdout else ''
                        }
                    },
                    'command': ' '.join(full_command),
                    'operation_id': operation_id
                }

        except asyncio.TimeoutError:
            return {
                'success': False,
                'error': {
                    'code': 'CLI_TIMEOUT_ERROR',
                    'message': f'{self.timeout_seconds}秒でタイムアウトしました',
                    'hint': 'より小さなファイル・シンプルな設定で再試行してください',
                    'details': {
                        'timeout_seconds': self.timeout_seconds,
                        'command': ' '.join(full_command)
                    }
                },
                'command': ' '.join(full_command),
                'operation_id': operation_id
            }

        except Exception as e:
            return {
                'success': False,
                'error': {
                    'code': 'UNEXPECTED_ERROR',
                    'message': f'予期しないエラー: {str(e)}',
                    'hint': 'システム管理者に連絡してください',
                    'details': {
                        'error_type': type(e).__name__,
                        'error_message': str(e)
                    }
                },
                'command': ' '.join(full_command),
                'operation_id': operation_id
            }

    def _format_mcp_response(self, cli_result: Dict[str, Any]) -> types.TextContent:
        """CLI結果をMCPレスポンス形式に変換"""

        if cli_result.get('success', False):
            # 成功レスポンス
            response_text = self._format_success_response(cli_result)
        else:
            # エラーレスポンス
            response_text = self._format_error_response(cli_result)

        return types.TextContent(
            type="text",
            text=response_text
        )

    def _format_success_response(self, cli_result: Dict[str, Any]) -> str:
        """成功レスポンス整形"""
        import json

        # ファイル参照情報抽出
        file_refs = []
        if 'outputs' in cli_result and 'files' in cli_result['outputs']:
            for file_info in cli_result['outputs']['files']:
                file_refs.append(f"📄 {file_info['path']} ({file_info['size_bytes']} bytes)")

        # メタデータ情報抽出
        metadata = cli_result.get('metadata', {})
        execution_time = cli_result.get('execution_time_ms', 0)

        response_parts = [
            "✅ 実行完了",
            f"コマンド: {cli_result.get('command', 'N/A')}",
            f"実行時間: {execution_time:.2f}ms",
            ""
        ]

        if file_refs:
            response_parts.extend([
                "📁 生成ファイル:",
                *[f"  {ref}" for ref in file_refs],
                ""
            ])

        if metadata:
            response_parts.extend([
                "📊 メタデータ:",
                *[f"  {k}: {v}" for k, v in metadata.items()],
                ""
            ])

        response_parts.extend([
            "🔍 詳細情報:",
            "ファイル内容を確認するには、該当パスのファイルを読み込んでください。",
            "SHA256ハッシュによる完全性検証も利用可能です。"
        ])

        return "\n".join(response_parts)

    def _format_error_response(self, cli_result: Dict[str, Any]) -> str:
        """エラーレスポンス整形"""

        error = cli_result.get('error', {})
        error_code = error.get('code', 'UNKNOWN_ERROR')
        error_message = error.get('message', '不明なエラー')
        error_hint = error.get('hint', 'ログを確認してください')

        response_parts = [
            f"❌ エラー: {error_code}",
            f"メッセージ: {error_message}",
            f"解決方法: {error_hint}",
            ""
        ]

        # 詳細情報がある場合
        if 'details' in error:
            details = error['details']
            response_parts.extend([
                "🔍 詳細情報:",
                *[f"  {k}: {v}" for k, v in details.items()],
                ""
            ])

        response_parts.extend([
            f"コマンド: {cli_result.get('command', 'N/A')}",
            f"実行時刻: {cli_result.get('timestamp', 'N/A')}"
        ])

        return "\n".join(response_parts)
```

### 4.2 Episode Creation Tool実装

```python
# scripts/infrastructure/mcp/tools/episode_creation_tool.py
from typing import Any, Dict
from mcp import types
from .base_tool import BaseMCPTool

class EpisodeCreationTool(BaseMCPTool):
    """エピソード作成ツール"""

    async def execute(self, arguments: Dict[str, Any]) -> types.TextContent:
        """エピソード作成実行"""

        # 入力バリデーション
        validation_result = self.validator.validate_episode_creation(arguments)
        if not validation_result.is_valid:
            return self._format_validation_error(validation_result.errors)

        # CLI コマンド引数構築
        command_args = [
            "create",
            str(arguments["episode_number"]),
            "--title", arguments["title"],
            "--genre", arguments["genre"],
            "--viewpoint", arguments["viewpoint"],
            "--viewpoint-character", arguments["viewpoint_character"],
            "--word-count-target", str(arguments.get("word_count_target", 2000))
        ]

        # カスタム要件追加
        if "custom_requirements" in arguments:
            for requirement in arguments["custom_requirements"]:
                command_args.extend(["--custom-requirement", requirement])

        # AI生成フラグ
        if arguments.get("use_ai_generation", True):
            command_args.append("--use-ai-generation")

        # CLI実行
        cli_result = await self._execute_cli_command(command_args)

        # MCP レスポンス形式変換
        return self._format_mcp_response(cli_result)

    def _format_validation_error(self, errors: List[str]) -> types.TextContent:
        """バリデーションエラー整形"""
        error_text = "❌ 入力データエラー\n\n" + "\n".join([
            f"• {error}" for error in errors
        ])

        return types.TextContent(type="text", text=error_text)
```

### 4.3 Quality Check Tool実装

```python
# scripts/infrastructure/mcp/tools/quality_check_tool.py
from typing import Any, Dict, List
from mcp import types
from .base_tool import BaseMCPTool

class QualityCheckTool(BaseMCPTool):
    """品質チェックツール"""

    async def execute(self, arguments: Dict[str, Any]) -> types.TextContent:
        """品質チェック実行"""

        # バリデーション
        validation_result = self.validator.validate_quality_check(arguments)
        if not validation_result.is_valid:
            return self._format_validation_error(validation_result.errors)

        # CLI コマンド引数構築
        command_args = ["check"]

        # 対象ファイル指定
        if "target_files" in arguments:
            for file_path in arguments["target_files"]:
                command_args.extend(["--file", file_path])
        else:
            command_args.append("--all")  # 全ファイル対象

        # チェック種別指定
        for check_type in arguments["check_types"]:
            command_args.extend(["--check-type", check_type])

        # しきい値指定
        severity = arguments.get("severity_threshold", "medium")
        command_args.extend(["--severity", severity])

        # オプション指定
        if arguments.get("include_suggestions", True):
            command_args.append("--include-suggestions")

        output_format = arguments.get("output_format", "detailed")
        command_args.extend(["--output-format", output_format])

        # CLI実行
        cli_result = await self._execute_cli_command(command_args)

        # 品質チェック特化の応答整形
        return self._format_quality_check_response(cli_result)

    def _format_quality_check_response(self, cli_result: Dict[str, Any]) -> types.TextContent:
        """品質チェック特化レスポンス整形"""

        if not cli_result.get('success', False):
            return self._format_mcp_response(cli_result)

        # 品質チェック結果の詳細表示
        metadata = cli_result.get('metadata', {})
        quality_score = metadata.get('quality_score', 'N/A')
        issue_count = metadata.get('issue_count', 0)

        response_parts = [
            "📊 品質チェック完了",
            f"総合品質スコア: {quality_score}",
            f"検出問題数: {issue_count}",
            ""
        ]

        # ファイル別結果表示
        if 'outputs' in cli_result:
            response_parts.append("📁 詳細レポート:")
            for file_info in cli_result['outputs']['files']:
                file_path = file_info['path']
                file_size = file_info['size_bytes']
                response_parts.append(f"  📄 {file_path} ({file_size} bytes)")
            response_parts.append("")

        response_parts.extend([
            "💡 推奨アクション:",
            "1. 生成されたレポートファイルを確認してください",
            "2. 高優先度の問題から順番に対応してください",
            "3. 修正後、再度品質チェックを実行してください"
        ])

        return types.TextContent(
            type="text",
            text="\n".join(response_parts)
        )
```

## 5. MCP Server実装

### 5.1 Main Server Class

```python
# scripts/infrastructure/mcp/novel_mcp_server.py
import logging
from typing import Any, Dict, List, Optional, Sequence
from pathlib import Path

from mcp import Server, types
from mcp.server.models import InitializationOptions

from .tools.episode_creation_tool import EpisodeCreationTool
from .tools.quality_check_tool import QualityCheckTool
from .tools.plot_generation_tool import PlotGenerationTool
from .tools.project_status_tool import ProjectStatusTool
from .tools.file_management_tool import FileManagementTool
from .resources.file_resource_handler import FileResourceHandler
from .resources.config_resource_handler import ConfigResourceHandler

class NovelMCPServer:
    """小説執筆支援 MCP サーバー"""

    def __init__(self,
                 project_root: Path = None,
                 cli_script_path: Path = None,
                 output_dir: Path = None):

        self.project_root = project_root or Path.cwd()
        self.output_dir = output_dir or self.project_root / "mcp_outputs"

        # MCPサーバー初期化
        self.server = Server("novel-writing-cli-wrapper")

        # ツール初期化
        self.episode_tool = EpisodeCreationTool(
            cli_script_path=cli_script_path,
            output_dir=self.output_dir
        )
        self.quality_tool = QualityCheckTool(
            cli_script_path=cli_script_path,
            output_dir=self.output_dir
        )
        self.plot_tool = PlotGenerationTool(
            cli_script_path=cli_script_path,
            output_dir=self.output_dir
        )
        self.status_tool = ProjectStatusTool(
            cli_script_path=cli_script_path,
            output_dir=self.output_dir
        )
        self.file_tool = FileManagementTool(
            cli_script_path=cli_script_path,
            output_dir=self.output_dir
        )

        # リソースハンドラー初期化
        self.file_resource_handler = FileResourceHandler(self.output_dir)
        self.config_resource_handler = ConfigResourceHandler(self.project_root)

        # ツール・リソース登録
        self._register_tools()
        self._register_resources()

        # ロギング設定
        self._setup_logging()

    def _register_tools(self) -> None:
        """ツール登録"""

        @self.server.call_tool()
        async def create_episode(arguments: Dict[str, Any]) -> types.TextContent:
            """エピソード作成ツール"""
            return await self.episode_tool.execute(arguments)

        @self.server.call_tool()
        async def quality_check(arguments: Dict[str, Any]) -> types.TextContent:
            """品質チェックツール"""
            return await self.quality_tool.execute(arguments)

        @self.server.call_tool()
        async def generate_plot(arguments: Dict[str, Any]) -> types.TextContent:
            """プロット生成ツール"""
            return await self.plot_tool.execute(arguments)

        @self.server.call_tool()
        async def get_project_status(arguments: Dict[str, Any]) -> types.TextContent:
            """プロジェクト状況ツール"""
            return await self.status_tool.execute(arguments)

        @self.server.call_tool()
        async def manage_files(arguments: Dict[str, Any]) -> types.TextContent:
            """ファイル管理ツール"""
            return await self.file_tool.execute(arguments)

    def _register_resources(self) -> None:
        """リソース登録"""

        @self.server.list_resources()
        async def list_resources() -> List[types.Resource]:
            """利用可能リソース一覧"""
            resources = []

            # 生成ファイルリソース
            resources.extend(await self.file_resource_handler.list_resources())

            # 設定リソース
            resources.extend(await self.config_resource_handler.list_resources())

            return resources

        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """リソース読み込み"""

            if uri.startswith("file://generated/"):
                return await self.file_resource_handler.read_resource(uri)
            elif uri.startswith("config://"):
                return await self.config_resource_handler.read_resource(uri)
            else:
                raise ValueError(f"未サポートのリソースURI: {uri}")

    def _setup_logging(self) -> None:
        """ロギング設定"""

        log_file = self.project_root / "logs" / "mcp_server.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

        self.logger = logging.getLogger(__name__)

        @self.server.set_logging_level()
        async def set_logging_level(level: types.LoggingLevel) -> None:
            """ログレベル設定"""
            log_levels = {
                types.LoggingLevel.DEBUG: logging.DEBUG,
                types.LoggingLevel.INFO: logging.INFO,
                types.LoggingLevel.NOTICE: logging.INFO,
                types.LoggingLevel.WARNING: logging.WARNING,
                types.LoggingLevel.ERROR: logging.ERROR,
                types.LoggingLevel.CRITICAL: logging.CRITICAL,
                types.LoggingLevel.ALERT: logging.CRITICAL,
                types.LoggingLevel.EMERGENCY: logging.CRITICAL,
            }

            logging.getLogger().setLevel(log_levels.get(level, logging.INFO))
            self.logger.info(f"ログレベル変更: {level}")

    async def run(self, transport) -> None:
        """サーバー実行"""
        self.logger.info("Novel MCP Server 起動中...")

        async with self.server.create_session(
            transport,
            InitializationOptions(
                server_name="novel-writing-cli-wrapper",
                server_version="1.0.0"
            )
        ) as session:
            self.logger.info("MCP セッション開始")
            await session.run()
```

## 6. 利用例・統合方法

### 6.1 Claude Desktop統合設定

```json
{
  "mcpServers": {
    "novel-writing-cli-wrapper": {
      "command": "python",
      "args": ["/path/to/novel-writing-system/scripts/infrastructure/mcp/run_server.py"],
      "env": {
        "PROJECT_ROOT": "/path/to/your/novel/project",
        "CLI_SCRIPT_PATH": "/path/to/novel-writing-system/bin/novel",
        "OUTPUT_DIR": "/path/to/outputs",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### 6.2 使用例

#### エピソード作成

```
LLMプロンプト:
"第5話「謎の手紙」をファンタジージャンル、三人称視点で主人公アリス中心に2000文字で作成してください"

MCPツール実行:
create_episode({
  "episode_number": 5,
  "title": "謎の手紙",
  "genre": "fantasy",
  "word_count_target": 2000,
  "viewpoint": "third_person",
  "viewpoint_character": "アリス"
})
```

#### 品質チェック

```
LLMプロンプト:
"第1-5話の文法と一貫性をチェックして、改善提案も含めて詳細レポートを作成してください"

MCPツール実行:
quality_check({
  "target_files": ["episodes/第001話.md", "episodes/第002話.md", "episodes/第003話.md", "episodes/第004話.md", "episodes/第005話.md"],
  "check_types": ["grammar", "consistency"],
  "include_suggestions": true,
  "output_format": "detailed"
})
```

#### プロジェクト状況確認

```
LLMプロンプト:
"現在のプロジェクト全体の進捗状況と品質メトリクスを教えてください"

MCPツール実行:
get_project_status({
  "include_metrics": true,
  "include_quality_summary": true,
  "date_range_days": 30
})
```

## 7. エラーハンドリング・ロギング

### 7.1 エラー分類

```python
MCP_ERROR_CODES = {
    # ツール実行エラー
    "TOOL_EXECUTION_ERROR": "ツール実行エラー",
    "TOOL_TIMEOUT_ERROR": "ツール実行タイムアウト",
    "TOOL_VALIDATION_ERROR": "ツール入力バリデーションエラー",

    # CLI統合エラー
    "CLI_NOT_FOUND": "CLI実行ファイル未発見",
    "CLI_PERMISSION_ERROR": "CLI実行権限エラー",
    "CLI_RESPONSE_PARSE_ERROR": "CLIレスポンス解析エラー",

    # リソースエラー
    "RESOURCE_NOT_FOUND": "リソース未発見",
    "RESOURCE_READ_ERROR": "リソース読み込みエラー",
    "RESOURCE_PERMISSION_ERROR": "リソースアクセス権限エラー",

    # システムエラー
    "MCP_SERVER_ERROR": "MCPサーバーエラー",
    "UNEXPECTED_ERROR": "予期しないエラー"
}
```

### 7.2 ログ形式

```python
# ログエントリ例
{
    "timestamp": "2025-08-27T12:34:56.789Z",
    "level": "INFO",
    "source": "novel_mcp_server",
    "tool_name": "create_episode",
    "operation_id": "550e8400-e29b-41d4-a716-446655440000",
    "arguments": {
        "episode_number": 5,
        "title": "謎の手紙"
    },
    "execution_time_ms": 15420.5,
    "result": {
        "success": true,
        "files_generated": 2,
        "total_output_size": 4096
    },
    "session_id": "mcp_session_123",
    "user_agent": "Claude Desktop/1.0"
}
```

## 8. セキュリティ考慮事項

### 8.1 入力サニタイゼーション

- **パスインジェクション防止**: 相対パスのみ許可、`..`文字列禁止
- **コマンドインジェクション防止**: 引数のエスケープ処理
- **ファイルサイズ制限**: 最大100MB、大容量ファイル攻撃防止

### 8.2 権限制御

- **プロジェクト内アクセス限定**: `project_root`以外へのアクセス禁止
- **実行可能ファイル制限**: 事前定義されたCLIのみ実行許可
- **リソース読み込み制限**: 許可されたパターンのファイルのみアクセス可能

### 8.3 監査ログ

- **全操作記録**: ツール実行・リソースアクセス・エラー発生の完全ログ
- **ハッシュ値検証**: ファイル完全性の暗号学的保証
- **セッション追跡**: MCPセッション全体の操作履歴管理

---

**注意**: 本API仕様書はアーキテクチャ仕様書・技術仕様書・実装ガイドと連携して使用してください。
