#!/usr/bin/env python3

"""Domain.services.plot_validation_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""プロットファイル検証サービス

プロットファイルの内容を検証し、問題を検出するドメインサービス
"""


import re
from typing import Any

import yaml

from noveler.domain.value_objects.plot_schema import (
    CHAPTER_PLOT_SCHEMA,
    EPISODE_PLOT_SCHEMA,
    MASTER_PLOT_SCHEMA,
    FieldDefinition,
    PlotSchema,
)
from noveler.domain.value_objects.validation_result import (
    ValidationIssue,
    ValidationLevel,
    ValidationResult,
)
from noveler.domain.value_objects.workflow_stage_type import WorkflowStageType


class PlotValidationService:
    """プロットファイル検証サービス"""

    def __init__(self) -> None:
        """初期化"""
        self._schema_mapping = {
            WorkflowStageType.MASTER_PLOT: MASTER_PLOT_SCHEMA,
            WorkflowStageType.CHAPTER_PLOT: CHAPTER_PLOT_SCHEMA,
            WorkflowStageType.EPISODE_PLOT: EPISODE_PLOT_SCHEMA,
        }

    def validate_plot_file(self, stage_type: WorkflowStageType, content: dict[str, Any]) -> ValidationResult:
        """プロットファイルの内容を検証

        Args:
            stage_type: ワークフローステージタイプ
            content: 検証するコンテンツ

        Returns:
            ValidationResult: 検証結果
        """
        schema = self.get_schema_for_stage(stage_type)
        if not schema:
            return self._create_schema_not_found_result(stage_type)

        issues = []
        validated_fields = {}

        # 各検証を個別メソッドに分離
        self._validate_required_fields(content, schema, issues, validated_fields)
        self._validate_field_types(content, schema, issues)
        self._validate_non_empty_fields(content, schema, issues)
        issues.extend(self._validate_template_variables(content))

        # オプションフィールドの警告
        optional_warnings = self._check_optional_fields(schema, content)
        issues.extend(optional_warnings)

        # 有効性の判定(エラーがなければ有効)
        is_valid = not any(issue.level == ValidationLevel.ERROR for issue in issues)

        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            validated_fields=validated_fields,
        )

    def _create_schema_not_found_result(self, stage_type: WorkflowStageType) -> ValidationResult:
        """スキーマが見つからない場合の結果を作成"""
        return ValidationResult(
            is_valid=False,
            issues=[
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message=f"ステージタイプ '{stage_type}' のスキーマが定義されていません",
                )
            ],
        )

    def _validate_required_fields(
        self, content: dict[str, Any], schema: object, issues: list, validated_fields: dict
    ) -> None:
        """必須フィールドの検証"""
        for field_name, field_def in schema.fields.items():
            if field_def.required:
                issue = self._validate_required_field(content, field_name, field_def)
                if issue:
                    issues.append(issue)
                else:
                    validated_fields[field_name] = content.get(field_name)

    def _validate_field_types(self, content: dict[str, Any], schema: object, issues: list) -> None:
        """型の検証"""
        for field_name, value in content.items():
            if field_name in schema.fields:
                field_def = schema.fields[field_name]
                issue = self._validate_field_type(field_name, value, field_def)
                if issue:
                    issues.append(issue)

    def _validate_non_empty_fields(self, content: dict[str, Any], schema: object, issues: list) -> None:
        """空フィールドの検証"""
        for field_name, value in content.items():
            if field_name in schema.fields and schema.fields[field_name].required:
                issue = self._validate_non_empty(field_name, value)
                if issue:
                    issues.append(issue)

    def validate_yaml_syntax(self, yaml_content: str) -> ValidationResult:
        """YAML構文の検証

        Args:
            yaml_content: YAML形式の文字列

        Returns:
            ValidationResult: 検証結果
        """
        try:
            parsed = yaml.safe_load(yaml_content)
            if parsed is None:
                return ValidationResult(
                    is_valid=False,
                    issues=[
                        ValidationIssue(
                            level=ValidationLevel.ERROR,
                            message="YAMLファイルが空です",
                        )
                    ],
                )

            return ValidationResult(is_valid=True, validated_fields={"parsed": parsed})
        except yaml.YAMLError as e:
            return ValidationResult(
                is_valid=False,
                issues=[
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        message=f"YAML構文エラー: {e!s}",
                        suggestion="YAMLの構文を確認してください(インデント、括弧の対応など)",
                    )
                ],
            )

    def get_schema_for_stage(self, stage_type: WorkflowStageType) -> PlotSchema | None:
        """ステージタイプに対応するスキーマを取得

        Args:
            stage_type: ワークフローステージタイプ

        Returns:
            PlotSchema: 対応するスキーマ(存在しない場合はNone)
        """
        return self._schema_mapping.get(stage_type)

    def _validate_required_field(
        self, content: dict[str, Any], field_name: str, field_def: FieldDefinition
    ) -> ValidationIssue | None:
        """必須フィールドの存在を検証"""
        if field_name not in content:
            return ValidationIssue(
                level=ValidationLevel.ERROR,
                message=f"必須フィールド '{field_name}' が見つかりません",
                field_path=field_name,
                suggestion=f"{field_def.description}を追加してください",
            )

        return None

    def _validate_field_type(
        self, field_name: str, value: object, field_def: FieldDefinition
    ) -> ValidationIssue | None:
        """フィールドの型を検証"""
        expected_type = field_def.field_type
        if not isinstance(value, expected_type):
            actual_type = type(value).__name__
            expected_type_name = expected_type.__name__
            return ValidationIssue(
                level=ValidationLevel.ERROR,
                message=f"フィールド '{field_name}' の型が不正です(期待: {expected_type_name}, 実際: {actual_type})",
            )
        return None

    def _validate_non_empty(self, field_name: str, value: object) -> ValidationIssue | None:
        """フィールドが空でないことを検証"""
        if isinstance(value, str) and not value.strip():
            return ValidationIssue(
                level=ValidationLevel.ERROR,
                message=f"必須フィールド '{field_name}' が空です",
                field_path=field_name,
                suggestion="有効な値を入力してください",
            )

        if isinstance(value, list | dict) and len(value) == 0:
            return ValidationIssue(
                level=ValidationLevel.ERROR,
                message=f"必須フィールド '{field_name}' が空です",
                field_path=field_name,
                suggestion="少なくとも1つの要素を追加してください",
            )

        return None

    def _validate_template_variables(self, content: dict[str, Any]) -> list[ValidationIssue]:
        """テンプレート変数が残っていないか検証"""
        issues = []
        template_pattern = re.compile(r"\$\{[^}]+\}")

        def check_value(value: object, path: str = "") -> None:
            if isinstance(value, str):
                matches = template_pattern.findall(value)
                if matches:
                    issues.append(
                        ValidationIssue(
                            level=ValidationLevel.WARNING,
                            message=f"テンプレート変数が残っています: {', '.join(matches)}",
                            field_path=path,
                            suggestion="プロジェクト固有の値に置き換えてください",
                        )
                    )

            elif isinstance(value, dict):
                for key, val in value.items():
                    new_path = f"{path}.{key}" if path else key
                    check_value(val, new_path)
            elif isinstance(value, list):
                for i, val in enumerate(value):
                    new_path = f"{path}[{i}]" if path else f"[{i}]"
                    check_value(val, new_path)

        check_value(content, "")
        return issues

    def _check_optional_fields(self, schema: PlotSchema, content: dict[str, Any]) -> list[ValidationIssue]:
        """オプションフィールドの存在を確認し、警告を生成"""
        warnings = []
        optional_fields = schema.get_optional_fields()

        for field_name in optional_fields:
            if field_name not in content:
                field_def = schema.fields[field_name]
                warnings.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        message=f"推奨フィールド '{field_name}' が設定されていません",
                        field_path=field_name,
                        suggestion=f"{field_def.description}の追加を検討してください",
                    )
                )

        return warnings
