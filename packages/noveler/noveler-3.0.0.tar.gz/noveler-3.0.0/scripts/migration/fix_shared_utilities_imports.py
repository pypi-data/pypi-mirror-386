#!/usr/bin/env python3
"""Typer CLI削除後のshared_utilitiesインポート修正スクリプト

noveler.presentation.shared.shared_utilities → noveler.presentation.shared.shared_utilities
への一括変更を実行します。
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path: Path) -> tuple[bool, str]:
    """ファイル内のインポート文を修正"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # パターンマッチングと置換
        patterns = [
            (
                r'from noveler\.presentation\.cli\.shared_utilities import',
                'from noveler.presentation.shared.shared_utilities import'
            ),
            (
                r'import noveler\.presentation\.cli\.shared_utilities',
                'import noveler.presentation.shared.shared_utilities'
            ),
            (
                r'noveler\.presentation\.cli\.shared_utilities',
                'noveler.presentation.shared.shared_utilities'
            ),
        ]

        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, "Updated"
        else:
            return False, "No changes"

    except Exception as e:
        return False, f"Error: {e}"

def main():
    """メイン実行関数"""
    project_root = Path(__file__).parent.parent.parent

    # 対象ディレクトリ
    target_dirs = [
        project_root / "src",
        project_root / "tests",
        project_root / "scripts",
    ]

    updated_files = []
    error_files = []

    for target_dir in target_dirs:
        if not target_dir.exists():
            continue

        for file_path in target_dir.rglob("*.py"):
            # アーカイブ、バックアップ、キャッシュディレクトリをスキップ
            if any(part in str(file_path) for part in ['archive', 'backup', '__pycache__', '.git', 'cache']):
                continue

            success, message = fix_imports_in_file(file_path)

            if success:
                updated_files.append((file_path, message))
                print(f"✅ Updated: {file_path}")
            elif "Error" in message:
                error_files.append((file_path, message))
                print(f"❌ Error: {file_path} - {message}")

    print(f"\n📊 Summary:")
    print(f"   Updated files: {len(updated_files)}")
    print(f"   Error files: {len(error_files)}")

    if error_files:
        print(f"\n❌ Errors occurred in {len(error_files)} files:")
        for file_path, error in error_files[:10]:  # 最初の10個のエラーのみ表示
            print(f"   {file_path}: {error}")

if __name__ == "__main__":
    main()
