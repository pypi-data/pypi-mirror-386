"""Infrastructure.json.mcp.integrations.claude_code_bridge
Where: Infrastructure module bridging JSON MCP integrations with Claude Code.
What: Handles JSON payloads, wiring, and session management for Claude MCP.
Why: Enables Claude Code integrations to communicate via JSON MCP protocols.
"""

from noveler.infrastructure.logging.unified_logger import get_logger
from noveler.presentation.shared.shared_utilities import console

"Claude Code MCP統合ブリッジ"
import asyncio
import sys
from pathlib import Path
from typing import Any

from noveler.infrastructure.json.mcp.servers.json_conversion_server import JSONConversionServer


class ClaudeCodeMCPBridge:
    """Claude Code MCP統合ブリッジクラス"""

    def __init__(self, output_dir: Path | None = None) -> None:
        self.output_dir = output_dir or Path.cwd() / "temp" / "json_output"
        self.mcp_server: JSONConversionServer | None = None
        self.logger = get_logger(__name__)

    async def initialize_server(self) -> bool:
        """MCPサーバー初期化"""
        try:
            self.mcp_server = JSONConversionServer(self.output_dir)
            console.print("MCPサーバー初期化完了")
            return True
        except Exception:
            self.logger.exception("MCPサーバー初期化失敗")
            return False

    async def handle_stdio_communication(self) -> None:
        """stdio通信処理（Claude Code標準）"""
        if not self.mcp_server:
            msg = "MCPサーバーが初期化されていません"
            raise ValueError(msg)
        try:
            await self.mcp_server.run()
        except KeyboardInterrupt:
            console.print("MCPサーバーが停止されました")
        except Exception:
            self.logger.exception("stdio通信エラー")
            raise

    def get_server_capabilities(self) -> dict[str, Any]:
        """サーバー機能情報取得"""
        return {
            "name": "novel-json-converter",
            "version": "1.0.0",
            "description": "小説執筆支援システム JSON変換・MCP統合サーバー",
            "tools": [
                {
                    "name": "convert_cli_to_json",
                    "description": "CLI実行結果をJSON形式に変換（95%トークン削減）",
                    "parameters": {"cli_result": "CLI実行結果データ", "output_config": "出力設定（オプション）"},
                },
                {
                    "name": "validate_json_response",
                    "description": "JSON応答形式の検証",
                    "parameters": {"json_data": "検証対象JSONデータ"},
                },
                {
                    "name": "get_file_content_by_reference",
                    "description": "ファイル参照からコンテンツ取得（完全性チェック付き）",
                    "parameters": {"file_reference": "ファイル参照オブジェクト"},
                },
                {
                    "name": "list_output_files",
                    "description": "出力ファイル一覧取得",
                    "parameters": {"pattern": "ファイルパターン（オプション）"},
                },
                {
                    "name": "cleanup_old_files",
                    "description": "古いファイル削除",
                    "parameters": {"max_age_days": "保持日数"},
                },
            ],
            "features": {
                "token_reduction": "95%",
                "file_integrity": "SHA256検証",
                "pydantic_validation": "v2対応",
                "async_support": True,
                "stdio_compatible": True,
            },
        }

    async def process_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """ツール呼び出し処理"""
        if not self.mcp_server:
            return {"success": False, "error": "MCPサーバーが初期化されていません"}
        try:
            return await self.mcp_server.execute_tool_async(tool_name, arguments)
        except Exception as e:
            self.logger.exception("ツール実行エラー [%s]", tool_name)
            return {"success": False, "error": f"ツール実行失敗: {e!s}"}

    def validate_configuration(self) -> dict[str, Any]:
        """設定検証"""
        validation_result = {"valid": True, "checks": [], "errors": []}
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            validation_result["checks"].append(
                {"name": "output_directory", "status": "OK", "path": str(self.output_dir)}
            )
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"出力ディレクトリエラー: {e}")
        try:
            import pydantic

            validation_result["checks"].append({"name": "pydantic", "status": "OK", "version": pydantic.VERSION})
        except ImportError:
            validation_result["valid"] = False
            validation_result["errors"].append("Pydantic v2が必要です")
        try:
            import importlib.util

            if importlib.util.find_spec("mcp") is not None:
                validation_result["checks"].append({"name": "mcp", "status": "OK"})
            else:
                msg = "mcp not found"
                raise ImportError(msg)
        except ImportError:
            validation_result["valid"] = False
            validation_result["errors"].append("MCPライブラリが必要です")
        return validation_result


async def run_claude_code_mcp_server(output_dir: Path | None = None) -> int:
    """Claude Code MCP サーバー実行"""
    bridge = ClaudeCodeMCPBridge(output_dir)
    validation = bridge.validate_configuration()
    if not validation["valid"]:
        console.print(f"設定エラー: {validation['errors']}", file=sys.stderr)
        return 1
    if not await bridge.initialize_server():
        console.print("MCPサーバー初期化失敗", file=sys.stderr)
        return 1
    try:
        await bridge.handle_stdio_communication()
        return 0
    except Exception as e:
        console.print(f"MCP通信エラー: {e}", file=sys.stderr)
        return 1


def main():
    """メイン実行（asyncio対応）"""
    import argparse

    parser = argparse.ArgumentParser(description="Claude Code MCP統合ブリッジ")
    parser.add_argument(
        "-o", "--output-dir", type=Path, default=Path.cwd() / "temp" / "json_output", help="出力ディレクトリ"
    )
    args = parser.parse_args()
    try:
        exit_code = asyncio.run(run_claude_code_mcp_server(args.output_dir))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        console.print("MCPサーバーが停止されました")
        sys.exit(0)


if __name__ == "__main__":
    main()
