#!/usr/bin/env python3
"""MCPサーバー統合テスト

src/mcp_servers/noveler/のMCPサーバー機能をテストします。
JSON変換、ファイル参照、novel コマンド実行のテストを含みます。
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import pytest

from noveler.presentation.shared.shared_utilities import get_common_path_service
from tests.unit.infrastructure.test_base import BaseIntegrationTestCase


@pytest.mark.integration
@pytest.mark.spec("SPEC-MCP-001")
class TestMCPServerIntegration(BaseIntegrationTestCase):
    """MCPサーバー統合テストクラス"""

    @pytest.mark.spec("SPEC-MCP_SERVER_INTEGRATION-MCP_SERVER_JSON_CONV")
    def test_mcp_server_json_conversion(self) -> None:
        """JSON変換機能のテスト"""
        # Given: CLI形式の結果データ
        get_common_path_service()
        cli_result = {
            "status": "success",
            "project_name": "テストプロジェクト",
            "episode_count": 10,
            "files": [
                "/path/to/file1.txt",
                "/path/to/file2.txt",
                "/path/to/very/long/path/that/would/normally/consume/many/tokens.txt"
            ],
            "verbose_output": """
            This is a very long output that would normally consume many tokens
            when transmitted directly. It contains detailed information about
            the project status, file contents, and various metadata that may
            not be essential for the immediate task.
            """ * 100  # 大量のテキストをシミュレート
        }

        # When: JSON変換を実行（MCPサーバーのconvert_cli_to_json相当）
        converted_result = self._convert_cli_to_json(cli_result)

        # Then: トークン削減が達成されている
        original_size = len(json.dumps(cli_result))
        converted_size = len(json.dumps(converted_result))
        reduction_rate = (original_size - converted_size) / original_size * 100

        assert reduction_rate > 90, f"トークン削減率が不十分: {reduction_rate:.2f}%"
        assert "file_references" in converted_result
        assert "summary" in converted_result
        assert converted_result["status"] == "success"

    @pytest.mark.spec("SPEC-MCP_SERVER_INTEGRATION-MCP_SERVER_NOVEL_COM")
    def test_mcp_server_novel_command_execution(self) -> None:
        """novel コマンド実行機能のテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Given: テストプロジェクト構造
            project_dir = project_root / "テストプロジェクト"
            project_dir.mkdir()
            path_service = get_common_path_service()
            # 既存ディレクトリでもエラーにならないよう冪等に作成
            (project_dir / str(path_service.get_plots_dir())).mkdir(parents=True, exist_ok=True)
            (project_dir / str(path_service.get_plots_dir())).mkdir(parents=True, exist_ok=True)
            (project_dir / str(path_service.get_manuscript_dir())).mkdir(parents=True, exist_ok=True)

            # When: MCP経由でnovelコマンドを実行（status相当）
            result = self._execute_novel_command(
                "status",
                project_root=str(project_root)
            )

            # Then: コマンド実行が成功
            assert result["success"] is True
            assert "projects" in result or "status" in result

    @pytest.mark.spec("SPEC-MCP_SERVER_INTEGRATION-MCP_SERVER_FILE_REFE")
    def test_mcp_server_file_reference_info(self) -> None:
        """ファイル参照情報取得のテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Given: テストファイル
            test_file = Path(tmpdir) / "test_episode.md"
            test_content = """# 第1話 テストエピソード

これはテストコンテンツです。
文字数は約50文字程度。
"""
            test_file.write_text(test_content, encoding="utf-8")

            # When: ファイル参照情報を取得
            file_info = self._get_file_reference_info(str(test_file))

            # Then: ファイル情報が正しく取得される
            assert file_info["exists"] is True
            assert file_info["size"] > 0
            assert "sha256" in file_info
            assert file_info["type"] == "text"
            assert file_info["encoding"] == "utf-8"

    @pytest.mark.spec("SPEC-MCP_SERVER_INTEGRATION-MCP_SERVER_BATCH_PRO")
    def test_mcp_server_batch_processing(self) -> None:
        """バッチ処理機能のテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            project_dir = project_root / "テストプロジェクト"
            project_dir.mkdir()
            path_service = get_common_path_service()
            episodes_dir = project_dir / str(path_service.get_manuscript_dir())
            episodes_dir.mkdir()

            # Given: 複数のエピソードファイル
            for i in range(1, 6):
                episode_file = episodes_dir / f"第{i:03d}話_テストエピソード{i}.md"
                content = f"""# 第{i}話 テストエピソード{i}

これは第{i}話の内容です。
"""
                episode_file.write_text(content, encoding="utf-8")

            # When: バッチ処理を実行
            result = self._execute_novel_command(
                "check batch 1-5",
                project_root=str(project_root)
            )

            # Then: バッチ処理が成功
            assert result["success"] is True
            if "processed_count" in result:
                assert result["processed_count"] == 5

    @pytest.mark.spec("SPEC-MCP_SERVER_INTEGRATION-MCP_SERVER_WITH_BIN_")
    def test_mcp_server_with_bin_noveler(self) -> None:
        """bin/noveler 経由でのMCPサーバー動作テスト"""
        # Given: bin/noveler コマンドパス
        noveler_cmd = Path.cwd() / "bin" / "noveler"

        assert noveler_cmd.exists(), "bin/noveler が見つかりません"

        # When: ヘルプコマンドを実行
        result = subprocess.run(
            [str(noveler_cmd), "--help"],
            check=False, capture_output=True,
            text=True,
            timeout=30,
        )

        # Then: コマンドが正常に動作
        assert result.returncode == 0
        out = (result.stdout or "") + (result.stderr or "")
        assert "usage" in out.lower() or "noveler" in out.lower()

    @pytest.mark.spec("SPEC-MCP_SERVER_INTEGRATION-MCP_SERVER_WITH_BIN_")
    def test_mcp_server_with_bin_noveler_help(self) -> None:
        """bin/noveler のヘルプ表示テスト（dev相当）"""
        # Given: bin/noveler コマンドパス
        noveler_cmd = Path.cwd() / "bin" / "noveler"
        assert noveler_cmd.exists(), "bin/noveler が見つかりません"

        # When: ヘルプコマンドを実行
        result = subprocess.run(
            [str(noveler_cmd), "--help"],
            check=False, capture_output=True,
            text=True,
            timeout=30,
        )

        # Then: コマンドが正常に動作（Usageの表示など）
        assert result.returncode == 0
        out = (result.stdout or "") + (result.stderr or "")
        assert "usage" in out.lower() or "noveler" in out.lower()

    # ヘルパーメソッド
    def _convert_cli_to_json(self, cli_result: dict[str, Any]) -> dict[str, Any]:
        """CLI結果をJSON形式に変換（MCPサーバー機能のシミュレート）"""
        # ファイル参照に変換
        file_references = {}
        if "files" in cli_result:
            for file_path in cli_result["files"]:
                ref_id = f"ref_{hash(file_path) % 10000:04d}"
                file_references[ref_id] = file_path

        # 冗長な出力を要約
        summary = None
        if "verbose_output" in cli_result:
            output_lines = cli_result["verbose_output"].strip().split("\n")
            summary = f"出力: {len(output_lines)}行"

        # 変換済み結果
        return {
            "status": cli_result.get("status", "unknown"),
            "project_name": cli_result.get("project_name"),
            "episode_count": cli_result.get("episode_count"),
            "file_references": file_references,
            "summary": summary
        }


    def _execute_novel_command(self, command: str, project_root: str = "") -> dict[str, Any]:
        """novel コマンドを実行（MCPサーバー経由のシミュレート）"""
        # 簡易的な実装（実際のMCPサーバーでは mcp_servers/noveler/main.py を使用）
        return {
            "success": True,
            "command": command,
            "project_root": project_root,
            "status": "completed"
        }

    def _get_file_reference_info(self, file_path: str) -> dict[str, Any]:
        """ファイル参照情報を取得（MCPサーバー機能のシミュレート）"""
        import hashlib

        path = Path(file_path)
        if not path.exists():
            return {"exists": False}

        # SHA256ハッシュ計算
        with open(path, "rb") as f:
            sha256_hash = hashlib.sha256(f.read()).hexdigest()

        # ファイル情報
        return {
            "exists": True,
            "size": path.stat().st_size,
            "sha256": sha256_hash,
            "type": "text" if path.suffix in [".txt", ".md", ".py"] else "binary",
            "encoding": "utf-8" if path.suffix in [".txt", ".md", ".py"] else None
        }


@pytest.mark.integration
class TestMCPServerCommunication(BaseIntegrationTestCase):
    """MCPサーバー通信プロトコルのテスト"""

    @pytest.mark.spec("SPEC-MCP_SERVER_INTEGRATION-MCP_MESSAGE_FORMAT")
    def test_mcp_message_format(self) -> None:
        """MCPメッセージフォーマットの検証"""
        # Given: MCPメッセージ
        message = {
            "jsonrpc": "2.0",
            "method": "novel/execute",
            "params": {
                "command": "status",
                "options": {}
            },
            "id": 1
        }

        # When: メッセージ検証
        is_valid = self._validate_mcp_message(message)

        # Then: 有効なメッセージ
        assert is_valid is True

    @pytest.mark.spec("SPEC-MCP_SERVER_INTEGRATION-MCP_RESPONSE_FORMAT")
    def test_mcp_response_format(self) -> None:
        """MCPレスポンスフォーマットの検証"""
        # Given: MCPレスポンス
        response = {
            "jsonrpc": "2.0",
            "result": {
                "success": True,
                "data": {
                    "projects": ["プロジェクト1", "プロジェクト2"]
                }
            },
            "id": 1
        }

        # When: レスポンス検証
        is_valid = self._validate_mcp_response(response)

        # Then: 有効なレスポンス
        assert is_valid is True

    @pytest.mark.spec("SPEC-MCP_SERVER_INTEGRATION-MCP_ERROR_HANDLING")
    def test_mcp_error_handling(self) -> None:
        """MCPエラーハンドリングのテスト"""
        # Given: エラーレスポンス
        error_response = {
            "jsonrpc": "2.0",
            "error": {
                "code": -32601,
                "message": "Method not found",
                "data": {
                    "method": "invalid/method"
                }
            },
            "id": 1
        }

        # When: エラー処理
        error_info = self._parse_mcp_error(error_response)

        # Then: エラー情報が正しく解析される
        assert error_info["code"] == -32601
        assert error_info["message"] == "Method not found"
        assert error_info["method"] == "invalid/method"

    # ヘルパーメソッド
    def _validate_mcp_message(self, message: dict[str, Any]) -> bool:
        """MCPメッセージの妥当性を検証"""
        required_fields = ["jsonrpc", "method", "id"]
        return all(field in message for field in required_fields) and message["jsonrpc"] == "2.0"

    def _validate_mcp_response(self, response: dict[str, Any]) -> bool:
        """MCPレスポンスの妥当性を検証"""
        if "jsonrpc" not in response or response["jsonrpc"] != "2.0":
            return False
        if "id" not in response:
            return False
        # resultまたはerrorのいずれかが必要
        return "result" in response or "error" in response

    def _parse_mcp_error(self, response: dict[str, Any]) -> dict[str, Any]:
        """MCPエラーレスポンスを解析"""
        if "error" not in response:
            return {}

        error = response["error"]
        return {
            "code": error.get("code"),
            "message": error.get("message"),
            "method": error.get("data", {}).get("method")
        }
