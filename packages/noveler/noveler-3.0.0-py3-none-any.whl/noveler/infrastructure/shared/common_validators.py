#!/usr/bin/env python3
"""共通バリデーション機能

中優先度問題解決:コード重複の解消
- 類似のバリデーション処理の統一化
- 再利用可能なバリデーションルール
"""

import re
from pathlib import Path


class ValidationResult:
    """バリデーション結果"""

    def __init__(self, is_valid: bool, message: str) -> None:
        self.is_valid = is_valid
        self.message = message

    def __bool__(self) -> bool:
        return self.is_valid


class CommonValidators:
    """共通バリデーション機能"""

    @staticmethod
    def validate_required_field(value: object, field_name: str) -> ValidationResult:
        """必須フィールドのバリデーション"""
        if value is None:
            return ValidationResult(False, f"{field_name}は必須です")

        if isinstance(value, str) and not value.strip():
            return ValidationResult(False, f"{field_name}は空文字列にできません")

        if isinstance(value, list | dict) and len(value) == 0:
            return ValidationResult(False, f"{field_name}は空にできません")

        return ValidationResult(True)

    @staticmethod
    def validate_episode_number(episode_number: int) -> ValidationResult:
        """エピソード番号のバリデーション"""
        if not isinstance(episode_number, int):
            try:
                episode_number = int(episode_number)
            except (ValueError, TypeError):
                return ValidationResult(False, "エピソード番号は数値である必要があります")

        if episode_number <= 0:
            return ValidationResult(False, "エピソード番号は1以上である必要があります")

        if episode_number > 9999:
            return ValidationResult(False, "エピソード番号は9999以下である必要があります")

        return ValidationResult(True)

    @staticmethod
    def validate_project_name(project_name: str) -> ValidationResult:
        """プロジェクト名のバリデーション"""
        if not project_name or not project_name.strip():
            return ValidationResult(False, "プロジェクト名は必須です")

        # 不正な文字をチェック
        invalid_chars = r'[<>:"/\\|?*]'
        if re.search(invalid_chars, project_name):
            return ValidationResult(False, "プロジェクト名に使用できない文字が含まれています")

        if len(project_name) > 100:
            return ValidationResult(False, "プロジェクト名は100文字以下である必要があります")

        return ValidationResult(True)

    @staticmethod
    def validate_file_path(file_path: str | Path) -> ValidationResult:
        """ファイルパスのバリデーション"""
        try:
            path = Path(file_path)
        except (TypeError, ValueError):
            return ValidationResult(False, "無効なファイルパスです")

        # パスの長さチェック(Windows制限)
        if len(str(path)) > 260:
            return ValidationResult(False, "ファイルパスが長すぎます(260文字以下)")

        return ValidationResult(True)

    @staticmethod
    def validate_file_exists(file_path: str | Path) -> ValidationResult:
        """ファイル存在チェック"""
        path_validation = CommonValidators.validate_file_path(file_path)
        if not path_validation:
            return path_validation

        path = Path(file_path)
        if not path.exists():
            return ValidationResult(False, f"ファイルが見つかりません: {file_path}")

        if not path.is_file():
            return ValidationResult(False, f"指定されたパスはファイルではありません: {file_path}")

        return ValidationResult(True)

    @staticmethod
    def validate_yaml_structure(data: dict[str, object], required_fields: list[str]) -> ValidationResult:
        """YAML構造のバリデーション"""
        if not isinstance(data, dict):
            return ValidationResult(False, "YAMLデータは辞書である必要があります")

        missing_fields = []
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)

        if missing_fields:
            return ValidationResult(False, f"必須フィールドが不足しています: {', '.join(missing_fields)}")

        return ValidationResult(True)

    @staticmethod
    def validate_episode_range(episode_range: str) -> ValidationResult:
        """エピソード範囲のバリデーション(例: "1-5", "10", "15-20")"""
        if not episode_range or not episode_range.strip():
            return ValidationResult(False, "エピソード範囲は必須です")

        # 単一エピソード(例: "5")
        if episode_range.isdigit():
            return CommonValidators.validate_episode_number(int(episode_range))

        # 範囲(例: "1-5")
        range_pattern = r"^(\d+)-(\d+)$"
        match = re.match(range_pattern, episode_range)
        if not match:
            return ValidationResult(False, "エピソード範囲の形式が不正です(例: 1-5, 10-15)")

        start_ep = int(match.group(1))
        end_ep = int(match.group(2))

        start_validation = CommonValidators.validate_episode_number(start_ep)
        if not start_validation:
            return start_validation

        end_validation = CommonValidators.validate_episode_number(end_ep)
        if not end_validation:
            return end_validation

        if start_ep >= end_ep:
            return ValidationResult(False, "開始エピソードは終了エピソードより小さい必要があります")

        return ValidationResult(True)

    @staticmethod
    def validate_quality_score(score: float | int) -> ValidationResult:
        """品質スコアのバリデーション(0.0-100.0)"""
        try:
            score = float(score)
        except (ValueError, TypeError):
            return ValidationResult(False, "品質スコアは数値である必要があります")

        if score < 0.0:
            return ValidationResult(False, "品質スコアは0.0以上である必要があります")

        if score > 100.0:
            return ValidationResult(False, "品質スコアは100.0以下である必要があります")

        return ValidationResult(True)

    @staticmethod
    def validate_word_count(word_count: int) -> ValidationResult:
        """文字数のバリデーション"""
        try:
            word_count = int(word_count)
        except (ValueError, TypeError):
            return ValidationResult(False, "文字数は整数である必要があります")

        if word_count < 0:
            return ValidationResult(False, "文字数は0以上である必要があります")

        if word_count > 1000000:  # 100万文字上限:
            return ValidationResult(False, "文字数が上限(100万文字)を超えています")

        return ValidationResult(True)


# 便利関数
def validate_required(value: object, field_name: str) -> ValidationResult:
    """必須フィールド検証の便利関数"""
    return CommonValidators.validate_required_field(value, field_name)


def validate_episode_num(episode_number: int) -> ValidationResult:
    """エピソード番号検証の便利関数"""
    return CommonValidators.validate_episode_number(episode_number)


def validate_project(project_name: str) -> ValidationResult:
    """プロジェクト名検証の便利関数"""
    return CommonValidators.validate_project_name(project_name)
