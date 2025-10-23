#!/usr/bin/env python3
"""日付・時刻のタイムゾーン問題を修正するスクリプト

DTZ011(date.today())とDTZ005(datetime.datetime.now(datetime.datetime.timezone.utc))のエラーを修正します。
"""


import re
from pathlib import Path

from noveler.infrastructure.logging.unified_logger import get_logger
from noveler.presentation.shared.shared_utilities import console

logger = get_logger(__name__)

# 削除: 不正なインポート

# 削除: 不正なインポート
def fix_timezone_in_file(file_path: Path) -> tuple[bool, dict[str, int]]:
    """ファイル内のタイムゾーン問題を修正

    Returns:
        (修正があったか, 修正内容の詳細)
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        original_content = content
    except Exception:
        return False, {}

    fixes = {
        "date.today()": 0,
        "datetime.datetime.now(datetime.datetime.timezone.utc)": 0
    }

    # インポート文を探す
    has_datetime_import = bool(re.search(r"from datetime.datetime import.*datetime.datetime", content))
    has_date_import = bool(re.search(r"from datetime.datetime import.*date", content))
    has_timezone_import = bool(re.search(r"from datetime.datetime import.*datetime.datetime.timezone", content))

    # date.today() を project_now().date に置換
    if "date.today()" in content:
        # ProjectTimezoneのインポートを追加(なければ)
        if "from noveler.domain.value_objects.project_time import" not in content:
            # 最初のimport文の後に追加
            import_match = re.search(r"^((?:from .* import .*\n|import .*\n)+)", content, re.MULTILINE)
            if import_match:
                insert_pos = import_match.end()
                content = (content[:insert_pos] +
                          content[insert_pos:])

        # date.today() を project_now().date に置換
        pattern = r"\bdate\.today\(\)"
        replacement = "project_now().date"
        content, count = re.subn(pattern, replacement, content)
        fixes["date.today()"] = count

    # datetime.datetime.now(datetime.datetime.timezone.utc) を project_now().datetime.datetime に置換
    if "datetime.datetime.now(datetime.datetime.timezone.utc)" in content:
        # ProjectTimezoneのインポートを追加(なければ)
        if "from noveler.domain.value_objects.project_time import" not in content:
            # 最初のimport文の後に追加
            import_match = re.search(r"^((?:from .* import .*\n|import .*\n)+)", content, re.MULTILINE)
            if import_match:
                insert_pos = import_match.end()
                content = (content[:insert_pos] +
                          content[insert_pos:])
        elif "project_now" not in content:
            # インポートはあるがproject_nowがない場合
            content = re.sub(
                r"(from noveler\.domain\.value_objects\.project_time import)([^\\n]+)",
                r"\1\2, project_now",
                content,
                count=1)

        # datetime.datetime.now(datetime.datetime.timezone.utc) を project_now().datetime.datetime に置換
        pattern = r"\bdatetime\.now\(\)"
        replacement = "project_now().datetime.datetime"
        content, count = re.subn(pattern, replacement, content)
        fixes["datetime.datetime.now(datetime.datetime.timezone.utc)"] = count

    # 修正があった場合のみファイルを更新
    if content != original_content:
        file_path.write_text(content, encoding="utf-8")
        return True, fixes

    return False, fixes

def main():
    """メイン処理"""
    scripts_dir = Path(__file__).parent.parent
    python_files = list(scripts_dir.rglob("*.py"))

    total_files = 0
    total_fixes = {
        "date.today()": 0,
        "datetime.datetime.now(datetime.datetime.timezone.utc)": 0
    }

    console.print("🔧 タイムゾーン問題の修正を開始します...")

    for py_file in python_files:
        # テストファイルとツール自身は除外
        if "tests" in py_file.parts or py_file == Path(__file__):
            continue

        fixed, fixes = fix_timezone_in_file(py_file)
        if fixed:
            total_files += 1
            for key, count in fixes.items():
                total_fixes[key] += count

            if any(fixes.values()):
                console.print(f"✅ {py_file.relative_to(scripts_dir)}:")
                for key, count in fixes.items():
                    if count > 0:
                        console.print(f"   - {key}: {count}箇所")

    console.print(f"\n📊 修正完了: {total_files}ファイル")
    for key, count in total_fixes.items():
        if count > 0:
            console.print(f"   - {key}: 合計{count}箇所")

if __name__ == "__main__":
    main()
