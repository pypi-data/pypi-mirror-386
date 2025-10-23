#!/usr/bin/env python3
"""ガイドルート検索システム

Strategy Patternを使用した柔軟なガイドルート検索
"""

import os
from pathlib import Path


class GuideRootSearchStrategy:
    """ガイドルート検索戦略の基底クラス"""

    def search(self, _current_file: Path) -> Path | None:
        """ガイドルートを検索

        Strategy Patternの抽象メソッド
        各具体戦略クラスで実装される検索ロジック

        Args:
            _current_file: 現在のファイルパス（検索の起点）

        Returns:
            Path | None: 発見されたガイドルートパス、見つからない場合はNone

        Note:
            このメソッドは各具体戦略クラスで実装する必要があります。
            - RelativePathStrategy: 相対パス構造による検索
            - EnvironmentVariableStrategy: 環境変数による検索
            - UpwardTraversalStrategy: 上位ディレクトリ探索
            - CurrentDirectoryStrategy: カレントディレクトリからの検索
            - KnownPathStrategy: 既知パターンによる検索
        """
        # 抽象メソッドのデフォルト実装（基本実装）
        # 具体戦略クラスでオーバーライドして実装する
        return None

    def _is_valid_guide_root(self, path: Path) -> bool:
        """有効なガイドルートかチェック"""
        return path.exists() and (path / "scripts").exists() and path.name in ["00_ガイド", "ガイド"]


class RelativePathStrategy(GuideRootSearchStrategy):
    """相対パスによる検索戦略"""

    def search(self, _current_file: Path) -> Path | None:
        # scripts/main/novel.py の場合
        if _current_file.parent.name == "main" and _current_file.parent.parent.name == "scripts":
            guide_root = _current_file.parent.parent.parent
            if self._is_valid_guide_root(guide_root):
                return guide_root
        return None


class EnvironmentVariableStrategy(GuideRootSearchStrategy):
    """環境変数による検索戦略"""

    def search(self, _current_file: Path) -> Path | None:
        guide_root_env = os.environ.get("GUIDE_ROOT")
        if guide_root_env:
            guide_root = Path(guide_root_env)
            if self._is_valid_guide_root(guide_root):
                return guide_root
        return None


class UpwardTraversalStrategy(GuideRootSearchStrategy):
    """上位ディレクトリ探索戦略"""

    def search(self, current_file: Path) -> Path | None:
        check_dir = current_file.parent
        for _ in range(10):  # 最大10階層まで遡る
            if self._is_valid_guide_root(check_dir):
                return check_dir
            if check_dir.parent == check_dir:  # ルートディレクトリに到達:
                break
            check_dir = check_dir.parent
        return None


class CurrentDirectoryStrategy(GuideRootSearchStrategy):
    """カレントディレクトリからの検索戦略"""

    def search(self, _current_file: Path) -> Path | None:
        current_dir = Path.cwd()
        check_dir = current_dir
        for _ in range(10):
            if self._is_valid_guide_root(check_dir):
                return check_dir
            if (check_dir / "scripts" / "main" / "novel.py").exists():
                return check_dir
            if check_dir.parent == check_dir:
                break
            check_dir = check_dir.parent
        return None


class KnownPathStrategy(GuideRootSearchStrategy):
    """既知パターンによる検索戦略"""

    def search(self, current_file: Path) -> Path | None:
        possible_paths = [
            Path.home() / "Documents" / "9_小説" / "00_ガイド",
            Path("/mnt/c/Users") / os.environ.get("USER", "user") / "OneDrive" / "Documents" / "9_小説" / "00_ガイド",
            current_file.parent.parent.parent,  # フォールバック
        ]

        for path in possible_paths:
            if self._is_valid_guide_root(path):
                return path
        return None


class GuideRootFinder:
    """ガイドルート検索のファサードクラス"""

    def __init__(self) -> None:
        self.strategies = [
            RelativePathStrategy(),
            EnvironmentVariableStrategy(),
            UpwardTraversalStrategy(),
            CurrentDirectoryStrategy(),
            KnownPathStrategy(),
        ]

    def find_guide_root(self, current_file: Path) -> Path:
        """すべての戦略を試してガイドルートを検索"""
        for strategy in self.strategies:
            result = strategy.search(current_file)
            if result:
                return result

        # フォールバック
        return current_file.parent.parent.parent


def find_guide_root() -> Path:
    """ガイドルートを確実に特定する実行場所非依存システム"""
    current_file = Path(__file__).resolve()
    finder = GuideRootFinder()
    return finder.find_guide_root(current_file)
