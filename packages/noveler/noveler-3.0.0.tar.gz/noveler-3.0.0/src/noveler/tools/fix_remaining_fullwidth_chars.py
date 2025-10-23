#!/usr/bin/env python3
"""
残存全角文字修正スクリプト

Phase 3: その他の全角文字を半角文字に一括置換
RUF001-003エラーの完全修正ツール
"""
from pathlib import Path

def fix_remaining_fullwidth_chars(file_path: Path) -> tuple[bool, int]:
    """
    ファイル内の残存全角文字を半角文字に修正

    Args:
        file_path: 修正対象ファイルパス

    Returns:
        Tuple[bool, int]: (修正実行の有無, 修正箇所数)
    """
    try:
        content = file_path.read_text(encoding="utf-8")

        original_content = content

        # 全角文字の置換マッピング
        replacements = {
            "！": "!",
            "？": "?",
            "，": ",",
            "．": ".",
            "；": ";",
            "＝": "=",
            "＋": "+",
            "－": "-",
            "＊": "*",
            "／": "/",
            "｜": "|",
            "＆": "&",
            "％": "%",
            "＃": "#",
            "＠": "@",
            "＄": "$",
            "｀": "`",
            "～": "~",
            "＾": "^",
            "［": "[",
            "］": "]",
            "｛": "{",
            "｝": "}",
            "＜": "<",
            "＞": ">",
            "　": " ",
        }

        total_fixes = 0

        # 各置換を実行
        for fullwidth, halfwidth in replacements.items():
            count = content.count(fullwidth)
            if count > 0:
                content = content.replace(fullwidth, halfwidth)
                total_fixes += count

        if content != original_content:
            # バッチ書き込みを使用
            file_path.write_text(content, encoding="utf-8")

            return True, total_fixes

        return False, 0

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False, 0

def scan_and_fix_directory(directory: Path) -> dict[str, int]:
    """
    ディレクトリ内のPythonファイルを再帰的にスキャンして修正

    Args:
        directory: スキャン対象ディレクトリ

    Returns:
        typing.Dict[str, int]: 修正結果の統計
    """
    stats = {
        "files_processed": 0,
        "files_modified": 0,
        "total_fixes": 0
    }

    python_files = list(directory.rglob("*.py"))

    for file_path in python_files:
        stats["files_processed"] += 1

        modified, fix_count = fix_remaining_fullwidth_chars(file_path)

        if modified:
            stats["files_modified"] += 1
            stats["total_fixes"] += fix_count
            print(f"✅ 修正完了: {file_path.relative_to(directory)} ({fix_count}箇所)")

    return stats

def main():
    """メイン実行関数"""
    scripts_dir = Path(__file__).parent.parent

    print("🔧 Phase 3: 残存全角文字修正開始")
    print(f"📁 対象ディレクトリ: {scripts_dir}")
    print("-" * 50)

    stats = scan_and_fix_directory(scripts_dir)

    print("-" * 50)
    print("📊 修正結果サマリー:")
    print(f"  処理ファイル数: {stats['files_processed']}")
    print(f"  修正ファイル数: {stats['files_modified']}")
    print(f"  総修正箇所数: {stats['total_fixes']}")

    if stats["files_modified"] > 0:
        print("\n✅ Phase 3 完了: 残存全角文字修正成功")
    else:
        print("\nℹ️  修正対象の全角文字が見つかりませんでした")

if __name__ == "__main__":
    main()
