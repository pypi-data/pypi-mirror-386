#!/usr/bin/env python3
"""ファイルエンコーディングチェックとBOM付きUTF-8への変換

全Pythonファイルを走査し、UTF-8-BOM以外のファイルを検出・変換する。
"""

import sys
from pathlib import Path
from typing import List, Tuple


def check_encoding(file_path: Path) -> str:
    """ファイルのエンコーディングを検出"""
    try:
        with open(file_path, 'rb') as f:
            raw = f.read(4)
            if raw.startswith(b'\xef\xbb\xbf'):
                return 'UTF-8-BOM'
            elif raw.startswith(b'\xff\xfe') or raw.startswith(b'\xfe\xff'):
                return 'UTF-16'
            else:
                # UTF-8として読めるか確認
                with open(file_path, 'r', encoding='utf-8') as tf:
                    tf.read()
                return 'UTF-8'
    except Exception:
        return 'UNKNOWN'


def convert_to_utf8_bom(file_path: Path, dry_run: bool = True) -> bool:
    """ファイルをUTF-8-BOMに変換"""
    try:
        # 現在の内容を読み込み
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if not dry_run:
            # BOM付きUTF-8で書き込み
            with open(file_path, 'w', encoding='utf-8-sig') as f:
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

    # エンコーディング別に分類
    encodings: dict[str, List[Path]] = {}
    for file_path in all_files:
        enc = check_encoding(file_path)
        if enc not in encodings:
            encodings[enc] = []
        encodings[enc].append(file_path)

    # 統計表示
    print("=" * 60)
    print("エンコーディング統計:")
    print("=" * 60)
    for enc in sorted(encodings.keys()):
        files = encodings[enc]
        print(f"{enc}: {len(files)}ファイル")
    print()

    # UTF-8-BOM以外のファイルを変換
    to_convert = []
    for enc in ['UTF-8', 'UTF-16', 'UNKNOWN']:
        if enc in encodings:
            to_convert.extend(encodings[enc])

    if not to_convert:
        print("[OK] すべてのファイルがUTF-8-BOMです")
        return

    print(f"変換対象: {len(to_convert)}ファイル")
    print()

    if dry_run:
        print("[WARNING] DRY RUNモード（実際には変換しません）")
        print()
        print("変換対象ファイル:")
        for file_path in sorted(to_convert)[:20]:
            enc = check_encoding(file_path)
            print(f"  [{enc}] {file_path}")
        if len(to_convert) > 20:
            print(f"  ... 他{len(to_convert) - 20}ファイル")
        print()
        print("実際に変換するには: python scripts/check_and_fix_encoding.py --fix")
    else:
        print("変換を実行します...")
        success_count = 0
        for file_path in to_convert:
            if convert_to_utf8_bom(file_path, dry_run=False):
                success_count += 1
                print(f"[OK] {file_path}")

        print()
        print(f"変換完了: {success_count}/{len(to_convert)}ファイル")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='ファイルエンコーディングチェック・変換')
    parser.add_argument('--fix', action='store_true', help='実際に変換を実行')
    args = parser.parse_args()

    main(dry_run=not args.fix)
