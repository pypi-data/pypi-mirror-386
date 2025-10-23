#!/usr/bin/env python3
"""BOM付きUTF-8からBOMを除去してUTF-8に戻す

Pythonの標準はBOMなしUTF-8のため、誤ってBOMを追加してしまった場合に元に戻す。
"""

import sys
from pathlib import Path
from typing import List


def has_bom(file_path: Path) -> bool:
    """ファイルがBOMを持つか確認"""
    try:
        with open(file_path, 'rb') as f:
            return f.read(3) == b'\xef\xbb\xbf'
    except Exception:
        return False


def remove_bom(file_path: Path, dry_run: bool = True) -> bool:
    """ファイルからBOMを除去"""
    try:
        # BOM付きUTF-8として読み込み（BOMは自動的にスキップされる）
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()

        if not dry_run:
            # BOMなしUTF-8で書き込み
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        return True
    except Exception as e:
        print(f"エラー: {file_path}: {e}", file=sys.stderr)
        return False


def main(dry_run: bool = True) -> None:
    """メイン処理"""
    # 対象ディレクトリ
    target_dirs = [Path('src'), Path('tests'), Path('scripts')]

    all_files: List[Path] = []
    for target_dir in target_dirs:
        if target_dir.exists():
            all_files.extend(target_dir.rglob('*.py'))

    # BOM付きファイルを検出
    bom_files = [f for f in all_files if has_bom(f)]

    print("=" * 60)
    print(f"BOM付きファイル: {len(bom_files)}ファイル")
    print("=" * 60)

    if not bom_files:
        print("[OK] BOM付きファイルはありません")
        return

    if dry_run:
        print("[WARNING] DRY RUNモード（実際には変換しません）")
        print()
        print("BOM除去対象:")
        for file_path in sorted(bom_files)[:20]:
            print(f"  {file_path}")
        if len(bom_files) > 20:
            print(f"  ... 他{len(bom_files) - 20}ファイル")
        print()
        print("実際にBOMを除去するには: python scripts/remove_bom.py --fix")
    else:
        print("BOM除去を実行します...")
        success_count = 0
        for file_path in bom_files:
            if remove_bom(file_path, dry_run=False):
                success_count += 1
                if success_count % 100 == 0:
                    print(f"[進行中] {success_count}/{len(bom_files)}ファイル処理完了")

        print()
        print(f"BOM除去完了: {success_count}/{len(bom_files)}ファイル")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='BOM除去')
    parser.add_argument('--fix', action='store_true', help='実際にBOMを除去')
    args = parser.parse_args()

    main(dry_run=not args.fix)
