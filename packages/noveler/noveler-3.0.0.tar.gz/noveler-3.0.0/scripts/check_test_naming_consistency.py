#!/usr/bin/env python3
"""
テストファイル名とソースファイル名の一致性チェックスクリプト
"""

from pathlib import Path


def extract_source_files() -> dict[str, list[Path]]:
    """src/noveler配下のPythonファイルを収集"""
    src_root = Path("src/noveler")
    source_files = {}

    for py_file in src_root.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue

        # 相対パス（src/noveler/以降）を取得
        relative_path = py_file.relative_to(src_root)
        module_path = str(relative_path.with_suffix(""))

        # モジュール名をキーとして保存
        module_name = py_file.stem
        if module_name not in source_files:
            source_files[module_name] = []
        source_files[module_name].append(py_file)

    return source_files

def extract_test_files() -> dict[str, list[Path]]:
    """tests/unit配下のテストファイルを収集"""
    test_root = Path("tests/unit")
    test_files = {}

    for py_file in test_root.rglob("*.py"):
        if py_file.name in ["__init__.py", "conftest.py"]:
            continue
        if py_file.suffix in [".skip", ".disabled"]:
            continue
        if py_file.name.endswith(".skip.py") or py_file.name.endswith(".disabled.py"):
            continue

        # テストファイル名の解析
        test_name = py_file.stem
        if test_name.startswith("test_"):
            target_name = test_name[5:]  # "test_"を除去
        else:
            target_name = test_name

        if target_name not in test_files:
            test_files[target_name] = []
        test_files[target_name].append(py_file)

    return test_files

def check_naming_consistency() -> dict[str, list[str]]:
    """命名一致性をチェック"""
    source_files = extract_source_files()
    test_files = extract_test_files()

    results = {
        "missing_tests": [],      # ソースファイルはあるがテストファイルがない
        "orphaned_tests": [],     # テストファイルはあるがソースファイルがない
        "multiple_sources": [],   # 同名の複数ソースファイル
        "multiple_tests": [],     # 同名の複数テストファイル
        "consistent": []          # 一致している組み合わせ
    }

    # ソースファイル基準でチェック
    for source_name, source_paths in source_files.items():
        if len(source_paths) > 1:
            results["multiple_sources"].append(f"{source_name}: {[str(p) for p in source_paths]}")

        if source_name in test_files:
            results["consistent"].append(f"{source_name} ✅")
        else:
            results["missing_tests"].append(f"{source_name} (source: {source_paths[0]})")

    # テストファイル基準でチェック
    for test_name, test_paths in test_files.items():
        if len(test_paths) > 1:
            results["multiple_tests"].append(f"{test_name}: {[str(p) for p in test_paths]}")

        if test_name not in source_files:
            results["orphaned_tests"].append(f"{test_name} (test: {test_paths[0]})")

    return results

def main():
    """メイン実行関数"""
    print("🔍 テストファイル名とソースファイル名の一致性チェック")
    print("=" * 60)

    results = check_naming_consistency()

    # 結果表示
    if results["consistent"]:
        print(f"✅ 一致する組み合わせ ({len(results['consistent'])}件):")
        for item in results["consistent"][:10]:  # 最初の10件のみ表示
            print(f"  {item}")
        if len(results["consistent"]) > 10:
            print(f"  ... 他{len(results['consistent']) - 10}件")
        print()

    if results["missing_tests"]:
        print(f"❌ ソースファイルはあるがテストファイルがない ({len(results['missing_tests'])}件):")
        for item in results["missing_tests"]:
            print(f"  {item}")
        print()

    if results["orphaned_tests"]:
        print(f"⚠️ テストファイルはあるがソースファイルがない ({len(results['orphaned_tests'])}件):")
        for item in results["orphaned_tests"]:
            print(f"  {item}")
        print()

    if results["multiple_sources"]:
        print(f"🔄 同名の複数ソースファイル ({len(results['multiple_sources'])}件):")
        for item in results["multiple_sources"]:
            print(f"  {item}")
        print()

    if results["multiple_tests"]:
        print(f"🔄 同名の複数テストファイル ({len(results['multiple_tests'])}件):")
        for item in results["multiple_tests"]:
            print(f"  {item}")
        print()

    # サマリー
    total_sources = sum(len(paths) for paths in extract_source_files().values())
    total_tests = sum(len(paths) for paths in extract_test_files().values())

    print("📊 サマリー:")
    print(f"  ソースファイル数: {total_sources}")
    print(f"  テストファイル数: {total_tests}")
    print(f"  一致する組み合わせ: {len(results['consistent'])}")
    print(f"  テストが不足: {len(results['missing_tests'])}")
    print(f"  孤立したテスト: {len(results['orphaned_tests'])}")

if __name__ == "__main__":
    main()
