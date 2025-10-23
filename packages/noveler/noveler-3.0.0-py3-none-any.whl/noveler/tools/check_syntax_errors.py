"""構文エラーチェック用スクリプト

すべてのPythonファイルの構文エラーをチェックし、一覧表示する
"""
import argparse
import ast
import sys
from pathlib import Path

from noveler.presentation.shared.shared_utilities import console



def check_syntax(file_path: Path) -> tuple[bool, str]:
    """ファイルの構文をチェック

    Returns:
        (成功フラグ, エラーメッセージ)
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        ast.parse(content)
        return (True, "")
    except SyntaxError as e:
        return (False, f"Line {e.lineno}: {e.msg}")
    except Exception as e:
        return (False, str(e))

def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description="構文エラーチェック")
    parser.add_argument("--quiet", action="store_true", help="エラー時のみ出力")
    args = parser.parse_args()
    script_dir = Path(__file__).parent.parent
    error_files = []
    for py_file in script_dir.rglob("*.py"):
        if any(part in str(py_file) for part in ["__pycache__", ".git", "backup", "temp"]):
            continue
        (success, error_msg) = check_syntax(py_file)
        if not success:
            error_files.append((py_file, error_msg))
    if error_files:
        if not args.quiet:
            console.print(f"❌ {len(error_files)} ファイルに構文エラーが見つかりました:\n")
            for (file_path, error_msg) in error_files:
                rel_path = file_path.relative_to(script_dir)
                console.print(f"  • {rel_path}: {error_msg}")
    elif not args.quiet:
        console.print("✅ すべてのファイルの構文チェックが成功しました")
    return len(error_files)
if __name__ == "__main__":
    sys.exit(main())
