#!/usr/bin/env python3
"""AST変換ツール動作検証テスト"""

def create_test_file():
    """テスト用ファイル作成"""
    test_content = '''#!/usr/bin/env python3
"""テスト用ファイル"""

def test_function():
    print("これはprint()のテストです")
    message = "Hello World"
    print(message)
    print(f"Format: {message}")

    # console_serviceのテスト
    console_service.print_("これはconsole_service.print_()のテストです")
    console_service.print_(f"Format: {message}")

if __name__ == "__main__":
    test_function()
'''

    with open("test_migration_sample.py", "w", encoding="utf-8") as f:
        f.write(test_content)

    print("✅ テスト用ファイル作成完了: test_migration_sample.py")


def test_ast_migration_tool():
    """AST変換ツールテスト"""
    print("\n=== Test 2: AST変換ツール動作テスト ===")

    # テストファイル作成
    create_test_file()

    # 変換前の内容確認
    print("\n📄 変換前の内容:")
    with open("test_migration_sample.py", "r", encoding="utf-8") as f:
        content = f.read()
        print(content)

    # AST変換ツール実行
    print("\n🔄 AST変換ツール実行中...")
    import subprocess
    result = subprocess.run([
        "python",
        "src/noveler/tools/console_migration_tool.py",
        "test_migration_sample.py"
    ], capture_output=True, text=True)

    print("STDOUT:", result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    # 変換後の内容確認
    print("\n📄 変換後の内容:")
    try:
        with open("test_migration_sample.py", "r", encoding="utf-8") as f:
            content = f.read()
            print(content)
        print("✅ AST変換成功")
    except FileNotFoundError:
        print("❌ 変換後ファイルが見つかりません")

    # バックアップファイル確認
    try:
        with open("test_migration_sample.py.backup", "r", encoding="utf-8") as f:
            print("✅ バックアップファイル作成確認")
    except FileNotFoundError:
        print("❌ バックアップファイルが見つかりません")


def cleanup():
    """テストファイル削除"""
    import os
    files_to_remove = [
        "test_migration_sample.py",
        "test_migration_sample.py.backup"
    ]

    for file in files_to_remove:
        try:
            os.remove(file)
            print(f"🗑️  削除: {file}")
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    test_ast_migration_tool()
    print("\n🧹 テストファイル削除中...")
    cleanup()
    print("🎯 AST変換ツールテスト完了!")
