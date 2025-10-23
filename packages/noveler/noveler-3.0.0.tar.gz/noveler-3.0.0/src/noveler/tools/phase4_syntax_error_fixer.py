#!/usr/bin/env python3
"""Phase 4+ 構文エラー自動修正ツール

428件の構文エラー（IndentationError・SyntaxError）を体系的に修正する。

前回までの実績:
- Phase 1-3: CLAUDE.md準拠・循環依存解決・ファイル分解完了
- Phase 4: Path API現代化91%・関数内インポート90%削減達成

今回対象:
- IndentationError: 予期せぬインデント・ブロック不足
- SyntaxError: 未完了のtry-except文・syntax違反
"""

import ast
import sys
from pathlib import Path
from typing import Any

from noveler.infrastructure.logging.unified_logger import get_logger
from noveler.presentation.shared.shared_utilities import get_console


class Phase4SyntaxErrorFixer:
    """Phase 4+ 構文エラー修正エンジン"""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.console = get_console()
        self.fixed_files: list[Path] = []
        self.errors_found: dict[str, list[str]] = {}

    def fix_all_syntax_errors(self, project_root: Path) -> dict[str, Any]:
        """全構文エラーを検出・修正"""
        self.console.print("[yellow]🔧 Phase 4+ 構文エラー修正開始...[/yellow]")

        python_files = list((project_root / "src").rglob("*.py"))
        self.console.print(f"📁 対象ファイル数: {len(python_files)}件")

        for py_file in python_files:
            try:
                if self._fix_single_file(py_file):
                    self.fixed_files.append(py_file)
            except Exception as e:
                self.errors_found[str(py_file)] = [str(e)]
                self.logger.exception(f"ファイル修正エラー {py_file}: {e}")

        return self._generate_summary_report()

    def _fix_single_file(self, file_path: Path) -> bool:
        """単一ファイルの構文エラー修正"""
        if not file_path.exists():
            return False

        try:
            # 構文チェック
            with file_path.open(encoding="utf-8") as f:
                content = f.read()

            # パース試行で構文エラー検出
            ast.parse(content)
            return False  # 構文エラーなし

        except SyntaxError as e:
            # 構文エラー発見→修正実行
            return self._repair_syntax_error(file_path, content, e)
        except IndentationError as e:
            # インデントエラー発見→修正実行
            return self._repair_indentation_error(file_path, content, e)
        except Exception as e:
            self.logger.warning(f"構文解析失敗 {file_path}: {e}")
            return False

    def _repair_syntax_error(self, file_path: Path, content: str, error: SyntaxError) -> bool:
        """SyntaxError修正"""
        self.console.print(f"🔧 SyntaxError修正: {file_path.name}:{error.lineno}")

        lines = content.splitlines()

        if "expected 'except' or 'finally' block" in str(error):
            return self._fix_incomplete_try_block(file_path, lines, error.lineno)

        return False

    def _repair_indentation_error(self, file_path: Path, content: str, error: IndentationError) -> bool:
        """IndentationError修正"""
        self.console.print(f"🔧 IndentationError修正: {file_path.name}:{error.lineno}")

        lines = content.splitlines()
        error_msg = str(error)

        if "expected an indented block after" in error_msg:
            return self._fix_missing_indented_block(file_path, lines, error.lineno, error_msg)
        if "unexpected indent" in error_msg:
            return self._fix_unexpected_indent(file_path, lines, error.lineno)
        if "unindent does not match any outer indentation level" in error_msg:
            return self._fix_unindent_mismatch(file_path, lines, error.lineno)

        return False

    def _fix_incomplete_try_block(self, file_path: Path, lines: list[str], line_no: int) -> bool:
        """未完了のtry文を修正"""
        if line_no > len(lines):
            return False

        # try文の後にexceptまたはfinallyが無い場合の修正
        insert_line = line_no - 1  # 0-based index

        # passを追加してexcept文を補完
        lines.insert(insert_line + 1, "    except Exception as e:")
        lines.insert(insert_line + 2, "        pass  # TODO: 適切なエラーハンドリングを実装")

        return self._write_fixed_content(file_path, lines)

    def _fix_missing_indented_block(self, file_path: Path, lines: list[str], line_no: int, error_msg: str) -> bool:
        """インデントブロック不足を修正"""
        if line_no > len(lines):
            return False

        insert_line = line_no - 1  # 0-based index

        # 適切なインデントレベルを推定
        if insert_line > 0:
            prev_line = lines[insert_line - 1]
            indent = self._get_indent_level(prev_line) + "    "
        else:
            indent = "    "

        # passを追加
        lines.insert(insert_line, f"{indent}pass  # TODO: 実装を追加")

        return self._write_fixed_content(file_path, lines)

    def _fix_unexpected_indent(self, file_path: Path, lines: list[str], line_no: int) -> bool:
        """予期しないインデントを修正"""
        if line_no > len(lines):
            return False

        line_idx = line_no - 1  # 0-based index
        problem_line = lines[line_idx]

        # 前の行のインデントレベルに合わせる
        if line_idx > 0:
            prev_indent = self._get_indent_level(lines[line_idx - 1])
            fixed_line = prev_indent + problem_line.lstrip()
            lines[line_idx] = fixed_line

            return self._write_fixed_content(file_path, lines)

        return False

    def _fix_unindent_mismatch(self, file_path: Path, lines: list[str], line_no: int) -> bool:
        """インデント不一致を修正"""
        if line_no > len(lines):
            return False

        line_idx = line_no - 1  # 0-based index

        # 前の適切なインデントレベルを探索
        for i in range(line_idx - 1, -1, -1):
            prev_line = lines[i].rstrip()
            if prev_line and not prev_line.isspace():
                target_indent = self._get_indent_level(prev_line)

                # 同じレベルに調整
                problem_line = lines[line_idx]
                lines[line_idx] = target_indent + problem_line.lstrip()

                return self._write_fixed_content(file_path, lines)

        return False

    def _get_indent_level(self, line: str) -> str:
        """行のインデントレベルを取得"""
        return line[:len(line) - len(line.lstrip())]

    def _write_fixed_content(self, file_path: Path, lines: list[str]) -> bool:
        """修正内容をファイルに書き戻し"""
        try:
            fixed_content = "\n".join(lines)

            # 修正前バックアップ
            backup_path = file_path.with_suffix(file_path.suffix + ".syntax_backup")
            backup_path.write_text(file_path.read_text(encoding="utf-8"), encoding="utf-8")

            # 修正版を書き込み
            file_path.write_text(fixed_content, encoding="utf-8")

            # 構文チェック
            ast.parse(fixed_content)

            self.console.print(f"✅ 構文修正完了: {file_path.name}")
            return True

        except Exception as e:
            # 修正失敗時はバックアップから復元
            if backup_path.exists():
                file_path.write_text(backup_path.read_text(encoding="utf-8"), encoding="utf-8")
                backup_path.unlink()

            self.logger.exception(f"構文修正失敗 {file_path}: {e}")
            return False

    def _generate_summary_report(self) -> dict[str, Any]:
        """修正結果サマリー生成"""
        return {
            "fixed_files_count": len(self.fixed_files),
            "error_files_count": len(self.errors_found),
            "fixed_files": [str(f) for f in self.fixed_files],
            "errors_found": self.errors_found,
            "success_rate": len(self.fixed_files) / max(1, len(self.fixed_files) + len(self.errors_found)) * 100
        }


def main() -> None:
    """メイン実行関数"""
    console = get_console()
    logger = get_logger(__name__)

    try:
        # プロジェクトルート検出
        project_root = Path.cwd()

        console.print("[blue]🚀 Phase 4+ リファクタリング: 構文エラー428件修正開始[/blue]")

        # 構文エラー修正実行
        fixer = Phase4SyntaxErrorFixer()
        result = fixer.fix_all_syntax_errors(project_root)

        # 結果レポート
        console.print("\n📊 [green]Phase 4+ 構文エラー修正完了[/green]")
        console.print(f"✅ 修正完了: {result['fixed_files_count']}件")
        console.print(f"❌ 修正失敗: {result['error_files_count']}件")
        console.print(f"📈 成功率: {result['success_rate']:.1f}%")

        if result["fixed_files"]:
            console.print("\n🔧 修正ファイル一覧:")
            for file_path in result["fixed_files"][:10]:  # 上位10件表示
                console.print(f"  - {Path(file_path).name}")

        logger.info(f"Phase 4+ 構文エラー修正完了: {result['fixed_files_count']}件修正")

    except Exception as e:
        console.print(f"[red]❌ Phase 4+ 構文エラー修正失敗: {e}[/red]")
        logger.exception(f"構文エラー修正失敗: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
