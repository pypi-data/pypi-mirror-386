#!/usr/bin/env python3
"""CLI レスポンス→JSON変換器"""

import json
from pathlib import Path
from typing import Any

from noveler.domain.value_objects.project_time import project_now
from noveler.infrastructure.json.converters.base_converter import BaseConverter
from noveler.infrastructure.json.file_managers.file_reference_manager import FileReferenceManager
from noveler.infrastructure.json.models.file_reference_models import FileReferenceCollection
from noveler.infrastructure.json.models.response_models import (
    ErrorDetailModel,
    ErrorResponseModel,
    StandardResponseModel,
)


class CLIResponseConverter(BaseConverter):
    """CLI レスポンス→JSON変換器"""

    def __init__(
        self,
        schema_dir: Path | None = None,
        output_dir: Path | None = None,
        validate_schema: bool = True
    ) -> None:
        super().__init__(schema_dir, output_dir, validate_schema)
        self.file_manager = FileReferenceManager(self.output_dir)

    def convert(self, cli_result: dict[str, Any]) -> dict[str, Any]:
        """CLI実行結果をJSON形式に変換"""

        start_time = project_now().datetime

        try:
            if cli_result.get("success", False):
                result = self._convert_success_response(cli_result)
            else:
                result = self._convert_error_response(cli_result)

            # 実行時間追加（存在しない場合のみ）
            if "execution_time_ms" not in result:
                end_time = project_now().datetime
                result["execution_time_ms"] = (end_time - start_time).total_seconds() * 1000

            return result

        except Exception as e:
            return self._create_emergency_error_response(str(e), cli_result)

    def _convert_success_response(self, cli_result: dict[str, Any]) -> dict[str, Any]:
        """成功レスポンス変換"""

        file_references = []

        # コンテンツをファイル参照に変換
        if "content" in cli_result:
            file_ref = self.file_manager.save_content(
                content=cli_result["content"],
                content_type="text/markdown",
                filename_prefix=cli_result.get("command", "output").replace(" ", "_"),
            )
            file_references.append(file_ref)

        if "yaml_content" in cli_result:
            file_ref = self.file_manager.save_content(
                content=cli_result["yaml_content"],
                content_type="text/yaml",
                filename_prefix=f"{cli_result.get('command', 'output').replace(' ', '_')}_config",
            )
            file_references.append(file_ref)

        if "json_data" in cli_result:
            file_ref = self.file_manager.save_content(
                content=json.dumps(cli_result["json_data"], ensure_ascii=False, indent=2),
                content_type="application/json",
                filename_prefix=f"{cli_result.get('command', 'output').replace(' ', '_')}_data",
            )
            file_references.append(file_ref)

        # FileReferenceCollectionモデル作成
        file_collection = FileReferenceCollection(
            files=file_references,
            total_files=len(file_references),
            total_size_bytes=sum(f.size_bytes for f in file_references),
        )

        # StandardResponseModel作成・バリデーション
        response_data = {
            "success": True,
            "command": cli_result.get("command", "unknown"),
            "execution_time_ms": cli_result.get("execution_time_ms", 0.0),
            "outputs": file_collection.model_dump(),
            "metadata": self._extract_metadata(cli_result),
            "created_at": project_now().datetime,
        }

        response_model = StandardResponseModel(**response_data)
        return response_model.model_dump()

    def _convert_error_response(self, cli_result: dict[str, Any]) -> dict[str, Any]:
        """エラーレスポンス変換"""

        error_detail = ErrorDetailModel(
            code=cli_result.get("error_code", "UNKNOWN_ERROR"),
            message=cli_result.get("error_message", "不明なエラーが発生しました"),
            hint=cli_result.get("error_hint", "ログを確認し、必要に応じてサポートに連絡してください"),
            details=cli_result.get("error_details", {}),
            stack_trace=cli_result.get("stack_trace") if cli_result.get("debug_mode") else None,
        )

        error_data = {
            "success": False,
            "error": error_detail.model_dump(),
            "command": cli_result.get("command", "unknown"),
            "created_at": project_now().datetime,
        }

        # ErrorResponseModel作成・バリデーション
        error_model = ErrorResponseModel(**error_data)
        return error_model.model_dump()

    def _extract_metadata(self, cli_result: dict[str, Any]) -> dict[str, Any]:
        """メタデータ抽出"""
        metadata_keys = [
            "session_id",
            "user_id",
            "project_id",
            "environment",
            "version",
            "git_commit",
            "performance_metrics",
            "word_count",
            "character_count",
            "quality_score",
        ]

        metadata = {}

        # トップレベルからメタデータキーを抽出
        for key in metadata_keys:
            if key in cli_result:
                metadata[key] = cli_result[key]

        # 'metadata'キー内からも抽出
        if "metadata" in cli_result and isinstance(cli_result["metadata"], dict):
            for key in metadata_keys:
                if key in cli_result["metadata"]:
                    metadata[key] = cli_result["metadata"][key]

        return metadata

    def _create_emergency_error_response(self, error_msg: str, original_data: dict) -> dict[str, Any]:
        """緊急エラーレスポンス生成"""
        return {
            "success": False,
            "error": {
                "code": "CONVERTER_ERROR",
                "message": f"JSON変換中にエラーが発生しました: {error_msg}",
                "hint": "開発者に連絡してください。原因調査のため元データを保存しています。",
                "details": {"original_data_keys": list(original_data.keys()), "conversion_error": error_msg},
            },
            "command": original_data.get("command", "unknown"),
            "created_at": project_now().datetime.isoformat(),
        }
