#!/usr/bin/env python3
"""環境設定管理システム

システム全体の環境変数とPYTHONPATHを自動設定・管理する
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

from rich.table import Table

from noveler.infrastructure.factories.path_service_factory import create_path_service
from noveler.infrastructure.logging.unified_logger import get_logger

logger = get_logger(__name__)


class EnvironmentManager:
    """環境設定を自動管理するクラス"""

    CONFIG_FILE = ".novel-env.json"

    def __init__(self, logger_service=None, console_service=None) -> None:
        self.script_dir = Path(__file__).parent.resolve()
        self.guide_root = self.script_dir.parent.parent.parent
        self.config_cache: dict[str, Any] | None = None
        self._logger_service = logger_service
        self._console_service = console_service

    def setup_environment(self) -> bool:
        """環境設定の自動セットアップ（プロジェクト設定.yaml統合版）"""
        try:
            # 1. GUIDE_ROOTの設定
            guide_root = str(self.guide_root)
            os.environ["GUIDE_ROOT"] = guide_root

            # 2. PYTHONPATHの設定(統合インポート管理システム準拠)
            guide_root_str = str(self.guide_root)
            current_path = os.environ.get("PYTHONPATH", "")

            if guide_root_str not in current_path:
                if current_path:
                    os.environ["PYTHONPATH"] = f"{guide_root_str}:{current_path}"
                else:
                    os.environ["PYTHONPATH"] = guide_root_str

            # sys.pathにも追加
            if guide_root_str not in sys.path:
                sys.path.insert(0, guide_root_str)

            # 3. Pythonキャッシュディレクトリの設定
            temp_cache_dir = self.guide_root / "temp" / "cache" / "python"
            temp_cache_dir.mkdir(parents=True, exist_ok=True)
            os.environ["PYTHONPYCACHEPREFIX"] = str(temp_cache_dir)

            # sys.pycache_prefixも設定(実行中のプロセス用)
            if hasattr(sys, "pycache_prefix"):
                sys.pycache_prefix = str(temp_cache_dir)

            # 既存の__pycache__フォルダを無効化(将来的にtempに集約)
            # sysは既にインポート済み
            if hasattr(sys, "dont_write_bytecode"):
                # デバッグ時のみバイトコード無効化を検討
                pass

            # 4. PROJECT_ROOT設定（DDD準拠・環境変数優先）
            # 既に設定された環境変数は尊重し、副作用のある上書きを廃止
            existing_project_root = os.environ.get("PROJECT_ROOT")
            if not existing_project_root:
                # 環境変数が未設定の場合のみ自動検出
                project_root = self.detect_project_root()
                if project_root:
                    os.environ["PROJECT_ROOT"] = str(project_root)

                    # プロジェクトフォルダ構成の初期化
                    # 統合されたCommonPathServiceを使用してフォルダ構成を管理
                    try:

                        path_service = create_path_service(project_root)
                        # 必要なフォルダの作成
                        path_service.ensure_directories_exist()
                    except ImportError:
                        # サービスが利用できない場合は続行
                        pass

            # 5. 設定をキャッシュ
            self.save_config_cache()

            return True

        except Exception as e:
            if self._logger_service:
                self._logger_service.warning(f"環境設定エラー: {e}")
            else:
                logger.warning(f"環境設定エラー: {e}")
            return False

    def detect_project_root(self) -> Path | None:
        """プロジェクトルートの自動検出"""
        current_dir = Path.cwd()

        # パターン1: プロジェクト設定.yamlを探す
        check_dir = current_dir
        for _ in range(10):  # 最大10階層まで遡る
            if (check_dir / "プロジェクト設定.yaml").exists():
                return check_dir

            if check_dir.parent == check_dir:  # ルートディレクトリに到達:
                break
            check_dir = check_dir.parent

        # パターン2: .novel-projectファイルを探す
        check_dir = current_dir
        for _ in range(10):
            if (check_dir / ".novel-project").exists():
                return check_dir

            if check_dir.parent == check_dir:
                break
            check_dir = check_dir.parent

        # パターン3: 40_原稿フォルダがあるディレクトリを探す
        check_dir = current_dir
        for _ in range(10):

            try:
                path_service = create_path_service(check_dir)
                if path_service.get_manuscript_dir().exists():
                    return check_dir
            except Exception:
                pass

            if check_dir.parent == check_dir:
                break
            check_dir = check_dir.parent

        return None

    def create_virtual_project_environment(self) -> Path:
        """仮想プロジェクト環境の作成"""
        temp_project = self.guide_root / "temp" / "virtual_project"
        temp_project.mkdir(parents=True, exist_ok=True)

        # 最小限のプロジェクト設定を作成
        project_config: dict[str, Any] = temp_project / "プロジェクト設定.yaml"
        if not project_config.exists():
            config_content = """# 仮想プロジェクト設定(一時的)
project:
  name: "仮想プロジェクト"
  type: "development"
  created: "auto-generated"

settings:
  quality_check: true
  auto_backup: false
"""
            project_config.write_text(config_content, encoding="utf-8")

        return temp_project

    def is_guide_folder_execution(self) -> bool:
        """ガイドフォルダから実行されているかチェック"""
        current_dir = Path.cwd()
        return current_dir == self.guide_root or current_dir.is_relative_to(self.guide_root)

    def get_effective_project_root(self) -> Path:
        """有効なプロジェクトルートを取得(仮想環境含む・DDD準拠)"""
        # 1. 環境変数PROJECT_ROOTを最優先で確認（副作用なし）
        env_project_root = os.environ.get("PROJECT_ROOT")
        if env_project_root:
            env_path = Path(env_project_root)
            if env_path.exists():
                return env_path

        # 2. 通常の探索ロジック
        project_root = self.detect_project_root()
        if project_root:
            return project_root

        # 3. プロジェクトが見つからない場合
        if self.is_guide_folder_execution():
            # ガイドフォルダから実行 → 仮想プロジェクト環境を作成
            return self.create_virtual_project_environment()
        # その他の場所から実行 → 現在のディレクトリを使用
        return Path.cwd()

    def save_config_cache(self) -> None:
        """設定をキャッシュファイルに保存"""
        config = {
            "guide_root": os.environ.get("GUIDE_ROOT"),
            "project_root": os.environ.get("PROJECT_ROOT"),
            "pythonpath": os.environ.get("PYTHONPATH"),
            "last_updated": str(Path.cwd()),
        }

        cache_file = self.guide_root / "temp" / self.CONFIG_FILE
        cache_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with cache_file.open("w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception:
            # キャッシュ保存は失敗しても問題なし(ログレベルを下げる)
            pass

    def load_config_cache(self) -> dict[str, Any]:
        """キャッシュファイルから設定を読み込み"""
        if self.config_cache is not None:
            return self.config_cache

        cache_file = self.guide_root / "temp" / self.CONFIG_FILE
        if not cache_file.exists():
            return {}

        try:
            with cache_file.open("r", encoding="utf-8") as f:
                self.config_cache = json.load(f)
                return self.config_cache
        except Exception:
            return {}

    def validate_environment(self) -> dict[str, bool]:
        """環境設定の検証"""
        validation = {
            "guide_root_set": bool(os.environ.get("GUIDE_ROOT")),
            "guide_root_exists": False,
            "pythonpath_set": bool(os.environ.get("PYTHONPATH")),
            "scripts_in_path": False,
            "project_root_set": bool(os.environ.get("PROJECT_ROOT")),
            "project_root_exists": False,
        }

        # GUIDE_ROOTの存在チェック
        guide_root = os.environ.get("GUIDE_ROOT")
        if guide_root:
            validation["guide_root_exists"] = Path(guide_root).exists()

        # PYTHONPATHにguide_rootが含まれているかチェック(統合インポート管理システム準拠)
        pythonpath = os.environ.get("PYTHONPATH", "")
        guide_root_str = str(self.guide_root)
        validation["scripts_in_path"] = guide_root_str in pythonpath or guide_root_str in sys.path

        # PROJECT_ROOTの存在チェック
        project_root = os.environ.get("PROJECT_ROOT")
        if project_root:
            validation["project_root_exists"] = Path(project_root).exists()

        return validation

    def get_environment_status(self) -> str:
        """環境設定の状態を文字列で取得"""
        validation = self.validate_environment()

        if all(validation.values()):
            return "✅ 正常"
        if validation["guide_root_set"] and validation["pythonpath_set"]:
            return "⚠️ 部分的に正常"
        return "❌ 要修正"

    def print_environment_info(self) -> None:
        """環境設定情報を表示"""
        if self._console_service:
            table = Table(title="🔧 環境設定情報")
            table.add_column("項目", style="cyan")
            table.add_column("値", style="green")

            table.add_row("GUIDE_ROOT", os.environ.get("GUIDE_ROOT", "未設定"))
            table.add_row("PROJECT_ROOT", os.environ.get("PROJECT_ROOT", "未設定"))
            table.add_row("PYTHONPATH", os.environ.get("PYTHONPATH", "未設定"))
            table.add_row("状態", self.get_environment_status())

            self._console_service.print(table)
        elif self._logger_service:
            self._logger_service.info("🔧 環境設定情報")
            self._logger_service.info(f"   GUIDE_ROOT: {os.environ.get('GUIDE_ROOT', '未設定')}")
            self._logger_service.info(f"   PROJECT_ROOT: {os.environ.get('PROJECT_ROOT', '未設定')}")
            self._logger_service.info(f"   PYTHONPATH: {os.environ.get('PYTHONPATH', '未設定')}")
            self._logger_service.info(f"   状態: {self.get_environment_status()}")
        else:
            logger.info("🔧 環境設定情報")
            logger.info(f"   GUIDE_ROOT: {os.environ.get('GUIDE_ROOT', '未設定')}")
            logger.info(f"   PROJECT_ROOT: {os.environ.get('PROJECT_ROOT', '未設定')}")
            logger.info(f"   PYTHONPATH: {os.environ.get('PYTHONPATH', '未設定')}")
            logger.info(f"   状態: {self.get_environment_status()}")


# グローバルインスタンス
_env_manager = EnvironmentManager()


def setup_environment() -> bool:
    """環境設定の自動セットアップ(グローバル関数)"""
    return _env_manager.setup_environment()


def get_environment_manager() -> EnvironmentManager:
    """環境設定マネージャーのインスタンスを取得"""
    return _env_manager


def ensure_environment() -> bool:
    """環境設定を確実にセットアップ"""
    if not _env_manager.setup_environment():
        return False

    validation = _env_manager.validate_environment()
    critical_checks = ["guide_root_set", "pythonpath_set", "scripts_in_path"]

    return all(validation[check] for check in critical_checks)
