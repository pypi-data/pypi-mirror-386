#!/usr/bin/env python3
"""
グローバル /noveler コマンドインストールスクリプト

SPEC-MCP-001準拠: グローバルコマンドの簡単インストール
"""

import sys
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from noveler.infrastructure.commands.global_command_installer import (
    GlobalCommandInstaller,
    GlobalCommandInstallerError,
)
from noveler.infrastructure.logging.unified_logger import get_logger


def main() -> int:
    """メイン実行関数"""
    logger = get_logger(__name__)

    try:
        installer = GlobalCommandInstaller()

        # インストール状況確認
        info = installer.get_installation_info()
        logger.info("=== グローバル /noveler コマンドインストーラー ===")
        logger.info(f"インストール先: {info['target_path']}")
        logger.info(f"既にインストール済み: {info['installed']}")

        if info["installed"]:
            response = input("既にインストール済みです。再インストールしますか？ (y/N): ")
            if response.lower() not in ["y", "yes"]:
                logger.info("インストールを中止しました")
                return 0

        # インストール実行
        logger.info("インストール実行中...")
        success = installer.install_global_command()

        if success:
            logger.info("✅ グローバル /noveler コマンドのインストールが完了しました！")
            logger.info("")
            logger.info("🚀 使用方法:")
            logger.info("  /noveler write 1    # 第1話執筆")
            logger.info("  /noveler check 1    # 第1話品質チェック")
            logger.info("  /noveler status     # プロジェクト状況確認")
            logger.info("  /noveler init my-novel  # 新規プロジェクト作成")
            logger.info("")
            logger.info("任意のディレクトリから /noveler コマンドが使用できます。")
            return 0
        logger.error("❌ インストールに失敗しました")
        return 1

    except GlobalCommandInstallerError as e:
        logger.error(f"❌ インストールエラー: {e}")
        return 1
    except KeyboardInterrupt:
        logger.info("\n中断されました")
        return 130
    except Exception as e:
        logger.error(f"❌ 予期しないエラー: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
