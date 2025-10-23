#!/usr/bin/env python3
"""バックアップカオス状態緊急整理スクリプト

既存のカオス状態を段階的に安全に整理
実行前にdry-runモードで必ず計画確認を行う
"""

import argparse
import sys

from scripts.tools.backup_management_system import CleanupResult, MigrationResult, UnifiedBackupManager


class BackupChaosCleanup:
    """バックアップカオス整理専用クラス"""

    def __init__(self):
        self.manager = UnifiedBackupManager()
        self.project_root = self.manager.path_service.get_project_root()

    def analyze_chaos_state(self) -> dict:
        """現在のカオス状態詳細分析"""
        analysis = {
            "legacy_backups": [],
            "total_chaos_size": 0.0,
            "potential_duplicates": [],
            "urgent_cleanup": []
        }

        # レガシーバックアップフォルダ特定
        chaos_patterns = [
            "tests_backup_*",
            "specs_backup_*",
            "temp/ddd_fix_backups",
            "backup",
            "archive/backup_files",
            ".codemap_backups"
        ]

        for pattern in chaos_patterns:
            matches = list(self.project_root.glob(pattern))
            for path in matches:
                if path.exists():
                    size = self.manager._calculate_size(path)
                    analysis["legacy_backups"].append({
                        "path": str(path),
                        "size_mb": round(size, 2),
                        "pattern": pattern
                    })
                    analysis["total_chaos_size"] += size

        # 重複可能性分析
        analysis["potential_duplicates"] = self._analyze_duplicates()

        # 緊急クリーンアップ対象
        analysis["urgent_cleanup"] = self._identify_urgent_cleanup()

        analysis["total_chaos_size"] = round(analysis["total_chaos_size"], 2)

        return analysis

    def _analyze_duplicates(self) -> list[dict]:
        """重複の可能性分析"""
        duplicates = []

        # tests_backup フォルダ間の比較
        test_backups = list(self.project_root.glob("tests_backup_*"))
        if len(test_backups) > 1:
            duplicates.append({
                "type": "tests_backup重複",
                "paths": [str(p) for p in test_backups],
                "recommendation": "最新のもの以外は削除可能"
            })

        return duplicates

    def _identify_urgent_cleanup(self) -> list[dict]:
        """緊急クリーンアップ対象特定"""
        urgent = []

        # temp配下の大容量バックアップ
        temp_backups = self.project_root.glob("temp/*backup*")
        for temp_backup in temp_backups:
            if temp_backup.exists():
                size = self.manager._calculate_size(temp_backup)
                if size > 10:  # 10MB以上
                    urgent.append({
                        "path": str(temp_backup),
                        "reason": f"temp内大容量バックアップ ({size:.1f}MB)",
                        "action": "移行またはアーカイブ"
                    })

        return urgent

    def execute_safe_cleanup(self, dry_run: bool = True, interactive: bool = True) -> dict:
        """安全なクリーンアップ実行"""
        results = {
            "migration_result": None,
            "cleanup_result": None,
            "safety_checks": [],
            "warnings": []
        }

        print(f"\n{'=== DRY RUN MODE ===' if dry_run else '=== LIVE MODE ==='}")

        # 事前安全チェック
        safety_ok = self._perform_safety_checks()
        results["safety_checks"] = safety_ok

        if not all(safety_ok.values()):
            results["warnings"].append("安全チェック失敗: 実行を中止することを推奨")
            return results

        # インタラクティブ確認
        if interactive and not dry_run:
            if not self._interactive_confirmation():
                results["warnings"].append("ユーザーによる実行キャンセル")
                return results

        # レガシー移行
        print("\n--- レガシーバックアップ移行 ---")
        migration_result = self.manager.migrate_legacy_backups(dry_run=dry_run)
        results["migration_result"] = migration_result

        self._report_migration_result(migration_result, dry_run)

        # 古いバックアップクリーンアップ
        print("\n--- 古いバックアップクリーンアップ ---")
        cleanup_result = self.manager.cleanup_old_backups(dry_run=dry_run)
        results["cleanup_result"] = cleanup_result

        self._report_cleanup_result(cleanup_result, dry_run)

        return results

    def _perform_safety_checks(self) -> dict:
        """実行前安全チェック"""
        checks = {}

        # 1. プロジェクトルート確認
        checks["project_root_valid"] = self.project_root.exists() and self.project_root.is_dir()

        # 2. 重要ファイルの存在確認
        important_files = ["pyproject.toml", "CLAUDE.md"]
        checks["important_files_exist"] = all(
            (self.project_root / f).exists() for f in important_files
        )

        # 3. 書き込み権限確認
        try:
            test_file = self.project_root / ".backup_test"
            test_file.write_text("test")
            test_file.unlink()
            checks["write_permission"] = True
        except:
            checks["write_permission"] = False

        # 4. ディスク容量確認
        import shutil
        free_space_gb = shutil.disk_usage(self.project_root).free / (1024**3)
        checks["sufficient_disk_space"] = free_space_gb > 1  # 1GB以上の空き

        return checks

    def _interactive_confirmation(self) -> bool:
        """インタラクティブ実行確認"""
        print("\n" + "="*60)
        print("警告: 実際のファイル移動・削除を実行します")
        print("この操作は元に戻せません")
        print("="*60)

        response = input("\n続行しますか？ (yes/no): ").lower().strip()
        return response in ["yes", "y"]

    def _report_migration_result(self, result: MigrationResult, dry_run: bool):
        """移行結果レポート"""
        action = "移行予定" if dry_run else "移行完了"

        print(f"{action}項目: {len(result.migrated_backups)}件")
        if result.migrated_backups:
            for source, dest in result.migrated_backups:
                print(f"  {source} -> {dest}")

        if not dry_run and result.removed_legacy:
            print(f"削除完了: {len(result.removed_legacy)}件")
            print(f"解放容量: {result.total_freed_space:.2f}MB")

        if result.migration_errors:
            print(f"エラー: {len(result.migration_errors)}件")
            for error in result.migration_errors:
                print(f"  {error}")

    def _report_cleanup_result(self, result: CleanupResult, dry_run: bool):
        """クリーンアップ結果レポート"""
        action = "削除予定" if dry_run else "削除完了"

        print(f"{action}項目: {len(result.removed_backups)}件")
        if not dry_run and result.freed_space > 0:
            print(f"解放容量: {result.freed_space:.2f}MB")

        if result.errors:
            print(f"エラー: {len(result.errors)}件")
            for error in result.errors:
                print(f"  {error}")


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="バックアップカオス状態緊急整理スクリプト",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 現状分析のみ
  python cleanup_backup_chaos.py --analyze

  # 計画表示（安全・推奨）
  python cleanup_backup_chaos.py --dry-run

  # 実際に整理実行（要注意）
  python cleanup_backup_chaos.py --execute

  # 非対話的実行
  python cleanup_backup_chaos.py --execute --no-interactive
        """
    )

    parser.add_argument("--analyze", action="store_true",
                       help="現在のカオス状態分析のみ実行")
    parser.add_argument("--dry-run", action="store_true",
                       help="実行計画表示（実際のファイル操作なし）")
    parser.add_argument("--execute", action="store_true",
                       help="実際の整理を実行（要注意）")
    parser.add_argument("--no-interactive", action="store_true",
                       help="対話的確認をスキップ")

    args = parser.parse_args()

    # 引数チェック
    if not any([args.analyze, args.dry_run, args.execute]):
        args.dry_run = True  # デフォルトはdry-run

    cleanup = BackupChaosCleanup()

    try:
        if args.analyze:
            print("=== バックアップカオス状態分析 ===")
            analysis = cleanup.analyze_chaos_state()

            print(f"\nレガシーバックアップ: {len(analysis['legacy_backups'])}件")
            print(f"総カオスサイズ: {analysis['total_chaos_size']}MB")

            print("\n詳細:")
            for backup in analysis["legacy_backups"]:
                print(f"  {backup['path']}: {backup['size_mb']}MB ({backup['pattern']})")

            if analysis["potential_duplicates"]:
                print("\n重複可能性:")
                for dup in analysis["potential_duplicates"]:
                    print(f"  {dup['type']}: {dup['recommendation']}")

            if analysis["urgent_cleanup"]:
                print("\n緊急クリーンアップ対象:")
                for urgent in analysis["urgent_cleanup"]:
                    print(f"  {urgent['path']}: {urgent['reason']}")

        else:
            # クリーンアップ実行
            dry_run = not args.execute
            interactive = not args.no_interactive

            results = cleanup.execute_safe_cleanup(
                dry_run=dry_run,
                interactive=interactive
            )

            # 結果サマリー
            print(f"\n{'=== 実行完了 ===' if not dry_run else '=== 計画完了 ==='}")

            if results["warnings"]:
                print("\n警告:")
                for warning in results["warnings"]:
                    print(f"  {warning}")

            if not dry_run and results["migration_result"] and results["cleanup_result"]:
                total_freed = (
                    results["migration_result"].total_freed_space +
                    results["cleanup_result"].freed_space
                )
                print(f"\n総解放容量: {total_freed:.2f}MB")

    except KeyboardInterrupt:
        print("\n\n処理がユーザーによって中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nエラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
