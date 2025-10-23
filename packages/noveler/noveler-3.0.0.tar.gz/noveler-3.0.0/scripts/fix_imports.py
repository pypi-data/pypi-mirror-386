#!/usr/bin/env python3
"""scriptsインポートパス修正スクリプト

scripts.*からnoveler.*へのインポートパス修正を一括実行
DDDアーキテクチャ違反修正の一環
"""

import os
import re
from pathlib import Path


# 修正対象のインポートマッピング
IMPORT_MAPPINGS = {
    # Presentation層の共有ユーティリティ
    "from noveler.presentation.shared.shared_utilities": "from noveler.presentation.shared.shared_utilities",
    "from noveler.presentation.shared.shared_utilities": "from noveler.presentation.shared.shared_utilities",
    "from noveler.presentation.shared.shared_utilities": "from noveler.presentation.shared.shared_utilities",

    # Domain層
    "from noveler.domain": "from noveler.domain",
    "from noveler.domain": "from noveler.domain",

    # Application層
    "from noveler.application": "from noveler.application",

    # Infrastructure層
    "from noveler.infrastructure": "from noveler.infrastructure",

    # MCPサーバー関連
    "from src.mcp_servers": "from src.mcp_servers",

    # Tools
    "from scripts.tools": "from scripts.tools",  # 一部のツールはscriptsに残す
}

# 特殊ケースの修正パターン
SPECIAL_PATTERNS = [
    # get_console関数の修正
    (r"from scripts\.presentation\.cli\.shared_utilities\.console import get_console",
     "from noveler.presentation.shared.shared_utilities import get_console"),

    # console単体インポート
    (r"from scripts\.presentation\.cli\.shared_utilities import console",
     "from noveler.presentation.shared.shared_utilities import console"),

    # get_unified_logger
    (r"from scripts\.presentation\.cli\.shared_utilities import get_unified_logger",
     "from noveler.presentation.shared.shared_utilities import get_unified_logger"),
]


def fix_file_imports(file_path: Path) -> bool:
    """ファイルのインポートを修正

    Args:
        file_path: 修正対象ファイルパス

    Returns:
        bool: 修正が行われたかどうか
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # 特殊パターンから先に修正
        for pattern, replacement in SPECIAL_PATTERNS:
            content = re.sub(pattern, replacement, content)

        # 基本的なマッピング修正
        for old_import, new_import in IMPORT_MAPPINGS.items():
            content = content.replace(old_import, new_import)

        # 修正があった場合のみファイルを書き戻し
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"修正: {file_path}")
            return True

    except Exception as e:
        print(f"エラー {file_path}: {e}")
        return False

    return False


def main():
    """メイン実行関数"""
    root_dir = Path(".")

    # 修正対象ファイル検索（アーカイブとdistディレクトリは除外）
    exclude_dirs = {"archive", "backups", "dist", ".git", "__pycache__", ".pytest_cache"}

    python_files = []
    for root, dirs, files in os.walk(root_dir):
        # 除外ディレクトリをスキップ
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)

    print(f"修正対象ファイル数: {len(python_files)}")

    fixed_count = 0
    for file_path in python_files:
        if fix_file_imports(file_path):
            fixed_count += 1

    print(f"修正完了: {fixed_count}ファイル")


if __name__ == "__main__":
    main()
