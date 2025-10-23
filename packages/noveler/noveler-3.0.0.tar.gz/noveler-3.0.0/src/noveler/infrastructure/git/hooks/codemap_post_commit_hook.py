#!/usr/bin/env python3
"""CODEMAP自動更新用Post-commitフック

仕様書: SPEC-CODEMAP-AUTO-UPDATE-001
REQ-3: Git統合機能
"""

import shutil
import sys
from pathlib import Path

# プロジェクトルートをsys.pathに追加
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from noveler.application.use_cases.codemap_auto_update_use_case import (
    CodeMapAutoUpdateRequest,
    CodeMapAutoUpdateUseCase,
)
from noveler.domain.services.codemap_synchronization_service import CodeMapSynchronizationService
from noveler.infrastructure.adapters.git_information_adapter import GitInformationAdapter
from noveler.infrastructure.repositories.yaml_codemap_repository import YamlCodeMapRepository

# DDD準拠: Infrastructure→Presentation依存を除去
from noveler.presentation.shared.shared_utilities import console


class CodeMapPostCommitHook:
    """CODEMAP自動更新Post-commitフック

    Git post-commit hookから呼び出される統合機能
    """

    def __init__(self, repository_path: Path | None = None, logger_service: object | None = None, console_service: object | None = None) -> None:
        """初期化

        Args:
            repository_path: リポジトリパス（Noneの場合は現在のディレクトリ）
            logger_service: ロガーサービス
            console_service: コンソールサービス
        """
        self.repository_path = repository_path or Path.cwd()

        # CODEMAPパスの確定
        self.codemap_path = self.repository_path / "CODEMAP.yaml"

        # 依存性の初期化
        self._initialize_dependencies()

        self.logger_service = logger_service
        # コンソールサービスが未指定の場合は共有Consoleにフォールバック
        self.console_service = console_service or console
    def _initialize_dependencies(self) -> None:
        """依存性の初期化"""
        # リポジトリとアダプターの初期化
        self.codemap_repository = YamlCodeMapRepository(self.codemap_path)
        self.git_adapter = GitInformationAdapter(self.repository_path)
        self.sync_service = CodeMapSynchronizationService()

        # ユースケースの初期化
        self.use_case = CodeMapAutoUpdateUseCase(self.codemap_repository, self.git_adapter, self.sync_service)

    def execute(self, force_update: bool = False, skip_validation: bool = False) -> bool:
        """CODEMAP自動更新実行

        Args:
            force_update: 強制更新フラグ
            skip_validation: 検証スキップフラグ

        Returns:
            bool: 実行成功時True
        """
        try:
            self.console_service.print("🔄 CODEMAP auto-update starting...")

            # リクエスト作成
            request = CodeMapAutoUpdateRequest(
                force_update=force_update, create_backup=True, validate_result=not skip_validation
            )

            # 自動更新実行
            response = self.use_case.execute(request)

            # 結果の処理
            if response.success:
                if response.updated:
                    self.console_service.print("✅ CODEMAP updated successfully")
                    self.console_service.print(f"📝 Changes: {response.changes_summary}")
                    if response.backup_id:
                        self.console_service.print(f"💾 Backup: {response.backup_id}")
                else:
                    self.console_service.print("ℹ️ CODEMAP is already up-to-date")

                self.console_service.print(f"⏱️ Execution time: {response.execution_time_ms:.1f}ms")
                return True
            self.console_service.print(f"❌ CODEMAP update failed: {response.error_message}")
            if response.validation_errors:
                self.console_service.print("Validation errors:")
                for error in response.validation_errors:
                    self.console_service.print(f"  - {error}")
            return False

        except Exception as e:
            self.console_service.print(f"❌ Hook execution error: {e}")
            return False

    def get_status(self) -> dict:
        """更新システムの状態取得

        Returns:
            dict: システム状態情報
        """
        try:
            return self.use_case.get_update_status()
        except Exception as e:
            return {"error": str(e), "codemap_available": False, "git_repository": False}


def main() -> int:
    """メイン実行関数

    Git post-commit hookから呼び出される

    Returns:
        int: 終了コード（0: 成功, 1: 失敗）
    """
    try:
        # 現在のディレクトリをリポジトリルートとして使用
        hook = CodeMapPostCommitHook()

        # システム状態の確認
        status = hook.get_status()

        if not status.get("git_repository", False):
            console.print("[yellow]⚠️ Not a Git repository, skipping CODEMAP update[/yellow]")
            return 0

        if not status.get("codemap_available", False):
            console.print("[yellow]⚠️ CODEMAP not found, skipping update[/yellow]")
            return 0

        # 自動更新実行
        success = hook.execute()

        return 0 if success else 1

    except KeyboardInterrupt:
        console.print("[yellow]⚠️ CODEMAP update interrupted[/yellow]")
        return 1
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
        return 1


# フック統合のための関数エクスポート
def install_codemap_post_commit_hook(git_root: Path, guide_root: Path | None = None) -> bool:
    """CODEMAP post-commit hookのインストール

    Args:
        git_root: GitリポジトリのルートPath
        guide_root: ガイドプロジェクトのルートPath（省略時はgit_rootを使用）

    Returns:
        bool: インストール成功時True
    """
    try:
        hooks_dir = git_root / ".git" / "hooks"
        # フォールバック: guide_root未指定の場合は、このファイルのリポジトリルートを推定
        guide_root = guide_root or Path(__file__).resolve().parents[5]
        hook_file = hooks_dir / "post-commit"

        # フック内容の生成
        hook_content = f"""#!/bin/bash
# CODEMAP Auto-Update Post-Commit Hook
# Generated by Claude Code Development Guidelines

# Python環境の確認
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "Warning: Python not found, skipping CODEMAP update"
    exit 0
fi

# CODEMAP自動更新の実行
cd "{git_root}"
export PYTHONPATH="{(guide_root / 'src').as_posix()}:$PYTHONPATH"
$PYTHON_CMD "{(guide_root / 'src' / 'noveler' / 'infrastructure' / 'git' / 'hooks' / 'codemap_post_commit_hook.py').as_posix()}"

# 元のpost-commitフックが存在する場合は実行
if [ -f "{hooks_dir / "post-commit.original"}" ]; then
    bash "{hooks_dir / "post-commit.original"}" "$@"
fi
"""

        # 既存のフックをバックアップ
        if hook_file.exists():
            backup_file = hooks_dir / "post-commit.original"
            if not backup_file.exists():
                shutil.copy2(hook_file, backup_file)

        # 新しいフックを書き込み
        hook_file.write_text(hook_content)
        hook_file.chmod(0o755)  # 実行権限を付与

        console.print(f"[green]✅ CODEMAP post-commit hook installed: {hook_file}[/green]")
        return True

    except Exception as e:
        console.print(f"[red]❌ Failed to install CODEMAP post-commit hook: {e}[/red]")
        return False


if __name__ == "__main__":
    sys.exit(main())
