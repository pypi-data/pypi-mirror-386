#!/usr/bin/env python3
"""pytest fixtureの警告を自動修正するツール

PytestRemovedIn9Warning対応：
- fixtureデコレーターに適用されたマークを削除
- @pytest.fixtureが最後に来るように修正
"""

import re
from pathlib import Path
from typing import List, Tuple

def find_fixture_with_marks(content: str) -> List[Tuple[int, str]]:
    """fixtureにマークが適用されている箇所を検出"""
    problems = []
    lines = content.split('\n')

    for i in range(len(lines) - 1):
        current = lines[i].strip()
        next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""

        # Pattern 1: @pytest.fixture followed by @pytest.mark
        if current == "@pytest.fixture" and next_line.startswith("@pytest.mark."):
            problems.append((i, "fixture_then_mark"))

        # Pattern 2: @pytest.mark followed by @pytest.fixture
        if current.startswith("@pytest.mark.") and next_line == "@pytest.fixture":
            # Check if more marks follow
            j = i - 1
            while j >= 0 and lines[j].strip().startswith("@pytest.mark."):
                j -= 1
            problems.append((j + 1, "marks_then_fixture"))

    return problems

def fix_fixture_marks(file_path: Path) -> bool:
    """fixtureのマーク問題を修正"""
    try:
        content = file_path.read_text(encoding="utf-8")
        original = content
        lines = content.split('\n')

        # 修正が必要な箇所を検出
        problems = find_fixture_with_marks(content)

        if not problems:
            return False

        # 逆順で修正（行番号がずれないように）
        for line_num, problem_type in reversed(problems):
            if problem_type == "fixture_then_mark":
                # @pytest.fixtureの後のマークを削除
                i = line_num + 1
                while i < len(lines) and lines[i].strip().startswith("@pytest.mark."):
                    lines[i] = ""  # マーク行を削除
                    i += 1

            elif problem_type == "marks_then_fixture":
                # マークを削除してfixtureだけを残す
                i = line_num
                fixture_line = -1
                marks_to_remove = []

                # fixtureを見つけてマークを記録
                while i < len(lines):
                    if lines[i].strip() == "@pytest.fixture":
                        fixture_line = i
                        break
                    elif lines[i].strip().startswith("@pytest.mark."):
                        marks_to_remove.append(i)
                    i += 1

                # マークを削除
                for mark_line in reversed(marks_to_remove):
                    lines[mark_line] = ""

        # 空行を整理
        cleaned_lines = []
        prev_empty = False
        for line in lines:
            if line == "":
                if not prev_empty:
                    cleaned_lines.append(line)
                prev_empty = True
            else:
                cleaned_lines.append(line)
                prev_empty = False

        new_content = '\n'.join(cleaned_lines)

        if new_content != original:
            file_path.write_text(new_content, encoding="utf-8")
            return True

    except Exception as e:
        print(f"エラー: {file_path} - {e}")

    return False

def main():
    """メイン処理"""
    test_dir = Path("/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド/tests")

    # 問題のあるファイルを検索
    problem_files = []
    for py_file in test_dir.rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
            if find_fixture_with_marks(content):
                problem_files.append(py_file)
        except:
            continue

    print(f"検出されたファイル: {len(problem_files)}個")

    # 修正実行
    fixed_count = 0
    for file_path in problem_files:
        relative_path = file_path.relative_to(test_dir)
        if fix_fixture_marks(file_path):
            print(f"✅ 修正: {relative_path}")
            fixed_count += 1
        else:
            print(f"⚠️  スキップ: {relative_path}")

    print(f"\n修正完了: {fixed_count}/{len(problem_files)} ファイル")

if __name__ == "__main__":
    main()
