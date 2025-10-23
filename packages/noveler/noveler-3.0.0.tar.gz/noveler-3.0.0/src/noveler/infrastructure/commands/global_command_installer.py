#!/usr/bin/env python3
"""
グローバルコマンドインストーラー

SPEC-MCP-001準拠: グローバル /noveler コマンド実装
95%トークン削減を実現するMCPサーバー統合
"""

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from noveler.infrastructure.logging.unified_logger import get_logger


class GlobalCommandInstallerError(Exception):
    """グローバルコマンドインストーラー例外"""


class GlobalCommandInstaller:
    """グローバルコマンドインストーラー"""

    def __init__(self) -> None:
        """初期化"""
        self.logger = get_logger(__name__)

    def get_claude_commands_path(self) -> Path:
        """Claude Codeコマンドディレクトリパスを取得"""
        return Path.home() / ".claude" / "commands"

    def get_noveler_template_path(self) -> Path:
        """novelerテンプレートファイルパスを取得"""
        current_dir = Path(__file__).parent
        return current_dir / "templates" / "global_noveler.md"

    def get_global_noveler_path(self) -> Path:
        """グローバルnovelerコマンドファイルパスを取得"""
        return self.get_claude_commands_path() / "noveler.md"

    def is_installed(self) -> bool:
        """グローバルコマンドがインストール済みかチェック"""
        return self.get_global_noveler_path().exists()

    def create_backup(self, file_path: Path) -> Path | None:
        """既存ファイルのバックアップを作成"""
        if not file_path.exists():
            return None

        timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.parent / f"{file_path.name}.backup.{timestamp}"

        try:
            shutil.copy2(file_path, backup_path)
            self.logger.info("バックアップ作成: %s", backup_path)
            return backup_path
        except Exception as e:
            self.logger.exception("バックアップ作成失敗")
            msg = f"バックアップ作成エラー: {e}"
            raise GlobalCommandInstallerError(msg) from e

    def install_global_command(self) -> bool:
        """グローバルコマンドをインストール"""
        try:
            # Claude Codeコマンドディレクトリを作成
            commands_dir = self.get_claude_commands_path()
            commands_dir.mkdir(parents=True, exist_ok=True)

            # 既存ファイルのバックアップ
            target_file = self.get_global_noveler_path()
            if target_file.exists():
                self.create_backup(target_file)

            # テンプレートファイルをコピー
            template_path = self.get_noveler_template_path()
            if not template_path.exists():
                msg = f"テンプレートファイルが見つかりません: {template_path}"
                raise GlobalCommandInstallerError(msg)

            shutil.copy2(template_path, target_file)
            self.logger.info("グローバルコマンドインストール完了: %s", target_file)
            return True

        except PermissionError as e:
            error_msg = f"権限エラー: {commands_dir} への書き込み権限がありません"
            self.logger.exception("権限エラー")
            raise GlobalCommandInstallerError(error_msg) from e

        except Exception as e:
            error_msg = f"インストールエラー: {e}"
            self.logger.exception("インストールエラー")
            raise GlobalCommandInstallerError(error_msg) from e

    def uninstall_global_command(self) -> bool:
        """グローバルコマンドをアンインストール"""
        try:
            target_file = self.get_global_noveler_path()
            if not target_file.exists():
                self.logger.info("グローバルコマンドは既にインストールされていません")
                return True

            # バックアップ作成後削除
            self.create_backup(target_file)
            target_file.unlink()

            self.logger.info("グローバルコマンドアンインストール完了: %s", target_file)
            return True

        except Exception as e:
            error_msg = f"アンインストールエラー: {e}"
            self.logger.exception("アンインストールエラー")
            raise GlobalCommandInstallerError(error_msg) from e

    def get_installation_info(self) -> dict[str, Any]:
        """インストール状況を取得"""
        target_file = self.get_global_noveler_path()
        commands_dir = self.get_claude_commands_path()

        info = {
            "installed": self.is_installed(),
            "target_path": str(target_file),
            "commands_dir": str(commands_dir),
            "commands_dir_exists": commands_dir.exists(),
            "template_exists": self.get_noveler_template_path().exists(),
        }

        if target_file.exists():
            stat = target_file.stat()
            info.update(
                {
                    "file_size": stat.st_size,
                    "modified_time": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                }
            )

        return info
