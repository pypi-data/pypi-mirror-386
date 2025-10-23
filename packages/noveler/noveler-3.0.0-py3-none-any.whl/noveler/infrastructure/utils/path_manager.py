#!/usr/bin/env python3
"""統一パス管理システム
すべての実行コンテキストで一貫したモジュールインポートを提供
"""

import sys
from pathlib import Path
from typing import Any


class PathManager:
    """システム全体のパス管理を統一するシングルトンクラス"""

    _instance = None
    _initialized = False

    def __new__(cls) -> Any:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not self._initialized:
            self.setup_paths()
            PathManager._initialized = True

    def setup_paths(self) -> None:
        """Pythonパスを設定(実行コンテキストに依存しない)"""
        # スクリプトディレクトリを特定
        self.scripts_root = self._find_scripts_root()
        self.guide_root = self.scripts_root.parent

        # sys.pathに追加(重複チェック付き)
        paths_to_add = [
            str(self.scripts_root),  # scripts/をルートとして追加
            str(self.guide_root),  # 00_ガイド/をルートとして追加
        ]

        for path in paths_to_add:
            if path not in sys.path:
                sys.path.insert(0, path)

    def _find_scripts_root(self) -> Path:
        """scriptsディレクトリを検索(確実な方法)"""
        # このファイルからscriptsルートを計算
        current_file = Path(__file__).resolve()

        # scripts/infrastructure/utils/path_manager.py なので、3つ上がscripts/
        scripts_root = current_file.parent.parent.parent

        # 検証:domain/存在チェック
        if (scripts_root / "domain").exists():
            return scripts_root

        # フォールバック検索
        search_paths = [
            Path.cwd().resolve(),
            current_file.parent.parent.parent,  # 00_ガイド/
        ]

        for base in search_paths:
            candidates = [
                base / "scripts",
                base / "00_ガイド" / "scripts",
            ]

            for candidate in candidates:
                if candidate.exists() and (candidate / "domain").exists():
                    return candidate

        # 最終フォールバック
        return scripts_root

    def get_paths(self) -> dict[str, str]:
        """パス情報を取得"""
        return {
            "scripts_root": str(self.scripts_root),
            "guide_root": str(self.guide_root),
            "current_sys_path": sys.path[:5],  # 最初の5つのパス
        }

    @classmethod
    def ensure_paths(cls) -> None:
        """パスが正しく設定されていることを保証(静的メソッド)"""
        cls()  # インスタンス化することで自動的にsetup_paths()が呼ばれる


def ensure_imports() -> None:
    """すべてのスクリプトで使用する統一インポート設定関数"""
    PathManager.ensure_paths()


# モジュールインポート時に自動実行
ensure_imports()
