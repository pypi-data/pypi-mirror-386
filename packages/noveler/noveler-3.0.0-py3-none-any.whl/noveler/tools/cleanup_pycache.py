"""Tools.cleanup_pycache
Where: Utility script cleaning up __pycache__ directories.
What: Removes Python bytecode caches from the project tree.
Why: Keeps working directories clean and avoids stale caches.
"""

import os
import shutil
import sys
from pathlib import Path

from noveler.presentation.shared.shared_utilities import console

"__pycache__フォルダ一括削除スクリプト\n\n統合キャッシュ管理システムの一環として、\nscriptsフォルダ内の__pycache__フォルダを全て削除し、\ntemp/cache/pythonフォルダに統一する。\n"


def cleanup_pycache_directories() -> dict[str, any]:
    """__pycache__フォルダを一括削除"""
    guide_root = Path(__file__).parent.parent.parent
    scripts_dir = guide_root / "scripts"
    stats = {"deleted_dirs": [], "failed_dirs": [], "total_size_freed": 0, "success": True}
    console.print("🧹 __pycache__フォルダ一括削除開始...")
    pycache_dirs = list(scripts_dir.rglob("__pycache__"))
    if not pycache_dirs:
        console.print("✅ 削除対象の__pycache__フォルダは見つかりませんでした")
        return stats
    console.print(f"📂 削除対象: {len(pycache_dirs)}個のフォルダ")
    for pycache_dir in pycache_dirs:
        try:
            size = sum(f.stat().st_size for f in pycache_dir.rglob("*") if f.is_file())
            stats["total_size_freed"] += size
            shutil.rmtree(pycache_dir)
            stats["deleted_dirs"].append(str(pycache_dir))
            console.print(f"  ✅ 削除: {pycache_dir.relative_to(guide_root)}")
        except Exception as e:
            stats["failed_dirs"].append({"path": str(pycache_dir), "error": str(e)})
            stats["success"] = False
            console.print(f"  ❌ 失敗: {pycache_dir.relative_to(guide_root)} - {e}")
    return stats


def setup_cache_environment() -> bool:
    """キャッシュ環境を設定"""
    guide_root = Path(__file__).parent.parent.parent
    cache_dir = guide_root / "temp" / "cache" / "python"
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        console.print(f"📁 キャッシュディレクトリ準備完了: {cache_dir}")

        os.environ["PYTHONPYCACHEPREFIX"] = str(cache_dir)
        console.print(f"🔧 PYTHONPYCACHEPREFIX設定: {cache_dir}")
        return True
    except Exception as e:
        console.print(f"❌ キャッシュ環境設定失敗: {e}")
        return False


def verify_cleanup() -> bool:
    """クリーンアップの検証"""
    guide_root = Path(__file__).parent.parent.parent
    scripts_dir = guide_root / "scripts"
    remaining = list(scripts_dir.rglob("__pycache__"))
    if remaining:
        console.print(f"⚠️  残存する__pycache__フォルダ: {len(remaining)}個")
        for folder in remaining:
            console.print(f"   - {folder.relative_to(guide_root)}")
        return False
    console.print("✅ 全ての__pycache__フォルダが削除されました")
    return True


def show_summary(stats: dict) -> None:
    """削除結果のサマリーを表示"""
    console.print("\n" + "=" * 60)
    console.print("📊 __pycache__クリーンアップ結果")
    console.print("=" * 60)
    console.print(f"削除成功: {len(stats['deleted_dirs'])}個")
    console.print(f"削除失敗: {len(stats['failed_dirs'])}個")
    console.print(f"解放容量: {stats['total_size_freed'] / 1024:.1f} KB")
    if stats["failed_dirs"]:
        console.print("\n❌ 削除に失敗したフォルダ:")
        for failed in stats["failed_dirs"]:
            console.print(f"  - {failed['path']}: {failed['error']}")
    console.print(f"\n総合結果: {('✅ 成功' if stats['success'] else '⚠️ 部分的成功')}")


def main():
    """メイン処理"""
    console.print("🎯 統合キャッシュ管理システム - __pycache__クリーンアップ")
    console.print("=" * 60)
    try:
        stats = cleanup_pycache_directories()
        setup_success = setup_cache_environment()
        verify_success = verify_cleanup()
        show_summary(stats)
        overall_success = stats["success"] and setup_success and verify_success
        if overall_success:
            console.print("\n🎉 __pycache__問題の解決が完了しました!")
            console.print("💡 今後のPythonキャッシュは temp/cache/python に統一されます")
        else:
            console.print("\n⚠️ 一部の処理に問題がありました。手動確認が必要です。")
        return 0 if overall_success else 1
    except Exception as e:
        console.print(f"\n❌ 予期しないエラーが発生しました: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
