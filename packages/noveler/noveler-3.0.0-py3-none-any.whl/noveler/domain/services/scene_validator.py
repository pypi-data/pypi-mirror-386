#!/usr/bin/env python3
"""シーン検証サービス

B30品質作業指示書に基づく実装
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ValidationResult:
    """検証結果"""

    is_valid: bool
    errors: list[str]
    warnings: list[str]

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


class SceneValidator:
    """シーン検証サービス"""

    def __init__(self) -> None:
        """初期化"""

    def validate(self, scene_data: dict[str, Any]) -> ValidationResult:
        """シーンデータ検証

        Args:
            scene_data: 検証対象のシーンデータ

        Returns:
            ValidationResult: 検証結果
        """
        errors: list[str] = []
        warnings: list[str] = []

        # 基本的な検証項目
        if not scene_data:
            errors.append("シーンデータが空です")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        # 必須フィールドチェック
        required_fields = ["scene_id", "title", "content"]
        for field in required_fields:
            if field not in scene_data:
                errors.append(f"必須フィールドが欠けています: {field}")

        # 内容の長さチェック
        if "content" in scene_data:
            content = scene_data["content"]
            if isinstance(content, str) and len(content.strip()) < 10:
                warnings.append("シーン内容が短すぎます")

        # タイトルチェック
        if "title" in scene_data:
            title = scene_data["title"]
            if isinstance(title, str) and len(title.strip()) == 0:
                errors.append("タイトルが空です")

        is_valid = len(errors) == 0
        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)

    def validate_batch(self, scene_list: list[dict[str, Any]]) -> list[ValidationResult]:
        """バッチ検証

        Args:
            scene_list: シーンデータのリスト

        Returns:
            List[ValidationResult]: 各シーンの検証結果
        """
        results: list[ValidationResult] = []
        for scene_data in scene_list:
            result = self.validate(scene_data)
            results.append(result)
        return results
