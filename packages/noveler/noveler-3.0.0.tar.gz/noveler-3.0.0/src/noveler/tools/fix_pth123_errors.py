#!/usr/bin/env python3
"""PTH123: builtin-open エラーを修正

open()をPath.open()に置き換えます。
"""

import ast
import re
from pathlib import Path

def fix_builtin_open(file_path: Path) -> bool:
    """builtin openをPath.open()に修正

    Args:
        file_path: 対象ファイル

    Returns:
        修正が行われたかどうか
    """
    try:
        content = file_path.read_text(encoding="utf-8")

        lines = content.split("\n")
        modified = False
        has_path_import = False

        # Pathのインポートがあるか確認
        for line in lines:
            if "from pathlib import" in line and "Path" in line:
                has_path_import = True
                break

        # Pathインポートがない場合は追加
        if not has_path_import:
            # 最初のインポート文を探す
            for i, line in enumerate(lines):
                if line.startswith("import ") or line.startswith("from "):
                    lines.insert(i, "from pathlib import Path")
                    modified = True
                    has_path_import = True
                    break

        # open()をPath().open()に置き換え
        for i, line in enumerate(lines):
            # with open(xxx) as f: パターン
            match = re.search(r"with\s+open\(([^,\)]+)(?:,\s*([^)]*))?\)\s+as\s+(\w+):", line)
            if match:
                file_arg = match.group(1).strip()
                mode_args = match.group(2) if match.group(2) else ""
                var_name = match.group(3)

                # ファイル引数がPath()でラップされていない場合
                if not file_arg.startswith("Path("):
                    # mode_argsがある場合は整形
                    if mode_args:
                        mode_args = ", " + mode_args

                    new_line = line[:match.start()]
                    new_line += f"with Path({file_arg}).open({mode_args}) as {var_name}:"
                    new_line += line[match.end():]

                    lines[i] = new_line
                    modified = True

            # open(xxx).read() パターン
            elif "open(" in line and "Path(" not in line:
                # open(xxx, ...) を Path(xxx).open(...) に置き換え
                pattern = r"open\(([^,\)]+)(?:,\s*([^)]*))?\)"

                def replacer(m):
                    file_arg = m.group(1).strip()
                    mode_args = m.group(2) if m.group(2) else ""

                    if mode_args:
                        return f"Path({file_arg}).open({mode_args})"
                    return f"Path({file_arg}).open()"

                new_line = re.sub(pattern, replacer, line)
                if new_line != line:
                    lines[i] = new_line
                    modified = True

        if modified:
            new_content = "\n".join(lines)

            # 構文チェック
            try:
                ast.parse(new_content)
                # バッチ書き込みを使用
                file_path.write_text(new_content, encoding="utf-8")
                return True
            except SyntaxError:
                return False

        return False

    except Exception:
        return False

def main():
    """メイン処理"""
    scripts_dir = Path("scripts")
    fixed_count = 0

    print("=== Fixing PTH123: builtin-open errors ===")

    # 特定の重要ファイルから修正
    important_files = [
        "noveler/infrastructure/tools/syntax_fixer.py",
        "noveler/tools/syntax_fixer_ddd.py",
        "noveler/tools/unified_syntax_fixer.py",
    ]

    for file_path in important_files:
        py_file = Path(file_path)
        if py_file.exists() and fix_builtin_open(py_file):
            print(f"Fixed: {py_file}")
            fixed_count += 1

    # その他のファイル
    for py_file in scripts_dir.rglob("*.py"):
        if str(py_file) not in important_files:
            if fix_builtin_open(py_file):
                print(f"Fixed: {py_file}")
                fixed_count += 1

    print(f"Total files fixed: {fixed_count}")

if __name__ == "__main__":
    main()
