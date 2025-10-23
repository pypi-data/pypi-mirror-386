#!/usr/bin/env python3
"""JSON変換ツールMCPラッピング"""


from datetime import datetime
from pathlib import Path
from typing import Any

from noveler.domain.value_objects.project_time import project_now
from noveler.infrastructure.json.converters.cli_response_converter import CLIResponseConverter
from noveler.infrastructure.json.file_managers.file_reference_manager import FileReferenceManager
from noveler.infrastructure.json.models.response_models import ErrorResponseModel, StandardResponseModel


class JSONToolWrapper:
    """JSON変換ツールのMCPラッピング層"""

    def __init__(self, output_dir: Path | None = None) -> None:
        self.output_dir = output_dir or Path.cwd() / "temp" / "json_output"
        self.converter = CLIResponseConverter(output_dir=self.output_dir)
        self.file_manager = FileReferenceManager(self.output_dir)
        # logger_service経由で注入

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """MCPツール定義リスト取得"""
        return [
            {
                "name": "convert_cli_to_json",
                "description": "CLI実行結果をJSON形式に変換し、ファイル参照として保存",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "cli_result": {"type": "object", "description": "CLI実行結果オブジェクト", "required": True},
                        "output_prefix": {
                            "type": "string",
                            "description": "出力ファイル名プレフィックス",
                            "default": "cli_output",
                        },
                    },
                    "required": ["cli_result"],
                },
            },
            {
                "name": "validate_json_response",
                "description": "JSON レスポンス形式の Pydantic バリデーション",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "json_data": {"type": "object", "description": "検証対象JSONデータ", "required": True}
                    },
                    "required": ["json_data"],
                },
            },
            {
                "name": "get_file_content_by_reference",
                "description": "ファイル参照からコンテンツ読み込み（完全性チェック付き）",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_reference": {
                            "type": "object",
                            "description": "FileReferenceModelオブジェクト",
                            "required": True,
                        }
                    },
                    "required": ["file_reference"],
                },
            },
            {
                "name": "list_output_files",
                "description": "出力ディレクトリ内のファイル一覧取得",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string", "description": "ファイル名パターン（glob形式）", "default": "*"}
                    },
                },
            },
            {
                "name": "cleanup_old_files",
                "description": "古い出力ファイルの削除",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "max_age_days": {
                            "type": "integer",
                            "description": "保持期間（日数）",
                            "default": 30,
                            "minimum": 1,
                        }
                    },
                },
            },
        ]

    def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """ツール実行"""
        try:
            if tool_name == "convert_cli_to_json":
                return self._convert_cli_to_json(arguments)
            if tool_name == "validate_json_response":
                return self._validate_json_response(arguments)
            if tool_name == "get_file_content_by_reference":
                return self._get_file_content_by_reference(arguments)
            if tool_name == "list_output_files":
                return self._list_output_files(arguments)
            if tool_name == "cleanup_old_files":
                return self._cleanup_old_files(arguments)
            return self._create_error_result(f"未知のツール: {tool_name}", "UNKNOWN_TOOL")

        except Exception as e:
            # logger未初期化の場合のフォールバック
            return self._create_error_result(f"ツール実行エラー: {e!s}", "TOOL_EXECUTION_ERROR")

    def _convert_cli_to_json(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """CLI→JSON変換実行"""
        cli_result = arguments.get("cli_result", {})
        if not cli_result:
            return self._create_error_result("cli_resultパラメータが必要です", "MISSING_PARAMETER")

        # JSON変換実行
        json_result = self.converter.convert(cli_result)

        return {
            "success": True,
            "result": json_result,
            "message": "CLI→JSON変換が完了しました",
            "execution_time": json_result.get("execution_time_ms", 0),
            "output_files": json_result.get("outputs", {}).get("total_files", 0),
        }

    def _validate_json_response(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """JSON レスポンス検証実行"""
        json_data = arguments.get("json_data", {})
        if not json_data:
            return self._create_error_result("json_dataパラメータが必要です", "MISSING_PARAMETER")

        try:
            # モデル選択・バリデーション
            if json_data.get("success", False):
                StandardResponseModel(**json_data)
                model_type = "StandardResponseModel"
            else:
                ErrorResponseModel(**json_data)
                model_type = "ErrorResponseModel"

            return {
                "success": True,
                "result": {"valid": True, "model_type": model_type, "validated_at": project_now().datetime.isoformat()},
                "message": f"JSON形式検証成功: {model_type}",
            }

        except Exception as e:
            return {
                "success": False,
                "result": {"valid": False, "validation_errors": str(e)},
                "message": f"JSON形式検証失敗: {e!s}",
            }

    def _get_file_content_by_reference(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """ファイル参照からコンテンツ読み込み"""
        file_reference_data = arguments.get("file_reference", {})
        if not file_reference_data:
            return self._create_error_result("file_referenceパラメータが必要です", "MISSING_PARAMETER")

        try:
            # FileReferenceModelオブジェクト作成
            from noveler.infrastructure.json.models.file_reference_models import FileReferenceModel

            file_reference = FileReferenceModel(**file_reference_data)

            # コンテンツ読み込み（完全性チェック付き）
            content = self.file_manager.load_file_content(file_reference)

            return {
                "success": True,
                "result": {
                    "content": content,
                    "file_path": file_reference.path,
                    "content_type": file_reference.content_type,
                    "size_bytes": file_reference.size_bytes,
                    "sha256_verified": True,
                },
                "message": f"ファイル読み込み成功: {file_reference.path}",
            }

        except ValueError as e:
            return self._create_error_result(f"ファイル完全性エラー: {e!s}", "FILE_INTEGRITY_ERROR")
        except Exception as e:
            return self._create_error_result(f"ファイル読み込みエラー: {e!s}", "FILE_READ_ERROR")

    def _list_output_files(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """出力ファイル一覧取得"""
        pattern = arguments.get("pattern", "*")

        try:
            files = []
            for file_path in self.output_dir.glob(pattern):
                if file_path.is_file():
                    stat = file_path.stat()
                    files.append(
                        {
                            "name": file_path.name,
                            "path": str(file_path.relative_to(self.output_dir)),
                            "size_bytes": stat.st_size,
                            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        }
                    )

            return {
                "success": True,
                "result": {"files": files, "total_files": len(files), "pattern": pattern},
                "message": f"{len(files)}個のファイルが見つかりました",
            }

        except Exception as e:
            return self._create_error_result(f"ファイル一覧取得エラー: {e!s}", "FILE_LIST_ERROR")

    def _cleanup_old_files(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """古いファイル削除"""
        max_age_days = arguments.get("max_age_days", 30)

        try:
            deleted_files = self.file_manager.cleanup_old_files(max_age_days)

            return {
                "success": True,
                "result": {
                    "deleted_files": deleted_files,
                    "total_deleted": len(deleted_files),
                    "max_age_days": max_age_days,
                },
                "message": f"{len(deleted_files)}個の古いファイルを削除しました",
            }

        except Exception as e:
            return self._create_error_result(f"ファイル削除エラー: {e!s}", "FILE_CLEANUP_ERROR")

    def _create_error_result(self, message: str, error_code: str) -> dict[str, Any]:
        """エラー結果生成"""
        return {
            "success": False,
            "error": {"code": error_code, "message": message, "timestamp": project_now().datetime.isoformat()},
            "message": message,
        }
