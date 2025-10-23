"""Domain.services.format_standardization_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""
FormatStandardizationService

各種ファイルフォーマットの標準化を行うドメインサービスです。
YAML、Markdown等のフォーマット整形、検証、準拠性チェックを担当します。
"""


import re
from typing import Any

import yaml

from noveler.domain.exceptions import ValidationError
from noveler.domain.value_objects.format_specification import FormatSpecification, FormatType
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class StandardizationResult:
    """標準化結果を表現するクラス"""

    def __init__(
        self,
        standardized_content: str,
        applied_spec: FormatSpecification,
        violations: list[str] | None = None,
        corrections: list[str] | None = None,
    ) -> None:
        self.standardized_content = standardized_content
        self.applied_spec = applied_spec
        self.violations = violations or []
        self.corrections = corrections or []
        self.standardization_timestamp = project_now().datetime.isoformat()

    def is_successful(self) -> bool:
        """標準化が成功したかチェック"""
        return len(self.violations) == 0

    def has_corrections(self) -> bool:
        """修正が適用されたかチェック"""
        return len(self.corrections) > 0


class ComplianceCheckResult:
    """準拠性チェック結果を表現するクラス"""

    def __init__(
        self, is_compliant: bool, violations: list[str], suggestions: list[str] | None = None, score: float = 0.0
    ) -> None:
        self.is_compliant = is_compliant
        self.violations = violations or []
        self.suggestions = suggestions or []
        self.score = score
        self.check_timestamp = project_now().datetime.isoformat()


class FormatStandardizationService:
    """ファイルフォーマット標準化を行うドメインサービス"""

    def __init__(self) -> None:
        self._format_specs: dict[FormatType, FormatSpecification] = {}
        self._setup_default_specs()

    def _setup_default_specs(self) -> None:
        """デフォルトのフォーマット仕様を設定"""
        self._format_specs[FormatType.YAML] = FormatSpecification.create_yaml_spec()
        self._format_specs[FormatType.MARKDOWN] = FormatSpecification.create_markdown_spec()

    def register_format_specification(self, spec: FormatSpecification) -> None:
        """フォーマット仕様を登録"""
        if not isinstance(spec, FormatSpecification):
            msg = "フォーマット仕様はFormatSpecificationのインスタンスである必要があります"
            raise ValidationError(msg, msg)

        self._format_specs[spec.format_type] = spec

    def get_format_specifications(self) -> dict[FormatType, FormatSpecification]:
        """フォーマット仕様一覧を取得"""
        return self._format_specs.copy()

    def standardize_yaml_format(
        self, yaml_content: str | dict[str, Any], spec: FormatSpecification | None
    ) -> StandardizationResult:
        """YAMLフォーマットを標準化"""
        if spec is None:
            spec = self._format_specs.get(FormatType.YAML)
            if spec is None:
                msg = "YAML仕様が設定されていません"
                raise ValidationError(msg, msg)

        if spec.format_type != FormatType.YAML:
            msg = "YAML用の仕様ではありません"
            raise ValidationError(msg, msg)

        violations: list[str] = []
        corrections: list[str] = []

        # 入力データの解析
        if isinstance(yaml_content, str):
            try:
                data = yaml.safe_load(yaml_content)
            except yaml.YAMLError as e:
                violations.append(f"YAML構文エラー: {e}")
                return StandardizationResult("", spec, violations, corrections)
        else:
            data = yaml_content

        if data is None:
            violations.append("YAMLデータが空です")
            return StandardizationResult("", spec, violations, corrections)

        # フォーマット設定の取得
        formatting_options = spec.properties or {}

        # YAML出力の生成
        try:
            standardized_content = yaml.dump(
                data,
                allow_unicode=formatting_options.get("allow_unicode", True),
                default_flow_style=formatting_options.get("default_flow_style", False),
                indent=spec.indent_size,
                sort_keys=formatting_options.get("sort_keys", True),
                line_break=formatting_options.get("line_break", "\n"),
            )

            corrections.append("YAML標準フォーマットを適用しました")

        except Exception as e:
            violations.append(f"YAML標準化エラー: {e}")
            return StandardizationResult("", spec, violations, corrections)

        # 追加の整形処理
        standardized_content = self._apply_yaml_post_processing(standardized_content, spec)
        if standardized_content != yaml.dump(data):
            corrections.append("追加の整形処理を適用しました")

        return StandardizationResult(standardized_content, spec, violations, corrections)

    def standardize_markdown_format(
        self, markdown_content: str, spec: FormatSpecification | None
    ) -> StandardizationResult:
        """Markdownフォーマットを標準化"""
        if not markdown_content:
            return StandardizationResult(
                "", spec or self._format_specs[FormatType.MARKDOWN], ["Markdownコンテンツが空です"], []
            )

        spec = self._validate_markdown_spec(spec)
        violations: list[str] = []
        corrections: list[str] = []

        lines = markdown_content.split("\n")
        standardized_lines = []

        # 行ごとの標準化処理
        for i, original_line in enumerate(lines):
            standardized_line, line_corrections = self._standardize_line(original_line, spec, i + 1)
            standardized_lines.append(standardized_line)
            corrections.extend(line_corrections)

        # 空行の正規化
        standardized_content = self._normalize_empty_lines("\n".join(standardized_lines))
        if standardized_content != markdown_content:
            corrections.append("空行を正規化しました")

        return StandardizationResult(standardized_content, spec, violations, corrections)

    def validate_format_compliance(
        self, content: str, format_type: FormatType, spec: FormatSpecification | None = None
    ) -> ComplianceCheckResult:
        """フォーマット準拠性をチェック"""
        if spec is None:
            spec = self._format_specs.get(format_type)
            if spec is None:
                return ComplianceCheckResult(
                    False, [f"フォーマットタイプ{format_type.value}の仕様が設定されていません"], []
                )

        violations: list[Any] = []
        suggestions = []

        if format_type == FormatType.YAML:
            violations, suggestions = self._validate_yaml_compliance(content, spec)
        elif format_type == FormatType.MARKDOWN:
            violations, suggestions = self._validate_markdown_compliance(content, spec)
        else:
            violations.append(f"サポートされていないフォーマット: {format_type}")

        # 準拠性スコアの計算
        score = self._calculate_compliance_score(content, violations, suggestions)

        return ComplianceCheckResult(
            is_compliant=len(violations) == 0, violations=violations, suggestions=suggestions, score=score
        )

    def batch_standardize_content(self, content_list: list[tuple[str, FormatType]]) -> list[StandardizationResult]:
        """コンテンツを一括標準化"""
        results: list[Any] = []

        for content, format_type in content_list:
            try:
                if format_type == FormatType.YAML:
                    result = self.standardize_yaml_format(content, None)
                elif format_type == FormatType.MARKDOWN:
                    result = self.standardize_markdown_format(content, None)
                else:
                    spec = self._format_specs.get(format_type)
                    result = StandardizationResult(
                        content,
                        spec or FormatSpecification.create_yaml_spec(),
                        [f"サポートされていないフォーマット: {format_type.value}"],
                        [],
                    )

                results.append(result)

            except Exception as e:
                error_result = StandardizationResult(
                    "", self._format_specs.get(format_type, FormatSpecification.create_yaml_spec()), [str(e)], []
                )

                results.append(error_result)

        return results

    def _apply_yaml_post_processing(self, content: str, spec: FormatSpecification) -> str:
        """YAML後処理"""
        lines = content.split("\n")
        processed_lines = []

        for line in lines:
            # 空行の処理
            if not line.strip():
                processed_lines.append("")
                continue

            # インデントの確認と修正
            if line.startswith(" "):
                indent_level = len(line) - len(line.lstrip())
                expected_indent = spec.indent_size

                if indent_level % expected_indent != 0:
                    # インデントを修正
                    corrected_indent = (indent_level // expected_indent) * expected_indent
                    corrected_line = " " * corrected_indent + line.lstrip()
                    processed_lines.append(corrected_line)
                else:
                    processed_lines.append(line)
            else:
                processed_lines.append(line)

        return "\n".join(processed_lines)

    def _standardize_heading(self, line: str, spec: FormatSpecification) -> str:
        """見出しを標準化"""
        heading_style = spec.properties.get("heading_style", "atx") if spec.properties else "atx"

        if heading_style != "atx":
            return line

        # ATXスタイル(# ## ###)への統一
        heading_match = re.match(r"^(#+)\s*(.*)", line)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2).strip()
            if text:
                return f"{'#' * level} {text}"

        return line

    def _standardize_list(self, line: str, spec: FormatSpecification) -> str:
        """リストを標準化"""
        list_style = spec.properties.get("bullet_style", "-") if spec.properties else "-"

        # 無序リストの標準化
        list_match = re.match(r"^(\s*)[\*\+\-]\s+(.*)", line)
        if list_match:
            indent = list_match.group(1)
            content = list_match.group(2)
            return f"{indent}{list_style} {content}"

        # 順序付きリストはそのまま
        ordered_match = re.match(r"^(\s*)(\d+)\.\s+(.*)", line)
        if ordered_match:
            return line

        return line

    def _standardize_emphasis(self, line: str, spec: FormatSpecification) -> str:
        """強調を標準化"""
        emphasis_style = spec.properties.get("emphasis_style", "*") if spec.properties else "*"

        if emphasis_style == "*":
            # アスタリスクに統一
            line = re.sub(r"__(.*?)__", r"**\1**", line)  # __text__ -> **text**
            line = re.sub(r"_(.*?)_", r"*\1*", line)  # _text_ -> *text*

        return line

    def _validate_markdown_spec(self, spec: FormatSpecification | None) -> FormatSpecification:
        """Markdown仕様を検証"""
        if spec is None:
            spec = self._format_specs.get(FormatType.MARKDOWN)
            if spec is None:
                msg = "Markdown仕様が設定されていません"
                raise ValidationError(msg, msg)

        if spec.format_type != FormatType.MARKDOWN:
            msg = "Markdown用の仕様ではありません"
            raise ValidationError(msg, msg)

        return spec

    def _standardize_line(self, line: str, spec: FormatSpecification, line_number: int) -> tuple[str, list[str]]:
        """単一行を標準化"""
        corrections: list[str] = []
        current_line = line

        # 見出しの標準化
        standardized_line = self._standardize_heading(current_line, spec)
        if standardized_line != current_line:
            corrections.append(f"行{line_number}: 見出し形式を標準化")
        current_line = standardized_line

        # リストの標準化
        standardized_line = self._standardize_list(current_line, spec)
        if standardized_line != current_line:
            corrections.append(f"行{line_number}: リスト形式を標準化")
        current_line = standardized_line

        # 強調の標準化
        standardized_line = self._standardize_emphasis(current_line, spec)
        if standardized_line != current_line:
            corrections.append(f"行{line_number}: 強調形式を標準化")
        current_line = standardized_line

        # 行末空白の削除
        if current_line.rstrip() != current_line:
            corrections.append(f"行{line_number}: 行末空白を削除")
            current_line = current_line.rstrip()

        return current_line, corrections

    def _normalize_empty_lines(self, content: str) -> str:
        """空行を正規化"""
        # 連続する空行を最大2行に制限
        content = re.sub(r"\n{3,}", "\n\n\n", content)
        # 文書の最後の空行を1つに
        return content.rstrip() + "\n"

    def _validate_yaml_compliance(self, content: str, spec: FormatSpecification) -> tuple[list[str], list[str]]:
        """YAML準拠性をチェック"""
        violations: list[Any] = []
        suggestions = []

        # 構文チェック
        # TODO: 検証ルールの実装が必要
        if True:  # 常に構文チェックを実行:
            try:
                yaml.safe_load(content)
            except yaml.YAMLError as e:
                violations.append(f"YAML構文エラー: {e}")

        # インデントチェック
        # TODO: 検証ルールの実装が必要
        if True:  # 常にインデントチェックを実行:
            expected_indent = spec.indent_size
            lines = content.split("\n")

            for i, line in enumerate(lines, 1):
                if line.strip() and line.startswith(" "):
                    indent = len(line) - len(line.lstrip())
                    if indent % expected_indent != 0:
                        violations.append(f"行{i}: インデントが不正(期待値: {expected_indent}の倍数)")

        return violations, suggestions

    def _validate_markdown_compliance(self, content: str, spec: FormatSpecification) -> tuple[list[str], list[str]]:
        """Markdown準拠性をチェック"""
        violations: list[Any] = []
        suggestions = []
        lines = content.split("\n")

        # 各チェックを個別メソッドに分離
        self._check_line_length(lines, spec, suggestions)
        self._check_trailing_whitespace(lines, violations)
        self._check_heading_style(lines, spec, violations)

        return violations, suggestions

    def _check_line_length(self, lines: list[str], spec: FormatSpecification, suggestions: list[str]) -> None:
        """行長チェック"""
        if not spec.max_line_length:
            return

        max_length = spec.max_line_length
        for i, line in enumerate(lines, 1):
            if len(line) > max_length:
                suggestions.append(f"行{i}: 行が長すぎます({len(line)}文字)")

    def _check_trailing_whitespace(self, lines: list[str], violations: list[str]) -> None:
        """行末空白チェック"""
        for i, line in enumerate(lines, 1):
            if line.endswith((" ", "\t")):
                violations.append(f"行{i}: 行末に不要な空白文字があります")

    def _check_heading_style(self, lines: list[str], spec: FormatSpecification, violations: list[str]) -> None:
        """見出しスタイルチェック"""
        expected_style = spec.properties.get("heading_style", "atx") if spec.properties else "atx"
        if expected_style != "atx":
            return

        for i, line in enumerate(lines, 1):
            if i < len(lines) and re.match(r"^.+\n=+$", line + "\n" + lines[i]):
                violations.append(f"行{i}: 見出しスタイルが期待値と異なります(ATX形式を推奨)")

    def _calculate_compliance_score(
        self, content: str, violations: list[str], suggestions: list[str] | None = None
    ) -> float:
        """準拠性スコアを計算"""
        if not content:
            return 0.0

        # 基本スコア
        score = 1.0

        # 違反による減点
        violation_penalty = len(violations) * 0.1
        score -= min(violation_penalty, 0.8)  # 最大80%減点

        # 提案による軽微な減点
        suggestions = suggestions or []
        suggestion_penalty = len(suggestions) * 0.02
        score -= min(suggestion_penalty, 0.2)  # 最大20%減点

        return max(score, 0.0)
