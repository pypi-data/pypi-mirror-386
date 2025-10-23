#!/usr/bin/env python3
"""ログでのf-string使用を修正するスクリプト

G004エラー(logging-f-string)を%形式に修正します。
"""

import re
from pathlib import Path

from noveler.presentation.shared.shared_utilities import console


def fix_logging_fstrings_in_file(file_path: Path) -> tuple[bool, int]:
    """ファイル内のログのf-string使用を修正

    Returns:
        (修正があったか, 修正数)
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        original_content = content
    except Exception:
        return False, 0

    fixes = 0

    # self._logger.メソッド(f"...") のパターンを探す
    patterns = [
        (r'(self._logger\.(debug|info|warning|error|critical))\(f(["\'])([^"\']+)\3\)',
         lambda m: _convert_fstring_to_percent(m)),
        (r'(logging\.(debug|info|warning|error|critical))\(f(["\'])([^"\']+)\3\)',
         lambda m: _convert_fstring_to_percent(m)),
    ]

    for pattern, replacer in patterns:
        matches = list(re.finditer(pattern, content))
        # 後ろから置換していく(位置がずれないように)
        for match in reversed(matches):
            old_text = match.group(0)
            new_text = replacer(match)
            if old_text != new_text:
                content = content[:match.start()] + new_text + content[match.end():]
                fixes += 1

    # 修正があった場合のみファイルを更新
    if content != original_content:
        file_path.write_text(content, encoding="utf-8")
        return True, fixes

    return False, fixes

def _convert_fstring_to_percent(match: re.Match) -> str:
    """f-stringを%形式に変換"""
    logger_call = match.group(1)
    quote = match.group(3)
    fstring_content = match.group(4)

    # {変数}を抽出して%sに置換
    variables = []

    def replacer(m):
        var_expr = m.group(1)
        # 単純な変数名の場合
        if re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", var_expr):
            variables.append(var_expr)
        else:
            # より複雑な式の場合(例: obj.attr, func()等)
            variables.append(f"({var_expr})")
        return "%s"

    # {expr}を%sに置換
    new_content = re.sub(r"\{([^}]+)\}", replacer, fstring_content)

    if variables:
        # 変数がある場合は%形式で
        return f'{logger_call}({quote}{new_content}{quote}, {", ".join(variables)})'
    # 変数がない場合は単純な文字列
    return f"{logger_call}({quote}{new_content}{quote})"

def main():
    """メイン処理"""
    scripts_dir = Path(__file__).parent.parent
    python_files = list(scripts_dir.rglob("*.py"))

    total_files = 0
    total_fixes = 0

    console.print("🔧 ログのf-string使用の修正を開始します...")

    for py_file in python_files:
        # ツール自身は除外
        if py_file == Path(__file__):
            continue

        fixed, count = fix_logging_fstrings_in_file(py_file)
        if fixed:
            total_files += 1
            total_fixes += count
            console.print(f"✅ {py_file.relative_to(scripts_dir)}: {count}箇所を修正")

    console.print(f"\n📊 修正完了: {total_files}ファイル、{total_fixes}箇所")

if __name__ == "__main__":
    main()
