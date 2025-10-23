#!/usr/bin/env python3
"""構文エラー修正ツール

Pythonファイルの構文エラーを検出・修正するインフラストラクチャ層のツール。
DDD準拠のアーキテクチャに従い、技術的な詳細実装を提供。
"""

import ast
import re
from enum import Enum
from pathlib import Path
from typing import Any


class FixMode(Enum):
    """修正モード"""

    SAFE = "safe"
    NORMAL = "normal"
    AGGRESSIVE = "aggressive"
    CHECK_ONLY = "check"


class SyntaxFixer:
    """構文エラー修正クラス"""

    def __init__(self, mode: FixMode = FixMode.NORMAL, logger_service=None, console_service=None) -> None:
        """初期化

        Args:
            mode: 修正モード
        """
        self.mode = mode
        self.project_root = Path(__file__).parent.parent.parent
        self.fixes_applied = 0
        self.files_fixed = 0
        self.files_checked = 0

        self.logger_service = logger_service
        self.console_service = console_service
    def check_syntax(self, file_path: Path) -> tuple[bool, str | None]:
        """構文エラーをチェック

        Args:
            file_path: チェック対象ファイル

        Returns:
            (エラーなしフラグ, エラーメッセージ)
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            ast.parse(content)
            return True, None
        except SyntaxError as e:
            return False, f"Line {e.lineno}: {e.msg}"
        except Exception as e:
            return False, str(e)

    def fix_file(self, file_path: Path, dry_run: bool = False) -> bool:
        """ファイルの構文エラーを修正

        Args:
            file_path: 対象ファイル
            dry_run: 実際に修正せずチェックのみ

        Returns:
            修正成功フラグ
        """
        try:
            original_content = file_path.read_text(encoding="utf-8")
            try:
                ast.parse(original_content)
                return False
            except SyntaxError as e:
                error_msg = str(e.msg)
                error_line = e.lineno

            fixed_content = self._apply_fixes(original_content, error_msg, error_line)

            if fixed_content != original_content:
                try:
                    ast.parse(fixed_content)

                    if not dry_run:
                        if self.mode == FixMode.SAFE:
                            backup_path = file_path.with_suffix(file_path.suffix + ".bak")
                            # バッチ書き込みを使用
                            backup_path.write_text(original_content, encoding="utf-8")

                        # バッチ書き込みを使用
                        file_path.write_text(fixed_content, encoding="utf-8")

                    self.fixes_applied += 1
                    return True

                except SyntaxError:
                    if self.mode == FixMode.AGGRESSIVE:
                        return self._aggressive_fix(file_path, fixed_content, dry_run)
                    return False

            return False

        except Exception:
            return False

    def _apply_fixes(self, content: str, error_msg: str, error_line: int) -> str:
        """エラーに応じた修正を適用

        Args:
            content: ファイル内容
            error_msg: エラーメッセージ
            error_line: エラー行番号

        Returns:
            修正後の内容
        """
        lines = content.split("\n")

        if "unmatched ')'" in error_msg.lower():
            return self._fix_unmatched_paren(lines)
        if "unexpected indent" in error_msg.lower():
            return self._fix_unexpected_indent(lines, error_line)
        if "invalid syntax" in error_msg.lower():
            return self._fix_invalid_syntax(lines, error_line)
        if "'(' was never closed" in error_msg.lower():
            return self._fix_unclosed_paren(lines, error_line)
        if "perhaps you forgot a comma" in error_msg.lower():
            return self._fix_missing_comma(lines, error_line)

        return content

    def _fix_unmatched_paren(self, lines: list[str]) -> str:
        """unmatched ')' エラーを修正

        Args:
            lines: ファイルの行リスト

        Returns:
            修正後の内容
        """
        fixed_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]

            if line.strip() == ")":
                prev_idx = i - 1
                while prev_idx >= 0 and not lines[prev_idx].strip():
                    prev_idx -= 1

                if prev_idx >= 0:
                    prev_line = lines[prev_idx]
                    if "#" in prev_line and "(" in prev_line:
                        if prev_line.count("(") > prev_line.count(")"):
                            fixed_lines[prev_idx] = prev_line.rstrip() + ")"
                            i += 1
                            continue
                    elif "#" in prev_line and not prev_line.rstrip().endswith(")"):
                        fixed_lines[prev_idx] = prev_line.rstrip() + ")"
                        i += 1
                        continue

            fixed_lines.append(line)
            i += 1

        return "\n".join(fixed_lines)

    def _fix_unexpected_indent(self, lines: list[str], error_line: int) -> str:
        """unexpected indent エラーを修正

        Args:
            lines: ファイルの行リスト
            error_line: エラー行番号

        Returns:
            修正後の内容
        """
        if 0 < error_line <= len(lines):
            line_idx = error_line - 1
            line = lines[line_idx]

            if line.strip():
                lines[line_idx] = line.lstrip()

        return "\n".join(lines)

    def _fix_invalid_syntax(self, lines: list[str], error_line: int) -> str:
        """invalid syntax エラーを修正

        Args:
            lines: ファイルの行リスト
            error_line: エラー行番号

        Returns:
            修正後の内容
        """
        if 0 < error_line <= len(lines):
            line_idx = error_line - 1
            line = lines[line_idx]

            if (
                (re.match(r"^\s*if\s+.*[^:]$", line) and ":" not in line)
                or (re.match(r"^\s*for\s+.*[^:]$", line) and ":" not in line)
                or (re.match(r"^\s*while\s+.*[^:]$", line) and ":" not in line)
            ):
                lines[line_idx] = line + ":"

        return "\n".join(lines)

    def _fix_unclosed_paren(self, lines: list[str], error_line: int) -> str:
        """'(' was never closed エラーを修正

        Args:
            lines: ファイルの行リスト
            error_line: エラー行番号

        Returns:
            修正後の内容
        """
        if 0 < error_line <= len(lines):
            line_idx = error_line - 1
            line = lines[line_idx]

            open_count = line.count("(")
            close_count = line.count(")")

            if open_count > close_count:
                missing = open_count - close_count
                lines[line_idx] = line.rstrip() + ")" * missing

        return "\n".join(lines)

    def _fix_missing_comma(self, lines: list[str], error_line: int) -> str:
        """カンマ不足エラーを修正

        Args:
            lines: ファイルの行リスト
            error_line: エラー行番号

        Returns:
            修正後の内容
        """
        if 0 < error_line <= len(lines):
            line_idx = error_line - 1
            line = lines[line_idx]

            if not line.rstrip().endswith(",") and not line.rstrip().endswith(":"):
                if line_idx + 1 < len(lines):
                    next_line = lines[line_idx + 1]
                    if next_line.strip() and not next_line.strip().startswith("#"):
                        lines[line_idx] = line.rstrip() + ","

        return "\n".join(lines)

    def _aggressive_fix(self, file_path: Path, content: str, dry_run: bool) -> bool:
        """積極的な修正（複数のエラーパターンを順次修正）

        Args:
            file_path: 対象ファイル
            content: ファイル内容
            dry_run: ドライランフラグ

        Returns:
            修正成功フラグ
        """
        max_iterations = 5
        iteration = 0

        while iteration < max_iterations:
            try:
                ast.parse(content)
                if not dry_run:
                    # バッチ書き込みを使用
                    file_path.write_text(content, encoding="utf-8")
                return True
            except SyntaxError as e:
                content = self._apply_fixes(content, str(e.msg), e.lineno)
                iteration += 1

        return False

    def process_directory(self, directory: Path, recursive: bool = True, dry_run: bool = False) -> None:
        """ディレクトリ内のPythonファイルを処理

        Args:
            directory: 対象ディレクトリ
            recursive: 再帰的処理フラグ
            dry_run: ドライランフラグ
        """
        pattern = "**/*.py" if recursive else "*.py"
        py_files = list(directory.glob(pattern))

        self.console_service.print(f"\n🔍 {len(py_files)} ファイルを処理中...")

        errors: list[Any] = []
        for py_file in py_files:
            self.files_checked += 1

            if self.mode == FixMode.CHECK_ONLY:
                is_valid, error_msg = self.check_syntax(py_file)
                if not is_valid:
                    errors.append(f"{py_file.relative_to(self.project_root)}: {error_msg}")
            elif self.fix_file(py_file, dry_run):
                self.files_fixed += 1
                status = "🔧 修正済み" if not dry_run else "✅ 修正可能"
                self.console_service.print(f"{status}: {py_file.relative_to(self.project_root)}")

        if self.mode == FixMode.CHECK_ONLY:
            if errors:
                self.console_service.print(f"\n❌ {len(errors)} ファイルにエラーが見つかりました:")
                for error in errors[:20]:
                    self.console_service.print(f"  • {error}")
                if len(errors) > 20:
                    self.console_service.print(f"  ... 他 {len(errors) - 20} 件")
            else:
                self.console_service.print("\n✅ すべてのファイルで構文エラーなし")
        else:
            self.console_service.print("\n📊 結果:")
            self.console_service.print(f"  • チェック: {self.files_checked} ファイル")
            self.console_service.print(f"  • 修正: {self.files_fixed} ファイル")
            if dry_run:
                self.console_service.print("  ※ ドライラン実行のため、実際の修正は行われていません")
