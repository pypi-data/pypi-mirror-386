"""Domain.services.auto_repair_engine
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""
SPEC-WORKFLOW-001: 自動修復エンジン

プロジェクト構造の自動修復処理を実行するドメインサービス。
DDD設計に基づく修復ビジネスロジックの実装。
"""


import os
import shutil
from dataclasses import dataclass
from pathlib import Path

# Phase 6修正: Service → Repository循環依存解消
from typing import TYPE_CHECKING, Protocol

from noveler.domain.interfaces.path_service import IPathService

if TYPE_CHECKING:
    from datetime import datetime

    from noveler.domain.interfaces.i_path_service import IPathService


# B20準拠修正: Infrastructure依存をInterface経由に変更
# from noveler.infrastructure.adapters.path_service_adapter import create_path_service


@dataclass
class BackupInfo:
    """バックアップ情報（循環依存解消のため移動）"""

    backup_path: Path
    original_path: Path
    created_at: datetime


class IProjectStructureRepository(Protocol):
    """プロジェクト構造リポジトリインターフェース（循環依存解消）"""

    def create_backup(self, path: Path) -> BackupInfo: ...
    def restore_backup(self, backup_info: BackupInfo) -> bool: ...
    def validate_structure(self, project_path: Path) -> bool: ...


from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

if TYPE_CHECKING:
    from noveler.domain.interfaces.i_path_service import IPathService
    from noveler.domain.services.project_structure_value_objects import (
        RepairCommand,
        ValidationResult,
    )



# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class RepairExecutionResult:
    """修復実行結果"""

    def __init__(self) -> None:
        self.succeeded_commands: list[RepairCommand] = []
        self.failed_commands: list[tuple[RepairCommand, str]] = []
        self.warnings: list[str] = []
        self.execution_time: float = 0.0

    @property
    def is_success(self) -> bool:
        """修復が成功したか"""
        return len(self.failed_commands) == 0

    @property
    def success_rate(self) -> float:
        """成功率を計算"""
        total = len(self.succeeded_commands) + len(self.failed_commands)
        if total == 0:
            return 1.0
        return len(self.succeeded_commands) / total


class AutoRepairEngine:
    """自動修復エンジンドメインサービス"""

    def __init__(self, path_service: IPathService | None = None) -> None:
        self._path_service = path_service
        self.dry_run_mode = False
        self.backup_enabled = True

    def create_safety_backup(self, project_path: str) -> BackupInfo:
        """安全バックアップを作成

        Args:
            project_path: バックアップ対象のプロジェクトパス

        Returns:
            バックアップ情報

        Raises:
            OSError: バックアップ作成に失敗した場合
        """
        if not project_path.exists():
            msg = f"プロジェクトパスが存在しません: {project_path}"
            raise ValueError(msg)

        # バックアップディレクトリ作成
        backup_root = project_path.parent / "backup"
        backup_root.mkdir(exist_ok=True)

        # タイムスタンプ付きバックアップ名
        timestamp = project_now().datetime.strftime("%Y%m%d_%H%M%S")
        backup_name = f"{project_path.name}_backup_{timestamp}"
        backup_path = backup_root / backup_name

        try:
            # ディレクトリ全体をコピー
            if not self.dry_run_mode:
                shutil.copytree(project_path, backup_path)

            # バックアップサイズ計算
            backup_size = self._calculate_directory_size(backup_path) if backup_path.exists() else 0

            return BackupInfo(
                backup_path=backup_path,
                original_path=project_path,
                created_at=project_now().datetime,
                backup_size=backup_size,
            )

        except Exception as e:
            msg = f"バックアップ作成に失敗しました: {e}"
            raise OSError(msg) from e

    def execute_repair_commands(self, commands: list[RepairCommand], project_path: str) -> RepairExecutionResult:
        """修復コマンドを実行

        Args:
            commands: 実行する修復コマンドのリスト
            project_path: プロジェクトパス

        Returns:
            修復実行結果
        """
        result = RepairExecutionResult()
        start_time = project_now().datetime

        for command in commands:
            try:
                success = self._execute_single_command(command, project_path)

                if success:
                    result.succeeded_commands.append(command)
                else:
                    result.failed_commands.append((command, "実行に失敗しました"))

            except Exception as e:
                result.failed_commands.append((command, str(e)))

        # 実行時間を記録
        end_time = project_now().datetime
        result.execution_time = (end_time - start_time).total_seconds()

        return result

    def verify_repair_results(self, original_validation: ValidationResult, project_path: str) -> dict[str, any]:
        """修復結果を検証

        Args:
            original_validation: 修復前の検証結果
            project_path: プロジェクトパス

        Returns:
            検証結果の辞書
        """
        # 修復後の構造を再読み込み(実際の実装では構造リポジトリを使用)
        verification_result = {
            "repair_successful": False,
            "remaining_errors": [],
            "new_errors": [],
            "improvement_score": 0.0,
            "verification_time": project_now().datetime,
        }

        try:
            # 簡易検証:基本的な構造チェック
            # B20準拠: Path ServiceはDI注入されたものを使用
            if self._path_service is None:
                # PathServiceが利用できない場合はデフォルトチェック
                required_dirs = ["src", "docs", "tests"]
            else:
                required_dirs = self._path_service.get_required_directories()
            existing_dirs = [d.name for d in project_path.iterdir() if d.is_dir()]

            missing_dirs = [d for d in required_dirs if d not in existing_dirs]

            verification_result["remaining_errors"] = missing_dirs
            verification_result["repair_successful"] = len(missing_dirs) == 0

            # 改善スコア計算
            original_missing = len(
                [error for error in original_validation.validation_errors if "ディレクトリ" in error.description]
            )

            current_missing = len(missing_dirs)

            if original_missing > 0:
                improvement = (original_missing - current_missing) / original_missing
                verification_result["improvement_score"] = max(0.0, improvement)
            else:
                verification_result["improvement_score"] = 1.0

        except Exception as e:
            verification_result["new_errors"].append(f"検証エラー: {e}")

        return verification_result

    def rollback_changes(self, backup_info: BackupInfo) -> bool:
        """変更をロールバック

        Args:
            backup_info: バックアップ情報

        Returns:
            ロールバック成功の場合True
        """
        try:
            if not backup_info.backup_path.exists():
                msg = "バックアップが存在しません"
                raise ValueError(msg)

            # 既存ディレクトリを削除
            if backup_info.original_path.exists() and not self.dry_run_mode:
                shutil.rmtree(backup_info.original_path)

            # バックアップから復元
            if not self.dry_run_mode:
                shutil.copytree(backup_info.backup_path, backup_info.original_path)

            return True

        except (OSError, shutil.Error):
            return False

    def set_dry_run_mode(self, enabled: bool) -> None:
        """ドライランモードを設定

        Args:
            enabled: ドライランモードを有効にするか
        """
        self.dry_run_mode = enabled

    def set_backup_enabled(self, enabled: bool) -> None:
        """バックアップ機能を設定

        Args:
            enabled: バックアップを有効にするか
        """
        self.backup_enabled = enabled

    def _execute_single_command(self, command: RepairCommand, project_path: str) -> bool:
        """単一の修復コマンドを実行"""
        if self.dry_run_mode:
            # ドライランモードでは実際の操作は行わない
            return True

        try:
            if command.command_type == "mkdir":
                target_path = project_path / command.target_path
                target_path.mkdir(parents=True, exist_ok=True)
                return True

            if command.command_type == "create_template":
                target_path = project_path / command.target_path

                # 親ディレクトリを作成
                target_path.parent.mkdir(parents=True, exist_ok=True)

                # テンプレートファイルを作成
                if target_path.suffix == ".yaml":
                    self._create_yaml_template(target_path)
                elif target_path.suffix == ".md":
                    self._create_markdown_template(target_path)
                else:
                    target_path.touch()

                return True

            if command.command_type == "remove":
                target_path = project_path / command.target_path
                if target_path.exists():
                    if target_path.is_file():
                        target_path.unlink()
                    else:
                        shutil.rmtree(target_path)
                return True

            # 未知のコマンドタイプ
            return False

        except (OSError, ValueError, shutil.Error):
            return False

    def _create_yaml_template(self, file_path: str) -> None:
        """YAMLテンプレートファイルを作成"""
        template_content = """# 自動生成されたテンプレートファイル
# 作成日時: {}
# 必要に応じて内容を編集してください

metadata:
  created_at: "{}"
  version: "1.0.0"
  auto_generated: true

# ここに設定内容を追加してください
""".format(project_now().datetime.strftime("%Y-%m-%d %H:%M:%S"), project_now().datetime.isoformat())

        with Path(file_path).open("w", encoding="utf-8") as f:  # TODO: IPathServiceを使用するように修正
            f.write(template_content)

    def _create_markdown_template(self, file_path: str) -> None:
        """Markdownテンプレートファイルを作成"""
        template_content = """# {}

作成日時: {}

## 概要

ここに内容を記述してください。

## 詳細

詳細な情報をここに追加してください。

---
*このファイルは自動生成されました。必要に応じて編集してください。*
""".format(file_path.stem, project_now().datetime.strftime("%Y-%m-%d %H:%M:%S"))

        with Path(file_path).open("w", encoding="utf-8") as f:  # TODO: IPathServiceを使用するように修正
            f.write(template_content)

    def _calculate_directory_size(self, directory: Path) -> int:
        """ディレクトリサイズを計算"""
        if not directory.exists():
            return 0

        total_size = 0
        try:
            for dirpath, _dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    file_path = Path(dirpath) / filename  # TODO: IPathServiceを使用するように修正
                    if file_path.exists():
                        total_size += file_path.stat().st_size
        except (OSError, PermissionError):
            # アクセス権限がない場合は0を返す
            pass

        return total_size
