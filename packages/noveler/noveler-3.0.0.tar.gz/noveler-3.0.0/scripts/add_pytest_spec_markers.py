#!/usr/bin/env python3
"""pytest.mark.spec マーカーを自動追加するスクリプト

B30品質作業指示書準拠: TDD実践のためのspecマーカー追加
"""

import re
from pathlib import Path


def add_spec_markers(file_path: Path) -> int:
    """テストファイルにpytest.mark.specマーカーを追加

    Args:
        file_path: テストファイルのパス

    Returns:
        追加したマーカーの数
    """
    content = file_path.read_text(encoding="utf-8")
    lines = content.split("\n")

    # pytest import 追加（未追加の場合）
    has_pytest_import = any("import pytest" in line for line in lines)

    modified_lines = []
    markers_added = 0
    in_class = False
    class_indent = 0

    for i, line in enumerate(lines):
        # クラス定義の検出
        if line.strip().startswith("class Test"):
            in_class = True
            class_indent = len(line) - len(line.lstrip())

        # クラス外の検出
        if in_class and line and not line[0].isspace():
            in_class = False

        # テスト関数の検出
        if re.match(r"^(\s*)def test_\w+\(", line):
            indent = len(line) - len(line.lstrip())
            test_name = re.search(r"test_(\w+)", line).group(1)

            # 前の行がデコレータでない場合のみ追加
            prev_line_idx = i - 1
            while prev_line_idx >= 0 and not lines[prev_line_idx].strip():
                prev_line_idx -= 1

            if prev_line_idx >= 0:
                prev_line = lines[prev_line_idx].strip()
                if not prev_line.startswith("@"):
                    # SPEC IDを生成（ファイル名とテスト名から）
                    module_name = file_path.stem.replace("test_", "")
                    spec_id = f"SPEC-{module_name.upper()}-{test_name.upper()[:20]}"

                    # マーカーを追加
                    modified_lines.append(f"{' ' * indent}@pytest.mark.spec('{spec_id}')")
                    markers_added += 1

        modified_lines.append(line)

    # pytest import を先頭に追加
    if not has_pytest_import and markers_added > 0:
        # 既存のimport文の後に追加
        import_added = False
        final_lines = []
        for line in modified_lines:
            final_lines.append(line)
            if (not import_added and line.startswith("import ")) or line.startswith("from "):
                if not any("import pytest" in l for l in final_lines):
                    final_lines.append("import pytest")
                    import_added = True
        modified_lines = final_lines

    if markers_added > 0:
        file_path.write_text("\n".join(modified_lines), encoding="utf-8")

    return markers_added


def main():
    """メイン処理"""
    test_dir = Path("/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド/tests")

    total_markers = 0
    modified_files = 0

    for test_file in test_dir.rglob("test_*.py"):
        markers = add_spec_markers(test_file)
        if markers > 0:
            total_markers += markers
            modified_files += 1
            print(f"✅ {test_file.relative_to(test_dir)}: {markers} マーカー追加")

    print("\n📊 結果:")
    print(f"  - 修正ファイル数: {modified_files}")
    print(f"  - 追加マーカー数: {total_markers}")


if __name__ == "__main__":
    main()
