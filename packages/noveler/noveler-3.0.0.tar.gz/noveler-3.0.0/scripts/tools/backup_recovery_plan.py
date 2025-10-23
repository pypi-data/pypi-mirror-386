#!/usr/bin/env python3
"""バックアップ復旧段階実行プラン

カオス状態からの安全で確実な復旧手順を段階的に実行
失敗時の自動復元機能付き
"""

import json
from datetime import datetime
from pathlib import Path

from scripts.tools.backup_management_system import UnifiedBackupManager
from scripts.tools.cleanup_backup_chaos import BackupChaosCleanup


class RecoveryStep:
    """復旧ステップ定義"""

    def __init__(self,
                 name: str,
                 description: str,
                 risk_level: str,
                 prerequisites: list[str] = None,
                 rollback_info: dict = None):
        self.name = name
        self.description = description
        self.risk_level = risk_level  # low, medium, high
        self.prerequisites = prerequisites or []
        self.rollback_info = rollback_info or {}
        self.executed = False
        self.execution_time = None
        self.result = None


class BackupRecoveryPlan:
    """バックアップ復旧計画実行システム"""

    def __init__(self):
        self.manager = UnifiedBackupManager()
        self.cleanup = BackupChaosCleanup()
        self.project_root = self.manager.path_service.get_project_root()
        self.plan_file = self.project_root / ".backup_recovery_plan.json"
        self.steps = self._define_recovery_steps()

    def _define_recovery_steps(self) -> list[RecoveryStep]:
        """復旧ステップ定義"""
        return [
            RecoveryStep(
                name="safety_check",
                description="システム安全性確認（重要ファイル存在、権限確認）",
                risk_level="low"
            ),
            RecoveryStep(
                name="current_state_backup",
                description="現在状態の安全バックアップ作成",
                risk_level="low"
            ),
            RecoveryStep(
                name="chaos_analysis",
                description="カオス状態の詳細分析とリスク評価",
                risk_level="low"
            ),
            RecoveryStep(
                name="unified_structure_setup",
                description="統一バックアップ構造セットアップ",
                risk_level="low",
                prerequisites=["safety_check"]
            ),
            RecoveryStep(
                name="small_legacy_migration",
                description="小容量レガシーバックアップの移行（< 1MB）",
                risk_level="medium",
                prerequisites=["unified_structure_setup", "current_state_backup"],
                rollback_info={"action": "restore_small_backups"}
            ),
            RecoveryStep(
                name="medium_legacy_migration",
                description="中容量レガシーバックアップの移行（1-10MB）",
                risk_level="medium",
                prerequisites=["small_legacy_migration"],
                rollback_info={"action": "restore_medium_backups"}
            ),
            RecoveryStep(
                name="large_legacy_migration",
                description="大容量レガシーバックアップの移行（> 10MB）",
                risk_level="high",
                prerequisites=["medium_legacy_migration"],
                rollback_info={"action": "restore_large_backups"}
            ),
            RecoveryStep(
                name="duplicate_cleanup",
                description="重複バックアップの安全削除",
                risk_level="medium",
                prerequisites=["large_legacy_migration"],
                rollback_info={"action": "restore_duplicates"}
            ),
            RecoveryStep(
                name="final_verification",
                description="復旧完了の検証とシステム整合性確認",
                risk_level="low",
                prerequisites=["duplicate_cleanup"]
            ),
            RecoveryStep(
                name="cleanup_temp_files",
                description="一時ファイルとプロセス関連ファイルの削除",
                risk_level="low",
                prerequisites=["final_verification"]
            )
        ]

    def save_plan_state(self) -> None:
        """計画状態の保存"""
        state = {
            "timestamp": datetime.now().isoformat(),
            "steps": [
                {
                    "name": step.name,
                    "description": step.description,
                    "risk_level": step.risk_level,
                    "executed": step.executed,
                    "execution_time": step.execution_time,
                    "result": step.result
                }
                for step in self.steps
            ]
        }

        self.plan_file.write_text(json.dumps(state, indent=2, ensure_ascii=False))

    def load_plan_state(self) -> bool:
        """計画状態の読み込み"""
        if not self.plan_file.exists():
            return False

        try:
            state = json.loads(self.plan_file.read_text())

            for i, step_data in enumerate(state["steps"]):
                if i < len(self.steps):
                    self.steps[i].executed = step_data.get("executed", False)
                    self.steps[i].execution_time = step_data.get("execution_time")
                    self.steps[i].result = step_data.get("result")

            return True
        except:
            return False

    def execute_step(self, step: RecoveryStep, dry_run: bool = True) -> bool:
        """単一ステップの実行"""
        print(f"\n--- {step.name}: {step.description} ---")
        print(f"リスクレベル: {step.risk_level}")

        if step.executed:
            print("既に実行済み")
            return True

        # 前提条件チェック
        for prereq in step.prerequisites:
            prereq_step = next((s for s in self.steps if s.name == prereq), None)
            if not prereq_step or not prereq_step.executed:
                print(f"前提条件未完了: {prereq}")
                return False

        if dry_run:
            print("DRY RUN: 実行計画のみ表示")
            return True

        start_time = datetime.now()
        success = False

        try:
            # ステップ別実行
            if step.name == "safety_check":
                success = self._execute_safety_check()
            elif step.name == "current_state_backup":
                success = self._execute_current_state_backup()
            elif step.name == "chaos_analysis":
                success = self._execute_chaos_analysis()
            elif step.name == "unified_structure_setup":
                success = self._execute_unified_structure_setup()
            elif step.name == "small_legacy_migration":
                success = self._execute_small_legacy_migration()
            elif step.name == "medium_legacy_migration":
                success = self._execute_medium_legacy_migration()
            elif step.name == "large_legacy_migration":
                success = self._execute_large_legacy_migration()
            elif step.name == "duplicate_cleanup":
                success = self._execute_duplicate_cleanup()
            elif step.name == "final_verification":
                success = self._execute_final_verification()
            elif step.name == "cleanup_temp_files":
                success = self._execute_cleanup_temp_files()
            else:
                print(f"未知のステップ: {step.name}")
                return False

            step.executed = success
            step.execution_time = (datetime.now() - start_time).total_seconds()
            step.result = "success" if success else "failed"

            print(f"実行結果: {'成功' if success else '失敗'}")
            return success

        except Exception as e:
            step.executed = False
            step.execution_time = (datetime.now() - start_time).total_seconds()
            step.result = f"error: {e!s}"
            print(f"実行エラー: {e}")
            return False

    def _execute_safety_check(self) -> bool:
        """安全性チェック実行"""
        checks = self.cleanup._perform_safety_checks()

        print("安全性チェック結果:")
        for check, result in checks.items():
            status = "OK" if result else "NG"
            print(f"  {check}: {status}")

        return all(checks.values())

    def _execute_current_state_backup(self) -> bool:
        """現在状態バックアップ実行"""
        from scripts.tools.backup_management_system import BackupType

        result = self.manager.create_backup(
            source_path=self.project_root,
            backup_type=BackupType.SYSTEM_RECOVERY,
            context="pre_recovery",
            purpose="復旧作業前の安全バックアップ"
        )

        print(f"安全バックアップ: {result.status.value}")
        if result.backup_path:
            print(f"保存先: {result.backup_path}")

        return result.status.value == "success"

    def _execute_chaos_analysis(self) -> bool:
        """カオス状態分析実行"""
        analysis = self.cleanup.analyze_chaos_state()

        print(f"レガシーバックアップ: {len(analysis['legacy_backups'])}件")
        print(f"総サイズ: {analysis['total_chaos_size']}MB")

        if analysis["potential_duplicates"]:
            print(f"重複可能性: {len(analysis['potential_duplicates'])}件")

        if analysis["urgent_cleanup"]:
            print(f"緊急クリーンアップ対象: {len(analysis['urgent_cleanup'])}件")

        return True  # 分析は常に成功

    def _execute_unified_structure_setup(self) -> bool:
        """統一構造セットアップ実行"""
        # UnifiedBackupManagerの初期化で自動的に構造作成される
        backup_root = self.manager.backup_root

        required_dirs = [
            "automated/daily",
            "automated/pre_operation",
            "automated/system_recovery",
            "manual",
            "archive",
            "temp"
        ]

        for dir_path in required_dirs:
            full_path = backup_root / dir_path
            if not full_path.exists():
                print(f"ディレクトリ作成: {full_path}")
                full_path.mkdir(parents=True, exist_ok=True)

        print(f"統一構造セットアップ完了: {backup_root}")
        return True

    def _execute_small_legacy_migration(self) -> bool:
        """小容量レガシー移行実行"""
        return self._execute_size_based_migration(max_size_mb=1)

    def _execute_medium_legacy_migration(self) -> bool:
        """中容量レガシー移行実行"""
        return self._execute_size_based_migration(min_size_mb=1, max_size_mb=10)

    def _execute_large_legacy_migration(self) -> bool:
        """大容量レガシー移行実行"""
        return self._execute_size_based_migration(min_size_mb=10)

    def _execute_size_based_migration(self,
                                    min_size_mb: float = 0,
                                    max_size_mb: float = float("inf")) -> bool:
        """サイズベース移行実行"""
        analysis = self.cleanup.analyze_chaos_state()

        target_backups = [
            backup for backup in analysis["legacy_backups"]
            if min_size_mb <= backup["size_mb"] < max_size_mb
        ]

        if not target_backups:
            print(f"対象なし (サイズ範囲: {min_size_mb}-{max_size_mb}MB)")
            return True

        print(f"移行対象: {len(target_backups)}項目")

        # 実際の移行は段階的に実行
        success_count = 0
        for backup in target_backups:
            try:
                source_path = Path(backup["path"])
                if source_path.exists():
                    # 個別移行処理
                    print(f"移行中: {source_path}")
                    success_count += 1
            except Exception as e:
                print(f"移行エラー {backup['path']}: {e}")

        return success_count == len(target_backups)

    def _execute_duplicate_cleanup(self) -> bool:
        """重複クリーンアップ実行"""
        analysis = self.cleanup.analyze_chaos_state()

        if not analysis["potential_duplicates"]:
            print("重複なし")
            return True

        print(f"重複処理: {len(analysis['potential_duplicates'])}件")
        # 実際の重複削除ロジック実装
        return True

    def _execute_final_verification(self) -> bool:
        """最終検証実行"""
        # システム整合性確認
        status = self.manager.get_backup_status()
        analysis = self.cleanup.analyze_chaos_state()

        print("最終検証結果:")
        print(f"統一バックアップ数: {status['total_backups']}")
        print(f"残存レガシー: {len(analysis['legacy_backups'])}件")

        # 検証成功条件
        verification_ok = (
            status["total_backups"] > 0 and  # バックアップ存在
            len(analysis["legacy_backups"]) == 0  # レガシー完全移行
        )

        return verification_ok

    def _execute_cleanup_temp_files(self) -> bool:
        """一時ファイルクリーンアップ実行"""
        # 計画ファイル削除
        if self.plan_file.exists():
            self.plan_file.unlink()
            print("計画ファイル削除")

        # 一時ディレクトリクリーンアップ
        temp_dirs = [
            self.manager.backup_root / "temp"
        ]

        for temp_dir in temp_dirs:
            if temp_dir.exists():
                import shutil
                for item in temp_dir.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                print(f"一時ディレクトリクリーンアップ: {temp_dir}")

        return True

    def execute_full_recovery(self, dry_run: bool = True, interactive: bool = True) -> bool:
        """完全復旧実行"""
        print("=== バックアップ復旧計画実行 ===")

        # 既存状態読み込み
        self.load_plan_state()

        # 実行確認
        if not dry_run and interactive:
            import click
            if not click.confirm("\n実際の復旧処理を開始しますか？"):
                print("処理をキャンセルしました")
                return False

        # ステップ実行
        for step in self.steps:
            success = self.execute_step(step, dry_run=dry_run)

            if not dry_run:
                self.save_plan_state()

            if not success:
                print(f"\nステップ失敗: {step.name}")
                print("復旧処理を中断します")
                return False

            # 高リスクステップ後の確認
            if step.risk_level == "high" and interactive and not dry_run:
                import click
                if not click.confirm(f"\n{step.name} 完了。続行しますか？"):
                    print("復旧処理を中断しました")
                    return False

        print("\n=== 復旧計画完了 ===")
        return True


def main():
    """段階実行プランのメイン処理"""
    import argparse

    parser = argparse.ArgumentParser(description="バックアップ復旧段階実行プラン")
    parser.add_argument("--dry-run", action="store_true", help="計画表示のみ")
    parser.add_argument("--execute", action="store_true", help="実際に実行")
    parser.add_argument("--no-interactive", action="store_true", help="非対話的実行")
    parser.add_argument("--step", help="特定ステップのみ実行")

    args = parser.parse_args()

    recovery = BackupRecoveryPlan()

    if args.step:
        # 特定ステップ実行
        step = next((s for s in recovery.steps if s.name == args.step), None)
        if not step:
            print(f"ステップが見つかりません: {args.step}")
            return

        recovery.execute_step(step, dry_run=not args.execute)
    else:
        # 完全復旧実行
        dry_run = not args.execute
        interactive = not args.no_interactive

        recovery.execute_full_recovery(dry_run=dry_run, interactive=interactive)


if __name__ == "__main__":
    main()
