#!/usr/bin/env python3
"""Phase 4+ PTH123 Path API現代化ツール

53件のPTH123（builtin-open）を手動でPath APIに現代化する。
構文エラーのあるファイルをスキップして、正常なファイルのみを対象とする。

修正パターン:
- open(file_path) → Path(file_path).open()
- with open(file_path) as f: → with Path(file_path).open() as f:
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from noveler.infrastructure.logging.unified_logger import get_logger
from noveler.presentation.shared.shared_utilities import get_console


class Phase4PTH123Fixer:
    """PTH123 Path API現代化エンジン"""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.console = get_console()
        self.fixed_files: list[Path] = []
        self.fix_count = 0

    def fix_all_pth123(self, project_root: Path) -> dict[str, Any]:
        """全PTH123を修正"""
        self.console.print("[yellow]🔧 Phase 4+ PTH123 Path API現代化開始...[/yellow]")

        # PTH123対象ファイルを特定（構文エラーチェック付き）
        pth123_files = self._find_valid_pth123_files(project_root)
        self.console.print(f"🎯 PTH123対象ファイル: {len(pth123_files)}件（構文正常ファイルのみ）")

        for py_file in pth123_files:
            try:
                if self._fix_single_pth123_file(py_file):
                    self.fixed_files.append(py_file)
            except Exception as e:
                self.logger.exception(f"PTH123修正エラー {py_file}: {e}")

        return self._generate_pth123_report()

    def _find_valid_pth123_files(self, project_root: Path) -> list[Path]:
        """構文正常なPTH123対象ファイルを特定"""
        valid_files = []

        # 全Pythonファイルを取得
        all_py_files = list((project_root / "src").rglob("*.py"))

        for py_file in all_py_files:
            try:
                # 構文チェック
                subprocess.run([
                    "python3", "-m", "py_compile", str(py_file)
                ], check=True, capture_output=True)

                # PTH123エラーチェック
                result = subprocess.run([
                    "ruff", "check", str(py_file), "--select=PTH123"
                ], check=False, capture_output=True, text=True)

                if result.returncode != 0 and "PTH123" in result.stderr:
                    valid_files.append(py_file)

            except subprocess.CalledProcessError:
                # 構文エラーファイルはスキップ
                continue
            except Exception as e:
                self.logger.warning(f"ファイル検査失敗 {py_file}: {e}")
                continue

        return valid_files

    def _fix_single_pth123_file(self, file_path: Path) -> bool:
        """単一ファイルのPTH123修正"""
        if not file_path.exists():
            return False

        try:
            content = file_path.read_text(encoding="utf-8")
            original_content = content
            fixes_made = 0

            # パターン1: with open(file_path, ...) as f:
            pattern1 = r"with\s+open\s*\(\s*([^,\)]+)([^)]*)\)\s+as\s+(\w+):"
            def replace1(match) -> str:
                nonlocal fixes_made
                path_expr = match.group(1).strip()
                args = match.group(2)
                var_name = match.group(3)
                fixes_made += 1
                return f'with Path({path_expr}).open({args.lstrip(",").strip()}) as {var_name}:'

            content = re.sub(pattern1, replace1, content)

            # パターン2: file.read() -> Path(file).read_text()
            pattern2 = r"(\w+)\s*=\s*open\s*\(\s*([^,\)]+)([^)]*)\)\s*\.read\s*\(\s*\)"
            def replace2(match) -> str:
                nonlocal fixes_made
                var_name = match.group(1)
                path_expr = match.group(2).strip()
                args = match.group(3)
                fixes_made += 1
                if "encoding" in args:
                    # encoding引数を抽出
                    encoding_match = re.search(r'encoding\s*=\s*["\']([^"\']+)["\']', args)
                    encoding = f'encoding="{encoding_match.group(1)}"' if encoding_match else 'encoding="utf-8"'
                    return f"{var_name} = Path({path_expr}).read_text({encoding})"
                return f'{var_name} = Path({path_expr}).read_text(encoding="utf-8")'

            content = re.sub(pattern2, replace2, content)

            # パターン3: simple open() assignment
            pattern3 = r"(\w+)\s*=\s*open\s*\(\s*([^,\)]+)([^)]*)\)"
            def replace3(match) -> str:
                nonlocal fixes_made
                var_name = match.group(1)
                path_expr = match.group(2).strip()
                args = match.group(3)
                fixes_made += 1
                return f'{var_name} = Path({path_expr}).open({args.lstrip(",").strip()})'

            content = re.sub(pattern3, replace3, content)

            if fixes_made == 0:
                return False

            # Pathインポート追加
            if "from pathlib import Path" not in content and "import Path" not in content:
                # 既存のimport文の後に追加
                if "import" in content:
                    import_lines = []
                    other_lines = []
                    in_imports = True

                    for line in content.splitlines():
                        if (in_imports and (line.strip().startswith("import ") or line.strip().startswith("from "))) or (in_imports and line.strip() == ""):
                            import_lines.append(line)
                        else:
                            if in_imports:
                                import_lines.append("from pathlib import Path")
                                import_lines.append("")
                                in_imports = False
                            other_lines.append(line)

                    if in_imports:  # ファイル全体がimportだった場合
                        import_lines.append("from pathlib import Path")

                    content = "\n".join(import_lines + other_lines)
                else:
                    content = "from pathlib import Path\n\n" + content

            # 変更をファイルに保存
            return self._save_pth123_fix(file_path, content, original_content, fixes_made)

        except Exception as e:
            self.logger.exception(f"PTH123修正失敗 {file_path}: {e}")
            return False

    def _save_pth123_fix(self, file_path: Path, new_content: str, original_content: str, fixes_made: int) -> bool:
        """PTH123修正をファイルに保存"""
        try:
            # バックアップ作成
            backup_path = file_path.with_suffix(file_path.suffix + ".pth123_backup")
            backup_path.write_text(original_content, encoding="utf-8")

            # 修正版を書き込み
            file_path.write_text(new_content, encoding="utf-8")

            # 構文チェック
            subprocess.run([
                "python3", "-m", "py_compile", str(file_path)
            ], check=True, capture_output=True)

            self.fix_count += fixes_made
            self.console.print(f"🔧 PTH123修正完了: {file_path.name} ({fixes_made}箇所)")

            return True

        except Exception as e:
            # 修正失敗時はバックアップから復元
            if backup_path.exists():
                file_path.write_text(original_content, encoding="utf-8")
                backup_path.unlink()

            self.logger.exception(f"PTH123修正保存失敗 {file_path}: {e}")
            return False

    def _generate_pth123_report(self) -> dict[str, Any]:
        """PTH123修正結果レポート生成"""
        return {
            "fixed_files_count": len(self.fixed_files),
            "total_fixes": self.fix_count,
            "fixed_files": [str(f) for f in self.fixed_files],
            "average_fixes_per_file": self.fix_count / max(1, len(self.fixed_files))
        }


def main() -> None:
    """メイン実行関数"""
    console = get_console()
    logger = get_logger(__name__)

    try:
        # プロジェクトルート検出
        project_root = Path.cwd()

        console.print("[blue]🚀 Phase 4+ リファクタリング: PTH123 Path API現代化開始[/blue]")

        # PTH123修正実行
        fixer = Phase4PTH123Fixer()
        result = fixer.fix_all_pth123(project_root)

        # 結果レポート
        console.print("\n📊 [green]Phase 4+ PTH123 Path API現代化完了[/green]")
        console.print(f"🔧 修正ファイル: {result['fixed_files_count']}件")
        console.print(f"⚡ 総修正箇所: {result['total_fixes']}箇所")
        console.print(f"📈 ファイル当たり平均: {result['average_fixes_per_file']:.1f}箇所")

        if result["fixed_files"]:
            console.print("\n🔧 修正ファイル一覧:")
            for file_path in result["fixed_files"][:10]:  # 上位10件表示
                console.print(f"  - {Path(file_path).name}")

        logger.info(f"Phase 4+ PTH123修正完了: {result['total_fixes']}箇所修正")

    except Exception as e:
        console.print(f"[red]❌ Phase 4+ PTH123修正失敗: {e}[/red]")
        logger.exception(f"PTH123修正失敗: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
