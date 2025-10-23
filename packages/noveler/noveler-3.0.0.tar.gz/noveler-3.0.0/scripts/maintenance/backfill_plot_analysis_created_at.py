#!/usr/bin/env python3
"""プロット分析JSONファイルのcreated_atフィールドバックフィルスクリプト

既存の分析結果JSONファイルにcreated_atフィールドが存在しない場合、
analyzed_atの値で補完するバックフィルスクリプト。

Usage:
    python scripts/maintenance/backfill_plot_analysis_created_at.py [analysis_dir]
"""

import json
import sys
from pathlib import Path
from typing import Any

from noveler.presentation.shared.shared_utilities import get_common_path_service


def backfill_created_at(analysis_dir: Path, dry_run: bool = True) -> dict[str, int]:
    """既存の分析JSONファイルにcreated_atフィールドを追加

    Args:
        analysis_dir: 分析結果ディレクトリ
        dry_run: True の場合は変更を実際に適用せず、レポートのみ出力

    Returns:
        統計情報の辞書 (processed, updated, errors)
    """
    stats = {"processed": 0, "updated": 0, "errors": 0}

    if not analysis_dir.exists():
        print(f"分析ディレクトリが存在しません: {analysis_dir}")
        return stats

    print(f"分析ディレクトリをスキャン中: {analysis_dir}")
    if dry_run:
        print("*** DRY RUN モード - 実際の変更は行いません ***")

    for json_file in analysis_dir.glob("*.json"):
        stats["processed"] += 1

        try:
            # JSONファイルを読み込み
            with json_file.open("r", encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)

            # created_atが存在しない場合のみ処理
            if "created_at" not in data and "analyzed_at" in data:
                data["created_at"] = data["analyzed_at"]
                stats["updated"] += 1

                print(f"更新対象: {json_file.name} - created_at を {data['analyzed_at']} で補完")

                # dry_runでない場合のみ書き込み
                if not dry_run:
                    with json_file.open("w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    print(f"  → ファイルを更新しました")

            elif "created_at" in data:
                print(f"スキップ: {json_file.name} - created_at は既に存在")
            else:
                print(f"警告: {json_file.name} - analyzed_at フィールドが見つかりません")

        except Exception as e:
            stats["errors"] += 1
            print(f"エラー: {json_file.name} - {e}")

    return stats


def main() -> None:
    """メイン処理"""
    # 引数からディレクトリを取得、または標準パスを使用
    if len(sys.argv) > 1:
        analysis_dir = Path(sys.argv[1])
    else:
        # デフォルトは logs/ai_analysis
        path_service = get_common_path_service()
        try:
            project_root = path_service.get_project_root()
            analysis_dir = project_root / "logs" / "ai_analysis"
        except Exception:
            analysis_dir = Path("logs/ai_analysis")

    print("プロット分析JSONファイルのcreated_atバックフィルスクリプト")
    print("=" * 60)

    # DRY RUN実行
    print("\n1. DRY RUN実行:")
    dry_stats = backfill_created_at(analysis_dir, dry_run=True)

    print(f"\n処理結果 (DRY RUN):")
    print(f"  処理対象ファイル: {dry_stats['processed']}")
    print(f"  更新が必要: {dry_stats['updated']}")
    print(f"  エラー: {dry_stats['errors']}")

    if dry_stats["updated"] == 0:
        print("\n更新が必要なファイルはありません。")
        return

    # 実行確認
    print(f"\n{dry_stats['updated']} 個のファイルを更新します。")
    response = input("実行しますか? (y/N): ").strip().lower()

    if response != "y":
        print("キャンセルしました。")
        return

    # 実際の更新実行
    print("\n2. 実際の更新実行:")
    real_stats = backfill_created_at(analysis_dir, dry_run=False)

    print(f"\n最終結果:")
    print(f"  処理対象ファイル: {real_stats['processed']}")
    print(f"  実際に更新: {real_stats['updated']}")
    print(f"  エラー: {real_stats['errors']}")

    if real_stats["errors"] == 0:
        print("\nバックフィル処理が正常に完了しました。")
    else:
        print(f"\n警告: {real_stats['errors']} 個のファイルでエラーが発生しました。")


if __name__ == "__main__":
    main()
