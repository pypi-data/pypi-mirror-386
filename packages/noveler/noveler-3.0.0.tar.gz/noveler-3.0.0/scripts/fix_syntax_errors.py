#!/usr/bin/env python3
"""
構文エラー一括修正スクリプト

重複したproject_nowインポートを修正
"""

import re
import subprocess
from pathlib import Path


def fix_duplicate_project_now_imports():
    """重複したproject_nowインポート行を修正"""

    # src/ディレクトリ内の全Pythonファイルを取得
    src_path = Path("src")
    python_files = list(src_path.rglob("*.py"))

    fixed_count = 0

    for file_path in python_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # パターン1: from文の途中に別のfrom文が挿入されているパターンを修正
            # 例: from noveler.domain.versioning.value_objects import (
            #     from noveler.domain.value_objects.project_time import project_now
            #     BidirectionalForeshadowingImpact,
            pattern1 = r'(from\s+[\w.]+\s+import\s+\(\s*)\n(from\s+noveler\.domain\.value_objects\.project_time\s+import\s+project_now)\s*\n(\s*)([A-Z]\w+)'

            def replace_pattern1(match):
                import_start = match.group(1)
                duplicate_import = match.group(2)  # この行を削除
                indent = match.group(3)
                first_import = match.group(4)
                return f"{import_start}\n{indent}{first_import}"

            content = re.sub(pattern1, replace_pattern1, content, flags=re.MULTILINE)

            # パターン2: 単体行の重複インポートを削除
            # from noveler.domain.value_objects.project_time import project_now が2回以上出現する場合
            lines = content.split('\n')
            project_now_import_count = 0
            new_lines = []

            for line in lines:
                if re.match(r'^\s*from\s+noveler\.domain\.value_objects\.project_time\s+import\s+project_now\s*$', line.strip()):
                    project_now_import_count += 1
                    if project_now_import_count == 1:
                        # 初回のみ保持
                        new_lines.append(line)
                    # 2回目以降は削除（追加しない）
                else:
                    new_lines.append(line)

            content = '\n'.join(new_lines)

            # パターン3: TYPE_CHECKINGブロック内での重複修正
            # if TYPE_CHECKING: の後に続くfrom文の重複を修正
            pattern3 = r'(if\s+TYPE_CHECKING:\s*\n(?:\s*.*\n)*?)\s*(from\s+noveler\.domain\.value_objects\.project_time\s+import\s+project_now)\s*\n'

            # TYPE_CHECKINGブロック外に既にproject_nowインポートがある場合、ブロック内から削除
            if 'from noveler.domain.value_objects.project_time import' in content:
                content = re.sub(pattern3, r'\1', content, flags=re.MULTILINE)

            # 変更があった場合のみファイルを更新
            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                fixed_count += 1
                print(f"修正: {file_path}")

        except Exception as e:
            print(f"エラー修正失敗 {file_path}: {e}")

    return fixed_count


def main():
    """メイン処理"""
    print("構文エラー一括修正開始...")

    # 修正前のエラー数確認
    result = subprocess.run(['ruff', 'check', 'src/', '--statistics'], capture_output=True, text=True)
    if result.returncode == 0:
        print("エラーなし")
        return

    lines = result.stdout.split('\n')
    syntax_errors_before = 0
    for line in lines:
        if 'invalid-syntax' in line:
            # エラー数を抽出
            parts = line.split('\t')
            if len(parts) > 0:
                try:
                    syntax_errors_before = int(parts[0])
                    break
                except ValueError:
                    pass

    print(f"修正前の構文エラー数: {syntax_errors_before}")

    # 修正実行
    fixed_count = fix_duplicate_project_now_imports()
    print(f"修正されたファイル数: {fixed_count}")

    # 修正後のエラー数確認
    result = subprocess.run(['ruff', 'check', 'src/', '--statistics'], capture_output=True, text=True)
    lines = result.stdout.split('\n')
    syntax_errors_after = 0
    for line in lines:
        if 'invalid-syntax' in line:
            parts = line.split('\t')
            if len(parts) > 0:
                try:
                    syntax_errors_after = int(parts[0])
                    break
                except ValueError:
                    pass

    print(f"修正後の構文エラー数: {syntax_errors_after}")
    print(f"削減されたエラー数: {syntax_errors_before - syntax_errors_after}")


if __name__ == "__main__":
    main()
