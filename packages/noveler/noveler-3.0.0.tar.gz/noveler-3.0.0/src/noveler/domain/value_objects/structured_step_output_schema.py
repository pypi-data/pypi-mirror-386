"""構造化STEP出力JSONスキーマバリデーション

SPEC-JSON-001: JSON形式STEP間橋渡しシステムのスキーマバリデーション実装
JSONSchema形式による入力データの厳密なバリデーションを提供する。
"""

import json
from typing import Any, ClassVar

import jsonschema
from jsonschema import Draft7Validator


class StructuredStepOutputValidator:
    """構造化STEP出力バリデータ

    JSONスキーマベースの厳密なバリデーション機能を提供する。
    """

    # JSONスキーマ定義
    BRIDGE_DATA_SCHEMA: ClassVar[dict[str, Any]] = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "bridge_data": {
                "type": "object",
                "properties": {
                    "from_step": {
                        "type": "string",
                        "pattern": "^(STAGE_[A-Z_]+|STEP_\\d{2})$",
                        "description": "送信元STEP識別子",
                    },
                    "from_step_name": {"type": "string", "minLength": 1, "description": "送信元STEP名称"},
                    "to_step": {
                        "type": ["string", "null"],
                        "pattern": "^(STAGE_[A-Z_]+|STEP_\\d{2})$",
                        "description": "送信先STEP識別子（オプション）",
                    },
                    "completion_timestamp": {
                        "type": "string",
                        "format": "date-time",
                        "description": "完了タイムスタンプ（ISO形式）",
                    },
                    "completion_status": {
                        "type": "string",
                        "enum": ["completed", "partial", "failed", "skipped"],
                        "description": "完了ステータス",
                    },
                    "structured_results": {"type": "object", "description": "構造化された結果データ"},
                    "quality_metrics": {
                        "type": "object",
                        "properties": {
                            "overall_score": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0,
                                "description": "総合品質スコア",
                            }
                        },
                        "required": ["overall_score"],
                        "additionalProperties": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    },
                    "next_step_instructions": {
                        "type": "object",
                        "properties": {
                            "focus_areas": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "重点領域リスト",
                            },
                            "constraints": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "制約事項リスト",
                            },
                            "quality_threshold": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0,
                                "description": "品質閾値",
                            },
                            "specific_instructions": {"type": "object", "description": "具体的指示内容"},
                        },
                        "required": ["focus_areas", "constraints", "quality_threshold", "specific_instructions"],
                    },
                    "validation_status": {
                        "type": "object",
                        "properties": {
                            "passed": {"type": "boolean", "description": "バリデーション通過フラグ"},
                            "schema_version": {
                                "type": "string",
                                "pattern": "^\\d+\\.\\d+\\.\\d+$",
                                "description": "スキーマバージョン",
                            },
                        },
                        "required": ["passed", "schema_version"],
                    },
                },
                "required": [
                    "from_step",
                    "from_step_name",
                    "completion_timestamp",
                    "completion_status",
                    "structured_results",
                    "quality_metrics",
                    "next_step_instructions",
                    "validation_status",
                ],
            }
        },
        "required": ["bridge_data"],
    }

    STRUCTURED_DATA_SCHEMA: ClassVar[dict[str, Any]] = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "step_id": {"type": "string", "pattern": "^(STAGE_[A-Z_]+|STEP_\\d{2})$"},
            "step_name": {"type": "string", "minLength": 1},
            "completion_status": {"type": "string", "enum": ["completed", "partial", "failed", "skipped"]},
            "structured_data": {"type": "object"},
            "quality_metrics": {
                "type": "object",
                "properties": {
                    "overall_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "specific_metrics": {
                        "type": "object",
                        "additionalProperties": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    },
                },
                "required": ["overall_score", "specific_metrics"],
            },
            "next_step_context": {
                "type": "object",
                "properties": {
                    "focus_areas": {"type": "array", "items": {"type": "string"}},
                    "constraints": {"type": "array", "items": {"type": "string"}},
                    "quality_threshold": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "specific_instructions": {"type": "object"},
                },
                "required": ["focus_areas", "constraints", "quality_threshold", "specific_instructions"],
            },
            "validation_passed": {"type": "boolean"},
            "metadata": {"type": "object"},
        },
        "required": [
            "step_id",
            "step_name",
            "completion_status",
            "structured_data",
            "quality_metrics",
            "next_step_context",
            "validation_passed",
            "metadata",
        ],
    }

    def __init__(self) -> None:
        """バリデータ初期化"""
        self.bridge_validator = Draft7Validator(self.BRIDGE_DATA_SCHEMA)
        self.structured_validator = Draft7Validator(self.STRUCTURED_DATA_SCHEMA)

    def validate_bridge_json(self, json_data: str) -> tuple[bool, list[str]]:
        """橋渡しJSON形式のバリデーション

        Args:
            json_data: バリデーション対象のJSONデータ（文字列）

        Returns:
            tuple[bool, list[str]]: (バリデーション成功フラグ, エラーメッセージリスト)
        """
        try:
            # JSON解析
            data = json.loads(json_data)

            # スキーマバリデーション
            errors: list[Any] = list(self.bridge_validator.iter_errors(data))

            if errors:
                error_messages = [self._format_validation_error(error) for error in errors]
                return False, error_messages

            return True, []

        except json.JSONDecodeError as e:
            return False, [f"JSON解析エラー: {e!s}"]
        except Exception as e:
            return False, [f"バリデーション実行エラー: {e!s}"]

    def validate_structured_data(self, data_dict: dict[str, Any]) -> tuple[bool, list[str]]:
        """構造化データのバリデーション

        Args:
            data_dict: バリデーション対象の辞書データ

        Returns:
            tuple[bool, list[str]]: (バリデーション成功フラグ, エラーメッセージリスト)
        """
        try:
            # スキーマバリデーション
            errors: list[Any] = list(self.structured_validator.iter_errors(data_dict))

            if errors:
                error_messages = [self._format_validation_error(error) for error in errors]
                return False, error_messages

            return True, []

        except Exception as e:
            return False, [f"バリデーション実行エラー: {e!s}"]

    def _format_validation_error(self, error: jsonschema.ValidationError) -> str:
        """バリデーションエラーの日本語フォーマット

        Args:
            error: JSONSchemaバリデーションエラー

        Returns:
            str: 日本語フォーマットされたエラーメッセージ
        """
        path = " -> ".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"

        # 主要なエラータイプの日本語化
        error_type_map = {
            "required": "必須フィールド不足",
            "type": "データ型不正",
            "minimum": "最小値制約違反",
            "maximum": "最大値制約違反",
            "minLength": "最小文字数制約違反",
            "pattern": "パターン制約違反",
            "enum": "許可値制約違反",
            "format": "フォーマット制約違反",
        }

        error_type = error_type_map.get(error.validator, error.validator)

        return f"{path}: {error_type} - {error.message}"

    def get_schema_version(self) -> str:
        """スキーマバージョン取得

        Returns:
            str: 現在のスキーマバージョン
        """
        return "1.0.0"


class ValidationError(Exception):
    """バリデーション例外クラス"""

    def __init__(self, message: str, errors: list[str]) -> None:
        """バリデーション例外初期化

        Args:
            message: エラーメッセージ
            errors: 詳細エラーリスト
        """
        super().__init__(message)
        self.errors = errors

    def get_error_summary(self) -> str:
        """エラーサマリー取得

        Returns:
            str: エラーサマリー文字列
        """
        if not self.errors:
            return str(self)

        return f"{self!s}\n詳細エラー:\n" + "\n".join(f"- {error}" for error in self.errors)


# モジュールレベル関数（便利関数）
def validate_bridge_json_data(json_data: str) -> None:
    """橋渡しJSONデータバリデーション（例外スロー版）

    Args:
        json_data: バリデーション対象JSONデータ

    Raises:
        ValidationError: バリデーション失敗時
    """
    validator = StructuredStepOutputValidator()
    is_valid, errors = validator.validate_bridge_json(json_data)

    if not is_valid:
        error_msg = "橋渡しJSONバリデーション失敗"
        raise ValidationError(error_msg, errors)


def validate_structured_output_data(data_dict: dict[str, Any]) -> None:
    """構造化出力データバリデーション（例外スロー版）

    Args:
        data_dict: バリデーション対象辞書データ

    Raises:
        ValidationError: バリデーション失敗時
    """
    validator = StructuredStepOutputValidator()
    is_valid, errors = validator.validate_structured_data(data_dict)

    if not is_valid:
        error_msg = "構造化出力データバリデーション失敗"
        raise ValidationError(error_msg, errors)
