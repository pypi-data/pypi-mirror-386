#!/usr/bin/env python3
"""デバッグ用MCPモックテスト"""

def mock_check_file_changes(file_paths: list) -> dict:
    """check_file_changesのモック"""
    results = {}
    changed_count = 0

    for file_path in file_paths:
        # "changed"という文字列を含むファイルを変更ありとして扱う
        changed = "changed" in file_path.lower()
        print(f"Debug: {file_path} -> changed={changed}")
        if changed:
            changed_count += 1

        results[file_path] = {
            "changed": changed,
            "previous_hash": "abc123...",
            "current_hash": "def456..." if changed else "abc123...",
            "error": None
        }

    summary = {
        "total": len(file_paths),
        "changed": changed_count,
        "errors": 0
    }
    print(f"Debug: Summary = {summary}")

    return {
        "results": results,
        "summary": summary
    }

# テスト実行
test_files = ["unchanged_file.txt", "changed_file.txt"]
result = mock_check_file_changes(test_files)
print(f"Result: {result}")
print(f"Changed count: {result['summary']['changed']}")
