"""YAML検証機能のアダプター(統合版)"""

import re
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.quality.entities import QualityReport, QualityViolation
from noveler.domain.quality.value_objects import ErrorContext, ErrorSeverity, LineNumber, RuleCategory
from noveler.infrastructure.exceptions import YAMLParseException
from noveler.infrastructure.utils import YAMLHandler


class YAMLValidatorAdapter:
    """YAML検証機能をDDDに適応させるアダプター(統合版)"""

    def __init__(self) -> None:
        self.errors: list[dict[str, Any]] = []
        self.warnings: list[dict[str, Any]] = []

    def validate_yaml_file(self, file_path: Path, schema_type: str) -> QualityReport:
        """YAMLファイルを検証してDDDレポートを生成"""

        self.errors = []
        self.warnings = []

        # ファイル存在確認
        if not file_path.exists():
            self.errors.append(
                {"message": f"ファイルが見つかりません: {file_path}", "line": 0, "type": "file_not_found"}
            )
        else:
            try:
                # YAMLHandlerを使用して読み込み
                data = YAMLHandler.load_yaml(file_path)

                # スキーマタイプに応じた検証
                if schema_type == "project_config":
                    self.errors.extend(self._validate_project_config(data))
                elif schema_type == "episode_management":
                    self.errors.extend(self._validate_episode_management(data))
                elif schema_type == "character":
                    self.errors.extend(self._validate_character_config(data))

                # 基本的なYAML構造チェック
                self._validate_basic_yaml_structure(file_path)

            except YAMLParseException as e:
                self.errors.append(
                    {"message": f"YAMLパースエラー: {e}", "line": getattr(e, "line", 0), "type": "yaml_parse_error"}
                )
            except Exception as e:
                self.errors.append({"message": f"予期しないエラー: {e}", "line": 0, "type": "unexpected_error"})

        # DDDのQualityReportに変換
        report = QualityReport(
            episode_id=str(file_path),
        )

        # エラーを変換して追加
        for error in self.errors + self.warnings:
            violation = self._convert_to_violation(error, file_path)
            report.add_violation(violation)

        return report

    def validate_yaml_content(self, content: str, schema_type: str) -> QualityReport:
        """YAML内容を検証してDDDレポートを生成"""

        try:
            data = yaml.safe_load(content)
            errors: list[Any] = []

            # 基本的な構造チェック
            if data is None:
                errors.append({"message": "構文エラー", "line": 0, "type": "syntax_error"})

            # スキーマタイプに応じた検証
            if schema_type == "project_config":
                errors.extend(self._validate_project_config(data))
            elif schema_type == "episode_management":
                errors.extend(self._validate_episode_management(data))
            elif schema_type == "character":
                errors.extend(self._validate_character_config(data))

        except yaml.YAMLError as e:
            errors: list[dict[str, Any]] = [
                {
                    "line": getattr(e, "problem_mark", None).line + 1 if hasattr(e, "problem_mark") else 1,
                    "type": "yaml_syntax_error",
                    "message": str(e),
                    "severity": "error",
                },
            ]

        # DDDのQualityReportに変換
        report = QualityReport(
            episode_id=f"yaml_content_{schema_type}",
        )

        for error in errors:
            violation = self._convert_to_violation(error, None)
            report.add_violation(violation)

        return report

    def _convert_to_violation(self, error: dict[str, Any], file_path: Path | None) -> QualityViolation:
        """エラーをDDDのViolationに変換"""

        # エラータイプのマッピング
        severity_map = {
            "error": ErrorSeverity.ERROR,
            "warning": ErrorSeverity.WARNING,
            "info": ErrorSeverity.INFO,
        }

        # カテゴリーの判定
        error_type = error.get("type", "")
        if "syntax" in error_type or "indent" in error_type or "format" in error_type:
            category = RuleCategory.BASIC_STYLE
        else:
            category = RuleCategory.CONSISTENCY

        # 行番号の取得
        line_num = error.get("line", 1)
        line_number = LineNumber(line_num)

        # エラーコンテキストの生成
        context_text = error.get("context", "")
        if not context_text and file_path and file_path.exists():
            # ファイルから該当行を取得
            try:
                with Path(file_path).open(encoding="utf-8") as f:
                    lines = f.readlines()
                    if 0 < line_num <= len(lines):
                        context_text = lines[line_num - 1].rstrip()
            except (OSError, IndexError, UnicodeDecodeError):
                context_text = ""

        context = ErrorContext(text=context_text or "YAMLファイルのコンテキストが取得できません")

        # 修正提案の生成
        suggestion = self._generate_suggestion(error_type, error)

        # Violationの生成
        return QualityViolation(
            rule_name=error_type,
            severity=severity_map.get(error.get("severity", "warning"), ErrorSeverity.WARNING),
            message=error.get("message", ""),
            line_number=line_number,
            category=category,
            context=context,
            suggestion=suggestion,
        )

    def _generate_suggestion(self, error_type: str, error_data: dict[str, Any]) -> str:
        """エラータイプに基づいて修正提案を生成"""

        suggestions = {
            "yaml_syntax_error": "YAMLの構文を確認してください。インデントや記号の使い方に注意してください。",
            "missing_required_field": f"必須フィールド '{error_data.get('field', '')}' を追加してください。",
            "invalid_field_type": f"フィールド '{error_data.get('field', '')}' の型が正しくありません。",
            "odd_indent": "インデントは偶数個のスペースを使用してください(推奨: 2スペース)。",
            "tab_character": "タブ文字の代わりにスペースを使用してください。",
            "empty_yaml": "YAMLファイルに内容を追加してください。",
            "invalid_ncode": "ncodeは n + 7桁の数字 + アルファベット1文字 の形式にしてください。",
        }

        return suggestions.get(error_type, "YAMLファイルの形式を確認してください。")

    def _validate_basic_yaml_structure(self, file_path: Path) -> None:
        """基本的なYAML構造をチェック"""
        try:
            # ファイル読み込み
            content = Path(file_path).read_text(encoding="utf-8")

            # インデント検証
            lines = content.split("\n")
            for _i, line in enumerate(lines, 1):
                if "\t" in line:
                    self.warnings.append({"message": "構文エラー", "line": 0, "type": "syntax_error"})

                # 奇数インデントの確認
                if line.startswith(" "):
                    indent_count = 0
                    for char in line:
                        if char == " ":
                            indent_count += 1
                        else:
                            break
                    if indent_count % 2 == 1:
                        self.warnings.append({"message": "構文エラー", "line": 0, "type": "syntax_error"})
        except Exception:
            self.errors.append({"message": "構文エラー", "line": 0, "type": "syntax_error"})

    def _validate_project_config(self, data: dict[str, Any]) -> list[dict[str, object]]:
        """プロジェクト設定の検証"""
        errors: list[Any] = []

        if not isinstance(data, dict):
            return [
                {
                    "line": 1,
                    "type": "invalid_root_type",
                    "message": "ルート要素は辞書型である必要があります",
                    "severity": "error",
                },
            ]

        # 必須フィールドの確認
        required_fields = ["project", "author"]
        errors.extend(
            [
                {"message": "構文エラー", "line": 0, "type": "syntax_error"}
                for field in required_fields
                if field not in data
            ]
        )

        # プロジェクト情報の検証
        if "project" in data and isinstance(data["project"], dict):
            if "title" not in data["project"]:
                errors.append({"message": "構文エラー", "line": 0, "type": "syntax_error"})

            if "ncode" in data["project"]:
                ncode = data["project"]["ncode"]
                if not self._is_valid_ncode(ncode):
                    errors.append({"message": "構文エラー", "line": 0, "type": "syntax_error"})

        return errors

    def _validate_episode_management(self, data: dict[str, Any]) -> list[dict[str, object]]:
        """話数管理の検証"""
        errors: list[Any] = []

        if not isinstance(data, dict):
            return [
                {
                    "line": 1,
                    "type": "invalid_root_type",
                    "message": "ルート要素は辞書型である必要があります",
                    "severity": "error",
                },
            ]

        # エピソード情報の検証
        if "episodes" in data and isinstance(data["episodes"], dict):
            errors.extend(
                [
                    {"message": "構文エラー", "line": 0, "type": "syntax_error"}
                    for ep_data in data["episodes"].values()
                    if not isinstance(ep_data, dict) or "title" not in ep_data
                ]
            )

        return errors

    def _validate_character_config(self, data: dict[str, Any]) -> list[dict[str, object]]:
        """キャラクター設定の検証"""
        errors: list[Any] = []

        if not isinstance(data, dict):
            return [
                {
                    "line": 1,
                    "type": "invalid_root_type",
                    "message": "ルート要素は辞書型である必要があります",
                    "severity": "error",
                },
            ]

        # メインキャラクターの検証
        if "main_characters" in data and isinstance(data["main_characters"], dict):
            errors.extend(
                [
                    {"message": "構文エラー", "line": 0, "type": "syntax_error"}
                    for char_data in data["main_characters"].values()
                    if not isinstance(char_data, dict) or "profile" not in char_data
                ]
            )

        return errors

    def _is_valid_ncode(self, ncode: str) -> bool:
        """ncodeの形式を検証"""
        return bool(re.match(r"^n\d{7}[a-z]$", str(ncode).lower()))
