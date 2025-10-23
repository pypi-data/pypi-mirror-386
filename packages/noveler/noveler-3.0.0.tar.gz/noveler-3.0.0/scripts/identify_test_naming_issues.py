#!/usr/bin/env python3
"""
テストファイル命名規則の問題を特定し、修正候補を提示
"""

import re
from pathlib import Path


def identify_naming_issues():
    """テスト命名の問題パターンを特定"""
    test_root = Path("tests/unit")

    issues = {
        "wrong_prefix": [],      # test_で始まらない
        "underscored_names": [], # アンダースコアが多すぎる
        "inconsistent_casing": [], # 大文字小文字の問題
        "redundant_names": []    # 冗長な命名
    }

    for py_file in test_root.rglob("*.py"):
        if py_file.name in ["__init__.py", "conftest.py"]:
            continue
        if py_file.suffix in [".skip", ".disabled"]:
            continue
        if py_file.name.endswith(".skip.py") or py_file.name.endswith(".disabled.py"):
            continue

        test_name = py_file.stem
        relative_path = str(py_file.relative_to(test_root))

        # test_で始まらないテストファイル
        if not test_name.startswith("test_"):
            issues["wrong_prefix"].append((relative_path, f"Should start with 'test_': {test_name}"))

        # 過度なアンダースコアの使用
        underscore_count = test_name.count("_")
        if underscore_count > 6:  # 基準値として6個を設定
            issues["underscored_names"].append((relative_path, f"Too many underscores ({underscore_count}): {test_name}"))

        # 冗長な命名パターン
        redundant_patterns = [
            r"test_test_",          # test_test_*
            r"_test_test",          # *_test_test
            r"_service_service",    # *_service_service
            r"_use_case_use_case",  # *_use_case_use_case
        ]

        for pattern in redundant_patterns:
            if re.search(pattern, test_name):
                issues["redundant_names"].append((relative_path, f"Redundant pattern '{pattern}': {test_name}"))

    return issues

def find_likely_source_matches():
    """孤立テストファイルに対応する可能性のあるソースファイルを探す"""
    from difflib import get_close_matches

    # ソースファイル名を収集
    src_root = Path("src/noveler")
    source_names = set()
    for py_file in src_root.rglob("*.py"):
        if py_file.name != "__init__.py":
            source_names.add(py_file.stem)

    # 孤立テストファイルを収集
    test_root = Path("tests/unit")
    orphaned_tests = []

    for py_file in test_root.rglob("*.py"):
        if py_file.name in ["__init__.py", "conftest.py"]:
            continue
        if py_file.suffix in [".skip", ".disabled"]:
            continue
        if py_file.name.endswith(".skip.py") or py_file.name.endswith(".disabled.py"):
            continue

        test_name = py_file.stem
        if test_name.startswith("test_"):
            target_name = test_name[5:]
        else:
            target_name = test_name

        if target_name not in source_names:
            # 類似の名前を探す
            close_matches = get_close_matches(target_name, source_names, n=3, cutoff=0.6)
            orphaned_tests.append((py_file.relative_to(test_root), target_name, close_matches))

    return orphaned_tests

def main():
    print("🔍 テストファイル命名規則問題の特定")
    print("=" * 60)

    # 1. 命名規則の問題を特定
    issues = identify_naming_issues()

    for issue_type, issue_list in issues.items():
        if issue_list:
            print(f"\n🚨 {issue_type.upper()} ({len(issue_list)}件):")
            for path, description in issue_list[:10]:  # 最初の10件のみ表示
                print(f"  {path}: {description}")
            if len(issue_list) > 10:
                print(f"  ... 他{len(issue_list) - 10}件")

    # 2. 孤立テストの類似マッチング
    print("\n🔗 孤立テストファイルの類似ソース候補:")
    orphaned_tests = find_likely_source_matches()

    for test_path, target_name, matches in orphaned_tests[:15]:  # 最初の15件のみ表示
        if matches:
            print(f"  {test_path} (looking for: {target_name})")
            for match in matches:
                print(f"    → 類似候補: {match}")
        else:
            print(f"  {test_path} (looking for: {target_name}) - 候補なし")

    if len(orphaned_tests) > 15:
        print(f"  ... 他{len(orphaned_tests) - 15}件の孤立テスト")

if __name__ == "__main__":
    main()
