#!/usr/bin/env python3
"""保存前内容検証サービス

仕様書: SPEC-FIVE-STAGE-SESSION-002 (P1実装)
JSONメタデータ誤認防止・品質基準チェック・内容妥当性検証
"""

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from noveler.infrastructure.logging.unified_logger import get_logger

# DDD準拠: Infrastructure→Presentation依存を除去
from noveler.presentation.shared.shared_utilities import console


class ValidationLevel(Enum):
    """検証レベル"""

    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"
    CRITICAL = "critical"


class ContentType(Enum):
    """コンテンツタイプ"""

    MANUSCRIPT = "manuscript"
    FINAL_MANUSCRIPT = "final_manuscript"
    JSON_METADATA = "json_metadata"
    TEXT_CONTENT = "text_content"
    INVALID = "invalid"


@dataclass
class ValidationResult:
    """検証結果"""

    is_valid: bool
    content_type: ContentType
    issues: list[str]
    warnings: list[str]
    metrics: dict[str, Any]
    recommendation: str

    def has_critical_issues(self) -> bool:
        """重要な問題有無判定"""
        critical_keywords = ["メタデータのみ", "JSON形式", "内容なし", "文字数不足"]
        return any(keyword in issue for issue in self.issues for keyword in critical_keywords)

    def get_summary(self) -> str:
        """検証結果サマリー"""
        status = "✅ 合格" if self.is_valid else "❌ 不合格"
        issue_count = len(self.issues)
        warning_count = len(self.warnings)

        return f"{status} | 問題: {issue_count}件, 警告: {warning_count}件 | {self.recommendation}"


class ContentValidationService:
    """コンテンツ検証サービス

    責務:
        - 5段階生成システムの出力検証
        - JSONメタデータやプロンプト混入の検出
        - 原稿形式の妥当性チェック
        - 品質基準の適用と評価

    設計原則:
        - 段階的な検証レベル（BASIC, STANDARD, STRICT）
        - 検出と修正の分離
        - 詳細なエラーレポート生成
    """

    def __init__(
        self, validation_level: ValidationLevel = ValidationLevel.STANDARD, logger_service=None, console_service=None
    ) -> None:
        """初期化

        Args:
            validation_level: 検証レベル
        """
        self.validation_level = validation_level
        self.logger = get_logger(__name__)

        # 検証ルール定義
        self.validation_rules = {
            ValidationLevel.BASIC: [self._check_not_empty, self._check_basic_structure],
            ValidationLevel.STANDARD: [
                self._check_not_empty,
                self._check_basic_structure,
                self._check_no_prompt_contamination,
                self._check_title_format,
            ],
            ValidationLevel.STRICT: [
                self._check_not_empty,
                self._check_basic_structure,
                self._check_no_prompt_contamination,
                self._check_no_json_metadata,
                self._check_title_format,
                self._check_chapter_structure,
                self._check_no_code_blocks,
                self._check_no_system_messages,
                self._check_word_count_range,
            ],
        }

    async def validate(
        self, content: str, stage: str | None = None, metadata: dict[str, Any] | None = None
    ) -> ValidationResult:
        """コンテンツ検証

        Args:
            content: 検証対象コンテンツ
            stage: 実行段階（オプション）
            metadata: 追加メタデータ（オプション）

        Returns:
            ValidationResult: 検証結果
        """
        errors: list[Any] = []
        warnings = []
        suggestions = []

        # 検証レベルに応じたルール適用
        rules = self.validation_rules.get(self.validation_level, [])

        for rule in rules:
            try:
                result = rule(content, stage, metadata)
                if result:
                    if result["severity"] == "error":
                        errors.append(result["message"])
                    elif result["severity"] == "warning":
                        warnings.append(result["message"])

                    if "suggestion" in result:
                        suggestions.append(result["suggestion"])

            except Exception as e:
                self.logger.exception("検証ルール実行エラー: %s", e)
                warnings.append(f"検証ルール実行失敗: {rule.__name__}")

        # 自動修正可能な問題の修正
        cleaned_content = content
        if self.validation_level == ValidationLevel.STRICT:
            cleaned_content = self._auto_clean_content(content)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            cleaned_content=cleaned_content,
            metadata={
                "validation_level": self.validation_level.value,
                "stage": stage,
                "original_length": len(content),
                "cleaned_length": len(cleaned_content),
            },
        )

    def _check_not_empty(
        self, content: str, stage: str | None = None, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """空コンテンツチェック"""
        if not content or not content.strip():
            return {
                "severity": "error",
                "message": "コンテンツが空です",
                "suggestion": "有効なコンテンツを生成してください",
            }
        return None

    def _check_basic_structure(
        self, content: str, stage: str | None = None, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """基本構造チェック"""
        lines = content.split("\n")

        # 最低行数チェック
        if len(lines) < 10:
            return {
                "severity": "warning",
                "message": "コンテンツが短すぎます",
                "suggestion": "より詳細な内容を追加してください",
            }

        # 日本語コンテンツチェック
        japanese_pattern = re.compile(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]")
        if not japanese_pattern.search(content):
            return {
                "severity": "error",
                "message": "日本語コンテンツが含まれていません",
                "suggestion": "日本語で原稿を作成してください",
            }

        return None

    def _check_no_prompt_contamination(
        self, content: str, stage: str | None = None, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """プロンプト混入チェック"""
        prompt_indicators = [
            "## 指示:",
            "## 要件:",
            "## 注意事項:",
            "以下の指示に従って",
            "次の要件を満たして",
            "あなたは",
            "してください",
            "必ず含めて",
            "Claude Code",
            "プロンプト",
            "生成して",
        ]

        for indicator in prompt_indicators:
            if indicator in content:
                return {
                    "severity": "error",
                    "message": f'プロンプトの混入を検出: "{indicator}"',
                    "suggestion": "プロンプト部分を除去して原稿のみを抽出してください",
                }

        return None

    def _check_no_json_metadata(
        self, content: str, stage: str | None = None, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """JSONメタデータチェック"""

        # JSON形式の検出
        json_patterns = [
            r'\{[^{}]*"[^"]+"\s*:\s*[^{}]*\}',  # 基本的なJSON
            r"```json.*?```",  # JSONコードブロック
            r'"metadata"\s*:\s*\{',  # メタデータオブジェクト
            r'"stage"\s*:\s*"[^"]+"',  # ステージ情報
        ]

        for pattern in json_patterns:
            if re.search(pattern, content, re.MULTILINE | re.DOTALL):
                return {
                    "severity": "error",
                    "message": "JSONメタデータの混入を検出",
                    "suggestion": "JSONメタデータを除去して純粋な原稿テキストのみにしてください",
                }

        return None

    def _check_title_format(
        self, content: str, stage: str | None = None, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """タイトル形式チェック"""

        # タイトル行のパターン
        title_patterns = [r"^第\d+話", r"^# 第\d+話", r"^## 第\d+話"]

        has_title = any(re.search(pattern, content, re.MULTILINE) for pattern in title_patterns)

        if not has_title:
            return {
                "severity": "warning",
                "message": "タイトル行が見つかりません",
                "suggestion": "「第XXX話 タイトル」形式でタイトルを追加してください",
            }

        return None

    def _check_chapter_structure(
        self, content: str, stage: str | None = None, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """章構造チェック"""
        lines = content.split("\n")

        # セクション見出しの検出
        section_count = sum(1 for line in lines if line.startswith("#"))
        if section_count < 3:
            return {
                "severity": "warning",
                "message": "セクション構造が不十分です",
                "suggestion": "起承転結などの章立てを追加してください",
            }

        return None

    def _check_no_code_blocks(
        self, content: str, stage: str | None = None, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """コードブロックチェック"""
        if "```" in content:
            return {
                "severity": "error",
                "message": "コードブロックが含まれています",
                "suggestion": "コードブロックを除去してください",
            }

        return None

    def _check_no_system_messages(
        self, content: str, stage: str | None = None, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """システムメッセージチェック"""
        system_indicators = [
            "[System]",
            "[Error]",
            "[Warning]",
            "Traceback",
            "Exception",
            "DEBUG:",
            "INFO:",
            "ERROR:",
            "WARNING:",
        ]

        for indicator in system_indicators:
            if indicator in content:
                return {
                    "severity": "error",
                    "message": f'システムメッセージの混入: "{indicator}"',
                    "suggestion": "システムメッセージを除去してください",
                }

        return None

    def _check_word_count_range(
        self, content: str, stage: str | None = None, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """文字数範囲チェック"""
        # タイトル行を除外
        content_without_title = re.sub(r"^.*第\d+話.*$", "", content, flags=re.MULTILINE).strip()

        char_count = len(content_without_title)

        if char_count < 2000:
            return {
                "severity": "warning",
                "message": f"文字数が少なすぎます: {char_count}文字",
                "suggestion": "最低2000文字以上の内容を作成してください",
            }

        if char_count > 10000:
            return {
                "severity": "warning",
                "message": f"文字数が多すぎます: {char_count}文字",
                "suggestion": "10000文字以内に収めることを推奨します",
            }

        return None

    def _auto_clean_content(self, content: str) -> str:
        """自動クリーニング

        Args:
            content: 入力コンテンツ

        Returns:
            クリーニング済みコンテンツ
        """

        cleaned = content

        # JSONメタデータ除去
        json_patterns = [
            r'\{[^{}]*"metadata"[^{}]*\}',
            r'\{[^{}]*"stage"[^{}]*\}',
            r"```json.*?```",
        ]
        for pattern in json_patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.MULTILINE | re.DOTALL)

        # コードブロック除去
        cleaned = re.sub(r"```.*?```", "", cleaned, flags=re.DOTALL)

        # システムメッセージ除去
        system_patterns = [r"^\[System\].*$", r"^\[Error\].*$", r"^(DEBUG|INFO|WARNING|ERROR):.*$"]
        for pattern in system_patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.MULTILINE)

        # プロンプト行除去
        prompt_lines = [r"^.*指示:.*$", r"^.*要件:.*$", r"^.*してください.*$"]
        for pattern in prompt_lines:
            cleaned = re.sub(pattern, "", cleaned, flags=re.MULTILINE)

        # 連続空行を1行に
        cleaned = re.sub(r"\n\n+", "\n\n", cleaned)

        return cleaned.strip()


class ManuscriptQualityGate:
    """原稿品質ゲート"""

    def __init__(self, validation_service: ContentValidationService, logger_service=None, console_service=None) -> None:
        self.validation_service = validation_service
        self.logger = get_logger(__name__)

        self.logger_service = logger_service
        self.console_service = console_service

    def check_before_save(self, content: str, file_path: Path) -> bool:
        """保存前品質ゲートチェック"""

        console.print(f"[blue]🔍 品質ゲートチェック: {file_path.name}[/blue]")

        # 基本検証
        validation_result = self.validation_service.validate_content_for_saving(content, file_path)

        # 結果表示
        console.print(f"[cyan]検証結果: {validation_result.get_summary()}[/cyan]")

        # メトリクス表示
        if validation_result.metrics:
            console.print("[dim]品質メトリクス:[/dim]")
            for key, value in validation_result.metrics.items():
                console.print(f"[dim]  - {key}: {value}[/dim]")

        # 重要な問題がある場合は保存を阻止
        if validation_result.has_critical_issues():
            console.print("[red]🚫 保存を中止します - 重要な品質問題があります[/red]")
            return False

        # 警告がある場合は確認
        if validation_result.warnings:
            console.print("[yellow]⚠️ 警告事項がありますが、保存を続行します[/yellow]")

        console.print("[green]✅ 品質ゲート通過 - 保存を続行します[/green]")
        return True
