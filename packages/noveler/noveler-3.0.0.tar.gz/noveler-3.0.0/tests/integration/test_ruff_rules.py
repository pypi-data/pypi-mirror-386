#!/usr/bin/env python3
"""Ruffルール検証テスト"""

def create_print_test_file():
    """print()を含むテストファイル作成"""
    test_content = '''#!/usr/bin/env python3
"""print()テスト用ファイル"""

def bad_function():
    print("これはRuffで警告されるべきprint()です")
    message = "Bad practice"
    print(message)
    print(f"Format: {message}")

def good_function():
    from noveler.presentation.cli.shared_utilities import console
    console.print("これは適切なconsole.print()です")

if __name__ == "__main__":
    bad_function()
    good_function()
'''

    with open("test_ruff_print.py", "w", encoding="utf-8") as f:
        f.write(test_content)

    print("✅ print()テスト用ファイル作成: test_ruff_print.py")


def test_ruff_print_detection():
    """Ruffによるprint()検出テスト"""
    print("\n=== Test 3: Ruffルール検証テスト ===")

    create_print_test_file()

    print("\n🔍 Ruffでprint()検出テスト実行中...")
    import subprocess

    # T201（print found）ルールでチェック
    result = subprocess.run([
        "ruff", "check", "test_ruff_print.py", "--select", "T201"
    ], capture_output=True, text=True)

    print("Ruff検出結果:")
    print(result.stdout)

    if result.stderr:
        print("STDERR:", result.stderr)

    # print()が検出されたかチェック
    if "T201" in result.stdout and "print" in result.stdout:
        print("✅ Ruffがprint()を正しく検出しました")

        # 検出された行数をカウント
        lines = result.stdout.strip().split('\n')
        error_lines = [line for line in lines if 'T201' in line]
        print(f"📊 検出されたprint()の数: {len(error_lines)}")

        for line in error_lines:
            if line.strip():
                print(f"   🚨 {line}")
    else:
        print("❌ Ruffがprint()を検出できませんでした")
        print(f"Return code: {result.returncode}")


def test_ruff_exceptions():
    """Ruff例外設定テスト"""
    print("\n🔍 Ruff例外設定テスト...")

    import subprocess

    # MCPサーバーファイルでのprint()使用テスト（例外設定されているはず）
    exception_content = '''#!/usr/bin/env python3
"""MCP サーバー用ファイル（print()使用許可）"""

def mcp_function():
    print("MCPサーバーではprint()使用が許可されています")

if __name__ == "__main__":
    mcp_function()
'''

    # MCPサーバーディレクトリに配置
    import os
    os.makedirs("src/mcp_servers/test", exist_ok=True)

    with open("src/mcp_servers/test/test_exception.py", "w", encoding="utf-8") as f:
        f.write(exception_content)

    print("✅ 例外テスト用ファイル作成: src/mcp_servers/test/test_exception.py")

    # Ruffチェック実行
    result = subprocess.run([
        "ruff", "check", "src/mcp_servers/test/test_exception.py", "--select", "T201"
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ MCPサーバーファイルでprint()例外設定が正常動作")
    else:
        print("❌ MCPサーバーファイルでprint()が警告されました（例外設定に問題あり）")
        print(result.stdout)


def cleanup_ruff_test():
    """Ruffテストファイル削除"""
    import os
    import shutil

    files_to_remove = [
        "test_ruff_print.py"
    ]

    dirs_to_remove = [
        "src/mcp_servers/test"
    ]

    for file in files_to_remove:
        try:
            os.remove(file)
            print(f"🗑️  削除: {file}")
        except FileNotFoundError:
            pass

    for dir_path in dirs_to_remove:
        try:
            shutil.rmtree(dir_path)
            print(f"🗑️  削除: {dir_path}")
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    test_ruff_print_detection()
    test_ruff_exceptions()
    print("\n🧹 Ruffテストファイル削除中...")
    cleanup_ruff_test()
    print("🎯 Ruffルール検証テスト完了!")
