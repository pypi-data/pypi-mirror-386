#!/usr/bin/env python3
"""テスト共通ベースクラス

全てのテストでtempフォルダ統合とクリーンアップを一元管理


仕様書: SPEC-INFRASTRUCTURE
"""

import shutil
import time
from pathlib import Path


class BaseTestCase:
    """テスト共通ベースクラス

    - tempフォルダ配下にテストディレクトリを作成
    - 自動クリーンアップ機能
    - タイムスタンプベースの一意なディレクトリ生成
    """

    def setup_method(self) -> None:
        """テストメソッド開始時の共通処理"""
        # プロジェクトのtempフォルダ配下にテストディレクトリを作成
        project_root = Path(__file__).parent.parent.parent
        temp_base = project_root / "temp" / "tests"
        temp_base.mkdir(parents=True, exist_ok=True)

        # タイムスタンプ付きの一意なテストディレクトリを作成
        timestamp = int(time.time())
        test_class_name = self.__class__.__name__
        test_dir_name = f"{test_class_name}_{timestamp}_{id(self)}"
        self.test_root = temp_base / test_dir_name
        self.test_root.mkdir(exist_ok=True)

        # クリーンアップフラグ
        self._cleanup_required = True

        print(f"🏗️  テストディレクトリ作成: {self.test_root}")

    def teardown_method(self) -> None:
        """テストメソッド終了時の共通処理"""
        if hasattr(self, "_cleanup_required") and self._cleanup_required:
            if hasattr(self, "test_root") and self.test_root.exists():
                try:
                    shutil.rmtree(self.test_root)
                    print(f"🗑️  テストディレクトリ削除: {self.test_root}")
                except Exception as e:
                    print(f"⚠️  テストディレクトリ削除失敗: {self.test_root} - {e}")
                    # 削除失敗時の手動削除指示
                    print(f"   手動削除してください: rm -rf '{self.test_root}'")

    def create_temp_project(self, project_name: str) -> Path:
        """テスト用プロジェクトディレクトリを作成

        Args:
            project_name: プロジェクト名

        Returns:
            Path: 作成されたプロジェクトディレクトリのパス
        """
        project_dir = self.test_root / project_name
        project_dir.mkdir(exist_ok=True)
        return project_dir

    def disable_cleanup(self) -> None:
        """クリーンアップを無効化(デバッグ用)"""
        self._cleanup_required = False
        print(f"⚠️  クリーンアップ無効化: {self.test_root}")


class BaseIntegrationTestCase(BaseTestCase):
    """統合テスト用ベースクラス

    統合テスト特有の機能を追加
    """

    def setup_method(self) -> None:
        """統合テスト用セットアップ"""
        super().setup_method()

        # 統合テスト用の環境変数設定
        import os

        self.original_env = os.environ.copy()
        os.environ["NOVEL_PROJECTS_ROOT"] = str(self.test_root)

    def teardown_method(self) -> None:
        """統合テスト用クリーンアップ"""
        # 環境変数を元に戻す
        import os

        os.environ.clear()
        os.environ.update(self.original_env)

        super().teardown_method()


class BaseE2ETestCase(BaseTestCase):
    """E2Eテスト用ベースクラス

    E2Eテスト特有の機能を追加
    """

    def setup_method(self) -> None:
        """E2Eテスト用セットアップ"""
        super().setup_method()

        # 実際のnovelerコマンドパス（2025年8月30日よりnovel→novelerに統一）
        project_root = Path(__file__).parent.parent.parent.parent.parent
        self.novel_cmd = project_root / "bin" / "noveler"

        # フォールバック: bin/noveler-devも確認
        if not self.novel_cmd.exists():
            self.novel_cmd = project_root / "bin" / "noveler-dev"

        # 最終フォールバック: Pythonモジュールとして実行
        if not self.novel_cmd.exists():
            self.novel_cmd = f"python -m noveler.presentation.cli.main"

        # 環境変数設定
        import os

        self.original_cwd = os.getcwd()
        self.env = os.environ.copy()
        self.env["NOVEL_PROJECTS_ROOT"] = str(self.test_root)

        # novelerコマンド用の環境変数追加
        project_src_path = project_root / "src"
        if project_src_path.exists():
            self.env["PYTHONPATH"] = f"{project_src_path}:{self.env.get('PYTHONPATH', '')}"

    def teardown_method(self) -> None:
        """E2Eテスト用クリーンアップ"""
        # 作業ディレクトリを元に戻す
        import os

        os.chdir(self.original_cwd)

        super().teardown_method()
